"""
FastAPI application for the Code RAG Engine.
"""
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
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
    """Request model for querying the code repository."""
    query: str = Field(..., description="The query to search for in the code repository")
    similarity_top_k: Optional[int] = Field(
        None, 
        description="Number of similar chunks to retrieve",
        ge=1,
        le=20
    )
    return_context_only: bool = Field(
        True,
        description="If true, only return context without LLM response"
    )


class ContextItem(BaseModel):
    """Model for a single context item."""
    rank: int
    file_path: str
    file_name: str
    file_type: str
    score: float
    text: str


class QueryResponse(BaseModel):
    """Response model for query results."""
    query: str
    context: List[ContextItem]
    num_results: int
    response: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    llm_provider: str = Field(..., description="Tipo de LLM provider: 'ollama' (local) ou 'gemini' (remoto)")


# Create FastAPI app
app = FastAPI(
    title="Code RAG Engine",
    description="A RAG system specialized in code repositories",
    version="0.1.0"
)


# Global instances (lazy loading)
_query_engine: Optional[CodeQueryEngine] = None
_llm_provider = None


def get_query_engine() -> CodeQueryEngine:
    """Get or create the query engine instance."""
    global _query_engine
    if _query_engine is None:
        try:
            _query_engine = CodeQueryEngine(
                collection_name="img_converter",
                use_ollama=False  # Default to context-only mode
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Query engine not available. Please index a repository first. Error: {str(e)}"
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
    """Root endpoint - health check."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        llm_provider=settings.LLM_PROVIDER
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        llm_provider=settings.LLM_PROVIDER
    )


@app.post("/query", response_model=QueryResponse)
async def query_code(request: QueryRequest):
    """
    Query the indexed code repository.
    
    Returns relevant code context and optionally an LLM-generated response.
    """
    try:
        engine = get_query_engine()
        result = engine.query(
            query=request.query,
            similarity_top_k=request.similarity_top_k,
            return_context_only=request.return_context_only
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@app.get("/context")
async def get_context(
    query: str = Query(..., description="The query to search for"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return")
):
    """
    Get relevant code context as plain text.
    
    This endpoint returns formatted context that can be directly used with any LLM.
    """
    try:
        engine = get_query_engine()
        context = engine.retrieve_context(
            query=query,
            similarity_top_k=top_k
        )
        return {"context": context}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Context retrieval failed: {str(e)}"
        )


@app.post("/ask", response_model=QueryResponse)
async def ask_with_llm(request: QueryRequest):
    """
    Query with LLM-generated answer (combines context + reasoning).
    
    Retrieves relevant code context and sends it to the configured LLM provider
    (Ollama local or Gemini remoto) for analysis.
    Returns both the context and the LLM's structured analysis.
    """
    try:
        engine = get_query_engine()
        
        # Etapa 1: Recuperar contexto relevante (RAG - Retrieval)
        result = engine.query(
            query=request.query,
            similarity_top_k=request.similarity_top_k,
            return_context_only=True
        )
        
        if result['num_results'] == 0:
            raise HTTPException(status_code=404, detail="Nenhum contexto encontrado")
        
        # Formata o contexto como texto
        context_text = "\n\n---\n\n".join(
            f"Arquivo: {ctx['file_path']} (relevância: {ctx['score']:.3f})\n{ctx['text']}"
            for ctx in result['context']
        )
        
        # Etapa 2: Construir prompt com instruções sênior
        prompt = build_prompt(context_text, request.query)
        
        # Etapa 3: Enviar para o LLM provider configurado (Ollama ou Gemini)
        llm = get_llm()
        llm_answer = llm.generate(prompt)
        
        # Retorna contexto + resposta do LLM
        return QueryResponse(
            query=request.query,
            context=result['context'],
            num_results=result['num_results'],
            response=llm_answer
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM query failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
