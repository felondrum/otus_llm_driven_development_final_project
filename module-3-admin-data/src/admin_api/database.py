# ===========================================
# Database module for Module 3 Admin API
# ===========================================

import asyncpg
import json
import uuid
import random
import logging
from typing import Optional, List, Dict, Any
import os

# Import configuration with defaults
try:
    from config import (
        CORE_ENGINE_HTTP_HOST,
        CORE_ENGINE_HTTP_PORT,
        RETRIEVER_HTTP_HOST,
        RETRIEVER_HTTP_PORT,
        QDRANT_HOST,
        QDRANT_PORT,
    )
except ImportError:
    # Use defaults for testing
    CORE_ENGINE_HTTP_HOST = os.getenv("CORE_ENGINE_HTTP_HOST", "localhost")
    CORE_ENGINE_HTTP_PORT = int(os.getenv("CORE_ENGINE_HTTP_PORT", "8001"))
    RETRIEVER_HTTP_HOST = os.getenv("RETRIEVER_HTTP_HOST", "localhost")
    RETRIEVER_HTTP_PORT = int(os.getenv("RETRIEVER_HTTP_PORT", "8002"))
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chameleon:chameleon123@localhost:5433/chameleon_admin")

_pool: Optional[asyncpg.Pool] = None
logger = logging.getLogger(__name__)


async def get_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def close_pool():
    """Close database connection pool"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ===========================================
# Profiles CRUD operations
# ===========================================

async def get_profiles() -> List[Dict]:
    """Get all profiles from database"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM profiles ORDER BY user_id")
        return [dict(row) for row in rows]


async def get_profile(user_id: str) -> Optional[Dict]:
    """Get a specific profile by user_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM profiles WHERE user_id = $1", user_id)
        return dict(row) if row else None


async def create_profile(data: Dict) -> Dict:
    """Create a new profile"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO profiles (user_id, full_name, role, department, honorific_type, communication_mode, known_triggers)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
            data.get("user_id"), data.get("full_name"), data.get("role"), data.get("department"),
            data.get("honorific_type"), data.get("communication_mode"), json.dumps(data.get("known_triggers")) if data.get("known_triggers") else None
        )
        return dict(row)


async def update_profile(user_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing profile"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE profiles SET full_name = $1, role = $2, department = $3, honorific_type = $4, 
               communication_mode = $5, known_triggers = $6, updated_at = CURRENT_TIMESTAMP
               WHERE user_id = $7 RETURNING *""",
            data.get("full_name"), data.get("role"), data.get("department"), data.get("honorific_type"),
            data.get("communication_mode"), json.dumps(data.get("known_triggers")) if data.get("known_triggers") is not None else None, user_id
        )
        return dict(row) if row else None


async def delete_profile(user_id: str) -> bool:
    """Delete a profile from PostgreSQL and Qdrant"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM profiles WHERE user_id = $1", user_id)
        if result == "DELETE 1":
            # Also delete from Qdrant
            await delete_profile_from_core(user_id)
            return True
        return False


async def delete_profile_from_core(user_id: str) -> bool:
    """Delete a profile from Qdrant"""
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Generate UUID5 from user_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id))
        
        client.delete(
            collection_name="user_profiles",
            points_selector=[point_id]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete profile {user_id} from Qdrant: {e}")
        return False


# ===========================================
# Rules CRUD operations
# ===========================================

async def get_rules() -> List[Dict]:
    """Get all rules from database"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM rules ORDER BY priority DESC, created_at DESC")
        return [dict(row) for row in rows]


async def get_rule(rule_id: str) -> Optional[Dict]:
    """Get a specific rule by rule_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM rules WHERE rule_id = $1", rule_id)
        return dict(row) if row else None


async def create_rule(data: Dict) -> Dict:
    """Create a new rule"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO rules (rule_id, name, description, category, role, priority, condition, action, example_original, example_adapted, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *""",
            data.get("rule_id"), data.get("name"), data.get("description"), data.get("category"),
            data.get("role"), data.get("priority"), data.get("condition"), data.get("action"),
            data.get("example_original"), data.get("example_adapted"), data.get("is_active", True)
        )
        return dict(row)


