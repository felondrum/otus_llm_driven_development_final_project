#!/usr/bin/env python3
"""
Тесты RAG для корпоративной культуры.

Эти тесты проверяют:
1. Загрузку документа корпоративной культуры в Qdrant
2. Векторный поиск релевантных фрагментов
3. Интеграцию культуры в промпт
"""

import asyncio
import pytest
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from retriever.qdrant_client import get_qdrant_client
from retriever.chunking import get_chunker
from retriever.embeddings import get_embedder
from orchestrator.context_assembler import get_context_assembler
from common.schemas import CorporateRule

# Используем относительный путь к файлу культуры
CULTURE_FILE = Path("demo_data/corporate_culture.md")


@pytest.fixture
def qdrant_client():
    """Fixture for Qdrant client."""
    return get_qdrant_client()


@pytest.fixture
def chunker():
    """Fixture for text chunker."""
    return get_chunker(chunk_size=500, chunk_overlap=50)


@pytest.mark.asyncio
async def test_culture_chunking(chunker):
    """Test that culture document is correctly chunked."""
    # Load culture document
    if not CULTURE_FILE.exists():
        pytest.skip(f"Culture file not found: {CULTURE_FILE}")
        
    with open(CULTURE_FILE) as f:
        content = f.read()

    # Chunk the content
    chunks = chunker.chunk(content)

    # Verify chunks were created
    assert len(chunks) > 0, "Should create at least one chunk"

    # Verify chunk sizes
    for i, chunk in enumerate(chunks):
        assert len(chunk) > 0, f"Chunk {i} should not be empty"
        # Allow some chunks to be larger due to overlap handling
        assert len(chunk) < 1000, f"Chunk {i} should be less than 1000 chars"

    # Verify content is from culture document
    assert any("корпоративная культура" in chunk.lower() for chunk in chunks), \
        "Chunks should contain culture document content"


@pytest.mark.asyncio
async def test_culture_embeddings(chunker):
    """Test that culture embeddings are generated correctly."""
    if not CULTURE_FILE.exists():
        pytest.skip(f"Culture file not found: {CULTURE_FILE}")
    
    # Skip if Ollama is not available
    try:
        embedder = get_embedder()
    except Exception:
        pytest.skip("Ollama not available for embeddings")
        return
    
    with open(CULTURE_FILE) as f:
        content = f.read()

    # Chunk the content
    chunks = chunker.chunk(content)

    # Generate embeddings for chunks
    for i, chunk in enumerate(chunks[:3]):  # Test first 3 chunks
        embedding = await embedder.generate_embedding(chunk)
        assert embedding is not None, f"Embedding for chunk {i} should not be None"
        assert len(embedding) == 768, f"Embedding for chunk {i} should have 768 dimensions"


@pytest.mark.asyncio
async def test_culture_search():
    """Test searching for culture chunks."""
    # Skip if Qdrant is not available
    try:
        qdrant_client = get_qdrant_client()
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")
        return
    
    # Test search with different queries
    queries = [
        ("открытость и честность", 3),
        ("командная работа", 2),
        ("принципы", 5),
    ]

    for query, limit in queries:
        chunks = await qdrant_client.get_culture_chunks(
            query_text=query,
            limit=limit
        )

        assert len(chunks) > 0, f"Should find chunks for query: {query}"
        assert len(chunks) <= limit, f"Should return at most {limit} chunks"

        # Verify chunks contain culture-related content
        for chunk in chunks:
            text = chunk.get("text", "")
            assert len(text) > 0, "Chunk should have text"


@pytest.mark.asyncio
async def test_culture_in_context_assembler():
    """Test that culture chunks are properly included in context."""
    assembler = get_context_assembler()

    # Test with sample culture chunks
    culture_chunks = [
        {
            "text": "Принцип 1: Открытость и честность - мы ценим открытость во всех формах коммуникации.",
            "section_title": "Открытость и честность",
            "section_level": 2,
        },
        {
            "text": "Принцип 2: Уважение к собеседнику - каждый человек достоин уважения.",
            "section_title": "Уважение к собеседнику",
            "section_level": 2,
        },
    ]

    # Assemble context with culture
    context = assembler.assemble_context(
        original_text="Привет, нужно улучшить код",
        culture_chunks=culture_chunks
    )

    # Verify context contains culture section
    assert "Корпоративная культура" in context, \
        "Context should contain culture section header"

    # Verify culture chunks are in context
    for chunk in culture_chunks:
        text = chunk.get("text", "")
        if text:
            assert text[:50] in context or text[:50].lower() in context.lower(), \
                "Culture chunk should be in context"


@pytest.mark.asyncio
async def test_culture_integration():
    """Test end-to-end culture integration."""
    if not CULTURE_FILE.exists():
        pytest.skip(f"Culture file not found: {CULTURE_FILE}")
    
    # Skip if Qdrant is not available
    try:
        qdrant_client = get_qdrant_client()
    except Exception as e:
        pytest.skip(f"Qdrant not available: {e}")
        return
    
    # 1. Load culture document
    with open(CULTURE_FILE) as f:
        original_content = f.read()

    # 2. Get culture chunks for a query
    query = "открытость"
    chunks = await qdrant_client.get_culture_chunks(
        query_text=query,
        limit=3
    )

    # 3. Verify chunks are relevant
    assert len(chunks) > 0, "Should find culture chunks"

    # 4. Build context with culture
    assembler = get_context_assembler()
    context = assembler.assemble_context(
        original_text="Мне нужно говорить открыто",
        culture_chunks=chunks
    )

    # 5. Verify context structure
    assert "Исходное сообщение" in context
    assert "Корпоративная культура" in context
    assert "Инструкции" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
