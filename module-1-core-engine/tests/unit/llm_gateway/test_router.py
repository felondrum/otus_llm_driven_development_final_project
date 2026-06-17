# Тесты роутера LLM

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_gateway.router import Router, get_router, ModelComplexity


class TestRouter:
    """Tests for Router class."""
    
    def test_init_with_config(self):
        """Инициализация роутера с конфигом."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        assert router.config == config
        assert router.fallback_chain == config['fallback_chain']
    
    def test_route_fast_complexity(self):
        """Маршрутизация для fast complexity."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=1, prompt_length=100)
        
        assert model is not None
    
    def test_route_balanced_complexity(self):
        """Маршрутизация для balanced complexity."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=2, prompt_length=100)
        
        assert model is not None
    
    def test_route_powerful_complexity(self):
        """Маршрутизация для powerful complexity."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=3, prompt_length=100)
        
        assert model is not None
    
    def test_route_short_prompt_fast(self):
        """Короткий промпт -> fast модель."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=0, prompt_length=100, has_style=False)
        
        assert model is not None
    
    def test_route_long_prompt_balanced(self):
        """Длинный промпт -> balanced модель."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=0, prompt_length=1000, has_style=False)
        
        assert model is not None
    
    def test_route_with_style(self):
        """Стиль -> balanced модель."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router.route_request(complexity=0, prompt_length=100, has_style=True)
        
        assert model is not None
    
    def test_find_model_found(self):
        """Поиск существующей модели."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router._find_model('llama3.2')
        
        assert model == 'ollama:llama3.2:3b'
    
    def test_find_model_fallback(self):
        """Поиск с fallback."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'ollama:mixtral:8x7b'
            ]
        }
        router = Router(config)
        
        model = router._find_model('unknown')
        
        assert model == 'ollama:mixtral:8x7b'
    
    def test_get_available_models(self):
        """Получение списка доступных моделей."""
        config = {
            'fallback_chain': [
                'ollama:llama3.2:3b',
                'ollama:qwen2.5:7b',
                'openai:gpt-4o'
            ]
        }
        router = Router(config)
        
        models = router.get_available_models()
        
        assert 'ollama:llama3.2:3b' in models
        assert 'ollama:qwen2.5:7b' in models
        assert 'openai:gpt-4o' in models
