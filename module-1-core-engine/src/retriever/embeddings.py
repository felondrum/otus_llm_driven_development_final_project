# Embeddings - генерация эмбеддингов через Ollama

import os
import aiohttp
from typing import List, Optional
from common.logging import logger


class Embedder:
    """Embedding generator using Ollama."""

    def __init__(self, host: str = None, port: int = 11434):
        # Use environment variable or default to ollama service name
        self.host = host or os.getenv("OLLAMA_HOST", "ollama")
        self.base_url = f"http://{self.host}:{port}"
        self.model = "nomic-embed-text"
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/embeddings"
                payload = {"model": self.model, "prompt": text}

                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Embedding API error: {response.status}")
                        return None

                    result = await response.json()
                    embedding = result.get("embedding", [])

                    # Validate embedding
                    if embedding and len(embedding) == 768:
                        return embedding
                    return None

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    async def health_check(self) -> bool:
        """Check if embedding model is available."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"{self.base_url}/api/tags"

                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        return any(m.get("name") == self.model for m in models)
                    return False
        except Exception as e:
            logger.error(f"Embedding health check failed: {e}")
            return False


# Global embedder instance
_embedder: Optional[Embedder] = None


def get_embedder(host: str = None, port: int = 11434) -> Embedder:
    """Get global embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder(host=host, port=port)
    return _embedder
