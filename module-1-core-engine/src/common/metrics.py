# Prometheus метрики

import asyncio
import functools
from prometheus_client import Counter, Histogram, Gauge, Summary
import time


# ===== Request Counters =====
requests_total = Counter(
    "chameleon_requests_total",
    "Total number of requests",
    ["service", "endpoint", "method"],
)

requests_failed = Counter(
    "chameleon_requests_failed",
    "Number of failed requests",
    ["service", "endpoint", "error_type"],
)

# ===== Latency Histograms =====
request_latency = Histogram(
    "chameleon_request_latency_seconds",
    "Request latency in seconds",
    ["service", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0, 10.0],
)

# ===== Cache Metrics =====
cache_hits = Counter(
    "chameleon_cache_hits_total", "Number of cache hits", ["cache_type"]
)

cache_misses = Counter(
    "chameleon_cache_misses_total", "Number of cache misses", ["cache_type"]
)

cache_size = Gauge("chameleon_cache_size", "Current cache size", ["cache_type"])

# ===== LLM Metrics =====
llm_calls = Counter(
    "chameleon_llm_calls_total",
    "Number of LLM calls",
    ["provider", "model", "complexity"],
)

llm_latency = Histogram(
    "chameleon_llm_latency_seconds",
    "LLM inference latency in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

llm_fallbacks = Counter(
    "chameleon_llm_fallbacks_total",
    "Number of LLM fallbacks",
    ["from_provider", "to_provider"],
)

# ===== Token Usage =====
token_usage = Summary(
    "chameleon_token_usage",
    "Token usage for LLM calls",
    ["prompt_completion"],  # 'prompt', 'completion', 'total'
)

# ===== Cache TTL Metrics =====
cache_ttl_hits = Counter(
    "chameleon_cache_ttl_hits_total", "Number of cache TTL hits", ["cache_type"]
)

cache_ttl_misses = Counter(
    "chameleon_cache_ttl_misses_total", "Number of cache TTL misses", ["cache_type"]
)

# ===== gRPC Timeout Metrics =====
grpc_timeouts = Counter(
    "chameleon_grpc_timeouts_total", "Number of gRPC timeouts", ["service", "method"]
)

# ===== LLM Model Metrics =====
llm_model_calls = Counter(
    "chameleon_llm_model_calls_total", "Number of LLM calls per model", ["model"]
)

# ===== Service Status =====
service_status = Gauge(
    "chameleon_service_status", "Service status (1=healthy, 0=unhealthy)", ["service"]
)

# ===== Helper functions =====


def measure_latency(service: str, endpoint: str):
    """Decorator to measure latency."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                request_latency.labels(service=service, endpoint=endpoint).observe(
                    time.time() - start_time
                )
                return result
            except Exception:
                request_latency.labels(service=service, endpoint=endpoint).observe(
                    time.time() - start_time
                )
                raise

        return wrapper

    return decorator


def track_cache_hit(cache_type: str):
    """Track cache hit."""
    cache_hits.labels(cache_type=cache_type).inc()


def track_cache_miss(cache_type: str):
    """Track cache miss."""
    cache_misses.labels(cache_type=cache_type).inc()


def track_llm_fallback(from_provider: str, to_provider: str):
    """Track LLM fallback."""
    llm_fallbacks.labels(from_provider=from_provider, to_provider=to_provider).inc()


def track_llm_call(provider: str, model: str, complexity: str):
    """Track LLM call."""
    llm_calls.labels(provider=provider, model=model, complexity=complexity).inc()


def track_token_usage(prompt_tokens: int, completion_tokens: int):
    """Track token usage."""
    token_usage.labels(prompt_completion="prompt").observe(prompt_tokens)
    token_usage.labels(prompt_completion="completion").observe(completion_tokens)
    token_usage.labels(prompt_completion="total").observe(
        prompt_tokens + completion_tokens
    )


def track_cache_ttl_hit(cache_type: str):
    """Track cache TTL hit."""
    cache_ttl_hits.labels(cache_type=cache_type).inc()


def track_cache_ttl_miss(cache_type: str):
    """Track cache TTL miss."""
    cache_ttl_misses.labels(cache_type=cache_type).inc()


def track_grpc_timeout(service: str, method: str):
    """Track gRPC timeout."""
    grpc_timeouts.labels(service=service, method=method).inc()


def track_llm_model_call(model: str):
    """Track LLM model call."""
    llm_model_calls.labels(model=model).inc()
