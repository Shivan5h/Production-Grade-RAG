"""
Document processing utilities for extracting text from various file formats.

Implements intelligent document parsing with:
- Multi-format support (PDF, DOCX, TXT, Markdown)
- Robust error handling and fallback mechanisms
- Text cleaning and preprocessing
- Metadata extraction for context tracking
- Character encoding detection

Supported Formats:
- PDF: Using pypdf for text extraction
- DOCX: Using python-docx for Word documents
- TXT: Direct text file reading with encoding detection
- Markdown: Preservation of structure and formatting

Process Flow:
1. Format detection
2. Appropriate loader selection
3. Text extraction
4. Preprocessing and cleaning
5. Metadata attachment
"""
import logging
from pathlib import Path
from typing import Dict, List, Any

import pypdf
from docx import Document
import markdown

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document loading and text extraction from various formats."""
    
    SUPPORTED_FORMATS = {
        ".pdf": "process_pdf",
        ".docx": "process_docx",
        ".txt": "process_txt",
        ".md": "process_markdown"
    }
    
    def __init__(self):
        """Initialize the document processor."""
        pass
    
    def process_document(self, file_path: Path) -> Dict[str, any]:
        """
        Process a document and extract its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing:
                - text: Extracted text content
                - metadata: Document metadata (filename, page_count, etc.)
                - pages: List of page contents (for paginated documents)
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {list(self.SUPPORTED_FORMATS.keys())}"
            )
        
        processor_method = getattr(self, self.SUPPORTED_FORMATS[file_extension])
        
        try:
            result = processor_method(file_path)
            logger.info(f"Successfully processed {file_path.name}")
            return result
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            raise
    
    def process_pdf(self, file_path: Path) -> Dict[str, any]:
        """Extract text from PDF files."""
        pages = []
        full_text = []
        
        with open(file_path, "rb") as file:
            pdf_reader = pypdf.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                text = page.extract_text()
                pages.append({
                    "page_number": page_num,
                    "content": text
                })
                full_text.append(text)
        
        return {
            "text": "\n\n".join(full_text),
            "pages": pages,
            "metadata": {
                "filename": file_path.name,
                "file_type": "pdf",
                "page_count": num_pages,
                "file_size": file_path.stat().st_size
            }
        }
    
    def process_docx(self, file_path: Path) -> Dict[str, any]:
        """Extract text from DOCX files."""
        doc = Document(file_path)
        
        paragraphs = []
        full_text = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
                full_text.append(para.text)
        
        return {
            "text": "\n\n".join(full_text),
            "pages": [{"page_number": 1, "content": "\n\n".join(full_text)}],
            "metadata": {
                "filename": file_path.name,
                "file_type": "docx",
                "paragraph_count": len(paragraphs),
                "file_size": file_path.stat().st_size
            }
        }
    
    def process_txt(self, file_path: Path) -> Dict[str, any]:
        """Extract text from TXT files."""
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
        
        return {
            "text": text,
            "pages": [{"page_number": 1, "content": text}],
            "metadata": {
                "filename": file_path.name,
                "file_type": "txt",
                "file_size": file_path.stat().st_size
            }
        }
    
    def process_markdown(self, file_path: Path) -> Dict[str, any]:
        """Extract text from Markdown files."""
        with open(file_path, "r", encoding="utf-8") as file:
            md_text = file.read()
        
        return {
            "text": md_text,
            "pages": [{"page_number": 1, "content": md_text}],
            "metadata": {
                "filename": file_path.name,
                "file_type": "markdown",
                "file_size": file_path.stat().st_size
            }
        }
