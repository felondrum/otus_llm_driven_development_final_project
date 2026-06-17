# Circuit Breaker for LLM providers

import time
from typing import Any, Dict
from common.logging import logger


class CircuitBreaker:
    """Circuit breaker for LLM providers to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # State per provider
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, float] = {}
        self.success_counts: Dict[str, int] = {}
        self.half_open_calls: Dict[str, int] = {}

    def is_open(self, provider: str) -> bool:
        """Check if circuit is open (should fallback)."""
        if provider not in self.failure_counts:
            return False

        if self.failure_counts[provider] >= self.failure_threshold:
            last_failure = self.last_failure_times.get(provider, 0)
            time_since_failure = time.time() - last_failure

            if time_since_failure >= self.recovery_timeout:
                # Transition to half-open state
                self.half_open_calls[provider] = 0
                logger.info(
                    f"Circuit breaker for {provider} transitioning to half-open state"
                )
                return False

            return True

        return False

    def record_success(self, provider: str):
        """Record a successful call."""
        if provider in self.failure_counts:
            self.failure_counts[provider] = 0

        if provider in self.success_counts:
            self.success_counts[provider] += 1
        else:
            self.success_counts[provider] = 1

        # If in half-open state, increment success count
        if provider in self.half_open_calls:
            self.half_open_calls[provider] += 1

            # If we've had enough successful calls in half-open, close circuit
            if (
                self.half_open_calls[provider] >= self.half_open_max_calls
                and provider in self.failure_counts
            ):
                self.failure_counts[provider] = 0
                del self.half_open_calls[provider]
                logger.info(
                    f"Circuit breaker for {provider} closing - all tests passed"
                )

    def record_failure(self, provider: str):
        """Record a failed call."""
        if provider not in self.failure_counts:
            self.failure_counts[provider] = 0

        self.failure_counts[provider] += 1
        self.last_failure_times[provider] = time.time()

        if provider in self.half_open_calls:
            del self.half_open_calls[provider]

        if self.failure_counts[provider] >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker for {provider} OPEN - "
                f"{self.failure_counts[provider]} failures"
            )

    def reset(self, provider: str):
        """Reset circuit breaker state for a provider."""
        if provider in self.failure_counts:
            del self.failure_counts[provider]
        if provider in self.last_failure_times:
            del self.last_failure_times[provider]
        if provider in self.success_counts:
            del self.success_counts[provider]
        if provider in self.half_open_calls:
            del self.half_open_calls[provider]

        logger.info(f"Circuit breaker state reset for {provider}")

    def get_state(self, provider: str) -> str:
        """Get current circuit state for a provider."""
        if provider not in self.failure_counts:
            return "closed"

        if self.failure_counts[provider] >= self.failure_threshold:
            last_failure = self.last_failure_times.get(provider, 0)
            time_since_failure = time.time() - last_failure

            if time_since_failure >= self.recovery_timeout:
                return "half-open"
            return "open"

        return "closed"

    def get_stats(self, provider: str) -> Dict[str, Any]:
        """Get circuit breaker statistics for a provider."""
        return {
            "state": self.get_state(provider),
            "failure_count": self.failure_counts.get(provider, 0),
            "success_count": self.success_counts.get(provider, 0),
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }
