# ===========================================
# Admin API Configuration for Module 3
# ===========================================

import os

# Core Engine (Module 1) configuration - HTTP
CORE_ENGINE_HTTP_HOST = os.getenv("CORE_ENGINE_HTTP_HOST", "localhost")
CORE_ENGINE_HTTP_PORT = int(os.getenv("CORE_ENGINE_HTTP_PORT", "8001"))

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis123")

# LLM Gateway configuration
LLM_GATEWAY_HOST = os.getenv("LLM_GATEWAY_HOST", "localhost")
LLM_GATEWAY_PORT = int(os.getenv("LLM_GATEWAY_PORT", "8003"))

# Retriever HTTP configuration
RETRIEVER_HTTP_HOST = os.getenv("RETRIEVER_HTTP_HOST", "localhost")
RETRIEVER_HTTP_PORT = int(os.getenv("RETRIEVER_HTTP_PORT", "8002"))

# Module 2 (Chat Frontend) configuration
MODULE2_HOST = os.getenv("MODULE2_HOST", "localhost")
MODULE2_PORT = int(os.getenv("MODULE2_PORT", "8080"))

# PostgreSQL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chameleon:chameleon123@localhost:5432/chameleon_admin")


def get_core_engine_http_url() -> str:
    """Get Core Engine HTTP URL."""
    return f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}"


def get_retriever_http_url() -> str:
    """Get Retriever HTTP URL."""
    return f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}"


def get_qdrant_url() -> str:
    """Get Qdrant URL."""
    return f"http://{QDRANT_HOST}:{QDRANT_PORT}"


def get_module2_url() -> str:
    """Get Module 2 (Chat Frontend) URL."""
    return f"http://{MODULE2_HOST}:{MODULE2_PORT}"
