# Orchestrator - gRPC сервер для оркестрации адаптации сообщений

import os
import sys
import grpc
import asyncio
import aiohttp

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chameleon.core.v1.orchestrator_pb2 as orchestrator_pb2
import chameleon.core.v1.orchestrator_pb2_grpc as orchestrator_pb2_grpc
import chameleon.core.v1.retriever_pb2 as retriever_pb2
import chameleon.core.v1.retriever_pb2_grpc as retriever_pb2_grpc
import chameleon.core.v1.common_pb2 as common_pb2
from common.logging import logger, log_info, log_error
from common.metrics import (
    track_llm_call,
    track_token_usage,
    track_cache_hit,
    track_cache_ttl_hit,
    track_cache_ttl_miss,
    track_grpc_timeout,
    track_llm_model_call,
)
from common.validator import InputValidator
from common.langfuse_integration import (
    init_langfuse_from_config,
    log_generation,
)

from .cache_manager import get_cache_manager
from .context_assembler import get_context_assembler
from .config import get_config, Config


class OrchestratorService(orchestrator_pb2_grpc.OrchestratorServiceServicer):
    """gRPC service implementation for Orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        redis_password = os.getenv(
            "REDIS_PASSWORD",
            config.redis_password if hasattr(config, "redis_password") else None,
        )
        self.cache_manager = get_cache_manager(
            host=config.redis_host,
            port=config.redis_port,
            ttl=config.cache_ttl,
            password=redis_password,
        )
        self.context_assembler = get_context_assembler()

        # gRPC channels to other services
        retriever_host = os.getenv("RETRIEVER_HOST", "retriever")
        retriever_port = 8002  # gRPC port for Retriever
        retriever_channel = grpc.insecure_channel(f"{retriever_host}:{retriever_port}")
        self.retriever_stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)

        llm_gateway_host = os.getenv("LLM_GATEWAY_HOST", "llm-gateway")
        llm_gateway_port = os.getenv("LLM_GATEWAY_PORT", "8003")
        self.llm_gateway_url = f"http://{llm_gateway_host}:{llm_gateway_port}/generate"

    async def ProcessMessage(self, request, context):
        """Process incoming message and return adapted version."""
        message_id = request.message_id
        log_info("Processing message", message_id=message_id)

        # Validate input first to avoid trace creation for invalid requests
        is_valid, error = InputValidator.validate_message(
            {
                "message_id": message_id,
                "sender_id": (
                    request.sender_id if hasattr(request, "sender_id") else ""
                ),
                "recipient_id": request.recipient_id,
                "text": request.text,
                "style_name": (
                    request.style_name if hasattr(request, "style_name") else None
                ),
            }
        )
        if not is_valid:
            log_error("Invalid message input", error=error)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return orchestrator_pb2.ProcessMessageResponse()

        # Use context manager to ensure trace is properly ended
        with log_generation(
            name=f"orchestrator-process-{message_id}",
            model="orchestrator",
            prompt=f"Processing message {message_id}",
            completion="Orchestrator processing complete",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            metadata={
                "message_id": message_id,
                "sender_id": (
                    request.sender_id if hasattr(request, "sender_id") else ""
                ),
                "recipient_id": request.recipient_id,
                "has_style": bool(request.style_name),
            },
        ):
            # Check cache
            cache_key = self.cache_manager.generate_key(
                message_id=request.message_id,
                text=request.text,
                recipient_id=request.recipient_id,
                rules=[],
            )

            cached = self.cache_manager.get(cache_key)
            if cached:
                log_info("Cache hit for message", message_id=message_id)
                track_cache_hit(cache_type="orchestrator")
                
                # Log cache hit to Langfuse - directly log without span context
                try:
                    log_generation(
                        name="orchestrator-cache-hit",
                        model="cache",
                        prompt=f"Cache lookup for message {message_id}",
                        completion="Cache hit",
                        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        metadata={"message_id": message_id, "from_cache": True},
                    )
                except Exception as e:
                    log_error("Failed to log cache hit to Langfuse", error=str(e))
                
                return orchestrator_pb2.ProcessMessageResponse(
                    adapted_text=cached["adapted_text"],
                    was_adapted=cached["was_adapted"],
                    confidence=cached.get("confidence", 0.0),
                    model_used=cached.get("model_used", ""),
                    processing_time_ms=cached.get("processing_time_ms", 0),
                    rules_applied=cached.get("rules_applied", []),
                    adaptation_metadata=orchestrator_pb2.AdaptationMetadata(
                        from_cache=True,
                        fallback_used=cached.get("from_cache", False),
                        fallback_reason=cached.get("fallback_reason", ""),
                        tokens_prompt=cached.get("tokens_prompt", 0),
                        tokens_completion=cached.get("tokens_completion", 0),
                    ),
                )

            # Fetch profile with TTL caching
        try:
            profile = self.retriever_stub.GetProfile(
                retriever_pb2.GetProfileRequest(
                    user_id=request.recipient_id, include_history=False, cache_ttl=3600
                ),
                timeout=5.0,
            )
            track_cache_ttl_hit(cache_type="profile")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                log_info(
                    "Profile not found, creating default", user_id=request.recipient_id
                )
                profile = retriever_pb2.UserProfile(
                    user_id=request.recipient_id,
                    full_name="Unknown User",
                    role="employee",
                    department="unknown",
                    honorific_type=0,
                    communication_mode=0,
                )
                track_cache_ttl_miss(cache_type="profile")
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                log_error("Retriever timeout", error="Deadline exceeded")
                track_grpc_timeout(service="retriever", method="GetProfile")
                profile = retriever_pb2.UserProfile(
                    user_id=request.recipient_id,
                    full_name="Unknown User",
                    role="employee",
                    department="unknown",
                    honorific_type=0,
                    communication_mode=0,
                )
            else:
                log_error("Failed to get profile", error=str(e))
                profile = retriever_pb2.UserProfile(
                    user_id=request.recipient_id,
                    full_name="Unknown User",
                    role="employee",
                    department="unknown",
                    honorific_type=0,
                    communication_mode=0,
                )
        except Exception as e:
            log_error("Failed to get profile", error=str(e))
            profile = retriever_pb2.UserProfile(
                user_id=request.recipient_id,
                full_name="Unknown User",
                role="employee",
                department="unknown",
                honorific_type=0,
                communication_mode=0,
            )

        # Fetch rules with TTL caching
        try:
            rules_response = self.retriever_stub.GetRules(
                retriever_pb2.GetRulesRequest(
                    sender_role="user",  # Default role
                    recipient_role=profile.role if profile.user_id else "",
                    message_text=request.text,
                    limit=5,
                    cache_ttl=300,
                ),
                timeout=5.0,
            )
            track_cache_ttl_hit(cache_type="rules")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                log_error("Retriever rules timeout", error="Deadline exceeded")
                track_grpc_timeout(service="retriever", method="GetRules")
                rules_response = retriever_pb2.GetRulesResponse(rules=[])
            else:
                log_error("Failed to get rules", error=str(e))
                rules_response = retriever_pb2.GetRulesResponse(rules=[])
        except Exception as e:
            log_error("Failed to get rules", error=str(e))
            rules_response = retriever_pb2.GetRulesResponse(rules=[])

        # Fetch style examples with TTL caching
        styles_response = retriever_pb2.GetStyleExamplesResponse()
        if request.style_name:
            try:
                styles_response = self.retriever_stub.GetStyleExamples(
                    retriever_pb2.GetStyleExamplesRequest(
                        style_name=request.style_name, sample_count=3, cache_ttl=86400
                    ),
                    timeout=5.0,
                )
                track_cache_ttl_hit(cache_type="style_examples")
            except grpc.RpcError as e:
                log_error("Failed to get style examples", error=str(e))
                track_cache_ttl_miss(cache_type="style_examples")
                styles_response = retriever_pb2.GetStyleExamplesResponse()
            except Exception as e:
                log_error("Failed to get style examples", error=str(e))
                track_cache_ttl_miss(cache_type="style_examples")
                styles_response = retriever_pb2.GetStyleExamplesResponse()

        # Fetch culture chunks with TTL caching (RAG for corporate culture)
        # Query combining style and recipient profile for better relevance
        culture_query = f"style:{request.style_name} role:{profile.role} department:{profile.department}"

        culture_chunks = []
        try:
            culture_response = self.retriever_stub.SearchCulture(
                retriever_pb2.SearchCultureRequest(
                    query_text=culture_query,
                    limit=3,
                ),
                timeout=5.0,
            )
            culture_chunks = [
                {
                    "text": chunk.text,
                    "section_title": chunk.section_title,
                    "section_level": chunk.section_level,
                    "relevance_score": chunk.relevance_score,
                }
                for chunk in culture_response.chunks
            ]
            log_info("Culture chunks retrieved", count=len(culture_chunks))
        except grpc.RpcError as e:
            log_error("Failed to get culture chunks", error=str(e))
            culture_chunks = []
        except Exception as e:
            log_error("Failed to get culture chunks", error=str(e))
            culture_chunks = []

        # Assemble context with culture chunks
        # Convert protobuf profile to dict for context_assembler
        profile_dict = None
        if profile and profile.user_id:
            profile_dict = {
                "user_id": profile.user_id,
                "full_name": profile.full_name,
                "role": profile.role,
                "department": profile.department,
                "honorific_type": profile.honorific_type,
                "communication_mode": profile.communication_mode,
                "known_triggers": list(profile.known_triggers) if profile.known_triggers else [],
            }
            # Debug logging
            log_info(
                "Profile dict created",
                user_id=profile_dict.get("user_id", ""),
                full_name=profile_dict.get("full_name", ""),
                role=profile_dict.get("role", ""),
                department=profile_dict.get("department", ""),
                honorific_type=profile_dict.get("honorific_type", 0),
                communication_mode=profile_dict.get("communication_mode", 0),
            )
        
        prompt = self.context_assembler.assemble_context(
            original_text=request.text,
            profile=profile_dict,
            rules=list(rules_response.rules),
            styles=list(styles_response.examples) if styles_response.examples else [],
            style_name=request.style_name,
            culture_chunks=culture_chunks,
        )

        # Call LLM Gateway
        llm_gateway_host = os.getenv("LLM_GATEWAY_HOST", "llm-gateway")
        llm_gateway_port = os.getenv("LLM_GATEWAY_PORT", "8003")
        llm_gateway_url = f"http://{llm_gateway_host}:{llm_gateway_port}/generate"

        adapted_text = request.text
        was_adapted = False
        confidence = 0.95
        model_used = ""
        tokens_prompt = 0
        tokens_completion = 0
        processing_time_ms = 100
        fallback_used = False
        fallback_reason = ""
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        llm_gateway_url,
                        json={
                            "prompt": prompt,
                            "complexity": 2,  # BALANCED
                            "config": {
                                "temperature": 0.7,
                                "max_tokens": 2048,
                                "style": request.style_name,
                            },
                        },
                        timeout=aiohttp.ClientTimeout(total=5.0),
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            log_error(
                                "LLM Gateway error",
                                status=response.status,
                                error=error_text,
                                retry=retry_count,
                            )
                            fallback_reason = f"LLM Gateway error: {response.status}"
                            fallback_used = True
                            # Fallback to original text on error
                            adapted_text = request.text
                            if retry_count < max_retries:
                                retry_count += 1
                                log_info("Retrying LLM Gateway call", retry=retry_count)
                                continue
                        else:
                            result = await response.json()
                            adapted_text = result.get("text", request.text)
                            model_used = result.get("model_used", "")
                            tokens_prompt = result.get("token_usage", {}).get(
                                "prompt_tokens", 0
                            )
                            tokens_completion = result.get("token_usage", {}).get(
                                "completion_tokens", 0
                            )
                            processing_time_ms = result.get("latency_ms", 100)
                            was_adapted = adapted_text != request.text

                            log_info(
                                "LLM Gateway call successful",
                                model=model_used,
                                was_adapted=was_adapted,
                            )
                            break

            except aiohttp.ClientError as e:
                log_error(
                    "LLM Gateway connection error", error=str(e), retry=retry_count
                )
                fallback_reason = f"Connection error: {str(e)}"
                fallback_used = True
                adapted_text = request.text
                if retry_count < max_retries:
                    retry_count += 1
                    log_info("Retrying LLM Gateway call", retry=retry_count)
                    continue
            except asyncio.TimeoutError:
                log_error("LLM Gateway timeout", retry=retry_count)
                fallback_reason = "Timeout"
                fallback_used = True
                adapted_text = request.text
                if retry_count < max_retries:
                    retry_count += 1
                    log_info("Retrying LLM Gateway call", retry=retry_count)
                    continue
            except Exception as e:
                log_error("LLM Gateway unknown error", error=str(e), retry=retry_count)
                fallback_reason = f"Unknown error: {str(e)}"
                fallback_used = True
                adapted_text = request.text
                if retry_count < max_retries:
                    retry_count += 1
                    log_info("Retrying LLM Gateway call", retry=retry_count)
                    continue

        # Track metrics
        track_llm_call(
            provider="orchestrator",
            model=model_used or "fallback",
            complexity="balanced",
        )
        track_token_usage(tokens_prompt, tokens_completion)
        track_llm_model_call(model=model_used or "fallback")

        log_info("Orchestrator processing logged to Langfuse")

        # Cache response
        self.cache_manager.set(
            cache_key,
            {
                "adapted_text": adapted_text,
                "was_adapted": was_adapted,
                "confidence": confidence,
                "model_used": model_used,
                "processing_time_ms": processing_time_ms,
                "rules_applied": [rule.rule_id for rule in rules_response.rules],
                "from_cache": False,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
            },
        )

        log_info("Message processed successfully", message_id=message_id)

        # Build final response
        return orchestrator_pb2.ProcessMessageResponse(
            adapted_text=adapted_text,
            was_adapted=was_adapted,
            confidence=confidence,
            model_used=model_used,
            processing_time_ms=processing_time_ms,
            rules_applied=[rule.rule_id for rule in rules_response.rules],
            adaptation_metadata=orchestrator_pb2.AdaptationMetadata(
                from_cache=False,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
            ),
        )

    async def HealthCheck(self, request, context):
        """Health check endpoint."""
        try:
            # Check dependencies
            checks = {"cache": "ok", "retriever": "ok", "llm_gateway": "ok"}

            status = (
                "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
            )

            return common_pb2.HealthStatus(
                status=status, version="1.0.0", checks=checks
            )

        except Exception as e:
            log_error("HealthCheck error", error=str(e))
            return common_pb2.HealthStatus(
                status="unhealthy", version="1.0.0", checks={"error": str(e)}
            )


async def serve():
    """Start async gRPC server."""
    config = get_config()
    port = config.server_port

    # Initialize Langfuse if enabled
    if config.langfuse_enabled:
        init_langfuse_from_config(config)

    server = grpc.aio.server()
    orchestrator_pb2_grpc.add_OrchestratorServiceServicer_to_server(
        OrchestratorService(config), server
    )
    server.add_insecure_port(f"[::]:{port}")

    logger.info(f"Orchestrator server starting on port {port}")
    await server.start()
    logger.info(f"Orchestrator server started on port {port}")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
