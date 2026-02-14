"""
Indexer module for indexing code repositories with unified vector + graph indexing.
"""
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from fnmatch import fnmatch
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings as LlamaSettings,
    Document,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
import chromadb
import os

from app.config import settings
from app.code_graph import CodeGraphBuilder
from app.graph_storage import GraphStorage

# Importar tree-sitter corretamente
try:
    from tree_sitter_languages import get_language, get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class CodeIndexer:
    """Indexes code repositories for RAG."""
    
    # Supported code file extensions and their languages
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.cs': 'c-sharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
    }
    
    # Non-code files (use SentenceSplitter)
    TEXT_EXTENSIONS = {
        '.md', '.txt', '.json', '.yaml', '.yml', '.xml', 
        '.html', '.css', '.sh', '.bat', '.ps1', '.sql',
        '.r', '.m', '.gradle', '.properties', '.toml', '.ini',
        '.conf', '.cfg', '.env', '.dockerignore', '.gitignore'
    }
    
    def __init__(self):
        """Initialize the indexer."""
        # Set up embedding model (Ollama)
        self.embed_model = OllamaEmbedding(
            model_name=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        
        # Configure LlamaIndex settings
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.chunk_size = settings.CHUNK_SIZE
        LlamaSettings.chunk_overlap = settings.CHUNK_OVERLAP
        
        # Set up ChromaDB client (com telemetria desabilitada)
        self.chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Set up Graph Storage
        self.graph_storage = GraphStorage(db_path=str(settings.GRAPH_DB_PATH))
        self.graph_builder = CodeGraphBuilder(graph_storage=self.graph_storage)
        
        # Cache de splitters por linguagem
        self._code_splitters: Dict[str, CodeSplitter] = {}
        
        # Fallback splitter para arquivos não-código
        self._fallback_splitter = SentenceSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
    
    def _get_code_splitter(self, language: str) -> CodeSplitter:
        """Get or create a CodeSplitter for a specific language."""
        if language not in self._code_splitters:
            if not TREE_SITTER_AVAILABLE:
                print(f"⚠️  tree-sitter-languages não disponível, usando SentenceSplitter")
                return self._fallback_splitter
            
            try:
                # Tentar criar parser manualmente
                parser = get_parser(language)
                
                self._code_splitters[language] = CodeSplitter(
                    language=language,
                    parser=parser,  # Passa o parser pronto
                    chunk_lines=settings.CODE_CHUNK_LINES,
                    chunk_lines_overlap=settings.CODE_CHUNK_OVERLAP,
                    max_chars=settings.CODE_MAX_CHARS
                )
                print(f"✓ CodeSplitter criado para {language}")
            except Exception as e:
                print(f"⚠️  CodeSplitter erro para {language}: {type(e).__name__}: {str(e)}")
                print(f"    Usando SentenceSplitter como fallback")
                return self._fallback_splitter
        return self._code_splitters[language]
    
    def index_repository(
        self, 
        repo_path: str,
        collection_name: str = "code_repository",
        exclude_dirs: Optional[List[str]] = None
    ) -> Tuple[VectorStoreIndex, Dict]:
        """
        Index a code repository with unified vector + graph indexing.
        
        This method performs a single repository walk, processing files for:
        1. Vector indexing (via CodeSplitter) → ChromaDB
        2. Graph extraction (via AST) → SQLite
        
        Args:
            repo_path: Path to the repository to index
            collection_name: Name for the ChromaDB collection
            exclude_dirs: List of directory names to exclude
            
        Returns:
            Tuple of (VectorStoreIndex, stats_dict)
            where stats_dict contains:
                - vector_chunks: int, total chunks created
                - graph_nodes: int, total nodes extracted
                - graph_edges: int, total edges extracted
                - files_processed: int, total files indexed
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
        
        print(f"\n{'='*60}")
        print(f"🚀 Indexing repository: {repo_path}")
        print(f"📚 Collection: {collection_name}")
        print(f"{'='*60}\n")
        
        # Clear previous graph data for this collection
        self.graph_storage.clear_graphs(collection_name)
        
        # Delete existing vector collection if it exists (reindex clean)
        try:
            self.chroma_client.delete_collection(name=collection_name)
            print(f"♻️  Cleared existing collection '{collection_name}' for clean reindex")
        except Exception:
            print(f"📁 Creating new collection '{collection_name}'")
        
        # SINGLE WALK: Collect all files in one pass
        code_files = []
        text_files = []
        all_extensions = set(self.LANGUAGE_MAP.keys()) | self.TEXT_EXTENSIONS
        
        for root, dirs, files in os.walk(repo_path):
            # Filter out excluded directories (supports wildcards)
            dirs[:] = [
                d for d in dirs 
                if not any(fnmatch(d, pattern) for pattern in exclude_dirs)
            ]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip excluded file patterns
                if any(fnmatch(file, pattern) for pattern in exclude_dirs):
                    continue
                
                # Only index supported files
                if file_path.suffix in all_extensions:
                    if file_path.suffix in self.LANGUAGE_MAP:
                        code_files.append(file_path)
                    else:
                        text_files.append(file_path)
        
        total_files = len(code_files) + len(text_files)
        print(f"Found {len(code_files)} code files + {len(text_files)} text files")
        print(f"Total: {total_files} files\n")
        
        if not total_files:
            raise ValueError("No code files found to index")
        
        # Initialize statistics
        documents = []
        total_vector_chunks = 0
        total_graph_nodes = 0
        total_graph_edges = 0
        
        # ===== UNIFIED PROCESSING: CODE FILES =====
        # Process code files for BOTH vector chunks AND graph relations (same loop)
        print("📝 Processing code files (vector + graph):")
        print("-" * 60)
        
        for file_path in code_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                rel_path = str(file_path.relative_to(repo_path))
                language = self.LANGUAGE_MAP.get(file_path.suffix, "python")
                
                # VECTOR INDEXING
                doc = Document(
                    text=content,
                    metadata={
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'relative_path': rel_path,
                        'collection': collection_name
                    }
                )
                
                splitter = self._get_code_splitter(language)
                chunks = splitter.get_nodes_from_documents([doc])
                documents.extend(chunks)
                vector_chunks = len(chunks)
                total_vector_chunks += vector_chunks
                
                # GRAPH INDEXING (same iteration)
                graph_nodes, graph_edges = self.graph_builder.analyze_file(
                    file_path=str(file_path),
                    content=content,
                    language=language,
                    collection_name=collection_name
                )
                total_graph_nodes += graph_nodes
                total_graph_edges += graph_edges
                
                print(f"  ✓ {rel_path}")
                print(f"    └─ Vector: {vector_chunks} chunks | Graph: {graph_nodes} nodes, {graph_edges} edges")
                
            except Exception as e:
                print(f"  ✗ {file_path}: {e}")
                continue
        
        # ===== TEXT FILES: Vector only (no graph extraction) =====
        print(f"\n📖 Processing text files (vector only):")
        print("-" * 60)
        
        for file_path in text_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                rel_path = str(file_path.relative_to(repo_path))
                
                doc = Document(
                    text=content,
                    metadata={
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_type': file_path.suffix,
                        'relative_path': rel_path,
                        'collection': collection_name
                    }
                )
                
                chunks = self._fallback_splitter.get_nodes_from_documents([doc])
                documents.extend(chunks)
                vector_chunks = len(chunks)
                total_vector_chunks += vector_chunks
                
                print(f"  ✓ {rel_path}: {vector_chunks} chunks")
                
            except Exception as e:
                print(f"  ✗ {file_path}: {e}")
                continue
        
        # ===== CREATE VECTOR INDEX =====
        print(f"\n{'='*60}")
        print(f"📊 Statistics:")
        print(f"  • Files processed: {total_files}")
        print(f"  • Vector chunks: {total_vector_chunks}")
        print(f"  • Graph nodes: {total_graph_nodes}")
        print(f"  • Graph edges: {total_graph_edges}")
        print(f"{'='*60}\n")
        
        print("🔍 Creating vector index...")
        chroma_collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )
        
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex(
            nodes=documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print("\n✅ Indexing complete!\n")
        
        stats = {
            "vector_chunks": total_vector_chunks,
            "graph_nodes": total_graph_nodes,
            "graph_edges": total_graph_edges,
            "files_processed": total_files,
            "collection_name": collection_name
        }
        
        return index, stats
    
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
