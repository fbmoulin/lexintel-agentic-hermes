# HANDOFF — lexintel-agentic-hermes

> Estado autoritativo para retomar o trabalho. Atualizado: **2026-07-11**.

## Estado atual

| | |
|---|---|
| Versão | **v0.5** |
| `master` | `2309b72` (pushed; `master == origin/master`) |
| Testes | **150 passed, 2 skipped** (+2 integração Qdrant vivo, pulados por padrão) |
| CI | verde (`ruff check` + `ruff format --check` + `mypy app` + drift de schema + `pytest` + `python -m app.evals.run_eval`) |
| Backlog crítico | **ZERO aberto** (fase P6 fechada) |
| Repo | público `github.com/fbmoulin/lexintel-agentic-hermes` |
| Clone local | `/home/fbmoulin/lexintel-agentic-hermes` |

Diretório de trabalho é limpo, exceto `uv.lock` (stub untracked, não usado — o projeto usa pip + `requirements*.txt`; ignorar ou apagar quando quiser).

## O que a v0.5 entregou (P6 — Busca híbrida jurídica, PR #22)

Busca híbrida real, **mock-first e determinística por padrão** (Qdrant permanece opt-in via `QDRANT_ENABLED`).

**Módulos novos:**
- `app/services/bm25.py` — `BM25Retriever` (Okapi, esparso, puro Python; reusa o `_tokenize` compartilhado → **TF binário**, ver limitações).
- `app/services/fusion.py` — `reciprocal_rank_fusion` (RRF k=60; `fusion_detail` = rastro auditável; deepcopy-safe).
- `app/agents/retrieval_agent.py` — `HybridRetrievalAgent` (`search()` primitiva + `run()` wrapper de pipeline) + factory `build_default_hybrid_agent()`.

**Retriever de registro único** (sem drift entre os três pontos):
1. `/rag/search` (`app/api/rag.py`) — shape de resposta inalterado; `retrieval_method="hybrid"`.
2. Passo `retrieval` no orquestrador (`app/agents/orchestrator.py`) — **`trace-v0.3`**, entre `indexing` (6) e `firac` (8); best-effort (nunca bloqueia; falha degrada a `warning` via try/except); **FIRAC NÃO é alimentado** com o contexto (adiado). Grava `retrieved_context[]` + `precedent_count`/`requested_top_k`/`own_case_excluded_count`.
3. `run_eval` (`app/evals/run_eval.py`) — `build_hybrid_eval_store`; thresholds de não-regressão `min_average_recall_at_1=0.9375`, `min_average_mrr=1.0`.

**Offline = ensemble de DOIS sinais léxicos** (BM25 + token-overlap do Mock sobre o mesmo tokenizer), NÃO um híbrido denso+esparso verdadeiro — o lado denso (Qdrant) só participa com `QDRANT_ENABLED`. Rotulado honestamente em docs + docstrings.

**Gate empírico** (`tests/test_hybrid_eval_gate.py`): o híbrido deve **igualar ou superar** o baseline do Mock (recall@1≥0.9375, recall@3=1.0, MRR≥1.0), não o piso frouxo de 0.85. Medido: híbrido **iguala** o Mock exatamente (corpus dourado pequeno, Mock já quase-perfeito, sem margem — esperado).

## Decisões de design (aprovadas — não reverter sem motivo)

- **Retrieval filtra chunks do próprio caso** (`case_id != atual`) — surfaceia precedentes, não ecoa o caso.
- **Guarda de completude do índice:** `index_status="upsert_failed"` a montante → `warning` + `requires_human_review=True` (sinal de proveniência; degrada, não bloqueia).
- **Shortfall de precedentes é INFORMACIONAL, não warning** — recuperar menos que `top_k` é normal (corpus pequeno); surfaceado via os campos de contagem + `logger.info`. Só a guarda de índice escala o status. (Senão todo run do pipeline viraria "warning".)
- **FIRAC não alimentado** — o passo de retrieval é trace-only por ora; fiar retrieval→FIRAC fica para quando FIRAC deixar de ser mock.

## Follow-ups abertos (nenhum bloqueia; ambos em `docs/12_VECTOR_INDEXING_CONTRACT.md`)

1. **BM25 usa TF binário** — o `_tokenize` compartilhado retorna `set`, então `Counter(_tokenize(text))` dá tf∈{0,1} e a saturação de TF do BM25 opera sobre presença. OK para chunks curtos (1–2 frases); revisar (tokenizer que preserve frequência) antes de indexar documentos longos.
2. **`/rag/search` reconstrói o BM25 por requisição** — `build_default_hybrid_agent()` → `snapshot_chunks()` → novo `BM25Retriever` a cada chamada. Trivial no mock; no caminho Qdrant faz scroll da coleção inteira por query. **Cache ingênuo é PERIGOSO** (índice BM25 defasado após upsert quebra `test_rag_search_finds_chunks_indexed_by_pipeline`) → precisa de invalidação-no-upsert ou BM25 incremental **antes** de o caminho Qdrant servir produção.

## Próximo na estrada (`docs/01_SPEC_TECNICO_COMPLETO.md`)

- **v0.6:** FIRAC+ e geração de minuta com validação (⚠️ HIGH RISK sob CNJ Res. 615/2025 — ver `docs/COMPLIANCE_CNJ_615.md`).
- Depois: n8n + Google Drive/Docs/Sheets; v1.0 = produto MVP auditável.

## Como rodar / verificar

```bash
cd /home/fbmoulin/lexintel-agentic-hermes
# testes (usar o venv do projeto; miniforge default vaza deps erradas)
.venv/bin/python -m pytest -q                 # 150 passed, 2 skipped
.venv/bin/python -m app.evals.run_eval        # exit 0; retriever=hybrid; passed=true
.venv/bin/ruff check app tests scripts integrations
.venv/bin/ruff format --check app tests scripts integrations
# API
uvicorn app.main:app --port 8000              # POST /rag/search → vector_backend="hybrid"
```

⚠️ **CI roda um gate ruff separado que o pytest NÃO exercita** — sempre rodar `ruff check` + `ruff format --check` antes de push (pytest-verde ≠ CI-verde).

## Convenções do repo (relevantes)

- **Direto-a-master autorizado** para este repo quando o Felipe pede explicitamente (ex.: docs-sync `d261e40`, `2309b72`); caso contrário, branch → PR (repo tem CI + histórico de PRs).
- Commits em inglês, **sem co-authorship/atribuição de IA** (Felipe é autor único).
- Merges preservam histórico (merge commits, não squash) — ver `## MERGE GOTCHA` no histórico de memória sobre PRs empilhados.

## Artefatos de referência desta feature

- Spec: `docs/superpowers/specs/2026-07-10-hybrid-retrieval-design.md`
- Plano TDD: `docs/superpowers/plans/2026-07-10-hybrid-retrieval.md`
- Contratos atualizados: `docs/08_TRACE_CONTRACT.md` (trace-v0.3), `docs/10_RAG_EVAL_CONTRACT.md` (híbrido + não-regressão), `docs/12_VECTOR_INDEXING_CONTRACT.md` (limitações).
- Changelog: `CHANGELOG.md` `[0.5.0]`.
