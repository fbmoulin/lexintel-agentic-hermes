import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agents.security_agent import SecurityAgent
from app.services.qdrant_service import is_qdrant_enabled

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
        from app.agents.retrieval_agent import build_default_hybrid_agent

        agent = build_default_hybrid_agent()
        results = []
        for result in agent.search(request.query, request.top_k):
            metadata = result.get("metadata", {})
            results.append(
                {
                    **result,
                    "retrieval_method": metadata.get("retrieval_method", "hybrid"),
                }
            )
        vector_backend = "hybrid"
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
        "vector_backend": vector_backend,
        "qdrant_enabled": is_qdrant_enabled(),
        "results": results,
    }
