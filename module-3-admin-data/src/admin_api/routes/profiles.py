# ===========================================
# Profiles management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Admin API endpoints for profile management
# This will be exposed at /api/admin/profiles


@api_router.get("")
async def list_profiles():
    """Get list of all profiles from Module 2"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://chameleon-chat-1:8080/api/v1/profiles",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get profiles from Module 2: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.post("")
async def create_profile(profile: dict):
    """Create a new profile in Module 2"""
    import httpx
    
    required_fields = ["user_id", "full_name"]
    for field in required_fields:
        if field not in profile:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://chameleon-chat-1:8080/api/v1/profiles",
                json=profile,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create profile: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.put("/{user_id}")
async def update_profile(user_id: str, profile: dict):
    """Update a profile in Module 2"""
    import httpx
    
    if "user_id" in profile and profile["user_id"] != user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id in body must match user_id in path"
        )
    
    profile["user_id"] = user_id
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://chameleon-chat-1:8080/api/v1/profiles/{user_id}",
                json=profile,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update profile: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.delete("/{user_id}")
async def delete_profile(user_id: str):
    """Delete a profile in Module 2"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://chameleon-chat-1:8080/api/v1/profiles/{user_id}",
                timeout=10.0
            )
            if response.status_code == 200:
                return {"status": "deleted", "user_id": user_id}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to delete profile: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.post("/{user_id}/sync")
async def sync_profile_with_core(user_id: str):
    """Sync a specific profile with Core Engine (Module 1)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://chameleon-chat-1:8080/api/v1/profiles/{user_id}/sync",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to sync profile: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.post("/sync")
async def sync_all_profiles():
    """Sync all profiles with Core Engine (Module 1)"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://chameleon-chat-1:8080/api/v1/profiles/sync",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to sync profiles: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )
