#!/usr/bin/env python3
"""Load demo data from Module 1 into PostgreSQL Module 3"""

import asyncio
import json
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "admin_api"))

from database import (
    get_pool,
    close_pool,
    create_profile,
    create_rule,
    create_style,
    create_document,
    get_profiles,
    get_rules,
    get_styles,
    get_documents,
)


async def load_profiles():
    """Load profiles from demo data to PostgreSQL"""
    with open("demo_data/profiles.json") as f:
        profiles = json.load(f)
    
    pool = await get_pool()
    
    for profile in profiles:
        # Check if profile already exists
        existing = await pool.fetchrow(
            "SELECT user_id FROM profiles WHERE user_id = $1",
            profile["user_id"]
        )
        
        if not existing:
            await pool.execute(
                """INSERT INTO profiles (user_id, full_name, role, department, honorific_type, 
                   communication_mode, known_triggers)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                profile["user_id"],
                profile["full_name"],
                profile["role"],
                profile["department"],
                profile["honorific_type"],
                profile["communication_mode"],
                json.dumps(profile.get("known_triggers", []))
            )
            print(f"  Created profile: {profile['user_id']}")
        else:
            print(f"  Profile {profile['user_id']} already exists, skipping")
    
    await close_pool()
    print(f"Loaded {len(profiles)} profiles")


async def load_rules():
    """Load rules from demo data to PostgreSQL"""
    with open("demo_data/rules.json") as f:
        rules = json.load(f)
    
    pool = await get_pool()
    
    for rule in rules:
        # Check if rule already exists
        existing = await pool.fetchrow(
            "SELECT rule_id FROM rules WHERE rule_id = $1",
            rule["rule_id"]
        )
        
        if not existing:
            await pool.execute(
                """INSERT INTO rules (rule_id, name, description, category, role, priority, 
                   condition, action, is_active)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                rule["rule_id"],
                rule.get("name", rule["rule_id"]),
                rule.get("description", ""),
                rule.get("category", ""),
                rule.get("role", ""),
                rule.get("priority", 5),
                rule.get("condition", ""),
                rule.get("transformation", ""),
                True
            )
            print(f"  Created rule: {rule['rule_id']}")
        else:
            print(f"  Rule {rule['rule_id']} already exists, skipping")
    
    await close_pool()
    print(f"Loaded {len(rules)} rules")


async def load_styles():
    """Load styles from demo data to PostgreSQL"""
    with open("demo_data/styles.json") as f:
        styles = json.load(f)
    
    pool = await get_pool()
    
    for style in styles:
        # Check if style already exists
        existing = await pool.fetchrow(
            "SELECT style_id FROM styles WHERE style_id = $1",
            style["style_id"]
        )
        
        if not existing:
            # Convert emotion_tags to tone string for PostgreSQL
            emotion_tags = style.get("emotion_tags", [])
            tone = ", ".join(emotion_tags) if emotion_tags else ""
            
            await pool.execute(
                """INSERT INTO styles (style_id, name, description, category, tone, examples, is_active)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                style["style_id"],
                style.get("style_name", style["style_id"]),
                style.get("description", f"Author: {style.get('author', '')}"),
                style.get("era", ""),
                tone,
                json.dumps([
                    {
                        "input": "default",
                        "output": style.get("sample_text", ""),
                        "note": f"Author: {style.get('author', '')}"
                    }
                ]),
                True
            )
            print(f"  Created style: {style['style_id']}")
        else:
            print(f"  Style {style['style_id']} already exists, skipping")
    
    await close_pool()
    print(f"Loaded {len(styles)} styles")


async def load_corporate_culture():
    """Load corporate culture document to PostgreSQL"""
    with open("demo_data/corporate_culture.md", "r") as f:
        content = f.read()
    
    pool = await get_pool()
    
    # Check if document already exists
    existing = await pool.fetchrow(
        "SELECT document_id FROM documents WHERE filename = $1",
        "corporate_culture.md"
    )
    
    if not existing:
        document_id = f"doc_corporate_culture_{hash(content) % 10000:04d}"
        
        await pool.execute(
            """INSERT INTO documents (document_id, filename, file_type, file_size, collection, content, status, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            document_id,
            "corporate_culture.md",
            "text/markdown",
            len(content),
            "corporate_culture",
            content,
            "uploaded",
            json.dumps({"source": "demo_data/corporate_culture.md"})
        )
        print(f"  Created corporate culture document: {document_id}")
    else:
        print(f"  Corporate culture document already exists, skipping")
    
    await close_pool()


async def main():
    """Load all demo data into PostgreSQL"""
    print("Loading demo data from Module 1 into PostgreSQL Module 3")
    print("=" * 60)
    
    try:
        # Load profiles
        print("\n1. Loading profiles...")
        await load_profiles()
        
        # Load rules
        print("\n2. Loading rules...")
        await load_rules()
        
        # Load styles
        print("\n3. Loading styles...")
        await load_styles()
        
        # Load corporate culture
        print("\n4. Loading corporate culture...")
        await load_corporate_culture()
        
        print("\n" + "=" * 60)
        print("Demo data loaded successfully!")
        
        # Verify loaded data
        await verify_data()
        
    except Exception as e:
        print(f"Error during loading: {e}")
        import traceback
        traceback.print_exc()


async def verify_data():
    """Verify loaded data"""
    pool = await get_pool()
    
    profiles_count = await pool.fetchval("SELECT COUNT(*) FROM profiles")
    rules_count = await pool.fetchval("SELECT COUNT(*) FROM rules")
    styles_count = await pool.fetchval("SELECT COUNT(*) FROM styles")
    documents_count = await pool.fetchval("SELECT COUNT(*) FROM documents")
    
    await close_pool()
    
    print("\nVerification:")
    print(f"  Profiles: {profiles_count}")
    print(f"  Rules: {rules_count}")
    print(f"  Styles: {styles_count}")
    print(f"  Documents: {documents_count}")


if __name__ == "__main__":
    asyncio.run(main())
