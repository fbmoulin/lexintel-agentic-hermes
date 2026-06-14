---
name: rag-evaluation
description: "Avalia qualidade de recuperação, fundamentação e resposta final (recall, MRR)."
version: 1.0.0
metadata:
  hermes:
    tags: [eval, rag, metricas]
    category: legal-br
---

# SKILL_RAG_EVALUATION

## Objetivo
Avaliar qualidade de recuperação, fundamentação e resposta final.

## Métricas
- Recall@5
- Recall@10
- MRR
- NDCG
- groundedness
- faithfulness
- citation_accuracy
- latency_ms
- cost_usd

## Procedimento
1. Executar dataset de perguntas.
2. Recuperar fontes.
3. Comparar fontes esperadas.
4. Gerar resposta.
5. Avaliar aderência ao contexto.
6. Registrar custo e latência.
7. Bloquear regressões no CI.
