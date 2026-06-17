# Тесты чанкования текста

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from retriever.chunking import TextChunker


class TestTextChunker:
    """Tests for TextChunker class."""
    
    def test_init_defaults(self):
        """Инициализация с дефолтными параметрами."""
        chunker = TextChunker()
        
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50
        assert chunker.method == "recursive"
    
    def test_init_custom_params(self):
        """Инициализация с кастомными параметрами."""
        chunker = TextChunker(
            chunk_size=256,
            chunk_overlap=25,
            method="simple"
        )
        
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 25
        assert chunker.method == "simple"
    
    def test_recursive_chunk_basic(self):
        """Базовое рекурсивное чанкование."""
        chunker = TextChunker(chunk_size=100, method="recursive")
        
        text = "This is a test text. It has multiple sentences. And more text here."
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 100
    
    def test_recursive_chunk_paragraphs(self):
        """Чанкование с параграфами."""
        chunker = TextChunker(chunk_size=200, method="recursive")
        
        text = "First paragraph with some text.\n\nSecond paragraph with more text."
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
    
    def test_recursive_chunk_sentences(self):
        """Чанкование с предложениями."""
        chunker = TextChunker(chunk_size=50, method="recursive")
        
        text = "Hello world. This is test. Another sentence here."
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
    
    def test_semantic_chunk(self):
        """Семантическое чанкование."""
        chunker = TextChunker(chunk_size=100, method="semantic")
        
        text = "Some test text with meaning."
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
    
    def test_simple_chunk(self):
        """Простое чанкование по символам."""
        chunker = TextChunker(chunk_size=20, method="simple")
        
        text = "This is a longer text that will be split."
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 20
    
    def test_chunk_empty_text(self):
        """Пустой текст."""
        chunker = TextChunker()
        
        chunks = chunker.chunk("")
        
        # Пустой текст может вернуть [""] или []
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")
    
    def test_chunk_single_word(self):
        """Одно слово."""
        chunker = TextChunker(chunk_size=10)
        
        chunks = chunker.chunk("hello")
        
        assert len(chunks) == 1
        assert chunks[0] == "hello"
    
    def test_chunk_large_text(self):
        """Большой текст."""
        chunker = TextChunker(chunk_size=50, method="simple")
        
        text = "word " * 100
        chunks = chunker.chunk(text)
        
        assert len(chunks) >= 1
    
    def test_create_chunks_with_metadata(self):
        """Создание чанков с метаданными."""
        chunker = TextChunker(chunk_size=50)
        
        text = "This is test text for chunking."
        metadata = {'source': 'test', 'doc_id': '123'}
        
        result = chunker.create_chunks_with_metadata(text, metadata)
        
        assert len(result) >= 1
        for item in result:
            assert 'text' in item
            assert 'metadata' in item
            assert item['metadata']['source'] == 'test'
            assert item['metadata']['doc_id'] == '123'
            assert 'chunk_index' in item['metadata']
            assert 'chunk_length' in item['metadata']
            assert 'total_chunks' in item['metadata']
    
    def test_create_chunks_with_metadata_none(self):
        """Создание чанков без метаданных."""
        chunker = TextChunker(chunk_size=50)
        
        text = "Test text."
        result = chunker.create_chunks_with_metadata(text, None)
        
        assert len(result) >= 1
        for item in result:
            assert 'text' in item
            assert 'metadata' in item
            assert 'chunk_index' in item['metadata']


class TestTextChunkerGlobal:
    """Tests for global chunker functions."""
    
    def test_get_chunker_first_init(self):
        """Получение chunker при первой инициализации."""
        from retriever import chunking as chunking_module
        
        chunking_module._chunker = None
        
        chunker = chunking_module.get_chunker(
            chunk_size=256,
            chunk_overlap=25,
            method="recursive"
        )
        
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 25
        assert chunker.method == "recursive"
    
    def test_get_chunker_existing_instance(self):
        """Получение существующего экземпляра."""
        from retriever import chunking as chunking_module
        
        chunking_module._chunker = None
        
        chunker1 = chunking_module.get_chunker()
        chunker2 = chunking_module.get_chunker()
        
        assert chunker1 is chunker2
