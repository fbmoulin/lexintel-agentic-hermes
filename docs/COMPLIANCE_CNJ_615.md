# Conformidade — CNJ Resolução 615/2025 + LGPD

> Mapa de requisitos → recurso do repositório → primitiva do Hermes Agent.
> Escopo: Lex Kratos Agentic Core v0.1 (mockado). Marca o que **já existe**, o
> que é **prior art reutilizável** do Hermes, e o que é **lacuna** (fase futura).
> Não é parecer jurídico; é checklist de engenharia para auditabilidade.

A Resolução CNJ 615/2025 (sucede a 332/2020) disciplina o uso de IA no Judiciário.
Os eixos abaixo resumem obrigações recorrentes; cada linha aponta como o sistema
as endereça.

## Mapa de requisitos

| Eixo (CNJ 615/2025) | Exigência (resumo) | Recurso no repositório | Prior art no Hermes | Status |
|---|---|---|---|---|
| **Supervisão humana** | Decisão final é humana; IA não decide | `AgentResult.requires_human_review`; FIRAC/Validation forçam `requires_human_review=true`; `external_use_allowed=false` fixo em saídas jurídicas | Hermes **write-approval gating** (`skills.write_approval`) estagia escritas para aprovação humana | ✅ no contrato; HITL real = fase futura |
| **Não-substituição** | Vedado substituir o ato decisório | Saídas marcadas `mock_not_for_external_use`; nenhuma minuta liberada sem revisão | — | ✅ |
| **Transparência / explicabilidade** | Rastrear como a saída foi produzida | `trace` por etapa + `trace_metadata` (trace_version, step_index, phase, agent, status); `pipeline_summary` | `SOUL.md`/prompt-assembly em camadas (estável/contexto/volátil) | ✅ trace; explicabilidade de LLM = fase futura |
| **Auditabilidade / rastreabilidade** | Registro íntegro e auditável | `_record_trace` propaga flags monotonicamente (review só sobe, external só desce); `blocked` para o pipeline (`_blocked_response`) | Hermes **audit.log** + scanning na instalação de skills | ✅ estrutura; ledger persistente = fase futura (ver `agent_run.schema.json`, future-spec) |
| **Segurança / integridade** | Proteger contra manipulação da decisão | `SecurityAgent` (prompt injection, manipulação de parcialidade, comando indevido); `/rag/search` bloqueia query suspeita | Hermes scanning de context files (injeção, unicode invisível, exfiltração de credenciais) | ✅ determinístico/monolíngue; classifier multilíngue = melhoria |
| **Anti-alucinação** | Vedado precedente/fato inventado | `ValidatorAgent` bloqueia "precedente inventado"; FIRAC roteado para o validador (caminho de bloqueio vivo) | — | ✅ regra única; validação semântica = fase futura |
| **Não-discriminação / impessoalidade** | Evitar viés e favorecimento | `SecurityAgent` detecta "favoreça uma parte"/"aja em favor da parte" | — | ⚠️ heurístico; auditoria de viés = lacuna |
| **Proteção de dados (LGPD)** | Minimização, retenção, finalidade de dados do processo (CPF, OAB, nº processo) | Sem persistência de texto bruto na v0.1; `errors` ao cliente são genéricos (não vazam `str(exc)`) | Hermes truncamento + scanning de exfiltração | ⚠️ parcial; retenção/forget + redação de PII = lacuna |
| **Prestação de contas** | Responsável identificável pela saída | `case_id` + trace por etapa; `agent_name`/`scan_version` | — | ✅ técnico; vínculo a magistrado responsável = fase futura |

## Proveniência a registrar (pipeline real)

Quando os agentes deixarem de ser mock, o trace/ledger deve registrar por etapa
(hoje ausentes — ver `agent_run.schema.json` como future-spec):

- `prompt_version` / `model_id` / `provider` — qual prompt e modelo geraram a saída;
- `source_citations` — fontes/precedentes recuperados que embasaram a análise;
- `human_reviewer` + `review_decision` + `timestamp` — quem aprovou e quando;
- `run_id`, `started_at`/`finished_at`, `latency_ms`, `cost_usd` — execução e custo;
- hash/encadeamento para detecção de adulteração (deferido; ver decisão MVP do KCP).

## Lacunas declaradas (honestas)

1. **HITL real**: hoje as flags exigem revisão, mas não há gate que **impeça**
   liberação sem aprovação registrada. Reutilizar o write-approval gating do Hermes.
2. **Retenção/LGPD**: sem política de retenção, `forget`, ou redação de PII.
3. **Auditoria de viés**: detecção de parcialidade é só por regex de instrução.
4. **Ledger persistente assinado**: `agent_run.schema.json` é spec, não implementação.

Estas lacunas são intencionais para a v0.1 mockada e devem ser fechadas em tarefa
explícita antes de qualquer uso com dados reais de processo.
