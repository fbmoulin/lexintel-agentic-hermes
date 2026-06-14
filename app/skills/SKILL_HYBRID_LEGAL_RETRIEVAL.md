---
name: hybrid-legal-retrieval
description: "Busca híbrida jurídica combinando recuperação semântica e lexical com reranking."
version: 1.0.0
metadata:
  hermes:
    tags: [rag, retrieval, hibrido]
    category: legal-br
---

# SKILL_HYBRID_LEGAL_RETRIEVAL

## Objetivo
Executar busca híbrida jurídica combinando recuperação semântica e lexical.

## Procedimento
1. Receber query.
2. Expandir consulta com sinônimos jurídicos.
3. Executar dense retrieval.
4. Executar sparse/BM25 retrieval.
5. Fundir resultados por RRF ou DBSF.
6. Aplicar filtros de metadados.
7. Reranquear candidatos.
8. Retornar fontes com score e justificativa.

## Filtros jurídicos
- tribunal
- ramo do direito
- classe
- data
- relator
- tema
- súmula
- tipo documental