async def update_rule(rule_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing rule"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build dynamic query
        update_fields = []
        values = []
        
        if 'name' in data:
            update_fields.append("name = $" + str(len(values) + 1))
            values.append(data['name'])
        if 'description' in data:
            update_fields.append("description = $" + str(len(values) + 1))
            values.append(data['description'])
        if 'category' in data:
            update_fields.append("category = $" + str(len(values) + 1))
            values.append(data['category'])
        if 'role' in data:
            update_fields.append("role = $" + str(len(values) + 1))
            values.append(data['role'])
        if 'priority' in data:
            update_fields.append("priority = $" + str(len(values) + 1))
            values.append(data['priority'])
        if 'condition' in data:
            update_fields.append("condition = $" + str(len(values) + 1))
            values.append(data['condition'])
        if 'action' in data:
            update_fields.append("action = $" + str(len(values) + 1))
            values.append(data['action'])
        if 'example_original' in data:
            update_fields.append("example_original = $" + str(len(values) + 1))
            values.append(data['example_original'])
        if 'example_adapted' in data:
            update_fields.append("example_adapted = $" + str(len(values) + 1))
            values.append(data['example_adapted'])
        if 'is_active' in data:
            update_fields.append("is_active = $" + str(len(values) + 1))
            values.append(data['is_active'])
        
        if not update_fields:
            return None
            
        values.append(rule_id)
        
        query = "UPDATE rules SET " + ", ".join(update_fields) + ", updated_at = CURRENT_TIMESTAMP WHERE rule_id = $" + str(len(values)) + " RETURNING *"
        
        row = await conn.fetchrow(query, *values)
        return dict(row) if row else None


async def delete_rule(rule_id: str) -> bool:
    """Delete a rule from PostgreSQL and Qdrant"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM rules WHERE rule_id = $1", rule_id)
        if result == "DELETE 1":
            # Also delete from Qdrant
            await delete_rule_from_core(rule_id)
            return True
        return False


# ===========================================
# Styles CRUD operations
# ===========================================

async def get_styles() -> List[Dict]:
    """Get all styles from database"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM styles ORDER BY name")
        result = []
        for row in rows:
            d = dict(row)
            # Convert JSONB fields
            if d.get("examples"):
                d["examples"] = json.loads(d["examples"]) if isinstance(d["examples"], str) else d["examples"]
            result.append(d)
        return result


async def get_style(style_id: str) -> Optional[Dict]:
    """Get a specific style by style_id"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM styles WHERE style_id = $1", style_id)
        if row:
            d = dict(row)
            # Convert JSONB fields
            if d.get("examples"):
                d["examples"] = json.loads(d["examples"]) if isinstance(d["examples"], str) else d["examples"]
            return d
        return None


async def create_style(data: Dict) -> Dict:
    """Create a new style"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        examples_json = json.dumps(data.get("examples")) if data.get("examples") else None
        row = await conn.fetchrow(
            """INSERT INTO styles (style_id, name, description, category, tone, examples, is_active)
               VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *""",
            data.get("style_id"), data.get("name"), data.get("description"), data.get("category"),
            data.get("tone"), examples_json, data.get("is_active", True)
        )
        result = dict(row)
        # Convert JSONB fields
        if result.get("examples"):
            result["examples"] = json.loads(result["examples"]) if isinstance(result["examples"], str) else result["examples"]
        return result


async def update_style(style_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing style"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        examples_json = json.dumps(data.get("examples")) if data.get("examples") is not None else None
        row = await conn.fetchrow(
            """UPDATE styles SET name = $1, description = $2, category = $3, tone = $4, examples = $5, is_active = $6, updated_at = CURRENT_TIMESTAMP
               WHERE style_id = $7 RETURNING *""",
            data.get("name"), data.get("description"), data.get("category"), data.get("tone"),
            examples_json, data.get("is_active"), style_id
        )
        if row:
            result = dict(row)
            # Convert JSONB fields
            if result.get("examples"):
                result["examples"] = json.loads(result["examples"]) if isinstance(result["examples"], str) else result["examples"]
            return result
        return None


async def delete_style(style_id: str) -> bool:
    """Delete a style from PostgreSQL and Qdrant"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM styles WHERE style_id = $1", style_id)
        if result == "DELETE 1":
            # Also delete from Qdrant
            await delete_style_from_core(style_id)
            return True
        return False


# ===========================================
# Documents CRUD operations
# ===========================================

async def get_all_documents() -> List[Dict]:
    """Get all documents from all collections"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM documents ORDER BY created_at DESC")
        return [dict(row) for row in rows]


