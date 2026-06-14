---
name: document-intake
description: "Classifica documentos jurídicos recebidos e monta o pacote inicial do caso (intake)."
version: 1.0.0
metadata:
  hermes:
    tags: [intake, classificacao, documentos]
    category: legal-br
---

# SKILL_DOCUMENT_INTAKE

## Objetivo
Classificar documentos jurídicos recebidos e montar pacote inicial do caso.

## Entrada
- case_id
- source_type
- files
- user_goal

## Procedimento
1. Identificar tipo de documento.
2. Separar documentos processuais, probatórios e jurisprudenciais.
3. Detectar duplicidade.
4. Atribuir confidence score.
5. Encaminhar para extração.

## Proibições
- Não interpretar mérito.
- Não redigir minuta.
- Não presumir tipo documental sem base textual.
