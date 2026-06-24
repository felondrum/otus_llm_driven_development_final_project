# Конфигурация оркестратора

import os
import yaml
from typing import Dict, Any, Optional

from common.logging import logger


class Config:
    """Application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        self.config: Dict[str, Any] = {}
        self.load_config(config_path)

    def load_config(self, config_path: Optional[str] = None):
        """Load configuration from YAML files."""
        config_path = config_path or os.getenv("CONFIG_PATH", "config/development.yaml")

        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self._set_defaults()

    def _set_defaults(self):
        """Set default configuration values."""
        self.config = {
            "server": {"port": 8001, "host": "0.0.0.0", "debug": True},
            "services": {
                "redis": {"host": "localhost", "port": 6379},
                "qdrant": {"host": "localhost", "port": 6333},
                "ollama": {"host": "localhost", "port": 11434},
                "llm_gateway": {"host": "llm-gateway", "port": 8003},
                "langfuse": {"host": "http://localhost:5000", "enabled": False},
            },
            "logging": {"level": "DEBUG"},
            "cache": {"default_ttl": 3600, "max_size": 10000},
            "cache_ttl": {
                "profile": 3600,
                "rules": 300,
                "style_examples": 86400,
                "adaptation": 3600,
            },
            "retries": {
                "max_attempts": 3,
                "initial_backoff_ms": 100,
                "max_backoff_ms": 10000,
                "backoff_multiplier": 2.0,
            },
            "fallback": {
                "chain": ["ollama:qwen2.5:1.5b", "yandex:ya-llm"],
                "return_original_on_fallback": True,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    @property
    def server_port(self) -> int:
        """Get server port."""
        return self.get("server.port", 8001)

    @property
    def server_host(self) -> str:
        """Get server host."""
        return self.get("server.host", "0.0.0.0")

    @property
    def redis_host(self) -> str:
        """Get Redis host."""
        return os.getenv("REDIS_HOST", self.get("services.redis.host", "localhost"))

    @property
    def redis_port(self) -> int:
        """Get Redis port."""
        return self.get("services.redis.port", 6379)

    @property
    def qdrant_host(self) -> str:
        """Get Qdrant host."""
        return self.get("services.qdrant.host", "localhost")

    @property
    def qdrant_port(self) -> int:
        """Get Qdrant port."""
        return self.get("services.qdrant.port", 6333)

    @property
    def ollama_host(self) -> str:
        """Get Ollama host."""
        return self.get("services.ollama.host", "localhost")

    @property
    def ollama_port(self) -> int:
        """Get Ollama port."""
        return self.get("services.ollama.port", 11434)

    @property
    def langfuse_host(self) -> str:
        """Get Langfuse host."""
        return self.get("services.langfuse.host", "http://localhost:5000")

    @property
    def langfuse_enabled(self) -> bool:
        """Get Langfuse enabled flag."""
        return self.get("services.langfuse.enabled", False)

    @property
    def llm_gateway_host(self) -> str:
        """Get LLM Gateway host."""
        return os.getenv("LLM_GATEWAY_HOST", self.get("services.llm_gateway.host", "llm-gateway"))

    @property
    def llm_gateway_port(self) -> int:
        """Get LLM Gateway port."""
        return int(os.getenv("LLM_GATEWAY_PORT", self.get("services.llm_gateway.port", 8003)))

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get("logging.level", "INFO")

    @property
    def cache_ttl(self) -> int:
        """Get cache TTL in seconds."""
        return self.get("cache.default_ttl", 3600)

    def get_cache_ttl(self, key: str) -> int:
        """Get cache TTL for specific key."""
        return self.get(f"cache_ttl.{key}", 3600)

    @property
    def fallback_chain(self) -> list:
        """Get fallback chain."""
        return self.get("fallback.chain", [])

    @property
    def return_original_on_fallback(self) -> bool:
        """Get fallback setting."""
        return self.get("fallback.return_original_on_fallback", True)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
