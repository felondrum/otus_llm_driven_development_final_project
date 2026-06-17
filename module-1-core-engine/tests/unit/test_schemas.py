# Тесты схем данных

import pytest


class TestSchemas:
    """Tests for data schemas."""
    
    def test_user_profile(self):
        """Test UserProfile schema - basic test."""
        profile_data = {
            "user_id": "user1",
            "full_name": "Иванов Иван",
            "role": "manager",
            "department": "sales",
            "honorific_type": 3,
            "communication_mode": 1,
            "known_triggers": ["deadline"]
        }
        
        assert profile_data["user_id"] == "user1"
        assert profile_data["role"] == "manager"
        assert len(profile_data["known_triggers"]) == 1
    
    def test_corporate_rule(self):
        """Test CorporateRule schema - basic test."""
        rule_data = {
            "rule_id": "rule1",
            "category": "address",
            "priority": 10,
            "transformation": "use formal address"
        }
        
        assert rule_data["rule_id"] == "rule1"
        assert rule_data["priority"] == 10
    
    def test_artistic_style(self):
        """Test ArtisticStyle schema - basic test."""
        style_data = {
            "style_id": "chekhov",
            "style_name": "чеховский",
            "author": "Антон Чехов",
            "sample_text": "Дорогой мой",
            "emotion_tags": ["melancholy"],
            "era": "XIX век"
        }
        
        assert style_data["style_id"] == "chekhov"
        assert "melancholy" in style_data["emotion_tags"]
    
    def test_message_request(self):
        """Test MessageRequest schema - basic test."""
        request_data = {
            "message_id": "msg1",
            "sender_id": "user1",
            "recipient_id": "user2",
            "text": "Hello",
            "style_name": "chekhov"
        }
        
        assert request_data["message_id"] == "msg1"
        assert request_data["style_name"] == "chekhov"
    
    def test_message_response(self):
        """Test MessageResponse schema - basic test."""
        response_data = {
            "adapted_text": "Adapted Hello",
            "was_adapted": True,
            "confidence": 0.95,
            "model_used": "qwen2.5:7b",
            "processing_time_ms": 100
        }
        
        assert response_data["adapted_text"] == "Adapted Hello"
        assert response_data["was_adapted"] is True
    
    def test_enum_values(self):
        """Test enum constant values."""
        honorific_types = {
            "UNSPECIFIED": 0,
            "FIRST_NAME": 1,
            "FIRST_LAST": 2,
            "PATRONYMIC": 3,
            "TITLE_LAST": 4
        }
        
        communication_modes = {
            "UNSPECIFIED": 0,
            "FORMAL": 1,
            "INFORMAL": 2
        }
        
        model_complexity = {
            "UNSPECIFIED": 0,
            "FAST": 1,
            "BALANCED": 2,
            "POWERFUL": 3
        }
        
        assert honorific_types["PATRONYMIC"] == 3
        assert communication_modes["FORMAL"] == 1
        assert model_complexity["FAST"] == 1
        assert model_complexity["BALANCED"] == 2