async def get_documents(collection: str = "corporate_rules") -> List[Dict]:
    """Get all documents in a collection"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM documents WHERE collection = $1 ORDER BY created_at DESC", collection)
        return [dict(row) for row in rows]


async def get_document(document_id: str) -> Optional[Dict]:
    """Get a specific document by document_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM documents WHERE document_id = $1", document_id)
        return dict(row) if row else None


async def create_document(data: Dict) -> Dict:
    """Create a new document"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO documents (document_id, filename, file_type, file_size, collection, content, status, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *""",
            data.get("document_id"), data.get("filename"), data.get("file_type"), data.get("file_size"),
            data.get("collection"), data.get("content"), data.get("status"), json.dumps(data.get("metadata")) if data.get("metadata") else None
        )
        return dict(row)


async def delete_document(document_id: str) -> bool:
    """Delete a document"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM documents WHERE document_id = $1", document_id)
        if result == "DELETE 1":
            # Also delete from Qdrant
            await delete_document_from_core(document_id)
            return True
        return False


async def delete_document_from_core(document_id: str) -> bool:
    """Delete a document from Qdrant"""
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Get document to find its collection
        document = await get_document(document_id)
        if not document:
            logger.warning(f"Document {document_id} not found in PostgreSQL, cannot determine collection")
            return False
        
        # Generate UUID5 from document_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, document_id))
        
        # Use document's collection
        collection_name = document.get("collection", "corporate_rules")
        
        client.delete(
            collection_name=collection_name,
            points_selector=[point_id]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete document {document_id} from Qdrant: {e}")
        return False


async def update_document(document_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing document (only updates provided fields)"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build dynamic query based on provided fields
        update_fields = []
        values = []
        
        if 'filename' in data:
            update_fields.append("filename = $" + str(len(values) + 1))
            values.append(data['filename'])
        if 'file_type' in data:
            update_fields.append("file_type = $" + str(len(values) + 1))
            values.append(data['file_type'])
        if 'file_size' in data:
            update_fields.append("file_size = $" + str(len(values) + 1))
            values.append(data['file_size'])
        if 'collection' in data:
            update_fields.append("collection = $" + str(len(values) + 1))
            values.append(data['collection'])
        if 'content' in data:
            update_fields.append("content = $" + str(len(values) + 1))
            values.append(data['content'])
        if 'status' in data:
            update_fields.append("status = $" + str(len(values) + 1))
            values.append(data['status'])
        if 'metadata' in data:
            update_fields.append("metadata = $" + str(len(values) + 1))
            values.append(json.dumps(data['metadata']) if data['metadata'] else None)
        
        if not update_fields:
            return None
            
        values.append(document_id)
        
        query = "UPDATE documents SET " + ", ".join(update_fields) + ", updated_at = CURRENT_TIMESTAMP " + " WHERE document_id = $" + str(len(values)) + " RETURNING *"
        
        row = await conn.fetchrow(query, *values)
        if row:
            d = dict(row)
            # Convert JSONB fields
            if d.get("metadata"):
                d["metadata"] = json.loads(d["metadata"]) if isinstance(d["metadata"], str) else d["metadata"]
            return d
        return None


# ===========================================
# Sync functions to Core Engine
# ===========================================

async def sync_profile_to_core(user_id: str) -> bool:
    """Sync a specific profile to Core Engine via HTTP"""
    import httpx
    
    profile = await get_profile(user_id)
    if not profile:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}/api/v1/profiles",
                json=profile,
                timeout=10.0
            )
            return response.status_code == 201
    except Exception as e:
        logger.error(f"Failed to sync profile {user_id}: {e}")
        return False


async def sync_all_profiles_to_core() -> int:
    """Sync all profiles from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    profiles = await get_profiles()
    success_count = 0
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        for profile in profiles:
            try:
                # Generate UUID5 from user_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, profile["user_id"]))
                
                # Generate vector (mock - in production would use actual embeddings)
                vector = [random.random() for _ in range(768)]
                
                # Convert JSONB fields to Python objects
                if profile.get("known_triggers"):
                    if isinstance(profile["known_triggers"], str):
                        profile["known_triggers"] = json.loads(profile["known_triggers"])
                
                client.upsert(
                    collection_name="user_profiles",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=profile
                    )]
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to sync profile {profile.get('user_id')}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
    
    return success_count


