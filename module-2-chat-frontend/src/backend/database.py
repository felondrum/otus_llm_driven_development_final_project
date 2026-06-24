# ===========================================
# SQLite Database for Chat Frontend
# Stores user profiles synchronized with Core Engine
# ===========================================

import sqlite3
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.environ.get("CHAT_DB_PATH", "/app/backend/chat_profiles.db")

# Core Engine HTTP client
try:
    from http_client.orchestrator_client import get_profile_sync
    logger.info("Successfully imported sync HTTP client for Core Engine")
    HTTP_ENABLED = True
except ImportError as e:
    logger.warning(f"Could not import HTTP client: {e}. Using fallback mode.")
    HTTP_ENABLED = False
    get_profile_sync = None

# Also try to import process_message_sync (used in websocket)
try:
    from http_client.orchestrator_client import process_message_sync
    logger.info("Successfully imported process_message_sync from HTTP client")
    HTTP_PROCESS_ENABLED = True
except ImportError:
    logger.warning("Could not import process_message_sync from HTTP client")
    process_message_sync = None

# Module 3 Admin API connection (PostgreSQL)
# Try importing requests first (for synchronous HTTP calls)
try:
    import requests
    MODULE3_HTTP_ENABLED = True
    logger.info("Successfully imported requests for Module 3")
except ImportError:
    logger.warning("Could not import requests for Module 3")
    MODULE3_HTTP_ENABLED = False

# Also try httpx for async operations
try:
    import httpx
    MODULE3_HTTPX_ENABLED = True
except ImportError:
    logger.warning("Could not import httpx for Module 3")
    MODULE3_HTTPX_ENABLED = False

