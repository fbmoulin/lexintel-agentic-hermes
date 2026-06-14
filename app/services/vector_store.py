import os
import re
import unicodedata
import uuid
from copy import deepcopy
from typing import Protocol

from app.schemas.case import LegalChunk, RetrievedContext
from app.services.embeddings import Embedder, get_embedder
from app.services.qdrant_service import get_qdrant_client, is_qdrant_enabled

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
    # Accent-fold so real Portuguese queries ("saúde", "serviço") match indexed
    # text regardless of diacritics. Mirrors SecurityAgent.normalize_text.
    folded = unicodedata.normalize("NFKD", value.lower())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return {token for token in re.split(r"\W+", folded) if len(token) >= 3}


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
    """Real vector retrieval backed by Qdrant + local fastembed embeddings.

    Client and embedder are injectable (mirrors IndexingAgent(vector_store=...)),
    so the mapping/id logic is unit-testable without a live server or model.
    Emits the SAME RetrievedContext dict shape as MockVectorStore -> rag.py and
    downstream agents need no change.
    """

    backend_name = "qdrant"

    def __init__(
        self,
        client=None,
        embedder: Embedder | None = None,
        collection_name: str | None = None,
    ):
        self._client = client if client is not None else get_qdrant_client()
        self._embedder = embedder if embedder is not None else get_embedder()
        self._collection = (
            collection_name or os.getenv("QDRANT_COLLECTION") or "lex_kratos_chunks"
        )
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        from qdrant_client import models

        dim = self._embedder.dimension
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=dim, distance=models.Distance.COSINE
                ),
            )
            return
        existing = self._client.get_collection(self._collection)
        existing_dim = existing.config.params.vectors.size  # type: ignore[union-attr]
        if existing_dim != dim:
            raise RuntimeError(
                f"Coleção Qdrant '{self._collection}' tem dim={existing_dim}, "
                f"mas o modelo de embedding produz dim={dim}. Recrie a coleção."
            )

    @staticmethod
    def _point_id(chunk_id: str) -> str:
        # Deterministic id => re-indexing the same chunk upserts (replaces),
        # mirroring MockVectorStore's existing_ids de-dup.
        return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

    def upsert(self, chunks: list[dict]) -> dict:
        from qdrant_client import models

        validated = [LegalChunk.model_validate(chunk).model_dump() for chunk in chunks]
        if validated:
            vectors = self._embedder.embed_texts([c["text"] for c in validated])
            points = [
                models.PointStruct(
                    id=self._point_id(chunk["chunk_id"]),
                    vector=vector,
                    payload=chunk,
                )
                for chunk, vector in zip(validated, vectors)
            ]
            self._client.upsert(collection_name=self._collection, points=points)
        return {
            "vector_backend": self.backend_name,
            "indexed_count": len(validated),
            "stored_count": self._client.count(self._collection, exact=True).count,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        query_vector = self._embedder.embed_query(query)
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=self._build_filter(filters),
            with_payload=True,
        )
        return [self._point_to_context(point) for point in response.points]

    @staticmethod
    def _build_filter(filters: dict | None):
        if not filters:
            return None
        from qdrant_client import models

        # Filters target chunk metadata (mirrors MockVectorStore._matches_filters);
        # payload stores the full chunk, so metadata is nested under "metadata.*".
        return models.Filter(
            must=[
                models.FieldCondition(
                    key=f"metadata.{key}", match=models.MatchValue(value=value)
                )
                for key, value in filters.items()
            ]
        )

    @staticmethod
    def _point_to_context(point) -> dict:
        payload = point.payload or {}
        metadata = dict(payload.get("metadata", {}))
        metadata.update(
            {
                "case_id": payload.get("case_id"),
                "unit_type": payload.get("unit_type"),
                "retrieval_method": "qdrant",
            }
        )
        context = RetrievedContext(
            chunk_id=payload["chunk_id"],
            doc_id=payload["doc_id"],
            score=round(point.score, 4),
            text=payload["text"],
            source=payload.get("source"),
            page_start=payload.get("page_start"),
            page_end=payload.get("page_end"),
            metadata=metadata,
        )
        return context.model_dump()


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
