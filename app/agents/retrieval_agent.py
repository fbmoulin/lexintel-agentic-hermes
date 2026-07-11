from app.schemas.case import AgentResult
from app.services.bm25 import BM25Retriever
from app.services.fusion import reciprocal_rank_fusion
from app.services.qdrant_service import is_qdrant_enabled
from app.services.vector_store import VectorStore, get_vector_store


class HybridRetrievalAgent:
    """Hybrid legal retrieval: RRF fusion over the active retrievers.

    `search()` is the retrieval primitive (used by /rag/search and the eval).
    `run()` is the pipeline wrapper: it excludes the current case's own chunks
    (retrieval should surface precedents, not echo the case) and honours the
    index-completeness guard (an upsert_failed run did NOT index its chunks).
    """

    name = "HybridRetrievalAgent"

    def __init__(self, retrievers: list, rrf_k: int = 60, candidate_k: int = 10):
        self.retrievers = retrievers
        self._rrf_k = rrf_k
        self._candidate_k = candidate_k

    def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
        rankings = [
            retriever.search(query, top_k=self._candidate_k, filters=filters)
            for retriever in self.retrievers
        ]
        fused = reciprocal_rank_fusion(rankings, k=self._rrf_k)
        for ctx in fused:
            ctx["metadata"]["retrieval_method"] = "hybrid"
        return fused[:top_k]

    def run(
        self,
        case_id: str,
        query: str,
        top_k: int = 5,
        index_status: str = "ok",
    ) -> AgentResult:
        # Over-fetch, then drop the case's own chunks so top_k precedents remain.
        candidates = self.search(query, top_k=top_k * 3)
        precedents = [
            ctx for ctx in candidates if ctx["metadata"].get("case_id") != case_id
        ][:top_k]

        warnings: list[str] = []
        requires_review = False
        if index_status != "ok":
            # An upsert_failed run completed WITHOUT indexing its chunks, so the
            # retrievable corpus may be incomplete for this case. Degrade, do not halt.
            warnings.append(
                "Índice incompleto (index_status != ok); recuperação pode omitir chunks do caso."
            )
            requires_review = True

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="warning" if warnings else "success",
            output={
                "retrieved_context": precedents,
                "retrieval_method": "hybrid",
                "rankers_used": [r.backend_name for r in self.retrievers],
                "index_status": index_status,
                "requires_human_review": requires_review,
                "external_use_allowed": False,
            },
            warnings=warnings,
            requires_human_review=requires_review,
            external_use_allowed=False,
        )


def build_default_hybrid_agent(store: VectorStore | None = None) -> HybridRetrievalAgent:
    """Assemble the default hybrid agent from the active vector store.

    Offline (default): RRF(BM25, Mock token-overlap) — an ensemble of two
    lexical signals over the same tokenizer. With QDRANT_ENABLED: RRF(dense
    Qdrant, BM25) — a true dense+sparse hybrid.
    """
    store = store or get_vector_store()
    bm25 = BM25Retriever(store.snapshot_chunks())
    if is_qdrant_enabled():
        return HybridRetrievalAgent(retrievers=[store, bm25])
    return HybridRetrievalAgent(retrievers=[bm25, store])
