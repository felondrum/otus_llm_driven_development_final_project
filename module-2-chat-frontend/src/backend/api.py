# ===========================================
# REST API endpoints for Chat Frontend
# ===========================================

import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Хранилище сообщений в памяти (для демонстрации)
# В реальном приложении нужно использовать базу данных
# Все сообщения хранятся в одном списке и фильтруются по需要
all_chat_messages = []


# Import from websocket module (same directory)
from websocket import connection_manager, get_test_users, get_styles as websocket_get_styles

# Import database module
from database import (
    init_database_and_load_profiles, get_all_profiles, get_profile_by_user_id,
    insert_profile, delete_profile, sync_with_core_engine, sync_with_core_engine_async,
    get_test_profiles, DB_PATH
)

# Import HTTP client for Module 3 Admin API
try:
    import httpx
    MODULE3_HTTP_ENABLED = True
except ImportError:
    logger.warning("Could not import httpx for Module 3")
    MODULE3_HTTP_ENABLED = False

# Module 3 Admin API connection (take from environment variables)
MODULE3_HOST = os.environ.get("MODULE3_HOST", "127.0.0.1")
MODULE3_PORT = os.environ.get("MODULE3_PORT", "8200")

# Initialize database and load profiles from Module 3 on import
import asyncio

async def init_app_profiles():
    """Initialize application profiles from Module 3"""
    try:
        profiles = await init_database_and_load_profiles()
        return profiles
    except Exception as e:
        logger.error(f"Failed to initialize profiles: {e}")
        return None

# Run async initialization synchronously during module import
# TEST_USERS is now loaded dynamically from get_test_users()
logger.info("Profile initialization completed - TEST_USERS loaded dynamically from Module 3")

# These are now just data, not async functions


# ===========================================
# Module 3 Admin API functions
# ===========================================

async def get_chat_profiles_from_module3() -> list:
    """Get chat profiles from Module 3 Admin API"""
    if not MODULE3_HTTP_ENABLED:
        logger.warning("Module 3 HTTP client not available")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{MODULE3_HOST}:{MODULE3_PORT}/api/v1/admin/chat_profiles",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("chat_profiles", [])
            else:
                logger.warning(f"Failed to get chat profiles from Module 3: {response.status_code}")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to connect to Module 3: {e}")
        return []


async def get_styles_from_module3() -> list:
    """Get styles from Module 3 Admin API"""
    if not MODULE3_HTTP_ENABLED:
        logger.warning("Module 3 HTTP client not available")
        return []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{MODULE3_HOST}:{MODULE3_PORT}/api/v1/admin/styles",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                styles = data.get("styles", [])
                # Transform styles: extract style_id as id, name as name
                return [{"id": s.get("style_id"), "name": s.get("name")} for s in styles]
            else:
                logger.warning(f"Failed to get styles from Module 3: {response.status_code}")
                return []
    except httpx.RequestError as e:
        logger.warning(f"Failed to connect to Module 3: {e}")
        return []


async def sync_chat_profiles_from_module3() -> int:
    """Sync chat profiles from Module 3 to local database"""
    if not MODULE3_HTTP_ENABLED:
        logger.warning("Module 3 HTTP client not available")
        return 0
    
    profiles = await get_chat_profiles_from_module3()
    count = 0
    
    for profile in profiles:
        try:
            insert_profile(profile)
            count += 1
        except Exception as e:
            logger.error(f"Failed to insert profile {profile.get('user_id')}: {e}")
    
    logger.info(f"Synced {count} chat profiles from Module 3")
    return count


@api_router.get("/users")
async def list_users():
    """Get list of test users"""
    # Load users dynamically from database (Module 3 PostgreSQL)
    users = get_test_users()
    return {"users": users}


@api_router.get("/styles")
async def list_styles():
    """Get list of available styles from Module 3 PostgreSQL"""
    styles = await get_styles_from_module3()
    return {"styles": styles}


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chameleon-chat-api"}


@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "chameleon-chat-api",
        "version": "1.0.0",
        "endpoints": {
            "users": "/api/v1/users",
            "profiles": "/api/v1/profiles",
            "styles": "/api/v1/styles",
            "health": "/api/v1/health",
            "messages": "/api/v1/messages/{recipient_id}"
        }
    }


@api_router.get("/messages/{recipient_id}")
async def get_chat_history(recipient_id: str):
    """Get chat history with a specific recipient"""
    # Фильтруем все сообщения, чтобы показать только те, где участвует текущий пользователь
    # (отправленные нами или полученные нами)
    filtered_messages = [
        msg for msg in all_chat_messages 
        if msg.get("from") == recipient_id or msg.get("to") == recipient_id
    ]
    return {"messages": filtered_messages}


@api_router.post("/messages/{recipient_id}")
async def save_message(recipient_id: str, message: dict):
    """Save a message to chat history"""
    # Используем recipient_id как получателя, извлекаем отправителя из сообщения
    sender_id = message.get("from")
    
    if not sender_id:
        return {"status": "error", "message": "Message must have 'from' field"}
    
    # Просто добавляем сообщение в общий список
    all_chat_messages.append(message)
    return {"status": "saved", "message_id": message.get("id")}


# ===========================================
# Profile management endpoints
# ===========================================

# MUST be before /profiles and /profiles/{user_id} due to route matching order
@api_router.post("/profiles/sync_module3")
async def sync_profiles_module3():
    """Sync profiles from Module 3 Admin API"""
    try:
        count = await sync_chat_profiles_from_module3()
        return {"status": "synced", "count": count}
    except Exception as e:
        logger.error(f"Error syncing profiles from Module 3: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/profiles")
async def list_profiles():
    """Get list of all profiles"""
    try:
        profiles = get_all_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Error getting profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/profiles/{user_id}")
async def get_profile(user_id: str):
    """Get a profile by user_id"""
    try:
        profile = get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
        return {"profile": profile}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/profiles")
async def create_profile(profile: dict):
    """Create a new profile"""
    required_fields = ["user_id", "full_name"]
    for field in required_fields:
        if field not in profile:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    try:
        insert_profile(profile)
        return {"status": "created", "user_id": profile["user_id"]}
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/profiles/{user_id}")
async def update_profile(user_id: str, profile: dict):
    """Update a profile"""
    if "user_id" in profile and profile["user_id"] != user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id in body must match user_id in path"
        )
    
    profile["user_id"] = user_id
    
    try:
        existing = get_profile_by_user_id(user_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
        
        insert_profile(profile)
        return {"status": "updated", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/profiles/{user_id}")
async def delete_user_profile(user_id: str):
    """Delete a profile"""
    try:
        existing = get_profile_by_user_id(user_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
        
        delete_profile(user_id)
        return {"status": "deleted", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/profiles/sync")
async def sync_profiles():
    """Sync profiles with Core Engine"""
    try:
        success = sync_with_core_engine()
        if success:
            return {"status": "synced", "message": "Profiles synced with Core Engine"}
        else:
            raise HTTPException(status_code=503, detail="Core Engine is not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
