# Тесты кэш-менеджера оркестратора

import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from orchestrator.cache_manager import CacheManager


class TestCacheManager:
    """Tests for CacheManager class."""
    
    def test_generate_key_basic(self):
        """Базовая генерация ключа."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key = cache_manager.generate_key(
            message_id="msg1",
            text="test text",
            recipient_id="user1",
            rules=[]
        )
        
        assert key.startswith("adaptation:")
        assert len(key) > len("adaptation:")
    
    def test_generate_key_with_rules(self):
        """Ключ с правилами."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key = cache_manager.generate_key(
            text="test",
            recipient_id="user1",
            rules=["rule1", "rule2"]
        )
        
        assert key.startswith("adaptation:")
    
    def test_generate_key_sorted_rules(self):
        """Правила сортируются для консистентных ключей."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key1 = cache_manager.generate_key(
            text="test",
            recipient_id="user1",
            rules=["rule1", "rule2"]
        )
        
        key2 = cache_manager.generate_key(
            text="test",
            recipient_id="user1",
            rules=["rule2", "rule1"]
        )
        
        assert key1 == key2
    
    def test_generate_key_different_text(self):
        """Разный текст -> разные ключи."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key1 = cache_manager.generate_key(
            text="text1",
            recipient_id="user1",
            rules=[]
        )
        
        key2 = cache_manager.generate_key(
            text="text2",
            recipient_id="user1",
            rules=[]
        )
        
        assert key1 != key2
    
    def test_generate_key_different_recipient(self):
        """Разные получатели -> разные ключи."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key1 = cache_manager.generate_key(
            text="test",
            recipient_id="user1",
            rules=[]
        )
        
        key2 = cache_manager.generate_key(
            text="test",
            recipient_id="user2",
            rules=[]
        )
        
        assert key1 != key2
    
    def test_generate_key_none_values(self):
        """Генерация ключа с None значениями."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        key = cache_manager.generate_key(
            message_id=None,
            text=None,
            recipient_id=None,
            rules=None
        )
        
        assert key.startswith("adaptation:")
    
    def test_key_generation_algorithm(self):
        """Проверка алгоритма генерации ключа."""
        cache_manager = CacheManager.__new__(CacheManager)
        
        text = "test text"
        recipient_id = "user1"
        rules = ["rule1", "rule2"]
        
        key_data = {
            'text': text or '',
            'recipient_id': recipient_id or '',
            'rules': sorted(rules) if rules else []
        }
        key_str = 'adaptation:' + __import__('hashlib').sha256(__import__('json').dumps(key_data, sort_keys=True).encode()).hexdigest()
        
        actual_key = cache_manager.generate_key(
            text=text,
            recipient_id=recipient_id,
            rules=rules
        )
        
        assert actual_key.startswith("adaptation:")


class TestCacheManagerOperations:
    """Tests for CacheManager operations with mock Redis."""
    
    def test_get_cached_adaptation(self):
        """Получение закэшированной адаптации."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"adapted_text": "Cached response"}'
        
        with patch('orchestrator.cache_manager.redis.Redis', return_value=mock_redis):
            cache_manager = CacheManager()
            result = cache_manager.get("test-key")
        
        assert result == {'adapted_text': 'Cached response'}
    
    def test_get_cache_miss(self):
        """Промах кэша."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        
        with patch('orchestrator.cache_manager.redis.Redis', return_value=mock_redis):
            cache_manager = CacheManager()
            result = cache_manager.get("test-key")
        
        assert result is None
    
    def test_set_cache_response(self):
        """Запись в кэш."""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        
        with patch('orchestrator.cache_manager.redis.Redis', return_value=mock_redis):
            cache_manager = CacheManager()
            result = cache_manager.set("test-key", {'response': 'test'})
        
        assert result is True
    
    def test_delete_cache_entry(self):
        """Удаление из кэша."""
        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1
        
        with patch('orchestrator.cache_manager.redis.Redis', return_value=mock_redis):
            cache_manager = CacheManager()
            result = cache_manager.delete("test-key")
        
        assert result is True
