# ===========================================
# Users management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import os

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Import config
MODULE2_HOST = os.environ.get("MODULE2_HOST", "localhost")
MODULE2_PORT = int(os.environ.get("MODULE2_PORT", "8080"))


class UserCreate(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role: str = "user"
    metadata: Optional[dict] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    metadata: Optional[dict] = None


@api_router.get("")
async def list_users(limit: int = 100, offset: int = 0):
    """Get list of all users from Module 2 (Chat Frontend)"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users",
                params={"limit": limit, "offset": offset},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get users: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.post("")
async def create_user(user: UserCreate):
    """Create a new user in Module 2"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users",
                json=user.dict(),
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create user: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID from Module 2"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users/{user_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get user: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.get("/{user_id}/chats")
async def get_user_chats(user_id: str, limit: int = 100):
    """Get chat history for a user from Module 2"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users/{user_id}/chats",
                params={"limit": limit},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get user chats: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.put("/{user_id}")
async def update_user(user_id: str, user: UserUpdate):
    """Update a user in Module 2"""
    update_data = user.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users/{user_id}",
                json=update_data,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update user: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )


@api_router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete a user in Module 2"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://{MODULE2_HOST}:{MODULE2_PORT}/api/v1/users/{user_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"status": "deleted", "user_id": user_id}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to delete user: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Module 2: {e}")
        raise HTTPException(
            status_code=503,
            detail="Module 2 (Chat Frontend) is not available"
        )
