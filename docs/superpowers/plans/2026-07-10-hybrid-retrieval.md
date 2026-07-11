# HybridRetrievalAgent (P6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver real hybrid legal retrieval (RRF fusion of BM25 + dense/lexical), mock-first and deterministic by default, as the single retriever of record across pipeline, `/rag/search`, and eval.

**Architecture:** Two pure/injectable retrieval primitives (`BM25Retriever`, `reciprocal_rank_fusion`) compose into a `HybridRetrievalAgent`. Offline default fuses BM25 + the existing `MockVectorStore` token-overlap (an ensemble of two lexical signals, honestly labelled); when `QDRANT_ENABLED=1` the dense `QdrantVectorStore` replaces the token-overlap side. An empirical gate (hybrid ≥ Mock golden baseline) runs *before* any wiring.

**Tech Stack:** Python 3, FastAPI, Pydantic, pytest. No new runtime dependency (BM25 is pure Python). Qdrant/fastembed remain opt-in.

**Design spec:** `docs/superpowers/specs/2026-07-10-hybrid-retrieval-design.md`

**Baseline before starting:** 123 passed, 2 skipped. Run `python -m pytest -q` after each task; the count only grows.

---

## File Structure

- **Create** `app/services/bm25.py` — `BM25Retriever` (Okapi BM25, sparse, deterministic).
- **Create** `app/services/fusion.py` — `reciprocal_rank_fusion` (pure function, audit trail).
- **Create** `app/agents/retrieval_agent.py` — `HybridRetrievalAgent` (`search()` primitive + `run()` pipeline wrapper) and `build_default_hybrid_agent()` factory.
- **Modify** `app/services/vector_store.py` — add module helper `build_retrieved_context(...)` and `snapshot_chunks()` on both stores + Protocol.
- **Modify** `app/api/rag.py` — `/rag/search` uses the hybrid agent.
- **Modify** `app/agents/orchestrator.py` — new `retrieval` step, bump trace to `v0.3`.
- **Modify** `app/agents/registry.py` — `HybridRetrievalAgent` → `implemented`.
- **Modify** `app/evals/run_eval.py` — score the hybrid; add non-regression thresholds.
- **Modify** docs: `08_TRACE_CONTRACT.md`, `10_RAG_EVAL_CONTRACT.md`, `README.md`, `04_BACKLOG.md`.
- **Create tests** `tests/test_bm25_retriever.py`, `tests/test_fusion.py`, `tests/test_hybrid_retrieval_agent.py`, `tests/test_hybrid_eval_gate.py`.
- **Modify tests** `tests/test_rag_api.py` (existing), orchestrator + eval tests as they surface.

---

## Task 1: `build_retrieved_context` helper + store snapshots

**Files:**
- Modify: `app/services/vector_store.py`
- Test: `tests/test_vector_store_helpers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_vector_store_helpers.py
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
    # Mutating the snapshot must not corrupt the store's corpus.
    assert store.snapshot_chunks()[0]["text"] != "MUTATED"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_vector_store_helpers.py -q`
Expected: FAIL with `ImportError: cannot import name 'build_retrieved_context'`.

- [ ] **Step 3: Write minimal implementation**

In `app/services/vector_store.py`, add the module-level helper after `_tokenize` (near line 79):

```python
def build_retrieved_context(chunk: dict, score: float, method: str) -> dict:
    """Map a LegalChunk dict to a RetrievedContext dict with retrieval_method.

    Shared by every retriever so the RetrievedContext shape (and the
    case_id/unit_type/retrieval_method flattening) is defined in one place.
    """
    context = RetrievedContext(
        chunk_id=chunk["chunk_id"],
        doc_id=chunk["doc_id"],
        score=round(score, 6),
        text=chunk["text"],
        source=chunk.get("source"),
        page_start=chunk.get("page_start"),
        page_end=chunk.get("page_end"),
        metadata={
            **chunk.get("metadata", {}),
            "case_id": chunk["case_id"],
            "unit_type": chunk["unit_type"],
            "retrieval_method": method,
        },
    )
    return context.model_dump()
```

