"""
Embedding generation using HuggingFace Sentence Transformers.

Implements local, privacy-preserving embedding generation with:
- High-quality semantic representations (768-dim vectors)
- No API costs or rate limits
- Consistent embeddings for retrieval
- Batch processing for efficiency

Model: sentence-transformers/all-mpnet-base-v2
- Trained on 1B+ sentence pairs
- Balanced performance and speed
- Suitable for semantic search and clustering
"""
import logging
from typing import List, Dict, Optional, Any
from sentence_transformers import SentenceTransformer

from config.settings import settings

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddings:
    """HuggingFace embeddings provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize HuggingFace embeddings."""
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Initialized embeddings with model: {model_name}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    @property
    def embedding_dimension(self) -> int:
        """Return the dimensionality of embeddings."""
        return self._dimension


class EmbeddingManager:
    """Manages embedding generation using HuggingFace Sentence Transformers."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize embedding manager."""
        model = model or settings.huggingface_embedding_model
        self.provider = HuggingFaceEmbeddings(model_name=model)
        logger.info(f"Initialized EmbeddingManager with model: {model}")
    
    def embed_chunks(self, chunks: List[any], batch_size: int = 8) -> List[Dict]:
        """
        Generate embeddings for a list of chunks in small batches to avoid memory issues.
        
        Args:
            chunks: List of chunk objects
            batch_size: Number of chunks to process at once (default: 8 for memory efficiency)
        """
        results = []
        total_chunks = len(chunks)
        
        # Process in small batches to avoid memory overflow
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.content for chunk in batch]
            
            # Generate embeddings for this batch with smaller internal batch size
            embeddings = self.provider.embed_batch(texts, batch_size=4)
            
            for chunk, embedding in zip(batch, embeddings):
                # Include content in metadata for retrieval
                metadata = dict(chunk.metadata)
                metadata['content'] = chunk.content
                metadata['token_count'] = chunk.token_count
                
                results.append({
                    "id": f"{chunk.metadata.get('filename', 'unknown')}_{chunk.chunk_id}",
                    "embedding": embedding,
                    "metadata": metadata
                })
            
            logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} ({len(batch)} chunks)")
        
        logger.info(f"Generated {len(results)} embeddings total")
        return results
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        return self.provider.embed_text(query)
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.provider.embedding_dimension
