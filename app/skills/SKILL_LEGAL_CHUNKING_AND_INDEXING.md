# SKILL_LEGAL_CHUNKING_AND_INDEXING

## Objetivo
Dividir documentos jurídicos por unidade lógica e indexar em base vetorial.

## Estratégia
Priorizar unidade jurídica em vez de quantidade fixa de caracteres.

## Tipos de unidade
- ementa
- relatório
- voto
- fundamentos
- dispositivo
- pedido
- contestação
- prova
- tese
- precedente citado

## Regras
1. Não quebrar tese jurídica no meio.
2. Não separar fundamento de sua conclusão.
3. Manter referência de página.
4. Manter doc_id e case_id.
5. Gerar chunk_id determinístico.
