from llama_index.core import VectorStoreIndex
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from app.config import *

def get_query_engine():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection("codebase")

    vector_store = ChromaVectorStore(chroma_collection=collection)

    embed_model = OllamaEmbedding(model_name=EMBED_MODEL)
    llm = Ollama(model=LLM_MODEL)

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model
    )

    return index.as_query_engine(
        llm=llm,
        similarity_top_k=5
    )
