# LLM Gateway - HTTP сервер для управления LLM

import os
import sys
import yaml
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import common modules
from common.logging import logger, log_info, log_error
from common.metrics import measure_latency
from common.schemas import (
    GenerationConfig,
    ModelComplexity,
)
from common.langfuse_integration import init_langfuse, log_generation
from .providers.base import LLMProvider
from .providers.ollama_provider import OllamaProvider
from .providers.yandex_provider import YandexProvider
from .router import get_router, Router
from .cache import get_cache, LLMCache
from .load_balancer import get_load_balancer, LoadBalancer
from .circuit_breaker import CircuitBreaker

# FastAPI app
app = FastAPI(
    title="Chameleon LLM Gateway",
    description="LLM model router and cache",
    version="1.0.0",
)

# Global instances
_router: Optional[Router] = None
_cache: Optional[LLMCache] = None
_load_balancer: Optional[LoadBalancer] = None
_circuit_breaker: Optional[CircuitBreaker] = None
_provider_map: Dict[str, LLMProvider] = {}
_fallback_chain: list = []


class GenerateRequest(BaseModel):
    """Request model for generate endpoint."""

    prompt: str
    complexity: int = ModelComplexity.BALANCED
    config: Optional[GenerationConfig] = None


class GenerateResponse(BaseModel):
    """Response model for generate endpoint."""

    text: str
    model_used: str
    complexity_used: int
    token_usage: Dict[str, int]
    latency_ms: int
    from_cache: bool


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    checks: Dict[str, str]


def init_components():
    """Initialize all components."""
    global _router, _cache, _load_balancer, _circuit_breaker, _provider_map, _fallback_chain

    # Load config
    config_path = os.getenv("CONFIG_PATH", "config/development.yaml")
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config not found: {config_path}, using defaults")
        config = {}

    # Initialize circuit breaker
    cb_config = config.get("circuit_breaker", {})
    _circuit_breaker = CircuitBreaker(
        failure_threshold=cb_config.get("failure_threshold", 5),
        recovery_timeout=cb_config.get("recovery_timeout", 30),
    )

    # Initialize router with circuit breaker
    _fallback_chain = config.get("fallback", {}).get(
        "chain", ["ollama:qwen2.5:1.5b", "yandex:ya-llm"]
    )
    _router = get_router(
        config={"fallback_chain": _fallback_chain},
        circuit_breaker=_circuit_breaker,
    )

    # Initialize cache
    redis_host = os.getenv(
        "REDIS_HOST", config.get("services", {}).get("redis", {}).get("host", "redis")
    )
    redis_port = int(
        os.getenv(
            "REDIS_PORT", config.get("services", {}).get("redis", {}).get("port", 6379)
        )
    )
    redis_password = os.getenv(
        "REDIS_PASSWORD", config.get("services", {}).get("redis", {}).get("password")
    )
    cache_ttl = int(
        os.getenv("CACHE_TTL", config.get("cache", {}).get("default_ttl", 3600))
    )
    _cache = get_cache(
        host=redis_host, port=redis_port, ttl=cache_ttl, password=redis_password
    )

    # Initialize load balancer
    _load_balancer = get_load_balancer(fallback_chain=_fallback_chain)

    # Initialize providers
    _provider_map = {}
    for provider_entry in _fallback_chain:
        try:
            provider, model = provider_entry.split(":", 1)
            if provider == "ollama":
                provider_config = {
                    "host": config.get("services", {})
                    .get("ollama", {})
                    .get("host", "localhost"),
                    "port": config.get("services", {})
                    .get("ollama", {})
                    .get("port", 11434),
                    "model_name": model,
                    "timeout": config.get("services", {})
                    .get("ollama", {})
                    .get("timeout", 30),
                }
                _provider_map[provider_entry] = OllamaProvider(provider_config)
            elif provider == "yandex":
                provider_config = {
                    "model_name": model,
                    "timeout": config.get("services", {})
                    .get("yandex", {})
                    .get("timeout", 60),
                }
                _provider_map[provider_entry] = YandexProvider(provider_config)
            else:
                continue

            # Set circuit breaker for provider
            if _circuit_breaker:
                _provider_map[provider_entry].set_circuit_breaker(_circuit_breaker)

        except Exception as e:
            log_error(
                "Failed to initialize provider", provider=provider_entry, error=str(e)
            )


