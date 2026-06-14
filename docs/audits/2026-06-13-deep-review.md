# Deep Review — `lexintel-agentic-hermes` (Lex Kratos Agentic Core v0.1)

> Reviewer: independent code analysis · 2026-06-13
> Commit reviewed: `e5a0c05` (master) · 53 tests passing · eval recall@3 = 0.917
> Lineage: conceptual reboot of [`kratos-master`](https://github.com/fbmoulin/kratos-master) (the mature 7-layer enterprise ecosystem, 295 tests, AWS/CNJ-deployed). This repo is the **deliberate clean-slate v0.1 scaffold** of just the *agentic core*, fully mocked.

---

## 1. Verdict

A **disciplined, honest, well-scoped v0.1 scaffold.** It does exactly what `AGENTS.md` and the README promise: a small, auditable, fully-mocked FastAPI pipeline of 8 specialized agents with a deterministic trace contract, no external calls, and a green test+eval gate. The engineering hygiene is good for a v0.1: clean Pydantic contracts, path-traversal-safe skill loader, feature-flagged Qdrant, consistent `requires_human_review`/`external_use_allowed` propagation, and meaningful tests (≈215 asserts / 53 tests).

The risk is **not what it does — it's what it *appears* to do.** Two things create false confidence: (1) the RAG eval is tautological and doesn't exercise the actual vector store, and (2) one documented safety invariant ("a blocked step stops the pipeline") is only enforced at the security gate. Neither breaks v0.1, but both will silently mislead once real components are plugged in. Fix those two and tighten a handful of smells below.

**Grade by dimension** (as a v0.1 mock scaffold, not as production):

| Dimension | Grade | Note |
|---|---|---|
| Scope discipline / honesty | A | Mock boundaries explicit everywhere; no scope creep |
| Architecture (orchestrator + agents) | A− | Clean separation; collect-then-summarize trace |
| Data contracts (Pydantic) | B+ | Rich/validated Pydantic — but a 2nd, unenforced JSON-schema surface drifts from it (M5) |
| Security agent | B+ | Solid normalization; deterministic; some gaps |
| RAG eval harness | C | **Tautological; tests `fake_retrieve`, not `MockVectorStore`** |
| Test quality | B+ | Good asserts; fragile global-state isolation |
| CI / tooling | C+ | No lint/type gate despite ruff+mypy intent in `.gitignore` |
| Docs | A− | Extensive; one contract drifts from code |

---

## 2. Architecture map

```
POST /cases/intake       → CaseOrchestrator.run_intake_only   (intake → security)
POST /cases/run-full-mock → CaseOrchestrator.run_full_mock     (8 agents)
POST /rag/search         → SecurityAgent gate → get_vector_store().search()
GET  /eval/run           → app.evals.run_eval.run()  (fake_retrieve, NOT the store)
GET  /catalog/skills|agents → skill_loader + agent registry (self-validating)
GET  /health
```

Full-mock pipeline (orchestrator.py):
`Intake → Security → [block?] → Extraction → Normalization → Metadata → Indexing → FIRAC → (hardcoded mock_draft) → Validation → summarize`

The orchestrator design is the strongest part: each agent returns a uniform `AgentResult`; `_record_trace` propagates review/external flags monotonically (review can only turn *on*, external only turn *off*) and stamps `trace_metadata`; `_summarize_trace` aggregates. This is the right shape for an auditable judicial pipeline.

---

## 3. Findings

### 🔴 High — address before this scaffold guides real implementation

**H1. The RAG eval scores a retriever you don't ship, and the contract doesn't disclose it.**
The precise, non-obvious failure (not "it's mocked" — the docs say that everywhere): `app/evals/run_eval.py::fake_retrieve` hardcodes source lists keyed on query substrings (`"fraude"`/`"banco"` → `["Súmula 479/STJ", "CDC art. 14"]`), and `golden_dataset.jsonl` is co-designed so each query contains exactly those keywords with matching `expected_sources`. But the decisive point is that the eval calls `fake_retrieve`, **not** `MockVectorStore.search()` — the very store `/rag/search` actually serves. The two retrieval systems share no code. So the recall@3/MRR gate gives **zero signal about the retrieval code you ship**: it cannot fail from a *retrieval-quality* regression because it never exercises retrieval (it can still fail on `dataset_size`/`required_areas`). Every historical green check is meaningless for retrieval quality, and the harness must be rewired the day real retrieval lands.
`docs/10_RAG_EVAL_CONTRACT.md` documents the dataset, metrics, and the 0.85 thresholds as an acceptance gate — but **never discloses** that the scored retriever is a hardcoded keyword map disconnected from the served store. That silence is the real defect: the contract presents a quality bar without its central caveat. (Not a contract *violation* — the doc doesn't claim to measure real retrieval — but a material under-disclosure.)
*Also note:* the run passes at the exact floor — `dataset_size` is **8 vs `min` 8**; deleting one golden case fails the gate on size alone, independent of any metric.
*Fix:* point `evaluate_item` at `get_vector_store().search()`, seed the store with the golden corpus, accept that early real numbers will be < 0.85 (that's what a gate is *for*), and add a sentence to doc 10 stating which retriever is scored. Keep `fake_retrieve` only as an explicitly labeled harness smoke test.

**H2. Documented safety invariant only half-enforced.**
`docs/08_TRACE_CONTRACT.md` → *Regras*: "Se uma etapa retorna `blocked`, o pipeline deve parar antes de etapas jurídicas posteriores." But `run_full_mock` only short-circuits on **SecurityAgent**. Any later `blocked`/`failed` (e.g. a future precedent validator mid-pipeline) does **not** stop downstream legal steps — indexing/FIRAC/validation still run and side effects (vector upsert) still happen.
*Impact:* latent correctness/compliance bug. Harmless today only because the sole mid-pipeline blocker (ValidatorAgent) runs last on a benign hardcoded draft.
*Fix:* after each `_record_trace`, if `result.status == "blocked"`, stop before the next legal phase — or amend the contract to say "the security gate blocks; later blocks are surfaced but non-halting," and make that explicit.

### 🟠 Medium

**M1. ValidatorAgent's blocking path is unreachable through the orchestrator.**
`run_full_mock` validates a hardcoded benign `mock_draft` (`"Relatório simulado."` …), which never contains `"precedente inventado"`. So the validator always approves in-pipeline; its only real logic is exercised solely by direct unit tests. The FIRAC output (also empty) is never fed to the validator. The "validation" step is currently decorative within the pipeline.
*Fix:* wire FIRAC/draft output into the validator input even in mock mode, so the path is live.

**M2. Global mutable singleton vector store; fragile test isolation.**
`vector_store._MOCK_STORE_INSTANCE` is module-global and shared across all requests and the IndexingAgent. In production this is cross-request shared state (concurrency hazard once it matters). In tests, isolation depends on each test *remembering* to call `reset_mock_vector_store()` manually — there is no `autouse` fixture, so test-ordering can leak seeded/indexed chunks.
*Fix:* add an `autouse=True` conftest fixture calling `reset_mock_vector_store()`; document the singleton as test-only and plan a request-scoped store for real use.

**M3. CI has no lint or type gate, despite intent.**
`.gitignore` ignores `.ruff_cache/` and `.mypy_cache/`, but no ruff/mypy config exists anywhere and `ci.yml` runs only `pytest` + the eval. For a project whose entire selling point is *auditability*, an unchecked style/type surface is a gap.
*Fix:* add `ruff check` + `ruff format --check` (and ideally `mypy app`) as CI steps; the codebase is small and already clean, so this is near-free.

**M4. `qdrant-client` is a hard, eagerly-imported dependency in "Qdrant-optional" v0.1.**
`qdrant_service.py` does `from qdrant_client import QdrantClient` at module top level, and that module is imported transitively by `vector_store` → the whole mock pipeline. So the "optional/future" backend is mandatory to even run the mock, and a heavy client is imported at startup unconditionally.
*Fix:* move the import inside `get_qdrant_client()` (lazy) and mark `qdrant-client` as an optional extra, not a core requirement.

**M5. A second, unenforced, *drifting* contract surface — the JSON schemas.**
`app/schemas/*.schema.json` is a parallel hand-written contract sitting next to the Pydantic models, but **nothing references or validates against it** (no `jsonschema` dependency; grep finds zero usages). It is also **already out of sync** with the live objects:
- `agent_run.schema.json` *requires* `run_id`, `started_at` and lists `finished_at`/`latency_ms`/`cost_usd` — **none of which exist on the live `AgentResult`**, which instead carries `requires_human_review`, `external_use_allowed`, `trace_metadata`, `case_id` (absent from the JSON schema). The two describe materially different objects.
- `validation_result.schema.json` enumerates five `blocking_errors.type` values (`missing_claim`, `unsupported_fact`, `contradiction`, `security_risk`, …) but `ValidatorAgent` only ever emits `hallucinated_precedent`, and its `output` isn't even a `ValidationResult` instance.

In a system whose entire pitch is *auditability*, a dual source of truth where the documentation contract contradicts the executable contract is exactly the kind of drift an auditor would flag.
*Fix:* either delete the JSON schemas and make Pydantic the single source of truth (generate JSON Schema from the models via `model_json_schema()` if an external artifact is needed), or wire a test that validates real agent output against them. Don't keep both, unchecked.

### 🟡 Low / polish

- **L1.** `SecurityAgent.SUSPICIOUS_PATTERNS` (16-item list) is dead code — never referenced; `DETECTION_RULES` is the live path. Delete or wire it in (it actually contains items like `"modo desenvolvedor"` already covered, but also plain `"jailbreak"` redundancy).
- **L2.** `/rag/search` and `IndexingAgent` return `str(exc)` to the API client. Low risk now (mock), but in a PII-bearing legal system, raw exception text to clients is a disclosure smell. Log full, return a generic message + correlation id.
- **L3.** `docker-compose.yml` pins `qdrant/qdrant:latest` — unpinned tag undermines reproducibility for an "auditable" stack. Pin a digest/version.
- **L4.** `ci/rerun-trigger.txt` and the deprecated duplicate CI manifest (`github/GITHUB_ACTIONS_CI.yml`) are repo cruft from a past CI fix; remove to reduce confusion about which workflow is canonical.
- **L5.** Security detection is monolingual-PT and substring/regex based after accent-folding. It correctly defeats zero-width/punctuation obfuscation (nice, and tested), but is trivially bypassed by English (`"ignore previous instructions"` — only the command/file-deletion rules have EN variants), synonyms, or base64/encoding. Fine for v0.1; note it loudly so it isn't mistaken for a real guardrail.
- **L6.** Both `_response_status` "failed" handling and IndexingAgent "failed" status exist, but no full-mock test drives a `failed` through the orchestrator (only the rag-search controlled-failure path is tested). Add one.
- **L7.** `CaseOrchestrator` is instantiated per-request in `cases.py`, rebuilding all 8 agents (and calling `get_vector_store()`) each call. Negligible now; consider a shared/injected orchestrator when agents become stateful or expensive.

---

## 4. What's genuinely well done (keep doing this)

- **Mock honesty is everywhere in the type system,** not just docs: `external_use_allowed` defaults `False`, `extraction_method: Literal["mock_filename_template"]`, schema-version strings (`*-mock-v0.1`) baked into outputs. This makes "is this real?" answerable from any payload — exactly right for a judicial audit trail.
- **`skill_loader._resolve_skill_path`** is properly defensive (name-only enforcement, `SKILL_*.md` allowlist, resolved-parent equality check) — a textbook path-traversal guard.
- **Self-validating agent registry** (`validate_agent_registry`) cross-checks implemented↔importable, skill existence, and that human-review phases carry the flag. This is a quietly excellent auditability feature.
- **Trace flag monotonicity** in `_record_trace` (review only escalates, external only de-escalates) is the correct invariant for compliance and is implemented cleanly.
- **Tests assert behavior, not implementation** (obfuscation, severity, trace ordering, controlled failures), and run fully offline/deterministic per `AGENTS.md`.

---

## 5. Relationship to `kratos-master` (the origin idea)

`kratos-master` is the full vision: 7 layers, microservices (`audit-service`, `graphrag-proxy`, `pdf-extraction-adapter`, `prompt-registry`, LangGraph `kratos-v5`), Next.js ops-console, real CNJ 615/2025 audit, AWS deployment, 295 tests. `lexintel-agentic-hermes` is the right instinct: **don't fork the monolith — re-grow the agentic core from a clean, mocked seed** with hard human-review/anti-hallucination invariants wired in from line one. `AGENTS.md`'s "não reutilizar código legacy sem autorização" enforces that discipline.

The main strategic caution: the planned agents (HybridRetrieval, Jurisprudence, Drafting, Evaluation) are exactly where `kratos-master` already has battle-tested implementations and contracts (GraphRAG proxy, prompt-registry, audit HITL). When promoting phases here, **port the contracts/test corpora from `kratos-master`, not the code** — otherwise this scaffold re-derives lessons the ecosystem already paid for (e.g. the real eval set, the CNJ provenance metadata, the HITL double-approval lock).

---

## 6. Recommended next actions (priority order)

1. **(H1)** Rewire `run_eval` to evaluate `MockVectorStore`; demote `fake_retrieve` to a labeled smoke test. Expect the gate to drop below 0.85 and treat that as honest signal.
2. **(H2)** Decide and enforce the blocked-stops-pipeline semantics; reconcile `orchestrator.py` ↔ `08_TRACE_CONTRACT.md`.
3. **(M1)** Feed FIRAC/draft output into ValidatorAgent so its blocking path is live in-pipeline; add a full-mock test that reaches `blocked` and `failed`.
4. **(M3)** Add `ruff` + `mypy` to CI (cheap, on-brand for "auditable").
5. **(M5)** Resolve the dual contract: make Pydantic the single source of truth (delete or auto-generate the JSON schemas), or add a validation test against them.
6. **(M2/M4/L-series)** `autouse` reset fixture; lazy Qdrant import + optional extra; pin compose image; delete dead `SUSPICIOUS_PATTERNS` and CI cruft; stop leaking `str(exc)`.

None of these block v0.1 acceptance — they harden the seed so phase 2 inherits truth instead of green theater.
