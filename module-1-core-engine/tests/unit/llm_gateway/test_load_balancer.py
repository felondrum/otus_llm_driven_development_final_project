# Тесты балансировщика нагрузки

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_gateway.load_balancer import LoadBalancer


class TestLoadBalancer:
    """Tests for LoadBalancer class."""
    
    def test_init_with_chain(self):
        """Инициализация с цепочкой провайдеров."""
        chain = [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b',
            'openai:gpt-4o'
        ]
        lb = LoadBalancer(chain)
        
        assert lb.fallback_chain == chain
        assert len(lb.provider_status) == 3
    
    def test_init_provider_status(self):
        """Инициализация статусов провайдеров."""
        chain = ['ollama:llama3.2:3b', 'openai:gpt-4o']
        lb = LoadBalancer(chain)
        
        assert 'ollama:llama3.2:3b' in lb.provider_status
        assert 'openai:gpt-4o' in lb.provider_status
        
        status = lb.provider_status['ollama:llama3.2:3b']
        assert status['success_count'] == 0
        assert status['error_count'] == 0
        assert status['is_healthy'] is True
    
    def test_select_provider(self):
        """Выбор провайдера по индексу."""
        chain = ['ollama:llama3.2:3b', 'ollama:qwen2.5:7b', 'openai:gpt-4o']
        lb = LoadBalancer(chain)
        
        provider = lb.select_provider(current_index=0)
        assert provider == 'ollama:llama3.2:3b'
        
        provider = lb.select_provider(current_index=1)
        assert provider == 'ollama:qwen2.5:7b'
    
    def test_select_provider_overflow(self):
        """Выбор при переполнении индекса."""
        chain = ['ollama:llama3.2:3b', 'openai:gpt-4o']
        lb = LoadBalancer(chain)
        
        provider = lb.select_provider(current_index=10)
        assert provider == 'openai:gpt-4o'
    
    def test_record_success(self):
        """Запись успешного запроса."""
        chain = ['ollama:llama3.2:3b']
        lb = LoadBalancer(chain)
        
        lb.record_success('ollama:llama3.2:3b', 100)
        
        status = lb.provider_status['ollama:llama3.2:3b']
        assert status['success_count'] == 1
        assert status['is_healthy'] is True
        assert status['avg_latency'] == 100
    
    def test_record_success_update_latency(self):
        """Обновление средней задержки при повторных успехах."""
        chain = ['ollama:llama3.2:3b']
        lb = LoadBalancer(chain)
        
        lb.record_success('ollama:llama3.2:3b', 100)
        lb.record_success('ollama:llama3.2:3b', 200)
        
        status = lb.provider_status['ollama:llama3.2:3b']
        assert status['success_count'] == 2
        assert status['avg_latency'] == 110.0
    
    def test_record_error(self):
        """Запись ошибки."""
        chain = ['ollama:llama3.2:3b']
        lb = LoadBalancer(chain)
        
        lb.record_error('ollama:llama3.2:3b', 'Connection timeout')
        
        status = lb.provider_status['ollama:llama3.2:3b']
        assert status['error_count'] == 1
        assert status['last_error'] == 'Connection timeout'
    
    def test_record_error_unhealthy(self):
        """Маркировка провайдера как нездорового после ошибок."""
        chain = ['ollama:llama3.2:3b']
        lb = LoadBalancer(chain)
        
        for _ in range(6):
            lb.record_error('ollama:llama3.2:3b', 'Error')
        
        status = lb.provider_status['ollama:llama3.2:3b']
        assert status['error_count'] == 6
        assert status['is_healthy'] is False
    
    def test_get_best_provider(self):
        """Получение лучшего доступного провайдера."""
        chain = [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b',
            'openai:gpt-4o'
        ]
        lb = LoadBalancer(chain)
        
        best = lb.get_best_provider()
        assert best == 'ollama:llama3.2:3b'
    
    def test_get_best_provider_unhealthy(self):
        """Получение лучшего провайдера, когда первый нездоров."""
        chain = [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b',
            'openai:gpt-4o'
        ]
        lb = LoadBalancer(chain)
        
        lb.provider_status['ollama:llama3.2:3b']['is_healthy'] = False
        
        best = lb.get_best_provider()
        assert best == 'ollama:qwen2.5:7b'
    
    def test_fallback(self):
        """Получение следующего провайдера в цепочке."""
        chain = [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b',
            'openai:gpt-4o'
        ]
        lb = LoadBalancer(chain)
        
        next_provider = lb.fallback('ollama:llama3.2:3b', 'Error')
        assert next_provider == 'ollama:qwen2.5:7b'
    
    def test_fallback_last_provider(self):
        """Последний провайдер в цепочке."""
        chain = [
            'ollama:llama3.2:3b',
            'openai:gpt-4o'
        ]
        lb = LoadBalancer(chain)
        
        next_provider = lb.fallback('openai:gpt-4o', 'Error')
        assert next_provider == 'openai:gpt-4o'
    
    def test_fallback_unknown_provider(self):
        """Получение следующего при неизвестном провайдере."""
        chain = ['ollama:llama3.2:3b', 'openai:gpt-4o']
        lb = LoadBalancer(chain)
        
        next_provider = lb.fallback('unknown:provider', 'Error')
        assert next_provider == 'unknown:provider'
    
    def test_get_status(self):
        """Получение полного статуса балансировщика."""
        chain = ['ollama:llama3.2:3b', 'openai:gpt-4o']
        lb = LoadBalancer(chain)
        
        status = lb.get_status()
        
        assert 'fallback_chain' in status
        assert 'provider_status' in status
        assert status['fallback_chain'] == chain
        assert len(status['provider_status']) == 2
