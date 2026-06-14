import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.security_agent import SecurityAgent
from app.services.qdrant_service import is_qdrant_enabled
from app.services.vector_store import get_vector_store

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


@router.post("/search")
def search(request: SearchRequest):
    security_result = SecurityAgent().run("rag_search", request.query)
    if security_result.status in {"blocked", "warning"}:
        return {
            "query": request.query,
            "top_k": request.top_k,
            "status": security_result.status,
            "suspicious_query": True,
            "requires_human_review": True,
            "security": security_result.output,
            "warnings": security_result.warnings,
            "errors": security_result.errors,
            "vector_backend": None,
            "qdrant_enabled": is_qdrant_enabled(),
            "results": [],
        }

    try:
        vector_store = get_vector_store()
        results = []
        for result in vector_store.search(request.query, request.top_k):
            metadata = result.get("metadata", {})
            results.append(
                {
                    **result,
                    "retrieval_method": metadata.get("retrieval_method", "mock"),
                }
            )
    except Exception:
        # Log full detail server-side; never leak exception text to the client
        # (paths / PII risk in a judicial system).
        logger.exception("RAG search failed")
        return {
            "query": request.query,
            "top_k": request.top_k,
            "status": "failed",
            "suspicious_query": False,
            "requires_human_review": True,
            "warnings": [],
            "errors": ["Erro interno ao executar a busca."],
            "vector_backend": "unknown",
            "qdrant_enabled": is_qdrant_enabled(),
            "results": [],
        }

    return {
        "query": request.query,
        "top_k": request.top_k,
        "status": "success",
        "suspicious_query": False,
        "requires_human_review": False,
        "warnings": [],
        "errors": [],
        "vector_backend": vector_store.backend_name,
        "qdrant_enabled": is_qdrant_enabled(),
        "results": results,
    }
