# SPEC — Optimization of `lexintel-agentic-hermes` (Lex Kratos Agentic Core)

> Status: DRAFT for approval · 2026-06-13 · Author: Felipe
> Inputs: `REVIEW_ANALYSIS.md` (deep review), `~/hermes-agent-research-brief.md` (Hermes framework research), inspection of the live Hermes v0.16.0 install (97 skills incl. `mlops/ai-legal-development`, Telegram gateway connected).
> Complexity: **Alta** (architectural decisions, judicial-compliance domain, two strands, >5 files). Executed under `dev-workflow`.

---

## 1. Objective

Harden `lexintel-agentic-hermes` from an honest-but-fragile v0.1 mock scaffold into a **trustworthy, audit-grade agentic core** whose green checks mean something — **and** position it to run *inside* the Hermes Nous framework the operator already runs in production (Telegram gateway), reusing Hermes governance primitives instead of re-deriving them.

Two strands, deliberately separable:
- **Strand A — Internal correctness & quality** (fix what the review found; make CI a real gate).
- **Strand B — Hermes leverage & integration** (run the pipeline from Telegram; adopt Hermes skills/plugins/governance; avoid duplicating the existing `ai-legal-development` skill).

## 2. Why (problem statement)

The review established the scaffold is well-disciplined but creates **false confidence** in three ways: (H1) the RAG eval scores a hardcoded `fake_retrieve` and never touches the served `MockVectorStore`, so the CI gate cannot regress on retrieval quality; (H2) the documented "a blocked step stops the pipeline" invariant is enforced only at the security gate; (M-series) a validator whose blocking path is unreachable in-pipeline, a second unenforced JSON-schema contract that already disagrees with the live Pydantic models, no lint/type gate, and a global mutable store with fragile test isolation.

Separately, the operator **already runs Hermes** with a `mlops/ai-legal-development` skill and a connected Telegram gateway. The scaffold currently lives in isolation: its `app/skills/SKILL_*.md` are not Hermes/agentskills.io-conformant, the pipeline is not reachable from the gateway, and it reimplements governance (human-review/external-use flags, prompt-injection scanning) that Hermes provides as first-class primitives (write-approval gating, install/context security scanning).

## 3. Scope

### In scope
- A: rewire the RAG eval to the real retriever; reconcile blocked-stops-pipeline; wire the validator live; unify the contract surface; add ruff+mypy CI; the M2/M4/L hygiene set.
- B: conform `app/skills/SKILL_*.md` to Hermes frontmatter; ship a Hermes **plugin** exposing the pipeline as tools reachable from Telegram; map Hermes governance primitives onto SecurityAgent/ValidatorAgent/trace + CNJ 615/2025; de-duplicate against the existing `ai-legal-development` skill.

### Out of scope (explicit)
- Real Qdrant / Supabase / LLM / DataJud / STJ / PJe integrations (stay feature-flagged off; v0.1 boundary preserved).
- Real FIRAC reasoning, real drafting, real precedent retrieval (planned agents stay planned).
- Fixing the operator's Discord gateway reconnect (separate ops issue; noted, not in this plan).
- Any change to the live `~/.hermes` install beyond *additive, opt-in* skill/plugin files the operator chooses to install.
- Commits/pushes — this spec/plan is authored; execution and any git operation require explicit approval.

## 4. Proposed architecture & key decisions

| # | Decision | Choice | Rationale / trade-off |
|---|---|---|---|
| D1 | RAG eval target | `evaluate_item` calls `get_vector_store().search()` over a **seeded golden corpus that MUST include distractor chunks**; `fake_retrieve` demoted to a labeled `_smoke_retrieve` | Eval must exercise the shipped code path. **Wiring alone is not enough:** the store scores by token overlap, so a corpus of only-correct chunks just moves the tautology down a layer — overlap retrieves them trivially and the gate still can't fail on quality. Distractors make it possible to retrieve the *wrong* chunk, so the metric actually discriminates. Offline-deterministic preserved via seeded MockVectorStore (no network). Expect scores < 0.85 initially — the honest baseline a gate is *for*. |
| D2 | Threshold philosophy | Keep area-coverage + dataset-size gates; **lower metric thresholds to an honest measured floor** and grow the dataset (target ≥ 24 rows, ≥ 6/area) | A gate pinned above achievable mock performance just gets disabled later; a gate at the real floor catches regressions. |
| D3 | blocked-stops-pipeline | **Enforce in `run_full_mock`**: after each `_record_trace`, if `status == "blocked"` stop before the next *legal* phase; document security as the canonical early gate | Aligns code with `08_TRACE_CONTRACT.md`. Alternative (amend the doc to "non-halting") rejected — halting is the safer judicial default. |
| D4 | Validator wiring | Feed FIRAC/draft output into `ValidatorAgent` in-pipeline (even mocked), so its blocking path is reachable; add tests reaching `blocked`/`failed` | Removes the decorative-validator dead path; makes the audit story real. |
| D5 | Contract single-source | **Pydantic is the source of truth** for the objects that *have* models (`ValidationResult`, `RetrievedContext`). Generate their JSON Schema via `model_json_schema()`. **✅ DECIDED (operator, 2026-06-14):** `agent_run.schema.json` — requires `run_id`/`started_at`/`latency_ms`/`cost_usd` (fields on **no existing model**) — is **KEPT and relabeled as an aspirational spec for a future run-ledger / cost-observability persistence layer (phase 2)**; documented as "not yet emitted by any agent"; **not** generated from a model, **not** deleted. | Eliminates dual-source drift where a model exists; the run-ledger schema is explicitly marked future-spec rather than current contract. **Audit-correctness caveat:** agents emit raw dicts into `AgentResult.output` (e.g. the validator emits a dict, not a `ValidationResult`), so the contract test must validate a **real captured runtime payload** against the schema — not just model→file consistency. |
| D6 | Lint/type gate | Add `ruff check` + `ruff format --check` + `mypy app` to `ci.yml`; add `[tool.ruff]`/`[tool.mypy]` to `pyproject.toml` | On-brand for an "auditable" project; codebase is small and already clean. |
| D7 | Qdrant coupling | Lazy-import `qdrant_client` inside `get_qdrant_client()`; move it to an optional extra (`requirements-qdrant.txt` or `[project.optional-dependencies]`) | "Optional/future" backend should not be a mandatory eager import in mock mode. |
| D8 | Store lifecycle | `autouse` pytest fixture resetting the singleton; document store as test-only; note request-scoped store as a phase-2 item | Fixes fragile isolation without over-engineering v0.1. |
| D9 | Hermes skill conformance | Add Hermes frontmatter (`name`/`description`/`version` + `## When to Use / Procedure / Verification`) to `app/skills/SKILL_*.md`; keep them agentskills.io-shaped | Makes the 12 existing skill docs loadable by the operator's Hermes; near-zero risk. |
| D10 | Hermes integration surface | Ship a **Hermes plugin** `lex-kratos/` (`plugin.yaml` + `register()` + `schemas.py` + `tools.py`) exposing `lex_intake`/`lex_run_pipeline`. **✅ DECIDED (operator, 2026-06-14): HTTP** — the plugin POSTs to a locally-running lexintel API; **no** direct import. **Reason:** Hermes runs **Python 3.11.15**; lexintel pins **3.12** + FastAPI/pydantic 2.11.7 and its README warns of venv conflicts — direct import loads lexintel's deps into Hermes's interpreter (the exact conflict). HTTP gives process isolation. | Pipeline reachable from Telegram, no core Hermes edits; handler returns JSON string, never raises (Hermes contract). |
| D11 | Governance mapping | Map Hermes write-approval gating + security scanning onto a CNJ 615/2025 checklist; reuse as prior art for SecurityAgent/ValidatorAgent/trace; do **not** fork Hermes | Avoid reinventing HITL/audit; document provenance fields (prompt_version, model_id, source citations) the trace must log. |
| D12 | De-duplication | Cross-reference the existing `~/.hermes/skills/mlops/ai-legal-development` skill; lexintel becomes the *implementation* that skill's patterns describe, not a competing doc | Prevent two diverging legal-AI knowledge sources. |

