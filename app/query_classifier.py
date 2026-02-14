"""
Query Classifier: Classifica o tipo de pergunta para rotear estratégia de busca.

Estratégias:
- SEMANTIC: Vector Search (como funciona, explique, validação)
- GRAPH: Graph Search (relações de código, chamadas, dependências)
- HYBRID: Combina ambas estratégias
"""
from enum import Enum
from typing import Dict, List


class QueryType(str, Enum):
    """Tipos de queries suportadas."""
    SEMANTIC = "semantic"  # Vector Search (contexto)
    GRAPH = "graph"        # Graph Search (relações)
    HYBRID = "hybrid"      # Ambas estratégias


class QueryClassifier:
    """Classifica queries para rotear estratégia de busca apropriada."""
    
    # Keywords que indicam queries de relações/grafo
    GRAPH_KEYWORDS = [
        "quem chama",
        "o que chama",
        "chama quais",
        "chama qual",
        "chama o que",
        "que chama",
        "chamada",
        "chamadas",
        "chamado por",
        "invoca",
        "invocado",
        "cadeia",
        "fluxo",
        "depende",
        "dependência",
        "dependências",
        "impacta",
        "impactado",
        "impacto",
        "afeta",
        "afetado",
        "executa antes",
        "executa depois",
        "relacionado",
        "relação",
        "referência",
        "importa",
        "é importado",
        "usa",
        "é usado",
        "utiliza",
        "utilizado",
        "call chain",
        "sequência",
        "ordem de execução",
        "hierarquia",
        "estrutura",
        "gráfico de chamadas",
    ]
    
    # Keywords que indicam queries semânticas
    SEMANTIC_KEYWORDS = [
        "como",
        "como funciona",
        "explique",
        "validação",
        "significa",
        "para que serve",
        "efeito",
        "resultado",
        "comportamento",
        "o que faz",
        "o que é",
        "descrição",
        "qual é",
        "por que",
        "porque",
        "quando",
        "condição",
        "algoritmo",
        "lógica",
        "implementação",
        "funcionalidade",
        "funcionamento",
        "propósito",
        "objetivo",
    ]
    
    # Keywords que indicam queries regex/literal
    REGEX_KEYWORDS = [
        "find",
        "match",
        "padrão",
        "regex",
        "expressão regular",
        "buscar",
        "procurar",
    ]
    
    @staticmethod
    def classify(query: str) -> QueryType:
        """
        Classifica uma query para determinar a estratégia de busca.
        
        Args:
            query: Texto da pergunta do usuário
            
        Returns:
            QueryType: Tipo de query (SEMANTIC, GRAPH, HYBRID)
        """
        query_lower = query.lower()
        
        # Contar matches para cada tipo
        graph_matches = sum(1 for kw in QueryClassifier.GRAPH_KEYWORDS if kw in query_lower)
        semantic_matches = sum(1 for kw in QueryClassifier.SEMANTIC_KEYWORDS if kw in query_lower)
        regex_matches = sum(1 for kw in QueryClassifier.REGEX_KEYWORDS if kw in query_lower)
        
        # Debug info
        matches_info = {
            "graph": graph_matches,
            "semantic": semantic_matches,
            "regex": regex_matches
        }
        
        # Decidir tipo baseado em pontuação
        if graph_matches > 0 and semantic_matches > 0:
            return QueryType.HYBRID
        elif graph_matches > 0:
            return QueryType.GRAPH
        elif semantic_matches > 0:
            return QueryType.SEMANTIC
        else:
            # Default para semantic (vector search é mais robusto)
            return QueryType.SEMANTIC
    
    @staticmethod
    def get_strategy_hint(query_type: QueryType) -> str:
        """Retorna dica sobre a estratégia a ser usada."""
        hints = {
            QueryType.SEMANTIC: "Usando Vector Search (contexto semântico)",
            QueryType.GRAPH: "Usando Graph Search (relações de código)",
            QueryType.HYBRID: "Usando Hybrid Search (contexto + relações)",
        }
        return hints.get(query_type, "Estratégia padrão")


class QueryMetadata:
    """Metadados sobre a query e sua classificação."""
    
    def __init__(self, query: str):
        self.query = query
        self.query_type = QueryClassifier.classify(query)
        self.strategy_hint = QueryClassifier.get_strategy_hint(self.query_type)
        self.keywords_found = self._extract_keywords()
    
    def _extract_keywords(self) -> Dict[str, List[str]]:
        """Extrai keywords encontradas na query."""
        query_lower = self.query.lower()
        result = {
            "graph": [],
            "semantic": [],
            "regex": []
        }
        
        for kw in QueryClassifier.GRAPH_KEYWORDS:
            if kw in query_lower:
                result["graph"].append(kw)
        
        for kw in QueryClassifier.SEMANTIC_KEYWORDS:
            if kw in query_lower:
                result["semantic"].append(kw)
        
        for kw in QueryClassifier.REGEX_KEYWORDS:
            if kw in query_lower:
                result["regex"].append(kw)
        
        return result
    
    def to_dict(self) -> dict:
        """Retorna metadados como dicionário."""
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "strategy_hint": self.strategy_hint,
            "keywords_found": self.keywords_found
        }
