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

# Core Engine gRPC client
try:
    from grpc_client.orchestrator_client import get_profile as grpc_get_profile
    logger.info("Successfully imported gRPC client for Core Engine")
    GRPC_ENABLED = True
except ImportError as e:
    logger.warning(f"Could not import gRPC client: {e}. Using fallback mode.")
    GRPC_ENABLED = False
    grpc_get_profile = None

# Also try to import process_message (used in websocket)
try:
    from grpc_client.orchestrator_client import process_message
    logger.info("Successfully imported process_message from gRPC client")
except ImportError:
    logger.warning("Could not import process_message from gRPC client")


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with profiles table"""
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


def load_profiles_from_core_engine():
    """Load profiles from Core Engine via gRPC"""
    if not GRPC_ENABLED or grpc_get_profile is None:
        logger.warning("gRPC client not available, cannot load profiles from Core Engine")
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
            profile = grpc_get_profile(user_id)
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
    """Get all profiles from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles ORDER BY full_name")
    rows = cursor.fetchall()
    conn.close()
    
    profiles = []
    for row in rows:
        profile = dict(row)
        # Convert known_triggers from JSON string
        if profile.get("known_triggers"):
            try:
                profile["known_triggers"] = json.loads(profile["known_triggers"])
            except json.JSONDecodeError:
                profile["known_triggers"] = []
        profiles.append(profile)
    
    return profiles


def get_profile_by_user_id(user_id: str) -> Optional[Dict]:
    """Get a profile by user_id"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        profile = dict(row)
        # Convert known_triggers from JSON string
        if profile.get("known_triggers"):
            try:
                profile["known_triggers"] = json.loads(profile["known_triggers"])
            except json.JSONDecodeError:
                profile["known_triggers"] = []
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
    """Sync profiles with Core Engine"""
    if not GRPC_ENABLED or grpc_get_profile is None:
        logger.warning("gRPC client not available, cannot sync with Core Engine")
        return False
    
    # Load profiles from Core Engine
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
