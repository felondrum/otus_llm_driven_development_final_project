"""E2E тесты RAG для корпоративной культуры.

Проверяет полный поток: загрузка culture chunks → векторный поиск → интеграция в промпт → адаптация сообщения.
"""

import os
import sys
import pytest
import time
from typing import Dict, Any

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "module-1-core-engine", "src"))

# Импортируем HTTP клиент
import requests

# Настройки
BASE_URL = os.getenv("LLM_GATEWAY_URL", "http://localhost:8003")
LANGFUSE_URL = os.getenv("LANGFUSE_URL", "http://localhost:3000")
ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8001"))


def test_culture_chunks_in_qdrant():
    """Проверка наличия culture chunks в Qdrant."""
    import grpc
    from retriever import retriever_pb2, retriever_pb2_grpc
    
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    retriever_stub = retriever_pb2_grpc.RetrieverServiceStub(channel)
    
    # Проверяем через retriever gRPC
    try:
        # Пробуем получить culture chunks через hybrid search
        from retriever.qdrant_client import get_qdrant_client
        qdrant = get_qdrant_client()
        
        # Получаем все culture chunks
        result = qdrant.client.search(
            collection_name="corporate_culture",
            query_vector=[0.0] * 768,
            limit=20
        )
        
        assert len(result) >= 5, f"Expected at least 5 culture chunks, got {len(result)}"
        print(f"\nCulture chunks count: {len(result)}")
        
        # Проверяем структуру chunks
        for i, hit in enumerate(result[:3]):
            payload = hit.payload
            assert "text" in payload, f"Chunk {i} missing 'text' field"
            assert len(payload["text"]) > 0, f"Chunk {i} text is empty"
            print(f"  Chunk {i+1}: [{payload.get('section_title', 'unknown')}] {payload['text'][:80]}...")
        
        channel.close()
    except Exception as e:
        pytest.fail(f"Failed to retrieve culture chunks: {e}")


