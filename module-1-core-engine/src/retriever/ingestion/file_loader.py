# Загрузчик файлов

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
from common.logging import logger, log_info
from .chunking import get_chunker


class FileLoader:
    """Loader for various file types to be ingested into RAG."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunker = get_chunker(chunk_size, chunk_overlap)

    async def load_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and chunk a file."""
        ext = Path(file_path).suffix.lower()

        if ext == ".txt" or ext == ".md":
            return await self._load_text(file_path)
        elif ext == ".json":
            return await self._load_json(file_path)
        elif ext == ".pdf":
            return await self._load_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []

    async def _load_text(self, file_path: str) -> List[Dict[str, Any]]:
        """Load text/Markdown file."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            chunks = self.chunker.create_chunks_with_metadata(
                content, metadata={"source": file_path, "type": "text"}
            )

            log_info("Loaded text file", file=file_path, chunks=len(chunks))
            return chunks

        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            return []

    async def _load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load JSON file."""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            data = json.loads(content)

            # Handle different JSON structures
            if isinstance(data, list):
                chunks = []
                for item in data:
                    if isinstance(item, dict):
                        chunks.append(
                            {
                                "text": json.dumps(item),
                                "metadata": {"source": file_path, "type": "json"},
                            }
                        )
                    else:
                        chunks.append(
                            {
                                "text": str(item),
                                "metadata": {"source": file_path, "type": "json"},
                            }
                        )
                return chunks
            elif isinstance(data, dict):
                return [
                    {
                        "text": json.dumps(data),
                        "metadata": {"source": file_path, "type": "json"},
                    }
                ]

            return []

        except Exception as e:
            logger.error(f"Failed to load JSON file {file_path}: {e}")
            return []

    async def _load_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Load PDF file (requires pdfplumber or PyPDF2)."""
        try:
            # This would require pdfplumber or PyPDF2
            # For now, return placeholder
            logger.warning("PDF loading requires pdfplumber or PyPDF2")
            return []
        except Exception as e:
            logger.error(f"Failed to load PDF file {file_path}: {e}")
            return []

    async def load_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Load all files in a directory."""
        all_chunks = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith("."):
                    continue

                file_path = os.path.join(root, file)
                chunks = await self.load_file(file_path)
                all_chunks.extend(chunks)

        log_info("Loaded directory", directory=directory, chunks=len(all_chunks))
        return all_chunks


# Global loader instance
_loader: Optional[FileLoader] = None


def get_file_loader(chunk_size: int = 500, chunk_overlap: int = 50) -> FileLoader:
    """Get global file loader instance."""
    global _loader
    if _loader is None:
        _loader = FileLoader(chunk_size, chunk_overlap)
    return _loader
