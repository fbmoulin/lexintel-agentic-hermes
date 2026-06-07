from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


@router.post("/search")
def search(request: SearchRequest):
    # Mock inicial. Substituir por HybridRetrievalAgent + QdrantService.
    return {
        "query": request.query,
        "top_k": request.top_k,
        "results": [
            {
                "chunk_id": "mock_chunk_001",
                "score": 0.85,
                "text": "Resultado simulado. Conectar Qdrant na próxima fase.",
                "retrieval_method": "mock"
            }
        ]
    }
