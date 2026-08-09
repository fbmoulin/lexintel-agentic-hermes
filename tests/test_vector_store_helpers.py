from app.services.vector_store import (
    DEFAULT_MOCK_CHUNKS,
    MockVectorStore,
    build_retrieved_context,
)


def _chunk():
    return {
        "chunk_id": "c1",
        "case_id": "case_x",
        "doc_id": "doc_1",
        "unit_type": "tese",
        "text": "Responsabilidade objetiva do banco.",
        "page_start": 1,
        "page_end": 1,
        "source": "seed",
        "metadata": {"source_ref": "Súmula 479/STJ"},
    }


def test_build_retrieved_context_stamps_method_and_flattens_metadata():
    ctx = build_retrieved_context(_chunk(), 0.5, "bm25")
    assert ctx["chunk_id"] == "c1"
    assert ctx["score"] == 0.5
    assert ctx["metadata"]["retrieval_method"] == "bm25"
    assert ctx["metadata"]["case_id"] == "case_x"
    assert ctx["metadata"]["unit_type"] == "tese"
    assert ctx["metadata"]["source_ref"] == "Súmula 479/STJ"


def test_snapshot_chunks_returns_independent_copy():
    store = MockVectorStore.seeded()
    snap = store.snapshot_chunks()
    assert len(snap) == len(DEFAULT_MOCK_CHUNKS)
    snap[0]["text"] = "MUTATED"
    assert store.snapshot_chunks()[0]["text"] != "MUTATED"


def test_mock_search_scores_via_shared_builder_six_dp():
    # MockVectorStore must emit exactly what the shared build_retrieved_context
    # produces (regression: a forked mapping rounded scores to 4 dp instead of
    # 6 and drifted from the single-source RetrievedContext shape).
    store = MockVectorStore(seed_chunks=[_chunk()])
    # Query tokens: {responsabilidade, banco, fraude}; overlap 2 of 3.
    [ctx] = store.search("responsabilidade banco fraude", top_k=1)
    assert ctx == build_retrieved_context(_chunk(), 2 / 3, "mock")
