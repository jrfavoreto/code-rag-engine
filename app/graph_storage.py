"""
Graph Storage: Persistência de grafo de dependências em SQLite.

Armazena:
- Nodes: Funções, classes, arquivos
- Edges: Relações (import, calls, inherits)
"""
import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict, Set, Any
import json
from datetime import datetime

from app.config import settings


class GraphStorage:
    """Gerencia persistência do grafo em SQLite."""
    
    def __init__(self, db_path: str = None):
        """
        Inicializa o storage do grafo.
        
        Args:
            db_path: Caminho para o banco de dados SQLite
        """
        if db_path is None:
            db_path = str(settings.DATA_DIR / "code_graph.db")
        
        self.db_path = db_path
        self._ensure_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com o banco de dados."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Retorna dicts ao invés de tuples
        return conn
    
    def _ensure_tables(self):
        """Cria tabelas se não existirem."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabela de nodes (funções, classes, arquivos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                signature TEXT,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de edges (relações entre nodes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_id) REFERENCES nodes(id),
                FOREIGN KEY(target_id) REFERENCES nodes(id),
                UNIQUE(source_id, target_id, relation_type)
            )
        """)
        
        # Tabela de metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_file ON nodes(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(relation_type)")
        
        conn.commit()
        conn.close()
    
    def clear(self):
        """Limpa o banco de dados completamente."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM edges")
        cursor.execute("DELETE FROM nodes")
        cursor.execute("DELETE FROM graph_metadata")
        conn.commit()
        conn.close()
    
    def clear_graphs(self, collection_name: str = None):
        """
        Limpa dados de um grafo específico ou todos os grafos.
        
        Args:
            collection_name: Nome da coleção (opcional)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if collection_name:
            # Limpar apenas grafo específico
            cursor.execute("""
                DELETE FROM nodes 
                WHERE metadata LIKE ?
            """, (f'%"{collection_name}"%',))
            cursor.execute("""
                DELETE FROM edges 
                WHERE (source_id LIKE ? OR target_id LIKE ?)
            """, (f'%:{collection_name}:%', f'%:{collection_name}:%'))
        else:
            # Limpar tudo
            cursor.execute("DELETE FROM edges")
            cursor.execute("DELETE FROM nodes")
            cursor.execute("DELETE FROM graph_metadata")
        
        conn.commit()
        conn.close()
    
    # ===== NODE OPERATIONS =====
    
    def add_node(self, node_id: str, name: str, node_type: str, 
                 file_path: str = None, line_number: int = None,
                 signature: str = None, metadata: dict = None):
        """
        Adiciona um node ao grafo.
        
        Args:
            node_id: Identificador único (ex: "module.function_name")
            name: Nome legível
            node_type: "function", "class", "module", "variable"
            file_path: Caminho do arquivo
            line_number: Número da linha
            signature: Assinatura da função/classe
            metadata: Metadados adicionais
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO nodes 
                (id, name, type, file_path, line_number, signature, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                node_id,
                name,
                node_type,
                file_path,
                line_number,
                signature,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_node(self, node_id: str) -> Dict:
        """Retorna um node pelo ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_nodes_by_file(self, file_path: str) -> List[Dict]:
        """Retorna todos os nodes de um arquivo."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM nodes WHERE file_path = ? ORDER BY line_number", (file_path,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_nodes(self, node_type: str = None) -> List[Dict]:
        """Retorna todos os nodes, opcionalmente filtrados por tipo."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if node_type:
            cursor.execute("SELECT * FROM nodes WHERE type = ?", (node_type,))
        else:
            cursor.execute("SELECT * FROM nodes")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ===== EDGE OPERATIONS =====
    
    def add_edge(self, source_id: str, target_id: str, relation_type: str, metadata: dict = None):
        """
        Adiciona uma aresta (relação) entre dois nodes.
        
        Args:
            source_id: ID do node de origem
            target_id: ID do node de destino
            relation_type: Tipo de relação ("calls", "imports", "inherits", etc)
            metadata: Metadados adicionais
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO edges 
                (source_id, target_id, relation_type, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                source_id,
                target_id,
                relation_type,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
        finally:
            conn.close()
    
    def get_predecessors(self, node_id: str, relation_type: str = None) -> List[Dict[str, Any]]:
        """
        Obtém nós que apontam PARA este nó (predecessores).
        
        Em um grafo de chamadas:
        - Predecessores = funções que CHAMAM este nó
        - source → target, então anterior aponta para target
        
        Args:
            node_id: ID do nó alvo
            relation_type: Tipo de relação a filtrar (ex: 'calls')
            
        Returns:
            Lista de nós predecessores
        """
        query = """
        SELECT DISTINCT n.id, n.name, n.type, n.file_path, n.line_number, 
                        n.signature, n.metadata, n.created_at
        FROM nodes n
        INNER JOIN edges e ON n.id = e.source_id
        WHERE e.target_id = ?
        """
        params = [node_id]
        
        if relation_type:
            query += " AND e.relation_type = ?"
            params.append(relation_type)
        
        query += " ORDER BY n.name"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_number': row[4],
                    'signature': row[5],
                    'metadata': row[6],
                    'created_at': row[7]
                })
            
            return results
        finally:
            conn.close()
    
    def get_successors(self, node_id: str, relation_type: str = None) -> List[Dict[str, Any]]:
        """
        Obtém nós que este nó aponta (sucessores).
        
        Em um grafo de chamadas:
        - Sucessores = funções que ESTE NÓ CHAMA
        - source → target, então source aponta para alvo
        
        Args:
            node_id: ID do nó fonte
            relation_type: Tipo de relação a filtrar (ex: 'calls')
            
        Returns:
            Lista de nós sucessores
        """
        query = """
        SELECT DISTINCT n.id, n.name, n.type, n.file_path, n.line_number, 
                        n.signature, n.metadata, n.created_at
        FROM nodes n
        INNER JOIN edges e ON n.id = e.target_id
        WHERE e.source_id = ?
        """
        params = [node_id]
        
        if relation_type:
            query += " AND e.relation_type = ?"
            params.append(relation_type)
        
        query += " ORDER BY n.name"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'file_path': row[3],
                    'line_number': row[4],
                    'signature': row[5],
                    'metadata': row[6],
                    'created_at': row[7]
                })
            
            return results
        finally:
            conn.close()
    
    def get_call_chain(self, start_node_id: str, max_depth: int = 5) -> List[Tuple[str, str]]:
        """
        Retorna a cadeia de chamadas a partir de um node (BFS).
        
        Args:
            start_node_id: Node inicial
            max_depth: Profundidade máxima
        
        Returns:
            Lista de tuplas (source, target)
        """
        chain = []
        visited = set()
        queue = [(start_node_id, 0)]
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited or depth >= max_depth:
                continue
            
            visited.add(current_id)
            
            # Get successors
            cursor.execute("""
                SELECT target_id FROM edges 
                WHERE source_id = ? AND relation_type = 'calls'
            """, (current_id,))
            
            for row in cursor.fetchall():
                target_id = row[0]
                chain.append((current_id, target_id))
                queue.append((target_id, depth + 1))
        
        conn.close()
        return chain
    
    # ===== METADATA OPERATIONS =====
    
    def set_metadata(self, key: str, value: str):
        """Define um valor de metadado."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO graph_metadata (key, value)
            VALUES (?, ?)
        """, (key, value))
        
        conn.commit()
        conn.close()
    
    def get_metadata(self, key: str) -> str:
        """Obtém um valor de metadado."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM graph_metadata WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    # ===== STATISTICS =====
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do grafo."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM nodes")
        num_nodes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM edges")
        num_edges = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT type, COUNT(*) FROM nodes GROUP BY type
        """)
        nodes_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT relation_type, COUNT(*) FROM edges GROUP BY relation_type
        """)
        edges_by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "nodes_by_type": nodes_by_type,
            "edges_by_type": edges_by_type,
            "db_path": self.db_path
        }
