"""
Script de teste para o Query Classifier.
Demonstra como o classifier roteia queries diferentes para estratégias apropriadas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.query_classifier import QueryClassifier, QueryMetadata, QueryType


def test_classifier():
    """Testa o classificador com várias queries."""
    
    test_queries = [
        # Queries SEMÂNTICAS (Vector Search)
        ("Como funciona a função compress_pdf()?", QueryType.SEMANTIC),
        ("Explique a validação de imagens", QueryType.SEMANTIC),
        ("O que faz a função process_file()?", QueryType.SEMANTIC),
        ("Qual é a lógica de compressão?", QueryType.SEMANTIC),
        
        # Queries GRAPH (Graph Search)
        ("Quem chama compress_pdf()?", QueryType.GRAPH),
        ("Qual é a cadeia de chamadas?", QueryType.GRAPH),
        ("Que funções dependem de convert_image()?", QueryType.GRAPH),
        ("Mostre o fluxo de execução", QueryType.GRAPH),
        ("Quais funções são importadas?", QueryType.GRAPH),
        
        # Queries HÍBRIDAS (ambas)
        ("Como funciona e quem chama compress_pdf()?", QueryType.HYBRID),
        ("Explique compress_pdf() e sua dependência", QueryType.HYBRID),
    ]
    
    print("=" * 80)
    print("🔍 QUERY CLASSIFIER TEST")
    print("=" * 80)
    print()
    
    results = {
        QueryType.SEMANTIC: 0,
        QueryType.GRAPH: 0,
        QueryType.HYBRID: 0
    }
    
    correct = 0
    total = len(test_queries)
    
    for i, (query, expected_type) in enumerate(test_queries, 1):
        metadata = QueryMetadata(query)
        is_correct = metadata.query_type == expected_type
        correct += is_correct
        results[metadata.query_type] += 1
        
        status = "✓" if is_correct else "✗"
        
        print(f"{i}. {status} Query: {query}")
        print(f"   Classificado como: {metadata.query_type.value}")
        print(f"   Estratégia: {metadata.strategy_hint}")
        
        if metadata.keywords_found["graph"]:
            print(f"   🔗 Graph keywords: {', '.join(metadata.keywords_found['graph'][:3])}")
        
        if metadata.keywords_found["semantic"]:
            print(f"   📚 Semantic keywords: {', '.join(metadata.keywords_found['semantic'][:3])}")
        
        if not is_correct:
            print(f"   ⚠️  Expected: {expected_type.value}")
        
        print()
    
    print("=" * 80)
    print(f"📊 RESULTS: {correct}/{total} correct ({correct*100//total}%)")
    print(f"   SEMANTIC: {results[QueryType.SEMANTIC]}")
    print(f"   GRAPH:    {results[QueryType.GRAPH]}")
    print(f"   HYBRID:   {results[QueryType.HYBRID]}")
    print("=" * 80)
    
    return correct == total


def test_real_queries():
    """Testa com queries reais do usuário."""
    
    print("\n" + "=" * 80)
    print("🎯 REAL QUERY CLASSIFICATION")
    print("=" * 80)
    print("Digite queries para ver como são classificadas (ou 'sair' para parar):\n")
    
    while True:
        query = input("❓ Query: ").strip()
        
        if query.lower() in ['sair', 'exit', 'quit', 'q']:
            print("\n👋 Encerrando...")
            break
        
        if not query:
            print("⚠️  Por favor, digite uma query válida.\n")
            continue
        
        metadata = QueryMetadata(query)
        
        print(f"\n📊 Classification:")
        print(f"   Type: {metadata.query_type.value.upper()}")
        print(f"   Strategy: {metadata.strategy_hint}")
        print(f"   Keywords found:")
        print(f"      - Graph: {metadata.keywords_found['graph'] or 'None'}")
        print(f"      - Semantic: {metadata.keywords_found['semantic'] or 'None'}")
        print()


if __name__ == "__main__":
    # Test 1: Predefined queries
    success = test_classifier()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    # Test 2: Interactive mode
    test_real_queries()
