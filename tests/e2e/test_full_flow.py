"""Интеграционные тесты модуля 1 Core Engine с реальными Yandex API и Langfuse v3."""

import os
import sys
import pytest
import time
from typing import Dict, Any

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "module-1-core-engine", "src"))

# Импортируем HTTP клиент
import requests

# Настройки
BASE_URL = os.getenv("LLM_GATEWAY_URL", "http://localhost:8003")
LANGFUSE_URL = os.getenv("LANGFUSE_URL", "http://localhost:3000")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-1234567890")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-1234567890")

# Генерация ID для трейсов
TRACE_ID_PREFIX = "integration-test-"


def test_health_check():
    """Проверка здоровья LLM Gateway."""
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "ollama:qwen2.5:1.5b" in data["checks"]
    assert "yandex:ya-llm" in data["checks"]
    assert data["checks"]["cache"] == "ok"


def test_yandex_llm_generation():
    """Тест генерации текста через Yandex LLM с реальным API ключом."""
    prompt = "Напиши короткое приветственное сообщение на русском языке."
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": prompt,
            "complexity": 1,  # fast
            "config": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        },
        timeout=60
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 0
    assert "model_used" in data
    assert "token_usage" in data
    assert "latency_ms" in data
    assert "from_cache" in data
    
    print(f"\nYandex LLM Response:")
    print(f"  Text: {data['text'][:100]}...")
    print(f"  Model: {data['model_used']}")
    print(f"  Latency: {data['latency_ms']}ms")
    print(f"  Token usage: {data['token_usage']}")
    print(f"  From cache: {data['from_cache']}")


def test_yandex_llm_complex_generation():
    """Тест генерации сложного текста через Yandex LLM."""
    prompt = """Напиши статью объемом 200-300 слов о важности искусственного интеллекта 
в современном мире. Статья должна быть структурированной с введением, 
основной частью и заключением."""
    
    response = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": prompt,
            "complexity": 2,  # balanced
            "config": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        timeout=60
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "text" in data
    assert len(data["text"]) > 200  # Должна быть генерация минимум 200 символов
    
    print(f"\nYandex LLM Complex Response:")
    print(f"  Text length: {len(data['text'])} chars")
    print(f"  Model: {data['model_used']}")
    print(f"  Latency: {data['latency_ms']}ms")
    print(f"  Token usage: {data['token_usage']}")


def test_cache_hit():
    """Тест кэширования - второй запрос с тем же prompt должен вернуть из кэша."""
    prompt = "Тест кэширования - уникальный запрос " + str(time.time())
    
    # Первый запрос
    response1 = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": prompt,
            "complexity": 1,
            "config": {"temperature": 0.7, "max_tokens": 100}
        },
        timeout=60
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Второй запрос с тем же prompt
    response2 = requests.post(
        f"{BASE_URL}/generate",
        json={
            "prompt": prompt,
            "complexity": 1,
            "config": {"temperature": 0.7, "max_tokens": 100}
        },
        timeout=60
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Проверка кэширования
    assert data1["text"] == data2["text"]
    assert data2["from_cache"] == True
    
    print(f"\nCache Test:")
    print(f"  First request - from_cache: {data1['from_cache']}")
    print(f"  Second request - from_cache: {data2['from_cache']}")
    print(f"  Text matches: {data1['text'] == data2['text']}")


def test_models_endpoint():
    """Проверка эндпоинта списка моделей."""
    response = requests.get(f"{BASE_URL}/models", timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    
    print(f"\nAvailable models: {data}")


def test_fallback_chain():
    """Тест цепочки fallback - если основной провайдер недоступен, использовать резервный."""
    # В данном тесте мы просто проверяем, что fallback chain настроен
    # Для полноценного теста fallback нужно выключить основной провайдер
    
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    assert response.status_code == 200
    
    data = response.json()
    
    # Проверяем, что оба провайдера в цепочке
    assert "ollama:qwen2.5:1.5b" in data["checks"]
    assert "yandex:ya-llm" in data["checks"]
    
    print(f"\nFallback chain test:")
    print(f"  Ollama status: {data['checks']['ollama:qwen2.5:1.5b']}")
    print(f"  Yandex status: {data['checks']['yandex:ya-llm']}")


def test_langfuse_integration():
    """Проверка интеграции с Langfuse v3."""
    # Проверяем доступность Langfuse
    try:
        response = requests.get(f"{LANGFUSE_URL}", timeout=10)
        assert response.status_code == 200
        print(f"\nLangfuse is accessible")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Langfuse is not accessible: {e}")
    
    # Проверяем наличие метрик в ClickHouse (Langfuse v3 uses ClickHouse for events)
    clickhouse_url = "http://localhost:8123"
    try:
        response = requests.get(f"{clickhouse_url}/ping", timeout=5)
        assert response.status_code == 200
        print(f"ClickHouse (Langfuse events storage) is accessible")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"ClickHouse is not accessible: {e}")


def test_real_api_key_usage():
    """Проверка использования реального Yandex API ключа."""
    # Проверяем, что Yandex API ключи заданы
    ya_llm_key = os.getenv("YA_LLM_KEY")
    ya_host_key = os.getenv("YA_HOST_KEY")
    
    assert ya_llm_key is not None and len(ya_llm_key) > 0, "YA_LLM_KEY not set"
    assert ya_host_key is not None and len(ya_host_key) > 0, "YA_HOST_KEY not set"
    
    print(f"\nYandex API keys configured:")
    print(f"  YA_LLM_KEY: {'*' * 10}{ya_llm_key[-10:] if ya_llm_key else 'None'}")
    print(f"  YA_HOST_KEY: {'*' * 10}{ya_host_key[-10:] if ya_host_key else 'None'}")


def test_multiple_complexity_levels():
    """Тест генерации с разными уровнями сложности."""
    prompt = "Тест многослойности текста."
    
    for complexity in [1, 2, 3]:  # fast, balanced, slow
        response = requests.post(
            f"{BASE_URL}/generate",
            json={
                "prompt": prompt,
                "complexity": complexity,
                "config": {"temperature": 0.7, "max_tokens": 200}
            },
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\nComplexity {complexity} test:")
        print(f"  Model: {data['model_used']}")
        print(f"  Latency: {data['latency_ms']}ms")
        print(f"  From cache: {data['from_cache']}")


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])
