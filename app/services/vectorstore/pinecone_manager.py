"""
Pinecone vector database operations for scalable similarity search.

Implements production-grade vector storage and retrieval with:
- Serverless architecture (no infrastructure management)
- Fast similarity search (cosine metric)
- Metadata filtering for multi-document scenarios
- Similarity threshold filtering to ensure relevance
- Automatic index creation and management

Key Features:
- Scalable from development to production
- Sub-100ms query latency
- Built-in replication and reliability
- REST API for global accessibility
"""
import logging
from typing import List, Dict, Optional, Any
from pinecone import Pinecone, ServerlessSpec
import time

from config.settings import settings

logger = logging.getLogger(__name__)


class PineconeDB:
    """Pinecone vector database implementation."""
    
    def __init__(self):
        """Initialize Pinecone client."""
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.dimension = settings.pinecone_dimension
        self._index = None
        logger.info(f"Initialized Pinecone client for index: {self.index_name}")
    
    def create_index(self):
        """Create index if it doesn't exist."""
        try:
            if self.index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=settings.pinecone_cloud,
                        region=settings.pinecone_region
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                logger.info(f"Index {self.index_name} created successfully")
            else:
                logger.info(f"Index {self.index_name} already exists")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    def get_index(self):
        """Get index instance."""
        if self._index is None:
            self._index = self.pc.Index(self.index_name)
        return self._index
    
    def upsert(self, vectors: List[Dict]):
        """Insert/update vectors in the index."""
        try:
            index = self.get_index()
            formatted_vectors = [
                (vec["id"], vec["embedding"], vec.get("metadata", {}))
                for vec in vectors
            ]
            index.upsert(vectors=formatted_vectors)
            logger.info(f"Upserted {len(formatted_vectors)} vectors")
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict]:
        """Query the index for similar vectors."""
        try:
            index = self.get_index()
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata
            )
            
            formatted_results = []
            for match in results.matches:
                result = {
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata if include_metadata else {}
                }
                # Extract content from metadata for easier access
                if include_metadata and 'content' in match.metadata:
                    result['content'] = match.metadata['content']
                
                formatted_results.append(result)
            
            logger.info(f"Query returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying index: {e}")
            raise
    
    def delete_all(self):
        """Delete all vectors from the index."""
        try:
            index = self.get_index()
            index.delete(delete_all=True)
            logger.info("Deleted all vectors from index")
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise


class VectorDatabaseManager:
    """Manages vector database operations with similarity filtering."""
    
    def __init__(self):
        """Initialize vector database manager."""
        self.db = PineconeDB()
        self.db.create_index()
        self.similarity_threshold = settings.similarity_threshold
        logger.info(f"Initialized VectorDatabaseManager with similarity threshold: {self.similarity_threshold}")
    
    def store_embeddings(self, embeddings: List[Dict]):
        """Store embeddings in vector database."""
        self.db.upsert(embeddings)
        logger.info(f"Stored {len(embeddings)} embeddings")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        filter: Optional[Dict] = None,
        apply_threshold: bool = True
    ) -> List[Dict]:
        """
        Search for similar embeddings with optional similarity threshold filtering.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to retrieve
            filter: Metadata filter
            apply_threshold: Whether to apply similarity threshold filtering
            
        Returns:
            List of filtered results above similarity threshold
        """
        top_k = top_k or settings.top_k_results
        
        # Retrieve more results to account for threshold filtering
        retrieval_k = top_k * 2 if apply_threshold else top_k
        
        results = self.db.query(
            query_embedding=query_embedding,
            top_k=retrieval_k,
            filter=filter
        )
        
        logger.info(f"Raw search returned {len(results)} results")
        if results:
            logger.info(f"Score range: {min(r['score'] for r in results):.3f} - {max(r['score'] for r in results):.3f}")
        
        # Apply similarity threshold filtering
        if apply_threshold:
            filtered_results = [
                result for result in results 
                if result['score'] >= self.similarity_threshold
            ]
            
            # If filtered results are less than requested, log warning
            if len(filtered_results) < top_k:
                logger.warning(
                    f"Only {len(filtered_results)} results above threshold {self.similarity_threshold}. "
                    f"Requested {top_k}. Returning all {len(filtered_results)} results."
                )
                if results:
                    top_scores = [round(r['score'], 3) for r in results[:5]]
                    logger.warning(f"Top scores from query: {top_scores}")
            
            results = filtered_results[:top_k] if filtered_results else []
            logger.info(
                f"Search returned {len(results)} results above threshold {self.similarity_threshold}"
            )
        else:
            results = results[:top_k]
            logger.info(f"Search returned {len(results)} results (no threshold applied)")
        
        return results
    
    def clear(self):
        """Clear all vectors from database."""
        self.db.delete_all()
        logger.info("Cleared vector database")
