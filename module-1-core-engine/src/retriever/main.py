# Retriever - HTTP сервер для RAG операций

import os
import sys
import uvicorn
from typing import Dict, List, Any, Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from common.logging import logger, log_error, log_info
from common.metrics import track_cache_ttl_hit, track_cache_ttl_miss
from common.langfuse_integration import (
    init_langfuse,
    log_generation,
)

from .qdrant_client import get_qdrant_client
from .embeddings import get_embedder
from .hybrid_search import get_searcher


# FastAPI app
app = FastAPI(
    title="Chameleon Retriever",
    description="Retriever service for RAG operations",
    version="1.0.0",
)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    checks: Dict[str, str]


# Global instances
_qdrant_client = None
_embedder = None
_searcher = None


def get_qdrant_instance():
    """Get Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = get_qdrant_client()
    return _qdrant_client


def get_embedder_instance():
    """Get embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


def get_searcher_instance():
    """Get searcher instance."""
    global _searcher
    if _searcher is None:
        _searcher = get_searcher()
    return _searcher


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    # Initialize Langfuse
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://langfuse-web:3000")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "local-key")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "local-secret")
    
    init_langfuse(
        public_key=langfuse_public_key,
        secret_key=langfuse_secret_key,
        host=langfuse_host,
    )
    
    log_info("Retriever HTTP server starting")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    checks = {"qdrant": "ok"}
    status = "healthy"
    
    # Check Qdrant
    try:
        qdrant = get_qdrant_instance()
        qdrant.client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {str(e)}"
        status = "degraded"
    
    # Check embedder
    try:
        embedder = get_embedder_instance()
        embedder_ok = await embedder.health_check()
        if embedder_ok:
            checks["embedder"] = "ok"
        else:
            checks["embedder"] = "unhealthy"
            status = "degraded"
    except Exception as e:
        checks["embedder"] = f"error: {str(e)}"
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        checks=checks
    )


@app.get("/api/v1/profiles/{user_id}")
async def get_profile(user_id: str):
    """Get user profile by user_id."""
    log_info("GetProfile request", user_id=user_id)
    
    qdrant = get_qdrant_instance()
    profile = qdrant.get_profile(user_id)
    
    if not profile:
        log_info("Profile not found", user_id=user_id)
        track_cache_ttl_miss(cache_type="profile")
        raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
    
    log_info("Profile found", user_id=user_id)
    track_cache_ttl_hit(cache_type="profile")
    
    return {"profile": profile}


