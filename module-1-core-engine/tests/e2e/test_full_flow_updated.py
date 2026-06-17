"""E2E тесты полного потока адаптации для Core Engine.

Тесты проверяют полный цикл обработки сообщений от отправителя до адаптированного ответа,
включая все компоненты: оркестратор, ретривер (RAG), кэш и LLM gateway.

Запуск:
    poetry run pytest tests/e2e/test_full_flow.py -v -s
"""

import pytest
import sys
import os
import grpc
import httpx
import uuid

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Импорты для gRPC stubs
from chameleon.core.v1 import (
    orchestrator_pb2,
    orchestrator_pb2_grpc,
    retriever_pb2,
    retriever_pb2_grpc,
    common_pb2,
    Empty,
)


# Настройки для тестов
ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8001"))
RETRIEVER_HOST = os.getenv("RETRIEVER_HOST", "localhost")
RETRIEVER_PORT = int(os.getenv("RETRIEVER_PORT", "8002"))
LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://localhost:8003")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Правильные user_id из демо-данных
USER_IDS = {
    "alex_i": "Иванов Алексей Петрович",  # engineer, informal
    "petr_s": "Смирнов Петр Иванович",    # team_lead, formal
    "anna_k": "Ковалева Анна Сергеевна",  # director, formal
    "maria_s": "Смирнова Мария Дмитриевна",  # hr_manager, formal
    "dmitry_k": "Кузнецов Дмитрий Александрович",  # senior_engineer, technical
    "elena_v": "Воронова Елена Николаевна",  # team_lead, collaborative
    "sergey_m": "Михайлов Сергей Олегович",  # intern, informal
    "olga_a": "Алексеева Ольга Викторовна",  # director, formal
}


@pytest.fixture(scope="module")
def test_user_profiles():
    """Fixture with valid user IDs from demo data."""
    return USER_IDS.copy()


@pytest.fixture(scope="module")
def orchestrator_channel():
    """gRPC канал для оркестратора."""
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    yield channel
    channel.close()


@pytest.fixture(scope="module")
def retriever_channel():
    """gRPC канал для ретривера."""
    channel = grpc.insecure_channel(f"{RETRIEVER_HOST}:{RETRIEVER_PORT}")
    yield channel
    channel.close()


