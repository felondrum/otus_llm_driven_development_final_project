# ===========================================
# Document Processor Service
# ===========================================

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and index documents for RAG system"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_extensions = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.html': 'text/html',
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.xml': 'text/xml',
        }
    
    def get_file_type(self, filename: str) -> Optional[str]:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        return self.supported_extensions.get(ext)
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap"""
        chunks = []
        words = text.split()
        
        current_chunk = []
        for i, word in enumerate(words):
            current_chunk.append(word)
            
            if len(' '.join(current_chunk)) >= self.chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start next chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                current_chunk = current_chunk[overlap_start:]
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except ImportError:
            logger.warning("python-docx not installed. Install with: pip install python-docx")
            return ""
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            return ""
    
    def process_file(self, file_path: str) -> Dict:
        """Process a single file and return metadata and chunks"""
        ext = Path(file_path).suffix.lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Failed to read file: {e}")
                content = ""
        
        chunks = self.chunk_text(content)
        
        return {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "file_type": self.get_file_type(file_path),
            "size": os.path.getsize(file_path),
            "content": content,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    
    def batch_process(self, directory: str) -> List[Dict]:
        """Process all files in a directory"""
        results = []
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                try:
                    processed = self.process_file(file_path)
                    results.append(processed)
                    logger.info(f"Processed: {filename} ({processed['chunk_count']} chunks)")
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {e}")
        
        return results
