"""FastAPI backend for Production RAG System.

Architecture:
- Lazy-loaded services (models load on first use)
- HuggingFace all-MiniLM-L6-v2 embeddings (384-dim)
- Pinecone vector database
- Groq Llama 3.3 70B for generation
"""
import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from routes.rag_routes import router as rag_router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
uploads_dir = project_root / "uploads"
uploads_dir.mkdir(exist_ok=True)


app = FastAPI(
    title="Production RAG System",
    description="FastAPI backend with lazy-loaded services and Groq LLM",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag_router, prefix="/api", tags=["RAG"])


@app.get("/")
async def root():
    return {
        "message": "Production RAG System API",
        "version": "3.0.0",
        "frontend": "Streamlit on port 8502",
        "docs": "/docs"
    }


@app.get("/api")
async def api_info():
    return {
        "message": "Production RAG System API",
        "version": "3.0.0",
        "endpoints": {
            "upload": "/api/upload",
            "query": "/api/query",
            "compare": "/api/compare"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for production monitoring.
    
    Returns system status and component availability.
    """
    try:
        # Check vector DB connection
        from services.vectorstore.pinecone_manager import VectorDatabaseManager
        vector_db = VectorDatabaseManager()
        index_stats = vector_db.db.get_index().describe_index_stats()
        vector_count = index_stats.get('total_vector_count', 0)
        
        return {
            "status": "healthy",
            "model": settings.groq_model,
            "embedding_model": settings.huggingface_embedding_model,
            "vector_db": "Pinecone",
            "vector_count": vector_count,
            "timestamp": "2026-02-18"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": "2026-02-18"
        }


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting AI RAG System...")
    logger.info("📍 Web UI: http://localhost:8000")
    logger.info("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
