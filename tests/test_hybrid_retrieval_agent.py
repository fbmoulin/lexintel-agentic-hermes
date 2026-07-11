from app.agents.retrieval_agent import HybridRetrievalAgent, build_default_hybrid_agent
from app.services.bm25 import BM25Retriever
from app.services.vector_store import MockVectorStore

CORPUS = [
    {
        "chunk_id": "prec_banco", "case_id": "seed", "doc_id": "d1", "unit_type": "tese",
        "text": "Responsabilidade objetiva do banco por fraude.", "page_start": 1,
        "page_end": 1, "source": "seed", "metadata": {"source_ref": "Súmula 479/STJ"},
    },
    {
        "chunk_id": "prec_saude", "case_id": "seed", "doc_id": "d2", "unit_type": "tese",
        "text": "Plano de saúde e rol da ANS, Tema 1082.", "page_start": 1,
        "page_end": 1, "source": "seed", "metadata": {"source_ref": "Tema 1082/STJ"},
    },
    {
        "chunk_id": "own_case", "case_id": "case_atual", "doc_id": "d9", "unit_type": "documento",
        "text": "Fraude bancária narrada na petição do caso atual.", "page_start": 1,
        "page_end": 1, "source": "case", "metadata": {"source_ref": "peticao"},
    },
]


def _agent():
    store = MockVectorStore(seed_chunks=CORPUS)
    bm25 = BM25Retriever(store.snapshot_chunks())
    return HybridRetrievalAgent(retrievers=[bm25, store])


def test_search_fuses_and_stamps_hybrid_method():
    results = _agent().search("fraude no banco", top_k=3)
    assert results[0]["metadata"]["retrieval_method"] == "hybrid"
    assert "fusion_detail" in results[0]["metadata"]
    assert results[0]["chunk_id"] in {"prec_banco", "own_case"}


def test_run_excludes_own_case_chunks():
    # top_k=1: only "prec_banco" matches "fraude bancária" (prec_saude is about
    # planos de saúde, zero overlap), so 1 requested == 1 precedent => full, success.
    # Intent here is own-case exclusion, not shortfall.
    result = _agent().run(case_id="case_atual", query="fraude bancária", top_k=1)
    retrieved_ids = [c["chunk_id"] for c in result.output["retrieved_context"]]
    assert "own_case" not in retrieved_ids
    assert "prec_banco" in retrieved_ids
    assert result.status == "success"


def test_run_flags_incomplete_index():
    result = _agent().run(
        case_id="case_atual", query="fraude", top_k=2, index_status="upsert_failed"
    )
    assert result.status == "warning"
    assert result.requires_human_review is True
    assert any("index_status=upsert_failed" in w for w in result.warnings)
    assert result.output["retrieved_context"]  # still returns precedents (degrade, not halt)


def test_run_external_use_never_allowed():
    result = _agent().run(case_id="case_atual", query="fraude", top_k=5)
    assert result.external_use_allowed is False


def test_factory_builds_offline_ensemble():
    store = MockVectorStore(seed_chunks=CORPUS)
    agent = build_default_hybrid_agent(store=store)
    methods = {r.backend_name for r in agent.retrievers}
    assert methods == {"bm25", "mock"}


def test_run_warns_on_precedent_shortfall_when_own_case_dominates():
    # Many own-case chunks that all match the query would crowd precedents out of
    # a naive top_k*3 pool; the shortfall must surface as a warning, not silent success.
    corpus = [
        {
            "chunk_id": f"own_{i}", "case_id": "case_atual", "doc_id": f"c{i}",
            "unit_type": "documento", "text": "Fraude bancária narrada na petição.",
            "page_start": 1, "page_end": 1, "source": "case", "metadata": {},
        }
        for i in range(12)
    ] + [
        {
            "chunk_id": "prec_banco", "case_id": "seed", "doc_id": "d1", "unit_type": "tese",
            "text": "Responsabilidade objetiva do banco por fraude.", "page_start": 1,
            "page_end": 1, "source": "seed", "metadata": {"source_ref": "Súmula 479/STJ"},
        }
    ]
    store = MockVectorStore(seed_chunks=corpus)
    bm25 = BM25Retriever(store.snapshot_chunks())
    agent = HybridRetrievalAgent(retrievers=[bm25, store])
    result = agent.run(case_id="case_atual", query="fraude bancária", top_k=5)
    ids = [c["chunk_id"] for c in result.output["retrieved_context"]]
    assert all(not i.startswith("own_") for i in ids)  # own-case excluded
    assert len(ids) < 5  # genuine shortfall (only 1 precedent exists)
    assert result.status == "warning"
    assert any("precedentes solicitados" in w for w in result.warnings)


def test_raises_on_empty_retrievers():
    import pytest
    with pytest.raises(ValueError):
        HybridRetrievalAgent(retrievers=[])
