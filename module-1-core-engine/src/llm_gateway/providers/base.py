# Базовый класс провайдера

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from common.schemas import GenerateResponse, GenerationConfig
from .circuit_breaker import CircuitBreaker


class LLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get("model_name", "")
        self.max_tokens = config.get("max_tokens", 2048)
        self.temperature = config.get("temperature", 0.7)
        self.timeout = config.get("timeout", 30)
        self.circuit_breaker: Optional[CircuitBreaker] = None

    @abstractmethod
    async def generate(self, prompt: str, config: GenerationConfig) -> GenerateResponse:
        """Generate text from the model."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass

    def _build_config(self, config: Optional[GenerationConfig]) -> GenerationConfig:
        """Build final config from defaults and request config."""
        if config is None:
            config = GenerationConfig()

        # Use request values or defaults
        config.temperature = config.temperature or self.temperature
        config.max_tokens = config.max_tokens or self.max_tokens
        return config

    def set_circuit_breaker(self, circuit_breaker: CircuitBreaker):
        """Set circuit breaker instance for this provider."""
        self.circuit_breaker = circuit_breaker