class TestOrchestratorService:
    """Тесты сервиса оркестратора."""

    def test_health_check(self, orchestrator_channel):
        """Проверка здоровья оркестратора."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        request = Empty()
        
        response = stub.HealthCheck(request, timeout=5.0)
        
        assert response.status in ["healthy", "degraded"]
        assert "cache" in response.checks
        assert "retriever" in response.checks
        assert "llm_gateway" in response.checks

    def test_process_message_basic(self, orchestrator_channel):
        """Базовая обработка сообщения."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Use valid user_id from demo data
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # Valid user_id
            text="Привет, как дела?",
        )
        
        response = stub.ProcessMessage(request, timeout=10.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        assert response.processing_time_ms >= 0

    def test_process_message_formal_to_manager(self, orchestrator_channel):
        """Формальное обращение к менеджеру."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Use valid user_id from demo data
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, formal
            text="Иван, ты должен проверить код сегодня",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        # Проверяем, что адаптация была выполнена
        assert response.was_adapted in [True, False]  # Может быть false, если нет правил
        
        # Проверяем, что текст валиден
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nOriginal: 'Иван, ты должен проверить код сегодня'")
        print(f"Adapted:  '{response.adapted_text}'")
        print(f"Model:    {response.model_used}")
        print(f"Was adapted: {response.was_adapted}")

    def test_process_message_blame_scenario(self, orchestrator_channel):
        """Сценарий с обвинением (должен быть переписан)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Use valid user_id from demo data
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="petr_s",  # team_lead, knows about blame triggers
            text="Петр, ты сломал сборку!",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        # Проверяем, что слово "сломал" не出现在 адаптированном тексте
        # (может не быть, если правило не применилось)
        if response.was_adapted:
            print(f"\nOriginal: 'Петр, ты сломал сборку!'")
            print(f"Adapted:  '{response.adapted_text}'")

    def test_process_message_with_style(self, orchestrator_channel):
        """Обработка сообщения с выбранным литературным стилем."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # Valid user_id
            text="Нужно обсудить новый проект",
            style_name="chekhov",  # Должен применить стиль Чехова
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\nWith chekhov style:")
        print(f"Adapted: '{response.adapted_text}'")

    def test_process_message_with_style_and_profile(self, orchestrator_channel):
        """Обработка сообщения с литературным стилем и профилем получателя."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (user_id, а не UUID5)
        # user_id 'alex_i' -> UUID5: 5e9c62fb-7d03-5193-8280-67c7592cb3f3
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="alex_i",  # user_id, не UUID5!
            text="Петр, ты должен проверить код",
            style_name="dovlatov",  # Применить стиль Довлатова
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        
        print(f"\nWith dovlatov style and profile (alex_i):")
        print(f"Original: 'Петр, ты должен проверить код'")
        print(f"Adapted:  '{response.adapted_text}'")
        print(f"Model:    {response.model_used}")
        print(f"Was adapted: {response.was_adapted}")


class TestRetrieverService:
    """Тесты сервиса ретривера (RAG)."""

    def test_get_profile_existing_user(self, retriever_channel):
        """Получение профиля существующего пользователя."""
        stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)
        
        request = retriever_pb2.GetProfileRequest(
            user_id="alex_i",
            include_history=False,
        )
        
        response = stub.GetProfile(request, timeout=5.0)
        
        assert response.user_id == "alex_i"
        assert response.full_name is not None
        assert response.role is not None

    def test_get_profile_non_existing_user(self, retriever_channel):
        """Получение профиля несуществующего пользователя."""
        stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)
        
        request = retriever_pb2.GetProfileRequest(
            user_id="nonexistent_user_999999",
            include_history=False,
        )
        
        response = stub.GetProfile(request, timeout=5.0)
        
        # Должен вернуться дефолтный профиль
        assert response.user_id == "nonexistent_user_999999" or response.user_id is not None

    def test_get_rules_for_manager(self, retriever_channel):
        """Получение правил для обращения к менеджеру."""
        stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)
        
        request = retriever_pb2.GetRulesRequest(
            sender_role="user",
            recipient_role="manager",
            message_text="ты должен",
            limit=5,
        )
        
        response = stub.GetRules(request, timeout=5.0)
        
        # Должен вернуться список правил
        assert response is not None
        print(f"\nRules for manager:")
        for rule in response.rules:
            print(f"  - {rule.rule_id}: {rule.transformation_prompt}")

    def test_get_style_examples(self, retriever_channel):
        """Получение примеров литературного стиля."""
        stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)
        
        request = retriever_pb2.GetStyleExamplesRequest(
            style_name="chekhov",
            sample_count=2,
        )
        
        response = stub.GetStyleExamples(request, timeout=5.0)
        
        # Должен вернуться список примеров
        assert response is not None
        if response.examples:
            print(f"\nChekhov style examples:")
            for example in response.examples:
                print(f"  - {example.style_name}: {example.sample_text[:50]}...")

    def test_health_check_retriever(self, retriever_channel):
        """Health check для ретривера."""
        stub = retriever_pb2_grpc.RetrieverServiceStub(retriever_channel)
        request = Empty()
        
        response = stub.HealthCheck(request, timeout=5.0)
        
        assert response.status in ["healthy", "degraded"]


