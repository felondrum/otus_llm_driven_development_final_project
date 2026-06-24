# Классификатор сообщений

import asyncio
import httpx
import time
from typing import Dict, Any, Optional, List
from common.logging import logger, log_info, log_error
from common.metrics import measure_latency
from common.schemas import MessageCategory, ClassificationResult

# Add src to path
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException


class MessageClassifier:
    """Classifier for incoming messages using LLM Gateway."""

    def __init__(self, llm_gateway_url: Optional[str] = None):
        # Use LLM_GATEWAY_HOST env variable if available, otherwise use default
        llm_gateway_host = os.getenv("LLM_GATEWAY_HOST", "llm-gateway")
        llm_gateway_port = os.getenv("LLM_GATEWAY_PORT", "8003")
        
        # If LLM_GATEWAY_URL is explicitly set, use it
        self.llm_gateway_url = llm_gateway_url or os.getenv(
            "LLM_GATEWAY_URL", f"http://{llm_gateway_host}:{llm_gateway_port}"
        )
        self.llm_gateway_model = os.getenv(
            "CLASSIFICATION_LLM_GATEWAY_MODEL", "ollama:qwen2.5:1.5b"
        )
        self.categories = [
            MessageCategory.GREETING,
            MessageCategory.FAREWELL,
            MessageCategory.CRITICISM,
            MessageCategory.FLATTERY,
            MessageCategory.OFFTOPIC,
            MessageCategory.COMPLIMENT,
            MessageCategory.COMPLAINT,
            MessageCategory.REQUEST,
            MessageCategory.INFORMATION,
            MessageCategory.EMOTION,
        ]
        self._prompt_template = """Классифицируй сообщение пользователя по следующим категориям: {categories}

Верни ТОЛЬКО название категории из списка.

Сообщение: "{text}"

Категория:"""

    def _build_classification_prompt(self, text: str) -> str:
        """Build classification prompt."""
        categories_list = "\n".join(f"- {cat}" for cat in self.categories)
        return self._prompt_template.format(
            categories=categories_list,
            text=text[:500]  # Limit text length
        )

    def _parse_category(self, category_text: str) -> str:
        """Parse category from LLM response."""
        category_text = category_text.strip().lower()
        
        # Try exact match first
        if category_text in self.categories:
            return category_text
        
        # Try to find match by checking keywords
        category_keywords = {
            MessageCategory.GREETING: ["привет", "здравствуй", "добрый", "здравствуйте", "hello", "hi"],
            MessageCategory.FAREWELL: ["пока", "до свидания", "до встречи", "goodbye", "bye"],
            MessageCategory.CRITICISM: ["критика", "плохо", "ошибка", "неправильно", "проблема"],
            MessageCategory.FLATTERY: ["ласть", "восхитительно", "прекрасно", "великолепно"],
            MessageCategory.COMPLIMENT: ["комплимент", "замечательно", "отлично", "хорошо", "сделал", "спасибо"],
            MessageCategory.COMPLAINT: ["жалоба", "неудовлетворен", "претензия", "жалуюсь", "недоволен"],
            MessageCategory.REQUEST: ["запрос", "помогите", "нужна", "можно", "хотел бы"],
            MessageCategory.INFORMATION: ["информация", "узнать", "узнать", "как", "что", "почему"],
            MessageCategory.EMOTION: ["эмоция", "счастлив", "грустно", "рад", "печально"],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in category_text:
                    return category
        
        return MessageCategory.UNKNOWN

    @measure_latency(service="orchestrator", endpoint="classify_message")
    async def classify_message(self, text: str) -> ClassificationResult:
        """Classify a message using LLM Gateway."""
        prompt = self._build_classification_prompt(text)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.llm_gateway_url}/generate",
                    json={
                        "prompt": prompt,
                        "complexity": 1,  # FAST - for quick classification
                        "config": {
                            "temperature": 0.1,  # Low temperature for deterministic output
                            "max_tokens": 50,
                            "stream": False,
                        },
                    },
                    timeout=15.0,
                )

                if response.status_code != 200:
                    error_text = response.text
                    log_error(
                        "Classification LLM Gateway error",
                        status=response.status_code,
                        error=error_text,
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"LLM Gateway error: {response.status_code}",
                    )

                result = response.json()
                category_text = result.get("text", "").strip().lower()
                category = self._parse_category(category_text)

                log_info(
                    "Message classified",
                    category=category,
                    original_category=category_text,
                    model=self.llm_gateway_model,
                )

                return ClassificationResult(
                    category=category,
                    category_code=category,
                    confidence=0.95 if category != MessageCategory.UNKNOWN else 0.7,
                    processed_at=int(time.time()),
                )

        except httpx.RequestError as e:
            log_error("Classification connection error", error=str(e))
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to LLM Gateway: {str(e)}",
            )
        except Exception as e:
            log_error("Classification unknown error", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Classification error: {str(e)}",
            )

    async def get_classification_categories(self) -> List[str]:
        """Get list of available classification categories."""
        return self.categories


# Global classifier instance
_classifier: Optional[MessageClassifier] = None


def get_classifier(llm_gateway_url: Optional[str] = None) -> MessageClassifier:
    """Get global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = MessageClassifier(llm_gateway_url)
    return _classifier