@app.post("/api/v1/profiles/sync")
async def sync_profiles_with_core():
    """Sync profiles with Core Engine (Module 1) - internal endpoint for Module 2"""
    log_info("SyncProfiles request")
    
    try:
        # Get all profiles from Module 2 database
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "module-2-chat-frontend", "src", "backend")))
        
        from database import get_all_profiles, load_profiles_from_core_engine
        
        # Load profiles from Core Engine (Module 1)
        profiles = load_profiles_from_core_engine()
        
        log_info("Profiles synced", count=len(profiles))
        return {
            "status": "synced",
            "message": f"Synced {len(profiles)} profiles with Core Engine",
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to sync profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync profiles: {str(e)}")


@app.get("/api/v1/profiles")
async def list_profiles(limit: int = 100, offset: int = 0):
    """Get all profiles from user_profiles collection."""
    log_info("ListProfiles request")
    
    qdrant = get_qdrant_instance()
    
    try:
        # Get all points from user_profiles collection
        scroll_result = qdrant.client.scroll(
            collection_name="user_profiles",
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        
        profiles = []
        for point in scroll_result[0]:
            payload = point.payload
            # Apply mappings to convert string values to proper format
            profile = qdrant._map_profile(payload)
            profiles.append({
                "user_id": point.id,
                **profile
            })
        
        track_cache_ttl_hit(cache_type="profiles")
        return {
            "profiles": profiles,
            "count": len(profiles),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")


@app.post("/api/v1/profiles")
async def create_profile(profile_data: Dict[str, Any]):
    """Create a new profile in user_profiles collection."""
    log_info("CreateProfile request")
    
    # Validate required fields
    required_fields = ["user_id", "full_name"]
    for field in required_fields:
        if field not in profile_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    qdrant = get_qdrant_instance()
    
    try:
        import uuid as uuid_module
        
        user_id = profile_data["user_id"]
        
        # Check if user_id looks like a UUID
        is_uuid = (
            len(user_id) == 36
            and user_id.count("-") == 4
            and all(
                c in "0123456789abcdef" for c in user_id.replace("-", "")
            )
        )
        
        if is_uuid:
            point_id = user_id
        else:
            # Generate UUID5 from user_id string
            point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, user_id))
        
        # Convert communication_mode and honorific_type to numeric
        honorific_type_map = {
            "first_name": 1,
            "patronymic": 3,
            "last_name": 2,
            "title": 4,
        }
        
        communication_mode_map = {
            "informal": 2,
            "formal": 1,
            "neutral": 0,
            "technical": 3,
            "collaborative": 4,
        }
        
        # Prepare payload
        payload = {
            "full_name": profile_data.get("full_name", ""),
            "role": profile_data.get("role"),
            "department": profile_data.get("department"),
            "honorific_type": honorific_type_map.get(profile_data.get("honorific_type", "default"), 0),
            "communication_mode": communication_mode_map.get(profile_data.get("communication_mode", "neutral"), 0),
            "known_triggers": profile_data.get("known_triggers", []),
            "core_user_id": profile_data.get("core_user_id", user_id),
            "created_at": int(profile_data.get("created_at", 0)),
            "updated_at": int(profile_data.get("updated_at", 0))
        }
        
        # Generate embedding for profile
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        profile_text = f"{payload.get('full_name', '')} {payload.get('role', '')} {payload.get('department', '')}"
        embedding = await embedder.generate_embedding(profile_text)
        
        # Upsert the profile
        qdrant.client.upsert(
            collection_name="user_profiles",
            points=[
                {
                    "id": point_id,
                    "vector": embedding,
                    "payload": payload
                }
            ]
        )
        
        log_info("Profile created", user_id=user_id, point_id=point_id)
        return {
            "status": "created",
            "profile": {
                "user_id": user_id,
                **payload
            }
        }
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")


@app.put("/api/v1/profiles/{user_id}")
async def update_profile(user_id: str, profile_data: Dict[str, Any]):
    """Update an existing profile in user_profiles collection."""
    log_info("UpdateProfile request", user_id=user_id)
    
    qdrant = get_qdrant_instance()
    
    try:
        # Check if user_id looks like a UUID
        is_uuid = (
            len(user_id) == 36
            and user_id.count("-") == 4
            and all(
                c in "0123456789abcdef" for c in user_id.replace("-", "")
            )
        )
        
        if is_uuid:
            point_id = user_id
        else:
            # Generate UUID5 from user_id string
            import uuid as uuid_module
            point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, user_id))
        
        # Get existing profile
        result = qdrant.client.retrieve(
            collection_name="user_profiles",
            ids=[point_id]
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
        
        existing_payload = result[0].payload
        
        # Update with new values
        honorific_type_map = {
            "first_name": 1,
            "patronymic": 3,
            "last_name": 2,
            "title": 4,
        }
        
        communication_mode_map = {
            "informal": 2,
            "formal": 1,
            "neutral": 0,
            "technical": 3,
            "collaborative": 4,
        }
        
        for key, value in profile_data.items():
            if key not in ["user_id", "core_user_id"]:
                if key == "honorific_type":
                    existing_payload[key] = honorific_type_map.get(value, 0)
                elif key == "communication_mode":
                    existing_payload[key] = communication_mode_map.get(value, 0)
                else:
                    existing_payload[key] = value
        
        existing_payload["updated_at"] = int(profile_data.get("updated_at", 0))
        
        # Generate new embedding if profile text changed
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        profile_text = f"{existing_payload.get('full_name', '')} {existing_payload.get('role', '')} {existing_payload.get('department', '')}"
        embedding = await embedder.generate_embedding(profile_text)
        
        # Update the profile
        qdrant.client.upsert(
            collection_name="user_profiles",
            points=[
                {
                    "id": point_id,
                    "vector": embedding,
                    "payload": existing_payload
                }
            ]
        )
        
        log_info("Profile updated", user_id=user_id, point_id=point_id)
        return {
            "status": "updated",
            "profile": {
                "user_id": user_id,
                **existing_payload
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@app.delete("/api/v1/profiles/{user_id}")
async def delete_profile(user_id: str):
    """Delete a profile from user_profiles collection."""
    log_info("DeleteProfile request", user_id=user_id)
    
    qdrant = get_qdrant_instance()
    
    try:
        # Check if user_id looks like a UUID
        is_uuid = (
            len(user_id) == 36
            and user_id.count("-") == 4
            and all(
                c in "0123456789abcdef" for c in user_id.replace("-", "")
            )
        )
        
        if is_uuid:
            point_id = user_id
        else:
            # Generate UUID5 from user_id string
            import uuid as uuid_module
            point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, user_id))
        
        # Check if profile exists
        result = qdrant.client.retrieve(
            collection_name="user_profiles",
            ids=[point_id]
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")
        
        # Delete the profile
        qdrant.client.delete(
            collection_name="user_profiles",
            points_selector=[point_id]
        )
        
        log_info("Profile deleted", user_id=user_id, point_id=point_id)
        return {
            "status": "deleted",
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")


@app.get("/api/v1/rules")
async def get_rules(
    sender_role: str = "user",
    recipient_role: str = "",
    text: str = "",
    limit: int = 5
):
    """Get corporate rules by sender and recipient roles."""
    log_info("GetRules request", sender_role=sender_role, recipient_role=recipient_role)
    
    qdrant = get_qdrant_instance()
    rules = await qdrant.get_rules(
        sender_role=sender_role,
        recipient_role=recipient_role,
        limit=limit,
    )
    track_cache_ttl_hit(cache_type="rules")
    
    return {"rules": rules}


@app.get("/api/v1/styles/examples")
async def get_style_examples(
    style_name: str,
    sample_count: int = 3
):
    """Get examples of artistic styles."""
    log_info("GetStyleExamples request", style_name=style_name)
    
    qdrant = get_qdrant_instance()
    styles = qdrant.get_style_examples(style_name=style_name, sample_count=sample_count)
    track_cache_ttl_hit(cache_type="style_examples")
    
    return {"examples": styles}


@app.get("/api/v1/rules/search")
async def search_rules(
    query_text: str,
    sender_role: str = "user",
    recipient_role: str = "",
    limit: int = 5
):
    """Search rules by query text."""
    log_info("SearchRules request", query_text=query_text[:50])
    
    qdrant = get_qdrant_instance()
    embedder = get_embedder_instance()
    
    # Generate embedding for query
    query_vector = await embedder.generate_embedding(query_text)
    if not query_vector:
        raise HTTPException(status_code=400, detail="Failed to generate embedding")
    
    rules = qdrant.search_rules(
        query_vector=query_vector,
        sender_role=sender_role,
        recipient_role=recipient_role,
        limit=limit,
    )
    track_cache_ttl_hit(cache_type="rules")
    
    return {"rules": rules}


@app.get("/api/v1/culture/search")
async def search_culture(
    query: str,
    limit: int = 3,
    category: Optional[str] = None
):
    """Search for culture chunks by query text."""
    log_info("SearchCulture request", query=query[:50], category=category)
    
    qdrant = get_qdrant_instance()
    chunks = await qdrant.get_culture_chunks(query_text=query, limit=limit, filter_category=category)
    track_cache_ttl_hit(cache_type="culture_chunks")
    
    return {"chunks": chunks}


@app.get("/api/v1/styles")
async def get_styles():
    """Get all styles."""
    qdrant = get_qdrant_instance()
    styles = await qdrant.get_styles()
    
    return {"styles": styles}


@app.get("/api/v1/rules")
async def list_rules(sender_role: str = "user", recipient_role: str = "", limit: int = 100, offset: int = 0):
    """Get all rules from corporate_rules collection."""
    log_info("ListRules request", sender_role=sender_role, recipient_role=recipient_role)
    
    qdrant = get_qdrant_instance()
    
    try:
        # Get all points from corporate_rules collection
        scroll_result = qdrant.client.scroll(
            collection_name="corporate_rules",
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        
        rules = []
        for point in scroll_result[0]:
            payload = point.payload
            # Map transformation to transformation_prompt for compatibility
            rule = {
                "rule_id": point.id,
                **payload
            }
            if "transformation" in rule and "transformation_prompt" not in rule:
                rule["transformation_prompt"] = rule["transformation"]
            rules.append(rule)
        
        return {
            "rules": rules,
            "count": len(rules),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list rules: {str(e)}")


@app.post("/api/v1/rules")
async def create_rule(rule_data: Dict[str, Any]):
    """Create a new rule in corporate_rules collection."""
    log_info("CreateRule request")
    
    # Validate required fields
    required_fields = ["name", "description", "category"]
    for field in required_fields:
        if field not in rule_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    qdrant = get_qdrant_instance()
    
    try:
        import uuid as uuid_module
        
        rule_id = rule_data.get("rule_id") or str(uuid_module.uuid4())
        
        # Prepare payload
        payload = {
            "name": rule_data.get("name", ""),
            "description": rule_data.get("description", ""),
            "category": rule_data.get("category", ""),
            "priority": rule_data.get("priority", 5),
            "condition": rule_data.get("condition", ""),
            "action": rule_data.get("action", ""),
            "transformation": rule_data.get("transformation", rule_data.get("transformation_prompt", "")),
            "transformation_prompt": rule_data.get("transformation_prompt", rule_data.get("transformation", "")),
            "example_original": rule_data.get("example_original", ""),
            "example_adapted": rule_data.get("example_adapted", ""),
            "role_from": rule_data.get("role_from", ""),
            "role_to": rule_data.get("role_to", ""),
            "is_active": rule_data.get("is_active", True),
            "created_at": int(rule_data.get("created_at", 0)),
            "updated_at": int(rule_data.get("updated_at", 0))
        }
        
        # Generate embedding for rule
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        rule_text = f"{payload.get('name', '')} {payload.get('description', '')} {payload.get('category', '')} {payload.get('condition', '')}"
        embedding = await embedder.generate_embedding(rule_text)
        
        # Upsert the rule
        qdrant.client.upsert(
            collection_name="corporate_rules",
            points=[
                {
                    "id": rule_id,
                    "vector": embedding,
                    "payload": payload
                }
            ]
        )
        
        log_info("Rule created", rule_id=rule_id)
        return {
            "status": "created",
            "rule": {
                "rule_id": rule_id,
                **payload
            }
        }
    except Exception as e:
        logger.error(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")


@app.put("/api/v1/rules/{rule_id}")
async def update_rule(rule_id: str, rule_data: Dict[str, Any]):
    """Update an existing rule in corporate_rules collection."""
    log_info("UpdateRule request", rule_id=rule_id)
    
    qdrant = get_qdrant_instance()
    
    try:
        # Get existing rule
        result = qdrant.client.retrieve(
            collection_name="corporate_rules",
            ids=[rule_id]
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
        
        existing_payload = result[0].payload
        
        # Update with new values
        for key, value in rule_data.items():
            if key != "rule_id":
                if key == "transformation" and "transformation_prompt" not in rule_data:
                    existing_payload["transformation_prompt"] = value
                existing_payload[key] = value
        
        existing_payload["updated_at"] = int(rule_data.get("updated_at", 0))
        
        # Generate new embedding if rule text changed
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        rule_text = f"{existing_payload.get('name', '')} {existing_payload.get('description', '')} {existing_payload.get('category', '')} {existing_payload.get('condition', '')}"
        embedding = await embedder.generate_embedding(rule_text)
        
        # Update the rule
        qdrant.client.upsert(
            collection_name="corporate_rules",
            points=[
                {
                    "id": rule_id,
                    "vector": embedding,
                    "payload": existing_payload
                }
            ]
        )
        
        log_info("Rule updated", rule_id=rule_id)
        return {
            "status": "updated",
            "rule": {
                "rule_id": rule_id,
                **existing_payload
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update rule: {str(e)}")


@app.delete("/api/v1/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete a rule from corporate_rules collection."""
    log_info("DeleteRule request", rule_id=rule_id)
    
    qdrant = get_qdrant_instance()
    
    try:
        # Check if rule exists
        result = qdrant.client.retrieve(
            collection_name="corporate_rules",
            ids=[rule_id]
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
        
        # Delete the rule
        qdrant.client.delete(
            collection_name="corporate_rules",
            points_selector=[rule_id]
        )
        
        log_info("Rule deleted", rule_id=rule_id)
        return {
            "status": "deleted",
            "rule_id": rule_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete rule: {str(e)}")


@app.post("/api/v1/styles")
async def create_style(style_data: Dict[str, Any]):
    """Create a new style."""
    qdrant = get_qdrant_instance()
    result = await qdrant.create_style(style_data)
    
    return {"style": result}


@app.put("/api/v1/styles/{style_id}")
async def update_style(style_id: str, style_data: Dict[str, Any]):
    """Update an existing style."""
    qdrant = get_qdrant_instance()
    
    try:
        result = await qdrant.update_style(style_id, style_data)
        return {"style": result}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/styles/{style_id}")
async def delete_style(style_id: str):
    """Delete a style."""
    qdrant = get_qdrant_instance()
    
    try:
        success = await qdrant.delete_style(style_id)
        return {"success": success}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/styles/{style_id}")
async def get_style(style_id: str):
    """Get a specific style by ID."""
    qdrant = get_qdrant_instance()
    
    try:
        result = await qdrant.get_style(style_id)
        return {"style": result}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rules/reload")
async def reload_rules():
    """Reload rules from data source."""
    qdrant = get_qdrant_instance()
    result = await qdrant.reload_rules()
    
    return result


@app.post("/api/v1/styles/reload")
async def reload_styles():
    """Reload styles from data source."""
    qdrant = get_qdrant_instance()
    result = await qdrant.reload_styles()
    
    return result


@app.post("/api/v1/documents/reindex")
async def reindex_documents(collection: str = "corporate_rules"):
    """Reindex all documents in a collection."""
    qdrant = get_qdrant_instance()
    result = await qdrant.reindex_collection(collection)
    
    return result


@app.post("/api/v1/documents/upload")
async def upload_document(
    collection: str = "corporate_rules"
):
    """Upload a document to Qdrant collection."""
    from fastapi import File, UploadFile, Form
    
    try:
        qdrant = get_qdrant_instance()
        
        # For now, return a placeholder since we can't use UploadFile in function signature
        # In a real implementation, this would handle multipart file upload
        return {
            "status": "success",
            "message": "Document upload endpoint ready",
            "collection": collection
        }
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.get("/api/v1/documents/collections")
async def list_collections():
    """List all available collections."""
    try:
        qdrant = get_qdrant_instance()
        collections = qdrant.client.get_collections()
        
        return {
            "collections": [
                {"name": c.name, "description": f"Collection {c.name}"}
                for c in collections.collections
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@app.get("/api/v1/documents")
async def list_documents(collection: str = "corporate_rules"):
    """List all documents in a collection."""
    try:
        qdrant = get_qdrant_instance()
        
        scroll_result = qdrant.client.scroll(
            collection_name=collection,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        
        documents = []
        for point in scroll_result[0]:
            payload = point.payload
            documents.append({
                "document_id": point.id,
                "filename": payload.get("source", "unknown"),
                "file_type": payload.get("file_type", "text"),
                "file_size": payload.get("original_size", 0),
                "status": payload.get("status", "indexed"),
                "chunk_index": payload.get("chunk_index", 0),
                "created_at": payload.get("created_at", 0)
            })
        
        return {
            "documents": documents,
            "count": len(documents),
            "collection": collection
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str, collection: str = "corporate_rules"):
    """Get a document by ID."""
    try:
        qdrant = get_qdrant_instance()
        
        result = qdrant.client.retrieve(
            collection_name=collection,
            ids=[document_id]
        )
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        payload = result[0].payload
        return {
            "document_id": document_id,
            "data": payload,
            "collection": collection
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str, collection: str = "corporate_rules"):
    """Delete a document by ID."""
    try:
        qdrant = get_qdrant_instance()
        
        qdrant.client.delete(
            collection_name=collection,
            points_selector=[document_id]
        )
        
        return {
            "status": "deleted",
            "document_id": document_id
        }
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@app.get("/api/v1/health", response_model=HealthResponse)
async def api_health_check():
    """API health check endpoint."""
    return await health_check()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    log_info(f"Starting Retriever HTTP server on port {port}")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
