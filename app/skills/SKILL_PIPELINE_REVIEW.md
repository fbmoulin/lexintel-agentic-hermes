---
name: pipeline-review
description: "Revisão holística da qualidade e consistência do pipeline jurídico completo."
version: 0.1.0
metadata:
  hermes:
    tags: [review, quality, consistency, pipeline]
    category: legal-br
    status: implemented
    phase: review
    requires_human_review: true
---

# SKILL_PIPELINE_REVIEW

## Objetivo

Realizar revisão holística da execução completa do pipeline de processamento jurídico, identificando inconsistências, calculando métricas de confiança e gerando recomendações acionáveis para revisão humana.

## Contexto

O ReviewAgent é executado após o ValidatorAgent como gate final de qualidade antes da revisão humana. Enquanto o ValidatorAgent foca em validações específicas (ex: precedentes inventados), o ReviewAgent avalia a qualidade e consistência geral de todo o pipeline.

## Entradas

- **case_id** (string): Identificador único do caso
- **trace** (list[dict]): Trace completo e ordenado de todas as execuções dos agentes
- **draft** (dict, opcional): Minuta gerada para verificação de consistência

## Saídas

Estrutura `AgentResult` contendo:

```json
{
  "case_id": "string",
  "agent_name": "ReviewAgent",
  "status": "success | warning",
  "output": {
    "review_status": "approved | conditional | rejected",
    "confidence_score": 0.0-1.0,
    "consistency_issues": [
      {
        "type": "string",
        "severity": "low | medium | critical",
        "description": "string",
        "agent": "string"
      }
    ],
    "recommendations": ["string"],
    "trace_coverage": {
      "agent_count": int,
      "completed_agents": ["string"],
      "blocked_agents": ["string"],
      "warning_agents": ["string"]
    },
    "review_version": "string",
    "requires_human_review": true,
    "external_use_allowed": false
  },
  "errors": ["string"],
  "warnings": ["string"],
  "requires_human_review": true,
  "external_use_allowed": false
}
```

## Lógica de Revisão

### 1. Cálculo de Confiança (Confidence Score)

Score de 0.0 a 1.0 baseado em:

- **Base**: 1.0
- **Penalidades**:
  - Agente bloqueado: score → 0.0 (imediato)
  - Status warning: -0.1 por agente
  - Cada warning individual: -0.05
  - Cada erro: -0.15

Exemplo:
```
1 agente warning + 2 warnings + 1 erro = 1.0 - 0.1 - 0.1 - 0.15 = 0.65
```

### 2. Verificação de Consistência

Detecta inconsistências lógicas entre agentes:

#### a) Falha de Indexação
- **Condição**: `IndexingAgent.status == "warning"` e `index_status == "upsert_failed"`
- **Severidade**: medium
- **Impacto**: Retrieval pode estar incompleto

#### b) Falha de Retrieval
- **Condição**: `HybridRetrievalAgent.status == "warning"` e `retrieval_status == "failed"`
- **Severidade**: medium
- **Impacto**: Contexto jurisprudencial ausente

#### c) FIRAC sem Contexto Completo
- **Condição**: `FIRACAgent.status == "success"` mas `HybridRetrievalAgent.status == "warning"` **e** `retrieval_status == "failed"`
- **Severidade**: low
- **Impacto**: Análise FIRAC pode ter contexto limitado (retrieval falhou completamente)

**Nota**: Esta verificação **não** dispara para warnings normais de índice degradado (upsert_failed, shortfall de precedentes), apenas quando o retrieval falha completamente. FIRAC deliberadamente não consome contexto recuperado (trace-only) conforme arquitetura aprovada em `docs/HANDOFF.md`.

### 3. Geração de Recomendações

Recomendações contextuais baseadas em:

- **Confiança < 0.5**: "Confiança muito baixa - revisão humana completa recomendada"
- **Confiança < 0.8**: "Confiança moderada - verificar warnings e erros reportados"
- **Issues críticas**: "Detectados N problemas críticos de consistência"
- **Agentes bloqueados**: "Pipeline bloqueado em: [lista de agentes]"
- **Agentes com warning**: "Warnings em: [lista de agentes] - revisar outputs"
- **Pipeline limpo**: "Pipeline executado com alta confiança - revisão de rotina recomendada"

### 4. Determinação de Status Final

```python
# ReviewAgent NUNCA bloqueia o pipeline - sempre retorna warning ou success
if blocked_count > 0 or confidence_score < 0.3:
    review_status = "rejected"
    status = "warning"  # Nunca "blocked" - review é informativo
elif warning_count > 0 or confidence_score < 0.8:
    review_status = "conditional"
    status = "warning"
else:
    review_status = "approved"
    status = "success"
```

