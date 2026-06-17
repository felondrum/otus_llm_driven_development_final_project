"""E2E тесты для Core Engine - конфигурация и фикстуры."""

import pytest
import pytest_asyncio
import asyncio
import sys
import os

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set OLLAMA_HOST for tests (docker service name)
os.environ["OLLAMA_HOST"] = "localhost"


@pytest.fixture(scope="session")
def docker_compose_command():
    """Return docker-compose command."""
    return "docker-compose -f docker-compose.module.yml"


@pytest.fixture(scope="session", autouse=True)
async def wait_for_services():
    """Wait for all services to be ready before running e2e tests."""
    import redis
    from qdrant_client import QdrantClient
    import httpx
    
    redis_password = os.getenv("REDIS_PASSWORD", "redis123")
    
    # Wait for Redis
    redis_client = redis.Redis(
        host="localhost", 
        port=6379, 
        password=redis_password, 
        decode_responses=True
    )
    
    for _ in range(30):
        try:
            redis_client.ping()
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        pytest.fail("Redis failed to start")
    
    # Wait for Qdrant
    qdrant_client = QdrantClient(host="localhost", port=6333, timeout=10)
    
    for _ in range(30):
        try:
            qdrant_client.get_collections()
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        pytest.fail("Qdrant failed to start")
    
    # Wait for Ollama
    async with httpx.AsyncClient() as client:
        for _ in range(60):
            try:
                response = await client.get("http://localhost:11434/")
                if response.status_code == 200 and "Ollama is running" in response.text:
                    break
            except Exception:
                await asyncio.sleep(1)
        else:
            pytest.fail("Ollama failed to start")
    
    # Wait for LLM Gateway
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                response = await client.get("http://localhost:8003/health")
                if response.status_code == 200:
                    break
            except Exception:
                await asyncio.sleep(1)
        else:
            pytest.fail("LLM Gateway failed to start")
    
    # Wait for Orchestrator gRPC
    import grpc
    channel = grpc.insecure_channel("localhost:8001")
    for _ in range(30):
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        pytest.fail("Orchestrator gRPC failed to start")
    
    # Wait for Retriever gRPC
    channel = grpc.insecure_channel("localhost:8002")
    for _ in range(30):
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            break
        except Exception:
            await asyncio.sleep(1)
    else:
        pytest.fail("Retriever gRPC failed to start")
    
    # Give services time to fully initialize
    await asyncio.sleep(2)
    
    # Load demo data into Qdrant if not already loaded
    await _load_demo_data_if_needed(qdrant_client)
    
    yield


async def _load_demo_data_if_needed(qdrant_client):
    """Load demo data if collections are empty."""
    collections = qdrant_client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    # Check if user_profiles collection has data
    if "user_profiles" in collection_names:
        # Try to get a point
        try:
            result = qdrant_client.scroll(
                collection_name="user_profiles",
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            # If no data, load demo data
            if len(result.points) == 0:
                await _load_demo_data(qdrant_client)
        except Exception:
            await _load_demo_data(qdrant_client)
    else:
        await _load_demo_data(qdrant_client)


async def _load_demo_data(qdrant_client):
    """Load demo data into Qdrant collections."""
    import random
    import json
    from qdrant_client.models import VectorParams, Distance, PointStruct
    
    # Load profiles
    profiles_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'demo_data', 
        'profiles.json'
    )
    
    if os.path.exists(profiles_path):
        with open(profiles_path) as f:
            profiles = json.load(f)
        
        for profile in profiles:
            vector = [random.random() for _ in range(768)]
            qdrant_client.upsert(
                collection_name="user_profiles",
                points=[PointStruct(
                    id=profile["user_id"],
                    vector=vector,
                    payload=profile
                )]
            )
        print(f"Loaded {len(profiles)} profiles")
    
    # Load rules
    rules_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'demo_data', 
        'rules.json'
    )
    
    if os.path.exists(rules_path):
        with open(rules_path) as f:
            rules = json.load(f)
        
        for rule in rules:
            vector = [random.random() for _ in range(768)]
            qdrant_client.upsert(
                collection_name="corporate_rules",
                points=[PointStruct(
                    id=rule["rule_id"],
                    vector=vector,
                    payload=rule
                )]
            )
        print(f"Loaded {len(rules)} rules")
    
    # Load styles
    styles_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'demo_data', 
        'styles.json'
    )
    
    if os.path.exists(styles_path):
        with open(styles_path) as f:
            styles = json.load(f)
        
        for style in styles:
            vector = [random.random() for _ in range(768)]
            qdrant_client.upsert(
                collection_name="artistic_styles",
                points=[PointStruct(
                    id=style["style_id"],
                    vector=vector,
                    payload=style
                )]
            )
        print(f"Loaded {len(styles)} styles")


@pytest.fixture(scope="module")
async def test_user_profiles():
    """Профили пользователей для тестов."""
    return {
        "sender": {
            "user_id": "sender_test_e2e",
            "full_name": "Иванов Иван",
            "role": "employee",
            "department": "it",
            "honorific_type": "first_name",
            "communication_mode": "informal",
        },
        "recipient_manager": {
            "user_id": "recipient_manager_test_e2e",
            "full_name": "Петров Петр Петрович",
            "role": "manager",
            "department": "it",
            "honorific_type": "patronymic",
            "communication_mode": "formal",
        },
        "recipient_director": {
            "user_id": "recipient_director_test_e2e",
            "full_name": "Сидоров Алексей Владимирович",
            "role": "director",
            "department": "engineering",
            "honorific_type": "patronymic",
            "communication_mode": "formal",
        },
    }


@pytest.fixture(scope="module")
async def test_corporate_rules():
    """Корпоративные правила для тестов."""
    return [
        {
            "rule_id": "rule_formal_address_manager",
            "category": "address",
            "priority": 10,
            "condition": "recipient_role == 'manager'",
            "transformation": "use formal address with patronymic",
            "example_original": "Иван, ты должен",
            "example_adapted": "Иван Петрович, вы должны",
        },
        {
            "rule_id": "rule_no_blame",
            "category": "tone",
            "priority": 9,
            "condition": "contains 'сломал' OR 'ошибка'",
            "transformation": "rephrase as observation, not blame",
            "example_original": "ты сломал систему",
            "example_adapted": "система не работает корректно",
        },
    ]


@pytest.fixture
async def test_user_id() -> str:
    """Generate unique test user ID."""
    import uuid
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def test_message_id() -> str:
    """Generate unique message ID."""
    import uuid
    return f"msg_{uuid.uuid4().hex[:8]}"
