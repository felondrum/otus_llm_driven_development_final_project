# ===========================================
# Styles management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import logging
import httpx
import os

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Import database
from database import (
    get_styles, get_style, create_style, update_style, delete_style,
    sync_style_to_core, delete_style_from_core, sync_all_styles_to_core
)


@api_router.get("")
async def list_styles():
    """Get list of all styles from PostgreSQL"""
    styles = await get_styles()
    return {"styles": styles, "count": len(styles)}


@api_router.post("")
async def create_style_endpoint(style: Dict[str, Any]):
    """Create a new style in PostgreSQL"""
    try:
        result = await create_style(style)
        return {"status": "created", "style": result}
    except Exception as e:
        logger.error(f"Failed to create style: {e}")
        raise HTTPException(status_code=500, detail="Failed to create style")


@api_router.put("/{style_id}")
async def update_style_endpoint(style_id: str, style: Dict[str, Any]):
    """Update a style in PostgreSQL"""
    result = await update_style(style_id, style)
    if result:
        return {"status": "updated", "style": result}
    else:
        raise HTTPException(status_code=404, detail=f"Style not found: {style_id}")


@api_router.delete("/{style_id}")
async def delete_style_endpoint(style_id: str):
    """Delete a style from PostgreSQL"""
    deleted = await delete_style(style_id)
    if deleted:
        return {"status": "deleted", "style_id": style_id}
    else:
        raise HTTPException(status_code=404, detail=f"Style not found: {style_id}")


@api_router.post("/{style_id}/sync")
async def sync_style(style_id: str):
    """Sync a specific style to Core Engine"""
    success = await sync_style_to_core(style_id)
    if success:
        return {"status": "synced", "style_id": style_id}
    else:
        raise HTTPException(status_code=404, detail=f"Style not found: {style_id}")


@api_router.post("/sync")
async def sync_all_styles_endpoint():
    """Sync all styles to Core Engine (Qdrant)"""
    count = await sync_all_styles_to_core()
    return {"status": "synced", "count": count}


@api_router.delete("/{style_id}/qdrant")
async def delete_style_from_qdrant(style_id: str):
    """Delete a style from Qdrant (for cleanup)"""
    from database import delete_style_from_core
    success = await delete_style_from_core(style_id)
    if success:
        return {"status": "deleted_from_qdrant", "style_id": style_id}
    else:
        raise HTTPException(status_code=404, detail=f"Style not found in Qdrant: {style_id}")


@api_router.get("/{style_id}/preview")
async def preview_style(style_id: str):
    """Get style preview with examples"""
    style = await get_style(style_id)
    
    if style:
        return {
            "style_id": style.get("style_id"),
            "name": style.get("name"),
            "description": style.get("description"),
            "category": style.get("category"),
            "tone": style.get("tone"),
            "examples": style.get("examples", []),
            "is_active": style.get("is_active")
        }
    else:
        raise HTTPException(status_code=404, detail=f"Style not found: {style_id}")


@api_router.get("/categories")
async def get_categories():
    """Get list of available style categories"""
    return {
        "categories": [
            "formal",
            "casual",
            "professional",
            "friendly",
            "technical",
            "creative",
            "academic",
            "journalistic",
            "literary",
            "persuasive"
        ]
    }


@api_router.get("/tones")
async def get_tones():
    """Get list of available tones"""
    return {
        "tones": [
            "neutral",
            "enthusiastic",
            "calm",
            "direct",
            "indirect",
            "humorous",
            "serious",
            "empathetic",
            "analytical",
            "inspirational"
        ]
    }


# ===========================================
# Core Engine (Module 1) Style endpoints
# ===========================================

@api_router.get("/core")
async def list_styles_from_core():
    """Get all styles from Core Engine (Module 1) via Retriever HTTP"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/styles",
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return {"styles": data.get("styles", []), "count": len(data.get("styles", []))}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get styles from Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.post("/core")
async def create_style_in_core(style: Dict[str, Any]):
    """Create a new style in Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/styles",
                json=style,
                timeout=10.0
            )
            if response.status_code == 201:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create style in Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.put("/core/{style_id}")
async def update_style_in_core(style_id: str, style: Dict[str, Any]):
    """Update a style in Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/styles/{style_id}",
                json=style,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Style not found in Core Engine: {style_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update style in Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.delete("/core/{style_id}")
async def delete_style_in_core(style_id: str):
    """Delete a style from Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/styles/{style_id}",
                timeout=10.0
            )
            if response.status_code == 200:
                return {"status": "deleted", "style_id": style_id}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Style not found in Core Engine: {style_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to delete style from Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )
