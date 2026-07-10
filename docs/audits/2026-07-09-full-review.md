# Full Review — `lexintel-agentic-hermes` (Lex Kratos Agentic Core v0.1)

> Reviewer: independent code analysis · 2026-07-09
> Commit reviewed: `bc23d0b` (master) · **77 passed, 2 skipped** · ruff + mypy clean · eval passed (24 cases, recall@1 = 0.9375, recall@3 = 1.0, MRR = 1.0)
> Method: full read of all 49 source files + acceptance suite run for ground truth (`pytest`, `ruff check`/`format --check`, `mypy app`, `run_eval`).
> Lineage: follow-up to [`docs/audits/2026-06-13-deep-review.md`](2026-06-13-deep-review.md), whose High/Medium findings were marked REMEDIATED (PRs #13/#15, 53→71 tests). This pass re-checks those remediations and reviews everything added since (Qdrant real-retrieval PR #17, richer-chunking spec).

> **Disposition (2026-07-09): REMEDIATED on `fix/review-2026-07-09-m1-m4`.** M1
> (indexing upsert failure now degrades to a review-flagged `warning`, not
> `failed` — best-effort, non-halting; 71→83 tests). M2 **withdrawn as an audit
> error**: reachability of the validator block path *is* already covered by
> `test_validator_blocks_on_hallucinated_precedent_through_pipeline`
> (`tests/test_orchestrator.py`) — only the *default* FIRAC mock emits empty
> content, which is a mock-completeness note, not a wiring gap. M3 (per-area
> recall@3 floor added to the eval gate + enforced). M4 (`CaseInput` now caps
> `case_id` ≤128, `files` ≤200 items, each path ≤2048 chars). L1–L3 doc/claim
> fixes pending. Full gate green: 83 passed / 2 skipped, ruff + mypy clean, eval exit 0.

---

## 1. Verdict

**A genuinely well-engineered v0.1 scaffold — above the bar for a mock.** No CRITICAL or HIGH severity defects. The security posture is fail-closed by construction, tests are deterministic, docs are largely honest, and the registry self-validates its own human-review invariants. The findings below are MEDIUM-and-below: one control-flow inconsistency (`failed` doesn't halt), one safety net that is still inert end-to-end (echo of the prior audit's M1), an eval-gate gap (no per-area floor), an unbounded-input surface, and a few doc/claim precision issues.

The 2026-06-13 audit's two Highs are **genuinely improved**: the eval is no longer tautological (it now runs the real `MockVectorStore` over a corpus with distractors and is false-green resistant), and `blocked` now stops the pipeline at every step. But the "dead validator" (old M1) was wired structurally without achieving actual reachability — see M2.

**Grade by dimension** (as a v0.1 mock scaffold, not production):

| Dimension | Grade | Note |
|---|---|---|
| Scope discipline / honesty | A | Mock boundaries explicit everywhere; no scope creep |
| Architecture (orchestrator + agents) | A− | Clean uniform `AgentResult`; monotonic flag propagation; halt-on-blocked. Minor `failed`-status gap (M1) |
| Data contracts (Pydantic) | A− | Literal enums, `Field` bounds, `model_validator`; single-source JSON-schema drift gate in CI |
| Security agent | B+ | Solid normalization + deterministic; denylist is bypassable by design (L1) |
| RAG eval harness | B+ | Metrics correct + false-green resistant; **no per-area floor (M3)** |
| Retrieval (Mock + Qdrant) | A− | Deterministic mock; dim-drift-proof, uuid5-idempotent Qdrant path |
| Test quality | A− | Autouse singleton reset → order-independent; meaningful asserts |
| CI / tooling | A− | lint + mypy + schema-drift + tests + eval; no vacuous steps |
| Docs | B+ | Extensive and mostly accurate; 3 claim/config drifts (L2, L3) |
| Input hardening | B | Unbounded `case_id`/`files` on unauthenticated endpoints (M4) |

---

## 2. Architecture map

```
POST /cases/intake        → CaseOrchestrator.run_intake_only   (intake → security)
POST /cases/run-full-mock → CaseOrchestrator.run_full_mock     (8 agents)
POST /rag/search          → SecurityAgent gate → get_vector_store().search()
GET  /eval/run            → app.evals.run_eval.run()  (real MockVectorStore over golden corpus)
GET  /catalog/skills|agents → skill_loader + self-validating agent registry
GET  /health
```

Full-mock pipeline (`orchestrator.py`):
`Intake → Security → [block?] → Extraction → Normalization → Metadata → Indexing → FIRAC → (mock_draft) → Validation → summarize`

Strongest part of the design: each agent returns a uniform `AgentResult`; `_record_trace` propagates review/external flags **monotonically** (review only turns *on*, external only turns *off*) and stamps `trace_metadata`; every step fail-closes on `blocked` before the next legal phase runs. This is the correct shape for an auditable judicial pipeline.

---

## 3. What is genuinely strong (preserve)

- **Fail-closed everywhere.** `external_use_allowed` is hard-wired `False` at every agent and every orchestrator return. Security runs at **step 2**, before any extraction/analysis (`orchestrator.py:253`).
- **Path-traversal defense is correct** (`skill_loader.py:6–21`) — triple-layered: `candidate.name != skill_name` rejects separators, `SKILL_*.md` allowlist, resolved-parent equality check.
- **Self-validating registry** (`registry.py:187–241`) asserts human-review phases carry `requires_human_review`, implemented agents are importable, and all skills are mapped — surfaced live at `GET /catalog/agents`.
- **Judicial-grade error hygiene**: `rag.py:48` and `indexing_agent.py:46` log full detail server-side, return generic client messages (no path/PII leak).
- **Qdrant path is drift-proof**: dim derived from the model (`embeddings.py:45–51`), collection fail-closes on dim mismatch (`vector_store.py:200`), deterministic `uuid5` point IDs → idempotent re-index.
- **Eval is false-green resistant**: runs the real `MockVectorStore.search` over a corpus with distractors; a dead retriever → recall/MRR = 0 → fails ≥0.85 gates → `SystemExit(1)`.
- **CI is real**: lint (`app tests scripts integrations`) + mypy + schema-drift (`gen_schemas` then `git diff --exit-code`) + tests + eval.

Note on metrics: `recall@1 = 0.9375` alongside `MRR = 1.0` is **not** a contradiction — `recall_at_1` is per-expected-set recall (`hits/len(expected)`), `reciprocal_rank` is first-hit rank. Both are correctly implemented (`run_eval.py:197–231`).

---

## 4. Findings (ranked)

### ✅ M1 (FIXED) — `status="failed"` did not halt the pipeline
`indexing_agent.py:60` emits `status="failed"` on upsert exception, but every orchestrator guard checks only `== "blocked"` (e.g. `orchestrator.py:286`). A failed indexing step therefore **continues** into FIRAC + validation, yet `_response_status` (`orchestrator.py:155`) stamps the whole response `"failed"`. Harm is limited (FIRAC reads normalizer output, not the index), so this is an inconsistency, not corruption: the halt vocabulary (`blocked`) and status vocabulary (`blocked|failed|warning`) are out of sync.
**Fix:** decide indexing's criticality — either best-effort (don't stamp the run `failed`, or downgrade to `warning`) or fatal (add `failed` to the halt guards, or route through `_blocked_response`).
**Done (best-effort):** `indexing_agent.py` upsert-failure branch now returns `status="warning"` + `requires_human_review=True` + a generic warning (no `errors`). Pipeline continues; run reports `warning`. Tests: `test_indexing_agent_returns_warning_result_on_upsert_error`, `test_failed_indexing_degrades_to_warning_without_halting`.

