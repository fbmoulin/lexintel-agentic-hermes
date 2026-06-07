from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)


@router.post("/search")
def search(request: SearchRequest):
    # Mock inicial. Substituir por HybridRetrievalAgent + QdrantService.
    """
    Handle a search request and return a mocked search response.
    
    Parameters:
        request (SearchRequest): Input containing the search `query` and `top_k` number of results to return.
    
    Returns:
        response (dict): A dictionary echoing the input `query` and `top_k`, and a `results` list with mocked result objects. Each result object contains:
            - `chunk_id` (str): Identifier of the matched chunk.
            - `score` (float): Relevance score for the chunk.
            - `text` (str): Snippet or content of the chunk.
            - `retrieval_method` (str): Source or method used for retrieval (set to `"mock"` in this implementation).
    """
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
