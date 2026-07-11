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

Descobertos durante a review da busca híbrida (`HybridRetrievalAgent`); pendentes de fase futura:

- **BM25 usa frequências de termo binárias.** Como o `_tokenize` compartilhado retorna um **conjunto**, `Counter(_tokenize(text))` produz tf ∈ {0,1} — a saturação de TF do BM25 opera sobre **presença** do termo, não sobre frequência bruta. Aceitável para os chunks jurídicos curtos (1-2 frases) do corpus mockado; revisitar se o índice passar a cobrir documentos longos (exigiria um tokenizer preservador de frequência apenas para o BM25).
- **`/rag/search` reconstrói o BM25 a cada requisição.** `build_default_hybrid_agent()` tira um snapshot do corpus e reconstrói o índice BM25 em toda requisição. Trivial para o store mockado; no caminho Qdrant, faz `scroll` da coleção inteira por query. Um cache ingênuo é **inseguro**: serviria um índice BM25 defasado após um `upsert` (quebrando a garantia "a busca encontra chunks recém-indexados"). Um cache correto precisa de invalidação por `upsert` ou BM25 incremental. **Deve ser resolvido antes de o caminho Qdrant servir tráfego de produção.**

## Fora do Escopo

Continuam fora desta fase:

- embeddings reais;
- RerankerService com cross-encoder (a fusão RRF do `HybridRetrievalAgent` já faz o rerank baseado em rank; o cross-encoder está adiado);
- Qdrant real;
- DataJud, STJ Dados Abertos, PJe ou LLMs.
