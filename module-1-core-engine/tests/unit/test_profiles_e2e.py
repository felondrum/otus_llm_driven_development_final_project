"""Unit тесты для проверки полных профилей пользователей."""

import sys
import os
import uuid
import pytest

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from retriever.qdrant_client import get_qdrant_client
from orchestrator.context_assembler import get_context_assembler


class TestUserProfiles:
    """Тесты всех профилей пользователей."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Qdrant client."""
        return get_qdrant_client()
    
    @pytest.fixture(scope="class")
    def assembler(self):
        """Context assembler."""
        return get_context_assembler()
    
    def test_profile_alex_i(self, client, assembler):
        """Тест профиля alex_i (engineer, informal)."""
        profile = client.get_profile("alex_i")
        assert profile is not None
        assert profile["full_name"] == "Иванов Алексей Петрович"
        assert profile["role"] == "engineer"
        assert profile["department"] == "backend"
        assert profile["honorific_type"] == 1  # FIRST_NAME
        assert profile["communication_mode"] == 2  # INFORMAL
        
        # Проверка форматирования (используем dict-профиль)
        prompt = assembler.assemble_context(
            original_text="Тест",
            profile=profile,
        )
        assert "по имени" in prompt
        assert "неформальный" in prompt
    
    def test_profile_petr_s(self, client, assembler):
        """Тест профиля petr_s (team_lead, formal, patronymic)."""
        profile = client.get_profile("petr_s")
        assert profile is not None
        assert profile["full_name"] == "Смирнов Петр Иванович"
        assert profile["role"] == "team_lead"
        assert profile["department"] == "backend"
        assert profile["honorific_type"] == 3  # PATRONYMIC
        assert profile["communication_mode"] == 1  # FORMAL
    
    def test_profile_maria_s(self, client, assembler):
        """Тест профиля maria_s (HR manager, formal)."""
        profile = client.get_profile("maria_s")
        assert profile is not None
        assert profile["full_name"] == "Смирнова Мария Дмитриевна"
        assert profile["role"] == "hr_manager"
        assert profile["department"] == "hr"
        assert profile["honorific_type"] == 3  # PATRONYMIC
        assert profile["communication_mode"] == 1  # FORMAL
    
    def test_profile_dmitry_k(self, client, assembler):
        """Тест профиля dmitry_k (senior engineer, technical)."""
        profile = client.get_profile("dmitry_k")
        assert profile is not None
        assert profile["full_name"] == "Кузнецов Дмитрий Александрович"
        assert profile["role"] == "senior_engineer"
        assert profile["department"] == "backend"
        assert profile["honorific_type"] == 1  # FIRST_NAME
        assert profile["communication_mode"] == 3  # TECHNICAL
    
    def test_profile_elena_v(self, client, assembler):
        """Тест профиля elena_v (team_lead, collaborative)."""
        profile = client.get_profile("elena_v")
        assert profile is not None
        assert profile["full_name"] == "Воронова Елена Николаевна"
        assert profile["role"] == "team_lead"
        assert profile["department"] == "frontend"
        assert profile["communication_mode"] == 4  # COLLABORATIVE (дипломатичный)
    
    def test_profile_sergey_m(self, client, assembler):
        """Тест профиля sergey_m (intern, informal)."""
        profile = client.get_profile("sergey_m")
        assert profile is not None
        assert profile["full_name"] == "Михайлов Сергей Олегович"
        assert profile["role"] == "intern"
        assert profile["department"] == "marketing"
        assert profile["communication_mode"] == 2  # INFORMAL
    
    def test_profile_olga_a(self, client, assembler):
        """Тест профиля olga_a (director of sales, formal)."""
        profile = client.get_profile("olga_a")
        assert profile is not None
        assert profile["full_name"] == "Алексеева Ольга Викторовна"
        assert profile["role"] == "director"
        assert profile["department"] == "sales"
        assert profile["honorific_type"] == 4  # TITLE_LAST
        assert profile["communication_mode"] == 1  # FORMAL
    
    def test_profile_unknown_fallback(self, client, assembler):
        """Тест fallback профиля с unknown данными."""
        profile = client.get_profile("nonexistent_user_999999")
        assert profile is not None
        assert profile["role"] == "employee"
        assert profile["department"] == "unknown"
    
    def test_profile_formatting_all(self, client, assembler):
        """Проверка форматирования всех профилей."""
        user_ids = [
            "alex_i", "petr_s", "anna_k", "maria_s", "dmitry_k",
            "elena_v", "sergey_m", "olga_a", "nonexistent_user_999999"
        ]
        
        for user_id in user_ids:
            profile = client.get_profile(user_id)
            if profile:
                # Проверка, что форматирование не ломается
                prompt = assembler.assemble_context(
                    original_text="Тест",
                    profile=profile,
                )
                assert len(prompt) > 0
                assert "Профи" in prompt or "Профиль" in prompt
    
    def test_profile_known_triggers(self, client):
        """Проверка известных триггеров."""
        profile = client.get_profile("alex_i")
        assert profile is not None
        assert "known_triggers" in profile
        assert len(profile["known_triggers"]) > 0
        
        # Проверка конкретных триггеров для некоторых профилей
        maria_profile = client.get_profile("maria_s")
        assert maria_profile is not None
        assert "salary" in maria_profile.get("known_triggers", [])
        assert "vacation" in maria_profile.get("known_triggers", [])
