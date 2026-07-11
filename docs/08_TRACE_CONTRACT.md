# Contrato de Trace v0.3

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

- `trace_version`: versao do contrato, atualmente `trace-v0.3`.
- `step_index`: indice deterministico da etapa, iniciado em 1.
- `phase`: fase funcional, como `intake`, `security`, `extraction`, `normalization`, `metadata`, `indexing`, `retrieval`, `firac` ou `validation`.
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

## Etapa `retrieval` (busca hibrida)

A partir de `trace-v0.3` o pipeline inclui a etapa `retrieval` (`HybridRetrievalAgent`), que roda **entre `indexing` (step 6) e `firac` (step 8)**.

- **Best-effort:** a etapa nunca emite `blocked` e nunca interrompe o pipeline. No pior caso degrada para `warning`.
- **Output** registra os precedentes recuperados e contadores de auditoria:
  - `retrieved_context[]`: precedentes recuperados (exclui os chunks do proprio caso).
  - `precedent_count`: numero de precedentes efetivamente retornados.
  - `requested_top_k`: quantos precedentes foram solicitados.
  - `own_case_excluded_count`: quantos candidatos foram descartados por pertencerem ao proprio caso.
- **Guarda de completude do indice:** se um agente a montante marcou `index_status="upsert_failed"`, o corpus recuperavel de precedentes pode estar defasado. Nesse caso a etapa emite `status="warning"` e `requires_human_review=True` como sinal de proveniencia (degrada, nao interrompe).
- **Escassez de precedentes e INFORMACIONAL:** recuperar menos precedentes que `requested_top_k` (corpus pequeno) e apenas registrado em log — NAO escala `status` nem `requires_human_review`. Escalar toda corrida curta tornaria o status do pipeline sem significado.
- **FIRAC ainda NAO consome o contexto recuperado:** a injecao do `retrieved_context` na analise FIRAC esta adiada para uma fase futura.

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
