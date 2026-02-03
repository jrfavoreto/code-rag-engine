"""
Indexer module for indexing code repositories.
"""
import os
from pathlib import Path
from typing import List, Optional
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings as LlamaSettings,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb

from app.config import settings


class CodeIndexer:
    """Indexes code repositories for RAG."""
    
    # Common code file extensions
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
        ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".r",
        ".m", ".sh", ".bash", ".sql", ".html", ".css", ".scss", ".sass",
        ".json", ".yaml", ".yml", ".xml", ".md", ".txt", ".toml", ".ini",
        ".cfg", ".conf", ".env.example"
    }
    
    def __init__(self):
        """Initialize the indexer."""
        # Set up embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name=settings.EMBEDDING_MODEL
        )
        
        # Configure LlamaIndex settings
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.chunk_size = settings.CHUNK_SIZE
        LlamaSettings.chunk_overlap = settings.CHUNK_OVERLAP
        
        # Set up ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR)
        )
        
    def index_repository(
        self, 
        repo_path: str,
        collection_name: str = "code_repository",
        exclude_dirs: Optional[List[str]] = None
    ) -> VectorStoreIndex:
        """
        Index a code repository.
        
        Args:
            repo_path: Path to the repository to index
            collection_name: Name for the ChromaDB collection
            exclude_dirs: List of directory names to exclude
            
        Returns:
            VectorStoreIndex: The created index
        """
        repo_path = Path(repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        # Default exclusions
        if exclude_dirs is None:
            exclude_dirs = [
                "__pycache__", "node_modules", ".git", ".venv", "venv",
                "env", "build", "dist", ".pytest_cache", ".mypy_cache",
                ".tox", "htmlcov", ".eggs", "*.egg-info"
            ]
        
        print(f"Indexing repository: {repo_path}")
        print(f"Excluded directories: {exclude_dirs}")
        
        # Load documents from repository
        documents = []
        for root, dirs, files in os.walk(repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                # Only index code files
                if file_path.suffix in self.CODE_EXTENSIONS:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Create relative path for better context
                            rel_path = file_path.relative_to(repo_path)
                            documents.append({
                                'text': content,
                                'metadata': {
                                    'file_path': str(rel_path),
                                    'file_name': file,
                                    'file_type': file_path.suffix
                                }
                            })
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {e}")
        
        print(f"Found {len(documents)} code files to index")
        
        if not documents:
            raise ValueError("No code files found to index")
        
        # Convert to LlamaIndex documents
        from llama_index.core import Document
        llama_docs = [
            Document(
                text=doc['text'],
                metadata=doc['metadata']
            ) for doc in documents
        ]
        
        # Create or get ChromaDB collection
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass  # Collection doesn't exist
        
        chroma_collection = self.chroma_client.create_collection(
            name=collection_name
        )
        
        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create index
        print("Creating vector index...")
        index = VectorStoreIndex.from_documents(
            llama_docs,
            storage_context=storage_context,
            show_progress=True
        )
        
        print(f"Successfully indexed {len(documents)} files")
        return index
    
    def load_index(
        self, 
        collection_name: str = "code_repository"
    ) -> VectorStoreIndex:
        """
        Load an existing index from ChromaDB.
        
        Args:
            collection_name: Name of the ChromaDB collection
            
        Returns:
            VectorStoreIndex: The loaded index
        """
        # Get ChromaDB collection
        chroma_collection = self.chroma_client.get_collection(
            name=collection_name
        )
        
        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        # Load index
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store
        )
        
        return index
