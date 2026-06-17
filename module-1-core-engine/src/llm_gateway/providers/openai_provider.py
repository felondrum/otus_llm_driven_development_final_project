# OpenAI провайдер

import asyncio
import aiohttp
import time
import os
from typing import Dict, Any, Optional
from common.schemas import GenerateResponse, GenerationConfig
from common.logging import logger, log_info, log_error
from common.metrics import track_llm_call, track_token_usage
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv("OPENAI_API_KEY", config.get("api_key", ""))
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))

    async def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> GenerateResponse:
        """Generate text using OpenAI API."""
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        start_time = time.time()
        config = self._build_config(config)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that adapts text.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                }

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                log_info("Calling OpenAI", url=url, model=self.model_name)

                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"OpenAI API error: {response.status} - {error_text}"
                        )

                    result = await response.json()

                    # Extract response text
                    text = result["choices"][0]["message"]["content"]

                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Track metrics
                    prompt_tokens = result["usage"]["prompt_tokens"]
                    completion_tokens = result["usage"]["completion_tokens"]

                    track_llm_call(
                        provider="openai", model=self.model_name, complexity="powerful"
                    )
                    track_token_usage(prompt_tokens, completion_tokens)

                    log_info(
                        "OpenAI response received",
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
            log_error("OpenAI timeout", model=self.model_name)
            raise
        except Exception as e:
            log_error("OpenAI error", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if OpenAI is healthy."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/models"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/models/{self.model_name}"
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
