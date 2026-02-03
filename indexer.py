from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from app.config import *

def index_repository(repo_path: str):
    documents = SimpleDirectoryReader(
        input_dir=repo_path,
        recursive=True,
        required_exts=ALLOWED_EXTENSIONS
    ).load_data()

    embed_model = OllamaEmbedding(model_name=EMBED_MODEL)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("codebase")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model,
        vector_store=vector_store
    )

    return index
