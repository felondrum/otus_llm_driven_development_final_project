#!/usr/bin/env python3
"""Скрипт для загрузки демо данных в Qdrant для e2e тестов.

Запуск в контейнере:
    poetry run python scripts/e2e_load_demo_data.py
"""

import json
import random
import os
import sys
import uuid

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from qdrant_client import QdrantClient


def map_profile(profile: dict) -> dict:
    """Map string enum values to numeric values for protobuf compatibility."""
    honorific_type_map = {
        "first_name": 1,
        "patronymic": 3,
        "last_name": 2,
        "title": 4,
        "default": 0,
    }
    
    communication_mode_map = {
        "informal": 2,
        "formal": 1,
        "neutral": 0,
        "technical": 3,
        "collaborative": 4,
    }
    
    # Create a copy to avoid modifying original
    mapped_profile = profile.copy()
    
    # Map honorific_type
    if "honorific_type" in mapped_profile:
        ht = mapped_profile["honorific_type"]
        if isinstance(ht, str):
            mapped_profile["honorific_type"] = honorific_type_map.get(ht, 0)
    
    # Map communication_mode
    if "communication_mode" in mapped_profile:
        cm = mapped_profile["communication_mode"]
        if isinstance(cm, str):
            mapped_profile["communication_mode"] = communication_mode_map.get(cm, 0)
    
    return mapped_profile


def load_profiles(client: QdrantClient):
    """Load user profiles from demo data to Qdrant."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    profiles_path = os.path.join(base_dir, 'demo_data', 'profiles.json')
    
    if not os.path.exists(profiles_path):
        print(f"Profiles file not found: {profiles_path}")
        return
    
    with open(profiles_path) as f:
        profiles = json.load(f)
    
    # Generate UUIDs based on user_id for consistency
    ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, profile["user_id"])) for profile in profiles]
    vectors = [[random.random() for _ in range(768)] for _ in profiles]
    
    # Apply mapping to profiles
    payloads = [map_profile(profile) for profile in profiles]
    
    # Create points list
    points = []
    for id, vector, payload in zip(ids, vectors, payloads):
        points.append({
            "id": id,
            "vector": vector,
            "payload": payload
        })
    
    # Use upsert
    result = client.upsert(collection_name="user_profiles", points=points)
    
    if result.status == "completed":
        print(f"✓ Loaded {len(profiles)} profiles with mapping applied")
        # Print summary of mapped values
        for profile in payloads:
            print(f"  - {profile['full_name']}: role={profile['role']}, dept={profile['department']}, honorific_type={profile.get('honorific_type')}, communication_mode={profile.get('communication_mode')}")
    else:
        print(f"✗ Failed to load profiles: {result.status}")


def load_rules(client: QdrantClient):
    """Load corporate rules from demo data to Qdrant."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    rules_path = os.path.join(base_dir, 'demo_data', 'rules.json')
    
    if not os.path.exists(rules_path):
        print(f"Rules file not found: {rules_path}")
        return
    
    with open(rules_path) as f:
        rules = json.load(f)
    
    # Generate UUIDs based on rule_id for consistency
    ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, rule["rule_id"])) for rule in rules]
    vectors = [[random.random() for _ in range(768)] for _ in rules]
    payloads = [rule for rule in rules]
    
    # Create points list
    points = []
    for id, vector, payload in zip(ids, vectors, payloads):
        points.append({
            "id": id,
            "vector": vector,
            "payload": payload
        })
    
    # Use upsert
    result = client.upsert(collection_name="corporate_rules", points=points)
    
    if result.status == "completed":
        print(f"✓ Loaded {len(rules)} rules")
    else:
        print(f"✗ Failed to load rules: {result.status}")


def load_styles(client: QdrantClient):
    """Load artistic styles from demo data to Qdrant."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    styles_path = os.path.join(base_dir, 'demo_data', 'styles.json')
    
    if not os.path.exists(styles_path):
        print(f"Styles file not found: {styles_path}")
        return
    
    with open(styles_path) as f:
        styles = json.load(f)
    
    # Generate UUIDs based on style_id for consistency
    ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"])) for style in styles]
    vectors = [[random.random() for _ in range(768)] for _ in styles]
    payloads = [style for style in styles]
    
    # Create points list
    points = []
    for id, vector, payload in zip(ids, vectors, payloads):
        points.append({
            "id": id,
            "vector": vector,
            "payload": payload
        })
    
    # Use upsert
    result = client.upsert(collection_name="artistic_styles", points=points)
    
    if result.status == "completed":
        print(f"✓ Loaded {len(styles)} styles")
    else:
        print(f"✗ Failed to load styles: {result.status}")


def main():
    """Main function."""
    # Connect to Qdrant
    # Use 'qdrant' for Docker container, 'localhost' for local execution
    host = os.getenv("QDRANT_HOST", "localhost" if os.getenv("DOCKER_ENV") != "true" else "qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    print(f"Connecting to Qdrant at {host}:{port}...")
    
    try:
        client = QdrantClient(host=host, port=port, timeout=10)
        
        # Check connection
        collections = client.get_collections()
        print(f"✓ Connected successfully. Found {len(collections.collections)} collections.")
        
        # Create collections if not exist
        collection_names = [c.name for c in collections.collections]
        
        if "user_profiles" not in collection_names:
            from qdrant_client.models import VectorParams, Distance
            client.create_collection(
                collection_name="user_profiles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Created collection: user_profiles")
        
        if "corporate_rules" not in collection_names:
            from qdrant_client.models import VectorParams, Distance
            client.create_collection(
                collection_name="corporate_rules",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Created collection: corporate_rules")
        
        if "artistic_styles" not in collection_names:
            from qdrant_client.models import VectorParams, Distance
            client.create_collection(
                collection_name="artistic_styles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("✓ Created collection: artistic_styles")
        
        # Load data
        print("\nLoading demo data...")
        load_profiles(client)
        load_rules(client)
        load_styles(client)
        
        print("\n✓ Demo data loaded successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Make sure Qdrant is running")
        sys.exit(1)


if __name__ == "__main__":
    main()