Add `snapshot_chunks` to `MockVectorStore` (after `upsert`):

```python
    def snapshot_chunks(self) -> list[dict]:
        return deepcopy(self._chunks)
```

Add `snapshot_chunks` to `QdrantVectorStore` (scroll the collection; opt-in path):

```python
    def snapshot_chunks(self, limit: int = 10_000) -> list[dict]:
        points, _ = self._client.scroll(
            collection_name=self._collection,
            limit=limit,
            with_payload=True,
        )
        return [dict(point.payload or {}) for point in points]
```

Add `snapshot_chunks` to the `VectorStore` Protocol:

```python
    def snapshot_chunks(self) -> list[dict]: ...
```

`deepcopy` is already imported at the top of the module.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_vector_store_helpers.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: 125 passed, 2 skipped.

- [ ] **Step 6: Commit**

```bash
git add app/services/vector_store.py tests/test_vector_store_helpers.py
git commit -m "feat(retrieval): shared build_retrieved_context + store snapshot_chunks"
```

---

## Task 2: `BM25Retriever`

**Files:**
- Create: `app/services/bm25.py`
- Test: `tests/test_bm25_retriever.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bm25_retriever.py
from app.services.bm25 import BM25Retriever

CHUNKS = [
    {
        "chunk_id": "banco", "case_id": "seed", "doc_id": "d1", "unit_type": "tese",
        "text": "Responsabilidade objetiva do banco por fraude de terceiro.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "Súmula 479/STJ"},
    },
    {
        "chunk_id": "saude", "case_id": "seed", "doc_id": "d2", "unit_type": "tese",
        "text": "Plano de saúde e rol da ANS, Tema 1082.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "Tema 1082/STJ", "area": "saude"},
    },
    {
        "chunk_id": "tutela", "case_id": "seed", "doc_id": "d3", "unit_type": "fundamentos",
        "text": "Tutela de urgência exige probabilidade do direito, art. 300 CPC.",
        "page_start": 1, "page_end": 1, "source": "seed",
        "metadata": {"source_ref": "art. 300 CPC"},
    },
]


def test_ranks_most_relevant_first():
    retriever = BM25Retriever(CHUNKS)
    results = retriever.search("fraude no banco", top_k=3)
    assert results[0]["chunk_id"] == "banco"
    assert results[0]["metadata"]["retrieval_method"] == "bm25"


def test_accent_folding_matches():
    retriever = BM25Retriever(CHUNKS)
    # "saude" (no accent) must match the accented "saúde" via shared _tokenize.
    results = retriever.search("saude ans", top_k=1)
    assert results[0]["chunk_id"] == "saude"


def test_applies_metadata_filters():
    retriever = BM25Retriever(CHUNKS)
    results = retriever.search("rol", top_k=3, filters={"area": "saude"})
    assert [r["chunk_id"] for r in results] == ["saude"]


def test_deterministic_tie_break_by_chunk_id():
    tied = [
        {**CHUNKS[0], "chunk_id": "b_id", "text": "termo comum unico"},
        {**CHUNKS[0], "chunk_id": "a_id", "text": "termo comum unico"},
    ]
    retriever = BM25Retriever(tied)
    results = retriever.search("termo comum unico", top_k=2)
    assert [r["chunk_id"] for r in results] == ["a_id", "b_id"]


def test_no_match_returns_empty():
    retriever = BM25Retriever(CHUNKS)
    assert retriever.search("xyzxyz inexistente", top_k=3) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bm25_retriever.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.bm25'`.

- [ ] **Step 3: Write minimal implementation**

