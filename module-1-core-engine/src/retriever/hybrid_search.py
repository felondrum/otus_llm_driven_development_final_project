# Гибридный поиск - vector search + keyword filters

from typing import List, Dict, Any, Optional
from common.logging import logger
from .embeddings import get_embedder
from .qdrant_client import get_qdrant_client


class HybridSearcher:
    """Hybrid search combining vector and keyword search."""

    def __init__(self):
        self.embedder = get_embedder()
        self.qdrant = get_qdrant_client()

    async def search_rules(
        self,
        query_text: str,
        sender_role: str = None,
        recipient_role: str = None,
        categories: List[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search corporate rules using hybrid approach.

        Args:
            query_text: Text to search for
            sender_role: Role of message sender (optional)
            recipient_role: Role of message recipient (optional)
            categories: List of categories to filter (optional)
            limit: Maximum number of results

        Returns:
            List of matching rules with relevance scores
        """
        # Generate embedding for query
        query_vector = await self.embedder.generate_embedding(query_text)
        if not query_vector:
            logger.warning("Failed to generate embedding for query")
            return []

        # Perform vector search
        rules = self.qdrant.search_rules(
            query_vector=query_vector,
            sender_role=sender_role,
            recipient_role=recipient_role,
            limit=limit * 2,  # Get more candidates
        )

        # Apply keyword filters if provided
        if sender_role or recipient_role or categories:
            filtered_rules = []
            for rule in rules:
                # Apply filters
                if sender_role and sender_role not in rule.get("condition", ""):
                    continue
                if recipient_role and recipient_role not in rule.get("condition", ""):
                    continue
                if categories and rule.get("category") not in categories:
                    continue
                filtered_rules.append(rule)
            rules = filtered_rules

        # Return top results
        return rules[:limit]

    async def search_profiles(
        self,
        query_text: str,
        roles: List[str] = None,
        departments: List[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search user profiles using hybrid approach.

        Args:
            query_text: Text to search for
            roles: List of roles to filter (optional)
            departments: List of departments to filter (optional)
            limit: Maximum number of results

        Returns:
            List of matching profiles
        """
        # For profiles, we do exact match by user_id first
        # Then fallback to vector search

        # This would be expanded for full profile search
        return []

    async def search_styles(
        self, query_text: str, emotion_tags: List[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search artistic styles using hybrid approach.

        Args:
            query_text: Text to search for
            emotion_tags: List of emotion tags to filter (optional)
            limit: Maximum number of results

        Returns:
            List of matching styles
        """
        # For styles, we do random or by tag
        styles = self.qdrant.get_style_examples(style_name="", sample_count=limit)

        # Apply emotion tag filters if provided
        if emotion_tags:
            filtered_styles = []
            for style in styles:
                style_tags = style.get("emotion_tags", [])
                if any(tag in style_tags for tag in emotion_tags):
                    filtered_styles.append(style)
            styles = filtered_styles

        return styles[:limit]

    async def search_culture(
        self,
        query_text: str,
        limit: int = 5,
        filter_category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search corporate culture using vector search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            filter_category: Optional category filter (e.g., "principles", "values")

        Returns:
            List of matching culture chunks
        """
        return await self.qdrant.get_culture_chunks(
            query_text=query_text,
            limit=limit,
            filter_category=filter_category
        )


# Global searcher instance
_searcher: Optional[HybridSearcher] = None


def get_searcher() -> HybridSearcher:
    """Get global searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = HybridSearcher()
    return _searcher
