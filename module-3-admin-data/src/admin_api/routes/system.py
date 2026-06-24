# ===========================================
# System management API for Admin
# ===========================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Import config
from config import (
    CORE_ENGINE_HTTP_HOST, CORE_ENGINE_HTTP_PORT,
    RETRIEVER_HTTP_HOST, RETRIEVER_HTTP_PORT,
    QDRANT_HOST, QDRANT_PORT,
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
)


class SystemStatus(BaseModel):
    service: str
    status: str
    version: Optional[str] = None
    details: Optional[dict] = None


class CacheClearResponse(BaseModel):
    status: str
    message: str
    cleared: int = 0


class ReloadResponse(BaseModel):
    status: str
    message: str
    affected: int = 0


@api_router.get("/status")
async def get_system_status():
    """Get status of all services (only Core Engine for now)"""
    status = {
        "system": "healthy",
        "services": {}
    }
    
    # Only check core_engine for now
    services_to_check = [
        ("core_engine", f"{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}", "http")
    ]
    
    async def check_service(name: str, url: str, type_: str) -> dict:
        try:
            if type_ == "http":
                async with httpx.AsyncClient(timeout=3.0) as client:
                    host, port = url.split(":")
                    response = await client.get(f"http://{host}:{port}/health", timeout=3.0)
                    if response.status_code == 200:
                        return {"status": "healthy", "type": "http", "code": response.status_code}
                    return {"status": "unhealthy", "type": "http", "code": response.status_code}
            elif type_ == "redis":
                import redis
                host, port = url.split(":")
                try:
                    r = redis.Redis(host=host, port=int(port), password=REDIS_PASSWORD or None)
                    r.ping()
                    return {"status": "healthy", "type": "redis"}
                except Exception as e:
                    return {"status": "unhealthy", "error": str(e), "type": "redis"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "type": type_}
    
    # Check services concurrently
    tasks = [check_service(name, url, type_) for name, url, type_ in services_to_check]
    results = await asyncio.gather(*tasks)
    
    for (name, _, _), result in zip(services_to_check, results):
        status["services"][name] = result
        if result["status"] == "unhealthy":
            status["system"] = "degraded"
    
    return status


@api_router.post("/cache/clear")
async def clear_cache(cache_type: Optional[str] = "all"):
    """Clear cache in Redis or other cache systems"""
    try:
        if cache_type == "all" or cache_type == "redis":
            import redis
            try:
                r = redis.Redis(host="localhost", port=6379, timeout=3)
                r.flushdb()
                cache_cleared = "redis"
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                cache_cleared = "none"
        else:
            cache_cleared = "none"
        
        return {
            "status": "success",
            "message": f"Cache cleared: {cache_cleared}",
            "cache_type": cache_type
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@api_router.post("/rules/reload")
async def reload_rules_in_cache():
    """Reload rules from database into Core Engine cache"""
    try:
        url = f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}/api/v1/rules/reload"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "reload_started",
                    "message": result.get("message", "Reload started"),
                    "rules_count": result.get("rules_count", 0)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Core Engine service unavailable: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine: {e}")
        raise HTTPException(status_code=503, detail=f"Core Engine service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to reload rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload rules: {str(e)}")


@api_router.post("/styles/reload")
async def reload_styles_in_cache():
    """Reload styles from database into Core Engine cache"""
    try:
        url = f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}/api/v1/styles/reload"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "reload_started",
                    "message": result.get("message", "Reload started"),
                    "styles_count": result.get("styles_count", 0)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Core Engine service unavailable: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine: {e}")
        raise HTTPException(status_code=503, detail=f"Core Engine service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to reload styles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload styles: {str(e)}")


@api_router.post("/profiles/sync")
async def sync_profiles_with_core():
    """Sync profiles from Module 2 to Core Engine"""
    try:
        module2_host = os.environ.get("MODULE2_HOST", "localhost")
        module2_port = os.environ.get("MODULE2_PORT", "8080")
        
        url = f"http://{module2_host}:{module2_port}/api/v1/profiles/sync"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, timeout=30.0)
            
            if response.status_code == 200:
                return {
                    "status": "sync_started",
                    "message": response.json().get("message", "Profile sync initiated"),
                    "profiles_synced": response.json().get("count", 0)
                }
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


@api_router.post("/documents/reindex")
async def reindex_documents(collection: Optional[str] = "corporate_rules"):
    """Reindex all documents in a collection"""
    try:
        url = f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}/api/v1/documents/reindex"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"collection": collection},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "reindex_started",
                    "message": result.get("message", "Reindex started"),
                    "collection": collection,
                    "documents_count": result.get("documents_count", 0)
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Core Engine service unavailable: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine: {e}")
        raise HTTPException(status_code=503, detail=f"Core Engine service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to reindex documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reindex documents: {str(e)}")


@api_router.get("/qdrant/collections")
async def get_qdrant_collections():
    """Get all collections from Qdrant (Module 1)"""
    try:
        # Use retriever service for Qdrant document endpoints
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/documents/collections"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get collections from Qdrant: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine (Qdrant): {e}")
        raise HTTPException(
            status_code=503,
            detail="Core Engine (Qdrant) service unavailable"
        )


@api_router.get("/qdrant/collections/{collection_name}/info")
async def get_qdrant_collection_info(collection_name: str):
    """Get information about a specific Qdrant collection"""
    try:
        # Use retriever service for Qdrant document endpoints
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/documents"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params={"collection": collection_name}, timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                documents = result.get("documents", [])
                return {
                    "collection": collection_name,
                    "count": len(documents),
                    "documents": documents[:10],  # Return first 10 for preview
                    "limit": 10
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get collection info from Qdrant: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine (Qdrant): {e}")
        raise HTTPException(
            status_code=503,
            detail="Core Engine (Qdrant) service unavailable"
        )


@api_router.get("/qdrant/profiles")
async def get_qdrant_profiles(limit: int = 10, offset: int = 0):
    """Get all profiles from Qdrant user_profiles collection"""
    try:
        # Use retriever service for Qdrant profiles
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/profiles"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params={"limit": limit, "offset": offset}, timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "collection": "user_profiles",
                    "count": result.get("count", 0),
                    "profiles": result.get("profiles", []),
                    "limit": limit,
                    "offset": offset
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get profiles from Qdrant: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine (Qdrant): {e}")
        raise HTTPException(
            status_code=503,
            detail="Core Engine (Qdrant) service unavailable"
        )


@api_router.get("/qdrant/rules")
async def get_qdrant_rules(limit: int = 10, offset: int = 0):
    """Get all rules from Qdrant corporate_rules collection"""
    try:
        # Use retriever service for Qdrant rules
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/rules"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, params={"limit": limit, "offset": offset}, timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "collection": "corporate_rules",
                    "count": result.get("count", 0),
                    "rules": result.get("rules", []),
                    "limit": limit,
                    "offset": offset
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get rules from Qdrant: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine (Qdrant): {e}")
        raise HTTPException(
            status_code=503,
            detail="Core Engine (Qdrant) service unavailable"
        )


@api_router.get("/qdrant/styles")
async def get_qdrant_styles():
    """Get all styles from Qdrant"""
    try:
        # Use retriever service for Qdrant styles
        url = f"http://{RETRIEVER_HTTP_HOST}:{RETRIEVER_HTTP_PORT}/api/v1/styles"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url, timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "collection": "styles",
                    "count": len(result.get("styles", [])),
                    "styles": result.get("styles", [])
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get styles from Qdrant: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Core Engine (Qdrant): {e}")
        raise HTTPException(
            status_code=503,
            detail="Core Engine (Qdrant) service unavailable"
        )

