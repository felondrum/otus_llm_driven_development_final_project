# Retriever - gRPC сервер для RAG операций

import os
import sys
import grpc
import asyncio

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chameleon.core.v1.retriever_pb2 as retriever_pb2
import chameleon.core.v1.retriever_pb2_grpc as retriever_pb2_grpc
import chameleon.core.v1.common_pb2 as common_pb2
from common.logging import logger, log_error, log_info
from common.metrics import track_cache_ttl_hit, track_cache_ttl_miss
from common.langfuse_integration import (
    init_langfuse,
    log_generation,
)

from .qdrant_client import get_qdrant_client
from .embeddings import get_embedder
from .hybrid_search import get_searcher


class RetrieverService(retriever_pb2_grpc.RetrieverServiceServicer):
    """gRPC service implementation for Retriever."""

    def __init__(self):
        self.qdrant = get_qdrant_client()
        self.embedder = get_embedder()
        self.searcher = get_searcher()

    async def GetProfile(self, request, context):
        """Get user profile by user_id."""
        # Log to Langfuse without span context for simplicity
        try:
            with log_generation(
                name="retriever-get-profile",
                model="qdrant",
                prompt=f"Get profile for user_id: {request.user_id}",
                completion="Profile retrieved",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "user_id": request.user_id,
                },
            ):
                pass  # Generation is logged within the context manager
        except Exception as e:
            log_error("Failed to log to Langfuse", error=str(e))

        # Debug logging
        log_info(
            "GetProfile request",
            user_id=request.user_id,
            is_uuid5=len(request.user_id) == 36 and request.user_id.count('-') == 4
        )

        profile = self.qdrant.get_profile(request.user_id)

        if not profile:
            log_info("Profile not found", user_id=request.user_id)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Profile not found: {request.user_id}")
            track_cache_ttl_miss(cache_type="profile")
            return retriever_pb2.UserProfile()

        log_info("Profile found", user_id=request.user_id)
        track_cache_ttl_hit(cache_type="profile")
        
        # Debug logging
        log_info(
            "Profile data",
            user_id=profile.get("user_id", ""),
            role=profile.get("role", ""),
            department=profile.get("department", ""),
            honorific_type=profile.get("honorific_type", 0),
            communication_mode=profile.get("communication_mode", 0),
        )

        # Get profile with mapped values (honorific_type and communication_mode are already converted to integers)
        return retriever_pb2.UserProfile(
            user_id=profile.get("user_id", ""),
            full_name=profile.get("full_name", ""),
            role=profile.get("role", ""),
            department=profile.get("department", ""),
            honorific_type=profile.get("honorific_type", 0),
            communication_mode=profile.get("communication_mode", 0),
            known_triggers=profile.get("known_triggers", []),
            adaptive_history_vector=profile.get("adaptive_history_vector", []),
            last_updated=profile.get("last_updated", 0),
        )

    async def GetRules(self, request, context):
        """Get corporate rules by sender and recipient roles."""
        # Log to Langfuse without span context
        try:
            with log_generation(
                name="retriever-get-rules",
                model="qdrant",
                prompt=f"Get rules for sender={request.sender_role}, recipient={request.recipient_role}",
                completion=f"Rules retrieved: limit={request.limit}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "sender_role": request.sender_role,
                    "recipient_role": request.recipient_role,
                    "limit": request.limit,
                },
            ):
                pass  # Generation is logged within the context manager
        except Exception as e:
            log_error("Failed to log to Langfuse", error=str(e))

        rules = await self.qdrant.get_rules(
            sender_role=request.sender_role,
            recipient_role=request.recipient_role,
            limit=request.limit,
        )
        track_cache_ttl_hit(cache_type="rules")

        corporate_rules = []
        for rule in rules:
            corporate_rules.append(
                retriever_pb2.CorporateRule(
                    rule_id=rule.get("rule_id", ""),
                    category=rule.get("category", ""),
                    priority=rule.get("priority", 0),
                    transformation_prompt=rule.get("transformation_prompt", ""),
                    example_original=rule.get("example_original", ""),
                    example_adapted=rule.get("example_adapted", ""),
                    relevance_score=rule.get("relevance_score", 0.0),
                )
            )

        return retriever_pb2.GetRulesResponse(rules=corporate_rules)

    async def GetStyleExamples(self, request, context):
        """Get examples of artistic styles."""
        # Log to Langfuse without span context
        try:
            with log_generation(
                name="retriever-get-styles",
                model="qdrant",
                prompt=f"Get style examples for style_name={request.style_name}",
                completion=f"Styles retrieved: sample_count={request.sample_count}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "style_name": request.style_name,
                    "sample_count": request.sample_count,
                },
            ):
                pass  # Generation is logged within the context manager
        except Exception as e:
            log_error("Failed to log to Langfuse", error=str(e))

        styles = self.qdrant.get_style_examples(
            style_name=request.style_name, sample_count=request.sample_count
        )
        track_cache_ttl_hit(cache_type="style_examples")

        style_examples = []
        for style in styles:
            style_examples.append(
                retriever_pb2.StyleExample(
                    style_name=style.get("style_name", ""),
                    author=style.get("author", ""),
                    sample_text=style.get("sample_text", ""),
                    metadata=style.get("metadata", {}),
                )
            )

        return retriever_pb2.GetStyleExamplesResponse(examples=style_examples)

    async def SearchRules(self, request, context):
        """Search rules by query text."""
        # Log to Langfuse without span context
        try:
            with log_generation(
                name="retriever-search-rules",
                model="qdrant",
                prompt=f"Search rules for query={request.query_text[:100]}",
                completion=f"Rules searched for sender={request.sender_role}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "query_text": request.query_text,
                    "sender_role": request.sender_role,
                },
            ):
                pass  # Generation is logged within the context manager
        except Exception as e:
            log_error("Failed to log to Langfuse", error=str(e))

        # Generate embedding for query
        query_vector = await self.embedder.generate_embedding(request.query_text)
        if not query_vector:
            log_error("Failed to generate embedding", query_text=request.query_text)
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Failed to generate embedding")
            return retriever_pb2.SearchRulesResponse(rules=[])

        # Search rules
        rules = self.qdrant.search_rules(
            query_vector=query_vector,
            sender_role=request.sender_role,
            recipient_role=request.recipient_role,
            limit=request.limit,
        )
        track_cache_ttl_hit(cache_type="rules")

        corporate_rules = []
        for rule in rules:
            corporate_rules.append(
                retriever_pb2.CorporateRule(
                    rule_id=rule.get("rule_id", ""),
                    category=rule.get("category", ""),
                    priority=rule.get("priority", 0),
                    transformation_prompt=rule.get("transformation_prompt", ""),
                    example_original=rule.get("example_original", ""),
                    example_adapted=rule.get("example_adapted", ""),
                    relevance_score=rule.get("relevance_score", 0.0),
                )
            )

        return retriever_pb2.SearchRulesResponse(rules=corporate_rules)

    async def SearchCulture(self, request, context):
        """Search for culture chunks by query text."""
        # Log to Langfuse without span context
        try:
            with log_generation(
                name="retriever-search-culture",
                model="qdrant",
                prompt=f"Search culture for query={request.query_text[:100]}",
                completion=f"Culture chunks retrieved: limit={request.limit}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={
                    "query_text": request.query_text,
                    "limit": request.limit,
                },
            ):
                pass  # Generation is logged within the context manager
        except Exception as e:
            log_error("Failed to log to Langfuse", error=str(e))

        # Search culture chunks
        chunks = await self.qdrant.get_culture_chunks(
            query_text=request.query_text,
            limit=request.limit,
        )
        track_cache_ttl_hit(cache_type="culture_chunks")

        culture_chunks = []
        for chunk in chunks:
            culture_chunks.append(
                retriever_pb2.CultureChunk(
                    text=chunk.get("text", ""),
                    section_title=chunk.get("section_title", ""),
                    section_level=chunk.get("section_level", 0),
                    relevance_score=chunk.get("relevance_score", 0.0),
                )
            )

        return retriever_pb2.SearchCultureResponse(chunks=culture_chunks)

    async def HealthCheck(self, request, context):
        """Health check endpoint."""
        try:
            # Check Qdrant connection
            self.qdrant.client.get_collections()

            # Check embedder
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            embedder_ok = await embedder.health_check()

            checks = {"qdrant": "ok", "embedder": "ok" if embedder_ok else "error"}

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
    port = int(os.getenv("PORT", 8002))

    # Initialize Langfuse if enabled
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://langfuse-web:3000")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "local-key")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "local-secret")
    
    # Always initialize Langfuse with OTLP exporter
    # The SDK will send data to langfuse-worker via OTLP regardless of keys
    init_langfuse(
        public_key=langfuse_public_key,
        secret_key=langfuse_secret_key,
        host=langfuse_host,
    )

    server = grpc.aio.server()
    retriever_pb2_grpc.add_RetrieverServiceServicer_to_server(
        RetrieverService(), server
    )
    server.add_insecure_port(f"[::]:{port}")

    logger.info(f"Retriever server starting on port {port}")
    await server.start()
    logger.info(f"Retriever server started on port {port}")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
