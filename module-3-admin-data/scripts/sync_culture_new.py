#!/usr/bin/env python3
"""
Скрипт синхронизации corporate_culture_new.md с Qdrant через PostgreSQL.

Загружает файл в PostgreSQL, затем синхронизирует с Qdrant,
генерируя embeddings через Ollama из module-1-core-engine.
"""

import asyncio
import os
import sys
import uuid
import logging
from typing import List, Dict, Any

# Add src to path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, "src"))

from admin_api.database import get_pool, create_document, sync_all_documents_to_core
from common.logging import logger, log_info

# Добавляем путь к module-1-core-engine для доступа к embedder
module1_path = os.path.join(base_dir, '..', 'module-1-core-engine', 'src')
if os.path.exists(module1_path):
    sys.path.insert(0, module1_path)


async def parse_culture_markdown(file_path: str) -> List[Dict[str, Any]]:
    """
    Парсинг Markdown документа с корпоративной культурой.
    Извлекает структуру: главы, подглавы, примеры.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return []
    
    lines = content.split('\n')
    sections = []
    current_section = None
    section_number = 0

    for line in lines:
        stripped = line.strip()

        # Заголовки уровня #
        if stripped.startswith('# '):
            if current_section:
                sections.append(current_section)
            current_section = {
                'title': stripped[2:].strip(),
                'level': 1,
                'content': [],
                'examples': [],
                'number': section_number
            }
            section_number += 1
        elif stripped.startswith('## '):
            if current_section:
                sections.append(current_section)
            current_section = {
                'title': stripped[3:].strip(),
                'level': 2,
                'content': [],
                'examples': [],
                'number': section_number
            }
            section_number += 1
        elif stripped.startswith('### '):
            if current_section:
                current_section['content'].append(stripped[4:].strip())
        # Формат "1. Название"
        elif stripped and stripped[0].isdigit() and '.' in stripped:
            if current_section:
                sections.append(current_section)
            current_section = {
                'title': stripped.split('.', 1)[-1].strip() if '.' in stripped else stripped,
                'level': 2,
                'content': [],
                'examples': [],
                'number': section_number
            }
            section_number += 1
        elif stripped.startswith('* '):
            # Примеры поведения
            if current_section:
                current_section['examples'].append(stripped[2:].strip())
        elif stripped.startswith('- '):
            # Обычные пункты списка
            if current_section:
                current_section['content'].append(stripped[2:].strip())
        elif stripped and current_section:
            # Обычный текст
            current_section['content'].append(stripped)

    if current_section:
        sections.append(current_section)

    return sections


def create_chunks_from_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Создание chunks из секций Markdown документа.
    Каждый chunk включает метаданные о структуре документа.
    """
    chunks = []

    for section in sections:
        # Формируем текст секции
        section_text = f"{'#' * section['level']} {section['title']}\n"
        section_text += "\n".join(section['content'])

        # Добавляем примеры, если есть
        if section.get('examples'):
            section_text += "\n\nПримеры:\n"
            for example in section['examples']:
                section_text += f"- {example}\n"

        # Извлекаем категорию из названия секции
        title_lower = section['title'].lower().strip()
        
        categories = {
            'приветствие': ['приветствие', 'greeting'],
            'прощание': ['прощание', 'farewell'],
            'грубость': ['грубость', 'груб', 'rudeness'],
            'лесть': ['лесть', 'flattery'],
            'критика': ['критика', 'criticism'],
            'комплимент': ['комплимент', 'compliment'],
            'жалоба': ['жалоба', 'complaint'],
            'запрос': ['запрос', 'request'],
            'информация': ['информация', 'info'],
            'эмоция': ['эмоция', 'emotion'],
            'принцип': ['принцип', 'основные принципы'],
            'антипаттерн': ['антипаттерн', 'словарь'],
        }
        
        category = 'неизвестно'
        for cat, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    category = cat
                    break
            if category != 'неизвестно':
                break

        # Создаем metadata
        chunk_metadata = {
            'section_title': section['title'],
            'section_level': section['level'],
            'source': 'corporate_culture_new.md',
            'type': 'corporate_culture',
            'chunk_index': len(chunks),
            'category': category
        }

        chunks.append({
            'text': section_text,
            'metadata': chunk_metadata
        })

    return chunks


async def sync_culture_new():
    """
    Основная функция синхронизации corporate_culture_new.md.
    """
    log_info("Starting culture new sync")

    # Путь к файлу
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "demo_data",
        "corporate_culture_new.md"
    )
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    log_info("File found", path=file_path)

    # 1. Парсинг Markdown
    log_info("Parsing Markdown...")
    sections = await parse_culture_markdown(file_path)
    log_info("Markdown parsed", sections=len(sections))

    # 2. Создание chunks
    log_info("Creating chunks...")
    chunks = create_chunks_from_sections(sections)
    log_info("Chunks created", count=len(chunks))

    # 3. Загрузка в PostgreSQL
    log_info("Loading to PostgreSQL...")
    pool = await get_pool()
    
    for i, chunk in enumerate(chunks):
        doc_id = f"culture_new_{i}"
        document = {
            "document_id": doc_id,
            "filename": "corporate_culture_new.md",
            "file_type": "text/markdown",
            "file_size": len(chunk['text']),
            "collection": "corporate_culture",
            "content": chunk['text'],
            "status": "uploaded",
            "metadata": chunk['metadata']
        }
        
        try:
            await create_document(document)
            log_info("Document saved", doc_id=doc_id)
        except Exception as e:
            logger.error(f"Failed to save document {doc_id}: {e}")

    log_info("Documents loaded to PostgreSQL", count=len(chunks))

    # 4. Синхронизация в Qdrant (через sync_all_documents_to_core)
    log_info("Syncing to Qdrant...")
    
    try:
        # Получаем все документы в коллекции corporate_culture
        from admin_api.database import get_documents
        documents = await get_documents("corporate_culture")
        
        culture_docs = [d for d in documents if d.get("collection") == "corporate_culture"]
        log_info("Documents to sync", count=len(culture_docs))
        
        for doc in culture_docs:
            try:
                success = await sync_all_documents_to_core()  # Синхронизирует все
                log_info("Document synced", doc_id=doc['document_id'])
            except Exception as e:
                logger.error(f"Failed to sync document {doc['document_id']}: {e}")

        log_info("Culture new sync completed", documents=len(culture_docs))
        
    except Exception as e:
        logger.error(f"Failed to sync to Qdrant: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function."""
    try:
        await sync_culture_new()
        log_info("Culture new sync finished successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Culture new sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
