from app.schemas.case import AgentResult, IndexingSummary
from app.services.chunking import chunk_extracted_text
from app.services.qdrant_service import is_qdrant_enabled
from app.services.vector_store import VectorStore, get_vector_store


class IndexingAgent:
    name = "IndexingAgent"

    def __init__(self, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or get_vector_store()

    @staticmethod
    def _chunk_unit_types(chunks: list[dict]) -> list[str]:
        return sorted({chunk.get("unit_type", "documento") for chunk in chunks})

    def run(self, case_id: str, extracted_text: list[dict]) -> AgentResult:
        chunks = chunk_extracted_text(case_id, extracted_text)
        warnings = []

        if not chunks:
            warnings.append("Nenhum chunk jurídico gerado para indexação mockada.")

        try:
            index_result = self.vector_store.upsert(chunks)
        except Exception as exc:
            summary = IndexingSummary(
                vector_backend=self.vector_store.backend_name,
                qdrant_enabled=is_qdrant_enabled(),
                chunk_count=len(chunks),
                indexed_count=0,
                skipped_count=len(chunks),
                chunk_unit_types=self._chunk_unit_types(chunks),
            )
            return AgentResult(
                case_id=case_id,
                agent_name=self.name,
                status="failed",
                output={
                    **summary.model_dump(),
                    "chunks": chunks,
                    "index_result": None,
                    "external_use_allowed": False,
                },
                errors=[str(exc)],
                external_use_allowed=False,
            )

        summary = IndexingSummary(
            vector_backend=self.vector_store.backend_name,
            qdrant_enabled=is_qdrant_enabled(),
            chunk_count=len(chunks),
            indexed_count=index_result["indexed_count"],
            skipped_count=max(len(chunks) - index_result["indexed_count"], 0),
            chunk_unit_types=self._chunk_unit_types(chunks),
        )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="warning" if warnings else "success",
            output={
                **summary.model_dump(),
                "chunks": chunks,
                "index_result": index_result,
                "external_use_allowed": False,
            },
            warnings=warnings,
            requires_human_review=bool(warnings),
            external_use_allowed=False,
        )