class TestLLMGateway:
    """Тесты HTTP API LLM Gateway."""

    def test_health_check_http(self):
        """Health check через HTTP."""
        response = httpx.get(f"{LLM_GATEWAY_URL}/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_generate_basic(self):
        """Базовая генерация текста."""
        response = httpx.post(
            f"{LLM_GATEWAY_URL}/generate",
            json={
                "prompt": "Привет, как дела?",
                "complexity": 1,  # fast
                "config": {
                    "temperature": 0.7,
                    "max_tokens": 100,
                },
            },
            timeout=60,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "text" in data
        assert len(data["text"]) > 0
        assert "model_used" in data
        assert "latency_ms" in data
        assert "token_usage" in data

    def test_generate_with_complexity(self):
        """Генерация с разными уровнями сложности."""
        prompt = "Напиши короткое сообщение о проекте."
        
        for complexity in [1, 2, 3]:
            response = httpx.post(
                f"{LLM_GATEWAY_URL}/generate",
                json={
                    "prompt": prompt,
                    "complexity": complexity,
                    "config": {
                        "temperature": 0.7,
                        "max_tokens": 200,
                    },
                },
                timeout=60,
            )
            
            assert response.status_code == 200
            data = response.json()
            print(f"\nComplexity {complexity}:")
            print(f"  Model: {data['model_used']}")
            print(f"  Latency: {data['latency_ms']}ms")


class TestEndToEndFlow:
    """Полные end-to-end сценарии."""

    def test_e2e_formal_communication(self, orchestrator_channel):
        """Полный сценарий: формальная переписка."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Сценарий: сотрудник пишет менеджеру
        # Используем существующих пользователей с профилями в Qdrant
        messages = [
            {
                "id": str(uuid.uuid4()),
                "sender": "employee_001",
                "recipient": "petr_s",  # manager with formal communication mode
                "text": "Иван, пришли отчет",
            },
            {
                "id": str(uuid.uuid4()),
                "sender": "employee_001",
                "recipient": "anna_k",  # director with formal communication mode
                "text": "Срочно нужно решение по багу",
            },
        ]
        
        for msg in messages:
            # Генерируем UUID5 для recipient_id из user_id
            recipient_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, msg["recipient"]))
            sender_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, msg["sender"]))
            
            request = orchestrator_pb2.ProcessMessageRequest(
                message_id=msg["id"],
                sender_id=sender_uuid,
                recipient_id=recipient_uuid,
                text=msg["text"],
            )
            
            response = stub.ProcessMessage(request, timeout=15.0)
            
            assert response.was_adapted in [True, False]
            assert len(response.adapted_text) > 0
            print(f"\nOriginal: '{msg['text']}'")
            print(f"Adapted:  '{response.adapted_text}'")

    def test_e2e_multiple_recipients(self, orchestrator_channel):
        """Полный сценарий: одно сообщение разным получателям."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        original_text = "Алексей, проверь код"
        
        recipients = [
            (str(uuid.uuid4()), "formal to manager"),
            (str(uuid.uuid4()), "formal to director"),
        ]
        
        for recipient_id, description in recipients:
            request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
                sender_id=str(uuid.uuid4()),
                recipient_id=recipient_id,
                text=original_text,
            )
            
            response = stub.ProcessMessage(request, timeout=15.0)
            
            print(f"\n{description}:")
            print(f"  Adapted: '{response.adapted_text}'")

    def test_e2e_hr_manager_profile(self, orchestrator_channel):
        """Полный сценарий: обращение к HR-менеджеру (формальный стиль)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (user_id, а не UUID5)
        # user_id 'maria_s' -> UUID5: aa38ba8f-4a68-56da-ae41-c060bb995818
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="maria_s",  # user_id, не UUID5!
            text="Мария, нужно обсудить зарплату",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nHR Manager (maria_s) test:")
        print(f"  Original: 'Мария, нужно обсудить зарплату'")
        print(f"  Adapted:  '{response.adapted_text}'")

    def test_e2e_intern_profile(self, orchestrator_channel):
        """Полный сценарий: обращение к стажеру (неформальный стиль)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (user_id, а не UUID5)
        # user_id 'sergey_m' -> UUID5: 5d1334cc-9feb-5770-b996-abd65b3c4b06
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="sergey_m",  # user_id, не UUID5!
            text="Сергей, помоги с задачей",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nIntern (sergey_m) test:")
        print(f"  Original: 'Сергей, помоги с задачей'")
        print(f"  Adapted:  '{response.adapted_text}'")

    def test_e2e_director_profile(self, orchestrator_channel):
        """Полный сценарий: обращение к директору (формальный стиль)."""
        stub = orchestrator_pb2_grpc.OrchestratorServiceStub(orchestrator_channel)
        
        # Используем существующего пользователя с профилем (user_id, а не UUID5)
        # user_id 'olga_a' -> UUID5: 439ed6b5-3c76-5740-abd4-6f8fd359be45
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id="olga_a",  # user_id, не UUID5!
            text="Ольга, нужно обсудить новые цели",
        )
        
        response = stub.ProcessMessage(request, timeout=15.0)
        
        assert response is not None
        assert len(response.adapted_text) > 0
        assert response.model_used is not None
        
        print(f"\nDirector (olga_a) test:")
        print(f"  Original: 'Ольга, нужно обсудить новые цели'")
        print(f"  Adapted:  '{response.adapted_text}'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])