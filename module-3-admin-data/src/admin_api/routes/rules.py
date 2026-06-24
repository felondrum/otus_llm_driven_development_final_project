# ===========================================
# Rules management API for Admin
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
    get_rules, get_rule, create_rule, update_rule, delete_rule,
    sync_rule_to_core, delete_rule_from_core, sync_all_rules_to_core
)


@api_router.get("")
async def list_rules():
    """Get list of all rules from PostgreSQL"""
    rules = await get_rules()
    return {"rules": rules, "count": len(rules)}


@api_router.post("")
async def create_rule_endpoint(rule: Dict[str, Any]):
    """Create a new rule in PostgreSQL"""
    try:
        result = await create_rule(rule)
        return {"status": "created", "rule": result}
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create rule")


@api_router.put("/{rule_id}")
async def update_rule_endpoint(rule_id: str, rule: Dict[str, Any]):
    """Update a rule in PostgreSQL"""
    result = await update_rule(rule_id, rule)
    if result:
        return {"status": "updated", "rule": result}
    else:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")


@api_router.delete("/{rule_id}")
async def delete_rule_endpoint(rule_id: str):
    """Delete a rule from PostgreSQL"""
    deleted = await delete_rule(rule_id)
    if deleted:
        return {"status": "deleted", "rule_id": rule_id}
    else:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")


@api_router.post("/{rule_id}/sync")
async def sync_rule(rule_id: str):
    """Sync a specific rule to Core Engine"""
    success = await sync_rule_to_core(rule_id)
    if success:
        return {"status": "synced", "rule_id": rule_id}
    else:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")


@api_router.post("/reload")
async def reload_rules():
    """Reload all rules from database into Core Engine cache via HTTP"""
    rules = await get_rules()
    success_count = 0
    
    for rule in rules:
        if await sync_rule_to_core(rule["rule_id"]):
            success_count += 1
    
    if success_count > 0:
        return {
            "status": "reload_started",
            "message": f"Rules reload started - {success_count} rules synced"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to reload rules")


@api_router.post("/sync")
async def sync_all_rules_endpoint():
    """Sync all rules to Core Engine (Qdrant)"""
    count = await sync_all_rules_to_core()
    return {"status": "synced", "count": count}


@api_router.delete("/{rule_id}/qdrant")
async def delete_rule_from_qdrant(rule_id: str):
    """Delete a rule from Qdrant (for cleanup)"""
    from database import delete_rule_from_core
    success = await delete_rule_from_core(rule_id)
    if success:
        return {"status": "deleted_from_qdrant", "rule_id": rule_id}
    else:
        raise HTTPException(status_code=404, detail=f"Rule not found in Qdrant: {rule_id}")


@api_router.get("/categories")
async def get_categories():
    """Get list of available rule categories"""
    return {
        "categories": [
            "general",
            "security",
            "content",
            "behavior",
            "format",
            "tone",
            "domain_knowledge",
            "personalization"
        ]
    }


@api_router.get("/roles")
async def get_roles():
    """Get list of available rule roles"""
    return {
        "roles": [
            "system",
            "admin",
            "moderator",
            "user",
            "guest",
            "bot",
            "anonymous"
        ]
    }


@api_router.get("/priorities")
async def get_priorities():
    """Get available priority levels"""
    return {
        "priorities": [
            {"level": 0, "name": "lowest"},
            {"level": 1, "name": "low"},
            {"level": 2, "name": "normal"},
            {"level": 3, "name": "high"},
            {"level": 4, "name": "highest"},
            {"level": 5, "name": "critical"}
        ]
    }


# ===========================================
# Core Engine (Module 1) Rule endpoints
# ===========================================

@api_router.get("/core")
async def list_rules_from_core(
    sender_role: str = "user",
    recipient_role: str = "",
    limit: int = 100,
    offset: int = 0
):
    """Get all rules from Core Engine (Module 1) via Retriever HTTP"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/rules",
                params={
                    "sender_role": sender_role,
                    "recipient_role": recipient_role,
                    "limit": limit,
                    "offset": offset
                },
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                return {"rules": data.get("rules", []), "count": len(data.get("rules", []))}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get rules from Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.post("/core")
async def create_rule_in_core(rule: Dict[str, Any]):
    """Create a new rule in Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/rules",
                json=rule,
                timeout=10.0
            )
            if response.status_code == 201:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create rule in Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.put("/core/{rule_id}")
async def update_rule_in_core(rule_id: str, rule: Dict[str, Any]):
    """Update a rule in Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/rules/{rule_id}",
                json=rule,
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Rule not found in Core Engine: {rule_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update rule in Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )


@api_router.delete("/core/{rule_id}")
async def delete_rule_in_core(rule_id: str):
    """Delete a rule from Core Engine (Module 1) Qdrant"""
    import httpx
    
    from config import RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/rules/{rule_id}",
                timeout=10.0
            )
            if response.status_code == 200:
                return {"status": "deleted", "rule_id": rule_id}
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Rule not found in Core Engine: {rule_id}")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to delete rule from Core Engine: {response.text}"
                )
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Retriever: {e}")
        raise HTTPException(
            status_code=503,
            detail="Retriever (Core Engine) is not available"
        )
