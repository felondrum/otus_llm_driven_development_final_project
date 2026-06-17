# Роутер - выбор модели на основе сложности и длины промпта

from typing import Dict, Any, Optional
from common.logging import logger


class ModelComplexity:
    """Model complexity constants."""

    COMPLEXITY_UNSPECIFIED = 0
    FAST = 1
    BALANCED = 2
    POWERFUL = 3


class Router:
    """Router for selecting appropriate LLM model."""

    def __init__(self, config: Dict[str, Any], circuit_breaker: Optional[Any] = None):
        self.config = config
        self.fallback_chain = config.get("fallback_chain", [])
        self.circuit_breaker = circuit_breaker

    def route_request(
        self, complexity: int, prompt_length: int, has_style: bool = False
    ) -> str:
        """
        Route request to appropriate model based on complexity and prompt length.

        Args:
            complexity: ModelComplexity enum value (0=unspecified, 1=fast, 2=balanced, 3=powerful)
            prompt_length: Length of the prompt in characters
            has_style: Whether style examples are included

        Returns:
            Model identifier string (e.g., "ollama:qwen2.5:7b")
        """
        # Fast path for simple requests
        if complexity == ModelComplexity.FAST or (
            prompt_length < 500 and not has_style
        ):
            model = self._find_model("fast")
            logger.info(f"Routing to fast model: {model}")
            return model

        # Balanced path for most requests
        elif complexity == ModelComplexity.BALANCED or has_style:
            model = self._find_model("balanced")
            logger.info(f"Routing to balanced model: {model}")
            return model

        # Powerful path for complex requests
        else:
            model = self._find_model("powerful")
            logger.info(f"Routing to powerful model: {model}")
            return model

    def _find_model(self, complexity_name: str) -> str:
        """Find model by complexity name from fallback chain."""
        for entry in self.fallback_chain:
            if complexity_name in entry.lower():
                return entry
        # Default fallback
        return self.fallback_chain[-1] if self.fallback_chain else "ollama:qwen2.5:7b"

    def get_available_models(self) -> Dict[str, str]:
        """Get dictionary of available models."""
        models = {}
        for entry in self.fallback_chain:
            parts = entry.split(":")
            if len(parts) >= 2:
                provider = parts[0]
                model = ":".join(parts[1:])
                models[f"{provider}:{model}"] = f"{provider}://{model}"
        return models

    def select_provider(self, current_index: int = 0) -> str:
        """Select next provider from fallback chain."""
        if current_index >= len(self.fallback_chain):
            return self.fallback_chain[-1]  # Return last provider (usually API)

        return self.fallback_chain[current_index]

    def fallback(self, current_model: str, error: str) -> str:
        """Select fallback provider when current one fails."""
        try:
            current_index = self.fallback_chain.index(current_model)
        except ValueError:
            # Current model not in chain, return first
            return self.fallback_chain[0] if self.fallback_chain else ""

        # Try next provider in chain
        if current_index + 1 < len(self.fallback_chain):
            next_model = self.fallback_chain[current_index + 1]
            logger.info(f"Falling back to: {next_model}, reason: {error}")
            return next_model

        # No more providers
        raise ValueError(f"All fallback providers failed: {error}")


# Global router instance
_router: Optional[Router] = None


def get_router(
    config: Optional[Dict[str, Any]] = None, circuit_breaker: Optional[Any] = None
) -> Router:
    """Get global router instance."""
    global _router
    if _router is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _router = Router(config, circuit_breaker)
    return _router
