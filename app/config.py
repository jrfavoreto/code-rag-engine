"""
Configuration module for the Code RAG Engine.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Paths
    DATA_DIR: Path = Path("data")
    CHROMA_DIR: Path = Path("data/chroma")
    
    # Embedding model
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    
    # LLM settings (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # Indexing settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Query settings
    SIMILARITY_TOP_K: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Create singleton instance
settings = get_settings()

# Ensure data directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
