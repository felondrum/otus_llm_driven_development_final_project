# Чанкование - разбиение текста на части для эмбеддинга

from typing import List, Dict, Any, Optional
import re


class TextChunker:
    """Chunk text into smaller pieces for embedding."""

    def __init__(
        self, chunk_size: int = 500, chunk_overlap: int = 50, method: str = "recursive"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.method = method

    def chunk(self, text: str) -> List[str]:
        """Chunk text into smaller pieces."""
        if self.method == "recursive":
            return self._recursive_chunk(text)
        elif self.method == "semantic":
            return self._semantic_chunk(text)
        else:
            return self._simple_chunk(text)

    def _recursive_chunk(self, text: str) -> List[str]:
        """Recursive chunking with sentence boundary."""
        # Split by paragraphs first
        paragraphs = text.split("\n\n")
        chunks = []

        for paragraph in paragraphs:
            # Split by sentences
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            current_chunk = ""

            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= self.chunk_size:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + " "

            if current_chunk:
                chunks.append(current_chunk.strip())

        return chunks

    def _semantic_chunk(self, text: str) -> List[str]:
        """Chunk by semantic sections (headers, code blocks, etc.)."""
        # This is a simplified version
        # In production, would use markdown parsing or similar
        return self._recursive_chunk(text)

    def _simple_chunk(self, text: str) -> List[str]:
        """Simple character-based chunking."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def create_chunks_with_metadata(
        self, text: str, metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Create chunks with metadata."""
        chunks = self.chunk(text)
        result = []

        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "chunk_index": i,
                "chunk_length": len(chunk),
                "total_chunks": len(chunks),
            }

            if metadata:
                chunk_metadata.update(metadata)

            result.append({"text": chunk, "metadata": chunk_metadata})

        return result


# Global chunker instance
_chunker: Optional[TextChunker] = None


def get_chunker(
    chunk_size: int = 500, chunk_overlap: int = 50, method: str = "recursive"
) -> TextChunker:
    """Get global chunker instance."""
    global _chunker
    if _chunker is None:
        _chunker = TextChunker(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, method=method
        )
    return _chunker