## 5. Dependencies & ordering

- A4/D5 depends on A1 being settled (schema generation touches `AgentResult`/`ValidationResult` shapes).
- A2/D3 and A3/D4 are independent of each other but both touch `orchestrator.py` → sequence them to avoid churn.
- A5/D6 (lint/type CI) should land **early** so subsequent tasks are gated.
- Strand B depends on Strand A being green (don't expose a pipeline whose contracts still drift). B9 (skill frontmatter) is independent and can land anytime.

## 6. Risks & plan B

| Risk | Mitigation / Plan B |
|---|---|
| Honest eval drops below current 0.85 and "breaks" CI | Expected. Set threshold to measured floor in the same PR; treat as new truthful baseline, not a regression. |
| mypy surfaces many pre-existing type gaps | Start `mypy` non-strict (`ignore_missing_imports`, no `--strict`); ratchet later. |
| Generating JSON Schema changes public artifact shape | The hand-written schemas are unenforced and already wrong → no real consumer to break; snapshot-test the generated output. |
| Hermes plugin tightly couples lexintel to a Hermes version | Keep the plugin a thin adapter over a stable orchestrator/HTTP contract; lexintel core stays framework-agnostic. |
| Touching the live `~/.hermes` install | Plan only *produces* installable artifacts; operator installs via `hermes skills tap`/plugin drop. No in-place edits. |

## 7. Test strategy

- Per task: `pytest --tb=short -q` green + `ruff check`/`ruff format --check` clean (stack auto-detected: Python).
- New tests required for: D1 (eval calls real store, fails on a deliberately broken store), D3 (a mid-pipeline blocked halts downstream), D4 (validator blocks on injected bad draft; failed propagates), D5 (generated-schema drift check), D10 (plugin tool returns valid JSON string, never raises).
- Determinism preserved: no network in any test; seeded MockVectorStore only.

## 8. Acceptance criteria ("done")

1. `python -m app.evals.run_eval` scores `MockVectorStore.search()`, not `fake_retrieve`; the corpus contains **distractor chunks** and a deliberately **mis-seeded** relevant chunk produces measurably **lower** recall (proves the eval *discriminates*, not just that it's *wired*); dataset ≥ 24 rows / ≥ 6 per required area; thresholds reflect measured floor. (D1/D2)
2. A `blocked` from any agent halts subsequent legal phases in `run_full_mock`, matching `08_TRACE_CONTRACT.md`; test proves it. (D3)
3. `ValidatorAgent` validates real pipeline draft output; tests reach `blocked` and `failed` through the orchestrator. (D4)
4. Contract test validates a **real captured agent runtime payload** against its schema (not just model→file). `ValidationResult`/`RetrievedContext` schemas generated from Pydantic + CI drift gate. `agent_run.schema.json` resolved per the OPEN DECISION (kept-as-aspirational or deleted), not silently regenerated. (D5)
5. CI runs `ruff` + `mypy`; both green. (D6)
6. `qdrant_client` lazily imported + optional; mock pipeline runs without it installed. (D7)
7. `autouse` reset fixture; suite order-independent. (D8)
8. The 12 `SKILL_*.md` carry Hermes-conformant frontmatter + sections. (D9)
9. A `lex-kratos` Hermes plugin exposes `lex_intake`/`lex_run_pipeline`, callable from the Telegram gateway, returning JSON strings; documented install steps. (D10)
10. A `docs/COMPLIANCE_CNJ_615.md` maps each CNJ 615/2025 + LGPD requirement to a concrete repo/trace feature, referencing Hermes governance primitives. (D11)
11. `app/skills/` and the live `ai-legal-development` skill cross-reference each other; no duplicated source of truth. (D12)
12. Dead code removed (`SUSPICIOUS_PATTERNS`), `str(exc)` no longer leaked, compose image pinned, CI cruft gone, all tests + lint green. (M2/M4/L)

The plan with task decomposition lives at `docs/superpowers/plans/2026-06-13-lexintel-optimization-plan.md`.
