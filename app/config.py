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
    GRAPH_DB_PATH: str = str(Path("data/code_graph.db"))
    
    # Embedding model (Ollama - local)
    EMBEDDING_MODEL: str = "nomic-embed-text:v1.5"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # LLM Provider settings
    LLM_PROVIDER: str = "ollama"  # "ollama" ou "gemini"
    
    # Ollama settings (se usar local)
    OLLAMA_MODEL: str = "qwen3:1.7b"
    
    # Gemini settings (se usar remoto)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"  # ou gemini-1.5-pro
    
    # Indexing settings
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # CodeSplitter settings (para chunking semântico de código)
    USE_CODE_SPLITTER: bool = True  # Se True, usa CodeSplitter para arquivos de código
    CODE_CHUNK_LINES: int = 40  # Número de linhas por chunk de código
    CODE_CHUNK_OVERLAP: int = 15  # Sobreposição entre chunks
    CODE_MAX_CHARS: int = 1500  # Limite máximo de caracteres por chunk
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Query settings
    SIMILARITY_TOP_K: int = 5
    
    class Config:
        # Caminho absoluto do arquivo .env (na raiz do projeto)
        env_file = str(Path(__file__).parent.parent / ".env")
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Create singleton instance
settings = get_settings()

# Ensure data directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
