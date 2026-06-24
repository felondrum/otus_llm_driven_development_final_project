#!/usr/bin/env python3
"""
CLI утилита для загрузки корпоративной культуры в Qdrant с эмбеддингами.

Использование:
    python scripts/ingest_corporate_culture_new.py \
        --input demo_data/corporate_culture_new.md \
        --collection corporate_culture \
        --batch-size 50
"""

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

# Добавляем путь к модулям
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, 'src'))

from retriever.chunking import get_chunker
from retriever.embeddings import get_embedder
from retriever.qdrant_client import get_qdrant_client
from common.logging import logger, log_info


class CorporateCultureLoader:
    """Загрузчик корпоративной культуры в Qdrant."""

    def __init__(
        self,
        input_path: str,
        collection: str = "corporate_culture",
        batch_size: int = 50,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedder_host: str = "localhost",
        embedder_port: int = 11434
    ):
        self.input_path = input_path
        self.collection = collection
        self.batch_size = batch_size
        self.chunker = get_chunker(chunk_size, chunk_overlap, "semantic")
        self.embedder = get_embedder(host=embedder_host, port=embedder_port)
        self.qdrant = get_qdrant_client()

    async def parse_markdown_new(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсинг Markdown документа с корпоративной культурой.
        Извлекает структуру: главы, подглавы, примеры.
        Поддерживает формат "1. Название" и "# Название"
        """
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

    async def create_chunks_from_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
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

            # Создаем chunks
            chunk_metadata = {
                'section_title': section['title'],
                'section_level': section['level'],
                'source': self.input_path,
                'type': 'corporate_culture',
                'chunk_index': len(chunks),
                'category': self._extract_category(section['title'])
            }

            section_chunks = self.chunker.create_chunks_with_metadata(
                section_text,
                metadata=chunk_metadata
            )

            chunks.extend(section_chunks)

        return chunks

    def _extract_category(self, title: str) -> str:
        """Извлечение категории из названия секции."""
        title_lower = title.lower().strip()
        
        categories = {
            'приветствие': ['приветствие', 'greeting', 'здравствуйте'],
            'прощание': ['прощание', 'farewell', 'до свидания'],
            'грубость': ['грубость', 'груб', 'rudeness', 'стоп-слово'],
            'лесть': ['лесть', 'flattery', 'ласть'],
            'критика': ['критика', 'criticism', 'бутерброд'],
            'комплимент': ['комплимент', 'compliment', 'хвал'],
            'жалоба': ['жалоба', 'complaint', 'нытье'],
            'запрос': ['запрос', 'request', 'просьба'],
            'информация': ['информация', 'info', 'факты'],
            'эмоция': ['эмоция', 'emotion', 'эмпатич'],
            'принцип': ['принцип', 'основные принципы'],
            'антипаттерн': ['антипаттерн', 'словарь', 'фраза'],
            'протокол': ['экстренные', 'протокол', 'если вы'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        return 'неизвестно'

    async def load_to_qdrant(
        self,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Загрузка chunks в Qdrant с эмбеддингами.
        Возвращает количество успешно загруженных документов.
        """
        loaded_count = 0

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_with_vectors = []

            for chunk in batch:
                text = chunk['text']
                metadata = chunk['metadata']

                # Генерируем эмбеддинг
                embedding = await self.embedder.generate_embedding(text)

                if embedding:
                    point_id = str(uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"{metadata['source']}:{metadata['chunk_index']}"
                    ))

                    batch_with_vectors.append({
                        'id': point_id,
                        'vector': embedding,
                        'payload': {
                            'text': text,
                            **metadata
                        }
                    })
                    loaded_count += 1
                else:
                    logger.warning(f"Failed to generate embedding for chunk {i}")

            # Загружаем батч в Qdrant
            if batch_with_vectors:
                from qdrant_client.models import PointStruct
                points = [
                    PointStruct(
                        id=item['id'],
                        vector=item['vector'],
                        payload=item['payload']
                    )
                    for item in batch_with_vectors
                ]

                self.qdrant.client.upsert(
                    collection_name=self.collection,
                    points=points
                )

                log_info(
                    "Batch loaded",
                    batch=i // self.batch_size + 1,
                    size=len(batch_with_vectors),
                    total=loaded_count
                )

        return loaded_count

    async def run(self) -> int:
        """
        Запуск процесса загрузки.
        Возвращает количество загруженных документов.
        """
        logger.info(f"Starting corporate culture ingestion from {self.input_path}")

        # 1. Загружаем файл
        with open(self.input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        log_info("File loaded", path=self.input_path, length=len(content))

        # 2. Парсим Markdown
        sections = await self.parse_markdown_new(content)
        log_info("Markdown parsed", sections=len(sections))

        # 3. Создаем chunks
        chunks = await self.create_chunks_from_sections(sections)
        log_info("Chunks created", count=len(chunks))

        # 4. Загружаем в Qdrant
        loaded = await self.load_to_qdrant(chunks)
        log_info("Ingestion completed", loaded=loaded)

        return loaded


async def main():
    parser = argparse.ArgumentParser(
        description='Загрузка корпоративной культуры в Qdrant'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='demo_data/corporate_culture_new.md',
        help='Путь к Markdown файлу с корпоративной культурой'
    )
    parser.add_argument(
        '--collection',
        type=str,
        default='corporate_culture',
        help='Имя коллекции в Qdrant'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Размер батча для загрузки'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500,
        help='Размер chunk в токенах'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=50,
        help='Перекрытие между chunks'
    )
    parser.add_argument(
        '--embedder-host',
        type=str,
        default='localhost',
        help='Хост сервиса эмбеддингов (Ollama)'
    )
    parser.add_argument(
        '--embedder-port',
        type=int,
        default=11434,
        help='Порт сервиса эмбеддингов'
    )

    args = parser.parse_args()

    # Проверяем существование файла
    if not os.path.exists(args.input):
        logger.error(f"File not found: {args.input}")
        sys.exit(1)

    # Создаем загрузчик и запускаем
    loader = CorporateCultureLoader(
        input_path=args.input,
        collection=args.collection,
        batch_size=args.batch_size,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embedder_host=args.embedder_host,
        embedder_port=args.embedder_port
    )

    try:
        loaded = await loader.run()
        logger.info(f"Ingestion completed. Loaded {loaded} documents.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
