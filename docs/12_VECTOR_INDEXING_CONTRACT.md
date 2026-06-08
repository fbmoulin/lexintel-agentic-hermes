# Contrato de Indexação Vetorial Mockada

Este contrato descreve a Fase 6 do Lex Kratos Agentic Core v0.1.

A fase prepara a fronteira de indexação/RAG sem ativar Qdrant real, embeddings reais, LLMs ou qualquer serviço externo.

## Feature Flag

Qdrant real permanece desligado por padrão.

Variável:

```text
LEX_KRATOS_ENABLE_QDRANT=true
```

Sem essa variável, `get_qdrant_client()` falha com `RuntimeError` e o pipeline usa `MockVectorStore`.

Mesmo com a flag, a v0.1 não executa busca real em Qdrant; a integração real permanece tarefa futura explícita.

## Chunking Jurídico

O serviço `chunk_extracted_text` recebe `ExtractedText` e gera `LegalChunk` validado por Pydantic.

Entradas sem texto útil são ignoradas e páginas inválidas são normalizadas para `1`, evitando que OCR vazio ou metadados incompletos derrubem o pipeline mockado.

Cada chunk inclui:

- `chunk_id` determinístico
- `case_id`
- `doc_id`
- `unit_type`
- `text`
- `page_start`
- `page_end`
- `source`
- `metadata`

Mapeamento mockado:

- `peticao_inicial` -> `pedido`
- `contestacao` -> `contestacao`
- `sentenca` -> `dispositivo`
- `acordao` -> `ementa`
- `unknown` -> `documento`

## IndexingAgent

O `IndexingAgent`:

- gera chunks jurídicos;
- indexa no `MockVectorStore`;
- retorna `IndexingSummary`;
- expõe `vector_backend`, `qdrant_enabled`, `chunk_count`, `indexed_count` e `chunk_unit_types`;
- mantém `external_use_allowed = false`.

Se nenhum chunk for gerado, o agente retorna `warning` e exige revisão humana.

## MockVectorStore

O `MockVectorStore`:

- roda em memória;
- é reutilizado como singleton local entre indexação e busca;
- não exige container;
- usa overlap lexical simples;
- retorna `RetrievedContext`;
- mantém `retrieval_method = mock`.

O endpoint `/rag/search` usa esse store por padrão e retorna:

- `query`
- `top_k`
- `status`
- `suspicious_query`
- `requires_human_review`
- `warnings`
- `errors`
- `vector_backend`
- `qdrant_enabled`
- `results`

Queries suspeitas de prompt injection não executam busca e retornam `status = blocked`.

## Fora do Escopo

Continuam fora desta fase:

- embeddings reais;
- HybridRetrievalAgent;
- RerankerService;
- Qdrant real;
- DataJud, STJ Dados Abertos, PJe ou LLMs.
