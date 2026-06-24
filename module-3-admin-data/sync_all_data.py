#!/usr/bin/env python3
"""Sync all data from PostgreSQL to Qdrant collections"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "admin_api"))

from database import (
    sync_all_profiles_to_core,
    sync_all_rules_to_core,
    sync_all_styles_to_core,
    sync_all_documents_to_core,
)


async def main():
    """Sync all data from PostgreSQL to Qdrant."""
    
    # Get Qdrant connection settings
    qdrant_host = os.getenv("QDRANT_HOST", "host.docker.internal")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    print(f"Syncing data from PostgreSQL to Qdrant at {qdrant_host}:{qdrant_port}")
    print("=" * 60)
    
    try:
        # Sync profiles
        print("\n1. Syncing profiles...")
        profile_count = await sync_all_profiles_to_core()
        print(f"   ✓ Synced {profile_count} profiles to user_profiles collection")
        
        # Sync rules
        print("\n2. Syncing rules...")
        rule_count = await sync_all_rules_to_core()
        print(f"   ✓ Synced {rule_count} rules to corporate_rules collection")
        
        # Sync styles
        print("\n3. Syncing styles...")
        style_count = await sync_all_styles_to_core()
        print(f"   ✓ Synced {style_count} styles to artistic_styles collection")
        
        # Sync documents
        print("\n4. Syncing documents...")
        document_count = await sync_all_documents_to_core()
        print(f"   ✓ Synced {document_count} documents")
        
        # Sync documents from corporate_culture
        print("\n5. Syncing corporate culture documents...")
        # Get all documents and sync those in corporate_culture collection
        from database import get_documents
        documents = await get_documents()
        culture_docs = [d for d in documents if d.get("collection") == "corporate_culture"]
        
        for doc in culture_docs:
            from database import sync_document_to_core
            success = await sync_document_to_core(doc["document_id"])
            if success:
                print(f"   ✓ Synced document {doc['document_id']} to corporate_culture")
        
        print("\n" + "=" * 60)
        print("Sync completed successfully!")
        print(f"Total: {profile_count} profiles, {rule_count} rules, {style_count} styles, {document_count + len(culture_docs)} documents")
        
    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
