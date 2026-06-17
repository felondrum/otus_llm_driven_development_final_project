# Тесты базового класса провайдера LLM

import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestLLMProviderBase:
    """Tests for LLMProvider base class."""
    
    def test_init_with_config(self):
        """Инициализация провайдера с конфигом."""
        from llm_gateway.providers.base import LLMProvider
        
        class MockProvider(LLMProvider):
            async def generate(self, prompt, config):
                pass
            async def health_check(self):
                return True
            async def get_model_info(self):
                return {}
        
        config = {
            'model_name': 'llama3.2:3b',
            'max_tokens': 2048,
            'temperature': 0.7,
            'timeout': 30
        }
        
        provider = MockProvider(config)
        
        assert provider.config == config
        assert provider.model_name == 'llama3.2:3b'
        assert provider.max_tokens == 2048
        assert provider.temperature == 0.7
        assert provider.timeout == 30
    
    def test_init_with_default_values(self):
        """Инициализация с дефолтными значениями."""
        from llm_gateway.providers.base import LLMProvider
        
        class MockProvider(LLMProvider):
            async def generate(self, prompt, config):
                pass
            async def health_check(self):
                return True
            async def get_model_info(self):
                return {}
        
        config = {}
        provider = MockProvider(config)
        
        assert provider.model_name == ''
        assert provider.max_tokens == 2048
        assert provider.temperature == 0.7
        assert provider.timeout == 30
    
    def test_build_config_none(self):
        """Построение config (None)."""
        from llm_gateway.providers.base import LLMProvider
        from common.schemas import GenerationConfig
        
        class MockProvider(LLMProvider):
            async def generate(self, prompt, config):
                pass
            async def health_check(self):
                return True
            async def get_model_info(self):
                return {}
        
        config = {}
        provider = MockProvider(config)
        
        result = provider._build_config(None)
        
        assert isinstance(result, GenerationConfig)
        assert result.temperature == 0.7
        assert result.max_tokens == 2048
        assert result.stream is False
    
    def test_build_config_partial(self):
        """Построение config (частичный)."""
        from llm_gateway.providers.base import LLMProvider
        from common.schemas import GenerationConfig
        
        class MockProvider(LLMProvider):
            async def generate(self, prompt, config):
                pass
            async def health_check(self):
                return True
            async def get_model_info(self):
                return {}
        
        provider = MockProvider({})
        
        partial_config = GenerationConfig(temperature=0.9)
        result = provider._build_config(partial_config)
        
        assert result.temperature == 0.9
        assert result.max_tokens == 2048
    
    def test_build_config_full(self):
        """Построение config (полный)."""
        from llm_gateway.providers.base import LLMProvider
        from common.schemas import GenerationConfig
        
        class MockProvider(LLMProvider):
            async def generate(self, prompt, config):
                pass
            async def health_check(self):
                return True
            async def get_model_info(self):
                return {}
        
        provider = MockProvider({})
        
        full_config = GenerationConfig(
            temperature=0.5,
            max_tokens=1000,
            stream=True
        )
        result = provider._build_config(full_config)
        
        assert result.temperature == 0.5
        assert result.max_tokens == 1000
        assert result.stream is True
    
    def test_abstract_methods(self):
        """Проверка абстрактных методов."""
        from abc import ABCMeta
        
        from llm_gateway.providers.base import LLMProvider
        
        # Проверяем, что класс имеет абстрактные методы
        assert hasattr(LLMProvider, 'generate')
        assert hasattr(LLMProvider, 'health_check')
        assert hasattr(LLMProvider, 'get_model_info')


class TestOllamaProvider:
    """Tests for OllamaProvider."""
    
    def test_init(self):
        """Инициализация OllamaProvider."""
        from llm_gateway.providers.ollama_provider import OllamaProvider
        
        config = {
            'model_name': 'llama3.2:3b',
            'host': 'localhost',
            'port': 11434,
            'timeout': 30
        }
        
        provider = OllamaProvider(config)
        
        assert provider.model_name == 'llama3.2:3b'
        assert provider.base_url == 'http://localhost:11434'
    
    def test_init_default_port(self):
        """Инициализация с дефолтным портом."""
        from llm_gateway.providers.ollama_provider import OllamaProvider
        
        config = {'model_name': 'llama3.2:3b'}
        provider = OllamaProvider(config)
        
        assert provider.base_url == 'http://localhost:11434'


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""
    
    def test_init(self):
        """Инициализация OpenAIProvider."""
        old_value = os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                from llm_gateway.providers.openai_provider import OpenAIProvider
                
                config = {
                    'model_name': 'gpt-4o',
                    'base_url': 'https://api.openai.com/v1',
                    'timeout': 60
                }
                
                provider = OpenAIProvider(config)
                
                assert provider.model_name == 'gpt-4o'
                assert provider.api_key == 'test-key'
                assert provider.base_url == 'https://api.openai.com/v1'
        finally:
            if old_value is not None:
                os.environ['OPENAI_API_KEY'] = old_value
    
    def test_init_config_api_key(self):
        """Инициализация с api_key в конфиге."""
        old_value = os.environ.pop('OPENAI_API_KEY', None)
        
        try:
            from llm_gateway.providers.openai_provider import OpenAIProvider
            
            config = {
                'model_name': 'gpt-4o',
                'api_key': 'config-key'
            }
            
            provider = OpenAIProvider(config)
            
            assert provider.api_key == 'config-key'
        finally:
            if old_value is not None:
                os.environ['OPENAI_API_KEY'] = old_value
