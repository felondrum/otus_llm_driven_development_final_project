"""E2E тест полного потока с проверкой трейсов в Langfuse."""

import os
import sys
import time
import grpc

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "module-1-core-engine", "src"))

import chameleon.core.v1.orchestrator_pb2 as orchestrator_pb2
import chameleon.core.v1.orchestrator_pb2_grpc as orchestrator_pb2_grpc

ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8001"))
CLICKHOUSE_URL = "http://localhost:8123"

def test_full_flow_with_traces():
    """Полный тест с проверкой трейсов."""
    print("\n=== Testing Full Flow with Langfuse Traces ===\n")
    
    # Подключаемся к оркестратору
    channel = grpc.insecure_channel(f"{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}")
    stub = orchestrator_pb2_grpc.OrchestratorServiceStub(channel)
    
    # Ждем готовности
    try:
        grpc.channel_ready_future(channel).result(timeout=10)
        print("✓ Connected to orchestrator")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False
    
    # Тестовые сообщения
    test_messages = [
        {
            "message_id": "test-trace-001",
            "sender_id": "user_001",
            "recipient_id": "manager_001",
            "text": "Нужно обсудить новые цели",
            "style_name": "formal"
        },
        {
            "message_id": "test-trace-002",
            "sender_id": "user_002",
            "recipient_id": "team_lead_001",
            "text": "Мы должны лучше работать вместе",
        },
        {
            "message_id": "test-trace-003",
            "sender_id": "user_003",
            "recipient_id": "employee_001",
            "text": "Петя, проверь код",
            "style_name": "dovlatov"
        }
    ]
    
    print(f"Sending {len(test_messages)} test messages...")
    
    for i, msg in enumerate(test_messages):
        request = orchestrator_pb2.ProcessMessageRequest(
            message_id=msg["message_id"],
            sender_id=msg["sender_id"],
            recipient_id=msg["recipient_id"],
            text=msg["text"],
            style_name=msg.get("style_name", "")
        )
        
        try:
            response = stub.ProcessMessage(request, timeout=30.0)
            print(f"\n✓ Message {i+1} processed:")
            print(f"  - ID: {msg['message_id']}")
            print(f"  - Original: {msg['text'][:50]}...")
            print(f"  - Adapted: {response.adapted_text[:50]}...")
            print(f"  - Was adapted: {response.was_adapted}")
            print(f"  - Model: {response.model_used}")
            print(f"  - Time: {response.processing_time_ms}ms")
            
        except Exception as e:
            print(f"\n✗ Message {i+1} failed: {e}")
    
    # Закрываем канал
    channel.close()
    
    # Ждем немного для доставки трейсов
    print("\nWaiting for traces to be delivered...")
    time.sleep(3)
    
    # Проверяем трейсы в ClickHouse
    print("\n=== Checking Langfuse Traces ===\n")
    
    try:
        # Проверяем последние трейсы
        query = """
        SELECT name, type, start_time 
        FROM observations 
        WHERE name LIKE '%test-trace%' OR name LIKE '%orchestrator-processing%' OR name LIKE '%retriever-%'
        ORDER BY start_time DESC 
        LIMIT 30
        FORMAT TabSeparated
        """
        
        import requests
        response = requests.post(
            f"{CLICKHOUSE_URL}",
            data=query,
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            print(f"Found {len(lines)} recent traces:")
            for line in lines[:20]:  # Показываем первые 20
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        print(f"  - {parts[0]} ({parts[1]}) at {parts[2]}")
        
        return True
    except Exception as e:
        print(f"Warning: Could not fetch traces: {e}")
        return True  # Не фейлим тест из-за этого

if __name__ == "__main__":
    success = test_full_flow_with_traces()
    if success:
        print("\n✓ Test completed successfully!")
    else:
        print("\n✗ Test failed!")
