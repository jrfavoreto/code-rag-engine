#!/usr/bin/env python3
"""
Script de validação para implementação de indexação unificada.
Verifica que todos os componentes estão corretamente integrados.
"""
import sys
from pathlib import Path

# Adicionar diretório pai ao caminho
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_imports():
    """Validar que todas as importações necessárias funcionam."""
    print("🔍 Validando importações...")
    try:
        from app.indexer import CodeIndexer
        from app.code_graph import CodeGraphBuilder
        from app.graph_storage import GraphStorage
        from app.query_classifier import QueryClassifier
        print("✅ Todas as importações bem-sucedidas\n")
        return True
    except ImportError as e:
        print(f"❌ Erro de importação: {e}\n")
        return False

def validate_indexer_signature():
    """Validar assinatura de CodeIndexer.index_repository."""
    print("🔍 Validando CodeIndexer.index_repository()...")
    try:
        from app.indexer import CodeIndexer
        import inspect
        
        sig = inspect.signature(CodeIndexer.index_repository)
        params = list(sig.parameters.keys())
        
        expected = ['self', 'repo_path', 'collection_name', 'exclude_dirs']
        if params == expected:
            print(f"✅ Assinatura correta: {params}\n")
            return True
        else:
            print(f"❌ Assinatura incorreta. Esperado {expected}, obtido {params}\n")
            return False
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def validate_code_graph_methods():
    """Validar que CodeGraphBuilder tem os métodos necessários."""
    print("🔍 Validando métodos de CodeGraphBuilder...")
    try:
        from app.code_graph import CodeGraphBuilder
        
        methods = [
            'parse_python_file',
            'analyze_file',  # NOVO MÉTODO
            'index_repository'
        ]
        
        for method_name in methods:
            if hasattr(CodeGraphBuilder, method_name):
                print(f"  ✓ {method_name}")
            else:
                print(f"  ✗ {method_name} NÃO ENCONTRADO")
                return False
        
        print("✅ Todos os métodos presentes\n")
        return True
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def validate_graph_storage_methods():
    """Validar que GraphStorage tem os métodos necessários."""
    print("🔍 Validando métodos de GraphStorage...")
    try:
        from app.graph_storage import GraphStorage
        
        methods = [
            'add_node',
            'add_edge',
            'clear',
            'clear_graphs',  # NOVO MÉTODO
            'get_successors',
            'get_predecessors'
        ]
        
        for method_name in methods:
            if hasattr(GraphStorage, method_name):
                print(f"  ✓ {method_name}")
            else:
                print(f"  ✗ {method_name} NÃO ENCONTRADO")
                return False
        
        print("✅ Todos os métodos presentes\n")
        return True
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def validate_config():
    """Validar que a configuração tem GRAPH_DB_PATH."""
    print("🔍 Validando config.py...")
    try:
        from app.config import settings
        
        if hasattr(settings, 'GRAPH_DB_PATH'):
            print(f"  ✓ GRAPH_DB_PATH = {settings.GRAPH_DB_PATH}")
            print("✅ Configuração válida\n")
            return True
        else:
            print("  ✗ GRAPH_DB_PATH não encontrado na configuração")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}\n")
        return False

def main():
    """Executar todas as validações."""
    print("=" * 60)
    print("VALIDAÇÃO DE INDEXAÇÃO UNIFICADA")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": validate_imports(),
        "Assinatura do Indexador": validate_indexer_signature(),
        "CodeGraphBuilder": validate_code_graph_methods(),
        "GraphStorage": validate_graph_storage_methods(),
        "Configuração": validate_config(),
    }
    
    print("=" * 60)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Todas as validações passaram! A indexação unificada está pronta.")
        return 0
    else:
        print(f"\n❌ {total - passed} validação(ões) falhou(aram). Por favor, revise.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
