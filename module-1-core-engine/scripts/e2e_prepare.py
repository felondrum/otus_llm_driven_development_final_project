#!/usr/bin/env python3
"""Скрипт для подготовки среды и загрузки демо данных для e2e тестов.

Запуск:
    poetry run python scripts/e2e_prepare.py

Или через make:
    make e2e-setup
"""

import asyncio
import os
import sys
import time
import uuid


async def main():
    """Main function."""
    print("=" * 60)
    print("Подготовка среды для E2E тестов Core Engine")
    print("=" * 60)
    
    # Переменные окружения
    orchestrator_port = os.getenv("ORCHESTRATOR_PORT", "8001")
    retriever_port = os.getenv("RETRIEVER_PORT", "8002")
    qdrant_port = os.getenv("QDRANT_PORT", "6333")
    redis_port = os.getenv("REDIS_PORT", "6379")
    ollama_port = os.getenv("OLLAMA_PORT", "11434")
    llm_gateway_port = os.getenv("LLM_GATEWAY_PORT", "8003")
    
    print("\n1. Проверка запущенных сервисов...")
    
    # Проверка Docker
    try:
        result = os.system("docker --version > /dev/null 2>&1")
        if result != 0:
            print("✗ Docker не установлен")
            return 1
        print("✓ Docker установлен")
    except Exception as e:
        print(f"✗ Ошибка проверки Docker: {e}")
        return 1
    
    # Проверка poetry
    try:
        result = os.system("poetry --version > /dev/null 2>&1")
        if result != 0:
            print("✗ Poetry не установлен")
            return 1
        print("✓ Poetry установлен")
    except Exception as e:
        print(f"✗ Ошибка проверки Poetry: {e}")
        return 1
    
    # Проверка запущенных контейнеров
    print("\n2. Проверка запущенных контейнеров...")
    
    containers = [
        ("qdrant", qdrant_port),
        ("redis", redis_port),
        ("ollama", ollama_port),
        ("orchestrator", orchestrator_port),
        ("retriever", retriever_port),
        ("llm-gateway", llm_gateway_port),
    ]
    
    for container, port in containers:
        try:
            # Проверка порта
            result = os.system(f"nc -z localhost {port} > /dev/null 2>&1")
            if result == 0:
                print(f"✓ {container}:{port} доступен")
            else:
                print(f"⚠ {container}:{port} не доступен - запустите через 'make run'")
        except Exception as e:
            print(f"⚠ Ошибка проверки {container}: {e}")
    
    print("\n3. Загрузка демо данных в Qdrant...")
    
    # Импорт и загрузка данных
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance, PointStruct
        import json
        import random
        
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        client = QdrantClient(host=host, port=port, timeout=10)
        
        # Проверка подключения
        collections = client.get_collections()
        print(f"✓ Подключено к Qdrant. Коллекций: {len(collections.collections)}")
        
        # Создание коллекций
        collection_names = [c.name for c in collections.collections]
        
        if "user_profiles" not in collection_names:
            client.create_collection(
                collection_name="user_profiles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Создана коллекция: user_profiles")
        
        if "corporate_rules" not in collection_names:
            client.create_collection(
                collection_name="corporate_rules",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Создана коллекция: corporate_rules")
        
        if "artistic_styles" not in collection_names:
            client.create_collection(
                collection_name="artistic_styles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Создана коллекция: artistic_styles")
        
        # Загрузка данных
        base_path = os.path.dirname(__file__)
        
        # Загрузка профилей
        profiles_path = os.path.join(base_path, '..', 'demo_data', 'profiles.json')
        if os.path.exists(profiles_path):
            with open(profiles_path) as f:
                profiles = json.load(f)
            
            for profile in profiles:
                # Generate UUID5 from user_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, profile["user_id"]))
                vector = [random.random() for _ in range(768)]
                client.upsert(
                    collection_name="user_profiles",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=profile
                    )]
                )
            print(f"✓ Загружено профилей: {len(profiles)}")
        
        # Загрузка правил
        rules_path = os.path.join(base_path, '..', 'demo_data', 'rules.json')
        if os.path.exists(rules_path):
            with open(rules_path) as f:
                rules = json.load(f)
            
            for rule in rules:
                # Generate UUID5 from rule_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule["rule_id"]))
                vector = [random.random() for _ in range(768)]
                client.upsert(
                    collection_name="corporate_rules",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=rule
                    )]
                )
            print(f"✓ Загружено правил: {len(rules)}")
        
        # Загрузка стилей
        styles_path = os.path.join(base_path, '..', 'demo_data', 'styles.json')
        if os.path.exists(styles_path):
            with open(styles_path) as f:
                styles = json.load(f)
            
            for style in styles:
                # Generate UUID5 from style_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"]))
                vector = [random.random() for _ in range(768)]
                client.upsert(
                    collection_name="artistic_styles",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=style
                    )]
                )
            print(f"✓ Загружено стилей: {len(styles)}")
        
        print("\n" + "=" * 60)
        print("✓ Среда подготовлена успешно!")
        print("=" * 60)
        print("\nТеперь вы можете запустить e2e тесты:")
        print("  poetry run pytest tests/e2e/ -v")
        print("\nИли через make:")
        print("  make test-e2e")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Ошибка при подготовке: {e}")
        print("\nУбедитесь, что:")
        print("  1. Qdrant запущен (make run)")
        print("  2. Все зависимости установлены (poetry install)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
