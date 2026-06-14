# PLAN — Optimization of `lexintel-agentic-hermes`

> Status: DRAFT for approval · 2026-06-13 · Spec: `../specs/2026-06-13-lexintel-optimization.md`
> Branch (when approved): `feat/optimization-strand-a` then `feat/hermes-integration-strand-b` (branch from master; never commit to master directly).
> Baseline: master `e5a0c05`, 53 tests passing, eval recall@3 = 0.917 (tautological). Stack: Python 3.12 · `pytest` · `ruff` (to add).
> Each task = single responsibility, independently testable, atomic commit, < 30 min. Execute one at a time, validate before advancing.

---

## Sequencing overview

```
A5 (lint/type CI)  ──┐  land FIRST so everything after is gated
A6 (hygiene set)   ──┤
A1 (eval rewire)   ──┼─ Strand A: correctness & honest gate ─┐
A2 (blocked halts) ──┤                                       │ A green
A3 (validator live)──┤                                       │ before
A4 (one contract)  ──┘                                       │ Strand B
                                                             ▼
B9 (skill frontmatter, independent) ── B1 (CNJ doc) ── B2 (Hermes plugin) ── B3 (de-dup w/ ai-legal-development)
```

---

## STRAND A — Internal correctness & honest gate

### A5 — Add lint + type gate to CI *(do first)*
- **Files:** `pyproject.toml` (+`[tool.ruff]`, `[tool.mypy]` non-strict, `ignore_missing_imports`), `.github/workflows/ci.yml` (steps: `ruff check`, `ruff format --check`, `mypy app`), `requirements-dev.txt` (ruff, mypy).
- **Do:** add config; run `ruff check --fix && ruff format` once to normalize; ensure `mypy app` passes non-strict.
- **Test/verify:** CI steps green locally; `pytest -q` still 53 green.
- **Acceptance:** D6. Commit: `ci: add ruff + mypy gate`.

### A6 — Hygiene set (dead code, leak, pins, cruft)
- **Files:** `app/agents/security_agent.py` (delete unused `SUSPICIOUS_PATTERNS`), `app/api/rag.py` + `app/agents/indexing_agent.py` (replace `str(exc)` to client with generic message + log full via `logger.exception`; keep `errors` generic), `docker-compose.yml` (pin `qdrant/qdrant:v1.14.x` digest), remove `ci/rerun-trigger.txt` + deprecated `github/GITHUB_ACTIONS_CI.yml`.
- **Test:** existing `test_rag_search_returns_controlled_failure` updated to assert generic message; `pytest -q` green.
- **Acceptance:** M2/M4/L subset. Commit: `chore: remove dead code, stop exc leakage, pin image, drop CI cruft`.

### A7 — Lazy Qdrant import + optional extra *(was D7)*
- **Files:** `app/services/qdrant_service.py` (move `from qdrant_client import QdrantClient` inside `get_qdrant_client()`), `requirements.txt` (drop `qdrant-client`), `requirements-qdrant.txt` (add it) or `pyproject` optional-deps.
- **Test:** new `test_mock_pipeline_runs_without_qdrant_client` — monkeypatch import to fail, assert `/cases/run-full-mock` + `/rag/search` still work.
- **Acceptance:** D7. Commit: `refactor: lazy qdrant import, make client an optional extra`.

### A8 — `autouse` store reset fixture *(was D8)*
- **Files:** `tests/conftest.py` (new — `@pytest.fixture(autouse=True)` calling `reset_mock_vector_store()`), drop the now-redundant manual resets in `test_api_routes.py`/`test_indexing_vector_store.py` (or leave; fixture is idempotent).
- **Test:** run suite in randomized order (`pytest -p no:randomly`? or `pytest-randomly`) → order-independent green.
- **Acceptance:** D8. Commit: `test: autouse mock-vector-store reset for isolation`.

