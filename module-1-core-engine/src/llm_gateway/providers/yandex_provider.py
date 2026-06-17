"""Обёртка для Yandex LLM API"""

import os
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
from common.schemas import GenerateResponse, GenerationConfig
from common.logging import logger, log_info, log_error
from common.metrics import track_llm_call, track_token_usage
from .base import LLMProvider


class YandexProvider(LLMProvider):
    """Yandex LLM API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv("YA_LLM_KEY", config.get("api_key", ""))
        self.folder_id = os.getenv("YA_HOST_KEY", config.get("folder_id", ""))
        self.base_url = config.get(
            "base_url",
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        )
        self.timeout = aiohttp.ClientTimeout(total=config.get("timeout", 60))

    async def generate(
        self, prompt: str, config: Optional[GenerationConfig] = None
    ) -> GenerateResponse:
        """Generate text using Yandex LLM API."""
        if not self.api_key or not self.folder_id:
            raise Exception("YA_LLM_KEY и YA_HOST_KEY должны быть в .env")

        start_time = time.time()
        config = self._build_config(config)

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = self.base_url

                messages = [
                    {
                        "role": "system",
                        "text": "Ты - эксперт по оценке качества ответов. Ты строгий, но справедливый судья.",
                    },
                    {"role": "user", "text": prompt},
                ]

                request_body = {
                    "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                    "completionOptions": {
                        "stream": False,
                        "temperature": config.temperature,
                        "maxTokens": str(config.max_tokens),
                    },
                    "messages": messages,
                }

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Api-Key {self.api_key}",
                }

                log_info("Calling Yandex LLM", url=url, model="yandexgpt-lite")

                async with session.post(
                    url, headers=headers, json=request_body
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Yandex LLM API error: {response.status} - {error_text}"
                        )

                    result = await response.json()

                    # Extract response text
                    if "result" in result and "alternatives" in result["result"]:
                        text = result["result"]["alternatives"][0]["message"]["text"]
                    else:
                        raise ValueError(f"Unexpected API response format: {result}")

                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Track metrics
                    # Yandex API doesn't return token counts in the response
                    # We'll use estimated values
                    prompt_tokens = len(prompt) // 4  # rough estimate
                    completion_tokens = len(text) // 4  # rough estimate

                    track_llm_call(
                        provider="yandex", model="yandexgpt-lite", complexity="powerful"
                    )
                    track_token_usage(prompt_tokens, completion_tokens)

                    log_info("Yandex LLM response received", latency_ms=latency_ms)

                    return GenerateResponse(
                        text=text,
                        model_used="yandexgpt-lite",
                        complexity_used=3,  # POWERFUL
                        token_usage={
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                        },
                        latency_ms=latency_ms,
                        from_cache=False,
                    )

        except aiohttp.ClientError as e:
            log_error("Yandex LLM request error", error=str(e))
            if self.circuit_breaker:
                self.circuit_breaker.record_failure("yandex:ya-llm")
            raise
        except asyncio.TimeoutError:
            log_error("Yandex LLM timeout")
            if self.circuit_breaker:
                self.circuit_breaker.record_failure("yandex:ya-llm")
            raise
        except Exception as e:
            log_error("Yandex LLM error", error=str(e))
            if self.circuit_breaker:
                self.circuit_breaker.record_failure("yandex:ya-llm")
            raise

    async def health_check(self) -> bool:
        """Check if Yandex LLM API is healthy."""
        if not self.api_key:
            return False
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = self.base_url
                payload = {
                    "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.1,
                        "maxTokens": "10",
                    },
                    "messages": [{"role": "user", "text": "hi"}],
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Api-Key {self.api_key}",
                }

                async with session.post(url, headers=headers, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Yandex LLM health check failed: {e}")
            return False

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        return {
            "model_name": "yandexgpt-lite",
            "provider": "yandex",
            "description": "Yandex GPT Lite model via API",
        }
