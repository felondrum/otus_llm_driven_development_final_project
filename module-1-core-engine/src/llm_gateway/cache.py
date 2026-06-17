# Кэш LLM

import hashlib
import json
import os
from typing import Dict, Any, Optional
import redis
from common.logging import logger, log_info
from common.metrics import track_cache_hit, track_cache_miss


class LLMCache:
    """Cache for LLM responses using Redis."""

    def __init__(
        self, host: str = None, port: int = 6379, ttl: int = 3600, password: str = None
    ):
        # Use environment variable or default to redis service name
        self.host = host or os.getenv("REDIS_HOST", "redis")
        self.port = port
        self.ttl = ttl
        self.password = password or os.getenv("REDIS_PASSWORD")
        if self.password:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True,
            )
        else:
            self.client = redis.Redis(
                host=self.host, port=self.port, decode_responses=True
            )
        self._init_connection()

    def _init_connection(self):
        """Initialize Redis connection."""
        try:
            self.client.ping()
            logger.info("Connected to Redis cache")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _generate_key(self, prompt: str, model: str, config: Dict[str, Any]) -> str:
        """Generate cache key from prompt, model, and config."""
        key_data = {
            "prompt": prompt,
            "model": model,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2048),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        return f"llm:{model}:{key_hash}"

    def get(
        self, prompt: str, model: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        key = self._generate_key(prompt, model, config)

        try:
            cached = self.client.get(key)
            if cached:
                track_cache_hit(cache_type="llm")
                log_info("Cache hit", key=key)
                return json.loads(cached)

            track_cache_miss(cache_type="llm")
            log_info("Cache miss", key=key)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self, prompt: str, model: str, config: Dict[str, Any], response: Dict[str, Any]
    ) -> bool:
        """Cache response."""
        key = self._generate_key(prompt, model, config)

        try:
            serialized = json.dumps(response)
            self.client.setex(key, self.ttl, serialized)
            log_info("Cache set", key=key, ttl=self.ttl)
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, prompt: str, model: str, config: Dict[str, Any]) -> bool:
        """Delete cached response."""
        key = self._generate_key(prompt, model, config)

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def clear_by_pattern(self, pattern: str) -> int:
        """Clear cache by pattern."""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0


# Global cache instance
_cache: Optional[LLMCache] = None


def get_cache(
    host: str = None, port: int = 6379, ttl: int = 3600, password: str = None
) -> LLMCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = LLMCache(host=host, port=port, ttl=ttl, password=password)
    return _cache
