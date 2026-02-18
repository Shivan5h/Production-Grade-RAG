"""
Configuration module for the RAG system.
Loads environment variables and provides centralized configuration.
"""
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    

    # HuggingFace Configuration (Embeddings)
    huggingface_api_key: str = Field(default="", alias="HUGGINGFACE_API_KEY")
    huggingface_embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        alias="HUGGINGFACE_EMBEDDING_MODEL"
    )
    
    # Groq Configuration (Main LLM)
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.1-70b-versatile",
        alias="GROQ_MODEL"
    )
    
    # Pinecone Configuration (Vector Database)
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field(
        default="imf-reports",
        alias="PINECONE_INDEX_NAME"
    )
    pinecone_dimension: int = Field(default=768, alias="PINECONE_DIMENSION")
    pinecone_cloud: str = Field(default="aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_REGION")
    
    # Chunking Configuration
    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    min_chunk_size: int = Field(default=100, alias="MIN_CHUNK_SIZE")
    
    # Retrieval Configuration
    top_k_results: int = Field(default=5, alias="TOP_K_RESULTS")
    similarity_threshold: float = Field(default=0.7, alias="SIMILARITY_THRESHOLD")
    max_tokens_context: int = Field(default=3000, alias="MAX_TOKENS_CONTEXT")
    
    # LLM Generation Configuration
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_top_p: float = Field(default=0.95, alias="LLM_TOP_P")
    llm_max_tokens: int = Field(default=1000, alias="LLM_MAX_TOKENS")
    
    # Upload Configuration
    max_upload_size: int = Field(default=10485760, alias="MAX_UPLOAD_SIZE")  # 10MB
    allowed_extensions: str = Field(
        default="pdf,docx,txt,md",
        alias="ALLOWED_EXTENSIONS"
    )
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    
    class Config:
        # Get the root directory (2 levels up from this file)
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed file extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir)


# Global settings instance
settings = Settings()

# Ensure required directories exist
settings.upload_path.mkdir(parents=True, exist_ok=True)
