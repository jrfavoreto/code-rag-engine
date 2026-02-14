"""
Script de teste para Graph Search.
Demonstra queries de relações de código no grafo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.code_graph import CodeGraphBuilder
from app.graph_search import GraphSearchEngine
from app.graph_storage import GraphStorage


def test_graph_builder():
    """Testa a construção do grafo."""
    
    print("=" * 80)
    print("🔍 GRAPH BUILDER TEST")
    print("=" * 80)
    print()
    
    # Usar repositório de teste
    repo_path = r"C:\desenv\img-converter"
    
    if not Path(repo_path).exists():
        print(f"❌ Repositório não encontrado: {repo_path}")
        return False
    
    print(f"📂 Indexando repositório: {repo_path}\n")
    
    # Criar builder
    builder = CodeGraphBuilder()
    
    # Indexar repositório
    try:
        stats = builder.index_repository(repo_path)
        
        print(f"✓ Indexação completa!")
        print(f"  - Nodes extraídos: {stats['total_nodes']}")
        print(f"  - Edges extraídos: {stats['total_edges']}")
        print(f"  - Arquivos processados: {stats['total_files']}")
        print()
        
        # Mostrar estatísticas detalhadas
        graph_stats = builder.storage.get_stats()
        print("📊 Estatísticas do Grafo:")
        print(f"  - Nodes por tipo: {graph_stats['nodes_by_type']}")
        print(f"  - Edges por tipo: {graph_stats['edges_by_type']}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_search():
    """Testa queries no grafo."""
    
    print("=" * 80)
    print("🔎 GRAPH SEARCH TEST")
    print("=" * 80)
    print()
    
    # Criar engine
    engine = GraphSearchEngine()
    
    # Queries de teste
    test_queries = [
        "Quem chama compress_pdf()?",
        "Qual é a cadeia de chamadas de compress_pdf()?",
        "O que process_file() chama?",
    ]
    
    for query in test_queries:
        print(f"❓ Query: {query}")
        
        try:
            results = engine.search(query)
            
            if "error" in results:
                print(f"⚠️  {results['error']}")
            else:
                print(f"📌 Tipo: {results['type']}")
                print(f"📄 Mensagem: {results['message']}")
                
                if isinstance(results['results'], list):
                    if not results['results']:
                        print("   (sem resultados)")
                    else:
                        for i, item in enumerate(results['results'][:5], 1):
                            if isinstance(item, dict):
                                if 'name' in item:
                                    print(f"   {i}. {item['name']} ({item.get('type', 'unknown')})")
                                elif 'depth' in item:
                                    print(f"   {i}. [{item['depth']}] {item['function']}")
                
                elif isinstance(results['results'], dict):
                    print(f"   {results['results']}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        print()


def test_interactive():
    """Modo interativo para testar queries."""
    
    print("\n" + "=" * 80)
    print("💬 INTERACTIVE MODE")
    print("=" * 80)
    print("Digite queries para buscar relações no grafo (ou 'sair' para parar):\n")
    
    engine = GraphSearchEngine()
    
    while True:
        query = input("❓ Query: ").strip()
        
        if query.lower() in ['sair', 'exit', 'quit', 'q']:
            print("\n👋 Encerrando...")
            break
        
        if not query:
            print("⚠️  Por favor, digite uma query válida.\n")
            continue
        
        try:
            results = engine.search(query)
            
            print()
            if "error" in results:
                print(f"⚠️  {results['error']}")
            else:
                print(f"📊 Resultados ({results['type']}):")
                print(f"   {results['message']}\n")
                
                if isinstance(results['results'], list):
                    if not results['results']:
                        print("   (sem resultados)")
                    else:
                        for item in results['results'][:10]:
                            if isinstance(item, dict):
                                if 'name' in item:
                                    sig = f" - {item.get('signature', '')}" if item.get('signature') else ""
                                    print(f"   • {item['name']}{sig}")
                                elif 'depth' in item:
                                    indent = "  " * item['depth']
                                    print(f"   {indent}└─ [{item['depth']}] {item['function']}")
                
                elif isinstance(results['results'], dict):
                    for key, value in results['results'].items():
                        if key != "chain":
                            print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        
        print()


if __name__ == "__main__":
    # Test 1: Build graph
    print("\n🚀 INICIANDO TESTES DE GRAPH SEARCH\n")
    
    success = test_graph_builder()
    
    if success:
        print("\n✅ Grafo construído com sucesso!")
        
        # Test 2: Search queries
        test_graph_search()
        
        # Test 3: Interactive mode
        test_interactive()
    else:
        print("\n❌ Erro ao construir o grafo")