### A1 — Rewire RAG eval to the real retriever *(core fix)*
- **Files:** `app/evals/run_eval.py` (rename `fake_retrieve` → `_smoke_retrieve`, clearly labeled; new path where `evaluate_item` builds a seeded `MockVectorStore` from a golden corpus and calls `.search()`), `app/evals/golden_corpus.jsonl` (new — chunks to seed, **MUST include distractor chunks**, not only the correct ones), `app/evals/golden_dataset.jsonl` (expand to ≥24 rows / ≥6 per area, queries decoupled from any hardcoded map).
- **Decision detail:** map `expected_sources` to chunk `source_ref`/`source` so recall is computed over real retrieved chunks. **Anti-tautology:** without distractors the token-overlap store retrieves the right chunk trivially and the gate still can't fail — distractors are load-bearing, not optional.
- **Test:** `test_eval.py` — (1) eval runs over real store; (2) **discrimination test**: a deliberately mis-seeded relevant chunk yields measurably lower recall than the correct seeding (proves the metric responds to retrieval quality); (3) empty/broken store → `passed=False`; (4) smoke path still available and labeled.
- **Acceptance:** D1 (partial). Commit: `feat(eval): score the served MockVectorStore over a corpus with distractors`.

### A2 — Honest thresholds + dataset size *(was D2)*
- **Files:** `app/evals/run_eval.py` (`DEFAULT_THRESHOLDS` → measured floor for recall@3/MRR after A1; `min_dataset_size` ≥ 24), `docs/10_RAG_EVAL_CONTRACT.md` (state which retriever is scored + new thresholds), `README.md` (sync numbers).
- **Test:** eval `passed=True` at new floor; dropping a case fails on size.
- **Acceptance:** D1/D2 complete. Commit: `feat(eval): honest thresholds + larger golden set + contract disclosure`.

### A3 — Enforce blocked-stops-pipeline *(was D3)*
- **Files:** `app/agents/orchestrator.py` (`run_full_mock`: after each `_record_trace`, `if result.status == "blocked": return early-summary` before the next legal phase), `docs/08_TRACE_CONTRACT.md` (mark security as canonical early gate; confirm rule).
- **Test:** new `test_full_mock_halts_on_midpipeline_block` — inject a stub agent returning `blocked`, assert downstream phases absent from trace and `blocked_at` set.
- **Acceptance:** D3. Commit: `fix(orchestrator): halt pipeline on any blocked legal step`.

### A4 — Wire validator live + reach blocked/failed *(was D4)*
- **Files:** `app/agents/orchestrator.py` (feed FIRAC/draft output into `ValidatorAgent` instead of a hardcoded benign draft; keep mock content but route it), `tests/test_api_routes.py` (case where draft contains "precedente inventado" → `blocked`; a `failed` indexing path propagates).
- **Test:** validator `blocked` reachable through `/cases/run-full-mock`.
- **Acceptance:** D4. Commit: `fix(orchestrator): validate real draft output; cover blocked/failed paths`.

### A9 — One contract source (generate JSON Schema) *(was D5)*
- **✅ DECIDED (operator):** `agent_run.schema.json` is **KEPT as an aspirational future-spec** for an unbuilt run-ledger/cost layer (`run_id`/`started_at`/`latency_ms`/`cost_usd`). Add a header comment / a line in `docs/08_TRACE_CONTRACT.md` marking it "future spec — not emitted by any agent yet"; do **not** generate it from a model, do **not** delete it. Generation applies only to `ValidationResult`/`RetrievedContext`.
- **Files:** `scripts/gen_schemas.py` (new — dumps `ValidationResult`/`RetrievedContext`.model_json_schema() to their `*.schema.json`; leaves `agent_run.schema.json` untouched), `docs/08_TRACE_CONTRACT.md` (mark agent_run schema as future-spec), `.github/workflows/ci.yml` (step: regenerate the two + `git diff --exit-code` drift check).
- **Test:** `test_schema_matches_runtime` — capture a **real** agent output (e.g. `ValidatorAgent(...).run(...).output`, which is a raw dict) and `jsonschema.validate` it against the committed schema. This checks schema→runtime payload, the thing that actually matters for an audit contract — not just model→file. (Add `jsonschema` to `requirements-dev.txt`.)
- **Acceptance:** D5. Commit: `refactor(schemas): single source for modelled contracts + runtime-validation gate`.

**Strand A gate:** all of A* green (pytest + ruff + mypy), eval honest, acceptance 1–7 + 12 met → proceed to Strand B.

---

## STRAND B — Hermes leverage & integration

