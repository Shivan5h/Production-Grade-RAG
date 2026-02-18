"""
FastAPI routes for production-grade RAG system.

Lazy-loading architecture - services are imported only when first used.
"""
import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-loaded services (initialized on first use)
_services = {}

def get_service(name: str):
    """Lazy load services to avoid loading heavy models at startup."""
    if name not in _services:
        logger.info(f"Initializing service: {name}")
        
        if name == 'doc_processor':
            from utils.document_processor import DocumentProcessor
            _services[name] = DocumentProcessor()
        elif name == 'chunker':
            from utils.chunking import DocumentChunker
            _services[name] = DocumentChunker()
        elif name == 'embedding_manager':
            from services.rag.embeddings.embedding_manager import EmbeddingManager
            _services[name] = EmbeddingManager()
        elif name == 'vector_db':
            from services.vectorstore.pinecone_manager import VectorDatabaseManager
            _services[name] = VectorDatabaseManager()
        elif name == 'llm_generator':
            from services.rag.llm.groq_generator import GroqLLMGenerator
            _services[name] = GroqLLMGenerator()
        else:
            raise ValueError(f"Unknown service: {name}")
    
    return _services[name]


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 0.95
    max_tokens: Optional[int] = 1000


class CompareRequest(BaseModel):
    query: str
    doc1_name: str
    doc2_name: str
    top_k: Optional[int] = 3
    temperature: Optional[float] = 0.3
    top_p: Optional[float] = 0.95
    max_tokens: Optional[int] = 1500


