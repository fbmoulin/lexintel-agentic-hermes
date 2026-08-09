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

> **Atualização v0.3 (PR #17):** com a flag ligada, o `QdrantVectorStore` deixou
> de ser stub — passa a indexar e buscar **com embeddings reais** (`fastembed`,
> modelo multilíngue local) sobre um Qdrant local, recuperando por significado.
> Ver `README.md` (seção "Recuperação real com Qdrant") e
> `docs/superpowers/specs/2026-06-14-qdrant-real-retrieval-design.md`. O chunking
> mockado descrito abaixo continua sendo a fonte dos `LegalChunk` indexados; só a
> camada de armazenamento/busca passou a ser real.

## Chunking Jurídico

O serviço `build_chunks` recebe `ExtractedText` e gera `LegalChunk` validado por Pydantic. A estratégia é escolhida por `get_chunker(text, doc_type)`: quando o texto tem ≥2 seções jurídicas detectáveis, o `StructuralChunker` emite **um chunk por seção** (relatório, fundamentação, dispositivo, ementa, voto, fatos, direito, preliminares, mérito, pedido); caso contrário, o `ParagraphChunker` (fallback) agrega/divide por orçamento de tokens com overlap de 1 sentença. Metadados de acórdão (órgão julgador, relator, número, tipo de recurso, data de publicação) são anexados a todos os chunks de um acórdão.

> A função `chunk_extracted_text` permanece como wrapper **deprecado** (emite `DeprecationWarning` e delega para `build_chunks`).

Entradas sem texto útil são ignoradas e páginas inválidas são normalizadas para `1`, evitando que OCR vazio ou metadados incompletos derrubem o pipeline mockado. O `chunk_id` recebe um ordinal condicional (só quando um grupo `(doc, página, unit_type)` gera mais de um chunk) e é único no conjunto, evitando colisão e perda silenciosa no `upsert`.

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

Mapeamento por tipo documental usado pelo fallback `ParagraphChunker` (sem marcadores); o `StructuralChunker` deriva o `unit_type` da própria seção detectada:

- `peticao_inicial` -> `pedido`
- `contestacao` -> `contestacao`
- `sentenca` -> `dispositivo`
- `acordao` -> `ementa`
- `unknown` -> `documento`

## IndexingAgent

O `IndexingAgent`:

- gera chunks jurídicos via `build_chunks` (structural/paragraph);
- indexa no `MockVectorStore` (ou no `QdrantVectorStore` quando a flag está ligada);
- retorna `IndexingSummary`;
- expõe `vector_backend`, `qdrant_enabled`, `chunk_count`, `indexed_count`, `chunk_unit_types` e `index_status` (`ok`/`upsert_failed`);
- mantém `external_use_allowed = false`.

Se nenhum chunk for gerado, o agente retorna `warning` e exige revisão humana. A indexação é **best-effort**: uma falha de `upsert` degrada para `warning` com revisão humana (`index_status = upsert_failed`), sem interromper o pipeline nem marcar a execução como `failed`.

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

## Limitações conhecidas / follow-ups

Descobertos durante a review da busca híbrida (`HybridRetrievalAgent`); resolvidos em `fix/review-2026-08-08`:

- ~~**BM25 usa frequências de termo binárias.**~~ **RESOLVIDO.** O `BM25Retriever` agora tokeniza com `_tokenize_seq` — a variante **preservadora de frequência** do tokenizer compartilhado (mesmas regras de accent-fold e comprimento mínimo; `_tokenize` continua sendo o `set` usado pelo overlap do Mock). `Counter(_tokenize_seq(text))` produz tf reais e o comprimento do documento volta a ser contagem de tokens, não de tokens únicos. Regressão: `test_term_frequency_influences_ranking` (doc que repete o termo deve superar doc que o menciona uma vez).
- ~~**`/rag/search` reconstrói o BM25 a cada requisição.**~~ **RESOLVIDO.** `build_default_hybrid_agent()` agora usa um cache do índice BM25 chaveado por (instância do store, `store.version`); todo `upsert` incrementa `version` e invalida o cache — a invalidação-por-`upsert` que este follow-up exigia (a garantia "a busca encontra chunks recém-indexados" segue coberta por `test_rag_search_finds_chunks_indexed_by_pipeline` e `test_factory_invalidates_bm25_cache_on_upsert`). Ressalva: `version` só enxerga escritas feitas **pela instância do processo** — escritas externas diretas no Qdrant não invalidam o cache (documentado no código); BM25 incremental permanece como evolução futura se esse cenário passar a existir.

## Fora do Escopo

Continuam fora desta fase:

- embeddings reais;
- RerankerService com cross-encoder (a fusão RRF do `HybridRetrievalAgent` já faz o rerank baseado em rank; o cross-encoder está adiado);
- Qdrant real;
- DataJud, STJ Dados Abertos, PJe ou LLMs.
