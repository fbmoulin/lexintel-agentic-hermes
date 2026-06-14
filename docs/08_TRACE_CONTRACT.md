# Contrato de Trace v0.2

O trace do Lex Kratos Agentic Core v0.1 e deterministico, local e mockado. Ele existe para auditoria tecnica do fluxo, nao para demonstrar analise juridica real.

## Campos por agente

Cada entrada em `trace` segue o contrato `AgentResult`:

- `case_id`: identificador do caso.
- `agent_name`: nome do agente.
- `status`: `success`, `warning`, `failed` ou `blocked`.
- `output`: payload especifico do agente.
- `warnings`: lista de avisos.
- `errors`: lista de erros.
- `requires_human_review`: indica se a etapa exige revisao humana.
- `external_use_allowed`: sempre `false` para saidas juridicas mockadas.
- `trace_metadata`: metadados da etapa.

## `trace_metadata`

Campos obrigatorios:

- `trace_version`: versao do contrato, atualmente `trace-v0.2`.
- `step_index`: indice deterministico da etapa, iniciado em 1.
- `phase`: fase funcional, como `intake`, `security`, `extraction`, `normalization`, `metadata`, `firac` ou `validation`.
- `agent_name`: nome do agente.
- `status`: status da etapa.

## `pipeline_summary`

Cada resposta de pipeline inclui:

- `trace_version`.
- `pipeline_name`.
- `agent_count`.
- `completed_agents`.
- `blocked_at`.
- `warning_count`.
- `error_count`.
- `requires_human_review`.
- `external_use_allowed`.

## Regras

- Se uma etapa retorna `blocked`, o pipeline para antes de etapas juridicas posteriores (aplicado em `run_full_mock` via `_blocked_response`).
- Saidas juridicas mockadas devem manter `requires_human_review = true`.
- Saidas juridicas mockadas devem manter `external_use_allowed = false`.
- Testes devem permanecer locais e deterministicos.

## Contratos JSON Schema

Fonte unica de verdade = modelos Pydantic. Schemas derivados por `python -m scripts.gen_schemas` (CI reprova em drift):

- `app/schemas/validation_result.schema.json` — gerado de `ValidationResult`.
- `app/schemas/retrieved_context.schema.json` — gerado de `RetrievedContext`.

Schemas NAO gerados:

- `app/schemas/agent_run.schema.json` — **FUTURE-SPEC**: contrato aspiracional de uma camada de run-ledger / custo ainda nao implementada (`run_id`, `started_at`, `latency_ms`, `cost_usd`). Nenhum agente emite isso hoje; o contrato vivo por etapa e `AgentResult`.
- `app/schemas/retrieval_result.schema.json` — envelope da resposta de `/rag/search` (hand-authored); cada item espelha `retrieved_context.schema.json`.