async def sync_rule_to_core(rule_id: str) -> bool:
    """Sync a specific rule from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    rule = await get_rule(rule_id)
    if not rule:
        return False
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Generate UUID5 from rule_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule["rule_id"]))
        
        # Generate text for embedding from condition + action + examples
        text_for_embedding = " ".join([
            rule.get("category", ""),
            rule.get("name", ""),
            rule.get("condition", ""),
            rule.get("action", ""),
            rule.get("example_original", ""),
            rule.get("example_adapted", ""),
        ])
        
        # Clean up text
        text_for_embedding = " ".join(text_for_embedding.split())
        
        # Import embedder from module 1
        import sys
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        sys.path.insert(0, os.path.join(base_dir, 'module-1-core-engine', 'src'))
        
        from retriever.embeddings import get_embedder
        
        # Generate embedding via Ollama
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        
        embedding = await embedder.generate_embedding(text_for_embedding)
        
        if not embedding:
            logger.warning(f"Failed to generate embedding for rule {rule_id}, using random vector")
            vector = [random.random() for _ in range(768)]
        else:
            vector = embedding
        
        # Build payload with all required fields for Qdrant
        payload = {
            "rule_id": rule["rule_id"],
            "category": rule.get("category", "general"),
            "role": rule.get("role", "system"),
            "priority": rule.get("priority", 50),
            "condition": rule.get("condition", ""),
            "name": rule.get("name", ""),
            "description": rule.get("description", ""),
            "action": rule.get("action", ""),
            "transformation": rule.get("action", ""),
            "transformation_prompt": rule.get("action", ""),
            "example_original": rule.get("example_original", ""),
            "example_adapted": rule.get("example_adapted", ""),
            "is_active": rule.get("is_active", True),
            "created_at": str(rule.get("created_at", "")),
            "updated_at": str(rule.get("updated_at", "")),
        }
        
        client.upsert(
            collection_name="corporate_rules",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        logger.info(f"Synced rule {rule_id} to Qdrant with embedding")
        return True
    except Exception as e:
        logger.error(f"Failed to sync rule {rule_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def delete_rule_from_core(rule_id: str) -> bool:
    """Delete a rule from Qdrant"""
    from qdrant_client import QdrantClient
    
    try:
        # Connect to Qdrant directly
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Generate UUID5 from rule_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule_id))
        
        client.delete(
            collection_name="corporate_rules",
            points_selector=[point_id]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete rule {rule_id} from Qdrant: {e}")
        return False


async def sync_style_to_core(style_id: str) -> bool:
    """Sync a specific style from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    style = await get_style(style_id)
    if not style:
        return False
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Generate UUID5 from style_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"]))
        
        # Generate vector (mock - in production would use actual embeddings)
        vector = [random.random() for _ in range(768)]
        
        # Convert JSONB fields
        if style.get("examples") and isinstance(style["examples"], str):
            style["examples"] = json.loads(style["examples"])
        
        client.upsert(
            collection_name="artistic_styles",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=style
            )]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to sync style {style_id}: {e}")
        return False


async def delete_style_from_core(style_id: str) -> bool:
    """Delete a style from Qdrant"""
    from qdrant_client import QdrantClient
    
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Generate UUID5 from style_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, style_id))
        
        client.delete(
            collection_name="artistic_styles",
            points_selector=[point_id]
        )
        return True
    except Exception as e:
        logger.error(f"Failed to delete style {style_id} from Qdrant: {e}")
        return False


