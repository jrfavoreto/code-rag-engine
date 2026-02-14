"""
Code Graph Builder: Extrai relações de código usando AST parsing.

Suporta:
- Function/class definitions
- Function calls
- Imports
- Variable references
"""
import ast
from pathlib import Path
from typing import List, Dict, Tuple, Set
from app.graph_storage import GraphStorage


class CodeGraphBuilder:
    """Constrói grafo de dependências a partir do código."""
    
    def __init__(self, graph_storage: GraphStorage = None):
        """
        Inicializa o builder.
        
        Args:
            graph_storage: Instância de GraphStorage para armazenar grafo
        """
        if graph_storage is None:
            graph_storage = GraphStorage()
        
        self.storage = graph_storage
    
    def parse_python_file(self, file_path: str, base_path: str = None) -> Dict:
        """
        Extrai definições e relações de um arquivo Python.
        
        Args:
            file_path: Caminho do arquivo
            base_path: Caminho base para IDs relativos
        
        Returns:
            Dict com nodes e edges extraídos
        """
        file_path = Path(file_path)
        
        if base_path:
            base_path = Path(base_path)
            relative_path = str(file_path.relative_to(base_path))
        else:
            relative_path = str(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"⚠️  Erro lendo {file_path}: {e}")
            return {"nodes": [], "edges": []}
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Erro parseando {file_path}: {e}")
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        
        # Extractor para AST
        extractor = PythonASTExtractor(file_path=relative_path)
        
        # Extrair nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                node_id = f"{relative_path}:{node.name}"
                nodes.append({
                    "id": node_id,
                    "name": node.name,
                    "type": "function",
                    "file_path": relative_path,
                    "line_number": node.lineno,
                    "signature": extractor._get_function_signature(node)
                })
            
            elif isinstance(node, ast.ClassDef):
                node_id = f"{relative_path}:{node.name}"
                nodes.append({
                    "id": node_id,
                    "name": node.name,
                    "type": "class",
                    "file_path": relative_path,
                    "line_number": node.lineno
                })
        
        # Extrair edges (relações)
        edges = extractor.extract_calls(tree, file_path=relative_path)
        edges += extractor.extract_imports(tree, file_path=relative_path)
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def analyze_file(self, file_path: str, content: str, language: str, 
                     collection_name: str) -> tuple:
        """
        Analisa um arquivo e extrai nós e arestas para armazenamento em grafo.
        
        Args:
            file_path: Caminho do arquivo
            content: Conteúdo do arquivo
            language: Linguagem do arquivo (e.g., "python")
            collection_name: Nome da coleção para metadados
            
        Returns:
            Tuple (nodes_added, edges_added)
        """
        if language.lower() != "python":
            return 0, 0  # Por enquanto apenas Python é suportado
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0, 0
        
        nodes_added = 0
        edges_added = 0
        
        # Construir relative path
        relative_path = Path(file_path).name if isinstance(file_path, str) else file_path.name
        
        # Extrair nós
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                node_id = f"{collection_name}:{relative_path}:{node.name}"
                extractor = PythonASTExtractor(file_path=relative_path)
                
                self.storage.add_node(
                    node_id=node_id,
                    name=node.name,
                    node_type="function",
                    file_path=file_path,
                    line_number=node.lineno,
                    signature=extractor._get_function_signature(node),
                    metadata={"collection": collection_name}
                )
                nodes_added += 1
            
            elif isinstance(node, ast.ClassDef):
                node_id = f"{collection_name}:{relative_path}:{node.name}"
                
                self.storage.add_node(
                    node_id=node_id,
                    name=node.name,
                    node_type="class",
                    file_path=file_path,
                    line_number=node.lineno,
                    metadata={"collection": collection_name}
                )
                nodes_added += 1
        
        # Extrair arestas (chamadas)
        extractor = PythonASTExtractor(file_path=relative_path)
        edges = extractor.extract_calls(tree, file_path=relative_path)
        edges += extractor.extract_imports(tree, file_path=relative_path)
        
        for source, target, rel_type in edges:
            source_id = f"{collection_name}:{source}"
            target_id = f"{collection_name}:{target}"
            
            self.storage.add_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=rel_type,
                metadata={"collection": collection_name}
            )
            edges_added += 1
        
        return nodes_added, edges_added
    
    def index_repository(self, repo_path: str) -> Dict:
        """
        Indexa um repositório completo.
        
        Args:
            repo_path: Caminho do repositório
        
        Returns:
            Estatísticas da indexação
        """
        repo_path = Path(repo_path)
        
        total_nodes = 0
        total_edges = 0
        
        # Limpar índice anterior
        self.storage.clear()
        
        # Indexar arquivos Python
        for py_file in repo_path.rglob("*.py"):
            # Skip directories
            if py_file.is_dir():
                continue
            
            # Skip common exclusions
            if any(part in py_file.parts for part in ['__pycache__', '.venv', 'venv', 'node_modules']):
                continue
            
            result = self.parse_python_file(str(py_file), base_path=str(repo_path))
            
            # Adicionar nodes
            for node in result["nodes"]:
                self.storage.add_node(
                    node_id=node["id"],
                    name=node["name"],
                    node_type=node["type"],
                    file_path=node.get("file_path"),
                    line_number=node.get("line_number"),
                    signature=node.get("signature")
                )
                total_nodes += 1
            
            # Adicionar edges
            for source, target, rel_type in result["edges"]:
                self.storage.add_edge(source, target, rel_type)
                total_edges += 1
        
        # Atualizar metadata
        self.storage.set_metadata("last_indexed", str(Path.cwd()))
        self.storage.set_metadata("num_files", str(len(list(repo_path.rglob("*.py")))))
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "total_files": len(list(repo_path.rglob("*.py")))
        }


