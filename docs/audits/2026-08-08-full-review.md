# Full Review — `lexintel-agentic-hermes` (Lex Kratos Agentic Core v0.5)

> Reviewer: independent code analysis · 2026-08-08
> Commit reviewed: `d7ed5a8` (master) · **150 passed, 2 skipped** · ruff check + format clean · mypy clean (33 files) · eval passed (24 cases, retriever=hybrid, recall@1 = 0.9375, recall@3 = 1.0, MRR = 1.0)
> Method: full review of `app/`, `scripts/`, `integrations/`, `tests/` + acceptance suite run for ground truth (`pytest`, `ruff check`/`format --check`, `mypy app`, `python -m app.evals.run_eval`). Every finding re-verified against source before inclusion.
> Lineage: follow-up to [`docs/audits/2026-07-09-full-review.md`](2026-07-09-full-review.md) (disposition REMEDIATED). This pass re-checks those remediations and reviews everything added since — chiefly P6 hybrid retrieval (PR #22: `BM25Retriever` + RRF + `HybridRetrievalAgent`) and the structural-chunking work.

> **Amended 2026-08-08 (post-review):** external review (Codex, PR #23) correctly flagged that this audit's first draft mischaracterized three findings against the repo's own docs. **M1 and M4 are not newly discovered silent defects** — both are disclosed, accepted follow-ups in `docs/HANDOFF.md` ("Follow-ups abertos") and `docs/12_VECTOR_INDEXING_CONTRACT.md` ("Limitações conhecidas"); the audit's contribution is prioritizing them, not finding them. **L1 is WITHDRAWN as an audit error**: trace-only retrieval is an approved design decision ("FIRAC não alimentado — não reverter sem motivo"; hybrid-retrieval design spec §6.1), not dropped output. Sections below carry inline corrections; severities and fixes for M1/M4 stand on their merits.

> **Disposition (2026-08-08): REMEDIATED on `fix/review-2026-08-08` (PR #24).** M1 (frequency-preserving `_tokenize_seq` feeds BM25), M2 (`cmd\s*exe`, scan v0.3), M3 (fail-fast scripts), M4 ((store, version)-keyed BM25 cache with upsert invalidation — the exact mechanism the documented follow-up required), L2–L5 all fixed with regression tests; 150 → 156 tests, all gates green, hybrid still meets the Mock golden baseline. L1 withdrawn (see amendment above), not implemented.

---

## 1. Verdict

**Still a disciplined, honest, well-engineered scaffold.** *(Corrected per the amendment above.)* The BM25 side of the retriever of record runs on binary term frequencies (M1) — a limitation the repo itself discloses in `HANDOFF.md`/`12_VECTOR_INDEXING_CONTRACT.md` with a planned frequency-preserving-tokenizer follow-up; this audit's contribution is elevating that follow-up to do-now, since the "Okapi BM25" label in docstrings and eval contract reads stronger than the disclosed behavior. The one genuinely new correctness defect of this pass is M2: a critical `SecurityAgent` pattern (`cmd\.?exe`) is unreachable after normalization — silent, since tests stay green.

The 2026-07-09 remediations all held up on re-check: indexing degrades to `warning` without halting, the per-area eval floor exists and is enforced (`run_eval.py:22`, `:427`), `CaseInput` is bounded (`case.py:10–14`), and the README's eval↔API parity wording was fixed to "same reference retriever, own instance" (old L2 closed). `.env.example` now explicitly marks the phase-2 keys as unread placeholders (old L3 mostly closed; the Windows-style `\.venv\Scripts\activate` line at README:48 remains).

**Grade by dimension** (as a mock-first v0.5, not production):

| Dimension | Grade | Note |
|---|---|---|
| Scope discipline / honesty | A | Mock boundaries still explicit everywhere; no scope creep |
| Architecture (orchestrator + agents) | A | Retrieval step correctly best-effort; trace-only-to-FIRAC is an approved boundary (ex-L1, withdrawn) |
| Retrieval (hybrid BM25 + RRF) | B | Fusion + agent design sound; BM25 tf binary (M1 — disclosed follow-up, now prioritized) |
| Security agent | B | Normalization solid; one critical pattern dead post-normalization (M2) |
| RAG eval harness | A− | Per-area floor enforced; non-regression pisos anchored; one cwd-dependent test (L2) |
| Test quality | A− | 150 deterministic tests, order-independent; integration guard has a port mismatch (L3) |
| CI / tooling | B+ | CI gates real; **local `run_tests.sh`/`.bat` can exit 0 on a red suite (M3)** |
| Performance posture | B | Fine for mock scale; hybrid agent rebuilt per request is O(corpus) on the hot path (M4) |
| Code reuse / DRY | B+ | `build_retrieved_context` exists but `MockVectorStore` forked it and drifted (L4) |
| Docs | A− | Extensive and accurate post-L2/L3 fixes; minor venv-activation drift remains |

---

## 2. What changed since 2026-07-09 (scope of this pass)

```
P6 hybrid retrieval (PR #22):
  app/services/bm25.py            BM25Retriever (new)
  app/services/fusion.py          reciprocal_rank_fusion (new)
  app/agents/retrieval_agent.py   HybridRetrievalAgent + build_default_hybrid_agent (new)
  app/api/rag.py                  /rag/search now served by the hybrid agent
  app/agents/orchestrator.py      retrieval step 7 (best-effort) between indexing and FIRAC
  app/evals/run_eval.py           build_hybrid_eval_store + non-regression floors
Structural chunking:
  app/services/chunking.py        StructuralChunker / ParagraphChunker / get_chunker
  app/services/markers.py         legal section detection
  app/services/extraction.py      MockExtractor behind Extractor interface
```

The prior audit's strong points all still hold (fail-closed flags, path-traversal-safe skill loader, self-validating registry, judicial-grade error hygiene, drift-proof Qdrant path, false-green-resistant eval, real CI). Not re-litigated here.

---

## 3. Findings (ranked)

### 🟠 M1 — BM25 term frequency is always 1 *(CORRECTED: a disclosed follow-up, not a new discovery)*

> **Amendment:** `docs/HANDOFF.md` (Follow-ups abertos #1) and `docs/12_VECTOR_INDEXING_CONTRACT.md` (Limitações conhecidas) already document exactly this — binary tf via the shared set tokenizer, accepted for short mock chunks, with a frequency-preserving tokenizer named as the fix. The technical analysis below stands; the framing "silently isn't what it claims" does not. This audit's position is only that the follow-up is cheap and worth doing now, before the "Okapi BM25" label hardens in more contracts.
`_tokenize` (`vector_store.py:75–81`) returns a **`set[str]`**; `BM25Retriever` builds `Counter(_tokenize(chunk["text"]))` (`bm25.py:27`). A Counter over a set gives every present term tf = 1, so the tf-saturation numerator `tf·(k1+1)/(tf+…)` is constant per match and `_doc_len` counts *unique* tokens, not real length. Okapi BM25 (`bm25.py:12`, docstring and eval contract both claim it) degenerates to IDF-sum matching: a chunk mentioning "fraude" five times scores the same as one mentioning it once. Silent — the golden dataset is small and lexically distinctive, so recall floors still pass.
**Fix:** tokenize to a `list` for BM25 (keep the set variant for the mock store's overlap scoring), e.g. a `_tokenize_seq()` sibling sharing the same fold/filter rules. Re-run the eval gate; floors should hold or improve.

### 🟠 M2 — Critical `command_execution` pattern is dead code post-normalization
`normalize_text` (`security_agent.py:108–127`) collapses everything non-alphanumeric to spaces, so "cmd.exe" always normalizes to `cmd exe`. The pattern `r"\b(cmd\.?exe|powershell|rm\s+rf)\b"` (`security_agent.py:49`) can only match `cmdexe` or the literal `cmd.exe` — neither can survive normalization. Input like "abra o cmd.exe e apague o histórico" scans as **safe** despite the critical rule written to block it (`powershell` and `rm rf` still fire; the `cmd.exe` alternative never does).
**Fix:** `cmd\s*exe` (post-normalization form), plus a regression test asserting the raw input "cmd.exe" is flagged. Worth a quick sweep of all patterns for other pre-normalization syntax (none found in this pass, but the test should encode the invariant: patterns must be written against *normalized* text).

### 🟠 M3 — `run_tests.sh` / `run_tests.bat` can report green on a red suite
`scripts/run_tests.sh` has no `set -e`; its exit code is that of the **last** command. pytest failing followed by the eval passing → exit 0. A missing `.venv` → `source` fails and the script silently continues on system Python. `run_tests.bat` has the same flaw. CI is unaffected (steps run separately), but these are the documented local gate.
**Fix:** `set -euo pipefail` (and `if errorlevel 1 exit /b 1` per step in the `.bat`).

### 🟠 M4 — Hybrid agent rebuilt from scratch on every request *(CORRECTED: a disclosed follow-up, not a new discovery)*

> **Amendment:** also already documented — `HANDOFF.md` Follow-ups abertos #2 and the vector-indexing contract describe the per-request rebuild, the Qdrant-path full-collection scroll, why a naive cache is dangerous (stale index after upsert), and that invalidation-on-upsert is required before the Qdrant path serves production. The fix below implements precisely that documented requirement.
`/rag/search` (`rag.py:39`) and the orchestrator's retrieval step (`orchestrator.py:300`) each call `build_default_hybrid_agent()` (`retrieval_agent.py:110`), which snapshots the **entire** vector store and rebuilds the BM25 IDF index per query (`retrieval_agent.py:120`). Harmless at mock scale; with `LEX_KRATOS_ENABLE_QDRANT=true` it means a full-collection scroll (10k-point batches) + per-chunk Pydantic validation + full index rebuild **per search**. Latency and load grow linearly with the index; concurrent searches multiply it.
**Fix:** cache the BM25 index (module-level, like the store singleton) and invalidate on upsert; or rebuild on an explicit signal. Flag as a hard gate before any real-corpus Qdrant deployment.

### ✅ L1 — WITHDRAWN (audit error): trace-only retrieval is an approved design decision
Original claim: retrieval output dead-ends because FIRAC never receives the retrieved precedents. **This was wrong as a defect.** `docs/HANDOFF.md` lists "FIRAC não alimentado — trace-only por ora; fiar retrieval→FIRAC fica para quando FIRAC deixar de ser mock" under "Decisões de design (aprovadas — não reverter sem motivo)", and the hybrid-retrieval design spec (§6.1) approves "FIRAC permanece inalterado" explicitly. The retrieval step's purpose in v0.5 is the auditable trace (`retrieved_context[]` + counts), which it fulfills. Wiring the contexts now would reverse an approved scope boundary — not done. The true residual is only a reminder: when FIRAC stops being a mock, the deferred wiring becomes due (it is already tracked in the design docs). No change made.

### 🟢 L2 — `test_hybrid_eval_gate.py` is cwd-dependent
`tests/test_hybrid_eval_gate.py:31` loads `"app/evals/golden_dataset.jsonl"` as a cwd-relative string instead of `run_eval.DATASET_PATH` — breaking the cwd-independence the eval module guarantees and `test_eval_runs_outside_project_root` explicitly protects. Run from any other working directory, the acceptance gate fails spuriously with `FileNotFoundError`.
**Fix:** import `DATASET_PATH` from `app.evals.run_eval`.

### 🟢 L3 — Integration-test reachability guard and client default disagree on the port
`tests/integration/test_qdrant_retrieval.py:28` defaults `QDRANT_PORT` to **6533** (matching `.env.example` and compose), while `get_qdrant_client()` (`qdrant_service.py:32`) defaults to **6333**. With the env var unset and the repo's compose stack up, the guard probes 6533, un-skips the test, then the client connects to 6333 → connection refused (or a foreign Qdrant) instead of a pass or clean skip.
**Fix:** single source the default (guard imports the same default the client uses), or make `get_qdrant_client()` default 6533 to match the repo's documented posture.

### 🟢 L4 — `MockVectorStore._to_retrieved_context` forked `build_retrieved_context` and drifted
`vector_store.py:172` re-implements the mapping that `build_retrieved_context` (`vector_store.py:84`) exists to centralize ("so the RetrievedContext shape … is defined in one place"), and has already drifted: scores rounded to 4 dp vs 6 dp everywhere else, `page_start`/`page_end` accessed as required vs optional. A future field added to the shared helper silently won't appear in mock results.
**Fix:** one-line delegation to `build_retrieved_context(chunk, score, …)`.

### 🟢 L5 — Section detection runs twice per structured document
`get_chunker()` (`chunking.py:132`) runs `detect_sections` to pick a strategy, then `StructuralChunker.chunk()` immediately re-runs the identical multi-pattern scan on the same text. 2× regex passes per document per pipeline run.
**Fix:** have `get_chunker` return the detected sections (or the chunker accept them).

### ℹ️ Note — mypy gate is inverted when run outside the project environment
With `warn_unused_ignores = true` + `ignore_missing_imports = true` (`pyproject.toml`), a mypy that cannot see the installed `qdrant-client` resolves those types to `Any` and then **fails** on the now-"unused" `# type: ignore[union-attr]` at `vector_store.py:228` — observed with a uv-tool-installed mypy in this review environment; `python -m mypy app` in the project env is clean, and CI is unaffected. Not a code defect; worth a line in the validation docs ("run mypy from the project venv") since the failure mode looks like a type error but is an environment error.

---

## 4. Recommended next steps (priority order)

1. **Fix M2 now** — the one new correctness defect: a dead critical detection branch, with a regression test (raw "cmd.exe" must flag) plus the invariant "patterns are written against *normalized* text".
2. **Close the two documented follow-ups (M1, M4)** — both were already on the books; this audit's position is that they're cheap enough to stop deferring (M1: frequency-preserving tokenizer + tf-sensitivity test; M4: the invalidation-on-upsert cache the docs themselves demand — a hard gate before real-corpus Qdrant use).
3. **Harden the local gates (M3, L2, L3)** — three tiny changes that make the documented validation commands trustworthy in any environment.
4. **Clean up L4 + L5** — unfork the context mapping, single-scan the sections.
5. Keep the standing pre-mortem gate from the 2026-07-09 audit before flipping `LEX_KRATOS_ENABLE_QDRANT=true` anywhere real. ~~Wire L1~~ — withdrawn; trace-only retrieval is an approved boundary until FIRAC stops being a mock.

---

## 5. Disposition

_~~OPEN as of 2026-08-08.~~ **REMEDIATED (same day) on `fix/review-2026-08-08` (PR #24)** — M1–M4 and L2–L5 fixed with regression tests (150 → 156 tests, all gates green, hybrid still meets the Mock golden baseline); L1 withdrawn as an audit error (approved design decision); M1/M4 reclassified as documented follow-ups closed, per the amendment in the header. No blocking defect for the mocked v0.5 scope._
