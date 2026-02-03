from fastapi import FastAPI
from pydantic import BaseModel
from app.query_engine import get_query_engine

app = FastAPI()
engine = get_query_engine()

class Query(BaseModel):
    question: str

@app.post("/rag/query")
def query_rag(q: Query):
    response = engine.query(q.question)
    return {
        "context": str(response)
    }