### ✅ M2 — WITHDRAWN (audit error): validator block path IS orchestrator-tested
Original claim: the validator block path is unreachable end-to-end and only unit-tested. **This was wrong** — `test_validator_blocks_on_hallucinated_precedent_through_pipeline` (`tests/test_orchestrator.py:75–84`) injects a `_HallucinatingFIRACAgent` whose output carries `precedente inventado`, runs `run_full_mock`, and asserts `status == "blocked"` with `blocked_at == "ValidatorAgent"`. So the wiring `firac_result.output → mock_draft → validator` is proven reachable at the orchestrator level, exactly the "test-only reachability" this remediation would have added.
**Residual (true, but lesser):** the *default* `FIRACAgent` returns empty lists (`firac_agent.py:28–36`), so a validator block never fires in normal operation — a mock-completeness note (FIRAC produces no real analysis yet), not a wiring defect. No change made.

### ✅ M3 (FIXED) — Eval gate had no per-area floor
`evaluate_thresholds` (`run_eval.py:360–361`) gates on **global** `average_recall_at_3`/`average_mrr` only. `summarize_by_area` computes per-area metrics + `failed_case_ids` that **nothing enforces**. With 4 areas × 6 cases, one area at recall@3 = 0.4 and three at 1.0 averages exactly 0.85 → **passes** while a whole legal area is broken.
**Fix:** add `min_per_area_recall_at_3` (and/or per-area MRR) to `DEFAULT_THRESHOLDS` and enforce it in `evaluate_thresholds`.
**Done:** `min_per_area_recall_at_3=0.85` added to `DEFAULT_THRESHOLDS`; `evaluate_thresholds` now emits a `per_area_recall_at_3` failure per area below the floor. Test: `test_eval_gate_enforces_per_area_floor` (weak area masked by 0.85 global still fails).

