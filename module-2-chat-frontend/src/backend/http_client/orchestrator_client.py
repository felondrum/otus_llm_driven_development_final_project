# HTTP Client for Core Engine Orchestrator

import os
import sys
import httpx
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Core Engine HTTP connection
ORCHESTRATOR_HOST = os.environ.get("ORCHESTRATOR_HOST", "127.0.0.1")
ORCHESTRATOR_PORT = os.environ.get("ORCHESTRATOR_PORT", "8001")


async def get_profile(user_id: str) -> Optional[Dict]:
    """
    Get user profile from Core Engine via HTTP
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        Dict with profile data or None if not available
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}/api/v1/profiles/{user_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("profile")
            else:
                logger.warning(f"Profile not found via HTTP for user_id: {user_id}")
                return None
    except httpx.RequestError as e:
        logger.warning(f"Failed to get profile via HTTP for user_id {user_id}: {e}")
        return None


def get_profile_sync(user_id: str) -> Optional[Dict]:
    """
    Synchronous version of get_profile for use in sync contexts
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        Dict with profile data or None if not available
    """
    try:
        import asyncio
        # Create a new event loop to run the async function
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(get_profile(user_id))
        finally:
            loop.close()
            asyncio.set_event_loop(None)
    except Exception as e:
        logger.warning(f"Failed to get profile (sync): {e}")
        return None


async def process_message(
    sender_id: str,
    recipient_id: str,
    text: str,
    style_name: Optional[str] = None,
    message_id: Optional[str] = None,
    room_id: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Call Core Engine HTTP to process and adapt message
    
    Args:
        sender_id: UUID of sender
        recipient_id: UUID of recipient
        text: Message text to adapt
        style_name: Optional writing style name
        message_id: Optional message ID for tracking
        room_id: Optional room ID
        metadata: Optional metadata dict
        
    Returns:
        Dict with adapted text and metadata
    """
    url = f"http://{ORCHESTRATOR_HOST}:{ORCHESTRATOR_PORT}/api/v1/messages/process"
    
    try:
        async with httpx.AsyncClient() as client:
            request_body = {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "text": text,
                "style_name": style_name or "",
                "message_id": message_id or "",
                "room_id": room_id or "",
                "metadata": metadata or {}
            }
            
            response = await client.post(
                url,
                json=request_body,
                timeout=30.0,
            )
            
            if response.status_code != 200:
                logger.error(f"Core Engine HTTP error: {response.status_code}")
                return {
                    "adapted_text": text,
                    "was_adapted": False,
                    "confidence": 0.0,
                    "model_used": "",
                    "processing_time_ms": 0,
                    "rules_applied": [],
                    "metadata": {
                        "from_cache": False,
                        "fallback_used": True,
                        "fallback_reason": f"HTTP error: {response.status_code}",
                        "tokens_prompt": 0,
                        "tokens_completion": 0,
                    }
                }
            
            result = response.json()
            
            logger.info(f"Core Engine processed message: was_adapted={result['was_adapted']}, model={result.get('model_used', '')}")
            
            return {
                "adapted_text": result.get("adapted_text", text),
                "was_adapted": result.get("was_adapted", False),
                "confidence": result.get("confidence", 1.0),
                "model_used": result.get("model_used", ""),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "rules_applied": result.get("rules_applied", []),
                "metadata": {
                    "from_cache": result.get("adaptation_metadata", {}).get("from_cache", False),
                    "fallback_used": result.get("adaptation_metadata", {}).get("fallback_used", False),
                    "fallback_reason": result.get("adaptation_metadata", {}).get("fallback_reason", ""),
                    "tokens_prompt": result.get("adaptation_metadata", {}).get("tokens_prompt", 0),
                    "tokens_completion": result.get("adaptation_metadata", {}).get("tokens_completion", 0),
                }
            }
            
    except httpx.RequestError as e:
        logger.error(f"HTTP error calling Core Engine: {e}")
        return {
            "adapted_text": text,
            "was_adapted": False,
            "confidence": 0.0,
            "model_used": "",
            "processing_time_ms": 0,
            "rules_applied": [],
            "metadata": {
                "from_cache": False,
                "fallback_used": True,
                "fallback_reason": f"HTTP error: {str(e)}",
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }
        }


def process_message_sync(
    sender_id: str,
    recipient_id: str,
    text: str,
    style_name: Optional[str] = None,
    message_id: Optional[str] = None,
    room_id: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Synchronous version of process_message for use in sync contexts
    
    Args:
        sender_id: UUID of sender
        recipient_id: UUID of recipient
        text: Message text to adapt
        style_name: Optional writing style name
        message_id: Optional message ID for tracking
        room_id: Optional room ID
        metadata: Optional metadata dict
        
    Returns:
        Dict with adapted text and metadata
    """
    try:
        import asyncio
        return asyncio.run(process_message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            text=text,
            style_name=style_name,
            message_id=message_id,
            room_id=room_id,
            metadata=metadata
        ))
    except Exception as e:
        logger.error(f"Failed to process message (sync): {e}")
        return {
            "adapted_text": text,
            "was_adapted": False,
            "confidence": 0.0,
            "model_used": "",
            "processing_time_ms": 0,
            "rules_applied": [],
            "metadata": {
                "from_cache": False,
                "fallback_used": True,
                "fallback_reason": f"Error: {str(e)}",
                "tokens_prompt": 0,
                "tokens_completion": 0,
            }
        }
