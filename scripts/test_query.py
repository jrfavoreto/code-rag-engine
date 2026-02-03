#!/usr/bin/env python3
"""
Script de teste para demonstrar consultas RAG completas.
Recupera contexto relevante e o exibe formatado.
"""
import sys
from pathlib import Path

# Adiciona diretório pai ao path para importar módulos da aplicação
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.query_engine import CodeQueryEngine

def main():
    """Função principal: executa consulta e exibe resultados."""
    
    # Inicializa o engine de query com a coleção indexada
    engine = CodeQueryEngine(
        collection_name="img_converter",  # Nome da coleção ChromaDB indexada
        use_ollama=False  # False = apenas recuperação, sem usar LLM para gerar resposta
    )

    # Executa consulta e recupera chunks relevantes
    result = engine.query(
        #query="onde ocorre a conversão de imagem para pdf?",  # Pergunta/consulta
        #query="em qual classe ocorre o redimensionamento de imagens?",  # Pergunta/consulta
        query="o que acontece quando compress_pdf() é executado?", # Pergunta/consulta
        similarity_top_k=5  # Número máximo de chunks similares a recuperar
    )

    # Exibe resumo dos resultados
    print(f"Query: {result['query']}")
    print(f"Número de resultados: {result['num_results']}\n")

    # Itera sobre cada chunk de contexto recuperado
    for ctx in result["context"]:
        # Exibe metadados: arquivo, score de similaridade (0.0-1.0)
        print(f"--- {ctx['file_path']} (score={ctx['score']:.3f}) ---")
        # Exibe o conteúdo do chunk (código encontrado)
        print(ctx["text"])
        print()

if __name__ == "__main__":
    main()

