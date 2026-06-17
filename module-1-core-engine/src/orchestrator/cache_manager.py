# Управление кэшем

import hashlib
import json
import os
from typing import Dict, Any, Optional
import redis
from common.logging import logger, log_info
from common.metrics import track_cache_hit, track_cache_miss


class CacheManager:
    """Manager for caching message adaptations."""

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
            logger.info("Connected to Redis cache manager")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def generate_key(
        self,
        message_id: str = None,
        text: str = None,
        recipient_id: str = None,
        rules: list = None,
    ) -> str:
        """Generate cache key from message attributes."""
        key_data = {
            "text": text or "",
            "recipient_id": recipient_id or "",
            "rules": sorted(rules) if rules else [],
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()
        return f"adaptation:{key_hash}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached adaptation."""
        try:
            cached = self.client.get(key)
            if cached:
                track_cache_hit(cache_type="adaptation")
                log_info("Cache hit", key=key)
                return json.loads(cached)

            track_cache_miss(cache_type="adaptation")
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, response: Dict[str, Any]) -> bool:
        """Cache adaptation."""
        try:
            serialized = json.dumps(response)
            self.client.setex(key, self.ttl, serialized)
            log_info("Cache set", key=key, ttl=self.ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cached adaptation."""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    host: str = None, port: int = 6379, ttl: int = 3600, password: str = None
) -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(host=host, port=port, ttl=ttl, password=password)
    return _cache_manager
