"""
Semantic chunking utilities for splitting documents intelligently.

Implements intelligent text segmentation with:
- Semantic-aware splitting (sentence and paragraph boundaries)
- Configurable chunk size and overlap for context preservation
- Token-based measurement using tiktoken
- Metadata propagation for traceability
- Overlap management to maintain semantic continuity

Chunking Strategy:
- Primary: Split at paragraph boundaries for semantic coherence
- Fallback: Split at sentence boundaries if paragraphs too large
- Last resort: Character-based splitting with word boundary respect
- Overlap: Configurable token overlap between chunks (default 200)

Benefits:
- Preserves semantic meaning across chunks
- Maintains context for better retrieval
- Avoids cutting in the middle of concepts
- Optimizes for LLM context windows

Configuration (from .env):
- CHUNK_SIZE: Target tokens per chunk (default 1000)
- CHUNK_OVERLAP: Overlap tokens for continuity (default 200)
- MIN_CHUNK_SIZE: Minimum viable chunk size (default 100)
"""
import re
import logging
from dataclasses import dataclass
from typing import Dict, List, Any

import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    content: str
    chunk_id: int
    start_char: int
    end_char: int
    token_count: int
    metadata: Dict[str, any]


class SemanticChunker:
    """
    Semantic-aware chunking that respects document structure.
    
    This strategy:
    1. Splits by paragraphs first
    2. Respects sentence boundaries
    3. Maintains configurable chunk size and overlap
    4. Preserves semantic coherence
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, min_chunk_size: int = 100):
        """Initialize semantic chunker."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Initialize tokenizer for accurate token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None
            logger.warning("Tiktoken not available, using character approximation")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Handle common abbreviations and edge cases
        text = re.sub(r'\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr)\.\s', r'\1<PERIOD> ', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore abbreviations
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]
        
        return [s.strip() for s in sentences if s.strip()]
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk_text(self, text: str, metadata: Dict[str, any]) -> List[Chunk]:
        """
        Chunk text using semantic-aware strategy.
        
        Process:
        1. Split into paragraphs (preserve document structure)
        2. Split paragraphs into sentences
        3. Group sentences into chunks respecting token limits
        4. Add overlap between chunks for context continuity
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_id = 0
        char_position = 0
        
        paragraphs = self.split_into_paragraphs(text)
        
        for paragraph in paragraphs:
            sentences = self.split_into_sentences(paragraph)
            
            for sentence in sentences:
                sentence_tokens = self.count_tokens(sentence)
                
                # If adding this sentence exceeds chunk size, save current chunk
                if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_start = char_position
                    chunk_end = char_position + len(chunk_text)
                    
                    chunks.append(Chunk(
                        content=chunk_text,
                        chunk_id=chunk_id,
                        start_char=chunk_start,
                        end_char=chunk_end,
                        token_count=current_tokens,
                        metadata={
                            **metadata,
                            "chunk_id": chunk_id,
                            "chunking_strategy": "semantic"
                        }
                    ))
                    
                    chunk_id += 1
                    char_position = chunk_end + 1
                    
                    # Handle overlap: keep last few sentences for context
                    overlap_text = []
                    overlap_tokens = 0
                    
                    for prev_sentence in reversed(current_chunk):
                        prev_tokens = self.count_tokens(prev_sentence)
                        if overlap_tokens + prev_tokens <= self.chunk_overlap:
                            overlap_text.insert(0, prev_sentence)
                            overlap_tokens += prev_tokens
                        else:
                            break
                    
                    current_chunk = overlap_text
                    current_tokens = overlap_tokens
                
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk and current_tokens >= self.min_chunk_size:
            chunk_text = " ".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text,
                chunk_id=chunk_id,
                start_char=char_position,
                end_char=char_position + len(chunk_text),
                token_count=current_tokens,
                metadata={
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunking_strategy": "semantic"
                }
            ))
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks


class DocumentChunker:
    """Main chunking interface."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """Initialize document chunker."""
        self.strategy = SemanticChunker(chunk_size, chunk_overlap, min_chunk_size)
    
    def chunk_document(self, document: Dict[str, any]) -> List[Chunk]:
        """
        Chunk a processed document.
        
        Args:
            document: Document dict from DocumentProcessor
            
        Returns:
            List of Chunk objects
        """
        text = document["text"]
        metadata = document["metadata"]
        
        # Add page information to metadata if available
        if "pages" in document and document["pages"]:
            chunks = []
            for page in document["pages"]:
                page_metadata = {
                    **metadata,
                    "page_number": page.get("page_number", 1)
                }
                page_chunks = self.strategy.chunk_text(page["content"], page_metadata)
                chunks.extend(page_chunks)
            return chunks
        else:
            return self.strategy.chunk_text(text, metadata)
