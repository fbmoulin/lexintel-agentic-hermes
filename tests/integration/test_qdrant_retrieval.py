"""End-to-end retrieval against a LIVE Qdrant with REAL embeddings.

Skipped by default. Runs only when ALL hold:
  - LEX_KRATOS_ENABLE_QDRANT=true
  - fastembed + qdrant-client importable
  - a Qdrant reachable at QDRANT_HOST:QDRANT_PORT (default localhost:6533)

This proves the value over the token-overlap mock: a paraphrased query with no
shared content words still retrieves the right chunk.
"""

import os
import socket
import uuid

import pytest


def _should_run() -> bool:
    if os.getenv("LEX_KRATOS_ENABLE_QDRANT", "false").lower() != "true":
        return False
    try:
        import fastembed  # noqa: F401
        import qdrant_client  # noqa: F401
    except ImportError:
        return False
    host = os.getenv("QDRANT_HOST", "localhost")
    port_env = os.getenv("QDRANT_PORT", "6533")
    port = int(port_env) if port_env.isdigit() else 6533
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _should_run(),
    reason="needs LEX_KRATOS_ENABLE_QDRANT=true, fastembed+qdrant-client, live Qdrant",
)

CHUNK = {
    "chunk_id": "chunk_it_bancario_p1_tese",
    "case_id": "caso_integracao",
    "doc_id": "doc_bancario",
    "unit_type": "tese",
    "text": "Responsabilidade objetiva de banco por fraude praticada por terceiro.",
    "page_start": 1,
    "page_end": 1,
    "source": "seed.pdf",
    "metadata": {"doc_type": "precedente", "source_ref": "Súmula 479/STJ"},
}


@pytest.fixture
def store():
    from app.services.vector_store import QdrantVectorStore

    # Unique collection per run so the test is isolated and self-cleaning.
    name = f"lex_it_{uuid.uuid4().hex[:8]}"
    s = QdrantVectorStore(collection_name=name)
    yield s
    s._client.delete_collection(name)


def test_paraphrase_query_retrieves_semantically(store):
    store.upsert([CHUNK])
    # Paraphrase with NO shared content words vs the chunk — mock would miss it.
    results = store.search(
        "instituição financeira responde por golpe aplicado por estranho", top_k=3
    )
    assert results, "expected at least one semantic hit"
    assert results[0]["chunk_id"] == CHUNK["chunk_id"]
    assert results[0]["metadata"]["retrieval_method"] == "qdrant"
    assert results[0]["metadata"]["source_ref"] == "Súmula 479/STJ"


def test_reindex_is_idempotent(store):
    store.upsert([CHUNK])
    second = store.upsert([CHUNK])  # same chunk_id -> uuid5 -> replace, not duplicate
    assert second["stored_count"] == 1