### B9 — Conform `app/skills/SKILL_*.md` to Hermes/agentskills.io *(independent, can land early)*
- **Files:** the 12 `app/skills/SKILL_*.md` — add frontmatter (`name`, `description`, `version: 1.0.0`, `metadata.hermes.tags`/`category: legal`) + ensure `## When to Use / ## Procedure / ## Verification` sections.
- **Test:** a small `test_skill_frontmatter` (skill_loader parses frontmatter; `validate_agent_registry` still green).
- **Acceptance:** D9. Commit: `docs(skills): make SKILL_*.md Hermes/agentskills.io-conformant`.

### B1 — CNJ 615/2025 + LGPD compliance map *(was D11)*
- **Files:** `docs/COMPLIANCE_CNJ_615.md` (new — table: requirement → repo/trace feature → Hermes primitive used; provenance fields to log: `prompt_version`, `model_id`, `source_citations`, `human_reviewer`, `timestamp`).
- **Note:** ground in the live `ai-legal-development` references (`judicial-pipeline-benchmark`, `brazilian-legal-sources`).
- **Acceptance:** D10 (doc). Commit: `docs: CNJ 615/2025 + LGPD compliance mapping`.

### B2 — Hermes plugin exposing the pipeline *(was D10)*
- **✅ DECIDED (operator): HTTP transport.** Hermes (Py3.11.15) and lexintel (Py3.12 + FastAPI/pydantic) would clash on a shared interpreter, so the plugin POSTs to a running lexintel API — process isolation, no shared venv. (Operator must have the lexintel API up: `uvicorn app.main:app` or a container; document in the plugin README.)
- **Files (new, shippable, NOT auto-installed):** `integrations/hermes/lex-kratos/{plugin.yaml, __init__.py, schemas.py, tools.py, README.md}`.
  - `plugin.yaml`: `name: lex-kratos`, `provides_tools: [lex_intake, lex_run_pipeline]`, `requires_env` for the lexintel base URL.
  - `tools.py`: handlers `def lex_run_pipeline(args, **kwargs) -> str` that **POST to a running lexintel API** (`LEX_KRATOS_BASE_URL`, default `http://127.0.0.1:8000`); direct-import variant documented but gated on the decision above. Always `json.dumps(...)`, never raise (return `{"error": ...}`).
- **Test:** `integrations/hermes/lex-kratos/test_tools.py` — `lex_run_pipeline` returns valid JSON string for a sample case; bad input returns `{"error": ...}` not an exception.
- **Install doc:** `cp -r integrations/hermes/lex-kratos ~/.hermes/plugins/ && hermes plugins list` (operator action; **out of plan execution** — we only produce the artifact).
- **Acceptance:** D10. Commit: `feat(hermes): lex-kratos plugin — run the judicial pipeline from the gateway`.

### B3 — De-duplicate with the existing `ai-legal-development` skill *(was D12)*
- **Files:** `docs/09_SKILLS_AGENTS_CATALOG.md` (cross-reference the operator's `mlops/ai-legal-development` skill as the *methodology* this repo *implements*), and a short `## Relationship to Hermes ai-legal-development skill` section in `README.md`.
- **Acceptance:** D12. Commit: `docs: align repo as the implementation of the ai-legal-development skill`.

**Strand B gate:** acceptance 8–11 met; plugin tested; compliance + de-dup docs in place.

---

## Execution notes (dev-workflow)

- Use `TaskCreate` to track A5→A6→A7→A8→A1→A2→A3→A4→A9, then B9→B1→B2→B3. One at a time.
- `/compact` at ≥60% context, preserving: branch + modified files, test command + count, this plan path, open PR, next task.
- Spawn only for genuinely parallel research (none anticipated here — it's sequential edit work).
- **Phase 6 final validation** before declaring done: all acceptance criteria, no out-of-scope edits, edge cases, tests + ruff + mypy green, MEMORY.md updated.
- **Nothing is committed or pushed without explicit approval.** Branch from master; PR per strand.

## Operational freebie (out of scope, flagged)
The live Hermes gateway shows **Discord = "retrying / failed to reconnect"** while Telegram is connected. Not part of this plan; fix separately (`hermes doctor`, re-auth Discord token) if desired.
