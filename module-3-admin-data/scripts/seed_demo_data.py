#!/usr/bin/env python3
"""
Seed Demo Data Script for Module 3 Admin
Generates and loads demo profiles, rules, and styles
"""

import sys
import os
import json
import logging
import httpx
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from admin_api.services.profile_generator import ProfileGenerator
from admin_api.services.bulk_importer import BulkImporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8100/api/v1/admin"

async def seed_profiles():
    """Generate and load demo profiles"""
    logger.info("Generating demo profiles...")
    
    generator = ProfileGenerator(seed=42)
    profiles = generator.generate_demo_profiles()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for profile in profiles:
            try:
                response = await client.post(
                    f"{API_URL}/profiles",
                    json=profile
                )
                if response.status_code == 200:
                    logger.info(f"Created profile: {profile['user_id']}")
                elif response.status_code == 409:
                    logger.warning(f"Profile already exists: {profile['user_id']}")
                else:
                    logger.error(f"Failed to create {profile['user_id']}: {response.text}")
            except Exception as e:
                logger.error(f"Error creating profile {profile['user_id']}: {e}")
    
    logger.info(f"Loaded {len(profiles)} profiles")

async def seed_rules():
    """Generate and load demo rules"""
    logger.info("Generating demo rules...")
    
    demo_rules = [
        {
            "rule_id": "rule_001",
            "name": "Greeting Policy",
            "description": "Always greet users with a friendly welcome message",
            "category": "behavior",
            "role": "user",
            "priority": 3,
            "condition": "if user.is_new",
            "action": "return generate_welcome_message()",
            "is_active": True
        },
        {
            "rule_id": "rule_002",
            "name": "Content Moderation",
            "description": "Flag and filter inappropriate content",
            "category": "security",
            "role": "user",
            "priority": 5,
            "condition": "if contains_profanity(user_message)",
            "action": "flag_content(); return polite_response()",
            "is_active": True
        },
        {
            "rule_id": "rule_003",
            "name": "Fallback Response",
            "description": "Default response when no other rule matches",
            "category": "general",
            "role": "system",
            "priority": 1,
            "condition": "always",
            "action": "return 'I apologize, but I need more context to help you. Could you please provide more details?'",
            "is_active": True
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for rule in demo_rules:
            try:
                response = await client.post(
                    f"{API_URL}/rules",
                    json=rule
                )
                if response.status_code == 200:
                    logger.info(f"Created rule: {rule['rule_id']}")
                elif response.status_code == 409:
                    logger.warning(f"Rule already exists: {rule['rule_id']}")
                else:
                    logger.error(f"Failed to create {rule['rule_id']}: {response.text}")
            except Exception as e:
                logger.error(f"Error creating rule {rule['rule_id']}: {e}")
    
    logger.info(f"Loaded {len(demo_rules)} rules")

async def seed_styles():
    """Generate and load demo styles"""
    logger.info("Generating demo styles...")
    
    demo_styles = [
        {
            "style_id": "style_001",
            "name": "Professional",
            "description": "Formal and business-like communication style",
            "category": "formal",
            "tone": "neutral",
            "examples": [
                {
                    "input": "Привет! Как дела?",
                    "output": "Здравствуйте! У меня все хорошо, спасибо. Чем могу помочь?",
                    "note": "Formal greeting response"
                },
                {
                    "input": "Мне нужно помощь с заказом",
                    "output": "Конечно, я готов помочь вам с вашим заказом. Пожалуйста, предоставьте номер заказа.",
                    "note": "Professional service response"
                }
            ],
            "is_active": True
        },
        {
            "style_id": "style_002",
            "name": "Friendly",
            "description": "Casual and approachable communication style",
            "category": "casual",
            "tone": "friendly",
            "examples": [
                {
                    "input": "Привет!",
                    "output": "Привет! Как я могу помочь тебе сегодня? 😊",
                    "note": "Casual greeting with emoji"
                },
                {
                    "input": "Мне нужна помощь",
                    "output": "Конечно! Давай я помогу тебе разобраться. Что именно тебя интересует?",
                    "note": "Friendly offer to help"
                }
            ],
            "is_active": True
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for style in demo_styles:
            try:
                response = await client.post(
                    f"{API_URL}/styles",
                    json=style
                )
                if response.status_code == 200:
                    logger.info(f"Created style: {style['style_id']}")
                elif response.status_code == 409:
                    logger.warning(f"Style already exists: {style['style_id']}")
                else:
                    logger.error(f"Failed to create {style['style_id']}: {response.text}")
            except Exception as e:
                logger.error(f"Error creating style {style['style_id']}: {e}")
    
    logger.info(f"Loaded {len(demo_styles)} styles")

async def main():
    """Run all seed operations"""
    logger.info("Starting demo data seeding...")
    
    try:
        await seed_profiles()
        await seed_rules()
        await seed_styles()
        
        logger.info("Demo data seeding completed!")
        
        # Try to sync profiles
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{API_URL}/system/profiles/sync")
                logger.info(f"Profile sync response: {response.json()}")
        except Exception as e:
            logger.warning(f"Could not sync profiles: {e}")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
