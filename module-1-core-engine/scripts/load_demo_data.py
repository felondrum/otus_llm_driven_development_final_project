import json
import random
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct


def load_profiles(client: QdrantClient):
    """Load user profiles from demo data to Qdrant."""
    with open("demo_data/profiles.json") as f:
        profiles = json.load(f)
    
    for profile in profiles:
        # Generate UUID5 from user_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, profile["user_id"]))
        
        # Generate vector (mock - in production would use actual embeddings)
        vector = [random.random() for _ in range(768)]
        
        client.upsert(
            collection_name="user_profiles",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=profile
            )]
        )
    print(f"Loaded {len(profiles)} profiles")


def load_rules(client: QdrantClient):
    """Load corporate rules from demo data to Qdrant."""
    with open("demo_data/rules.json") as f:
        rules = json.load(f)
    
    for rule in rules:
        # Generate UUID5 from rule_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule["rule_id"]))
        vector = [random.random() for _ in range(768)]
        client.upsert(
            collection_name="corporate_rules",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=rule
            )]
        )
    print(f"Loaded {len(rules)} rules")


def load_styles(client: QdrantClient):
    """Load artistic styles from demo data to Qdrant."""
    with open("demo_data/styles.json") as f:
        styles = json.load(f)
    
    for style in styles:
        # Generate UUID5 from style_id for consistent point IDs
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, style["style_id"]))
        vector = [random.random() for _ in range(768)]
        client.upsert(
            collection_name="artistic_styles",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=style
            )]
        )
    print(f"Loaded {len(styles)} styles")


if __name__ == "__main__":
    client = QdrantClient(host="localhost", port=6333)
    
    try:
        # Check connection
        client.get_collections()
        print("Connected to Qdrant successfully")
        
        # Create collections if not exist
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if "user_profiles" not in collection_names:
            client.create_collection(
                collection_name="user_profiles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("Created collection: user_profiles")
        
        if "corporate_rules" not in collection_names:
            client.create_collection(
                collection_name="corporate_rules",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("Created collection: corporate_rules")
        
        if "artistic_styles" not in collection_names:
            client.create_collection(
                collection_name="artistic_styles",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("Created collection: artistic_styles")
        
        if "corporate_culture" not in collection_names:
            client.create_collection(
                collection_name="corporate_culture",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            print("Created collection: corporate_culture")
        
        # Load data
        load_profiles(client)
        load_rules(client)
        load_styles(client)
        
        print("Demo data loaded successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Qdrant is running on localhost:6333")


def load_culture(client: QdrantClient):
    """Load corporate culture from demo data to Qdrant."""
    import uuid
    from retriever.chunking import get_chunker
    
    with open("demo_data/corporate_culture.md") as f:
        content = f.read()
    
    chunker = get_chunker(chunk_size=500, chunk_overlap=50, method="recursive")
    chunks = chunker.chunk(content)
    
    for i, chunk in enumerate(chunks):
        # Generate UUID for each chunk
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"corporate_culture:{i}"))
        # Generate vector (mock - in production would use actual embeddings)
        vector = [random.random() for _ in range(768)]
        
        # Extract metadata from chunk
        section_title = "culture"
        if i < len(chunks) - 1:
            # Try to extract section title from next chunk if it's a header
            next_chunk = chunks[i + 1].split('\n')[0] if '\n' in chunks[i + 1] else "culture"
            if next_chunk.startswith('#'):
                section_title = next_chunk.replace('#', '').strip()
        
        client.upsert(
            collection_name="corporate_culture",
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": chunk,
                    "section_title": section_title,
                    "section_level": 2,
                    "source": "demo_data/corporate_culture.md",
                    "type": "corporate_culture",
                    "chunk_index": i
                }
            )]
        )
    print(f"Loaded {len(chunks)} culture chunks")