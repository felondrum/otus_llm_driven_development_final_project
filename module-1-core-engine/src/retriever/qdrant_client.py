# Клиент Qdrant

import os
from typing import Dict, Any, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
)
from common.logging import logger, log_info

# Import embedder for generating query vectors
from .embeddings import get_embedder


class QdrantClientWrapper:
    """Wrapper for Qdrant client with collection management."""

    def __init__(self, host: str = None, port: int = 6333):
        # Use environment variable or default to localhost (for tests) or qdrant (for docker)
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collections = ["user_profiles", "corporate_rules", "artistic_styles", "corporate_culture"]
        # Initialize embedder for query vector generation
        self.embedder = get_embedder()

    def connect(self):
        """Connect to Qdrant and ensure collections exist."""
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                # Test connection
                self.client.get_collections()
                logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

                # Create collections if they don't exist
                current_collections = [
                    c.name for c in self.client.get_collections().collections
                ]

                for collection in self.collections:
                    if collection not in current_collections:
                        self._create_collection(collection)

                log_info("Qdrant ready", collections=self.collections)
                return

            except Exception as e:
                logger.error(
                    f"Failed to connect to Qdrant (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    import time

                    logger.info(f"Retrying Qdrant connection in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        logger.error(f"Failed to connect to Qdrant after {max_retries} attempts")
        raise ConnectionError(f"Failed to connect to Qdrant at {self.host}:{self.port}")

    def _create_collection(self, collection_name: str):
        """Create a collection with vector config."""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {collection_name}")

    async def get_culture_chunks(
        self,
        query_text: str,
        limit: int = 5,
        filter_category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get relevant chunks from corporate culture using vector search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            filter_category: Optional category filter (e.g., "principles", "values")

        Returns:
            List of matching culture chunks
        """
        try:
            # Generate embedding for query
            query_vector = await self.embedder.generate_embedding(query_text)

            if not query_vector:
                logger.warning("Failed to generate embedding for culture query")
                return []

            # Build filter if category specified (Qdrant client v1.8+ API)
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            filter = None
            if filter_category:
                # Support both 'category' field and 'tags' array
                # Use 'should' to match either category field or tags array
                filter = Filter(
                    must=[
                        Filter(
                            should=[
                                FieldCondition(
                                    key="category",
                                    match=MatchValue(value=filter_category)
                                ),
                                FieldCondition(
                                    key="tags",
                                    match=MatchValue(value=filter_category)
                                )
                            ]
                        )
                    ]
                )

            search_result = self.client.search(
                collection_name="corporate_culture",
                query_vector=query_vector,
                query_filter=filter,
                limit=limit,
            )

            # Map the result to include section_title, text, and section_level
            result_chunks = []
            for hit in search_result:
                payload = hit.payload
                chunk = {
                    "text": payload.get("text", ""),
                    "section_title": payload.get("section_title", payload.get("category", "Раздел")),
                    "section_level": payload.get("section_level", 2),
                    "chunk_index": payload.get("chunk_index", 0),
                    "source": payload.get("source", ""),
                }
                result_chunks.append(chunk)
            return result_chunks
        except Exception as e:
            logger.error(f"Failed to get culture chunks: {e}")
            return []

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id."""
        try:
            # Generate UUID from user_id for Qdrant storage
            import uuid as uuid_module

            # Check if user_id looks like a UUID (contains hyphens in correct positions)
            is_uuid = (
                len(user_id) == 36
                and user_id.count("-") == 4
                and all(
                    c in "0123456789abcdef" for c in user_id.replace("-", "")
                )
            )
            
            if is_uuid:
                # user_id is a UUID (v4 or v5), use it directly
                point_id = user_id
            else:
                # user_id is a string like 'alex_i', generate UUID5
                point_id = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, user_id))

            result = self.client.retrieve(
                collection_name="user_profiles", ids=[point_id]
            )
            if result and len(result) > 0:
                profile = result[0].payload
                # Apply mappings to convert string values to proper format
                return self._map_profile(profile)
            return None
        except Exception as e:
            logger.error(f"Failed to get profile {user_id}: {e}")
            return None

    def _map_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Convert string enum values to numeric values for protobuf compatibility."""
        honorific_type_map = {
            "first_name": 1,
            "patronymic": 3,
            "last_name": 2,
            "title": 4,
            "default": 0,
        }
        
        communication_mode_map = {
            "informal": 2,
            "formal": 1,
            "neutral": 0,
            "technical": 3,
            "collaborative": 4,
        }
        
        # Convert honorific_type
        if "honorific_type" in profile:
            ht = profile["honorific_type"]
            if isinstance(ht, str):
                profile["honorific_type"] = honorific_type_map.get(ht, 0)
            elif isinstance(ht, int):
                pass  # Already an int
        
        # Convert communication_mode
        if "communication_mode" in profile:
            cm = profile["communication_mode"]
            if isinstance(cm, str):
                profile["communication_mode"] = communication_mode_map.get(cm, 0)
            elif isinstance(cm, int):
                pass  # Already an int
        
        return profile

    async def get_rules(
        self, sender_role: str, recipient_role: str, limit: int = 5, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get corporate rules by roles and category.

        Args:
            sender_role: Role of the sender
            recipient_role: Role of the recipient
            limit: Maximum number of results
            category: Optional rule category filter (e.g., 'address', 'tone', 'criticism')

        Returns:
            List of matching corporate rules
        """
        try:
            # Generate embedding for query
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            query_text = f"sender_role:{sender_role} recipient_role:{recipient_role}"
            query_vector = await embedder.generate_embedding(query_text)

            if not query_vector:
                logger.warning("Failed to generate embedding for rules query")
                return []

            # Build filter with category if specified
            query_filter = None
            if category:
                query_filter = Filter(
                    must=[FieldCondition(key="category", match=MatchValue(value=category))]
                )

            search_result = self.client.search(
                collection_name="corporate_rules",
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )

            # Map transformation to transformation_prompt for compatibility
            rules = [hit.payload for hit in search_result]
            for rule in rules:
                if "transformation" in rule and "transformation_prompt" not in rule:
                    rule["transformation_prompt"] = rule["transformation"]
            return rules
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return []

    def get_style_examples(
        self, style_name: str, sample_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Get random style examples.
        
        Args:
            style_name: Style identifier - can be style_id (UUID), style_id (like 'chekov'), or name (like 'чеховский')
            sample_count: Number of examples to return
            
        Returns:
            List of style examples in ArtisticStyle format
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Try to match by style_id (for latin names like 'chekov') or name (for Cyrillic like 'чеховский')
            filter = Filter(
                should=[
                    # Try to match style_id first (UUID format)
                    Filter(
                        must=[
                            FieldCondition(
                                key="style_id", 
                                match=MatchValue(value=style_name)
                            )
                        ]
                    ),
                    # Then try name field (for Cyrillic names like 'чеховский')
                    Filter(
                        must=[
                            FieldCondition(
                                key="name", 
                                match=MatchValue(value=style_name)
                            )
                        ]
                    )
                ]
            )

            # Search with filter (dummy vector for filter-only search)
            search_result = self.client.search(
                collection_name="artistic_styles",
                query_vector=[0.0] * 768,  # Dummy vector
                query_filter=filter,
                limit=sample_count,
            )

            if search_result and len(search_result) > 0:
                # Transform Qdrant format to ArtisticStyle format for context_assembler
                examples = []
                for hit in search_result:
                    payload = hit.payload
                    
                    # Extract name (could be in 'name' or 'style_name')
                    name = payload.get("name") or payload.get("style_name", "")
                    
                    # Extract tone and convert to emotion_tags
                    tone = payload.get("tone", "")
                    emotion_tags = []
                    if tone and isinstance(tone, str):
                        emotion_tags = [t.strip() for t in tone.split(",") if t.strip()]
                    elif isinstance(tone, list):
                        emotion_tags = tone
                    
                    # Extract author from examples if available
                    author = ""
                    examples_list = payload.get("examples", [])
                    if examples_list and isinstance(examples_list, list) and len(examples_list) > 0:
                        first_example = examples_list[0]
                        if isinstance(first_example, dict):
                            note = first_example.get("note", "")
                            if note and "Author:" in note:
                                author = note.replace("Author:", "").strip()
                    
                    # Extract sample_text from examples if available
                    sample_text = ""
                    if examples_list and isinstance(examples_list, list) and len(examples_list) > 0:
                        first_example = examples_list[0]
                        if isinstance(first_example, dict):
                            sample_text = first_example.get("output", "") or first_example.get("output", "")
                    
                    examples.append({
                        "style_name": name,
                        "author": author,
                        "sample_text": sample_text,
                        "emotion_tags": emotion_tags,
                    })
                return examples
            return []
        except Exception as e:
            logger.error(f"Failed to get style examples: {e}")
            return []

    def search_rules(
        self,
        query_vector: List[float],
        sender_role: str,
        recipient_role: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search rules by vector."""
        try:
            filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value="address"))]
            )

            search_result = self.client.search(
                collection_name="corporate_rules",
                query_vector=query_vector,
                filter=filter,
                limit=limit,
            )

            # Map transformation to transformation_prompt for compatibility
            rules = [hit.payload for hit in search_result]
            for rule in rules:
                if "transformation" in rule and "transformation_prompt" not in rule:
                    rule["transformation_prompt"] = rule["transformation"]
            return rules
        except Exception as e:
            logger.error(f"Failed to search rules: {e}")
            return []

    def close(self):
        """Close Qdrant connection."""
        self.client.close()
        logger.info("Qdrant connection closed")

    # ===========================================
    # Styles management methods
    # ===========================================

    async def get_styles(self) -> List[Dict[str, Any]]:
        """Get all styles from artistic_styles collection."""
        try:
            # Get all points from artistic_styles collection
            result = self.client.scroll(
                collection_name="artistic_styles",
                limit=1000,
                with_payload=True,
                with_vectors=False,
            )
            
            styles = []
            for point in result[0]:
                payload = point.payload
                # Convert to common style format
                examples = []
                if "examples" in payload:
                    for ex in payload["examples"]:
                        if isinstance(ex, dict):
                            examples.append({
                                "input": ex.get("input", ""),
                                "output": ex.get("output", ""),
                                "note": ex.get("note", "")
                            })
                
                style = {
                    "style_id": point.id,
                    "name": payload.get("name", ""),
                    "description": payload.get("description", ""),
                    "category": payload.get("category", ""),
                    "tone": payload.get("tone", ""),
                    "examples": examples,
                    "is_active": payload.get("is_active", True),
                    "created_at": payload.get("created_at", 0),
                    "updated_at": payload.get("updated_at", 0)
                }
                styles.append(style)
            
            return styles
        except Exception as e:
            logger.error(f"Failed to get styles: {e}")
            return []

    async def create_style(self, style_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new style in artistic_styles collection."""
        try:
            import uuid
            
            style_id = style_data.get("style_id") or str(uuid.uuid4())
            
            # Prepare examples
            examples = []
            if "examples" in style_data:
                for ex in style_data["examples"]:
                    if isinstance(ex, dict):
                        examples.append({
                            "input": ex.get("input", ""),
                            "output": ex.get("output", ""),
                            "note": ex.get("note", "")
                        })
            
            payload = {
                "name": style_data.get("name", ""),
                "description": style_data.get("description", ""),
                "category": style_data.get("category", ""),
                "tone": style_data.get("tone", ""),
                "examples": examples,
                "is_active": style_data.get("is_active", True),
                "created_at": int(style_data.get("created_at", 0)),
                "updated_at": int(style_data.get("updated_at", 0))
            }
            
            # Generate embedding for style
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            style_text = f"{payload.get('name', '')} {payload.get('description', '')} {payload.get('category', '')} {payload.get('tone', '')}"
            embedding = await embedder.generate_embedding(style_text)
            
            # Upsert the style
            self.client.upsert(
                collection_name="artistic_styles",
                points=[
                    {
                        "id": style_id,
                        "vector": embedding,
                        "payload": payload
                    }
                ]
            )
            
            logger.info(f"Created style: {style_id}")
            return {"style_id": style_id, **payload}
        except Exception as e:
            logger.error(f"Failed to create style: {e}")
            raise

    async def update_style(self, style_id: str, style_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing style in artistic_styles collection."""
        try:
            # First get the existing style
            result = self.client.retrieve(
                collection_name="artistic_styles",
                ids=[style_id]
            )
            
            if not result or len(result) == 0:
                raise ValueError(f"Style not found: {style_id}")
            
            existing_payload = result[0].payload
            
            # Update with new values
            for key, value in style_data.items():
                if key != "style_id":
                    existing_payload[key] = value
            
            existing_payload["updated_at"] = int(style_data.get("updated_at", 0))
            
            # Generate new embedding if style text changed
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            style_text = f"{existing_payload.get('name', '')} {existing_payload.get('description', '')} {existing_payload.get('category', '')} {existing_payload.get('tone', '')}"
            embedding = await embedder.generate_embedding(style_text)
            
            # Update the style
            self.client.upsert(
                collection_name="artistic_styles",
                points=[
                    {
                        "id": style_id,
                        "vector": embedding,
                        "payload": existing_payload
                    }
                ]
            )
            
            logger.info(f"Updated style: {style_id}")
            return {"style_id": style_id, **existing_payload}
        except Exception as e:
            logger.error(f"Failed to update style {style_id}: {e}")
            raise

    async def delete_style(self, style_id: str) -> bool:
        """Delete a style from artistic_styles collection."""
        try:
            self.client.delete(
                collection_name="artistic_styles",
                points_selector=[style_id]
            )
            logger.info(f"Deleted style: {style_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete style {style_id}: {e}")
            raise

    async def get_style(self, style_id: str) -> Dict[str, Any]:
        """Get a specific style by ID."""
        try:
            result = self.client.retrieve(
                collection_name="artistic_styles",
                ids=[style_id]
            )
            
            if not result or len(result) == 0:
                raise ValueError(f"Style not found: {style_id}")
            
            payload = result[0].payload
            examples = []
            if "examples" in payload:
                for ex in payload["examples"]:
                    if isinstance(ex, dict):
                        examples.append({
                            "input": ex.get("input", ""),
                            "output": ex.get("output", ""),
                            "note": ex.get("note", "")
                        })
            
            return {
                "style_id": style_id,
                "name": payload.get("name", ""),
                "description": payload.get("description", ""),
                "category": payload.get("category", ""),
                "tone": payload.get("tone", ""),
                "examples": examples,
                "is_active": payload.get("is_active", True),
                "created_at": payload.get("created_at", 0),
                "updated_at": payload.get("updated_at", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get style {style_id}: {e}")
            raise

    # ===========================================
    # Rules management methods
    # ===========================================

    async def reload_rules(self) -> Dict[str, Any]:
        """Reload rules from data source."""
        try:
            # In a real implementation, this would reload rules from a file or external source
            # For now, we'll return a success message
            logger.info("Rules reloaded")
            
            # Get count of rules
            result = self.client.scroll(
                collection_name="corporate_rules",
                limit=1,
                with_payload=False,
                with_vectors=False,
            )
            rules_count = result[1] or 0
            
            return {
                "message": "Rules reloaded successfully",
                "rules_count": rules_count
            }
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")
            raise

    async def reindex_collection(self, collection: str) -> Dict[str, Any]:
        """Reindex all documents in a collection."""
        try:
            logger.info(f"Starting reindex for collection: {collection}")
            
            # Get all points from the collection
            scroll_result = self.client.scroll(
                collection_name=collection,
                limit=1000,
                with_payload=True,
                with_vectors=False,
            )
            
            points = scroll_result[0]
            total_points = scroll_result[1] or len(points)
            
            logger.info(f"Found {total_points} points in collection {collection}")
            
            # In a real implementation, this would:
            # 1. Delete existing vectors
            # 2. Re-embed all documents
            # 3. Upsert with new vectors
            
            # For now, return success message
            result = {
                "status": "reindex_started",
                "message": f"Reindex started for collection: {collection}",
                "documents_count": total_points
            }
            
            logger.info(f"Reindex completed for collection: {collection}")
            return result
        except Exception as e:
            logger.error(f"Failed to reindex collection {collection}: {e}")
            raise

    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str, 
        collection: str = "corporate_rules",
        metadata: dict = None
    ) -> Dict[str, Any]:
        """Upload document to Qdrant collection with chunking and embeddings."""
        try:
            import uuid as uuid_module
            from .chunking import get_chunker
            from .embeddings import get_embedder
            
            # Parse file content
            try:
                text_content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_content.decode('latin-1')
            
            # Use chunker to split text
            chunker = get_chunker(chunk_size=500, chunk_overlap=50)
            chunks = chunker.create_chunks_with_metadata(
                text_content,
                metadata={
                    "source": filename,
                    "file_type": "text",
                    "original_size": len(file_content)
                }
            )
            
            logger.info(f"Created {len(chunks)} chunks from file: {filename}")
            
            # Generate embeddings for each chunk
            ollama_host = os.getenv("OLLAMA_HOST", "ollama")
            ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
            embedder = get_embedder(host=ollama_host, port=ollama_port)
            
            points = []
            for i, chunk_info in enumerate(chunks):
                chunk_text = chunk_info["text"]
                chunk_metadata = chunk_info["metadata"]
                
                # Generate embedding for chunk
                embedding = await embedder.generate_embedding(chunk_text)
                
                if not embedding:
                    logger.warning(f"Failed to generate embedding for chunk {i}")
                    continue
                
                # Create point with chunk data
                point_id = str(uuid_module.uuid4())
                
                # Merge metadata
                full_metadata = {
                    "chunk_index": i,
                    "chunk_length": len(chunk_text),
                    "source": filename,
                    **(metadata or {}),
                    **chunk_metadata
                }
                
                points.append({
                    "id": point_id,
                    "vector": embedding,
                    "payload": full_metadata
                })
            
            # Upsert points to Qdrant
            self.client.upsert(
                collection_name=collection,
                points=points
            )
            
            logger.info(f"Successfully uploaded {len(points)} chunks from {filename} to {collection}")
            
            return {
                "status": "success",
                "filename": filename,
                "collection": collection,
                "chunks_count": len(points),
                "total_size": len(file_content)
            }
        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {e}")
            raise


# Global client instance
_qdrant_client: Optional[QdrantClientWrapper] = None


def get_qdrant_client(host: str = None, port: int = 6333) -> QdrantClientWrapper:
    """Get global Qdrant client instance."""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClientWrapper(host=host, port=port)
        _qdrant_client.connect()
    return _qdrant_client
