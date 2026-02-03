"""
FastAPI application for the Code RAG Engine.
"""
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.query_engine import CodeQueryEngine


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


# Create FastAPI app
app = FastAPI(
    title="Code RAG Engine",
    description="A RAG system specialized in code repositories",
    version="0.1.0"
)


# Global query engine instance (lazy loading)
_query_engine: Optional[CodeQueryEngine] = None


def get_query_engine() -> CodeQueryEngine:
    """Get or create the query engine instance."""
    global _query_engine
    if _query_engine is None:
        try:
            _query_engine = CodeQueryEngine(
                collection_name="code_repository",
                use_ollama=False  # Default to context-only mode
            )
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Query engine not available. Please index a repository first. Error: {str(e)}"
            )
    return _query_engine


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="ok",
        version="0.1.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0"
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
