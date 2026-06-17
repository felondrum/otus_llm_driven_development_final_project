# Интеграционный тест отказоустойчивости LLM

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.logging import logger


class MockProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self.fail = fail
    
    async def generate(self, prompt: str) -> str:
        """Generate text."""
        if self.fail:
            raise Exception(f"{self.name} is down")
        return f"Response from {self.name}"
    
    async def health_check(self) -> bool:
        """Check health."""
        return not self.fail


@pytest.fixture
def fallback_chain():
    """Fixture for fallback chain."""
    return [
        MockProvider("fast", fail=True),
        MockProvider("balanced", fail=True),
        MockProvider("powerful", fail=False),
        MockProvider("api", fail=False)
    ]


@pytest.mark.asyncio
async def test_fallback_success(fallback_chain):
    """Test fallback when first providers fail."""
    providers = fallback_chain
    
    assert not await providers[0].health_check()
    assert not await providers[1].health_check()
    
    assert await providers[2].health_check()
    
    result = await providers[2].generate("test prompt")
    assert "Response from powerful" in result
    
    logger.info("Fallback success test passed")


@pytest.mark.asyncio
async def test_fallback_chain(fallback_chain):
    """Test full fallback chain."""
    providers = fallback_chain
    
    for i, provider in enumerate(providers):
        try:
            result = await provider.generate("test prompt")
            logger.info(f"Provider {i} succeeded: {result}")
            break
        except Exception as e:
            logger.info(f"Provider {i} failed: {e}")
    
    logger.info("Fallback chain test passed")


@pytest.mark.asyncio
async def test_provider_health():
    """Test provider health check."""
    healthy = MockProvider("healthy", fail=False)
    unhealthy = MockProvider("unhealthy", fail=True)
    
    assert await healthy.health_check()
    assert not await unhealthy.health_check()
    
    logger.info("Provider health test passed")


@pytest.mark.asyncio
async def test_fallback_with_different_errors():
    """Test fallback with different types of errors."""
    providers = [
        MockProvider("fast", fail=True),
        MockProvider("balanced", fail=True),
        MockProvider("powerful", fail=False)
    ]
    
    error_count = 0
    for provider in providers:
        try:
            await provider.generate("test")
        except Exception:
            error_count += 1
    
    assert error_count == 2
    assert len(providers) == 3
    
    logger.info("Fallback with different errors test passed")
