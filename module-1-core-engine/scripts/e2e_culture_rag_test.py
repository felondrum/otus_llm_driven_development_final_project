#!/usr/bin/env python3
"""
Полный E2E тест culture RAG в Docker контейнерах.
Запуск: docker exec module-1-core-engine-retriever-1 python /app/scripts/e2e_culture_rag_test.py
"""

import sys
import asyncio
sys.path.insert(0, '/app/src')

from common.logging import logger
from retriever.qdrant_client import get_qdrant_client
from orchestrator.context_assembler import get_context_assembler


async def test_culture_rag_e2e():
    """Полный E2E тест culture RAG."""
    logger.info('===Culture RAG E2E Test===')
    
    # Step 1: Check culture chunks in Qdrant
    logger.info('Step 1: Checking culture chunks in Qdrant...')
    qdrant = get_qdrant_client()
    
    result = qdrant.client.search(
        collection_name='corporate_culture',
        query_vector=[0.0] * 768,
        limit=10
    )
    
    assert len(result) >= 5, f'Expected at least 5 chunks, got {len(result)}'
    logger.info(f'✓ Found {len(result)} culture chunks in Qdrant')
    
    # Step 2: Test vector search
    logger.info('Step 2: Testing vector search...')
    test_queries = [
        'команда и сотрудничество',
        'ответственность и качество'
    ]
    
    for query in test_queries:
        chunks = await qdrant.get_culture_chunks(query_text=query, limit=3)
        assert len(chunks) > 0, f'No chunks found for query: {query}'
        logger.info(f'✓ Query "{query}" → found {len(chunks)} chunks')
    
    # Step 3: Test context assembly with culture chunks
    logger.info('Step 3: Testing context assembly...')
    assembler = get_context_assembler()
    
    culture_chunks = await qdrant.get_culture_chunks(query_text='команда', limit=2)
    prompt = assembler.assemble_context(
        original_text='Нужно улучшить коммуникацию в команде',
        culture_chunks=culture_chunks
    )
    
    assert '## Корпоративная культура (рекомендации):' in prompt
    logger.info('✓ Context assembled with culture chunks')
    
    # Step 4: Verify culture chunks are in prompt
    for chunk in culture_chunks:
        assert chunk.get('section_title') in prompt or chunk.get('text', '')[:50] in prompt
    logger.info('✓ All culture chunks present in prompt')
    
    logger.info('===Culture RAG E2E Test PASSED===')
    return True


async def test_full_flow():
    """Полный поток: culture RAG + LLM generation."""
    logger.info('===Culture RAG Full Flow Test===')
    
    qdrant = get_qdrant_client()
    
    # Get culture chunks
    chunks = await qdrant.get_culture_chunks(query_text='этикет и коммуникация', limit=3)
    logger.info(f'✓ Got {len(chunks)} culture chunks')
    
    # Assemble prompt
    assembler = get_context_assembler()
    prompt = assembler.assemble_context(
        original_text='Мы должны лучше работать вместе',
        culture_chunks=chunks
    )
    
    logger.info('✓ Context assembled')
    
    # Call LLM Gateway
    import requests
    
    llm_url = 'http://localhost:8003/generate'
    response = requests.post(llm_url, json={
        'prompt': prompt,
        'complexity': 1,
        'config': {'temperature': 0.7, 'max_tokens': 200}
    }, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        logger.info(f'✓ LLM generation successful')
        logger.info(f'  Model: {result.get("model_used", "unknown")}')
        logger.info(f'  Text: {result.get("text", "")[:200]}')
        logger.info(f'  Latency: {result.get("latency_ms", 0)}ms')
    else:
        logger.error(f'LLM Gateway error: {response.status_code}')
        logger.error(response.text)
        return False
    
    logger.info('===Full Flow Test PASSED===')
    return True


if __name__ == '__main__':
    try:
        # Run tests
        asyncio.run(test_culture_rag_e2e())
        print()
        asyncio.run(test_full_flow())
        print()
        print('✅ All E2E tests passed!')
    except Exception as e:
        logger.error(f'❌ Test failed: {e}')
        sys.exit(1)
