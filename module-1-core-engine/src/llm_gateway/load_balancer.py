# Балансировка нагрузки

import time
from typing import Dict, Any, Optional, List
from common.logging import log_warning
from common.metrics import track_llm_fallback


class LoadBalancer:
    """Load balancer for LLM providers with automatic fallback."""

    def __init__(self, fallback_chain: List[str]):
        self.fallback_chain = fallback_chain
        self.provider_status: Dict[str, Dict[str, Any]] = {}
        self._init_provider_status()

    def _init_provider_status(self):
        """Initialize provider status tracking."""
        for entry in self.fallback_chain:
            # Handle models with colons in name (e.g., "llama3.2:3b")
            # Split only on first colon to separate provider from model
            provider, model = entry.split(":", 1)
            self.provider_status[entry] = {
                "success_count": 0,
                "error_count": 0,
                "last_request": None,
                "last_error": None,
                "avg_latency": 0,
                "is_healthy": True,
            }

    def select_provider(self, current_index: int = 0) -> str:
        """Select next provider from fallback chain."""
        if current_index >= len(self.fallback_chain):
            return self.fallback_chain[-1]  # Return last provider (usually API)

        return self.fallback_chain[current_index]

    def record_success(self, provider: str, latency_ms: int):
        """Record successful request."""
        if provider in self.provider_status:
            self.provider_status[provider]["success_count"] += 1
            self.provider_status[provider]["last_request"] = time.time()
            self.provider_status[provider]["is_healthy"] = True

            # Update moving average latency
            current_avg = self.provider_status[provider]["avg_latency"]
            if current_avg == 0:
                self.provider_status[provider]["avg_latency"] = latency_ms
            else:
                self.provider_status[provider]["avg_latency"] = (
                    current_avg * 0.9 + latency_ms * 0.1
                )

    def record_error(self, provider: str, error: str):
        """Record failed request."""
        if provider in self.provider_status:
            self.provider_status[provider]["error_count"] += 1
            self.provider_status[provider]["last_request"] = time.time()
            self.provider_status[provider]["last_error"] = error

            # Mark unhealthy if too many errors
            if self.provider_status[provider]["error_count"] > 5:
                self.provider_status[provider]["is_healthy"] = False
                log_warning("Provider marked unhealthy", provider=provider, error=error)

    def get_best_provider(self) -> str:
        """Get best available provider based on health and latency."""
        for provider in self.fallback_chain:
            status = self.provider_status.get(provider)
            if status and status.get("is_healthy", True):
                return provider
        return self.fallback_chain[-1]

    def fallback(self, current_provider: str, error: str) -> str:
        """Get next provider in fallback chain."""
        try:
            current_idx = self.fallback_chain.index(current_provider)
            next_idx = current_idx + 1

            if next_idx < len(self.fallback_chain):
                next_provider = self.fallback_chain[next_idx]
                track_llm_fallback(
                    from_provider=current_provider.split(":")[0],
                    to_provider=next_provider.split(":")[0],
                )
                return next_provider
            else:
                return current_provider  # Last provider, no more fallback
        except ValueError:
            return current_provider

    def get_status(self) -> Dict[str, Any]:
        """Get load balancer status."""
        return {
            "fallback_chain": self.fallback_chain,
            "provider_status": self.provider_status,
        }


# Global load balancer instance
_load_balancer: Optional[LoadBalancer] = None


def get_load_balancer(fallback_chain: Optional[List[str]] = None) -> LoadBalancer:
    """Get global load balancer instance."""
    global _load_balancer
    if _load_balancer is None:
        if fallback_chain is None:
            raise ValueError("Fallback chain required for first initialization")
        _load_balancer = LoadBalancer(fallback_chain)
    return _load_balancer
