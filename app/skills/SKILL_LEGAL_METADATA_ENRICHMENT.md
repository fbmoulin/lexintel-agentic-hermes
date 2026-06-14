---
name: legal-metadata-enrichment
description: "Enriquece documentos e chunks com metadados jurídicos (tribunal, classe, assunto)."
version: 1.0.0
metadata:
  hermes:
    tags: [metadados, enriquecimento]
    category: legal-br
---

# SKILL_LEGAL_METADATA_ENRICHMENT

## Objetivo
Enriquecer documentos e chunks com metadados jurídicos.

## Campos mínimos
- tribunal
- classe
- assunto
- relator
- órgão julgador
- data de julgamento
- data de publicação
- ramo do direito
- tipo documental
- tese jurídica
- resultado

## Regra
Quando o dado não estiver expressamente disponível, retornar null.
