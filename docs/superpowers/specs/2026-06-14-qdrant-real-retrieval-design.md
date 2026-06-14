# SPEC — Real Qdrant retrieval (MVP) for `lexintel-agentic-hermes`

> Status: **DRAFT** · 2026-06-14 · Author: Felipe
> Inputs: inspection of `app/services/vector_store.py` (stubbed `QdrantVectorStore`), `app/services/qdrant_service.py` (flag + client), `app/api/rag.py`, `app/evals/run_eval.py`, the `lex_kratos` Hermes plugin, and the live environment (docker + a foreign Qdrant 1.7.4 on :6333, hermes v0.16.0).
> Complexity: **Alta** (new component, an embedding-stack decision, an external service, >5 files). Brainstormed under `dev-workflow`.
> Supersedes the "Real Qdrant ... out of scope" line of `2026-06-13-lexintel-optimization.md` **for retrieval only** — Supabase/LLM/DataJud/PJe stay feature-flagged off.

---

## 1. Objective

Replace the stubbed `QdrantVectorStore` (currently two `raise RuntimeError`s) with a working, **local-only** vector retrieval backend, reachable through the existing `LEX_KRATOS_ENABLE_QDRANT` flag, and prove it live end-to-end:

1. **Option 1 (baseline):** run the app + load the `lex_kratos` Hermes plugin against the mock backend — confirm the gateway → pipeline → RAG path works as shipped.
2. **Option 3 (this work):** swap in real Qdrant retrieval; re-verify the same path with `vector_backend=qdrant` and semantically-retrieved hits.

## 2. Why (problem statement)

The scaffold's retrieval is deliberately mocked: `MockVectorStore` scores by token overlap with **no embeddings**. That is honest for v0.1 but cannot retrieve a paraphrase, a synonym, or a semantically-related precedent — the core value of RAG. The seam was built for exactly this swap (`Protocol` + feature flag + a stubbed `QdrantVectorStore` that `raise`s + `requirements-qdrant.txt` + a pinned Qdrant in `docker-compose.yml`), so the wiring is already proven against the mock. Only the backend body is missing, plus the one thing the mock never needed: an **embedding function**.

## 3. Scope

### In scope
- New `app/services/embeddings.py`: a lazy, local multilingual embedder (fastembed) with e5 asymmetric query/passage prefixes; the vector dim is **read from the model**, never hardcoded.
- Fill `QdrantVectorStore.upsert` / `.search` in `app/services/vector_store.py`: ensure-collection (create-if-absent; raise on dim mismatch), deterministic `uuid5(chunk_id)` point ids (idempotent re-index), full-chunk payload, COSINE search → the **same `RetrievedContext` dict shape the mock emits** (so `rag.py` is untouched).
- Config: add pinned `fastembed` to `requirements-qdrant.txt`; add `LEX_KRATOS_ENABLE_QDRANT=false` + optional `LEX_KRATOS_EMBEDDING_MODEL` to `.env.example`; parameterize the compose host port (`${QDRANT_HOST_PORT:-6333}:6333`).
- Integration tests under `tests/integration/`, skipped by default; one server-free unit test for id/payload mapping.
- Live verification of both options; brief docs touch (`CHANGELOG.md`, README run-note).

### Out of scope (explicit)
- **Rewiring `run_eval.py`** — it imports `MockVectorStore` directly and stays on mock. "Done" = real retrieval reachable via `/search`, **not** quality-proven against the 0.85 gates. (Chosen MVP scope.)
- Any external/cloud embedding API (no OpenAI) — keeps legal text on-machine, sidesteps the CNJ 615/LGPD PII concern that is itself out of MVP scope.
- Supabase, real LLM, DataJud, STJ, PJe — remain feature-flagged off.
- Production concerns: collection sharding, quantization, auth on Qdrant, retention/forget — deferred (the option-2 compliance track).

## 4. Proposed architecture & key decisions