```python
# app/services/bm25.py
import math
from collections import Counter

from app.services.vector_store import (
    LegalChunk,
    _tokenize,
    build_retrieved_context,
)


class BM25Retriever:
    """Okapi BM25 over LegalChunk text — sparse, deterministic, pure Python.

    Shares _tokenize (accent-fold) with the lexical store so both sides of the
    offline ensemble see the same terms. Emits the same RetrievedContext shape
    as MockVectorStore / QdrantVectorStore.
    """

    backend_name = "bm25"

    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self._k1 = k1
        self._b = b
        self._chunks = [
            LegalChunk.model_validate(chunk).model_dump() for chunk in chunks
        ]
        self._doc_tokens = [Counter(_tokenize(chunk["text"])) for chunk in self._chunks]
        self._doc_len = [sum(counter.values()) for counter in self._doc_tokens]
        self._avgdl = (sum(self._doc_len) / len(self._doc_len)) if self._doc_len else 0.0
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        n = len(self._chunks)
        df: Counter = Counter()
        for counter in self._doc_tokens:
            df.update(counter.keys())
        # ln(1 + (N - df + 0.5)/(df + 0.5)) keeps idf non-negative (Okapi/BM25+ variant).
        return {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def _score(self, query_tokens: list[str], index: int) -> float:
        counter = self._doc_tokens[index]
        length = self._doc_len[index]
        score = 0.0
        for term in query_tokens:
            tf = counter.get(term, 0)
            if tf == 0:
                continue
            idf = self._idf.get(term, 0.0)
            denom = tf + self._k1 * (1 - self._b + self._b * length / (self._avgdl or 1))
            score += idf * (tf * (self._k1 + 1)) / denom
        return score

    @staticmethod
    def _matches_filters(chunk: dict, filters: dict) -> bool:
        return all(chunk["metadata"].get(key) == value for key, value in filters.items())

    def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
        query_tokens = list(_tokenize(query))
        scored = []
        for index, chunk in enumerate(self._chunks):
            if filters and not self._matches_filters(chunk, filters):
                continue
            score = self._score(query_tokens, index)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
        return [build_retrieved_context(chunk, score, "bm25") for score, chunk in scored[:top_k]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bm25_retriever.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: 130 passed, 2 skipped.

- [ ] **Step 6: Commit**

```bash
git add app/services/bm25.py tests/test_bm25_retriever.py
git commit -m "feat(retrieval): Okapi BM25Retriever (sparse, deterministic)"
```

---

## Task 3: `reciprocal_rank_fusion`

**Files:**
- Create: `app/services/fusion.py`
- Test: `tests/test_fusion.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fusion.py
from app.services.fusion import reciprocal_rank_fusion


def _ctx(chunk_id):
    return {"chunk_id": chunk_id, "score": 0.0, "text": chunk_id, "metadata": {}}


def test_fuses_two_rankings_by_reciprocal_rank():
    a = [_ctx("x"), _ctx("y"), _ctx("z")]   # ranks 1,2,3
    b = [_ctx("y"), _ctx("x")]              # ranks 1,2
    fused = reciprocal_rank_fusion([a, b], k=60)
    # y: 1/62 + 1/61 ; x: 1/61 + 1/62  -> equal score, tie-break by chunk_id -> x before y
    assert [c["chunk_id"] for c in fused[:2]] == ["x", "y"]


def test_records_fusion_detail_per_ranker():
    a = [_ctx("x")]
    b = [_ctx("x")]
    fused = reciprocal_rank_fusion([a, b], k=60)
    detail = fused[0]["metadata"]["fusion_detail"]
    assert len(detail) == 2
    assert {d["ranker"] for d in detail} == {0, 1}
    assert all(d["rank"] == 1 for d in detail)


def test_chunk_in_single_ranking_still_ranked():
    a = [_ctx("x"), _ctx("only_a")]
    b = [_ctx("x")]
    fused = reciprocal_rank_fusion([a, b], k=60)
    ids = [c["chunk_id"] for c in fused]
    assert set(ids) == {"x", "only_a"}
    assert ids[0] == "x"  # x appears in both -> higher fused score


