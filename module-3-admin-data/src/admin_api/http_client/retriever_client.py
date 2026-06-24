# ===========================================
# HTTP Client for Core Engine Retriever
# ===========================================

import os
import sys
import httpx
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Core Engine Retriever HTTP connection
RETRIEVER_HOST = os.environ.get("RETRIEVER_HOST", "127.0.0.1")
RETRIEVER_PORT = os.environ.get("RETRIEVER_PORT", "8002")


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
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/profiles/{user_id}",
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


async def get_rules() -> List[Dict]:
    """
    Get all rules from Core Engine via HTTP
    
    Returns:
        List of rule dictionaries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/rules",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("rules", [])
            else:
                logger.warning("Failed to get rules via HTTP")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to get rules via HTTP: {e}")
        return []


async def search_rules(query: str, sender_role: str = "", recipient_role: str = "", limit: int = 10) -> List[Dict]:
    """
    Search rules in Core Engine via HTTP
    
    Args:
        query: Search query
        sender_role: Sender role filter
        recipient_role: Recipient role filter
        limit: Maximum number of results
        
    Returns:
        List of matching rule dictionaries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/rules/search",
                params={
                    "query": query,
                    "sender_role": sender_role,
                    "recipient_role": recipient_role,
                    "limit": limit
                },
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("rules", [])
            else:
                logger.warning("Failed to search rules via HTTP")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to search rules via HTTP: {e}")
        return []


async def search_culture(query: str) -> List[Dict]:
    """
    Search culture in Core Engine via HTTP
    
    Args:
        query: Search query
        
    Returns:
        List of matching culture dictionaries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/culture/search",
                params={"query": query},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("cultures", [])
            else:
                logger.warning("Failed to search culture via HTTP")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to search culture via HTTP: {e}")
        return []


async def get_styles() -> List[Dict]:
    """
    Get all styles from Core Engine via HTTP
    
    Returns:
        List of style dictionaries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("styles", [])
            else:
                logger.warning("Failed to get styles via HTTP")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to get styles via HTTP: {e}")
        return []


async def get_style(style_id: str) -> Optional[Dict]:
    """
    Get a specific style by ID from Core Engine via HTTP
    
    Args:
        style_id: Style ID
        
    Returns:
        Dict with style data or None if not found
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles/{style_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("style")
            else:
                logger.warning(f"Style not found via HTTP for style_id: {style_id}")
                return None
    except httpx.RequestError as e:
        logger.warning(f"Failed to get style via HTTP for style_id {style_id}: {e}")
        return None


async def create_style(style_data: Dict) -> Optional[Dict]:
    """
    Create a new style in Core Engine via HTTP
    
    Args:
        style_data: Style data dict with name, description, etc.
        
    Returns:
        Dict with created style data or None if failed
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles",
                json=style_data,
                timeout=5.0
            )
            if response.status_code == 201:
                return response.json()
            else:
                logger.warning(f"Failed to create style via HTTP: {response.status_code}")
                return None
    except httpx.RequestError as e:
        logger.warning(f"Failed to create style via HTTP: {e}")
        return None


async def update_style(style_id: str, style_data: Dict) -> Optional[Dict]:
    """
    Update a style in Core Engine via HTTP
    
    Args:
        style_id: Style ID
        style_data: Style data dict with updates
        
    Returns:
        Dict with updated style data or None if failed
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles/{style_id}",
                json=style_data,
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to update style via HTTP: {response.status_code}")
                return None
    except httpx.RequestError as e:
        logger.warning(f"Failed to update style via HTTP: {e}")
        return None


async def delete_style(style_id: str) -> bool:
    """
    Delete a style in Core Engine via HTTP
    
    Args:
        style_id: Style ID
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles/{style_id}",
                timeout=5.0
            )
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Failed to delete style via HTTP: {response.status_code}")
                return False
    except httpx.RequestError as e:
        logger.warning(f"Failed to delete style via HTTP: {e}")
        return False


async def get_style_examples() -> List[Dict]:
    """
    Get all style examples from Core Engine via HTTP
    
    Returns:
        List of style example dictionaries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/styles/examples",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("examples", [])
            else:
                logger.warning("Failed to get style examples via HTTP")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to get style examples via HTTP: {e}")
        return []


async def reload_rules() -> bool:
    """
    Reload rules in Core Engine via HTTP
    
    Returns:
        True if reload successful, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{RETRIEVER_HOST}:{RETRIEVER_PORT}/api/v1/rules/reload",
                timeout=5.0
            )
            if response.status_code == 200:
                return True
            else:
                logger.warning("Failed to reload rules via HTTP")
                return False
    except httpx.RequestError as e:
        logger.warning(f"Failed to reload rules via HTTP: {e}")
        return False
