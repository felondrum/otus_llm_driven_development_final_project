# Тесты LLM кэша

import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestLLMCache:
    """Tests for LLMCache class."""
    
    def test_generate_key(self):
        """Генерация ключа кэша."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        prompt = "test prompt"
        model = "ollama:llama3.2:3b"
        config = {'temperature': 0.7, 'max_tokens': 1000}
        
        key = cache._generate_key(prompt, model, config)
        
        assert key.startswith('llm:')
        assert model in key
    
    def test_generate_key_different_params(self):
        """Разные параметры -> разные ключи."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key1 = cache._generate_key("prompt1", "model1", {'temperature': 0.5})
        key2 = cache._generate_key("prompt2", "model1", {'temperature': 0.5})
        
        assert key1 != key2
    
    def test_generate_key_different_models(self):
        """Разные модели -> разные ключи."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key1 = cache._generate_key("prompt", "model1", {'temperature': 0.5})
        key2 = cache._generate_key("prompt", "model2", {'temperature': 0.5})
        
        assert key1 != key2
    
    def test_generate_key_different_temperature(self):
        """Разная температура -> разные ключи."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key1 = cache._generate_key("prompt", "model", {'temperature': 0.5})
        key2 = cache._generate_key("prompt", "model", {'temperature': 0.8})
        
        assert key1 != key2
    
    def test_generate_key_default_temperature(self):
        """Дефолтная температура при отсутствии в config."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key1 = cache._generate_key("prompt", "model", {})
        key2 = cache._generate_key("prompt", "model", {'temperature': 0.7})
        
        assert key1 == key2
    
    def test_generate_key_with_model_colon(self):
        """Модель с двоеточиями в ключе."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key = cache._generate_key("prompt", "provider:model:version", {'temperature': 0.5})
        
        assert 'provider:model:version' in key
    
    def test_generate_key_hash_is_consistent(self):
        """Одинаковые параметры -> одинаковый хеш."""
        from llm_gateway.cache import LLMCache
        cache = LLMCache.__new__(LLMCache)
        
        key1 = cache._generate_key("prompt", "model", {'temperature': 0.5, 'max_tokens': 1000})
        key2 = cache._generate_key("prompt", "model", {'temperature': 0.5, 'max_tokens': 1000})
        
        assert key1 == key2


class TestLLMCacheOperations:
    """Tests for LLMCache operations with mock Redis."""
    
    def test_get_cached_response(self):
        """Получение закэшированного ответа."""
        from llm_gateway.cache import LLMCache
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"adapted_text": "Cached response"}'
        
        with patch('llm_gateway.cache.redis.Redis', return_value=mock_redis):
            cache = LLMCache()
            result = cache.get("prompt", "model", {'temperature': 0.7})
        
        assert result == {'adapted_text': 'Cached response'}
    
    def test_get_cache_miss(self):
        """Промах кэша."""
        from llm_gateway.cache import LLMCache
        
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('llm_gateway.cache.redis.Redis', return_value=mock_redis):
            cache = LLMCache()
            result = cache.get("prompt", "model", {'temperature': 0.7})
        
        assert result is None
    
    def test_set_cache_response(self):
        """Запись в кэш."""
        from llm_gateway.cache import LLMCache
        
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        
        with patch('llm_gateway.cache.redis.Redis', return_value=mock_redis):
            cache = LLMCache()
            result = cache.set("prompt", "model", {'temperature': 0.7}, {'response': 'test'})
        
        assert result is True
    
    def test_delete_cache_entry(self):
        """Удаление из кэша."""
        from llm_gateway.cache import LLMCache
        
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        
        with patch('llm_gateway.cache.redis.Redis', return_value=mock_redis):
            cache = LLMCache()
            result = cache.delete("prompt", "model", {'temperature': 0.7})
        
        assert result is True
    
    def test_clear_by_pattern(self):
        """Очистка по паттерну."""
        from llm_gateway.cache import LLMCache
        
        mock_redis = MagicMock()
        mock_redis.keys.return_value = ['key1', 'key2']
        mock_redis.delete.return_value = 2
        
        with patch('llm_gateway.cache.redis.Redis', return_value=mock_redis):
            cache = LLMCache()
            result = cache.clear_by_pattern('pattern')
        
        assert result == 2
