"""
Script de teste para recuperar apenas contexto (sem geração de resposta LLM).
Útil para integração com LLMs externos (GPT, Claude, Llama, etc).
"""
import sys
from pathlib import Path

# Adiciona diretório pai ao path para importar módulos da aplicação
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.query_engine import CodeQueryEngine

# Inicializa o engine de query com a coleção indexada
engine = CodeQueryEngine(
    collection_name="img_converter",  # Nome da coleção ChromaDB
    use_ollama=False  # False = apenas recuperação, sem usar LLM para gerar resposta
)

# Recupera e exibe contexto formatado
# - min_score=0.3: Filtra chunks com relevância baixa
# - max_context_chars=8000: Limita tamanho do contexto para não exceder prompt
print(
    engine.retrieve_context(
        query="onde ocorre a conversão de imagem para pdf?",
        min_score=0.3,              # Mínimo de relevância (0.0-1.0)
        max_context_chars=8000      # Limite de caracteres (evita prompt gigante)
    )
)
