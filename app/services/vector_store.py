import re
from copy import deepcopy
from typing import Protocol

from app.schemas.case import LegalChunk, RetrievedContext
from app.services.qdrant_service import is_qdrant_enabled

DEFAULT_MOCK_CHUNKS = [
    {
        "chunk_id": "mock_bancario_sumula_479",
        "case_id": "mock_rag_seed",
        "doc_id": "mock_doc_bancario",
        "unit_type": "tese",
        "text": "Responsabilidade objetiva de banco por fraude praticada por terceiro.",
        "page_start": 1,
        "page_end": 1,
        "source": "mock_seed",
        "metadata": {
            "doc_type": "precedente_mockado",
            "source_ref": "Súmula 479/STJ",
            "retrieval_method": "mock",
        },
    },
    {
        "chunk_id": "mock_saude_tema_1082",
        "case_id": "mock_rag_seed",
        "doc_id": "mock_doc_saude",
        "unit_type": "tese",
        "text": "Plano de saúde, rol da ANS, Tema 1082/STJ e Lei 14.454/2022.",
        "page_start": 1,
        "page_end": 1,
        "source": "mock_seed",
        "metadata": {
            "doc_type": "precedente_mockado",
            "source_ref": "Tema 1082/STJ",
            "retrieval_method": "mock",
        },
    },
    {
        "chunk_id": "mock_processual_art_300",
        "case_id": "mock_rag_seed",
        "doc_id": "mock_doc_processual",
        "unit_type": "fundamentos",
        "text": "Tutela de urgência exige probabilidade do direito e perigo de dano, art. 300 CPC.",
        "page_start": 1,
        "page_end": 1,
        "source": "mock_seed",
        "metadata": {
            "doc_type": "lei_mockada",
            "source_ref": "art. 300 CPC",
            "retrieval_method": "mock",
        },
    },
]


class VectorStore(Protocol):
    backend_name: str

    def upsert(self, chunks: list[dict]) -> dict: ...

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]: ...


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"\W+", value.lower()) if len(token) >= 3}


class MockVectorStore:
    backend_name = "mock"

    def __init__(self, seed_chunks: list[dict] | None = None):
        self._chunks = [
            LegalChunk.model_validate(chunk).model_dump()
            for chunk in (seed_chunks or [])
        ]

    @classmethod
    def seeded(cls) -> "MockVectorStore":
        return cls(seed_chunks=deepcopy(DEFAULT_MOCK_CHUNKS))

    def upsert(self, chunks: list[dict]) -> dict:
        indexed_chunks = [
            LegalChunk.model_validate(chunk).model_dump() for chunk in chunks
        ]
        existing_ids = {chunk["chunk_id"] for chunk in indexed_chunks}
        self._chunks = [
            chunk for chunk in self._chunks if chunk["chunk_id"] not in existing_ids
        ]
        self._chunks.extend(indexed_chunks)
        return {
            "vector_backend": self.backend_name,
            "indexed_count": len(indexed_chunks),
            "stored_count": len(self._chunks),
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        query_tokens = _tokenize(query)
        scored = []
        for chunk in self._chunks:
            if filters and not self._matches_filters(chunk, filters):
                continue

            text_tokens = _tokenize(chunk["text"])
            metadata_tokens = _tokenize(
                " ".join(str(value) for value in chunk["metadata"].values())
            )
            overlap = len(query_tokens & (text_tokens | metadata_tokens))
            score = overlap / max(len(query_tokens), 1)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        return [
            self._to_retrieved_context(chunk, score) for score, chunk in scored[:top_k]
        ]

    @staticmethod
    def _matches_filters(chunk: dict, filters: dict) -> bool:
        return all(
            chunk["metadata"].get(key) == value for key, value in filters.items()
        )

    @staticmethod
    def _to_retrieved_context(chunk: dict, score: float) -> dict:
        context = RetrievedContext(
            chunk_id=chunk["chunk_id"],
            doc_id=chunk["doc_id"],
            score=round(score, 4),
            text=chunk["text"],
            source=chunk.get("source"),
            page_start=chunk["page_start"],
            page_end=chunk["page_end"],
            metadata={
                **chunk["metadata"],
                "case_id": chunk["case_id"],
                "unit_type": chunk["unit_type"],
                "retrieval_method": chunk["metadata"].get("retrieval_method", "mock"),
            },
        )
        return context.model_dump()


class QdrantVectorStore:
    backend_name = "qdrant"

    def upsert(self, chunks: list[dict]) -> dict:
        raise RuntimeError(
            "Qdrant real está protegido por feature flag e não é implementado na v0.1."
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        raise RuntimeError(
            "Qdrant real está protegido por feature flag e não é implementado na v0.1."
        )


_MOCK_STORE_INSTANCE: MockVectorStore | None = None


def reset_mock_vector_store() -> MockVectorStore:
    global _MOCK_STORE_INSTANCE
    _MOCK_STORE_INSTANCE = MockVectorStore.seeded()
    return _MOCK_STORE_INSTANCE


def get_vector_store() -> VectorStore:
    global _MOCK_STORE_INSTANCE
    if is_qdrant_enabled():
        return QdrantVectorStore()
    if _MOCK_STORE_INSTANCE is None:
        _MOCK_STORE_INSTANCE = MockVectorStore.seeded()
    return _MOCK_STORE_INSTANCE
