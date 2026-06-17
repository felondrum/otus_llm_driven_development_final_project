#!/usr/bin/env python3
"""Скрипт для загрузки корпоративной культуры в Qdrant (простой метод).

Запуск:
    poetry run python scripts/load_culture_data.py
"""

import os
import sys
import uuid
import random

# Добавляем путь к модулям
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'src'))

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


def chunk_text(text: str, chunk_size: int = 500) -> list:
    """Simple text chunking."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def load_culture(client: QdrantClient):
    """Load corporate culture from demo data to Qdrant."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    culture_path = os.path.join(base_dir, 'demo_data', 'corporate_culture.md')
    
    if not os.path.exists(culture_path):
        print(f"Culture file not found: {culture_path}")
        return 0
    
    with open(culture_path, encoding='utf-8') as f:
        content = f.read()
    
    # Chunk the content
    chunks = chunk_text(content, chunk_size=500)
    
    loaded_count = 0
    for i, chunk in enumerate(chunks):
        # Generate UUID for each chunk
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"corporate_culture:{i}"))
        # Generate vector (mock - in production would use actual embeddings)
        vector = [random.random() for _ in range(768)]
        
        # Extract section title from chunk
        lines = chunk.split('\n')
        section_title = "culture"
        if lines and lines[0].strip().startswith('#'):
            section_title = lines[0].replace('#', '').strip()
        
        # Create point
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "text": chunk,
                "section_title": section_title,
                "section_level": 2,
                "source": "demo_data/corporate_culture.md",
                "type": "corporate_culture",
                "chunk_index": i
            }
        )
        
        # Insert point
        client.upsert(collection_name="corporate_culture", points=[point])
        loaded_count += 1
    
    print(f"✓ Loaded {loaded_count} culture chunks")
    return loaded_count


def main():
    """Main function."""
    # Connect to Qdrant
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    print(f"Connecting to Qdrant at {host}:{port}...")
    
    try:
        client = QdrantClient(host=host, port=port, timeout=10)
        
        # Check connection
        collections = client.get_collections()
        print(f"✓ Connected successfully. Found {len(collections.collections)} collections.")
        
        # Load data
        print("\nLoading corporate culture data...")
        load_culture(client)
        
        print("\n✓ Corporate culture loaded successfully!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Make sure Qdrant is running on localhost:6333")
        sys.exit(1)


if __name__ == "__main__":
    main()