def test_empty_rankings_return_empty():
    assert reciprocal_rank_fusion([[], []], k=60) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fusion.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.fusion'`.

- [ ] **Step 3: Write minimal implementation**

```python
# app/services/fusion.py
from copy import deepcopy


def reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    """Fuse N ranked RetrievedContext lists by Reciprocal Rank Fusion.

    Fused score of a chunk = sum over rankings of 1/(k + rank) (rank 1-indexed).
    Rank-based, so it is scale-independent across dense/sparse/lexical scorers.
    Deterministic; ties broken by chunk_id. Each fused item records
    metadata.fusion_detail = [{ranker, rank, contribution}, ...] as an audit trail.
    """
    fused_score: dict[str, float] = {}
    detail: dict[str, list[dict]] = {}
    representative: dict[str, dict] = {}

    for ranker_index, ranking in enumerate(rankings):
        for rank, ctx in enumerate(ranking, start=1):
            chunk_id = ctx["chunk_id"]
            contribution = 1.0 / (k + rank)
            fused_score[chunk_id] = fused_score.get(chunk_id, 0.0) + contribution
            detail.setdefault(chunk_id, []).append(
                {"ranker": ranker_index, "rank": rank, "contribution": round(contribution, 6)}
            )
            representative.setdefault(chunk_id, deepcopy(ctx))

    ordered = sorted(fused_score, key=lambda cid: (-fused_score[cid], cid))
    results = []
    for chunk_id in ordered:
        ctx = representative[chunk_id]
        ctx["score"] = round(fused_score[chunk_id], 6)
        ctx["metadata"] = {**ctx.get("metadata", {}), "fusion_detail": detail[chunk_id]}
        results.append(ctx)
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fusion.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: 134 passed, 2 skipped.

- [ ] **Step 6: Commit**

```bash
git add app/services/fusion.py tests/test_fusion.py
git commit -m "feat(retrieval): reciprocal_rank_fusion (pure, audit trail)"
```

---

## Task 4: `HybridRetrievalAgent` (`search` + `run` + factory)

**Files:**
- Create: `app/agents/retrieval_agent.py`
- Test: `tests/test_hybrid_retrieval_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hybrid_retrieval_agent.py
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
    result = _agent().run(case_id="case_atual", query="fraude bancária", top_k=5)
    retrieved_ids = [c["chunk_id"] for c in result.output["retrieved_context"]]
    assert "own_case" not in retrieved_ids
    assert "prec_banco" in retrieved_ids
    assert result.status == "success"


def test_run_flags_incomplete_index():
    result = _agent().run(
        case_id="case_atual", query="fraude", top_k=5, index_status="upsert_failed"
    )
    assert result.status == "warning"
    assert result.requires_human_review is True
    assert result.output["retrieved_context"] is not None


def test_run_external_use_never_allowed():
    result = _agent().run(case_id="case_atual", query="fraude", top_k=5)
    assert result.external_use_allowed is False


