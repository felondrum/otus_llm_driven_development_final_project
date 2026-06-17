# Тесты context assembler

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestContextAssembler:
    """Tests for ContextAssembler."""
    
    def test_assemble_context_basic(self):
        """Базовая сборка контекста."""
        from orchestrator.context_assembler import ContextAssembler
        
        assembler = ContextAssembler()
        
        result = assembler.assemble_context(
            original_text="Hello",
            profile=None,
            rules=[],
            styles=[]
        )
        
        assert 'Hello' in result
        assert '## Исходное сообщение:' in result
        assert '## Инструкции:' in result
    
    def test_assemble_context_with_profile(self):
        """Сборка с пользовательским профилем."""
        from orchestrator.context_assembler import ContextAssembler
        from common.schemas import UserProfile
        
        assembler = ContextAssembler()
        profile = UserProfile(
            user_id="user123",
            full_name="John Doe",
            role="admin",
            department="IT",
            honorific_type=1,
            communication_mode=1
        )
        
        result = assembler.assemble_context(
            original_text="Hello",
            profile=profile,
            rules=[],
            styles=[]
        )
        
        assert 'Hello' in result
        assert '## Профиль получателя:' in result
        assert 'admin' in result
    
    def test_assemble_context_with_rules(self):
        """Сборка с правилами."""
        from orchestrator.context_assembler import ContextAssembler
        from common.schemas import CorporateRule
        
        assembler = ContextAssembler()
        rules = [CorporateRule(
            rule_id="rule1",
            category="tone",
            priority=1,
            condition="Always",
            transformation="Add greetings",
            example_original="Hi",
            example_adapted="Greetings"
        )]
        
        result = assembler.assemble_context(
            original_text="Hello",
            profile=None,
            rules=rules,
            styles=[]
        )
        
        assert 'Hello' in result
        assert '## Корпоративные правила коммуникации:' in result
        assert 'Add greetings' in result
    
    def test_assemble_context_with_styles(self):
        """Сборка со стилями."""
        from orchestrator.context_assembler import ContextAssembler
        from common.schemas import ArtisticStyle
        
        assembler = ContextAssembler()
        styles = [ArtisticStyle(
            style_id="style1",
            style_name="formal",
            author="Test Author",
            sample_text="This is a formal example.",
            era="Modern"
        )]
        
        result = assembler.assemble_context(
            original_text="Hello",
            profile=None,
            rules=[],
            styles=styles
        )
        
        assert 'Hello' in result
        assert '## Примеры стиля:' in result
    
    def test_parse_llm_response_basic(self):
        """Парсинг ответа LLM."""
        from orchestrator.context_assembler import ContextAssembler
        
        assembler = ContextAssembler()
        response = "This is the adapted response."
        
        result = assembler.parse_llm_response(response, "Original text")
        
        assert result['was_adapted'] is True
        assert result['adapted_text'] == "This is the adapted response."
        assert 'confidence' in result
    
    def test_parse_llm_response_not_adapted(self):
        """Парсинг не адаптированного ответа."""
        from orchestrator.context_assembler import ContextAssembler
        
        assembler = ContextAssembler()
        response = "Same text"
        
        result = assembler.parse_llm_response(response, response)
        
        assert result['was_adapted'] is False
        assert result['confidence'] == 1.0
    
    def test_assemble_context_with_style_name(self):
        """Сборка с указанным стилем."""
        from orchestrator.context_assembler import ContextAssembler
        
        assembler = ContextAssembler()
        
        result = assembler.assemble_context(
            original_text="Hello",
            profile=None,
            rules=[],
            styles=[],
            style_name="formal"
        )
        
        assert 'Hello' in result
        assert '## Требуемый стиль: formal' in result
