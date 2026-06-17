# Circuit Breaker для отказоустойчивости LLM провайдеров

import asyncio
from typing import Optional
from datetime import datetime, timedelta
from common.logging import logger


class CircuitBreaker:
    """Circuit breaker pattern implementation for LLM providers."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = "closed"  # closed, open, half_open
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._last_success_time: Optional[datetime] = None
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        # Check if we should transition from open to half_open
        if self._state == "open" and self._last_failure_time:
            elapsed = (datetime.now() - self._last_failure_time).total_seconds()
            if elapsed >= self.recovery_timeout:
                self._state = "half_open"
                self._half_open_calls = 0
                logger.info("Circuit breaker transitioned to half_open state")
        
        return self._state

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self._state == "closed":
            return True
        
        if self._state == "half_open":
            if self._half_open_calls < self.half_open_max_calls:
                return True
            return False
        
        # open state - circuit is tripped
        return False

    async def record_success(self):
        """Record successful call."""
        self._success_count += 1
        self._last_success_time = datetime.now()
        self._half_open_calls = 0
        
        if self._state == "half_open":
            self._state = "closed"
            self._failure_count = 0
            logger.info("Circuit breaker closed after successful call")
        
        # Reset failure count on success in closed state
        if self._state == "closed":
            self._failure_count = max(0, self._failure_count - 1)

    async def record_failure(self):
        """Record failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._state == "half_open":
            self._state = "open"
            self._half_open_calls = 0
            logger.warning("Circuit breaker opened after failure in half_open state")
        
        elif self._state == "closed":
            if self._failure_count >= self.failure_threshold:
                self._state = "open"
                logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    async def execute(self, coro):
        """Execute coroutine with circuit breaker protection."""
        if not self.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker is {self.state}, request rejected"
            )
        
        try:
            result = await coro
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass
