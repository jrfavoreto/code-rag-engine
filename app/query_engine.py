"""
Query engine module for querying indexed code repositories.
"""
from typing import Optional, Dict, Any, List
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core import Settings as LlamaSettings
from llama_index.llms.ollama import Ollama

from app.config import settings
from app.indexer import CodeIndexer
from app.query_classifier import QueryClassifier, QueryMetadata, QueryType
from app.graph_search import GraphSearchEngine
from app.graph_storage import GraphStorage
from app.llm_provider import get_llm_provider


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
        self.query_classifier = QueryClassifier()
        
        # Set up LLM Provider
        try:
            self.llm_provider = get_llm_provider()
            print(f"✅ LLM Provider inicializado: {settings.LLM_PROVIDER}")
        except Exception as e:
            print(f"⚠️  LLM Provider não disponível: {e}")
            self.llm_provider = None
        
        # Set up Graph Search
        try:
            self.graph_storage = GraphStorage(db_path=str(settings.GRAPH_DB_PATH))
            self.graph_search = GraphSearchEngine(
                graph_storage=self.graph_storage
            )
        except Exception as e:
            print(f"⚠️  Graph Search não disponível: {e}")
            self.graph_storage = None
            self.graph_search = None
        
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
            print(f"✅ Índice carregado da coleção: {collection_name}")
        except Exception as e:
            raise ValueError(
                f"Não foi possível carregar o índice '{collection_name}'. "
                f"Por favor, indexe um repositório primeiro. Erro: {e}"
            )
    
    def query(
        self,
        query: str,
        similarity_top_k: int = 5,
        return_context_only: bool = True,
        show_classifier_info: bool = True
    ) -> Dict[str, Any]:
        """
        Executa consulta com roteamento inteligente (semantic/graph/hybrid).
        
        Args:
            query: Consulta do usuário
            similarity_top_k: Número de chunks semânticos a recuperar
            return_context_only: Se False, gera resposta com LLM
            show_classifier_info: Se True, inclui info de classificação
        
        Returns:
            Dict com resultados e metadados
        """
        # Etapa 1: Classificar query
        query_type = self.query_classifier.classify(query)
        
        result = {
            "query": query,
            "query_classification": None,
            "semantic_results": None,
            "semantic_count": None,
            "graph_results": None,
            "graph_count": None,
            "graph_type": None,
            "response": None
        }
        
        if show_classifier_info:
            result["query_classification"] = {
                "tipo": query_type.value,
                "estrategia": "Vector Search" if query_type == QueryType.SEMANTIC else (
                    "Graph Search" if query_type == QueryType.GRAPH else "Vector + Graph"
                )
            }
        
        # Etapa 2: Executar busca apropriada
        if query_type in [QueryType.SEMANTIC, QueryType.HYBRID]:
            semantic_result = self._semantic_search(
                query=query,
                similarity_top_k=similarity_top_k
            )
            result["semantic_results"] = semantic_result.get("context") or []
            result["semantic_count"] = len(result["semantic_results"])
        
        if query_type in [QueryType.GRAPH, QueryType.HYBRID]:
            graph_result = self._graph_search(query)
            result["graph_results"] = graph_result.get("results") or []
            result["graph_count"] = len(result["graph_results"])
            result["graph_type"] = graph_result.get("type")
        
        # Etapa 3: Gerar resposta com LLM se solicitado
        if not return_context_only:
            if self.llm_provider is None:
                result["response"] = "LLM não disponível. Configure GEMINI_API_KEY ou instale Ollama."
            else:
                try:
                    print(f"🔍 DEBUG: return_context_only={return_context_only}, llm_provider={self.llm_provider}")
                    
                    context_text = self._build_context_for_llm(result)
                    print(f"🔍 DEBUG: Context length={len(context_text)}")
                    
                    if context_text.strip():
                        print(f"🔍 DEBUG: Chamando LLM...")
                        prompt = self._build_prompt(context_text, query)
                        llm_response = self.llm_provider.generate(prompt)
                        print(f"🔍 DEBUG: LLM response length={len(llm_response)}")
                        result["response"] = llm_response
                    else:
                        result["response"] = "Nenhum contexto relevante encontrado para responder à pergunta."
                except Exception as e:
                    print(f"❌ Erro ao gerar resposta LLM: {e}")
                    import traceback
                    traceback.print_exc()
                    result["response"] = f"Erro ao gerar resposta: {str(e)}"
        
        return result
    
    def _semantic_search(
        self,
        query: str,
        similarity_top_k: int,
        min_score: float = 0.0,
        max_context_chars: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute Vector Search and return context."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=similarity_top_k
        )
        
        nodes = retriever.retrieve(query)
        
        context = []
        total_chars = 0
        
        for i, node in enumerate(nodes):
            # Filtrar por score mínimo
            if node.score < min_score:
                continue
            
            # Verificar limite de caracteres
            if max_context_chars is not None:
                chunk_size = len(node.text)
                if total_chars + chunk_size > max_context_chars:
                    break
                total_chars += chunk_size
            
            context.append({
                'rank': len(context) + 1,
                'file_path': node.metadata.get('file_path', 'unknown'),
                'file_name': node.metadata.get('file_name', 'unknown'),
                'file_type': node.metadata.get('file_type', 'unknown'),
                'score': node.score,
                'text': node.text
            })
        
        return {
            'context': context,
            'count': len(context)
        }
    
    def _graph_search(self, query: str) -> Dict[str, Any]:
        """Execute Graph Search e retorna relações de código."""
        if not self.graph_search:
            return {'results': None, 'count': None, 'type': None}
        
        # Detectar tipo de query de grafo
        query_lower = query.lower()
        
        # Extrair nome da função usando padrões melhorados
        import re
        
        func_name = self._extract_function_name(query)
        
        # Se não conseguiu extrair nome de função explícito, retornar None
        # (Graph Search requer nome de função específico)
        if not func_name or len(func_name) < 2:
            return {'results': None, 'count': None, 'type': None}
        
        # Detectar tipo de query baseado em palavras-chave
        if "quem chama" in query_lower or "chamado por" in query_lower or "chamadores" in query_lower:
            # "Quem chama compress_pdf?" → find_callers
            results = self.graph_search.find_callers(func_name)
            result_type = "callers"
            
        elif "chama quais" in query_lower or "chama qual" in query_lower or "chama o que" in query_lower or "o que chama" in query_lower:
            # "compress_pdf chama quais funções?" → find_calls
            results = self.graph_search.find_calls(func_name)
            result_type = "calls"
            
        elif "cadeia" in query_lower or "fluxo" in query_lower or "chain" in query_lower:
            results = self.graph_search.find_call_chain(func_name)
            result_type = "chain"
            
        else:
            # Análise de impacto por padrão
            results = self.graph_search.get_impact_analysis(func_name)
            result_type = "impact"
        
        return {
            'results': results,
            'count': len(results) if results else 0,
            'type': result_type
        }
    
    def _extract_function_name(self, query: str) -> str:
        """
        Extrai nome da função de uma query.
        
        Exemplos:
        - "Quem chama compress_pdf?" → "compress_pdf"
        - "compress_pdf chama quais funções?" → "compress_pdf"
        - "O que compress_pdf chama?" → "compress_pdf"
        """
        import re
        
        # Padrão 1: Procurar por identificadores válidos em Python (func_name, func_name())
        pattern_with_parens = r'(\w+)\s*\(\s*\)'
        match = re.search(pattern_with_parens, query)
        if match:
            return match.group(1)
        
        # Padrão 2: Função DEPOIS de keywords ("quem chama compress_pdf")
        # ⚠️ Este deve vir ANTES do padrão "função ANTES de keyword"
        after_patterns = [
            r'chama\s+(?:a\s+)?(?:função\s+)?(\w+)',     # "quem chama compress_pdf" ou "quem chama a função compress_pdf"
            r'invoca\s+(?:a\s+)?(?:função\s+)?(\w+)',
            r'usa\s+(?:a\s+)?(?:função\s+)?(\w+)',
            r'depende\s+de\s+(\w+)',
        ]
        
        for pattern in after_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                candidate = match.group(1)
                # Verificar se não é palavra comum
                if candidate.lower() not in ['função', 'funções', 'qual', 'quais', 'que', 'o', 'a']:
                    return candidate
        
        # Padrão 3: Função ANTES de keywords ("compress_pdf chama...")
        before_patterns = [
            r'(\w+)\s+chama\s+(?:quais|qual|o\s+que)',  # "compress_pdf chama quais"
            r'(\w+)\s+invoca',
            r'(\w+)\s+usa',
            r'(\w+)\s+depende',
        ]
        
        for pattern in before_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                candidate = match.group(1)
                # Verificar se não é palavra comum/keyword
                if candidate.lower() not in ['quem', 'o', 'que', 'qual', 'quais', 'função', 'funções']:
                    return candidate
        
        # Padrão 4: Identificador seguido de '?' ou fim de string
        pattern_word = r'(\w+)\s*\)?(\s*\?)?$'
        match = re.search(pattern_word, query)
        if match:
            candidate = match.group(1)
            # Evitar pegar palavras comuns
            if candidate.lower() not in ['função', 'funções', 'qual', 'quais', 'que']:
                return candidate
        
        # Fallback: pegar palavra que parece um identificador (não palavra comum)
        words = query.replace("?", "").replace("(", "").replace(")", "").split()
        common_words = {'quem', 'o', 'que', 'qual', 'quais', 'função', 'funções', 'chama', 'a', 'de'}
        
        for word in reversed(words):
            if word and word[0].isalpha() and word.lower() not in common_words:
                return word
        
        return ""

    def _build_context_for_llm(self, result: Dict[str, Any]) -> str:
        """
        Constrói contexto formatado para o LLM a partir dos resultados.
        
        Prioriza resultados de grafo (precisos) sobre resultados semânticos.
        
        Args:
            result: Dicionário com semantic_results, graph_results, etc.
            
        Returns:
            String formatada com o contexto
        """
        context_parts = []
        
        # Extrair nome da função da query original (se existir)
        query_str = result.get("query", "")
        func_name = self._extract_function_name(query_str) if query_str else ""
        
        # 1. Adicionar resultados de grafo primeiro (mais precisos)
        if result.get("graph_results") and result.get("graph_count", 0) > 0:
            context_parts.append("### ANÁLISE DE RELAÇÕES DE CÓDIGO\n")
            
            graph_type = result.get("graph_type", "unknown")
            graph_results = result["graph_results"]
            
            if graph_type == "callers":
                if func_name:
                    context_parts.append(f"**Funções que CHAMAM `{func_name}()`:**\n")
                else:
                    context_parts.append("**Funções que CHAMAM a função consultada:**\n")
            elif graph_type == "calls":
                if func_name:
                    context_parts.append(f"**Funções CHAMADAS por `{func_name}()`:**\n")
                else:
                    context_parts.append("**Funções CHAMADAS pela função consultada:**\n")
            elif graph_type == "chain":
                context_parts.append("**Cadeia de chamadas:**\n")
            else:
                context_parts.append("**Análise de impacto:**\n")
            
            for idx, item in enumerate(graph_results, 1):
                if isinstance(item, dict):
                    name = item.get("name", "unknown")
                    node_type = item.get("type", "function")
                    file_path = item.get("file_path", "")
                    context_parts.append(f"{idx}. `{name}` ({node_type}) - {file_path}\n")
                else:
                    context_parts.append(f"{idx}. {item}\n")
            
            context_parts.append("\n")
        
        # 2. Adicionar resultados semânticos (contexto de código)
        if result.get("semantic_results") and result.get("semantic_count", 0) > 0:
            context_parts.append("### TRECHOS DE CÓDIGO RELEVANTES\n\n")
            
            for idx, item in enumerate(result["semantic_results"], 1):
                file_path = item.get("file_path", "unknown")
                text = item.get("text", "")
                score = item.get("score", 0.0)
                
                context_parts.append(f"**[{idx}] {file_path}** (relevância: {score:.2f})\n")
                context_parts.append("```python\n")
                context_parts.append(text)
                context_parts.append("\n```\n\n")
        
        return "".join(context_parts)

    def _build_prompt(self, context: str, query: str) -> str:
        """
        Constrói prompt estruturado para o LLM.
        
        Args:
            context: Contexto formatado (código + relações)
            query: Pergunta do usuário
            
        Returns:
            Prompt completo para o LLM
        """
        prompt = f"""Você é um assistente especializado em análise de código Python.

**CONTEXTO RECUPERADO:**
{context}

**PERGUNTA DO USUÁRIO:**
{query}

**INSTRUÇÕES:**
1. Use APENAS as informações fornecidas acima no contexto
2. Se a resposta não estiver no contexto, diga "Não tenho informações suficientes"
3. Cite especificamente funções, arquivos e relacionamentos mencionados
4. Seja preciso e objetivo
5. Use linguagem técnica apropriada

**RESPOSTA:**"""
        
        return prompt

    def retrieve_context(
        self,
        query: str,
        similarity_top_k: int = 5,
        min_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Recupera apenas contexto de código relevante (sem classificação/análise).
        
        Útil para:
        - Integração com LLMs externos
        - Debug e visualização
        - Uso direto do contexto em outras aplicações
        
        Args:
            query: Consulta do usuário
            similarity_top_k: Número de chunks a recuperar
            min_score: Score mínimo de relevância (0.0-1.0)
            
        Returns:
            Dict com contexto recuperado e metadados
        """
        return self._semantic_search(
            query=query,
            similarity_top_k=similarity_top_k,
            min_score=min_score
        )


if __name__ == "__main__":
    # Test do query engine
    engine = CodeQueryEngine(collection_name="img_converter")
    
    # Teste 1: Query semântica
    print("\n=== Teste 1: Query Semântica ===")
    result = engine.query("Como funciona a compressão de PDF?")
    print(f"Tipo: {result['query_classification']['tipo']}")
    print(f"Resultados semânticos: {result['semantic_count']}")
    
    # Teste 2: Query de grafo
    print("\n=== Teste 2: Query de Grafo ===")
    result = engine.query("Quem chama compress_pdf?")
    print(f"Tipo: {result['query_classification']['tipo']}")
    print(f"Resultados de grafo: {result['graph_count']}")
