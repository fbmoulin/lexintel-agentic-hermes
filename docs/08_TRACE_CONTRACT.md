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

- Se uma etapa retorna `blocked`, o pipeline deve parar antes de etapas juridicas posteriores.
- Saidas juridicas mockadas devem manter `requires_human_review = true`.
- Saidas juridicas mockadas devem manter `external_use_allowed = false`.
- Testes devem permanecer locais e deterministicos.
