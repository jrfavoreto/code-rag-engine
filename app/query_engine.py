"""
Query engine module for querying indexed code repositories.
"""
from typing import Optional, Dict, Any
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core import Settings as LlamaSettings
from llama_index.llms.ollama import Ollama

from app.config import settings
from app.indexer import CodeIndexer


class CodeQueryEngine:
    """Query engine for code repositories."""
    
    def __init__(
        self, 
        collection_name: str = "code_repository",
        use_ollama: bool = False
    ):
        """
        Initialize the query engine.
        
        Args:
            collection_name: Name of the ChromaDB collection
            use_ollama: Whether to use Ollama for LLM (optional)
        """
        self.collection_name = collection_name
        self.indexer = CodeIndexer()
        
        # Set up LLM if requested
        if use_ollama:
            self.llm = Ollama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL
            )
            LlamaSettings.llm = self.llm
        else:
            # Just retrieve context without LLM
            self.llm = None
        
        # Load the index
        try:
            self.index = self.indexer.load_index(collection_name)
            print(f"Loaded index from collection: {collection_name}")
        except Exception as e:
            raise ValueError(
                f"Could not load index '{collection_name}'. "
                f"Please index a repository first. Error: {e}"
            )
    
    def query(
        self, 
        query: str, 
        similarity_top_k: Optional[int] = None,
        return_context_only: bool = False
    ) -> Dict[str, Any]:
        """
        Query the indexed code repository.
        
        Args:
            query: The query string
            similarity_top_k: Number of similar chunks to retrieve
            return_context_only: If True, only return context without LLM response
            
        Returns:
            Dictionary containing the response and/or context
        """
        if similarity_top_k is None:
            similarity_top_k = settings.SIMILARITY_TOP_K
        
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        # Retrieve relevant nodes
        nodes = retriever.retrieve(query)
        
        # Format context
        context = []
        for i, node in enumerate(nodes):
            context.append({
                'rank': i + 1,
                'file_path': node.metadata.get('file_path', 'unknown'),
                'file_name': node.metadata.get('file_name', 'unknown'),
                'file_type': node.metadata.get('file_type', 'unknown'),
                'score': node.score,
                'text': node.text
            })
        
        result = {
            'query': query,
            'context': context,
            'num_results': len(context)
        }
        
        # If return_context_only, just return the context
        if return_context_only or self.llm is None:
            return result
        
        # Otherwise, use LLM to generate a response
        response_synthesizer = get_response_synthesizer(
            response_mode="compact"
        )
        
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
        
        response = query_engine.query(query)
        result['response'] = str(response)
        
        return result
    
    def retrieve_context(
        self,
        query: str,
        similarity_top_k: Optional[int] = None
    ) -> str:
        """
        Retrieve only the relevant context as a formatted string.
        This is useful for passing to external LLMs.
        
        Args:
            query: The query string
            similarity_top_k: Number of similar chunks to retrieve
            
        Returns:
            Formatted string with relevant code context
        """
        result = self.query(
            query=query,
            similarity_top_k=similarity_top_k,
            return_context_only=True
        )
        
        # Format context as a readable string
        formatted = f"Query: {query}\n\n"
        formatted += f"Relevant Code Context ({result['num_results']} results):\n\n"
        
        for ctx in result['context']:
            formatted += f"--- File: {ctx['file_path']} (Relevance: {ctx['score']:.3f}) ---\n"
            formatted += ctx['text']
            formatted += "\n\n"
        
        return formatted
