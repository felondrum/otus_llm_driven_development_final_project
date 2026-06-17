#!/usr/bin/env python3
"""
Скрипт для диагностики загрузки и поиска профилей в Qdrant.

Запуск в Docker контейнере (Retriever):
    docker exec -it chameleon-retriever python /app/scripts/test_profile_lookup.py

Запуск в Docker контейнере (Orchestrator):
    docker exec -it chameleon-orchestrator python /app/scripts/test_profile_lookup.py
"""

import sys
import os
import asyncio

# Добавляем src в path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if os.path.exists(src_dir):
    sys.path.insert(0, src_dir)

from common.logging import logger
from retriever.qdrant_client import get_qdrant_client


async def test_profile_lookup():
    """Тест поиска профилей в Qdrant."""
    logger.info('===Profile Lookup Test===')\n
    
    qdrant = get_qdrant_client()
    
    # Step 1: Check all profiles in Qdrant
    logger.info('Step 1: Checking all profiles in Qdrant...')
    result = qdrant.client.scroll(
        collection_name='user_profiles',
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    profiles, _ = result
    logger.info(f'✓ Found {len(profiles)} profiles in Qdrant')
    
    for profile in profiles:
        payload = profile.payload
        logger.info(f"  - user_id: {payload.get('user_id')}, full_name: {payload.get('full_name')}, role: {payload.get('role')}")
    
    # Step 2: Test lookup by known user_ids
    logger.info('\nStep 2: Testing lookup by known user_ids...')
    
    test_user_ids = ['alex_i', 'petr_s', 'anna_k']
    
    for user_id in test_user_ids:
        profile = qdrant.get_profile(user_id)
        if profile:
            logger.info(f'✓ Profile found for {user_id}: {profile.get("full_name")}')
        else:
            logger.info(f'✗ Profile NOT found for {user_id}')
    
    # Step 3: Test lookup by name (this will likely fail)
    logger.info('\nStep 3: Testing lookup by name "Иван"...')
    profile = qdrant.get_profile('Иван')
    if profile:
        logger.info(f'✓ Profile found for "Иван": {profile.get("full_name")}')
    else:
        logger.info(f'✗ Profile NOT found for "Иван" (expected - user_id is "alex_i")')
    
    # Step 4: Test full flow with context assembly
    logger.info('\nStep 4: Testing full flow with context assembly...')
    from orchestrator.context_assembler import get_context_assembler
    
    assembler = get_context_assembler()
    
    # Get profile for alex_i
    profile = qdrant.get_profile('alex_i')
    
    prompt = assembler.assemble_context(
        original_text='Иван, пришли отчет',
        profile=profile
    )
    
    logger.info('✓ Context assembled')
    logger.info(f'\nPrompt:\n{prompt}')
    
    # Check if profile is in prompt
    if profile and profile.get('full_name'):
        if profile.get('full_name') in prompt:
            logger.info('✓ Profile full_name found in prompt')
        else:
            logger.info('✗ Profile full_name NOT found in prompt')
    
    if profile and profile.get('role'):
        if profile.get('role') in prompt:
            logger.info('✓ Profile role found in prompt')
        else:
            logger.info('✗ Profile role NOT found in prompt')
    
    logger.info('\n===Profile Lookup Test Completed===')
    return True


if __name__ == '__main__':
    try:
        asyncio.run(test_profile_lookup())
    except Exception as e:
        logger.error(f'Test failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
