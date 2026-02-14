"""
Aplicação FastAPI para o Code RAG Engine.
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

from app.config import settings
from app.query_engine import CodeQueryEngine
from app.llm_provider import get_llm_provider

# Carrega variáveis de ambiente
load_dotenv()


# Pydantic models for API
class QueryRequest(BaseModel):
    """Modelo de requisição para consultas no repositório de código."""
    query: str = Field(..., description="A consulta para buscar no repositório")
    similarity_top_k: Optional[int] = Field(
        5, 
        description="Número de chunks semelhantes a recuperar",
        ge=1,
        le=20
    )
    return_context_only: bool = Field(
        True,
        description="Se true, retorna apenas contexto sem resposta do LLM"
    )


class AskRequest(BaseModel):
    """Modelo de requisição para /ask - sempre gera resposta com LLM."""
    query: str = Field(..., description="A pergunta para o assistente de código")
    similarity_top_k: Optional[int] = Field(
        5, 
        description="Número de chunks semelhantes a recuperar",
        ge=1,
        le=20
    )


class ContextItem(BaseModel):
    """Modelo para um item de contexto individual."""
    rank: int
    file_path: str
    file_name: str
    file_type: str
    score: float
    text: str


class QueryResponse(BaseModel):
    """Modelo de resposta para resultados de consulta."""
    query: str
    query_classification: Optional[Dict[str, Any]] = Field(
        None,
        description="Info de classificação: tipo (semantic/graph/hybrid), estratégia"
    )
    semantic_results: Optional[List[ContextItem]] = None
    semantic_count: Optional[int] = None
    graph_results: Optional[List[Any]] = None
    graph_count: Optional[int] = None
    graph_type: Optional[str] = None
    response: Optional[str] = None


class HealthResponse(BaseModel):
    """Modelo de resposta para health check."""
    status: str
    version: str
    llm_provider: str = Field(..., description="Tipo de LLM provider: 'ollama' (local) ou 'gemini' (remoto)")


# Create FastAPI app
app = FastAPI(
    title="Code RAG Engine",
    description="Sistema RAG especializado em repositórios de código",
    version="0.2.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global instances (lazy loading)
_query_engine: Optional[CodeQueryEngine] = None
_llm_provider = None


def get_query_engine() -> CodeQueryEngine:
    """Obtém ou cria instância do query engine."""
    global _query_engine
    if _query_engine is None:
        try:
            _query_engine = CodeQueryEngine(
                collection_name="img_converter",
                use_ollama=False  # Modo apenas contexto por padrão
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Query engine não disponível. Por favor, indexe um repositório primeiro. Erro: {str(e)}"
            )
    return _query_engine


def get_llm() -> object:
    """Get or create the LLM provider instance."""
    global _llm_provider
    if _llm_provider is None:
        try:
            _llm_provider = get_llm_provider()
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao configurar LLM: {str(e)}"
            )
        except ImportError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Biblioteca faltante: {str(e)}"
            )
    return _llm_provider


def build_prompt(context: str, question: str) -> str:
    """
    Build a RAG prompt with explicit instructions to avoid hallucinations.
    
    Args:
        context: Trechos de código relevantes recuperados pelo RAG
        question: Pergunta/consulta do usuário
        
    Returns:
        Prompt estruturado com instruções sênior
    """
    return f"""Você é um analista de código sênior.

Explique APENAS com base no código fornecido.
Não assuma comportamentos externos.
Não generalize.
Se algo não estiver explícito no código, diga que não é possível afirmar.

### CONTEXTO DO CÓDIGO
{context}

### PERGUNTA
{question}

### RESPOSTA"""


@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raiz - verificação de saúde."""
    return HealthResponse(
        status="ok",
        version="0.2.0",
        llm_provider=settings.LLM_PROVIDER
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Endpoint de verificação de saúde."""
    return HealthResponse(
        status="ok",
        version="0.2.0",
        llm_provider=settings.LLM_PROVIDER
    )


@app.post("/query", response_model=QueryResponse)
async def query_code(request: QueryRequest):
    """
    Consulta o repositório de código indexado com roteamento inteligente.
    
    O query_engine decide automaticamente:
    - SEMANTIC: Retorna chunks similares (Vector Search)
    - GRAPH: Analisa relações de código (Graph Search)
    - HYBRID: Combina ambas estratégias
    """
    try:
        engine = get_query_engine()
        result = engine.query(
            query=request.query,
            similarity_top_k=request.similarity_top_k,
            return_context_only=request.return_context_only,
            show_classifier_info=True
        )
        
        return QueryResponse(
            query=result['query'],
            query_classification=result.get('query_classification'),
            semantic_results=result.get('semantic_results'),
            semantic_count=result.get('semantic_count'),
            graph_results=result.get('graph_results'),
            graph_count=result.get('graph_count'),
            graph_type=result.get('graph_type'),
            response=result.get('response')
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha na consulta: {str(e)}"
        )


@app.get("/context")
async def get_context(
    query: str = Query(..., description="A consulta para buscar"),
    top_k: int = Query(5, ge=1, le=20, description="Número de resultados a retornar")
):
    """
    Recupera contexto de código relevante como texto simples.
    
    Este endpoint retorna contexto formatado que pode ser usado diretamente com qualquer LLM.
    """
    try:
        engine = get_query_engine()
        result = engine.query(
            query=query,
            similarity_top_k=top_k,
            return_context_only=True
        )
        
        # Formata contexto como texto
        context_text = "\n---\n".join([
            f"Arquivo: {ctx['file_path']} (relevância: {ctx['score']:.3f})\n{ctx['text']}"
            for ctx in result.get('semantic_results', [])
        ])
        
        return {"context": context_text, "count": result.get('semantic_count', 0)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao recuperar contexto: {str(e)}"
        )


@app.post("/ask", response_model=QueryResponse)
async def ask_with_llm(request: AskRequest):
    """
    Pergunta ao assistente de código com resposta em linguagem natural.
    
    Este endpoint SEMPRE gera uma resposta usando o LLM configurado
    (Gemini ou Ollama). Ideal para chatbots e interfaces conversacionais.
    
    Retorna tanto os dados estruturados (funções, arquivos) quanto
    uma explicação em linguagem natural gerada pelo LLM.
    """
    try:
        engine = get_query_engine()
        
        # Executar consulta SEMPRE com LLM (return_context_only=False)
        result = engine.query(
            query=request.query,
            similarity_top_k=request.similarity_top_k,
            return_context_only=False,  # ← Sempre False no /ask
            show_classifier_info=True
        )
        
        return QueryResponse(
            query=result['query'],
            query_classification=result.get('query_classification'),
            semantic_results=result.get('semantic_results'),
            semantic_count=result.get('semantic_count'),
            graph_results=result.get('graph_results'),
            graph_count=result.get('graph_count'),
            graph_type=result.get('graph_type'),
            response=result.get('response')
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha na consulta com LLM: {str(e)}"
        )


@app.post("/retrieve")
async def retrieve_context(request: QueryRequest):
    """
    Recupera apenas contexto de código relevante (sem classificação).
    
    Endpoint simples para obter contexto sem análise de tipo de query.
    Ideal para integração com LLMs externos ou debug.
    
    Returns:
        Contexto com metadados básicos
    """
    try:
        engine = get_query_engine()
        result = engine.retrieve_context(
            query=request.query,
            similarity_top_k=request.similarity_top_k
        )
        
        return {
            "query": request.query,
            "context": result.get('context'),
            "count": result.get('num_results'),
            "total_chars": len("".join([c['text'] for c in result.get('context', [])]))
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao recuperar contexto: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
