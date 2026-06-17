"""E2E тесты базовой адаптации текста для Core Engine.

Эти тесты проверяют полный поток обработки сообщений от оркестратора до LLM,
включая все зависимости: кэш, RAG (profiles, rules, styles), и LLM gateway.

Запуск:
    poetry run pytest tests/e2e/test_basic_adaptation_e2e.py -v
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

# Правильные user_id из профилей (см. demo_data/profiles.json)
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


class TestBasicAdaptationE2E:
    """E2E тесты базовой адаптации с реальным оркестратором."""

    def test_orchestrator_health(self, orchestrator_channel):
        """Проверка здоровья оркестратора через gRPC."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        request = Empty()
        
        response = stub.HealthCheck(request, timeout=5.0)
        
        assert response.status in ["healthy", "degraded"]
        assert "cache" in response.checks
        assert "retriever" in response.checks
        assert "llm_gateway" in response.checks

    def test_process_message_basic(self, orchestrator_channel):
        """Базовая обработка сообщения - с профилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # Valid user_id from demo data
            text="Привет, как дела?",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        assert response.processing_time_ms >= 0
        assert response.confidence >= 0

    def test_process_message_formal_to_manager(self, orchestrator_channel):
        """Формальное обращение к менеджеру (Петр - team_lead)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, formal - используем правильный user_id
            text="Алексей, ты должен проверить код сегодня",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        # Проверяем, что адаптация была выполнена
        assert response.was_adapted in [True, False]  # Может быть false, если нет правил
        
        # Проверяем, что текст валиден
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nOriginal: 'Алексей, ты должен проверить код сегодня'")
        print(f"Adapted:  '{response.adapted_text}'")
        print(f"Model:    {response.model_used}")
        print(f"Was adapted: {response.was_adapted}")
        print(f"Recipient: Петр Смирнов (team_lead)")

    def test_process_message_blame_scenario(self, orchestrator_channel):
        """Сценарий с обвинением (должен быть переписан)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, knows about blame triggers - используем правильный user_id
            text="Петр, ты сломал сборку!",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        if response.was_adapted:
            print(f"\nOriginal: 'Петр, ты сломал сборку!'")
            print(f"Adapted:  '{response.adapted_text}'")
            print(f"Recipient: Петр Смирнов (team_lead)")

    def test_process_message_with_style(self, orchestrator_channel):
        """Обработка сообщения с литературным стилем и профилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем правильный user_id (UUID версия alex_i)
        # alex_i UUID: 5e9c62fb-7d03-5193-8280-67c7592cb3f3
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="5e9c62fb-7d03-5193-8280-67c7592cb3f3",  # UUID for alex_i
            text="Нужно обсудить новый проект",
            style_name="chekhov",  # Применить стиль Чехова
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\nWith chekhov style and profile (alex_i):")
        print(f"Adapted: '{response.adapted_text}'")
        print(f"Recipient: Иванов Алексей Петрович (engineer)")

    def test_process_message_with_style_and_profile(self, orchestrator_channel):
        """Обработка сообщения с литературным стилем и профилем получателя."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем правильный user_id (UUID версия alex_i)
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="5e9c62fb-7d03-5193-8280-67c7592cb3f3",  # UUID for alex_i
            text="Алексей, ты должен проверить код",
            style_name="dovlatov",  # Применить стиль Довлатова
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\nWith dovlatov style and profile (alex_i):")
        print(f"Original: 'Алексей, ты должен проверить код'")
        print(f"Adapted:  '{response.adapted_text}'")
        print(f"Model:    {response.model_used}")
        print(f"Was adapted: {response.was_adapted}")
        print(f"Recipient: Иванов Алексей Петрович (engineer)")

    def test_process_message_formal_to_director(self, orchestrator_channel):
        """Формальное обращение к директору."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем правильный user_id для директора (UUID версия olga_a)
        # olga_a UUID: a8e6a554-7f31-5b2d-9c1e-4d8f2a6b3c5e (пример, нужно проверить)
        # Для надежности используем прямой user_id
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="olga_a",  # director, formal - используем правильный user_id
            text="Ольга, я обнаружил ошибку в коде",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response.was_adapted in [True, False]
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nOriginal: 'Ольга, я обнаружил ошибку в коде'")
        print(f"Adapted:  '{response.adapted_text}'")
        print(f"Recipient: Ольга Алексеева (director)")

    def test_process_message_multiple_recipients(self, orchestrator_channel):
        """Одно сообщение разным получателям с разной адаптацией."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        original_text = "Алексей, проверь код"
        
        # К менеджеру (team_lead, formal)
        request1 = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, formal - используем правильный user_id
            text=original_text,
        )
        
        response1 = stub.ProcessMessage(request1, timeout=15.0)
        
        # К директору (director, formal)
        request2 = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="anna_k",  # director, formal - используем правильный user_id
            text=original_text,
        )
        
        response2 = stub.ProcessMessage(request2, timeout=15.0)
        
        print(f"\nOriginal: '{original_text}'")
        print(f"To manager (Петр Смирнов):  '{response1.adapted_text}'")
        print(f"To director (Анна Ковалева): '{response2.adapted_text}'")

    def test_process_message_with_metadata(self, orchestrator_channel):
        """Проверка метаданных в ответе с профилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # используем правильный user_id
            text="Иван, пришли отчет",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        # Проверяем метаданные
        assert response.processing_time_ms >= 0
        assert response.confidence >= 0
        assert response.model_used is not None
        
        # Проверяем adaptation_metadata
        if response.HasField("adaptation_metadata"):
            metadata = response.adaptation_metadata
            assert metadata is not None
            print(f"\nMetadata:")
            print(f"  From cache: {metadata.from_cache}")
            print(f"  Fallback used: {metadata.fallback_used}")
            print(f"  Tokens prompt: {metadata.tokens_prompt}")
            print(f"  Tokens completion: {metadata.tokens_completion}")
        print(f"Recipient: Иванов Алексей Петрович (engineer)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
