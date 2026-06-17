# Тесты метрик

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.metrics import (
    track_cache_hit, track_cache_miss,
    track_llm_call, track_llm_fallback, track_token_usage,
    measure_latency
)


class TestMetrics:
    """Tests for metrics module."""
    
    def test_track_cache_hit(self):
        """Отслеживание попадания в кэш."""
        # Метрики инициализируются при импорте
        # Проверяем, что функция вызывается без ошибок
        track_cache_hit(cache_type='adaptation')
        track_cache_hit(cache_type='llm')
    
    def test_track_cache_miss(self):
        """Отслеживание промаха кэша."""
        track_cache_miss(cache_type='adaptation')
        track_cache_miss(cache_type='llm')
    
    def test_track_llm_call(self):
        """Отслеживание вызова LLM."""
        track_llm_call(provider='ollama', model='llama3.2:3b', complexity='fast')
        track_llm_call(provider='openai', model='gpt-4o', complexity='powerful')
    
    def test_track_llm_fallback(self):
        """Отслеживание отката LLM."""
        track_llm_fallback(from_provider='ollama', to_provider='openai')
    
    def test_track_token_usage(self):
        """Отслеживание использования токенов."""
        track_token_usage(prompt_tokens=100, completion_tokens=50)
    
    async def test_measure_latency_decorator(self):
        """Декоратор измерения задержки."""
        @measure_latency(service='test', endpoint='/api/test')
        async def test_function():
            return 'success'
        
        result = await test_function()
        assert result == 'success'
    
    async def test_measure_latency_exception(self):
        """Декоратор измерения задержки с исключением."""
        @measure_latency(service='test', endpoint='/api/test')
        async def test_function():
            raise ValueError('Test error')
        
        with pytest.raises(ValueError, match='Test error'):
            await test_function()
    
    def test_multiple_cache_hits(self):
        """Несколько попаданий в кэш."""
        for _ in range(5):
            track_cache_hit(cache_type='llm')
    
    def test_multiple_cache_misses(self):
        """Несколько промахов кэша."""
        for _ in range(3):
            track_cache_miss(cache_type='adaptation')


class TestMetricsBasic:
    """Базовые тесты для проверки работы метрик."""
    
    def test_metric_names_exist(self):
        """Проверка существования имен метрик."""
        import common.metrics as metrics
        
        assert hasattr(metrics, 'requests_total')
        assert hasattr(metrics, 'requests_failed')
        assert hasattr(metrics, 'request_latency')
        assert hasattr(metrics, 'cache_hits')
        assert hasattr(metrics, 'cache_misses')
        assert hasattr(metrics, 'llm_calls')
        assert hasattr(metrics, 'llm_latency')
        assert hasattr(metrics, 'llm_fallbacks')
        assert hasattr(metrics, 'token_usage')
        assert hasattr(metrics, 'service_status')
        assert hasattr(metrics, 'cache_ttl_hits')
        assert hasattr(metrics, 'cache_ttl_misses')
        assert hasattr(metrics, 'grpc_timeouts')
        assert hasattr(metrics, 'llm_model_calls')
    
    def test_cache_ttl_metrics(self):
        """Тест метрик cache TTL."""
        import common.metrics as metrics
        
        metrics.track_cache_ttl_hit(cache_type="profile")
        metrics.track_cache_ttl_hit(cache_type="rules")
        metrics.track_cache_ttl_hit(cache_type="style_examples")
        metrics.track_cache_ttl_miss(cache_type="profile")
    
    def test_grpc_timeout_metric(self):
        """Тест метрики gRPC timeout."""
        import common.metrics as metrics
        
        metrics.track_grpc_timeout(service="retriever", method="GetProfile")
        metrics.track_grpc_timeout(service="orchestrator", method="ProcessMessage")
    
    def test_llm_model_metric(self):
        """Тест метрики вызовов моделей LLM."""
        import common.metrics as metrics
        
        metrics.track_llm_model_call(model="qwen2.5:1.5b")
        metrics.track_llm_model_call(model="llama3.2:3b")
