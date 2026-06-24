#!/usr/bin/env python3
"""Clear all collections in Qdrant"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList

def clear_qdrant():
    qdrant_host = os.getenv("QDRANT_HOST", "host.docker.internal")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    client = QdrantClient(host=qdrant_host, port=qdrant_port)
    
    # Get all collections
    collections = client.get_collections()
    
    print(f"Found {len(collections.collections)} collections:")
    for collection in collections.collections:
        print(f"  - {collection.name}")
    
    # Clear each collection
    for collection in collections.collections:
        try:
            # Get all point IDs
            points, _ = client.scroll(
                collection_name=collection.name,
                limit=1000,
                with_payload=False,
                with_vectors=False
            )
            
            if points:
                point_ids = [point.id for point in points]
                print(f"\nDeleting {len(point_ids)} points from '{collection.name}'...")
                
                # Delete points in batches
                client.delete(
                    collection_name=collection.name,
                    points_selector=PointIdsList(
                        points=point_ids
                    )
                )
                print(f"✓ Cleared '{collection.name}'")
            else:
                print(f"  '{collection.name}' is already empty")
        except Exception as e:
            print(f"Error clearing '{collection.name}': {e}")
    
    print("\nQdrant cleared successfully!")

if __name__ == "__main__":
    clear_qdrant()
