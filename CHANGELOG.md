# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

### Adicionado

- **Chunking estrutural jurídico** (`app/services/chunking.py`, `app/services/markers.py`).
  `detect_sections()` reconhece seções por tipo documental (sentença, acórdão,
  petição inicial, contestação) e `StructuralChunker` emite um chunk por seção;
  `ParagraphChunker` (fallback) agrega/divide por orçamento de tokens com overlap
  de 1 sentença; `get_chunker()` escolhe a estratégia. Metadados de acórdão
  (órgão julgador, relator, número, tipo de recurso, data de publicação) são
  anexados a todos os chunks. Quatro novos `ChunkUnitType`: `fatos`, `direito`,
  `preliminares`, `merito` (não acentuados, house style).
- **Interface de extração** (`app/services/extraction.py`): protocolo `Extractor`,
  modelo Pydantic `ExtractedDocument` e `MockExtractor` com templates
  marker-rich por `doc_type` — o `ExtractionAgent` passa a consumir esse texto.

### Alterado

- `IndexingAgent` usa `build_chunks()` (structural/paragraph) no lugar do antigo
  um-chunk-por-documento. `chunk_extracted_text()` mantida como wrapper
  **deprecado** (emite `DeprecationWarning`, delega para `build_chunks()`).
- `build_chunk_id()` ganha um ordinal **condicional** (só quando um grupo
  `(doc, página, unit_type)` gera mais de um chunk), evitando colisão de id e
  perda silenciosa de chunk no `upsert`.

## [0.3.0] — 2026-06-14

Recuperação semântica real opcional (PR #17, merge `6d06566`). 71 → **77 testes**
(+2 de integração pulados por padrão). Base: spec/plan em `docs/superpowers/`.

### Adicionado

- **Recuperação real com Qdrant (MVP), atrás de `LEX_KRATOS_ENABLE_QDRANT`.**
  `QdrantVectorStore` deixou de ser stub: indexa e busca com embeddings reais
  (modelo multilíngue local `paraphrase-multilingual-MiniLM-L12-v2`, 384 dim, via
  `fastembed`), recuperando por significado e não por sobreposição de tokens.
  Coleção criada com a dimensão lida do próprio modelo (sem drift); ids `uuid5`
  determinísticos (reindexação idempotente); payload carrega o chunk completo e a
  busca emite o mesmo formato `RetrievedContext` do mock (carimba
  `retrieval_method=qdrant`), então `rag.py` não muda. Roda na porta **6533**
  (flag desligada por padrão).
- Testes unitários offline (cliente/embedder fake, sem rede) + teste de
  integração ponta-a-ponta em `tests/integration/` pulado por padrão.
- `fastembed==0.7.4` em `requirements-qdrant.txt`; `docker-compose.yml` com porta
  de host parametrizável (`QDRANT_HOST_PORT`, default 6533).

### Inalterado

- `MockVectorStore`, `run_eval` (continua mock-only) e o comportamento com a flag
  desligada. Escopo MVP: recuperação real alcançável via `/rag/search`, sem
  religar a avaliação.

## [0.2.0] — 2026-06-14

Otimização pós-revisão (PRs #13 Strand A + #15 Strand B). 53 → **71 testes**.
Base: revisão em `docs/audits/2026-06-13-deep-review.md`; spec/plan em
`docs/superpowers/`.

### Strand A — corretude interna e gate honesto

- **Avaliação RAG religada ao recuperador servido.** `run_eval` agora pontua o
  mesmo `MockVectorStore` (classe + scoring) que `/rag/search` usa, semeado com
  `golden_corpus.jsonl` que inclui **chunks distratores**. Antes, pontuava um
  stub de keywords (`fake_retrieve`, hoje `_smoke_retrieve`, só fumaça) e o gate
  não podia reprovar por qualidade. Dataset 8 → **24 casos** (6 por área);
  teste de discriminação (mis-seed reduz recall). `_tokenize` agora dobra acentos.
- **`blocked` para o pipeline.** Qualquer etapa `blocked` interrompe as fases
  jurídicas seguintes (antes só o gate de segurança), conforme `08_TRACE_CONTRACT`.
- **Validator vivo.** A saída do FIRAC é roteada para o `ValidatorAgent`; o
  caminho de bloqueio (precedente inventado) é alcançável e testado; `failed`
  coberto.
- **Contrato único.** Schemas JSON gerados dos modelos Pydantic
  (`scripts/gen_schemas.py`) + gate de drift na CI + teste de validação de
  payload real. `agent_run.schema.json` mantido como **future-spec**.
- **CI endurecida.** `ruff` + `mypy` + drift de schema antes dos testes.
- **`qdrant-client` opcional** (import lazy; `requirements-qdrant.txt`).
- Higiene: remoção de código morto, fim do vazamento de `str(exc)` ao cliente,
  imagem Qdrant pinada, isolamento de teste via fixture autouse.

### Strand B — integração com o Hermes Agent

- **Plugin `lex_kratos`** (`integrations/hermes/lex_kratos/`) expõe o pipeline
  como ferramentas do Hermes (`lex_intake`, `lex_run_pipeline`) via **HTTP**
  (Hermes Py3.11 ↔ lexintel Py3.12, processos separados), handlers stdlib-only.
- **Frontmatter Hermes/agentskills.io** nas 12 `app/skills/SKILL_*.md`.
- **`docs/COMPLIANCE_CNJ_615.md`** — mapa CNJ 615/2025 + LGPD verificado contra a
  resolução (categorias de risco: FIRAC/minuta/precedente = **alto risco**;
  registro Sinapses; regras de IA generativa), com lacunas declaradas.
- Repo posicionado como **implementação** da skill `ai-legal-development`.

### Notas

- Decisões do operador: `agent_run.schema.json` mantido como future-spec; plugin
  via HTTP (não import direto).
- 13 achados de bots de revisão nas 3 rodadas; 12 corrigidos, 1 informativo.