**Nota importante**: O ReviewAgent nunca usa `status="blocked"` porque não interrompe o pipeline. Mesmo quando rejeita (review_status="rejected"), emite apenas `warning` para manter consistência com o contrato do trace onde "blocked" significa interrupção antecipada.

## Casos de Uso

### 1. Pipeline Limpo (Alta Confiança)
```
Entrada: Trace com todos status="success"
Saída: 
  - review_status: "approved"
  - confidence_score: 1.0
  - recommendations: ["Pipeline executado com alta confiança..."]
```

### 2. Warnings Isolados (Confiança Moderada)
```
Entrada: IndexingAgent com warning
Saída:
  - review_status: "conditional"
  - confidence_score: 0.85
  - consistency_issues: [{"type": "indexing_failure", ...}]
  - recommendations: ["Warnings em: IndexingAgent - revisar outputs"]
```

### 3. Bloqueio Crítico (Confiança Zero)
```
Entrada: SecurityAgent bloqueou por prompt injection
Saída:
  - review_status: "rejected"
  - confidence_score: 0.0
  - recommendations: ["Pipeline bloqueado em: SecurityAgent"]
  - status: "warning"  # Review nunca bloqueia
```

### 4. Inconsistência Detectada
```
Entrada: Retrieval falhou mas FIRAC executou
Saída:
  - review_status: "conditional"
  - consistency_issues: [
      {"type": "retrieval_failure", "severity": "medium"},
      {"type": "firac_without_complete_context", "severity": "low"}
    ]
  - recommendations: ["Verificar warnings...", "FIRAC gerado mas retrieval teve problemas"]
```

## Invariantes e Garantias

1. **Revisão Humana Obrigatória**: `requires_human_review` sempre `True`
2. **Uso Externo Proibido**: `external_use_allowed` sempre `False`
3. **Score Determinístico**: Mesma trace → mesmo confidence_score
4. **Trace Vazio**: Sempre resulta em `warning` (não blocked) com confidence 0.0 e review_status "rejected"
5. **Nunca Bloqueia Pipeline**: ReviewAgent sempre retorna `success` ou `warning`, nunca `blocked`

## Limitações Conhecidas

1. **Mock-First**: Não faz análise semântica profunda do conteúdo jurídico (apenas estrutural)
2. **Regras Fixas**: Penalidades e thresholds são fixos, não adaptativos
3. **Sem LLM**: Não utiliza modelos de linguagem para análise contextual
4. **Trace-Only**: Revisão baseada apenas no trace; não acessa documentos originais
5. **Sem Persistência**: Não mantém histórico de revisões anteriores do mesmo caso

## Integração no Pipeline

Posição: **Passo 10** (após ValidatorAgent)

```python
# Orquestrador (run_full_mock)
validator_result = self.validator_agent.run(case.case_id, mock_draft)
self._record_trace(trace, validator_result, 9, "validation")

review_result = self.review_agent.run(case.case_id, trace, mock_draft)
self._record_trace(trace, review_result, 10, "review")

# Review não bloqueia pipeline (sempre continua)
```

## Evolução Futura

### v0.2 (Planejado)
- Análise semântica de consistência entre FIRAC e draft
- Detecção de contradições lógicas no raciocínio jurídico
- Métricas de qualidade específicas por tipo de processo

### v1.0 (Planejado)
- Integração com LLM para análise contextual profunda
- Sistema de pesos adaptativos baseado em feedback histórico
- Suporte a diferentes perfis de revisão (strict, balanced, permissive)

## Requisitos de Conformidade

- **CNJ Res. 332/2020** (Art. 8º): Revisão humana obrigatória preservada
- **CNJ Res. 615/2025**: Saída não autorizada para uso externo sem revisão
- **LGPD**: Não processa dados pessoais diretamente (apenas metadados de trace)

## Testes de Aceite

Cobertura em `tests/test_review_agent.py`:

1. ✅ `test_review_agent_rejects_empty_trace` - Trace vazio → warning + rejected
2. ✅ `test_review_agent_approves_clean_trace` - Pipeline limpo → approved
3. ✅ `test_review_agent_warns_on_warnings` - Warnings → conditional
4. ✅ `test_review_agent_blocks_on_blocked_trace` - Bloqueio → rejected
5. ✅ `test_review_agent_detects_firac_without_retrieval` - Inconsistência detectada
6. ✅ `test_review_agent_calculates_confidence_score` - Scores corretos
7. ✅ `test_review_agent_provides_recommendations` - Recomendações geradas
8. ✅ `test_review_agent_trace_coverage` - Estatísticas precisas
9. ✅ `test_review_agent_always_requires_human_review` - Invariantes preservados

## Referências

- `docs/08_TRACE_CONTRACT.md` - Contrato do trace
- `docs/COMPLIANCE_CNJ_615.md` - Requisitos de conformidade
- `app/agents/validator_agent.py` - Validação específica de precedentes
- `app/agents/security_agent.py` - Validação de segurança
