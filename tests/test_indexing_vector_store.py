import pytest
from pydantic import ValidationError

from app.agents.indexing_agent import IndexingAgent
from app.schemas.case import LegalChunk
from app.services.chunking import chunk_extracted_text
from app.services.qdrant_service import get_qdrant_client
from app.services.vector_store import (
    MockVectorStore,
    get_vector_store,
    reset_mock_vector_store,
)

EXTRACTED_TEXT = [
    {
        "doc_id": "doc_1",
        "file_path": "peticao_inicial.pdf",
        "doc_type": "peticao_inicial",
        "page": 1,
        "text": "Pedido de indenização por fraude bancária via pix.",
        "quality_score": 0.92,
        "extraction_method": "mock_filename_template",
        "warnings": [],
    },
    {
        "doc_id": "doc_2",
        "file_path": "contestacao.pdf",
        "doc_type": "contestacao",
        "page": 1,
        "text": "Contestação com defesa de culpa exclusiva de terceiro.",
        "quality_score": 0.92,
        "extraction_method": "mock_filename_template",
        "warnings": [],
    },
]


def test_chunk_extracted_text_generates_deterministic_legal_chunks():
    chunks = chunk_extracted_text("caso_indexacao_001", EXTRACTED_TEXT)

    assert [chunk["chunk_id"] for chunk in chunks] == [
        "chunk_caso_indexacao_001_doc_1_p1_pedido",
        "chunk_caso_indexacao_001_doc_2_p1_contestacao",
    ]
    assert [chunk["unit_type"] for chunk in chunks] == [
        "pedido",
        "contestacao",
    ]
    assert all(
        chunk["metadata"]["chunking_strategy"] == "legal_unit_mock_v0.1"
        for chunk in chunks
    )


def test_chunk_extracted_text_skips_empty_text_and_normalizes_page():
    chunks = chunk_extracted_text(
        "caso_indexacao_defensiva_001",
        [
            {
                "doc_id": "doc_empty",
                "file_path": "pagina_vazia.pdf",
                "doc_type": "peticao_inicial",
                "page": 0,
                "text": "   ",
                "quality_score": 0.1,
            },
            {
                "doc_id": "doc_valid",
                "file_path": "peticao_inicial.pdf",
                "doc_type": "peticao_inicial",
                "page": 0,
                "text": " Pedido com texto válido para indexação. ",
                "quality_score": 0.92,
            },
        ],
    )

    assert len(chunks) == 1
    assert chunks[0]["chunk_id"] == (
        "chunk_caso_indexacao_defensiva_001_doc_valid_p1_pedido"
    )
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["text"] == "Pedido com texto válido para indexação."


def test_legal_chunk_rejects_invalid_page_range():
    with pytest.raises(ValidationError, match="page_end"):
        LegalChunk(
            chunk_id="chunk_invalid_page_range",
            case_id="caso_invalid_page_range",
            doc_id="doc_1",
            unit_type="documento",
            text="Texto válido.",
            page_start=3,
            page_end=2,
        )


def test_mock_vector_store_indexes_and_searches_chunks():
    chunks = chunk_extracted_text("caso_indexacao_001", EXTRACTED_TEXT)
    vector_store = MockVectorStore()

    upsert_result = vector_store.upsert(chunks)
    results = vector_store.search("fraude bancária indenização", top_k=2)

    assert upsert_result["vector_backend"] == "mock"
    assert upsert_result["indexed_count"] == 2
    assert results[0]["chunk_id"] == "chunk_caso_indexacao_001_doc_1_p1_pedido"
    assert results[0]["metadata"]["retrieval_method"] == "mock"


def test_indexing_agent_uses_mock_vector_store_by_default():
    result = IndexingAgent(vector_store=MockVectorStore()).run(
        "caso_indexacao_002",
        EXTRACTED_TEXT,
    )

    assert result.status == "success"
    assert result.output["vector_backend"] == "mock"
    assert result.output["qdrant_enabled"] is False
    assert result.output["chunk_count"] == 2
    assert result.output["indexed_count"] == 2
    assert result.output["chunk_unit_types"] == ["contestacao", "pedido"]
    # A successful (or empty) upsert is queryable as "ok" so a systemic run of
    # index failures is distinguishable from content warnings (see below).
    assert result.output["index_status"] == "ok"


def test_indexing_agent_marks_empty_chunks_for_review():
    result = IndexingAgent(vector_store=MockVectorStore()).run(
        "caso_indexacao_vazio_001",
        [],
    )

    assert result.status == "warning"
    assert result.requires_human_review is True
    assert result.output["chunk_count"] == 0
    assert result.output["indexed_count"] == 0


def test_indexing_agent_returns_warning_result_on_upsert_error():
    # Indexing is best-effort: the RAG index serves future retrieval, not this
    # case's FIRAC analysis. An upsert failure degrades to a review-flagged
    # WARNING (not a hard failure) so the legal analysis still completes.
    class FailingVectorStore:
        backend_name = "mock"

        def upsert(self, chunks: list[dict]) -> dict:
            raise ValueError("falha simulada de upsert")

        def search(
            self,
            query: str,
            top_k: int = 5,
            filters: dict | None = None,
        ) -> list[dict]:
            return []

    result = IndexingAgent(vector_store=FailingVectorStore()).run(
        "caso_indexacao_falha_001",
        EXTRACTED_TEXT,
    )

    assert result.status == "warning"
    assert result.requires_human_review is True
    assert result.output["indexed_count"] == 0
    assert result.output["skipped_count"] == 2
    # Distinct, queryable tag: a systemic index outage (every case tagged
    # "upsert_failed") is separable from ordinary content warnings.
    assert result.output["index_status"] == "upsert_failed"
    # Generic, client-safe message — raw exception text must not leak.
    assert result.warnings == [
        "Falha na indexação mockada; revisão humana recomendada."
    ]
    assert result.errors == []


def test_get_vector_store_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("LEX_KRATOS_ENABLE_QDRANT", raising=False)
    reset_mock_vector_store()

    vector_store = get_vector_store()

    assert vector_store.backend_name == "mock"


def test_get_vector_store_reuses_mock_instance(monkeypatch):
    monkeypatch.delenv("LEX_KRATOS_ENABLE_QDRANT", raising=False)
    vector_store = reset_mock_vector_store()
    chunks = chunk_extracted_text("caso_indexacao_persistente_001", EXTRACTED_TEXT)

    vector_store.upsert(chunks)
    reused_store = get_vector_store()
    results = reused_store.search("fraude pix indenização", top_k=3)

    assert reused_store is vector_store
    assert results[0]["metadata"]["case_id"] == "caso_indexacao_persistente_001"


def test_qdrant_client_requires_explicit_feature_flag(monkeypatch):
    monkeypatch.delenv("LEX_KRATOS_ENABLE_QDRANT", raising=False)

    with pytest.raises(RuntimeError, match="Qdrant real está desativado"):
        get_qdrant_client()