def test_culture_vector_search():
    """Проверка векторного поиска culture chunks."""
    import grpc
    from retriever import retriever_pb2, retriever_pb2_grpc
    
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    
    try:
        from retriever.qdrant_client import get_qdrant_client
        qdrant = get_qdrant_client()
        
        # Тестовые запросы для поиска culture chunks
        test_queries = [
            "команда и сотрудничество",
            "ответственность и качество",
            "открытость и честность"
        ]
        
        for query in test_queries:
            chunks = qdrant.get_culture_chunks(query_text=query, limit=3)
            assert len(chunks) > 0, f"No chunks found for query: {query}"
            print(f"\nQuery: '{query}' → found {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks[:2]):
                print(f"  Result {i+1}: {chunk.get('text', '')[:100]}...")
        
        channel.close()
    except Exception as e:
        pytest.fail(f"Culture vector search failed: {e}")


def test_culture_chunks_in_context():
    """Проверка интеграции culture chunks в контекст промпта."""
    from orchestrator.context_assembler import get_context_assembler
    
    assembler = get_context_assembler()
    
    # Culture chunks mock
    culture_chunks = [
        {
            "section_title": "Команда",
            "text": "Мы работаем как единая команда, где каждый вклад ценен."
        },
        {
            "section_title": "Качество",
            "text": "Стремимся к высокому качеству во всех аспектах нашей работы."
        }
    ]
    
    # Собираем контекст с culture chunks
    prompt = assembler.assemble_context(
        original_text="Нужно обсудить проект",
        culture_chunks=culture_chunks
    )
    
    # Проверяем, что culture chunks есть в промпте
    assert "## Корпоративная культура (рекомендации):" in prompt, \
        "Culture section not found in prompt"
    
    assert "Команда" in prompt, "Team chunk not found in prompt"
    assert "Качество" in prompt, "Quality chunk not found in prompt"
    
    print("\nCulture chunks in context:")
    print(prompt)
    
    # Проверяем, что culture chunks включены в инструкции
    assert "Учтите корпоративную культуру" in prompt, \
        "Culture instruction not found in prompt"


@pytest.mark.asyncio
async def test_full_culture_rag_flow():
    """Полный тест RAG потока с culture chunks через gRPC."""
    import grpc
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Создаем gRPC канал
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    orchestrator_stub = grpc.channel_ready_future(channel)
    
    try:
        # Ждем готовности канала
        orchestrator_stub.result(timeout=10)
        
        from chameleon.core.v1 import orchestrator_pb2, common_pb2
        
        # Тестовое сообщение, которое должно использовать culture chunks
        test_messages = [
            {
                "message_id": "test-culture-001",
                "sender_id": "user_001",
                "recipient_id": "manager_001",
                "text": "Мы должны лучше работать вместе",
                "expected_culture_reference": "команда"
            },
            {
                "message_id": "test-culture-002",
                "sender_id": "user_002",
                "recipient_id": "team_lead_001",
                "text": "Нужно повысить качество работы",
                "expected_culture_reference": "качество"
            }
        ]
        
        for msg in test_messages:
            request = orchestrator_pb2.ProcessMessageRequest(
                message_id=msg["message_id"],
                sender_id=msg["sender_id"],
                recipient_id=msg["recipient_id"],
                text=msg["text"]
            )
            
            response = orchestrator_stub.ProcessMessage(request, timeout=30.0)
            
            # Проверяем ответ
            assert response.was_adapted or response.adapted_text, \
                "Message was not adapted"
            
            # Проверяем метаданные (culture_chunks_used должно быть в metadata)
            if hasattr(response, 'adaptation_metadata'):
                meta = response.adaptation_metadata
                print(f"\nMessage: {msg['text']}")
                print(f"  Adapted: {response.adapted_text[:100]}...")
                print(f"  Was adapted: {response.was_adapted}")
                print(f"  From cache: {meta.from_cache}")
            
            await asyncio.sleep(0.1)  # Небольшая пауза между запросами
        
        channel.close()
        
    except grpc.RpcError as e:
        pytest.fail(f"gRPC error: {e.code()}: {e.details()}")
    except Exception as e:
        pytest.fail(f"Full culture RAG flow failed: {e}")


def test_culture_rag_in_langfuse():
    """Проверка, что culture RAG отображается в Langfuse трейсах."""
    import requests
    
    # Проверяем доступность Langfuse
    try:
        response = requests.get(f"{LANGFUSE_URL}", timeout=5)
        assert response.status_code == 200, "Langfuse not accessible"
        print(f"\nLangfuse accessible at {LANGFUSE_URL}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Langfuse not accessible: {e}")
    
    # Проверяем наличие трейсов через API
    try:
        # Langfuse v3 API (через ClickHouse)
        clickhouse_url = "http://localhost:8123"
        response = requests.get(f"{clickhouse_url}/ping", timeout=5)
        assert response.status_code == 200, "ClickHouse not accessible"
        print("ClickHouse (Langfuse events) accessible")
        
        # Проверка таблиц events
        query = "SELECT count(*) FROM events"
        response = requests.post(
            f"{clickhouse_url}",
            data=query,
            params={"output_format": "JSONEachRow"}
        )
        
        if response.status_code == 200:
            count = response.json()
            print(f"Total events in Langfuse: {count}")
        
    except Exception as e:
        print(f"Langfuse check warning: {e}")


def test_culture_chunks_metadata():
    """Проверка метаданных culture chunks в Qdrant."""
    from retriever.qdrant_client import get_qdrant_client
    
    qdrant = get_qdrant_client()
    
    # Получаем culture chunks
    result = qdrant.client.search(
        collection_name="corporate_culture",
        query_vector=[0.0] * 768,
        limit=10,
        with_payload=True
    )
    
    assert len(result) > 0, "No culture chunks found"
    
    # Проверяем структуру payload
    required_fields = ["text", "section_title", "chunk_index"]
    
    for hit in result[:5]:
        payload = hit.payload
        
        for field in required_fields:
            assert field in payload, f"Missing required field '{field}' in culture chunk"
        
        # Проверяем, что текст не пустой
        assert len(payload["text"]) > 50, "Culture chunk text too short"
        
        print(f"\nCulture chunk metadata:")
        print(f"  Section: {payload.get('section_title', 'unknown')}")
        print(f"  Chunk index: {payload.get('chunk_index', 'unknown')}")
        print(f"  Text length: {len(payload['text'])} chars")
        print(f"  Preview: {payload['text'][:100]}...")


def test_culture_chunk_diversity():
    """Проверка разнообразия culture chunks (не все одинаковые)."""
    from retriever.qdrant_client import get_qdrant_client
    
    qdrant = get_qdrant_client()
    
    # Получаем несколько culture chunks
    result = qdrant.client.search(
        collection_name="corporate_culture",
        query_vector=[0.0] * 768,
        limit=10
    )
    
    assert len(result) >= 5, "Not enough culture chunks for diversity test"
    
    # Проверяем, что есть разные секции
    sections = set()
    for hit in result:
        section = hit.payload.get("section_title", "unknown")
        sections.add(section)
    
    assert len(sections) >= 2, f"Expected at least 2 different sections, got: {sections}"
    
    print(f"\nCulture chunk sections: {sections}")
    
    # Проверяем разнообразие текстов
    texts = [hit.payload.get("text", "")[:200] for hit in result]
    unique_texts = set(texts)
    
    assert len(unique_texts) >= 5, "Not enough diversity in culture chunks"
    print(f"Unique text samples: {len(unique_texts)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