async def sync_all_rules_to_core() -> int:
    """Sync all rules from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    rules = await get_rules()
    success_count = 0
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        for rule in rules:
            try:
                # Generate UUID5 from rule_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule["rule_id"]))
                
                # Generate vector (mock - in production would use actual embeddings)
                vector = [random.random() for _ in range(768)]
                
                client.upsert(
                    collection_name="corporate_rules",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=rule
                    )]
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to sync rule {rule.get('rule_id')}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
    
    return success_count


async def sync_all_styles_to_core() -> int:
    """Sync all styles from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    styles = await get_styles()
    success_count = 0
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        for style in styles:
            try:
                # Generate UUID5 from style_id for consistent point IDs
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"]))
                
                # Generate vector (mock - in production would use actual embeddings)
                vector = [random.random() for _ in range(768)]
                
                # Convert JSONB fields
                examples = []
                if style.get("examples") and isinstance(style["examples"], str):
                    examples = json.loads(style["examples"])
                elif style.get("examples") and isinstance(style["examples"], list):
                    examples = style["examples"]
                
                # Extract tone/emotion_tags
                tone = style.get("tone", "")
                emotion_tags = []
                if tone:
                    if isinstance(tone, str):
                        emotion_tags = [t.strip() for t in tone.split(",") if t.strip()]
                    elif isinstance(tone, list):
                        emotion_tags = tone
                
                # Build payload with all required fields for Qdrant
                payload = {
                    "style_id": style["style_id"],  # 'chekov', 'dovlatov', 'chekhov'
                    "style_name": style.get("name", ""),  # 'чеховский' (кириллица)
                    "author": "",  # Not in PostgreSQL, will be empty
                    "sample_text": "",  # Not in PostgreSQL, will be empty
                    "emotion_tags": emotion_tags,
                    "category": style.get("category", "literary"),
                    "tone": tone,
                    "description": style.get("description", ""),
                    "examples": examples,
                }
                
                # Extract sample_text and author from examples if available
                if examples and len(examples) > 0:
                    first_example = examples[0]
                    if isinstance(first_example, dict):
                        payload["sample_text"] = first_example.get("output", "")
                        note = first_example.get("note", "")
                        if note and "Author:" in note:
                            payload["author"] = note.replace("Author:", "").strip()
                
                client.upsert(
                    collection_name="artistic_styles",
                    points=[PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )]
                )
                success_count += 1
                print(f"  Synced style: {style['style_id']} -> style_name: {payload['style_name']}")
            except Exception as e:
                logger.error(f"Failed to sync style {style.get('style_id')}: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant: {e}")
        import traceback
        traceback.print_exc()
    
    return success_count


async def sync_document_to_core(document_id: str) -> bool:
    """Sync a specific document from PostgreSQL to Qdrant directly"""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    
    document = await get_document(document_id)
    if not document:
        return False
    
    try:
        # Connect to Qdrant directly
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        collection_name = document.get("collection", "corporate_rules")
        
        # Handle corporate_culture specially - chunk the document
        if collection_name == "corporate_culture":
            import uuid as uuid_module
            
            content = document.get("content", "")
            filename = document.get("filename", "document")
            
            # Simple chunking - split by sections
            chunks = []
            lines = content.split('\n')
            current_chunk = []
            current_length = 0
            
            for line in lines:
                line_length = len(line) + 1
                if current_length + line_length > 500 and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = [line]
                    current_length = line_length
                else:
                    current_chunk.append(line)
                    current_length += line_length
            
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            # Generate UUID for each chunk
            for i, chunk_text in enumerate(chunks):
                chunk_point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, f"{document_id}:{i}"))
                chunk_vector = [random.random() for _ in range(768)]
                
                # Extract section title from chunk
                first_line = chunk_text.split('\n')[0] if chunk_text else "culture"
                section_title = "culture"
                if first_line.startswith('#'):
                    section_title = first_line.replace('#', '').strip()
                
                client.upsert(
                    collection_name="corporate_culture",
                    points=[PointStruct(
                        id=chunk_point_id,
                        vector=chunk_vector,
                        payload={
                            "text": chunk_text,
                            "section_title": section_title,
                            "source": filename,
                            "type": "corporate_culture",
                            "chunk_index": i
                        }
                    )]
                )
            return True
        else:
            # For other collections, use simple upsert
            # Generate UUID5 from document_id for consistent point IDs
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, document["document_id"]))
            
            # Generate vector (mock - in production would use actual embeddings)
            vector = [random.random() for _ in range(768)]
            
            client.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=document
                )]
            )
            return True
    except Exception as e:
        logger.error(f"Failed to sync document {document_id}: {e}")
        return False