class CallVisitor(ast.NodeVisitor):
    """
    Visitor para rastrear chamadas de função com contexto/escopo correto.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.calls = []
        self.scope_stack = []  # Stack de (tipo, nome) para rastrear escopo
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Entra em uma função."""
        self.scope_stack.append(("function", node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Entra em uma classe."""
        self.scope_stack.append(("class", node.name))
        self.generic_visit(node)
        self.scope_stack.pop()
    
    def visit_Call(self, node: ast.Call):
        """Encontra uma chamada de função."""
        if not self.scope_stack:
            # Chamada no escopo global
            self.generic_visit(node)
            return
        
        # Extrair nome da função chamada
        target = None
        
        if isinstance(node.func, ast.Name):
            # Chamada simples: func()
            target = node.func.id
        
        elif isinstance(node.func, ast.Attribute):
            # Chamada com atributo: obj.method()
            target = node.func.attr
        
        if target:
            # Obter o contexto atual
            scope_type, scope_name = self.scope_stack[-1]
            source = f"{self.file_path}:{scope_name}"
            target_full = f"{self.file_path}:{target}"
            
            # Evitar auto-referência
            if source != target_full:
                self.calls.append((source, target_full, "calls"))
        
        self.generic_visit(node)


class PythonASTExtractor:
    """Extrai informações de código Python via AST."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_function = None
        self.current_class = None
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extrai assinatura de função."""
        args = []
        if node.args.args:
            args = [arg.arg for arg in node.args.args]
        
        return f"def {node.name}({', '.join(args)})"
    
    def extract_calls(self, tree: ast.AST, file_path: str) -> List[Tuple[str, str, str]]:
        """
        Extrai chamadas de função com análise de escopo.
        
        Returns:
            Lista de (source, target, "calls")
        """
        calls = []
        
        # Visitor para rastrear contexto
        visitor = CallVisitor(file_path)
        visitor.visit(tree)
        
        return visitor.calls
    
    def extract_imports(self, tree: ast.AST, file_path: str) -> List[Tuple[str, str, str]]:
        """
        Extrai importações.
        
        Returns:
            Lista de (file_path, imported_module, "imports")
        """
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    imports.append((file_path, target, "imports"))
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    target = f"{node.module}.{alias.name}" if node.module else alias.name
                    imports.append((file_path, target, "imports"))
        
        return imports
