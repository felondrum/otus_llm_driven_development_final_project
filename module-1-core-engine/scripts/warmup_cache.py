# Прогрев кэша

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_gateway.cache import get_cache, LLMCache
from common.logging import logger


async def warmup_cache(cache: LLMCache):
    """Warmup cache with sample data."""
    # Sample prompts for warming up cache
    sample_prompts = [
        ("Hello, how are you?", "fast"),
        ("Explain quantum computing.", "balanced"),
        ("Write a long technical document.", "powerful")
    ]
    
    for prompt, model in sample_prompts:
        cache_key = cache._generate_key(prompt, model, {'temperature': 0.7, 'max_tokens': 2048})
        
        # Check if already cached
        cached = cache.get(prompt, model, {'temperature': 0.7, 'max_tokens': 2048})
        if cached:
            logger.info(f"Cache warmup hit for {model}")
        else:
            logger.info(f"Cache warmup miss for {model}, would populate on first request")
    
    logger.info("Cache warmup completed")


async def main():
    """Main function."""
    cache = get_cache(host="localhost", port=6379, ttl=3600)
    
    await warmup_cache(cache)
    
    print("Cache warmup script completed")


if __name__ == "__main__":
    asyncio.run(main())