async def sync_all_documents_to_core() -> int:
    """Sync all documents from PostgreSQL to Qdrant directly"""
    documents = await get_all_documents()
    success_count = 0
    
    for document in documents:
        try:
            success = await sync_document_to_core(document["document_id"])
            if success:
                success_count += 1
        except Exception as e:
            logger.error(f"Failed to sync document {document.get('document_id')}: {e}")
    
    return success_count


# ===========================================
# Chat Profiles CRUD operations
# ===========================================

async def get_chat_profiles() -> List[Dict]:
    """Get all chat profiles from database"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM chat_profiles ORDER BY user_id")
        result = []
        for row in rows:
            d = dict(row)
            # Convert JSONB fields
            if d.get("known_triggers"):
                d["known_triggers"] = json.loads(d["known_triggers"])
            result.append(d)
        return result


async def get_chat_profile(user_id: str) -> Optional[Dict]:
    """Get a specific chat profile by user_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM chat_profiles WHERE user_id = $1", user_id)
        if row:
            d = dict(row)
            if d.get("known_triggers"):
                d["known_triggers"] = json.loads(d["known_triggers"])
            return d
        return None


async def create_chat_profile(data: Dict) -> Dict:
    """Create a new chat profile"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO chat_profiles (user_id, full_name, role, department, honorific_type, 
               communication_mode, known_triggers, core_user_id)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *""",
            data.get("user_id"), data.get("full_name"), data.get("role"), data.get("department"),
            data.get("honorific_type"), data.get("communication_mode"), 
            json.dumps(data.get("known_triggers")) if data.get("known_triggers") else None,
            data.get("core_user_id")
        )
        result = dict(row)
        if result.get("known_triggers"):
            result["known_triggers"] = json.loads(result["known_triggers"])
        return result


async def update_chat_profile(user_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing chat profile"""
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE chat_profiles SET full_name = $1, role = $2, department = $3, honorific_type = $4, 
               communication_mode = $5, known_triggers = $6, core_user_id = $7, last_updated = CURRENT_TIMESTAMP
               WHERE user_id = $8 RETURNING *""",
            data.get("full_name"), data.get("role"), data.get("department"), data.get("honorific_type"),
            data.get("communication_mode"), 
            json.dumps(data.get("known_triggers")) if data.get("known_triggers") is not None else None,
            data.get("core_user_id"), user_id
        )
        if row:
            result = dict(row)
            if result.get("known_triggers"):
                result["known_triggers"] = json.loads(result["known_triggers"])
            return result
        return None


async def delete_chat_profile(user_id: str) -> bool:
    """Delete a chat profile"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM chat_profiles WHERE user_id = $1", user_id)
        return result == "DELETE 1"


async def sync_chat_profile_to_core(user_id: str) -> bool:
    """Sync a specific chat profile to Core Engine via HTTP"""
    import httpx
    
    profile = await get_chat_profile(user_id)
    if not profile:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{CORE_ENGINE_HTTP_HOST}:{CORE_ENGINE_HTTP_PORT}/api/v1/chat/profiles",
                json=profile,
                timeout=10.0
            )
            return response.status_code == 201
    except Exception as e:
        print(f"Failed to sync chat profile {user_id}: {e}")
        return False


async def sync_all_chat_profiles_to_core() -> int:
    """Sync all chat profiles to Core Engine via HTTP"""
    profiles = await get_chat_profiles()
    success_count = 0
    
    for profile in profiles:
        if await sync_chat_profile_to_core(profile["user_id"]):
            success_count += 1
    
    return success_count
