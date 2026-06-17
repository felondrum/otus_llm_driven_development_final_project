#!/usr/bin/env python3
"""
Скрипт для тестирования полного потока обработки сообщения с профилями.

Запуск в Docker контейнере:
    docker exec -it chameleon-orchestrator python /app/scripts/test_profile_full_flow.py

Этот скрипт:
1. Подключается к оркестратору через gRPC
2. Отправляет тестовые сообщения с различными user_id
3. Проверяет, что профили используются для адаптации
"""

import sys
import os
import uuid
import grpc

# Добавляем src в path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if os.path.exists(src_dir):
    sys.path.insert(0, src_dir)

from chameleon.core.v1 import (
    orchestrator_pb2,
    orchestrator_pb2_grpc,
)


def test_profile_full_flow():
    """Полный тест потока с профилями."""
    print("===Profile Full Flow Test===\n")
    
    # Подключение к оркестратору
    orchestrator_host = os.getenv("ORCHESTRATOR_HOST", "localhost")
    orchestrator_port = int(os.getenv("ORCHESTRATOR_PORT", "8001"))
    
    print(f"Connecting to orchestrator at {orchestrator_host}:{orchestrator_port}...")
    channel = grpc.insecure_channel(f"{orchestrator_host}:{orchestrator_port}")
    stub = orchestrator_pb2_grpc.OrchestratorServiceStub(channel)
    
    # Тестируем различные user_id
    test_cases = [
        {
            "user_id": "alex_i",
            "name": "Иванов Алексей (инженер)",
            "text": "Иван, пришли отчет",
        },
        {
            "user_id": "petr_s",
            "name": "Смирнов Петр (тимлид)",
            "text": "Петр, ты должен проверить код",
        },
        {
            "user_id": "anna_k",
            "name": "Ковалева Анна (директор)",
            "text": "Анна, нужен ваш одобрение на проект",
        },
    ]
    
    print("Testing with different profiles:\n")
    print("=" * 80)
    
    for test_case in test_cases:
        user_id = test_case["user_id"]
        name = test_case["name"]
        text = test_case["text"]
        
        print(f"\nTest case: {name} (user_id: {user_id})")
        print(f"Original text: '{text}'")
        
        # Создаем запрос
        # Note: using recipient_id instead of user_id (per protobuf definition)
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=str(uuid.uuid4()),
            sender_id=str(uuid.uuid4()),
            recipient_id=user_id,  # Changed from user_id to recipient_id
            text=text,
        )
        
        # Отправляем запрос
        try:
            response = stub.ProcessMessage(request, timeout=15.0)
            
            print(f"Adapted text: '{response.adapted_text}'")
            print(f"Was adapted: {response.was_adapted}")
            print(f"Model used: {response.model_used}")
            print(f"Processing time: {response.processing_time_ms}ms")
            
            # Проверяем метаданные
            if response.HasField("adaptation_metadata"):
                metadata = response.adaptation_metadata
                print(f"Tokens prompt: {metadata.tokens_prompt}")
                print(f"Tokens completion: {metadata.tokens_completion}")
                print(f"From cache: {metadata.from_cache}")
                print(f"Fallback used: {metadata.fallback_used}")
            
            # Проверяем, что профиль был использован (если был найден)
            if response.was_adapted:
                print("✓ Profile was used for adaptation")
            else:
                print("⚠ Profile may not have been used (was_adapted=False)")
        
        except grpc.RpcError as e:
            print(f"✗ RPC error: {e.code()} - {e.details()}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 80)
    print("\n===Profile Full Flow Test Completed===")


if __name__ == '__main__':
    try:
        test_profile_full_flow()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
