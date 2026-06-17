# Ollama провайдер

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
from common.schemas import GenerateResponse, GenerationConfig
from common.logging import logger, log_info, log_error
from common.metrics import track_llm_call, track_token_usage
from .base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama LLM provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = (
            f"http://{config.get('host', 'localhost')}:{config.get('port', 11434)}"
        )
        self.timeout = aiohttp.ClientTimeout(total=config.get("timeout", 30))

    async def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> GenerateResponse:
        """Generate text using Ollama."""
        start_time = time.time()
        config = self._build_config(config)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/generate"
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "stream": False,
                }

                log_info("Calling Ollama", url=url, model=self.model_name)

                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Ollama API error: {response.status} - {error_text}"
                        )

                    result = await response.json()

                    # Extract response text
                    text = result.get("response", "")

                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Track metrics
                    prompt_tokens = result.get("prompt_eval_count", 0)
                    completion_tokens = result.get("eval_count", 0)

                    track_llm_call(
                        provider="ollama",
                        model=self.model_name,
                        complexity=(
                            "fast" if self.model_name == "llama3.2:3b" else "balanced"
                        ),
                    )
                    track_token_usage(prompt_tokens, completion_tokens)

                    log_info(
                        "Ollama response received",
                        latency_ms=latency_ms,
                        tokens=completion_tokens,
                    )

                    return GenerateResponse(
                        text=text,
                        model_used=self.model_name,
                        latency_ms=latency_ms,
                        token_usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                        },
                        from_cache=False,
                    )

        except asyncio.TimeoutError:
            log_error("Ollama timeout", model=self.model_name)
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(f"ollama:{self.model_name}")
            raise
        except Exception as e:
            log_error("Ollama error", error=str(e))
            if self.circuit_breaker:
                self.circuit_breaker.record_failure(f"ollama:{self.model_name}")
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Ollama 0.21.2+ uses root endpoint for health check
                # /api/health returns 404
                url = f"{self.base_url}/"
                log_info("Checking Ollama health", url=url)
                async with session.get(url) as response:
                    text = await response.text()
                    log_info(
                        "Ollama health response", status=response.status, text=text
                    )
                    result = response.status == 200 and "Ollama is running" in text
                    log_info("Ollama health check result", result=result)
                    return result
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/show"
                payload = {"name": self.model_name}

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
