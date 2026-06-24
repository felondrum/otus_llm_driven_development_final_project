#!/usr/bin/env python3
"""
Загрузка корпоративных правил в Qdrant с эмбеддингами через Ollama.

Правила формата YAML с полями:
- category: категория правила (грубость, адрес, тон и т.д.)
- role: роль (system)
- priority: приоритет (1-100)
- condition: условие применения
- name: название правила
- description: описание
- action: действие (что делать при нарушении)
- example_original: исходная грубая формулировка
- example_adapted: адаптированная вежливая формулировка
"""

import os
import sys
import yaml
import uuid
from typing import List, Dict, Any

# Add src to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, 'src'))

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from retriever.embeddings import get_embedder
from common.logging import logger, log_info, log_error


def load_rules_from_yaml(file_path: str) -> List[Dict[str, Any]]:
    """Load rules from YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse YAML content
        rules = []
        current_rule = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('- **category**'):
                if current_rule:
                    rules.append(current_rule)
                current_rule = {}
                current_rule['category'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **role**'):
                current_rule['role'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **priority**'):
                current_rule['priority'] = int(line.split(':', 1)[1].strip())
            elif line.startswith('- **condition**'):
                current_rule['condition'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **name**'):
                current_rule['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **description**'):
                current_rule['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **action**'):
                current_rule['action'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **example_original**'):
                current_rule['example_original'] = line.split(':', 1)[1].strip()
            elif line.startswith('- **example_adapted**'):
                current_rule['example_adapted'] = line.split(':', 1)[1].strip()
        
        # Don't forget the last rule
        if current_rule:
            rules.append(current_rule)
        
        return rules
    except Exception as e:
        logger.error(f"Failed to load rules from YAML: {e}")
        return []


def load_rules_from_markdown(file_path: str) -> List[Dict[str, Any]]:
    """Load rules from markdown file with YAML-like structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = []
        current_rule = {}
        
        for line in content.split('\n'):
            # Check for rule header (e.g., "## 1. Правило:...")
            if line.startswith('## ') and 'Правило:' in line:
                if current_rule:
                    rules.append(current_rule)
                current_rule = {}
                # Extract rule name from header
                rule_name = line.replace('## ', '').replace('Правило:', '').strip()
                current_rule['name'] = rule_name
            elif line.startswith('- **') and ':' in line:
                # Parse YAML field: - **field_name**: value
                field_part = line[2:]  # Remove '- '
                if '**' in field_part:
                    # Split field name and value
                    parts = field_part.split('**: ', 1)
                    if len(parts) == 2:
                        field_name = parts[0].replace('**', '').strip().lower().replace(' ', '_')
                        field_value = parts[1].strip()
                        current_rule[field_name] = field_value
        
        # Don't forget the last rule
        if current_rule:
            rules.append(current_rule)
        
        return rules
    except Exception as e:
        logger.error(f"Failed to load rules from markdown: {e}")
        return []


def create_points_from_rules(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create Qdrant points from rules."""
    points = []
    
    for i, rule in enumerate(rules):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, rule.get('name', f'rule_{i}')))
        
        # Create text representation for embedding
        text_parts = [
            f"Категория: {rule.get('category', 'general')}",
            f"Название: {rule.get('name', '')}",
            f"Описание: {rule.get('description', '')}",
            f"Условие: {rule.get('condition', '')}",
            f"Действие: {rule.get('action', '')}",
        ]
        if rule.get('example_original') and rule.get('example_adapted'):
            text_parts.append(f"Пример грубости: {rule.get('example_original')}")
            text_parts.append(f"Пример адаптации: {rule.get('example_adapted')}")
        
        text = '\n'.join(text_parts)
        
        point = {
            "id": point_id,
            "vector": None,  # Will be set later with embedding
            "payload": {
                "rule_id": point_id,
                "category": rule.get('category', 'general'),
                "role": rule.get('role', 'system'),
                "priority": rule.get('priority', 50),
                "condition": rule.get('condition', ''),
                "name": rule.get('name', ''),
                "description": rule.get('description', ''),
                "action": rule.get('action', ''),
                "transformation": rule.get('action', ''),
                "transformation_prompt": rule.get('action', ''),
                "example_original": rule.get('example_original', ''),
                "example_adapted": rule.get('example_adapted', ''),
                "rule_type": rule.get('category', 'general'),
                "created_at": "2026-06-24T00:00:00",
                "updated_at": "2026-06-24T00:00:00",
                "source": "corporate_rules",
                "chunk_index": i,
                "chunk_length": len(text)
            }
        }
        points.append(point)
    
    return points


async def upload_rules_to_qdrant(rules: List[Dict[str, Any]], host: str = "qdrant", port: int = 6333):
    """Upload rules to Qdrant with embeddings."""
    try:
        # Connect to Qdrant
        client = QdrantClient(host=host, port=port)
        
        # Get or create collection
        collections = [c.name for c in client.get_collections().collections]
        if "corporate_rules" not in collections:
            client.create_collection(
                collection_name="corporate_rules",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            log_info("Created corporate_rules collection")
        else:
            log_info("Corporate_rules collection already exists")
        
        # Initialize embedder
        ollama_host = os.getenv("OLLAMA_HOST", "ollama")
        ollama_port = int(os.getenv("OLLAMA_PORT", "11434"))
        embedder = get_embedder(host=ollama_host, port=ollama_port)
        
        # Create points
        points = create_points_from_rules(rules)
        
        # Generate embeddings for each point
        log_info(f"Generating embeddings for {len(points)} rules...")
        for point in points:
            # Use full text representation for embedding
            text = " ".join([
                point["payload"].get("category", ""),
                point["payload"].get("name", ""),
                point["payload"].get("description", ""),
                point["payload"].get("condition", ""),
                point["payload"].get("action", ""),
            ])
            
            # Clean up text (remove excessive whitespace)
            text = " ".join(text.split())
            
            embedding = await embedder.generate_embedding(text)
            
            if embedding:
                point["vector"] = embedding
                log_info(f"Generated embedding for rule: {point['payload']['name']}")
            else:
                log_error(f"Failed to generate embedding for rule: {point['payload']['name']}")
        
        # Upload points
        client.upsert(
            collection_name="corporate_rules",
            points=points
        )
        
        log_info(f"Successfully uploaded {len(points)} rules to Qdrant")
        
        return {"status": "success", "count": len(points)}
        
    except Exception as e:
        log_error(f"Failed to upload rules: {e}")
        raise


async def main():
    """Main function."""
    # File paths
    rules_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "demo_data",
        "corporate_rules.md"
    )
    
    # Load rules
    if not os.path.exists(rules_file):
        log_error(f"Rules file not found: {rules_file}")
        sys.exit(1)
    
    log_info(f"Loading rules from: {rules_file}")
    rules = load_rules_from_markdown(rules_file)
    log_info(f"Loaded {len(rules)} rules")
    
    # Upload to Qdrant
    host = os.getenv("QDRANT_HOST", "qdrant")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    result = await upload_rules_to_qdrant(rules, host=host, port=port)
    log_info(f"Upload result: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
