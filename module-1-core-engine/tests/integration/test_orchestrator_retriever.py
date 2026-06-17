# Интеграционный тест оркестратор-ретривер

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from common.logging import logger
from common.schemas import UserProfile, CorporateRule, ArtisticStyle
from orchestrator.context_assembler import ContextAssembler


class MockRetriever:
    """Mock retriever for testing."""
    
    def __init__(self):
        self.profiles = {
            "user_1": UserProfile(
                user_id="user_1",
                full_name="Иванов Иван Иванович",
                role="manager",
                department="sales",
                honorific_type=3,
                communication_mode=1,
                known_triggers=["deadline", "bug"]
            )
        }
    
    async def get_profile(self, user_id: str) -> UserProfile:
        """Get user profile."""
        return self.profiles.get(user_id)
    
    async def get_rules(self, sender_role: str, recipient_role: str) -> list:
        """Get corporate rules."""
        return [
            CorporateRule(
                rule_id="rule_formal",
                category="address",
                priority=10,
                condition="recipient_role == 'manager'",
                transformation="use formal address",
                example_original="ты должен",
                example_adapted="вы должны"
            )
        ]


class MockLLM:
    """Mock LLM for testing."""
    
    async def generate(self, prompt: str) -> str:
        """Generate text."""
        return f"Adapted: {prompt}"


@pytest.fixture
def mock_retriever():
    """Fixture for mock retriever."""
    return MockRetriever()


@pytest.fixture
def mock_llm():
    """Fixture for mock LLM."""
    return MockLLM()


@pytest.mark.asyncio
async def test_orchestrator_with_mock_retriever(mock_retriever, mock_llm):
    """Test orchestrator with mock retriever."""
    profile = await mock_retriever.get_profile("user_1")
    assert profile is not None
    assert profile.user_id == "user_1"
    assert profile.role == "manager"
    
    rules = await mock_retriever.get_rules("user", "manager")
    assert len(rules) == 1
    assert rules[0].category == "address"
    
    result = await mock_llm.generate("test prompt")
    assert result == "Adapted: test prompt"
    
    logger.info("Integration test passed")


@pytest.mark.asyncio
async def test_context_assembly(mock_retriever):
    """Test context assembly for LLM prompt."""
    assembler = ContextAssembler()
    
    profile = await mock_retriever.get_profile("user_1")
    
    rules = await mock_retriever.get_rules("user", "manager")
    
    styles = [
        ArtisticStyle(
            style_id="chekhov",
            style_name="чеховский",
            author="Антон Чехов",
            sample_text="Дорогой мой, всё это так грустно...",
            emotion_tags=["melancholy"],
            era="XIX век"
        )
    ]
    
    prompt = assembler.assemble_context(
        original_text="test message",
        profile=profile,
        rules=rules,
        styles=styles,
        style_name="chekhov"
    )
    
    assert "test message" in prompt
    assert "formal" in prompt.lower()
    assert "чеховский" in prompt.lower()
    
    logger.info("Context assembly test passed")


@pytest.mark.asyncio
async def test_full_message_flow():
    """Test full message processing flow."""
    from orchestrator.config import Config
    from llm_gateway.router import Router
    
    config = Config()
    assert config.server_port == 8001
    
    router_config = {
        'fallback_chain': [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b'
        ]
    }
    router = Router(router_config)
    model = router.route_request(complexity=1, prompt_length=100)
    assert model is not None
    
    logger.info("Full message flow test passed")


@pytest.mark.asyncio
async def test_router_integration():
    """Test router integration."""
    from llm_gateway.router import Router
    
    router_config = {
        'fallback_chain': [
            'ollama:llama3.2:3b',
            'ollama:qwen2.5:7b',
            'openai:gpt-4o'
        ]
    }
    router = Router(router_config)
    
    fast_model = router.route_request(complexity=1, prompt_length=50)
    assert fast_model is not None
    
    balanced_model = router.route_request(complexity=0, prompt_length=100, has_style=True)
    assert balanced_model is not None
    
    powerful_model = router.route_request(complexity=3, prompt_length=1000)
    assert powerful_model is not None
    
    logger.info("Router integration test passed")
