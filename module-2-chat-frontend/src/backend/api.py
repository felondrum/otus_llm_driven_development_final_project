# ===========================================
# REST API endpoints for Chat Frontend
# ===========================================

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
from websocket import TEST_USERS, STYLES, connection_manager

# Import database module
from database import (
    init_database, get_all_profiles, get_profile_by_user_id,
    insert_profile, delete_profile, sync_with_core_engine,
    get_test_profiles, DB_PATH
)

# Initialize database on import
init_database()

# Try to sync with Core Engine, fallback to test profiles
try:
    profiles = get_all_profiles()
    if not profiles:
        logger.info("No profiles in database, loading test profiles")
        test_profiles = get_test_profiles()
        for profile in test_profiles:
            insert_profile(profile)
        profiles = test_profiles
    TEST_USERS = profiles
except Exception as e:
    logger.warning(f"Failed to load profiles from database: {e}. Using test profiles.")
    TEST_USERS = get_test_profiles()

# These are now just data, not async functions


@api_router.get("/users")
async def list_users():
    """Get list of test users"""
    return {"users": TEST_USERS}


@api_router.get("/styles")
async def list_styles():
    """Get list of available styles"""
    return {"styles": STYLES}


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