- **D1 — Embedding model: local multilingual e5 via fastembed.** No API key, offline, free; multilingual e5 handles Portuguese legal text. The exact supported id is confirmed against the installed fastembed's `TextEmbedding.list_supported_models()` at impl time (primary: `intfloat/multilingual-e5-small`, 384-dim; fallback: a supported multilingual MiniLM/e5 variant). The store reads `dim` from the embedder so D1 and the collection config are a single coupled decision.
- **D2 — e5 prefixes encoded once.** `embed_documents` → `"passage: "`, `embed_query` → `"query: "`. Omitting these silently degrades recall; the embeddings module is the only place that knows this.
- **D3 — Idempotent point ids.** `uuid5(NAMESPACE, chunk_id)` so re-running the pipeline upserts (replaces) rather than duplicates — mirrors the mock's `existing_ids` de-dup semantics.
- **D4 — Payload carries the full chunk.** Search reconstructs `RetrievedContext` from payload (`chunk_id`, `doc_id`, `page_start/end`, `source`, `unit_type`, `case_id`, `metadata` incl. `source_ref`) + cosine `score`. Identical dict shape to the mock → `rag.py` and downstream agents need no change.
- **D5 — Ensure-collection is loud.** Create-if-absent with model dim + COSINE; if the collection exists with a different dim, raise (don't silently write into an incompatible space). Surfaces through `rag.py`'s existing PII-safe error path.
- **D6 — Non-destructive ops.** A foreign Qdrant 1.7.4 squats on :6333; the project pins v1.14.3 to match `qdrant-client==1.14.3`. Parameterize the compose host port and run the pinned instance on **6533** (`QDRANT_PORT=6533`), leaving the other project's container alone.

## 5. Dependencies & ordering

1. `embeddings.py` (no deps on the store).
2. `QdrantVectorStore` body (depends on `embeddings.py` + existing `get_qdrant_client`).
3. Config/compose/deps.
4. Tests.
5. Live verification (needs a running pinned Qdrant + fastembed installed).

## 6. Risks & plan B

- **R1 — chosen model id not in installed fastembed.** Mitigation: query `list_supported_models()` first; pick the nearest supported multilingual variant; dim is read from the model so nothing downstream breaks.
- **R2 — client 1.14 vs the foreign server 1.7.4 API skew.** Mitigation: D6 runs the pinned 1.14.3; do not point at the foreign instance.
- **R3 — first-run weight download (~100–400 MB).** Mitigation: integration tests skipped by default; download happens only during explicit live verification. Documented in the run-note.
- **R4 — score-semantics change (overlap-ratio → cosine).** No test/eval asserts on absolute `QdrantVectorStore` scores (eval is mock-only), so green→red surprise risk is low; verified during impl.

## 7. Test strategy

- Default suite stays **offline and green** — no network, no weight download. Real-Qdrant tests live in `tests/integration/`, `skipif`-gated on (flag set ∧ live server reachable ∧ fastembed importable).
- One server-free unit test: `uuid5` id determinism + payload→`RetrievedContext` mapping with a stubbed client.
- Integration test (manual/gated): seed the golden corpus, query a paraphrase the token-mock would miss, assert a semantically-correct hit and `retrieval_method="qdrant"`.

## 8. Acceptance criteria ("done")

- `LEX_KRATOS_ENABLE_QDRANT=true` + pinned Qdrant up → pipeline via the `lex_kratos` plugin indexes into Qdrant without error.
- `POST /rag/search` returns `vector_backend=qdrant`, `status=success`, and real hits whose dict shape matches the mock's `RetrievedContext`.
- A paraphrased query (no token overlap) returns the semantically-correct chunk — demonstrating real embeddings vs. the mock.
- Default `pytest` passes unchanged, offline; integration tests skip cleanly when Qdrant/fastembed absent.
- `ruff check` + `ruff format` clean; mypy clean on touched files.
- Mock path, eval, and CI behavior unchanged when the flag is off.
