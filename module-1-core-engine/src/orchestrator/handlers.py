# Обработчики запросов для оркестратора

from typing import Dict, Any, List, Optional
from common.logging import log_info

from .cache_manager import get_cache_manager
from .context_assembler import get_context_assembler
from .config import get_config, Config
from retriever.qdrant_client import get_qdrant_client
from common.schemas import UserProfile, CorporateRule, ArtisticStyle


class MessageHandler:
    """Handler for processing messages."""

    def __init__(self, config: Config = None):
        self.config = config or get_config()
        self.cache_manager = get_cache_manager(
            host=self.config.redis_host,
            port=self.config.redis_port,
            ttl=self.config.cache_ttl,
        )
        self.context_assembler = get_context_assembler()

    async def process_message(
        self,
        message_id: str,
        sender_id: str,
        recipient_id: str,
        text: str,
        room_id: Optional[str] = None,
        style_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process incoming message and return adapted version.

        Args:
            message_id: Unique message identifier
            sender_id: Sender user ID
            recipient_id: Recipient user ID
            text: Original message text
            room_id: Room ID (optional)
            style_name: Selected style name (optional)

        Returns:
            Dictionary with adapted message and metadata
        """
        log_info("Processing message", message_id=message_id)

        # Check cache
        cache_key = self.cache_manager.generate_key(
            message_id=message_id, text=text, recipient_id=recipient_id, rules=[]
        )

        cached = self.cache_manager.get(cache_key)
        if cached:
            log_info("Cache hit for message", message_id=message_id)
            return {
                "adapted_text": cached["adapted_text"],
                "was_adapted": cached["was_adapted"],
                "confidence": cached.get("confidence", 0.0),
                "model_used": cached.get("model_used", ""),
                "processing_time_ms": cached.get("processing_time_ms", 0),
                "rules_applied": cached.get("rules_applied", []),
                "from_cache": True,
                "message_id": message_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "room_id": room_id,
            }

        # Fetch profile, rules, styles, and corporate culture
        # This would call Retriever gRPC service
        profile = None
        rules = []
        styles = []
        culture_chunks = []

        # Get profile by recipient_id
        try:
            qdrant = get_qdrant_client()
            profile = qdrant.get_profile(recipient_id)
            if profile:
                log_info("Profile found", user_id=recipient_id, full_name=profile.get("full_name", ""))
            else:
                log_info("Profile not found", user_id=recipient_id)
        except Exception as e:
            log_info("Failed to get profile", user_id=recipient_id, error=str(e))

        # Get corporate culture chunks using vector search
        try:
            qdrant = get_qdrant_client()
            culture_chunks = await qdrant.get_culture_chunks(
                query_text=text,
                limit=3,  # Number of culture chunks to retrieve
                filter_category=None  # No category filter, search across all
            )
            log_info("Culture chunks retrieved", count=len(culture_chunks))
        except Exception as e:
            log_info("Failed to get culture chunks", error=str(e))

        # Assemble context with culture chunks
        _ = self.context_assembler.assemble_context(
            original_text=text,
            profile=profile,
            rules=rules,
            styles=styles,
            style_name=style_name,
            culture_chunks=culture_chunks,  # Culture chunks added
        )

        # Call LLM
        # This would call LLM Gateway HTTP service
        adapted_text = f"Adapted: {text}"
        was_adapted = True
        confidence = 0.95
        model_used = "mock-model"
        processing_time_ms = 100

        # Build response
        response = {
            "adapted_text": adapted_text,
            "was_adapted": was_adapted,
            "confidence": confidence,
            "model_used": model_used,
            "processing_time_ms": processing_time_ms,
            "rules_applied": [rule.get("rule_id", "") for rule in rules],
            "from_cache": False,
            "fallback_used": False,
            "fallback_reason": "",
            "tokens_prompt": 100,
            "tokens_completion": 50,
            "message_id": message_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "room_id": room_id,
            "culture_chunks_used": len(culture_chunks),  # Metadata about culture usage
        }

        # Cache response
        self.cache_manager.set(cache_key, response)

        log_info("Message processed successfully", message_id=message_id)
        return response

    async def batch_process_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple messages in batch.

        Args:
            messages: List of message dictionaries

        Returns:
            List of adapted message responses
        """
        results = []
        for msg in messages:
            result = await self.process_message(
                message_id=msg.get("message_id", ""),
                sender_id=msg.get("sender_id", ""),
                recipient_id=msg.get("recipient_id", ""),
                text=msg.get("text", ""),
                room_id=msg.get("room_id"),
                style_name=msg.get("style_name"),
            )
            results.append(result)
        return results


# Global handler instance
_handler: Optional[MessageHandler] = None


def get_message_handler(config: Config = None) -> MessageHandler:
    """Get global message handler instance."""
    global _handler
    if _handler is None:
        _handler = MessageHandler(config)
    return _handler
