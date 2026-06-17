# Клиент Qdrant

import os
from typing import Dict, Any, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
)
from common.logging import logger, log_info

# Import embedder for generating query vectors
from .embeddings import get_embedder


class QdrantClientWrapper:
    """Wrapper for Qdrant client with collection management."""

    def __init__(self, host: str = None, port: int = 6333):
        # Use environment variable or default to localhost (for tests) or qdrant (for docker)
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collections = ["user_profiles", "corporate_rules", "artistic_styles", "corporate_culture"]
        # Initialize embedder for query vector generation
        self.embedder = get_embedder()

    def connect(self):
        """Connect to Qdrant and ensure collections exist."""
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Test connection
                self.client.get_collections()
                logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

                # Create collections if they don't exist
                current_collections = [
                    c.name for c in self.client.get_collections().collections
                ]

                for collection in self.collections:
                    if collection not in current_collections:
                        self._create_collection(collection)

                log_info("Qdrant ready", collections=self.collections)
                return

            except Exception as e:
                logger.error(
                    f"Failed to connect to Qdrant (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    import time

                    logger.info(f"Retrying Qdrant connection in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        logger.error(f"Failed to connect to Qdrant after {max_retries} attempts")
        raise ConnectionError(f"Failed to connect to Qdrant at {self.host}:{self.port}")

    def _create_collection(self, collection_name: str):
        """Create a collection with vector config."""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {collection_name}")

    async def get_culture_chunks(
        self,
        query_text: str,
        limit: int = 5,
        filter_category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant chunks from corporate culture using vector search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            filter_category: Optional category filter (e.g., "principles", "values")

        Returns:
            List of matching culture chunks
        """
        try:
            # Generate embedding for query
            query_vector = await self.embedder.generate_embedding(query_text)

            if not query_vector:
                logger.warning("Failed to generate embedding for culture query")
                return []

            # Build filter if category specified (Qdrant client v1.8+ API)
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            filter = None
            if filter_category:
                filter = Filter(
                    must=[
                        FieldCondition(
                            key="section_title",
                            match=MatchValue(value=filter_category)
                        )
                    ]
                )

            search_result = self.client.search(
                collection_name="corporate_culture",
                query_vector=query_vector,
                query_filter=filter,
                limit=limit,
            )

            return [hit.payload for hit in search_result]
        except Exception as e:
            logger.error(f"Failed to get culture chunks: {e}")
            return []

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id."""
        try:
            # Generate UUID from user_id for Qdrant storage
            import uuid as uuid_module

            # Check if user_id looks like a UUID (contains hyphens in correct positions)
            is_uuid = (
                len(user_id) == 36
                and user_id.count("-") == 4
                and all(
                    c in "0123456789abcdef" for c in user_id.replace("-", "")
                )
            )
            
            if is_uuid:
                # user_id is a UUID (v4 or v5), use it directly
                point_id = user_id
            else:
                # user_id is a string like 'alex_i', generate UUID5
                point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, user_id))

            result = self.client.retrieve(
                collection_name="user_profiles", ids=[point_id]
            )
            if result and len(result) > 0:
                profile = result[0].payload
                # Apply mappings to convert string values to proper format
                return self._map_profile(profile)
            return None
        except Exception as e:
            logger.error(f"Failed to get profile {user_id}: {e}")
            return None

    def _map_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Convert string enum values to numeric values for protobuf compatibility."""
        honorific_type_map = {
            "first_name": 1,
            "patronymic": 3,
            "last_name": 2,
            "title": 4,
            "default": 0,
        }
        
        communication_mode_map = {
            "informal": 2,
            "formal": 1,
            "neutral": 0,
            "technical": 3,
            "collaborative": 4,
        }
        
        # Convert honorific_type
        if "honorific_type" in profile:
            ht = profile["honorific_type"]
            if isinstance(ht, str):
                profile["honorific_type"] = honorific_type_map.get(ht, 0)
            elif isinstance(ht, int):
                pass  # Already an int
        
        # Convert communication_mode
        if "communication_mode" in profile:
            cm = profile["communication_mode"]
            if isinstance(cm, str):
                profile["communication_mode"] = communication_mode_map.get(cm, 0)
            elif isinstance(cm, int):
                pass  # Already an int
        
        return profile

    async def get_rules(
        self, sender_role: str, recipient_role: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get corporate rules by roles."""
        try:
            # Generate embedding for query
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            query_text = f"sender_role:{sender_role} recipient_role:{recipient_role}"
            query_vector = await embedder.generate_embedding(query_text)

            if not query_vector:
                logger.warning("Failed to generate embedding for rules query")
                return []

            filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value="address"))]
            )

            search_result = self.client.search(
                collection_name="corporate_rules",
                query_vector=query_vector,
                query_filter=filter,
                limit=limit,
            )

            # Map transformation to transformation_prompt for compatibility
            rules = [hit.payload for hit in search_result]
            for rule in rules:
                if "transformation" in rule and "transformation_prompt" not in rule:
                    rule["transformation_prompt"] = rule["transformation"]
            return rules
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return []

    def get_style_examples(
        self, style_name: str, sample_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Get random style examples."""
        try:
            # Use search with filter to get random samples
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            filter = Filter(
                must=[
                    FieldCondition(key="style_name", match=MatchValue(value=style_name))
                ]
            )

            result = self.client.search(
                collection_name="artistic_styles",
                query_vector=[0.0] * 768,  # Dummy vector for filter-only search
                filter=filter,
                limit=sample_count,
            )

            if result and len(result) > 0:
                return [p.payload for p in result]
            return []
        except Exception as e:
            logger.error(f"Failed to get style examples: {e}")
            return []

    def search_rules(
        self,
        query_vector: List[float],
        sender_role: str,
        recipient_role: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search rules by vector."""
        try:
            filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value="address"))]
            )

            search_result = self.client.search(
                collection_name="corporate_rules",
                query_vector=query_vector,
                filter=filter,
                limit=limit,
            )

            # Map transformation to transformation_prompt for compatibility
            rules = [hit.payload for hit in search_result]
            for rule in rules:
                if "transformation" in rule and "transformation_prompt" not in rule:
                    rule["transformation_prompt"] = rule["transformation"]
            return rules
        except Exception as e:
            logger.error(f"Failed to search rules: {e}")
            return []

    def close(self):
        """Close Qdrant connection."""
        self.client.close()
        logger.info("Qdrant connection closed")


# Global client instance
_qdrant_client: Optional[QdrantClientWrapper] = None


def get_qdrant_client(host: str = None, port: int = 6333) -> QdrantClientWrapper:
    """Get global Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClientWrapper(host=host, port=port)
        _qdrant_client.connect()
    return _qdrant_client
