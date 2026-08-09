# CLAUDE.md

Memória do projeto para o Claude Code. Estado autoritativo detalhado em
`docs/HANDOFF.md`; regras de trabalho em `AGENTS.md` (valem integralmente aqui).

## O que é este repositório

Núcleo jurídico agentico do Lex Kratos (v0.5.1): FastAPI + 8 agentes
especializados mockados + busca híbrida (BM25 com tf real + fusão RRF,
Qdrant opcional e desligado por padrão) + avaliação RAG com gates de
não-regressão. Mock-first e auditável por princípio — nenhuma integração real
(Supabase, n8n, DataJud, PJe, LLMs) sem tarefa explícita; a única exceção é o
Qdrant opcional atrás de `LEX_KRATOS_ENABLE_QDRANT`.

## Comandos (gates de aceite — todos devem passar)

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check app tests scripts integrations && ruff format --check app tests scripts integrations
python -m mypy app          # SEMPRE via o Python do projeto — ver gotcha abaixo
python -m scripts.gen_schemas && git diff --exit-code app/schemas   # drift de schema
pytest                      # 156 passed, 2 skipped (integração Qdrant pulada)
python -m app.evals.run_eval  # exit 0; retriever=hybrid; passed=true
```

## Arquitetura em uma tela

- `app/main.py` registra as rotas de `app/api/` (health, cases, rag, evals, catalog).
- Pipeline (`app/agents/orchestrator.py`): Intake → Security → Extraction →
  Normalization → Metadata → Indexing → **Retrieval (best-effort, trace-only)**
  → FIRAC → Validator. `blocked` interrompe; indexação/retrieval degradam para
  `warning`, nunca bloqueiam.
- Retrieval de registro único: `build_default_hybrid_agent()`
  (`app/agents/retrieval_agent.py`) serve `/rag/search`, o passo do pipeline e
  a avaliação. Índice BM25 cacheado por (store, `store.version`); `upsert`
  incrementa `version` e invalida.
- Stores (`app/services/vector_store.py`): `MockVectorStore` (singleton,
  resetado por autouse fixture nos testes) e `QdrantVectorStore` (flag).
  `build_retrieved_context` é a ÚNICA fonte do shape RetrievedContext.
- Contratos Pydantic em `app/schemas/case.py`; JSON schemas gerados por
  `scripts/gen_schemas.py` (gate de drift no CI).

## Decisões aprovadas — não reverter sem motivo registrado

- **FIRAC não recebe o contexto recuperado** (trace-only) até deixar de ser
  mock. Já foi erroneamente apontado como defeito em auditoria e retirado —
  ver `docs/audits/2026-08-08-full-review.md` (L1) e `docs/HANDOFF.md`.
- Retrieval exclui chunks do próprio caso (surfaceia precedentes).
- Shortfall de precedentes é informacional, não warning.
- `requires_human_review` só liga; `external_use_allowed` só desliga
  (propagação monotônica no trace) e é sempre `False` em saída jurídica.
- Padrões do SecurityAgent são escritos contra o texto NORMALIZADO
  (pontuação vira espaço: "cmd.exe" → "cmd exe").

## Gotchas

- **mypy:** rode `python -m mypy app` com o Python do projeto. Um mypy
  instalado fora do venv não enxerga `qdrant-client`, colapsa os tipos em
  `Any` e falha com `unused-ignore` em `vector_store.py` — erro de ambiente,
  não de código.
- **Porta Qdrant:** o padrão do repo é **6533** (não 6333), single-sourced em
  `DEFAULT_QDRANT_PORT` (`app/services/qdrant_service.py`); `.env.example`,
  compose e o guard do teste de integração concordam.
- Tokenizers: `_tokenize` (set) para overlap do Mock; `_tokenize_seq` (lista,
  preserva frequência) para o BM25. Não trocar um pelo outro.
- Docs em português; código/comentários em inglês; auditorias em inglês no
  padrão `docs/audits/YYYY-MM-DD-*.md` (header com ground truth, findings
  ranqueados M/L, disposition).
- Antes de apontar um achado de auditoria como novo, checar
  `docs/HANDOFF.md` (Follow-ups/Decisões) e os contratos em `docs/` —
  limitações conhecidas já estão registradas lá.
