"""Empirical acceptance gate (spec §7): the hybrid retriever must MEET OR BEAT
the Mock golden baseline, not merely clear the 0.85 threshold. If this fails,
the hybrid is a quality regression — stop and replan before wiring."""

from statistics import mean

from app.agents.retrieval_agent import HybridRetrievalAgent
from app.evals.run_eval import (
    build_eval_store,
    evaluate_item,
    load_corpus,
    load_dataset,
)
from app.services.bm25 import BM25Retriever
from app.services.vector_store import MockVectorStore

# Mock golden baseline documented in docs/10_RAG_EVAL_CONTRACT.md.
BASELINE_RECALL_AT_1 = 0.9375
BASELINE_RECALL_AT_3 = 1.0
BASELINE_MRR = 1.0


def _hybrid_eval_store():
    corpus = load_corpus()
    mock = MockVectorStore(seed_chunks=corpus)
    bm25 = BM25Retriever(mock.snapshot_chunks())
    return HybridRetrievalAgent(retrievers=[bm25, mock])


def _aggregate(store):
    dataset = load_dataset("app/evals/golden_dataset.jsonl")
    results = [evaluate_item(item, store) for item in dataset]
    return {
        "recall_at_1": mean(r["recall_at_1"] for r in results),
        "recall_at_3": mean(r["recall_at_3"] for r in results),
        "mrr": mean(r["mrr"] for r in results),
    }


def test_mock_baseline_is_still_what_the_contract_claims():
    m = _aggregate(build_eval_store())
    assert m["recall_at_1"] == BASELINE_RECALL_AT_1
    assert m["recall_at_3"] == BASELINE_RECALL_AT_3
    assert m["mrr"] == BASELINE_MRR


def test_hybrid_meets_or_beats_mock_baseline():
    h = _aggregate(_hybrid_eval_store())
    assert h["recall_at_1"] >= BASELINE_RECALL_AT_1, h
    assert h["recall_at_3"] >= BASELINE_RECALL_AT_3, h
    assert h["mrr"] >= BASELINE_MRR, h
