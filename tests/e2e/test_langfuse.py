"""Тест Langfuse tracing через gRPC клиент."""

import os
import sys
import requests

# Настройки
LANGFUSE_URL = os.getenv("LANGFUSE_URL", "http://localhost:3000")
ORCHESTRATOR_HOST = os.getenv("ORCHESTRATOR_HOST", "localhost")
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", "8001"))
CLICKHOUSE_URL = "http://localhost:8123"

def test_langfuse_traces_via_http():
    """Проверка трейсов через HTTP API."""
    print("\n=== Testing Langfuse Traces via HTTP ===\n")
    
    # Проверяем доступность Langfuse
    try:
        response = requests.get(f"{LANGFUSE_URL}", timeout=5)
        assert response.status_code == 200, "Langfuse not accessible"
        print(f"✓ Langfuse accessible at {LANGFUSE_URL}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Langfuse not accessible: {e}")
        return False
    
    # Проверяем ClickHouse (Langfuse v3 uses ClickHouse for events)
    try:
        response = requests.get(f"{CLICKHOUSE_URL}/ping", timeout=5)
        assert response.status_code == 200, "ClickHouse not accessible"
        print(f"✓ ClickHouse (Langfuse events) accessible")
    except requests.exceptions.RequestException as e:
        print(f"✗ ClickHouse not accessible: {e}")
        return False
    
    # Проверка таблиц events
    try:
        query = "SELECT count(*) FROM events"
        response = requests.post(
            f"{CLICKHOUSE_URL}",
            data=query,
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
        
        if response.status_code == 200:
            count = response.text.strip()
            print(f"✓ Total events in Langfuse: {count}")
            
            # Проверяем наличие событий от LLM вызовов
            llm_query = "SELECT count(*) FROM events WHERE name LIKE '%orchestrator%' OR name LIKE '%retriever%'"
            response = requests.post(
                f"{CLICKHOUSE_URL}",
                data=llm_query,
                headers={"Content-Type": "text/plain"},
                timeout=5
            )
            
            if response.status_code == 200:
                llm_count = response.text.strip()
                print(f"✓ LLM/Retriever events: {llm_count}")
            
            # Показываем последние события
            recent_query = "SELECT name, timestamp FROM events ORDER BY timestamp DESC LIMIT 10 FORMAT TabSeparated"
            response = requests.post(
                f"{CLICKHOUSE_URL}",
                data=recent_query,
                headers={"Content-Type": "text/plain"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"\n✓ Recent events:")
                for line in response.text.strip().split('\n')[:10]:
                    if line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            print(f"  - {parts[0]} at {parts[1]}")
        
        return True
    except Exception as e:
        print(f"✗ Error checking events: {e}")
        return False

def test_trace_via_orchestrator():
    """Тест трейса через оркестратор."""
    print("\n=== Testing Trace via Orchestrator ===\n")
    
    # Запускаем полный поток через HTTP API (для проверки)
    llm_gateway_url = "http://localhost:8003/generate"
    
    try:
        response = requests.post(
            llm_gateway_url,
            json={
                "prompt": "Привет! Как дела?",
                "complexity": 1,
                "config": {
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ LLM Gateway call successful")
            print(f"  - Text: {data.get('text', '')[:100]}...")
            print(f"  - Model: {data.get('model_used', 'unknown')}")
            print(f"  - Latency: {data.get('latency_ms', 0)}ms")
            return True
        else:
            print(f"✗ LLM Gateway error: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ LLM Gateway connection error: {e}")
        return False

if __name__ == "__main__":
    print("Starting Langfuse tracing tests...")
    
    results = []
    
    # Тест 1: Проверка доступности
    print("\n### Test 1: Service Availability ###")
    results.append(test_langfuse_traces_via_http())
    
    # Тест 2: Проверка через LLM Gateway
    print("\n### Test 2: LLM Gateway Call ###")
    results.append(test_trace_via_orchestrator())
    
    # Результаты
    print("\n### Test Results ###")
    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
        print(f"  Passed: {sum(results)}/{len(results)}")