@router.get("/documents")
async def list_documents():
    """List all uploaded documents in the vector database."""
    try:
        # Get index stats to see what's stored
        vector_db = get_service('vector_db')
        index = vector_db.db.get_index()
        index_stats = index.describe_index_stats()
        total_vectors = index_stats.get('total_vector_count', 0)
        
        logger.info(f"Index stats: {index_stats}")
        
        # If no vectors, return empty list
        if total_vectors == 0:
            logger.info("No documents in vector database yet")
            return {
                "status": "success",
                "total_vectors": 0,
                "documents": [],
                "document_count": 0
            }
        
        # Query a sample to get unique filenames
        # We'll do a dummy query to fetch some vectors
        # Use dimension 384 for MiniLM-L6-v2 model
        dummy_embedding = [0.0] * 384
        sample_results = vector_db.db.query(
            query_embedding=dummy_embedding,
            top_k=min(100, total_vectors) if total_vectors > 0 else 10,
            include_metadata=True
        )
        
        logger.info(f"Sample query returned {len(sample_results)} results")
        
        # Extract unique filenames
        filenames = set()
        for result in sample_results:
            metadata = result.get('metadata', {})
            if 'filename' in metadata:
                filenames.add(metadata['filename'])
            logger.debug(f"Result {result['id']}: has content={('content' in metadata)}, filename={metadata.get('filename', 'N/A')}")
        
        logger.info(f"Found {len(filenames)} unique documents in vector database")
        
        return {
            "status": "success",
            "total_vectors": total_vectors,
            "documents": sorted(list(filenames)),
            "document_count": len(filenames)
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        # Return empty list instead of raising error
        return {
            "status": "error",
            "total_vectors": 0,
            "documents": [],
            "document_count": 0,
            "error": str(e)
        }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document with intelligent chunking and embedding generation.
    Automatically replaces old versions if document with same name exists.
    """
    try:
        # Save uploaded file
        file_path = Path(f"./uploads/{file.filename}")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing document: {file.filename}")
        
        # Get services (lazy loaded)
        doc_processor = get_service('doc_processor')
        chunker = get_service('chunker')
        embedding_manager = get_service('embedding_manager')
        vector_db = get_service('vector_db')
        
        # Delete old version if exists (prevents duplicates)
        try:
            index = vector_db.db.get_index()
            # Delete all vectors with this filename
            index.delete(filter={'filename': file.filename})
            logger.info(f"Deleted old version of {file.filename}")
        except Exception as e:
            # Ignore namespace not found (first upload)
            if "Namespace not found" in str(e) or "404" in str(e):
                logger.info(f"First upload of {file.filename} (no old version to delete)")
            else:
                logger.warning(f"Could not delete old version: {e}")
        
        # Process document with appropriate loader
        document = doc_processor.process_document(file_path)
        
        # Intelligent chunking with semantic continuity
        chunks = chunker.chunk_document(document)
        
        # Generate vector embeddings
        embeddings = embedding_manager.embed_chunks(chunks)
        
        # Log first embedding to verify content is included
        if embeddings:
            first_emb = embeddings[0]
            logger.info(f"First embedding - ID: {first_emb['id']}, has content: {'content' in first_emb['metadata']}, "
                       f"content length: {len(first_emb['metadata'].get('content', ''))} chars")
        
        # Store in vector database for similarity search
        vector_db.store_embeddings(embeddings)
        
        logger.info(f"Uploaded and processed document: {file.filename}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"Processed {len(chunks)} chunks"
        }
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query documents using RAG with similarity filtering and grounded generation."""
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Get services (lazy loaded)
        embedding_manager = get_service('embedding_manager')
        vector_db = get_service('vector_db')
        llm_generator = get_service('llm_generator')
        
        # Generate query embedding
        query_embedding = embedding_manager.embed_query(request.query)
        logger.info(f"Generated query embedding with dimension: {len(query_embedding)}")
        
        # Search vector database - TEMPORARILY disable threshold to debug
        results = vector_db.search(
            query_embedding, 
            top_k=request.top_k,
            apply_threshold=False  # CHANGED: Temporarily disabled to see all results
        )
        
        logger.info(f"Vector search returned {len(results)} results")
        
        # Log scores to debug
        if results:
            scores = [r.get('score', 0) for r in results]
            logger.info(f"Result scores: {scores}")
            logger.info(f"First result has content: {'content' in results[0].keys() or 'content' in results[0].get('metadata', {})}")
        
        # Validate retrieved context
        if not results:
            logger.warning(f"No relevant context found for query: {request.query[:50]}...")
            return {
                "status": "success",
                "query": request.query,
                "answer": "I could not find any relevant information in the uploaded documents to answer your question. Please ensure documents are uploaded and try rephrasing your query.",
                "context_chunks": [],
                "model": "N/A",
                "temperature": request.temperature,
                "top_p": request.top_p,
                "warning": "No relevant context above similarity threshold"
            }
        
        # Generate grounded answer with citation enforcement
        answer_data = llm_generator.generate_answer(
            query=request.query,
            context_chunks=results,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens
        )
        
        logger.info(f"Query: {request.query[:50]}...")
        
        return {
            "status": "success",
            "query": request.query,
            "answer": answer_data["answer"],
            "context_chunks": results,
            "source_mapping": answer_data.get("source_mapping", {}),
            "model": answer_data["model"],
            "temperature": request.temperature,
            "top_p": request.top_p
        }
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_documents(request: CompareRequest):
    """Compare two documents with parallel retrieval and structured analysis."""
    try:
        logger.info(f"Received compare request: {request.query[:50]}...")
        
        # Get services (lazy loaded)
        embedding_manager = get_service('embedding_manager')
        vector_db = get_service('vector_db')
        llm_generator = get_service('llm_generator')
        
        # Generate query embedding
        query_embedding = embedding_manager.embed_query(request.query)
        
        # Parallel retrieval from both documents
        doc1_results = vector_db.search(
            query_embedding,
            top_k=request.top_k,
            filter={'filename': request.doc1_name}
        )
        
        doc2_results = vector_db.search(
            query_embedding,
            top_k=request.top_k,
            filter={'filename': request.doc2_name}
        )
        
        # Validate retrieved contexts
        if not doc1_results and not doc2_results:
            return {
                "status": "error",
                "query": request.query,
                "comparison": "No relevant information found in either document.",
                "doc1_chunks": [],
                "doc2_chunks": []
            }
        
        # Build comparison prompt
        doc1_text = "\n".join([chunk.get('content', chunk.get('metadata', {}).get('content', '')) for chunk in doc1_results])
        doc2_text = "\n".join([chunk.get('content', chunk.get('metadata', {}).get('content', '')) for chunk in doc2_results])
        
        comparison_prompt = f"""Compare the following information from two different documents regarding: {request.query}

Document 1 ({request.doc1_name}):
{doc1_text}

Document 2 ({request.doc2_name}):
{doc2_text}

Provide a structured comparison highlighting:
1. Similarities
2. Differences
3. Key insights from each document"""
        
        # Generate comparison using the answer method
        comparison_data = llm_generator.generate_answer(
            query=comparison_prompt,
            context_chunks=doc1_results + doc2_results,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens
        )
        
        return {
            "status": "success",
            "query": request.query,
            "comparison": comparison_data["answer"],
            "doc1_name": request.doc1_name,
            "doc2_name": request.doc2_name,
            "doc1_chunks_found": len(doc1_results),
            "doc2_chunks_found": len(doc2_results),
            "model": comparison_data["model"]
        }
    except Exception as e:
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document from the vector database."""
    try:
        vector_db = get_service('vector_db')
        index = vector_db.db.get_index()
        
        # Delete all vectors with this filename
        index.delete(filter={'filename': filename})
        
        logger.info(f"Deleted document: {filename}")
        
        return {
            "status": "success",
            "message": f"Deleted {filename}"
        }
    except Exception as e:
        error_msg = str(e)
        # Handle namespace not found (no data uploaded yet)
        if "Namespace not found" in error_msg or "404" in error_msg:
            return {
                "status": "success",
                "message": "No data to delete (database is empty)"
            }
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def delete_all_documents():
    """Delete ALL documents from the vector database."""
    try:
        vector_db = get_service('vector_db')
        index = vector_db.db.get_index()
        
        # Get current count
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        
        if total_vectors == 0:
            return {
                "status": "success",
                "message": "Database is already empty (0 vectors)"
            }
        
        # Delete all
        index.delete(delete_all=True)
        
        logger.info(f"Deleted all {total_vectors} vectors")
        
        return {
            "status": "success",
            "message": f"Deleted all documents ({total_vectors} vectors)"
        }
    except Exception as e:
        error_msg = str(e)
        # Handle namespace not found (no data uploaded yet)
        if "Namespace not found" in error_msg or "404" in error_msg:
            return {
                "status": "success",
                "message": "Database is already empty (0 vectors)"
            }
        logger.error(f"Error deleting all documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
