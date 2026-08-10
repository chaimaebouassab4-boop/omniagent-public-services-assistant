from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel

from app.rag_service import query_rag

router = APIRouter(prefix="/api", tags=["chat"])


class RAGQueryRequest(BaseModel):
    query: str
    service_type: Optional[str] = None


class RAGQueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    language: str = "darija"
    fallback_reason: Optional[str] = None


@router.get("/chat/ping")
def ping_chat() -> dict:
    """Health ping for chat namespace."""
    return {"status": "success", "data": {"message": "chat online"}}


@router.post("/chat/query", response_model=RAGQueryResponse)
def query_chat_rag(body: RAGQueryRequest) -> RAGQueryResponse:
    """RAG query endpoint returning grounded Darija answer with metadata."""
    res = query_rag(user_query=body.query, service_type=body.service_type)
    return RAGQueryResponse(
        answer=res.get("answer", ""),
        confidence=res.get("confidence", 0.0),
        sources=res.get("sources", []),
        language=res.get("language", "darija"),
        fallback_reason=res.get("fallback_reason")
    )