MODULE3_HOST = os.environ.get("MODULE3_HOST", "127.0.0.1")
MODULE3_PORT = os.environ.get("MODULE3_PORT", "8200")


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_profiles_from_module3_sync() -> List[Dict]:
    """Load profiles from Module 3 PostgreSQL via HTTP (synchronous)"""
    if not MODULE3_HTTP_ENABLED:
        logger.warning("Module 3 HTTP client not available")
        return []
    
    profiles = []
    
    try:
        response = requests.get(
            f"http://{MODULE3_HOST}:{MODULE3_PORT}/api/v1/admin/chat_profiles",
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            profiles = data.get("chat_profiles", [])
            logger.info(f"Loaded {len(profiles)} profiles from Module 3 PostgreSQL")
        else:
            logger.warning(f"Failed to load profiles from Module 3: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Failed to connect to Module 3: {e}")
    except Exception as e:
        logger.error(f"Error loading profiles from Module 3: {e}")
    
    return profiles


async def init_database_and_load_profiles():
    """Initialize database and load profiles from Module 3 PostgreSQL"""
    # Initialize SQLite (for backward compatibility and caching)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            role TEXT,
            department TEXT,
            honorific_type TEXT,
            communication_mode TEXT,
            known_triggers TEXT,
            core_user_id TEXT,
            last_updated TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")
    
    # Try to load profiles from Module 3 PostgreSQL
    profiles = load_profiles_from_module3_sync()
    
    if not profiles:
        logger.info("No profiles from Module 3, using test profiles")
        profiles = get_test_profiles()
        for profile in profiles:
            insert_profile(profile)
    else:
        # Clear existing profiles and insert from Module 3
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles")
        conn.commit()
        conn.close()
        
        for profile in profiles:
            insert_profile(profile)
        logger.info(f"Loaded {len(profiles)} profiles from Module 3")
    
    return profiles


def load_profiles_from_core_engine():
    """Load profiles from Core Engine via HTTP (synchronous)"""
    if not HTTP_ENABLED or get_profile_sync is None:
        logger.warning("HTTP client not available, cannot load profiles from Core Engine")
        return []
    
    profiles = []
    
    # Get all users from Core Engine
    # We'll use the demo data user_ids from profiles.json
    demo_user_ids = [
        "alex_i", "petr_s", "anna_k", "maria_s", 
        "dmitry_k", "elena_v", "sergey_m", "olga_a"
    ]
    
    for user_id in demo_user_ids:
        try:
            profile = get_profile_sync(user_id)
            if profile:
                profiles.append(profile)
                logger.info(f"Loaded profile for {user_id} from Core Engine")
        except Exception as e:
            logger.error(f"Failed to load profile for {user_id}: {e}")
    
    return profiles


def insert_profile(profile: Dict):
    """Insert or update a profile"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert known_triggers to JSON string
    known_triggers_str = json.dumps(profile.get("known_triggers", []))
    
    cursor.execute('''
        INSERT OR REPLACE INTO profiles 
        (user_id, full_name, role, department, honorific_type, 
         communication_mode, known_triggers, core_user_id, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        profile["user_id"],
        profile["full_name"],
        profile.get("role"),
        profile.get("department"),
        profile.get("honorific_type"),
        profile.get("communication_mode"),
        known_triggers_str,
        profile.get("core_user_id"),
        datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"Profile inserted/updated: {profile['user_id']}")


def get_all_profiles() -> List[Dict]:
    """Get all profiles from PostgreSQL (Module 3) directly without caching"""
    # Try to load from PostgreSQL Module 3 directly
    if MODULE3_HTTP_ENABLED:
        try:
            profiles = load_profiles_from_module3_sync()
            
            if profiles:
                logger.info(f"Loaded {len(profiles)} profiles directly from Module 3 PostgreSQL")
                return profiles
        except Exception as e:
            logger.error(f"Failed to load profiles from Module 3 directly: {e}")
    
    # Fallback to test profiles
    return get_test_profiles()


def get_profile_by_user_id(user_id: str) -> Optional[Dict]:
    """Get a profile by user_id from PostgreSQL (Module 3) directly without caching"""
    # Try to load from PostgreSQL Module 3 directly
    if MODULE3_HTTP_ENABLED:
        try:
            profiles = load_profiles_from_module3_sync()
            
            # Find the requested profile
            for profile in profiles:
                if profile.get("user_id") == user_id:
                    return profile
        except Exception as e:
            logger.error(f"Failed to load profiles from Module 3 directly: {e}")
    
    # Fallback to test profiles
    for profile in get_test_profiles():
        if profile.get("user_id") == user_id:
            return profile
    
    return None


def delete_profile(user_id: str):
    """Delete a profile by user_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    logger.info(f"Profile deleted: {user_id}")


def sync_with_core_engine():
    """Sync profiles with Core Engine (synchronous)"""
    if not HTTP_ENABLED or get_profile_sync is None:
        logger.warning("HTTP client not available, cannot sync with Core Engine")
        return False
    
    try:
        # Load profiles from Core Engine (synchronous)
        profiles = load_profiles_from_core_engine()
        
        # Clear existing profiles
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM profiles")
        conn.commit()
        conn.close()
        
        # Insert new profiles
        for profile in profiles:
            insert_profile(profile)
        
        logger.info(f"Synced {len(profiles)} profiles with Core Engine")
        return True
    except Exception as e:
        logger.error(f"Failed to sync with Core Engine: {e}")
        return False


async def sync_with_core_engine_async():
    """Async version of sync_with_core_engine for use in async contexts"""
    return sync_with_core_engine()


def get_test_profiles() -> List[Dict]:
    """Get test profiles as fallback when Core Engine is not available"""
    return [
        {
            "user_id": "alex_i",
            "full_name": "Иванов Алексей Петрович",
            "role": "engineer",
            "department": "backend",
            "honorific_type": "first_name",
            "communication_mode": "informal",
            "known_triggers": ["deadline", "bug", "code_review"],
            "core_user_id": "alex_i"
        },
        {
            "user_id": "petr_s",
            "full_name": "Смирнов Петр Иванович",
            "role": "team_lead",
            "department": "backend",
            "honorific_type": "patronymic",
            "communication_mode": "formal",
            "known_triggers": ["blame", "deadline"],
            "core_user_id": "petr_s"
        },
        {
            "user_id": "anna_k",
            "full_name": "Ковалева Анна Сергеевна",
            "role": "director",
            "department": "engineering",
            "honorific_type": "patronymic",
            "communication_mode": "formal",
            "known_triggers": ["money", "deadline", "blame"],
            "core_user_id": "anna_k"
        },
        {
            "user_id": "maria_s",
            "full_name": "Смирнова Мария Дмитриевна",
            "role": "hr_manager",
            "department": "hr",
            "honorific_type": "patronymic",
            "communication_mode": "formal",
            "known_triggers": ["salary", "vacation", "review"],
            "core_user_id": "maria_s"
        },
        {
            "user_id": "dmitry_k",
            "full_name": "Кузнецов Дмитрий Александрович",
            "role": "senior_engineer",
            "department": "backend",
            "honorific_type": "first_name",
            "communication_mode": "technical",
            "known_triggers": ["code_review", "deployment", "tech_debt"],
            "core_user_id": "dmitry_k"
        },
        {
            "user_id": "elena_v",
            "full_name": "Воронова Елена Николаевна",
            "role": "team_lead",
            "department": "frontend",
            "honorific_type": "patronymic",
            "communication_mode": "collaborative",
            "known_triggers": ["team_conflict", "deadline", "resources"],
            "core_user_id": "elena_v"
        },
        {
            "user_id": "sergey_m",
            "full_name": "Михайлов Сергей Олегович",
            "role": "intern",
            "department": "marketing",
            "honorific_type": "first_name",
            "communication_mode": "informal",
            "known_triggers": ["learning", "feedback", "mentorship"],
            "core_user_id": "sergey_m"
        },
        {
            "user_id": "olga_a",
            "full_name": "Алексеева Ольга Викторовна",
            "role": "director",
            "department": "sales",
            "honorific_type": "title",
            "communication_mode": "formal",
            "known_triggers": ["revenue", "targets", "clients"],
            "core_user_id": "olga_a"
        }
    ]
