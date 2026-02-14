#!/usr/bin/env python3
from app.query_engine import CodeQueryEngine

# Inicializar
engine = CodeQueryEngine(collection_name="img_converter")

# Testar com a query que estava falhando
query = 'Quem chama compress_pdf?'
print(f'Query: {query}')
print()

try:
    result = engine.query(query)
    
    print(f'Status: OK')
    print(f'Classificação: {result.get("query_classification")}')
    print(f'Tipo de busca: {result.get("search_type")}')
    
    graph_results = result.get("graph_results", [])
    print(f'Resultados de grafo: {len(graph_results)} funções')
    
    # Mostrar resultados
    if graph_results:
        print('\nFunções que chamam compress_pdf:')
        for i, func in enumerate(graph_results, 1):
            print(f'{i}. {func.get("name")} - {func.get("file_path")}:{func.get("line_number")}')
    else:
        print('\nNenhuma função encontrada (esperado - apenas process_file deveria chamar)')
        
except Exception as e:
    print(f'ERRO: {e}')
    import traceback
    traceback.print_exc()