def test_factory_builds_offline_ensemble():
    store = MockVectorStore(seed_chunks=CORPUS)
    agent = build_default_hybrid_agent(store=store)
    methods = {r.backend_name for r in agent.retrievers}
    assert methods == {"bm25", "mock"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_hybrid_retrieval_agent.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.agents.retrieval_agent'`.

- [ ] **Step 3: Write minimal implementation**

```python
# app/agents/retrieval_agent.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_hybrid_retrieval_agent.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: 139 passed, 2 skipped.

- [ ] **Step 6: Commit**

```bash
git add app/agents/retrieval_agent.py tests/test_hybrid_retrieval_agent.py
git commit -m "feat(retrieval): HybridRetrievalAgent (RRF search + pipeline run + factory)"
```

---

## Task 5: Empirical gate — hybrid ≥ Mock golden baseline (GO/NO-GO)

**This task is the go/no-go checkpoint from spec §7. If the assertions fail, STOP and replan (tune RRF `k`, per-ranker weights, or dense-only-when-Qdrant) — do NOT proceed to wiring (Tasks 6-9).**

**Files:**
- Create: `tests/test_hybrid_eval_gate.py`

- [ ] **Step 1: Write the gate test**

The hybrid agent exposes `.search(query, top_k=...)` returning RetrievedContext dicts, so it drops into the existing eval helpers (`evaluate_item`/`retrieve_sources`) as the `store`.

```python
# tests/test_hybrid_eval_gate.py
"""Empirical acceptance gate (spec §7): the hybrid retriever must MEET OR BEAT
the Mock golden baseline, not merely clear the 0.85 threshold. If this fails,
the hybrid is a quality regression — stop and replan before wiring."""
from statistics import mean

from app.agents.retrieval_agent import HybridRetrievalAgent
from app.services.bm25 import BM25Retriever
from app.services.vector_store import MockVectorStore
from app.evals.run_eval import (
    build_eval_store,
    evaluate_item,
    load_corpus,
    load_dataset,
)

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
    # Guards against silent drift in the documented baseline itself.
    m = _aggregate(build_eval_store())
    assert m["recall_at_1"] == BASELINE_RECALL_AT_1
    assert m["recall_at_3"] == BASELINE_RECALL_AT_3
    assert m["mrr"] == BASELINE_MRR


def test_hybrid_meets_or_beats_mock_baseline():
    h = _aggregate(_hybrid_eval_store())
    assert h["recall_at_1"] >= BASELINE_RECALL_AT_1, h
    assert h["recall_at_3"] >= BASELINE_RECALL_AT_3, h
    assert h["mrr"] >= BASELINE_MRR, h
```

- [ ] **Step 2: Run the gate**

Run: `python -m pytest tests/test_hybrid_eval_gate.py -q`

**Decision point:**
- **PASS** → the hybrid is at least as good as the Mock. Proceed to Task 6.
- **FAIL on `test_hybrid_meets_or_beats_mock_baseline`** → STOP. Record the measured numbers. Try, in order: (a) tune RRF `k` (e.g. 10, 30, 60) via `candidate_k`/`rrf_k`; (b) weight the lexical ranker higher; (c) fall back to dense-only-when-Qdrant, offline = Mock only. If none reach the baseline, return to the user with the numbers before wiring anything.

> Note: adjust the expected per-metric fields (`recall_at_1`, `recall_at_3`, `mrr`) if `evaluate_item`'s key names differ — read `app/evals/run_eval.py` lines 237-320 to confirm before running.

- [ ] **Step 3: Commit (only if the gate passes)**

```bash
git add tests/test_hybrid_eval_gate.py
git commit -m "test(retrieval): empirical gate — hybrid >= Mock golden baseline"
```

---

## Task 6: Wire `/rag/search` to the hybrid agent

**Files:**
- Modify: `app/api/rag.py:37-47`
- Test: `tests/test_api_routes.py` (existing — the `/rag/search` test lives here; update)

- [ ] **Step 1: Update the API test expectation**

In `tests/test_api_routes.py`, find the `/rag/search` success test (grep `retrieval_method` in that file) and change the expected method to `"hybrid"`:

```python
    # was: assert result["results"][0]["retrieval_method"] == "mock"
    assert data["results"][0]["retrieval_method"] == "hybrid"
```

Also assert the response shape is otherwise unchanged (keys `query`, `top_k`, `status`, `results`, `vector_backend`, `qdrant_enabled`).

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_api_routes.py -q`
Expected: FAIL — endpoint still returns `retrieval_method="mock"`.

- [ ] **Step 3: Implement the wiring**

In `app/api/rag.py`, replace the retrieval block (lines 37-47) so it builds the hybrid agent over the served store and calls `.search()`:

```python
    try:
        from app.agents.retrieval_agent import build_default_hybrid_agent

        agent = build_default_hybrid_agent()
        results = agent.search(request.query, request.top_k)
        vector_backend = "hybrid"
    except Exception:
        logger.exception("RAG search failed")
        return {
            "query": request.query,
            "top_k": request.top_k,
            "status": "failed",
            "suspicious_query": False,
            "requires_human_review": True,
            "warnings": [],
            "errors": ["Erro interno ao executar a busca."],
            "vector_backend": "unknown",
            "qdrant_enabled": is_qdrant_enabled(),
            "results": [],
        }
```

Then in the success return (line 73), replace `"vector_backend": vector_store.backend_name` with `"vector_backend": vector_backend`. Each `results` item already carries `metadata.retrieval_method == "hybrid"`; if the existing response flattens `retrieval_method` at top level (line 45), keep that mapping reading from `metadata`.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/test_api_routes.py -q`
Expected: PASS.

- [ ] **Step 5: Run full suite**

Run: `python -m pytest -q`
Expected: all green (2 skipped).

- [ ] **Step 6: Commit**

```bash
git add app/api/rag.py tests/test_api_routes.py
git commit -m "feat(rag): /rag/search served by HybridRetrievalAgent"
```

---

## Task 7: Wire the orchestrator `retrieval` step (trace-v0.3)

**Files:**
- Modify: `app/agents/orchestrator.py`
- Test: `tests/` (the orchestrator/pipeline test — locate with the grep below)

- [ ] **Step 1: Locate the pipeline test and its agent-count assertions**

Run: `grep -rn "completed_agents\|agent_count\|trace-v0.2\|FULL_MOCK_PIPELINE\|indexing" tests/`
These are the assertions that will break when a step is inserted; update them in Step 4.

- [ ] **Step 2: Write the failing test (new retrieval step)**

Add to the pipeline test file (e.g. `tests/test_orchestrator.py`):

```python
def test_full_mock_pipeline_runs_retrieval_after_indexing():
    from app.agents.orchestrator import CaseOrchestrator
    from app.schemas.case import CaseInput

    case = CaseInput(
        case_id="case_retrieval_001",
        source_type="peticao",
        user_goal="fraude bancária responsabilidade do banco",
        files=["peticao_inicial.pdf"],
    )
    result = CaseOrchestrator().run_full_mock(case)
    phases = [entry["trace_metadata"]["phase"] for entry in result["trace"]]
    assert "retrieval" in phases
    assert phases.index("retrieval") == phases.index("indexing") + 1
    retrieval_entry = next(
        e for e in result["trace"] if e["trace_metadata"]["phase"] == "retrieval"
    )
    assert retrieval_entry["output"]["retrieval_method"] == "hybrid"
    assert result["pipeline_summary"]["trace_version"] == "trace-v0.3"
```

- [ ] **Step 3: Run to verify it fails**

Run: `python -m pytest tests/test_orchestrator.py::test_full_mock_pipeline_runs_retrieval_after_indexing -q`
Expected: FAIL — no `retrieval` phase; trace_version still `trace-v0.2`.

- [ ] **Step 4: Implement the step**

In `app/agents/orchestrator.py`:

1. Bump the version constants (lines 13-15):

```python
    TRACE_VERSION = "trace-v0.3"
    INTAKE_PIPELINE = "case-intake-v0.3"
    FULL_MOCK_PIPELINE = "case-full-mock-v0.3"
```

2. In `run_full_mock`, after the indexing block (after line 284) and before the FIRAC block, insert the retrieval step. It reads the indexing result's `index_status` for the guard and builds the query from case + normalized text:

```python
        from app.agents.retrieval_agent import build_default_hybrid_agent

        retrieval_query = " ".join(
            [case.user_goal, str(normalizer_result.output)]
        )
        retrieval_result = build_default_hybrid_agent().run(
            case_id=case.case_id,
            query=retrieval_query,
            index_status=indexing_result.output.get("index_status", "ok"),
        )
        self._record_trace(trace, retrieval_result, 7, "retrieval")
        # retrieval is best-effort (like indexing) and never emits "blocked".
```

3. Renumber the FIRAC/validation steps: FIRAC becomes step 8, validation step 9 (update the `step_index` args in their `_record_trace` calls at lines 287 and 305).

Update the assertions found in Step 1 to expect the retrieval agent in `completed_agents`, agent_count +1, and `trace-v0.3`.

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/test_orchestrator.py -q`
Expected: PASS.

- [ ] **Step 6: Run full suite**

Run: `python -m pytest -q`
Expected: all green (2 skipped).

- [ ] **Step 7: Commit**

```bash
git add app/agents/orchestrator.py tests/test_orchestrator.py
git commit -m "feat(pipeline): retrieval step after indexing (trace-v0.3), FIRAC unchanged"
```

---

## Task 8: Score the hybrid in `run_eval` + non-regression thresholds

**Files:**
- Modify: `app/evals/run_eval.py`
- Test: `tests/` eval test (locate with grep)

- [ ] **Step 1: Locate the eval test**

The eval test file is `tests/test_eval.py`. The runner entry point is `run(dataset_path, thresholds, corpus)` at `app/evals/run_eval.py:424`; its result dict already has `average_recall_at_1`, `average_mrr`, `passed`, `thresholds`. Threshold checks live in `evaluate_thresholds(scores, thresholds)` at line 341. `DEFAULT_THRESHOLDS` already has `min_average_mrr` (0.85) and `min_average_recall_at_3` (0.85).

- [ ] **Step 2: Write the failing test**

Add to `tests/test_eval.py`:

```python
def test_run_eval_scores_hybrid_and_enforces_non_regression():
    from app.evals.run_eval import run

    report = run()
    assert report["retriever"] == "hybrid"
    # Non-regression floors anchored on the Mock golden baseline, not 0.85.
    assert report["thresholds"]["min_average_recall_at_1"] == 0.9375
    assert report["thresholds"]["min_average_mrr"] == 1.0
    assert report["average_recall_at_1"] >= 0.9375
    assert report["average_mrr"] >= 1.0
    assert report["passed"] is True
```

- [ ] **Step 3: Run to verify it fails**

Run: `python -m pytest tests/test_eval.py::test_run_eval_scores_hybrid_and_enforces_non_regression -q`
Expected: FAIL — no `retriever` key; `min_average_recall_at_1` absent.

- [ ] **Step 4: Implement**

In `app/evals/run_eval.py`:

1. Add a hybrid eval-store builder right after `build_eval_store` (line 168):

```python
def build_hybrid_eval_store(corpus: list[dict] | None = None):
    """Eval retriever of record: the hybrid over the golden corpus (BM25 + Mock)."""
    from app.agents.retrieval_agent import HybridRetrievalAgent
    from app.services.bm25 import BM25Retriever

    mock = build_eval_store(corpus)
    bm25 = BM25Retriever(mock.snapshot_chunks())
    return HybridRetrievalAgent(retrievers=[bm25, mock])
```

2. In `DEFAULT_THRESHOLDS` (line 13), add the non-regression floor and raise MRR (keep the rest):

```python
    "min_average_recall_at_1": 0.9375,
    # Raised from 0.85: the Mock/hybrid baseline is MRR=1.0, so any drop is a regression.
    "min_average_mrr": 1.0,
```

3. In `evaluate_thresholds` (line 341), add a check that appends a failure when `average([s["recall_at_1"] for s in scores]) < thresholds["min_average_recall_at_1"]` (mirror the existing `min_average_mrr` check).

4. In `run` (line 424), change `store = build_eval_store(corpus)` to `store = build_hybrid_eval_store(corpus)` and add `"retriever": "hybrid",` to the `result` dict.

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/test_eval.py -q` then `python -m app.evals.run_eval`
Expected: tests PASS; CLI exits 0 (`passed: true`).

- [ ] **Step 6: Commit**

```bash
git add app/evals/run_eval.py tests/
git commit -m "feat(eval): score hybrid retriever + non-regression thresholds"
```

---

## Task 9: Registry flip + docs sync + backlog close

**Files:**
- Modify: `app/agents/registry.py:76-88`
- Modify: `docs/08_TRACE_CONTRACT.md`, `docs/10_RAG_EVAL_CONTRACT.md`, `README.md`, `docs/04_BACKLOG.md`
- Test: registry test (existing)

- [ ] **Step 1: Write the failing test**

In the registry test file:

```python
def test_hybrid_retrieval_agent_is_implemented_and_importable():
    from app.agents.registry import list_agent_registry, validate_agent_registry

    entry = next(a for a in list_agent_registry() if a["agent_name"] == "HybridRetrievalAgent")
    assert entry["status"] == "implemented"
    assert entry["class_importable"] is True
    assert validate_agent_registry()["valid"] is True
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/ -k registry -q`
Expected: FAIL — entry still `planned`, `module_path=None`.

- [ ] **Step 3: Flip the registry entry**

In `app/agents/registry.py`, update the `HybridRetrievalAgent` entry (lines 76-88):

```python
        "module_path": "app.agents.retrieval_agent",
        "class_name": "HybridRetrievalAgent",
        "skill_name": "SKILL_HYBRID_LEGAL_RETRIEVAL.md",
        "status": "implemented",
        "mocked": True,
        "description": "Busca híbrida (RRF de BM25 + denso/léxico) com rastro de fusão.",
```

Keep the index-completeness warning comment.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/ -k registry -q`
Expected: PASS.

- [ ] **Step 5: Update docs (no code)**

- `docs/08_TRACE_CONTRACT.md`: document `trace-v0.3` — the `retrieval` step between indexing and firac, its `retrieved_context[]` output, best-effort (never blocks), and the index-completeness guard.
- `docs/10_RAG_EVAL_CONTRACT.md`: the evaluated retriever is now the hybrid (BM25 + Mock token-overlap over the golden corpus); document the non-regression thresholds (`min_average_recall_at_1=0.9375`, `min_average_mrr=1.0`) and that offline hybrid is an ensemble of two lexical signals.
- `README.md`: update the v0.4 → v0.5 retrieval paragraph and the test count.
- `docs/04_BACKLOG.md`: check off `HybridRetrievalAgent`, `Métricas retrieval`; annotate `RerankerService` as partial (RRF fusion is the reranking; cross-encoder deferred).

- [ ] **Step 6: Full suite + eval CLI**

Run: `python -m pytest -q && python -m app.evals.run_eval`
Expected: all green (2 skipped); eval exits 0.

- [ ] **Step 7: Commit**

```bash
git add app/agents/registry.py docs/ README.md tests/
git commit -m "feat(retrieval): registry flip to implemented + docs/backlog sync (P6 closed)"
```

---

## Self-Review (completed during authoring)

- **Spec coverage:** §2 offline ensemble → Task 4 factory + Task 5 label; §3 components → Tasks 1-4; §4 target filter → Task 4 `run()` + test; §5 guard → Task 4 `run()` + test; §6 integration → Tasks 6 (endpoint), 7 (orchestrator), 8 (eval); §7 empirical gate → Task 5 (go/no-go, before wiring); §8 tests/rollout → every task; §9-10 done-criteria → Task 9.
- **Placeholder scan:** No TBD/TODO. Two steps (Task 5 metric keys, Task 8 runner entry name) instruct reading exact `run_eval.py` line ranges to confirm names before running — flagged, not left vague.
- **Type consistency:** `search(query, top_k, filters)` signature identical across `BM25Retriever`, `MockVectorStore`, `HybridRetrievalAgent`; `build_retrieved_context(chunk, score, method)` used in Tasks 1-2; `reciprocal_rank_fusion(rankings, k)` used in Tasks 3-4; `.run(case_id, query, top_k, index_status)` used in Tasks 4, 7. RetrievedContext shape single-sourced via Task 1 helper.