### ✅ M4 (FIXED) — Unbounded input on unauthenticated pipeline endpoints (DoS surface)
`CaseInput` (`case.py:6–10`) puts no cap on `case_id` or `files` (unbounded list of unbounded strings). `_build_security_text` concatenates all of it and runs NFKD + regex over the blob (`security_agent.py:116–126`). No endpoint has auth; `/eval/run` also runs the full eval synchronously.
**Fix:** add `Field(max_length=...)` / `max_items` to `CaseInput`; note auth + request-size limits as an explicit phase-2 gate before any exposure beyond localhost.
**Done:** `CaseInput` now bounds `case_id` (1–128), `files` (≤200 items, each ≤2048 chars) → HTTP 422 at the edge. Auth remains an explicit phase-2 gate. Tests: `tests/test_case_input_bounds.py` (4).

### 🟢 L1 — Denylist prompt-injection detector is bypassable by design
`SecurityAgent` (`security_agent.py:19–105`) is a fixed PT/EN regex denylist. Normalization is good (NFKC, zero-width strip, diacritic fold, `[a-z0-9]` collapse), but the approach only catches enumerated phrases — evaded by paraphrase, other languages, or semantics. **Expected for v0.1**; the risk is reporting green tests as "injection handled." Keep the "mock" framing in any status write-up.

### 🟢 L2 — README overstates eval↔API "parity"
README:90 says the eval scores "**o mesmo `MockVectorStore` que o endpoint `/rag/search` serve**." `build_eval_store` (`run_eval.py:155–165`) builds a **separate instance** seeded with the golden corpus, not the API singleton (seeded with `DEFAULT_MOCK_CHUNKS`). The shared thing is the *code path/class*, not the *instance/data* — the code's own docstring is honest; the README isn't. Reword to "same retrieval code path."

### 🟢 L3 — Minor doc/config drift
- README:130 documents `ruff check app tests scripts` but CI also lints `integrations` (`ci.yml:28`). Align local + CI.
- `.env.example` ships `SUPABASE_*`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` — **none read by any code** (only 5 `LEX_*`/`QDRANT_*` vars are). Mark as phase-2 placeholders or drop.
- README:47–48 uses Windows `.venv\Scripts\activate` in an otherwise Linux repo; primary path should be `source .venv/bin/activate`.

---

## 5. Recommended next steps (priority order)

1. **Resolve M1 + M2 together** — same theme (status-vocabulary coherence + safety-net reachability). Decide indexing criticality; make the validator block path reachable or explicitly test-covered through the orchestrator.
2. **Add the M3 per-area eval floor** — cheap; exactly the gate that prevents one practice area silently regressing.
3. **Add `Field` caps to `CaseInput` (M4)** — one-line invariants that close the DoS surface before exposure.
4. **Tighten L2/L3 doc claims** — for a CNJ-615/LGPD-facing project, "docs tell the exact truth about the code" is itself a compliance property.
5. Before ever flipping `LEX_KRATOS_ENABLE_QDRANT=true` in a real deployment, run a focused pre-mortem on the Qdrant path (collection lifecycle, dim migration, model-weight download failure modes, filter-injection on `metadata.*`).

---

## 6. Disposition

_REMEDIATED (M1/M3/M4 fixed, M2 withdrawn) on `fix/review-2026-07-09-m1-m4`; L1–L3 doc polish pending. No blocking defect for v0.1's stated scope._
