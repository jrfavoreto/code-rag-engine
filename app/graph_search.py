"""
Graph Search: Query engine para grafo de dependências.

Suporta queries como:
- "Quem chama compress_pdf()?"
- "Qual é a cadeia de chamadas?"
- "O que compress_pdf() importa?"
"""
from typing import List, Dict, Any
from app.graph_storage import GraphStorage
from app.query_classifier import QueryType


class GraphSearchEngine:
    """Query engine para buscar relações no grafo."""
    
    def __init__(self, graph_storage: GraphStorage = None):
        """
        Inicializa o search engine.
        
        Args:
            graph_storage: Instância de GraphStorage
        """
        if graph_storage is None:
            graph_storage = GraphStorage()
        
        self.storage = graph_storage
    
    def find_callers(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Encontra todas as funções que chamam uma função específica.
        
        Args:
            function_name: Nome da função a buscar (ex: 'compress_pdf')
        
        Returns:
            Lista de funções que chamam a função especificada
        """
        # Etapa 1: Encontrar o node pela função
        all_nodes = self.storage.get_all_nodes(node_type="function")
        
        if not all_nodes:
            return []
        
        target_node = None
        for node in all_nodes:
            if node.get('name') == function_name:
                target_node = node
                break
        
        if not target_node:
            print(f"DEBUG: Função '{function_name}' não encontrada")
            print(f"DEBUG: Funções disponíveis: {[n.get('name') for n in all_nodes[:5]]}")
            return []
        
        print(f"DEBUG: Encontrado nó alvo: {target_node.get('id')}")
        
        # Etapa 2: Encontrar predecessores (quem chama esta função)
        # predecessores = nós que TÊM uma aresta PARA este nó
        callers = self.storage.get_predecessors(target_node['id'], relation_type='calls')
        
        print(f"DEBUG: Predecessores encontrados: {len(callers) if callers else 0}")
        if callers:
            print(f"DEBUG: {[c.get('name') for c in callers]}")
        
        return callers if callers else []



    def find_calls(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Encontra todas as funções que uma função específica chama.
        
        Args:
            function_name: Nome da função a buscar (ex: 'compress_pdf')
        
        Returns:
            Lista de funções que são chamadas por essa função
        """
        # Etapa 1: Encontrar o node pela função
        all_nodes = self.storage.get_all_nodes(node_type="function")
        source_node = None
        
        if all_nodes:
            for node in all_nodes:
                if node.get('name') == function_name:
                    source_node = node
                    break
        
        if not source_node:
            return []
        
        # Etapa 2: Encontrar sucessores (o que esta função chama)
        calls = self.storage.get_successors(source_node['id'], relation_type='calls')
        
        return calls if calls else []


    def find_call_chain(self, function_name: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """
        Encontra a cadeia completa de chamadas (BFS - busca em largura).
        
        Args:
            function_name: Nome da função para iniciar a busca
            max_depth: Profundidade máxima da cadeia
            
        Returns:
            Lista com a cadeia de chamadas
        """
        # Etapa 1: Encontrar o node da função inicial
        all_nodes = self.storage.get_all_nodes(node_type="function")
        start_node = None
        
        if all_nodes:
            for node in all_nodes:
                if node.get('name') == function_name:
                    start_node = node
                    break
        
        if not start_node:
            return []
        
        # Etapa 2: Usar o método get_call_chain do storage
        chain_tuples = self.storage.get_call_chain(start_node['id'], max_depth=max_depth)
        
        if not chain_tuples:
            return []
        
        # Converter tuplas em dicts com informações dos nodes
        chain = []
        for source_id, target_id in chain_tuples:
            source_node = self.storage.get_node(source_id)
            target_node = self.storage.get_node(target_id)
            
            chain.append({
                'from': source_node.get('name', source_id) if source_node else str(source_id),
                'to': target_node.get('name', target_id) if target_node else str(target_id),
                'source_id': source_id,
                'target_id': target_id
            })
        
        return chain


    def get_impact_analysis(self, function_name: str) -> List[Dict[str, Any]]:
        """
        Análise de impacto: mostra quem chama e o que a função chama.
        
        Args:
            function_name: Nome da função
            
        Returns:
            Lista com análise de impacto
        """
        impact = []
        
        # Encontrar a função
        all_nodes = self.storage.get_all_nodes(node_type="function")
        func_node = None
        
        if all_nodes:
            for node in all_nodes:
                if node.get('name') == function_name:
                    func_node = node
                    break
        
        if not func_node:
            return []
        
        # Adicionar a função em si
        impact.append({
            'type': 'self',
            'name': func_node.get('name'),
            'id': func_node.get('id'),
            'signature': func_node.get('signature', '')
        })
        
        # Adicionar quem chama
        callers = self.find_callers(function_name)
        for caller in callers:
            impact.append({
                'type': 'caller',
                'name': caller.get('name'),
                'id': caller.get('id'),
                'signature': caller.get('signature', '')
            })
        
        # Adicionar o que é chamado
        calls = self.find_calls(function_name)
        for called in calls:
            impact.append({
                'type': 'called',
                'name': called.get('name'),
                'id': called.get('id'),
                'signature': called.get('signature', '')
            })
        
        return impact
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Processa uma query de grafo (GRAPH type).
        
        Args:
            query: Pergunta em linguagem natural
        
        Returns:
            Resultados da busca
        """
        query_lower = query.lower()
        
        # Extrair nome da função
        words = query_lower.split()
        function_name = None
        
        # Procurar padrões comuns
        for i, word in enumerate(words):
            if word in ["chama", "chamadas", "calls", "called"]:
                if i + 1 < len(words):
                    function_name = words[i + 1]
                break
            elif word in ["executa", "invoca"]:
                if i + 1 < len(words):
                    function_name = words[i + 1]
                break
        
        if not function_name:
            return {"error": "Não consegui identificar a função na query"}
        
        # Determinar tipo de query
        if "quem chama" in query_lower or "chamadores" in query_lower:
            results = self.find_callers(function_name)
            return {
                "type": "callers",
                "function": function_name,
                "results": results,
                "message": f"Funções que chamam {function_name}"
            }
        
        elif "cadeia" in query_lower or "call chain" in query_lower:
            results = self.find_call_chain(function_name)
            return {
                "type": "call_chain",
                "function": function_name,
                "results": results,
                "message": f"Cadeia de chamadas de {function_name}"
            }
        
        elif "impacto" in query_lower or "afeta" in query_lower:
            results = self.get_impact_analysis(function_name)
            return {
                "type": "impact",
                "function": function_name,
                "results": results,
                "message": f"Análise de impacto de {function_name}"
            }
        
        else:
            # Default: mostrar o que a função chama
            results = self.find_calls(function_name)
            return {
                "type": "calls",
                "function": function_name,
                "results": results,
                "message": f"Funções chamadas por {function_name}"
            }
