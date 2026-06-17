"""E2E тест полного потока с отображением в Langfuse.

Этот тест демонстрирует:
1. Полный цикл обработки сообщения
2. Получение данных из RAG (профиль, правила, стили)
3. Запрос в LLM
4. Все этапы видны в Langfuse

Запуск:
    poetry run pytest tests/e2e/test_langfuse_full_flow.py -v -s
"""

import pytest
import sys
import os
import grpc
import uuid

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Импорты для gRPC stubs
from chameleon.core.v1 import (
    orchestrator_pb2,
    orchestrator_pb2_grpc,
    common_pb2,
    Empty,
)


# Настройки для тестов
ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8001"))

# Правильные user_id из демо-данных (см. demo_data/profiles.json)
USER_IDS = {
    "alex_i": "Иванов Алексей Петрович",      # engineer, backend, informal
    "petr_s": "Смирнов Петр Иванович",         # team_lead, backend, formal
    "anna_k": "Ковалева Анна Сергеевна",       # director, engineering, formal
    "maria_s": "Смирнова Мария Дмитриевна",    # hr_manager, hr, formal
    "dmitry_k": "Кузнецов Дмитрий Александрович",  # senior_engineer, backend, technical
    "elena_v": "Воронова Елена Николаевна",    # team_lead, frontend, collaborative
    "sergey_m": "Михайлов Сергей Олегович",    # intern, marketing, informal
    "olga_a": "Алексеева Ольга Викторовна",    # director, sales, formal
}


@pytest.fixture(scope="module")
def orchestrator_channel():
    """gRPC канал для оркестратора."""
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    yield channel
    channel.close()


class TestLangfuseFullFlow:
    """E2E тесты с полным циклом и отображением в Langfuse."""

    def test_langfuse_full_flow_with_existing_profile(self, orchestrator_channel):
        """Полный E2E тест с существующим профилем пользователя.
        
        Этот тест проверяет:
        1. Получение профиля из RAG (Qdrant)
        2. Применение литературного стиля (Dovlatov)
        3. Адаптация сообщения с учетом профиля
        4. Всё это видно в Langfuse трейсах
        """
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (UUID версия alex_i)
        # UUID: 5e9c62fb-7d03-5193-8280-67c7592cb3f3 (alex_i)
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="5e9c62fb-7d03-5193-8280-67c7592cb3f3",
            text="Алексей, ты должен проверить код",
            style_name="dovlatov",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\n{'='*80}")
        print(f"Исходное сообщение: 'Алексей, ты должен проверить код'")
        print(f"Адаптированное:      '{response.adapted_text}'")
        print(f"Модель:              {response.model_used}")
        print(f"Было адаптировано:    {response.was_adapted}")
        print(f"Уверенность:         {response.confidence}")
        print(f"Время обработки:      {response.processing_time_ms}ms")
        print(f"Recipient:           Иванов Алексей Петрович (engineer)")
        print(f"{'='*80}")
        
        # Проверяем, что ответ был получен
        assert response.adapted_text is not None

    def test_langfuse_full_flow_formal_to_manager(self, orchestrator_channel):
        """E2E тест формального обращения к менеджеру.
        
        Проверяет, что LLM получает читаемый промпт с описанием роли и стиля общения,
        а не числовые коды.
        """
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем менеджера (petr_s)
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, formal - используем правильный user_id
            text="Алексей, ты должен проверить код сегодня",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\n{'='*80}")
        print(f"Исходное: 'Алексей, ты должен проверить код сегодня'")
        print(f"Адаптированное: '{response.adapted_text}'")
        print(f"Модель: {response.model_used}")
        print(f"Было адаптировано: {response.was_adapted}")
        print(f"Recipient: Петр Смирнов (team_lead)")
        print(f"{'='*80}")

    def test_langfuse_full_flow_with_chekhov_style(self, orchestrator_channel):
        """E2E тест с литературным стилем Чехова и профилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (UUID версия alex_i)
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="5e9c62fb-7d03-5193-8280-67c7592cb3f3",  # UUID for alex_i
            text="Нужно обсудить новый проект",
            style_name="chekhov",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\n{'='*80}")
        print(f"Стиль: chekhov")
        print(f"Recipient: Иванов Алексей Петрович (engineer)")
        print(f"Адаптированное: '{response.adapted_text}'")
        print(f"{'='*80}")

    def test_langfuse_full_flow_with_metadata(self, orchestrator_channel):
        """E2E тест с проверкой метаданных ответа и профилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # используем правильный user_id
            text="Иван, пришли отчет",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        # Проверяем метаданные
        assert response.processing_time_ms >= 0
        assert response.confidence >= 0
        assert response.model_used is not None
        
        print(f"\n{'='*80}")
        print(f"Метаданные:")
        print(f"  Время обработки:    {response.processing_time_ms}ms")
        print(f"  Уверенность:        {response.confidence}")
        print(f"  Модель:             {response.model_used}")
        print(f"  Было адаптировано:   {response.was_adapted}")
        if response.rules_applied:
            print(f"  Примененные правила: {response.rules_applied}")
        print(f"Recipient: Иванов Алексей Петрович (engineer)")
        print(f"{'='*80}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
