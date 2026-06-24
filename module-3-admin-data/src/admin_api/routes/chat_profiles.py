# ===========================================
# Chat Profiles management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

from database import (
    get_chat_profiles, get_chat_profile, create_chat_profile, update_chat_profile, delete_chat_profile,
    sync_chat_profile_to_core, sync_all_chat_profiles_to_core
)


@api_router.get("")
async def list_chat_profiles():
    """Get list of all chat profiles from PostgreSQL"""
    profiles = await get_chat_profiles()
    return {"chat_profiles": profiles, "count": len(profiles)}


@api_router.post("")
async def create_chat_profile_endpoint(profile: Dict[str, Any]):
    """Create a new chat profile in PostgreSQL"""
    required_fields = ["user_id", "full_name"]
    for field in required_fields:
        if field not in profile:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    try:
        result = await create_chat_profile(profile)
        return {"status": "created", "chat_profile": result}
    except Exception as e:
        logger.error(f"Failed to create chat profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create chat profile")


@api_router.put("/{user_id}")
async def update_chat_profile_endpoint(user_id: str, profile: Dict[str, Any]):
    """Update a chat profile in PostgreSQL"""
    if "user_id" in profile and profile["user_id"] != user_id:
        raise HTTPException(status_code=400, detail="user_id in body must match user_id in path")
    
    result = await update_chat_profile(user_id, profile)
    if result:
        return {"status": "updated", "chat_profile": result}
    else:
        raise HTTPException(status_code=404, detail=f"Chat profile not found: {user_id}")


@api_router.delete("/{user_id}")
async def delete_chat_profile_endpoint(user_id: str):
    """Delete a chat profile from PostgreSQL"""
    deleted = await delete_chat_profile(user_id)
    if deleted:
        return {"status": "deleted", "user_id": user_id}
    else:
        raise HTTPException(status_code=404, detail=f"Chat profile not found: {user_id}")


@api_router.post("/{user_id}/sync")
async def sync_chat_profile(user_id: str):
    """Sync a specific chat profile to Core Engine"""
    success = await sync_chat_profile_to_core(user_id)
    if success:
        return {"status": "synced", "user_id": user_id}
    else:
        raise HTTPException(status_code=404, detail=f"Chat profile not found: {user_id}")


@api_router.post("/sync")
async def sync_all_chat_profiles_endpoint():
    """Sync all chat profiles to Core Engine"""
    count = await sync_all_chat_profiles_to_core()
    return {"status": "synced", "count": count}
