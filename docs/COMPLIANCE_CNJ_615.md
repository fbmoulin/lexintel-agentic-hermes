# Conformidade — CNJ Resolução 615/2025 + LGPD

> Mapa de requisitos → recurso do repositório → primitiva do Hermes Agent.
> Escopo: Lex Kratos Agentic Core v0.1 (mockado). Marca o que **já existe**, o que
> é **prior art reutilizável** do Hermes, e o que é **lacuna** (fase futura).
> **Não é parecer jurídico.** Baseado no texto da Resolução e em sínteses
> (fontes ao final); reconciliar com o ato oficial antes de uso institucional.

A **Resolução CNJ nº 615, de 11/03/2025** (publicada 14/03/2025, em vigor desde
**14/07/2025**; sucede a 332/2020) disciplina desenvolvimento, uso e governança de
IA no Judiciário. Eixos centrais: **categorização por risco**, governança (Comitê
Nacional de IA + registro **Sinapses**), transparência, supervisão humana e regras
específicas para **IA generativa**.

## 1. Categorização por risco — onde este sistema se enquadra

A 615/2025 classifica usos de IA em três níveis. As **funções deste pipeline**
provavelmente se distribuem assim (avaliação preliminar, sujeita ao Comitê):

| Nível (Res. 615) | Exemplos da Resolução | Funções do lexintel | Exigência |
|---|---|---|---|
| **Risco excessivo (vedado)** | Sem revisão humana; predição de crime por perfil; ranqueamento de pessoas; reconhecimento de emoções | *Nenhuma* — o sistema fixa `external_use_allowed=false` e exige revisão | Proibido |
| **Alto risco (restrito)** | Valoração de prova; **análise conclusiva de aplicação de norma**; interpretação de tipo penal; perfilamento | **FIRAC+ (`FIRACAgent`), minuta (`DraftingAgent`), validação de precedente (`JurisprudenceAgent`)** | Auditoria regular, monitoramento contínuo, **revisão anual de categoria pelo Comitê** |
| **Baixo risco (permitido c/ supervisão)** | Atos ordinatórios; classificação/agrupamento de dados; **sumarização**; transcrição; jurimetria; documento anonimizado | **Intake, segurança, extração, normalização, metadados, indexação, RAG** | Monitoramento e revisão periódicos |

> Implicação: as etapas analíticas/decisórias são **alto risco** — não podem ser
> tratadas como utilitário. Daí o pipeline forçar revisão humana e bloquear uso externo.

## 2. IA generativa (regras específicas da 615)

Relevante quando o pipeline deixar de ser mock e chamar LLMs reais:

| Regra (Res. 615) | Recurso/lacuna |
|---|---|
| Solução institucional tem prioridade; ferramenta privada só na ausência | ⚠️ decisão de arquitetura (LiteLLM/local) — documentar |
| **Vedado processar dados para treino do modelo** | ⚠️ exigir flag "no-train" nos provedores; lacuna |
| Papel **auxiliar/complementar**; vedada valoração de prova e ato decisório | ✅ `requires_human_review`/`external_use_allowed=false`; FIRAC/minuta nunca liberados |
| **Anonimização antes de enviar a plataforma externa** | ⚠️ redação de PII (CPF/OAB/nº processo) antes de chamada externa — **lacuna** |
| Transparência: informar uso de IA | ⚠️ `draft_status=mock_not_for_external_use`; disclosure formal = lacuna |

## 3. Governança, supervisão e demais eixos

| Eixo (Res. 615 / LGPD) | Recurso no repositório | Prior art no Hermes | Status |
|---|---|---|---|
| **Supervisão humana** (obrigatória em todas as categorias; IA consultiva, não vinculante) | `requires_human_review`; `external_use_allowed=false` fixo | **write-approval gating** (`skills.write_approval`) | ✅ contrato; gate que **impede** liberação = lacuna |
| **Transparência / explicabilidade** | `trace` + `trace_metadata` (versão, step, fase, agente, status) | prompt-assembly em camadas | ✅ trace; explicabilidade de LLM = futura |
| **Auditabilidade / rastreabilidade** | `_record_trace` (flags monotônicas); `blocked` para o pipeline | `audit.log` do Hermes | ✅ estrutura; ledger persistente = futura (`agent_run.schema.json`, future-spec) |
| **Registro no Sinapses** | — | — | ⚠️ **lacuna**: solução de IA deve ser cadastrada/documentada no Sinapses; descontinuação registra motivo |
| **Comitê Nacional de IA** (auditoria, revisão anual de categoria) | docs de contrato/decisão | — | ⚠️ processo institucional externo |
| **Segurança / integridade** | `SecurityAgent` (injeção, parcialidade, comando indevido) | scanning de context files | ✅ determinístico/PT; classifier multilíngue = melhoria |
| **Anti-alucinação** | `ValidatorAgent` bloqueia "precedente inventado"; FIRAC roteado ao validador | — | ✅ regra única; validação semântica = futura |
| **Não-discriminação** | detecção de "favoreça uma parte" | — | ⚠️ heurístico; auditoria de viés = lacuna |
| **Proteção de dados (LGPD)** | sem persistência de texto bruto na v0.1; `errors` ao cliente genéricos | truncamento + scanning de exfiltração | ⚠️ retenção/forget + redação de PII = lacuna |

## 4. Proveniência a registrar (pipeline real)

`prompt_version` · `model_id`/`provider` · `source_citations` · `human_reviewer` +
`review_decision` + `timestamp` · `run_id`/`started_at`/`finished_at`/`latency_ms`/`cost_usd`
(ver `agent_run.schema.json`, future-spec) · hash/encadeamento para detecção de
adulteração (deferido).

## 5. Lacunas declaradas (honestas)

1. **HITL real**: flags exigem revisão, mas não há gate que **impeça** liberação sem
   aprovação registrada — reutilizar write-approval gating do Hermes.
2. **Cadastro no Sinapses** da solução (obrigação de governança).
3. **Anonimização de PII** antes de qualquer chamada a LLM externo (IA generativa).
4. **Retenção/LGPD**: sem política de retenção/`forget`.
5. **Auditoria de viés** além de regex de instrução.
6. **Ledger persistente assinado** (`agent_run.schema.json` é spec, não implementação).

Intencionais para a v0.1 mockada; fechar em tarefa explícita antes de uso com dados
reais de processo.

## Fontes

- Resolução CNJ nº 615/2025 (texto oficial): https://atos.cnj.jus.br/atos/detalhar/6001 · PDF: https://atos.cnj.jus.br/files/original1555302025031467d4517244566.pdf
- CNJ regulamenta uso de IA no Judiciário (TRF1/SJGO): https://www.trf1.jus.br/sjgo/noticias/cnj-regulamenta-uso-da-inteligencia-artificial-no-judiciario
- Síntese de requisitos (categorias de risco, IA generativa, Sinapses): https://juridico.ai/juridico/resolucao-cnj-615-2025-ia-no-judiciario/
