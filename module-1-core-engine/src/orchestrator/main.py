# Orchestrator - HTTP сервер для оркестрации адаптации сообщений

import os
import sys
import httpx
import asyncio
import uvicorn
from typing import Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
from common.validator import InputValidator, normalize_style_name
from common.langfuse_integration import (
    init_langfuse_from_config,
    log_generation,
)
from common.schemas import MessageRequest, MessageResponse, AdaptationMetadata, ClassificationResult

from .cache_manager import get_cache_manager
from .classifier import get_classifier
from .context_assembler import get_context_assembler
from .config import get_config, Config


# FastAPI app
app = FastAPI(
    title="Chameleon Orchestrator",
    description="Orchestrator service for message adaptation",
    version="1.0.0",
)

class ProcessMessageRequest(BaseModel):
    """Request model for process message endpoint."""
    message_id: str
    sender_id: str
    recipient_id: str
    room_id: Optional[str] = None
    text: str
    style_name: Optional[str] = None
    metadata: Dict[str, str] = {}


class ProcessMessageResponse(BaseModel):
    """Response model for process message endpoint."""
    adapted_text: str
    was_adapted: bool
    confidence: float
    model_used: str
    processing_time_ms: int
    rules_applied: list
    adaptation_metadata: AdaptationMetadata


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    checks: Dict[str, str]


# Global instances
_config: Optional[Config] = None
_cache_manager = None
_context_assembler = None
_classifier = None
_http_client = None
_retriever_url: str = None
_llm_gateway_url: str = None


def get_config_instance() -> Config:
    """Get config instance."""
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_cache_manager_instance():
    """Get cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        config = get_config_instance()
        redis_password = os.getenv(
            "REDIS_PASSWORD",
            config.redis_password if hasattr(config, "redis_password") else None,
        )
        _cache_manager = get_cache_manager(
            host=config.redis_host,
            port=config.redis_port,
            ttl=config.cache_ttl,
            password=redis_password,
        )
    return _cache_manager


def get_classifier_instance():
    """Get classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = get_classifier()
    return _classifier


def get_context_assembler_instance():
    """Get context assembler instance."""
    global _context_assembler
    if _context_assembler is None:
        _context_assembler = get_context_assembler()
    return _context_assembler


