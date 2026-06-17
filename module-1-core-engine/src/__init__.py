"""
Chameleon Core Engine

Main package for the text adaptation system with LLM-based routing,
Qdrant-based RAG, and multi-provider LLM support.
"""

__version__ = "1.0.0"

try:
    from common.logging import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

__all__ = ["logger", "__version__"]
