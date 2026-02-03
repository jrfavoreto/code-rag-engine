"""
Script de teste para demonstrar RAG completo com geração de resposta via LLM.
Fluxo: Recuperar contexto (RAG) → Enviar para LLM (Ollama) → Gerar resposta.
"""
import sys
from pathlib import Path

# Adiciona diretório pai ao path para importar módulos da aplicação
sys.path.insert(0, str(Path(__file__).parent.parent))

# Carrega variáveis do arquivo .env
from dotenv import load_dotenv
load_dotenv()

from app.query_engine import CodeQueryEngine
import requests
import os
import time

# Configurações do Ollama (carregadas do .env ou usa padrão)
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

def ask_ollama(context: str, question: str) -> str:
    """
    Envia contexto + pergunta para o Ollama e recebe resposta gerada.
    
    Args:
        context: Trechos de código relevantes recuperados pelo RAG
        question: Pergunta/consulta do usuário
        
    Returns:
        Resposta gerada pelo LLM (Ollama)
    """
    # Monta o prompt estruturado com contexto e pergunta
    prompt = f"""
Você é um analista de código sênior analisando um repositório de código.
Explique APENAS o que a função faz, com base estrita no código fornecido.
Não assuma comportamentos fora da função.
Não generalize.
Se algo não estiver claro no código, diga explicitamente.

CONTEXTO (trechos relevantes do código):
{context}

PERGUNTA:
{question}

Explique de forma clara e objetiva, em português.
"""

    try:
        # Faz requisição HTTP para a API do Ollama
        print("⏳ Aguardando resposta do LLM (isso pode demorar)...")
        start_time = time.time()  # Registra tempo inicial
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",  # Endpoint correto do Ollama para gerar texto
            json={
                "model": OLLAMA_MODEL,           # Modelo LLM a usar (ex: qwen3:1.7b)
                "prompt": prompt,                # Prompt estruturado com contexto
                "stream": False                  # False = aguarda resposta completa
            },
            timeout=300  # Aumentado para 300s (5 minutos) - LLM pode ser lento
        )

        response.raise_for_status()  # Lança exceção se houver erro HTTP
        elapsed_time = time.time() - start_time  # Calcula tempo decorrido
        print(f"⏱️  Tempo de resposta: {elapsed_time:.2f}s\n")  # Exibe tempo
        return response.json()["response"]
    
    except requests.exceptions.Timeout:
        print("\n❌ Timeout: O Ollama demorou muito para responder.")
        print("💡 Sugestões:")
        print("   - Verifique se o Ollama está rodando: ollama serve")
        print("   - Use um modelo menor: qwen2.5:3b")
        print("   - Aumente o timeout ainda mais no código")
        raise
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro de conexão: Não conseguiu conectar ao Ollama em", OLLAMA_URL)
        print("💡 Inicie o Ollama: ollama serve")
        raise
    except Exception as e:
        print(f"\n❌ Erro ao comunicar com Ollama: {e}")
        raise


def main():
    """Função principal: executa o pipeline RAG completo com LLM."""
    
    # Inicializa o engine com a coleção indexada
    engine = CodeQueryEngine(collection_name="img_converter")

    # Pergunta que será respondida com base no repositório
    #question = "O que acontece quando compress_pdf() é executado?"
    # força raciocínio procedural...
    question = "Explique passo a passo a lógica interna da função compress_pdf(), incluindo critérios de decisão e efeitos colaterais no sistema de arquivos."

    # Etapa 1: Recuperar contexto relevante (RAG - Retrieval)
    print("🔎 Recuperando contexto do código...\n")
    result = engine.query(question)

    # Formata os chunks recuperados em um texto estruturado
    # Inclui arquivo, score (relevância) e conteúdo
    context = "\n\n".join(
        f"Arquivo: {ctx['file_path']} (relevância: {ctx['score']:.3f})\n{ctx['text']}"
        for ctx in result['context']
    )

    # Etapa 2: Enviar contexto + pergunta para o LLM (Augmentation + Generation)
    print("🧠 Enviando contexto para o LLM...\n")
    answer = ask_ollama(context, question)

    # Etapa 3: Exibir resposta gerada
    print("✅ Resposta final:\n")
    print(answer)


if __name__ == "__main__":
    main()