def get_http_client():
    """Get async HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


def get_retriever_url() -> str:
    """Get Retriever HTTP URL."""
    global _retriever_url
    if _retriever_url is None:
        config = get_config_instance()
        retriever_host = os.getenv("RETRIEVER_HOST", "retriever")
        retriever_port = os.getenv("RETRIEVER_PORT", "8002")
        _retriever_url = f"http://{retriever_host}:{retriever_port}"
    return _retriever_url


def get_llm_gateway_url() -> str:
    """Get LLM Gateway HTTP URL."""
    global _llm_gateway_url
    if _llm_gateway_url is None:
        config = get_config_instance()
        llm_gateway_host = os.getenv("LLM_GATEWAY_HOST", "llm-gateway")
        llm_gateway_port = os.getenv("LLM_GATEWAY_PORT", "8003")
        _llm_gateway_url = f"http://{llm_gateway_host}:{llm_gateway_port}"
    return _llm_gateway_url


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    config = get_config_instance()
    
    # Initialize Langfuse if enabled
    if config.langfuse_enabled:
        init_langfuse_from_config(config)
    
    log_info("Orchestrator HTTP server starting")
    
    # Verify connections
    await verify_connections()


async def verify_connections():
    """Verify connections to dependent services."""
    try:
        retriever_url = get_retriever_url()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{retriever_url}/health", timeout=5.0)
            if response.status_code == 200:
                log_info("Retriever connection verified", url=retriever_url)
            else:
                log_error("Retriever returned unexpected status", status=response.status_code)
    except httpx.RequestError as e:
        log_error("Failed to connect to Retriever", error=str(e))
    
    try:
        llm_gateway_url = get_llm_gateway_url()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{llm_gateway_url}/health", timeout=5.0)
            if response.status_code == 200:
                log_info("LLM Gateway connection verified", url=llm_gateway_url)
            else:
                log_error("LLM Gateway returned unexpected status", status=response.status_code)
    except httpx.RequestError as e:
        log_error("Failed to connect to LLM Gateway", error=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    checks = {"cache": "ok"}
    status = "healthy"
    
    # Check Retriever
    try:
        retriever_url = get_retriever_url()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{retriever_url}/health", timeout=5.0)
            if response.status_code == 200:
                checks["retriever"] = "ok"
            else:
                checks["retriever"] = f"error: {response.status_code}"
                status = "degraded"
    except httpx.RequestError as e:
        checks["retriever"] = f"error: {str(e)}"
        status = "degraded"
    
    # Check LLM Gateway
    try:
        llm_gateway_url = get_llm_gateway_url()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{llm_gateway_url}/health", timeout=5.0)
            if response.status_code == 200:
                checks["llm_gateway"] = "ok"
            else:
                checks["llm_gateway"] = f"error: {response.status_code}"
                status = "degraded"
    except httpx.RequestError as e:
        checks["llm_gateway"] = f"error: {str(e)}"
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        checks=checks
    )


@app.post("/api/v1/messages/process", response_model=ProcessMessageResponse)
async def process_message(request: ProcessMessageRequest):
    """Process incoming message and return adapted version."""
    message_id = request.message_id
    
    # Normalize style_name from Russian to English
    normalized_style_name = normalize_style_name(request.style_name)
    
    log_info("Processing message", message_id=message_id)

    # Validate input first
    is_valid, error = InputValidator.validate_message({
        "message_id": message_id,
        "sender_id": request.sender_id,
        "recipient_id": request.recipient_id,
        "text": request.text,
        "style_name": normalized_style_name,
    })
    if not is_valid:
        log_error("Invalid message input", error=error)
        raise HTTPException(status_code=400, detail=error)

    # Classify message (before cache check)
    classification_result: Optional[ClassificationResult] = None
    try:
        classifier = get_classifier_instance()
        classification_result = await classifier.classify_message(request.text)
        log_info("Message classified", category=classification_result.category if classification_result else "none")
    except Exception as e:
        log_error("Failed to classify message", error=str(e))
        # Fallback to unknown classification
        import time
        classification_result = ClassificationResult(
            category="неизвестно",
            category_code="unknown",
            confidence=0.5,
            processed_at=int(time.time() * 1000)
        )

    # Use context manager to ensure trace is properly ended
    with log_generation(
        name=f"orchestrator-process-{message_id}",
        model="orchestrator",
        prompt=f"Processing message {message_id}",
        completion="Orchestrator processing complete",
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        metadata={
            "message_id": message_id,
            "sender_id": request.sender_id,
            "recipient_id": request.recipient_id,
            "has_style": bool(normalized_style_name),
        },
    ):
        # Check cache
        cache_manager = get_cache_manager_instance()
        cache_key = cache_manager.generate_key(
            message_id=request.message_id,
            text=request.text,
            recipient_id=request.recipient_id,
            rules=[],
        )

        cached = cache_manager.get(cache_key)
        if cached:
            log_info("Cache hit for message", message_id=message_id)
            track_cache_hit(cache_type="orchestrator")
            
            # Log cache hit to Langfuse
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
            
            return ProcessMessageResponse(
                adapted_text=cached["adapted_text"],
                was_adapted=cached["was_adapted"],
                confidence=cached.get("confidence", 0.0),
                model_used=cached.get("model_used", ""),
                processing_time_ms=cached.get("processing_time_ms", 0),
                rules_applied=cached.get("rules_applied", []),
                adaptation_metadata=AdaptationMetadata(
                    from_cache=True,
                    fallback_used=cached.get("from_cache", False),
                    fallback_reason=cached.get("fallback_reason", ""),
                    tokens_prompt=cached.get("tokens_prompt", 0),
                    tokens_completion=cached.get("tokens_completion", 0),
                ),
            )

        # Fetch profile via HTTP
        profile = None
        try:
            retriever_url = get_retriever_url()
            http_client = get_http_client()
            response = await http_client.get(
                f"{retriever_url}/api/v1/profiles/{request.recipient_id}",
                timeout=5.0,
            )
            if response.status_code == 200:
                profile = response.json().get("profile")
                track_cache_ttl_hit(cache_type="profile")
                log_info("Profile retrieved via HTTP", user_id=request.recipient_id)
            else:
                log_info("Profile not found via HTTP", user_id=request.recipient_id)
                track_cache_ttl_miss(cache_type="profile")
        except httpx.RequestError as e:
            log_error("Failed to get profile via HTTP", error=str(e))
            track_cache_ttl_miss(cache_type="profile")

        # Fetch rules via HTTP
        rules = []
        try:
            retriever_url = get_retriever_url()
            http_client = get_http_client()
            # Получаем роль получателя
            recipient_role = profile.get('role', '') if profile else ''
            log_info("Fetching rules", recipient_role=recipient_role)
            # Формируем запрос без text параметра (не используется в Retriever)
            rules_url = f"{retriever_url}/api/v1/rules?sender_role=user&recipient_role={recipient_role}&limit=5"
            response = await http_client.get(rules_url, timeout=5.0)
            if response.status_code == 200:
                rules = response.json().get("rules", [])
                track_cache_ttl_hit(cache_type="rules")
                log_info("Rules retrieved", count=len(rules), recipient_role=recipient_role)
            else:
                log_error("Failed to get rules via HTTP", status=response.status_code)
                track_cache_ttl_miss(cache_type="rules")
        except httpx.RequestError as e:
            log_error("Failed to get rules via HTTP", error=str(e))
            track_cache_ttl_miss(cache_type="rules")

        # Fetch style examples via HTTP
        styles = []
        if normalized_style_name:
            try:
                retriever_url = get_retriever_url()
                http_client = get_http_client()
                response = await http_client.get(
                    f"{retriever_url}/api/v1/styles/examples?style_name={normalized_style_name}&sample_count=3",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    styles = response.json().get("examples", [])
                    track_cache_ttl_hit(cache_type="style_examples")
            except httpx.RequestError as e:
                log_error("Failed to get style examples via HTTP", error=str(e))

        # Fetch culture chunks via HTTP
        culture_chunks = []
        try:
            # Формируем семантический запрос с учетом стиля и роли
            culture_query_parts = []
            if normalized_style_name:
                culture_query_parts.append(f"стиль {normalized_style_name}")
            if profile:
                if profile.get('role'):
                    culture_query_parts.append(f"роль {profile.get('role')}")
                if profile.get('department'):
                    culture_query_parts.append(f"отдел {profile.get('department')}")
            # Add classification category to query if available
            if classification_result and classification_result.category != "неизвестно":
                culture_query_parts.append(classification_result.category)
            culture_query = " ".join(culture_query_parts) if culture_query_parts else request.text
            
            retriever_url = get_retriever_url()
            http_client = get_http_client()
            # Pass classification category to retriever
            category_param = classification_result.category if classification_result and classification_result.category != "неизвестно" else ""
            response = await http_client.get(
                f"{retriever_url}/api/v1/culture/search?query={culture_query}&limit=3&category={category_param}",
                timeout=5.0,
            )
            if response.status_code == 200:
                culture_chunks = response.json().get("chunks", [])
                log_info("Culture chunks retrieved via HTTP", count=len(culture_chunks), category=category_param)
        except httpx.RequestError as e:
            log_error("Failed to get culture chunks via HTTP", error=str(e))

        # Assemble context
        context_assembler = get_context_assembler_instance()
        prompt = context_assembler.assemble_context(
            original_text=request.text,
            profile=profile,
            rules=rules,
            styles=styles,
            style_name=normalized_style_name,
            culture_chunks=culture_chunks,
            classification_result=classification_result,
        )

        # Call LLM Gateway via HTTP
        llm_gateway_url = get_llm_gateway_url()
        http_client = get_http_client()
        
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
                response = await http_client.post(
                    f"{llm_gateway_url}/generate",
                    json={
                        "prompt": prompt,
                        "complexity": 2,  # BALANCED
                        "config": {
                            "temperature": 0.7,
                            "max_tokens": 2048,
                            "style": normalized_style_name,
                        },
                    },
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    log_error(
                        "LLM Gateway error",
                        status=response.status_code,
                        error=error_text,
                        retry=retry_count,
                    )
                    fallback_reason = f"LLM Gateway error: {response.status_code}"
                    fallback_used = True
                    adapted_text = request.text
                    if retry_count < max_retries:
                        retry_count += 1
                        continue
                else:
                    result = response.json()
                    adapted_text = result.get("text", request.text)
                    model_used = result.get("model_used", "")
                    tokens_prompt = result.get("token_usage", {}).get("prompt_tokens", 0)
                    tokens_completion = result.get("token_usage", {}).get("completion_tokens", 0)
                    processing_time_ms = result.get("latency_ms", 100)
                    was_adapted = adapted_text != request.text

                    log_info(
                        "LLM Gateway call successful",
                        model=model_used,
                        was_adapted=was_adapted,
                    )
                    break

            except httpx.RequestError as e:
                log_error("LLM Gateway connection error", error=str(e), retry=retry_count)
                fallback_reason = f"Connection error: {str(e)}"
                fallback_used = True
                adapted_text = request.text
                if retry_count < max_retries:
                    retry_count += 1
                    continue
            except Exception as e:
                log_error("LLM Gateway unknown error", error=str(e), retry=retry_count)
                fallback_reason = f"Unknown error: {str(e)}"
                fallback_used = True
                adapted_text = request.text
                if retry_count < max_retries:
                    retry_count += 1
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
        cache_manager = get_cache_manager_instance()
        cache_manager.set(
            cache_key,
            {
                "adapted_text": adapted_text,
                "was_adapted": was_adapted,
                "confidence": confidence,
                "model_used": model_used,
                "processing_time_ms": processing_time_ms,
                "rules_applied": [rule.get("rule_id", "") for rule in rules],
                "from_cache": False,
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
            },
        )

        log_info("Message processed successfully", message_id=message_id)

        return ProcessMessageResponse(
            adapted_text=adapted_text,
            was_adapted=was_adapted,
            confidence=confidence,
            model_used=model_used,
            processing_time_ms=processing_time_ms,
            rules_applied=[rule.get("rule_id", "") for rule in rules],
            adaptation_metadata=AdaptationMetadata(
                from_cache=False,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
                tokens_prompt=tokens_prompt,
                tokens_completion=tokens_completion,
            ),
        )


@app.get("/api/v1/health", response_model=HealthResponse)
async def api_health_check():
    """API health check endpoint."""
    return await health_check()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    log_info(f"Starting Orchestrator HTTP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
