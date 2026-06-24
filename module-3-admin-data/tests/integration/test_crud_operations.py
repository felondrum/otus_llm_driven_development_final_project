# ===========================================
# Integration tests for CRUD operations with PostgreSQL
# ===========================================

import os
import sys
import pytest
import asyncio
import asyncpg
from typing import Dict, Any, Optional
import uuid

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Configuration for PostgreSQL connection
DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://chameleon:chameleon123@localhost:5433/chameleon_admin")


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the tests"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def pg_pool():
    """Create a database connection pool for tests"""
    pool = await asyncpg.create_pool(DATABASE_URL)
    yield pool
    await pool.close()


@pytest.fixture(scope="module", autouse=True)
async def setup_database(pg_pool):
    """Setup test database with initial data"""
    async with pg_pool.acquire() as conn:
        # Clear existing test data
        await conn.execute("DELETE FROM profiles WHERE user_id LIKE 'test_%'")
        await conn.execute("DELETE FROM rules WHERE rule_id LIKE 'test_%'")
        await conn.execute("DELETE FROM styles WHERE style_id LIKE 'test_%'")
        await conn.execute("DELETE FROM documents WHERE document_id LIKE 'test_%'")
    
    yield
    
    # Cleanup after tests
    async with pg_pool.acquire() as conn:
        await conn.execute("DELETE FROM profiles WHERE user_id LIKE 'test_%'")
        await conn.execute("DELETE FROM rules WHERE rule_id LIKE 'test_%'")
        await conn.execute("DELETE FROM styles WHERE style_id LIKE 'test_%'")
        await conn.execute("DELETE FROM documents WHERE document_id LIKE 'test_%'")


@pytest.mark.asyncio
async def test_profiles_crud(pg_pool):
    """Test CRUD operations for profiles"""
    from admin_api.database import get_profiles, get_profile, create_profile, update_profile, delete_profile
    
    test_user_id = f"test_{uuid.uuid4().hex[:8]}"
    test_profile_data = {
        "user_id": test_user_id,
        "full_name": "Test User",
        "role": "tester",
        "department": "QA",
        "honorific_type": "first_name",
        "communication_mode": "informal",
        "known_triggers": ["test", "feedback"]
    }
    
    # CREATE
    created = await create_profile(test_profile_data)
    assert created["user_id"] == test_user_id
    assert created["full_name"] == "Test User"
    
    # READ (get all)
    profiles = await get_profiles()
    test_profile = next((p for p in profiles if p["user_id"] == test_user_id), None)
    assert test_profile is not None
    assert test_profile["full_name"] == "Test User"
    
    # READ (get by id)
    profile = await get_profile(test_user_id)
    assert profile is not None
    assert profile["full_name"] == "Test User"
    
    # UPDATE
    updated_data = {
        "full_name": "Updated Test User",
        "role": "senior_tester"
    }
    updated = await update_profile(test_user_id, updated_data)
    assert updated is not None
    assert updated["full_name"] == "Updated Test User"
    assert updated["role"] == "senior_tester"
    
    # Verify update
    profile = await get_profile(test_user_id)
    assert profile["full_name"] == "Updated Test User"
    
    # DELETE
    deleted = await delete_profile(test_user_id)
    assert deleted is True
    
    # Verify delete
    profile = await get_profile(test_user_id)
    assert profile is None


@pytest.mark.asyncio
async def test_rules_crud(pg_pool):
    """Test CRUD operations for rules"""
    from admin_api.database import get_rules, get_rule, create_rule, update_rule, delete_rule
    
    test_rule_id = f"test_{uuid.uuid4().hex[:8]}"
    test_rule_data = {
        "rule_id": test_rule_id,
        "name": "Test Rule",
        "description": "Test rule description",
        "category": "test",
        "role": "system",
        "priority": 5,
        "condition": "test_condition",
        "action": "test_action",
        "is_active": True
    }
    
    # CREATE
    created = await create_rule(test_rule_data)
    assert created["rule_id"] == test_rule_id
    assert created["name"] == "Test Rule"
    
    # READ (get all)
    rules = await get_rules()
    test_rule = next((r for r in rules if r["rule_id"] == test_rule_id), None)
    assert test_rule is not None
    assert test_rule["name"] == "Test Rule"
    
    # READ (get by id)
    rule = await get_rule(test_rule_id)
    assert rule is not None
    assert rule["name"] == "Test Rule"
    
    # UPDATE
    updated_data = {
        "name": "Updated Test Rule",
        "priority": 10
    }
    updated = await update_rule(test_rule_id, updated_data)
    assert updated is not None
    assert updated["name"] == "Updated Test Rule"
    assert updated["priority"] == 10
    
    # Verify update
    rule = await get_rule(test_rule_id)
    assert rule["name"] == "Updated Test Rule"
    
    # DELETE
    deleted = await delete_rule(test_rule_id)
    assert deleted is True
    
    # Verify delete
    rule = await get_rule(test_rule_id)
    assert rule is None


