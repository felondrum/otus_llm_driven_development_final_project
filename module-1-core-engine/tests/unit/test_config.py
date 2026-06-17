# Тесты конфигурации

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from orchestrator.config import Config, get_config


class TestConfig:
    """Tests for Config class."""
    
    def test_init_with_defaults(self):
        """Инициализация с дефолтными значениями."""
        config = Config.__new__(Config)
        config.config = {}
        config._set_defaults()
        
        assert config.config['server']['port'] == 8001
        assert config.config['server']['host'] == '0.0.0.0'
        assert config.config['services']['redis']['host'] == 'localhost'
        assert config.config['services']['redis']['port'] == 6379
        assert config.config['services']['qdrant']['host'] == 'localhost'
        assert config.config['services']['qdrant']['port'] == 6333
        assert config.config['services']['ollama']['host'] == 'localhost'
        assert config.config['services']['ollama']['port'] == 11434
        assert config.config['logging']['level'] == 'DEBUG'
        assert config.config['cache']['default_ttl'] == 3600
    
    def test_get_value(self):
        """Получение значения по ключу."""
        config = Config.__new__(Config)
        config.config = {
            'server': {'port': 8001},
            'services': {'redis': {'host': 'localhost'}}
        }
        
        value = config.get('server.port')
        assert value == 8001
    
    def test_get_nested_value(self):
        """Получение вложенного значения."""
        config = Config.__new__(Config)
        config.config = {
            'services': {
                'redis': {
                    'host': 'localhost',
                    'port': 6379
                }
            }
        }
        
        value = config.get('services.redis.host')
        assert value == 'localhost'
    
    def test_get_missing_value(self):
        """Получение несуществующего значения."""
        config = Config.__new__(Config)
        config.config = {'server': {'port': 8001}}
        
        value = config.get('server.nonexistent')
        assert value is None
    
    def test_get_missing_value_with_default(self):
        """Получение несуществующего значения с дефолтом."""
        config = Config.__new__(Config)
        config.config = {'server': {'port': 8001}}
        
        value = config.get('server.nonexistent', 'default')
        assert value == 'default'
    
    def test_get_value_with_default(self):
        """Получение значения с дефолтом."""
        config = Config.__new__(Config)
        config.config = {'server': {'port': 8001}}
        
        value = config.get('server.timeout', 30)
        assert value == 30
    
    def test_server_properties(self):
        """Свойства сервера (порт/хост)."""
        config = Config.__new__(Config)
        config.config = {
            'server': {'port': 9000, 'host': '127.0.0.1'}
        }
        
        assert config.server_port == 9000
        assert config.server_host == '127.0.0.1'
    
    def test_service_properties(self):
        """Свойства сервисов (Redis/Qdrant/Ollama)."""
        config = Config.__new__(Config)
        config.config = {
            'services': {
                'redis': {'host': 'redis.local', 'port': 6380},
                'qdrant': {'host': 'qdrant.local', 'port': 6334},
                'ollama': {'host': 'ollama.local', 'port': 11435}
            }
        }
        
        assert config.redis_host == 'redis.local'
        assert config.redis_port == 6380
        assert config.qdrant_host == 'qdrant.local'
        assert config.qdrant_port == 6334
        assert config.ollama_host == 'ollama.local'
        assert config.ollama_port == 11435
    
    def test_cache_properties(self):
        """Свойства кэша."""
        config = Config.__new__(Config)
        config.config = {
            'cache': {'default_ttl': 7200, 'max_size': 20000}
        }
        
        assert config.cache_ttl == 7200
    
    def test_fallback_properties(self):
        """Свойства fallback."""
        config = Config.__new__(Config)
        config.config = {
            'fallback': {
                'chain': ['ollama:llama3.2:3b'],
                'return_original_on_fallback': False
            }
        }
        
        assert config.fallback_chain == ['ollama:llama3.2:3b']
        assert config.return_original_on_fallback is False
    
    def test_config_defaults_full(self):
        """Полная проверка дефолтной конфигурации."""
        config = Config.__new__(Config)
        config.config = {}
        config._set_defaults()
        
        assert config.server_port == 8001
        assert config.server_host == '0.0.0.0'
        assert config.redis_host == 'localhost'
        assert config.redis_port == 6379
        assert config.qdrant_host == 'localhost'
        assert config.qdrant_port == 6333
        assert config.ollama_host == 'localhost'
        assert config.ollama_port == 11434
        assert config.log_level == 'DEBUG'
        assert config.cache_ttl == 3600
        assert len(config.fallback_chain) == 2
        assert config.fallback_chain == ['ollama:qwen2.5:1.5b', 'yandex:ya-llm']
        assert config.return_original_on_fallback is True


class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_config_first_init(self):
        """Получение конфига при первой инициализации."""
        from orchestrator import config as config_module
        
        config_module._config = None
        
        cfg = config_module.get_config()
        
        assert cfg.server_port == 8001
    
    def test_get_config_existing_instance(self):
        """Получение существующего экземпляра."""
        from orchestrator import config as config_module
        
        config_module._config = None
        
        cfg1 = config_module.get_config()
        cfg2 = config_module.get_config()
        
        assert cfg1 is cfg2