def get_provider(model: str) -> Optional[LLMProvider]:
    """Get provider by model identifier."""
    return _provider_map.get(model)


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    try:
        init_langfuse()
        init_components()
        log_info("LLM Gateway started")
    except Exception as e:
        log_error("Failed to initialize LLM Gateway", error=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    checks = {}
    status = "healthy"

    # Check providers
    for provider_key, provider in _provider_map.items():
        try:
            result = await provider.health_check()
            checks[provider_key] = "ok" if result else "error"
            if not result:
                status = "degraded"
        except Exception as e:
            checks[provider_key] = f"error: {e}"
            status = "degraded"

    # Check cache connection
    try:
        if _cache:
            _cache.client.ping()
            checks["cache"] = "ok"
        else:
            checks["cache"] = "not_initialized"
            status = "degraded"
    except Exception as e:
        checks["cache"] = f"error: {e}"
        status = "degraded"

    return HealthResponse(status=status, version="1.0.0", checks=checks)


@app.post("/generate", response_model=GenerateResponse)
@measure_latency(service="llm_gateway", endpoint="/generate")
async def generate(request: GenerateRequest):
    """Generate text using appropriate model."""
    try:
        # Route request to appropriate model
        model = _router.route_request(
            complexity=request.complexity,
            prompt_length=len(request.prompt),
            has_style=request.config.style if request.config else False,
        )

        # Check cache first
        cache_config = {
            "temperature": request.config.temperature if request.config else 0.7,
            "max_tokens": request.config.max_tokens if request.config else 2048,
        }

        cached = _cache.get(request.prompt, model, cache_config)
        if cached:
            log_info("Cache hit for generate", model=model)
            
            # Log cache hit to Langfuse
            try:
                with log_generation(
                    name="generation-cache-hit",
                    model=model,
                    prompt=request.prompt,
                    completion=cached["text"],
                    usage=cached.get(
                        "token_usage",
                        {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    ),
                    metadata={
                        "from_cache": True,
                        "latency_ms": cached.get("latency_ms", 0),
                    },
                ):
                    pass  # Generation is logged within the context
            except Exception as e:
                log_error("Failed to log cache hit to Langfuse", error=str(e))
            
            return GenerateResponse(
                text=cached["text"],
                model_used=model,
                complexity_used=request.complexity,
                token_usage=cached.get(
                    "token_usage",
                    {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                ),
                latency_ms=cached.get("latency_ms", 0),
                from_cache=True,
            )

        # Get provider and generate with fallback support
        provider = get_provider(model)
        if not provider:
            raise HTTPException(status_code=500, detail=f"Provider not found: {model}")

        config = GenerationConfig(
            temperature=request.config.temperature if request.config else 0.7,
            max_tokens=request.config.max_tokens if request.config else 2048,
            stream=False,
        )

        # Generate with fallback support
        response = None
        current_model = model
        max_retries = len(_fallback_chain)

        for attempt in range(max_retries):
            try:
                provider = get_provider(current_model)
                if not provider:
                    log_info(
                        "Provider not found, using fallback", provider=current_model
                    )
                    current_model = _load_balancer.fallback(
                        current_model, "Provider not found"
                    )
                    continue

                response = await provider.generate(request.prompt, config)
                _load_balancer.record_success(current_model, response.latency_ms)
                log_info(
                    "LLM generation successful",
                    model=current_model,
                    latency_ms=response.latency_ms,
                )

                # Log generation to Langfuse
                try:
                    with log_generation(
                        name=f"generation-{current_model}",
                        model=current_model,
                        prompt=request.prompt,
                        completion=response.text,
                        usage=response.token_usage,
                        metadata={
                            "provider": (
                                current_model.split(":")[0]
                                if ":" in current_model
                                else "unknown"
                            )
                        },
                    ):
                        pass  # Generation is logged within the context
                except Exception as e:
                    log_error("Failed to log to Langfuse", error=str(e))

                break

            except Exception as e:
                _load_balancer.record_error(current_model, str(e))
                log_error("LLM generation failed", model=current_model, error=str(e))

                # Try next provider in fallback chain
                if attempt < max_retries - 1:
                    current_model = _load_balancer.fallback(current_model, str(e))
                    log_info("Falling back to next provider", provider=current_model)
                    continue
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"All fallback providers failed: {str(e)}",
                    )

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to generate response")

        # Cache response
        _cache.set(
            request.prompt,
            model,
            cache_config,
            {
                "text": response.text,
                "latency_ms": response.latency_ms,
                "token_usage": response.token_usage,
            },
        )

        return GenerateResponse(
            text=response.text,
            model_used=model,
            complexity_used=request.complexity,
            token_usage=response.token_usage,
            latency_ms=response.latency_ms,
            from_cache=False,
        )

    except Exception as e:
        logger.error(f"Generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=Dict[str, str])
async def get_models():
    """Get list of available models."""
    return _router.get_available_models()


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8003))

    uvicorn.run(app, host="0.0.0.0", port=port)