@pytest.mark.asyncio
async def test_styles_crud(pg_pool):
    """Test CRUD operations for styles"""
    from admin_api.database import get_styles, get_style, create_style, update_style, delete_style
    
    test_style_id = f"test_{uuid.uuid4().hex[:8]}"
    test_style_data = {
        "style_id": test_style_id,
        "name": "Test Style",
        "description": "Test style description",
        "category": "test",
        "tone": "neutral",
        "examples": [
            {
                "input": "Test input",
                "output": "Test output",
                "note": "Test note"
            }
        ],
        "is_active": True
    }
    
    # CREATE
    created = await create_style(test_style_data)
    assert created["style_id"] == test_style_id
    assert created["name"] == "Test Style"
    
    # READ (get all)
    styles = await get_styles()
    test_style = next((s for s in styles if s["style_id"] == test_style_id), None)
    assert test_style is not None
    assert test_style["name"] == "Test Style"
    
    # READ (get by id)
    style = await get_style(test_style_id)
    assert style is not None
    assert style["name"] == "Test Style"
    
    # UPDATE
    updated_data = {
        "name": "Updated Test Style",
        "tone": "enthusiastic"
    }
    updated = await update_style(test_style_id, updated_data)
    assert updated is not None
    assert updated["name"] == "Updated Test Style"
    assert updated["tone"] == "enthusiastic"
    
    # Verify update
    style = await get_style(test_style_id)
    assert style["name"] == "Updated Test Style"
    
    # DELETE
    deleted = await delete_style(test_style_id)
    assert deleted is True
    
    # Verify delete
    style = await get_style(test_style_id)
    assert style is None


@pytest.mark.asyncio
async def test_documents_crud(pg_pool):
    """Test CRUD operations for documents"""
    from admin_api.database import get_documents, get_document, create_document, delete_document
    
    test_document_id = f"test_{uuid.uuid4().hex[:8]}"
    test_document_data = {
        "document_id": test_document_id,
        "filename": "test_document.md",
        "file_type": "text/markdown",
        "file_size": 1024,
        "collection": "test_collection",
        "content": "# Test Document\n\nThis is a test document.",
        "status": "uploaded",
        "metadata": {"author": "test_user"}
    }
    
    # CREATE
    created = await create_document(test_document_data)
    assert created["document_id"] == test_document_id
    assert created["filename"] == "test_document.md"
    
    # READ (get all)
    documents = await get_documents(collection="test_collection")
    test_doc = next((d for d in documents if d["document_id"] == test_document_id), None)
    assert test_doc is not None
    assert test_doc["filename"] == "test_document.md"
    
    # READ (get by id)
    document = await get_document(test_document_id)
    assert document is not None
    assert document["filename"] == "test_document.md"
    
    # DELETE
    deleted = await delete_document(test_document_id)
    assert deleted is True
    
    # Verify delete
    document = await get_document(test_document_id)
    assert document is None


@pytest.mark.asyncio
async def test_chat_profiles_crud(pg_pool):
    """Test CRUD operations for chat profiles"""
    from admin_api.database import get_chat_profiles, get_chat_profile, create_chat_profile, update_chat_profile, delete_chat_profile
    
    test_user_id = f"test_{uuid.uuid4().hex[:8]}"
    test_profile_data = {
        "user_id": test_user_id,
        "full_name": "Test Chat User",
        "role": "chat_user",
        "department": "test_dept",
        "honorific_type": "first_name",
        "communication_mode": "informal",
        "known_triggers": ["test", "feedback"],
        "core_user_id": "alex_i"  # Reference to profiles table
    }
    
    # CREATE
    created = await create_chat_profile(test_profile_data)
    assert created["user_id"] == test_user_id
    assert created["full_name"] == "Test Chat User"
    assert created["core_user_id"] == "alex_i"
    
    # READ (get all)
    profiles = await get_chat_profiles()
    test_profile = next((p for p in profiles if p["user_id"] == test_user_id), None)
    assert test_profile is not None
    assert test_profile["full_name"] == "Test Chat User"
    
    # READ (get by id)
    profile = await get_chat_profile(test_user_id)
    assert profile is not None
    assert profile["full_name"] == "Test Chat User"
    
    # UPDATE
    updated_data = {
        "full_name": "Updated Chat User",
        "role": "senior_chat_user"
    }
    updated = await update_chat_profile(test_user_id, updated_data)
    assert updated is not None
    assert updated["full_name"] == "Updated Chat User"
    assert updated["role"] == "senior_chat_user"
    
    # Verify update
    profile = await get_chat_profile(test_user_id)
    assert profile["full_name"] == "Updated Chat User"
    
    # DELETE
    deleted = await delete_chat_profile(test_user_id)
    assert deleted is True
    
    # Verify delete
    profile = await get_chat_profile(test_user_id)
    assert profile is None


@pytest.mark.asyncio
async def test_database_pool_management(pg_pool):
    """Test database pool creation and closing"""
    from admin_api.database import get_pool, close_pool
    
    # Pool should already be created by fixture (pg_pool)
    pool = await get_pool()
    assert pool is not None
    
    # close_pool() closes the module-level pool
    await close_pool()
    
    # Create new pool after closing (should create fresh pool)
    new_pool = await get_pool()
    assert new_pool is not None
    
    # Verify the new pool is functional
    async with new_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1
    
    # Cleanup
    await close_pool()


@pytest.mark.asyncio
async def test_sync_functions(pg_pool):
    """Test sync functions (without actual Core Engine connection)"""
    from admin_api.database import sync_profile_to_core, sync_rule_to_core, sync_style_to_core
    
    # Test with non-existent data (should return False)
    result = await sync_profile_to_core("nonexistent_user")
    assert result is False
    
    result = await sync_rule_to_core("nonexistent_rule")
    assert result is False
    
    result = await sync_style_to_core("nonexistent_style")
    assert result is False


@pytest.mark.asyncio
async def test_sync_chat_functions(pg_pool):
    """Test sync functions for chat profiles (without actual Core Engine connection)"""
    from admin_api.database import sync_chat_profile_to_core, sync_all_chat_profiles_to_core
    
    # Test with non-existent data (should return False)
    result = await sync_chat_profile_to_core("nonexistent_user")
    assert result is False
    
    # Test sync all (should return 0)
    count = await sync_all_chat_profiles_to_core()
    assert count == 0
