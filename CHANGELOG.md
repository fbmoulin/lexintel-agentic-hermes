# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não lançado]

## [0.5.0] — 2026-07-11

Busca híbrida jurídica (P6, PR #22). 123 → **150 testes**. Base:
`docs/superpowers/specs/2026-07-10-hybrid-retrieval-design.md`,
`docs/superpowers/plans/2026-07-10-hybrid-retrieval.md`, `docs/10_RAG_EVAL_CONTRACT.md`.

### Adicionado

- **Busca híbrida** (`app/services/bm25.py`, `app/services/fusion.py`,
  `app/agents/retrieval_agent.py`): `BM25Retriever` (Okapi, esparso, puro Python,
  reutiliza `_tokenize`), `reciprocal_rank_fusion` (RRF, com `fusion_detail` de
  auditoria) e `HybridRetrievalAgent` (`search()` + `run()` + factory
  `build_default_hybrid_agent()`). Offline funde BM25 + token-overlap do Mock
  (ensemble de dois sinais léxicos); o lado denso (Qdrant) participa apenas com
  `QDRANT_ENABLED`.
- **Passo `retrieval` no pipeline** (`trace-v0.3`), entre indexação e FIRAC,
  best-effort (nunca bloqueia; falha degrada a `warning`), grava
  `retrieved_context[]` + `precedent_count`/`requested_top_k`/`own_case_excluded_count`.
  FIRAC ainda não recebe o contexto (adiado).
- **Gate empírico de não-regressão** (`tests/test_hybrid_eval_gate.py`): o híbrido
  deve igualar ou superar o baseline do Mock (recall@1≥0.9375, MRR≥1.0), não o
  piso frouxo de 0.85. `run_eval` passa a pontuar o híbrido
  (`build_hybrid_eval_store`) e reporta `retriever`.

### Alterado

- `/rag/search` passa a ser servido pelo `HybridRetrievalAgent` (shape de resposta
  inalterado; `retrieval_method="hybrid"`).
- Registro do agente `HybridRetrievalAgent` de `planned` para `implemented`.
- Thresholds de avaliação: `min_average_recall_at_1=0.9375`, `min_average_mrr` de
  0.85 para 1.0 (não-regressão ancorada no baseline do Mock).

### Limitações conhecidas (follow-ups)

- BM25 usa TF binário (o `_tokenize` compartilhado retorna `set`); adequado a
  chunks curtos, revisar para documentos longos.
- `/rag/search` reconstrói o índice BM25 por requisição; no caminho Qdrant um
  cache exige invalidação-no-upsert antes de servir produção.

## [0.4.0] — 2026-07-10

Ciclo de revisão + premortem + chunking estrutural (PRs #18–#21). 77 → **123 testes**.
Base: `docs/audits/2026-07-09-full-review.md`, `.premortems/PREMORTEM-2026-07-10*` e
`docs/superpowers/plans/2026-07-10-richer-chunking.md`.

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
- **Piso de recall@3 por área na avaliação** (`min_per_area_recall_at_3=0.85`,
  M3): uma área forte não pode mais mascarar uma área quebrada na média global.
- **Tag `index_status`** (`ok`/`upsert_failed`) no `IndexingAgent` (F1): uma
  falha sistêmica de indexação fica separável de warnings de conteúdo.

### Alterado

- `IndexingAgent` usa `build_chunks()` (structural/paragraph) no lugar do antigo
  um-chunk-por-documento. `chunk_extracted_text()` mantida como wrapper
  **deprecado** (emite `DeprecationWarning`, delega para `build_chunks()`).
- `build_chunk_id()` ganha um ordinal **condicional** (só quando um grupo
  `(doc, página, unit_type)` gera mais de um chunk) + unicidade global entre
  itens, evitando colisão de id e perda silenciosa de chunk no `upsert` (R1).
- **Indexação best-effort** (M1): falha de `upsert` degrada para `warning` com
  revisão humana (não `failed`), sem interromper o pipeline.
- `CaseInput` limita a superfície de entrada (M4): `case_id` 1–128, `files`
  ≤200 itens × ≤2048 chars → HTTP 422 na borda.
- Vocabulário de status alinhado ao fluxo (F4): `"failed"` removido de
  `AgentResult.status` (terminal = `blocked`, degradação = `warning`).

### Corrigido / Segurança

- Gate de avaliação por área lê o limiar fail-loud, não fail-open (F3).
- Plugin Hermes rejeita `case_id` vazio localmente em vez de enviar `""` (F2).
- Precisão de docs: paridade eval↔API reescrita (mesma classe, instância
  separada), chaves `.env.example` marcadas como placeholders, comandos de lint
  incluem `integrations` (L1–L3).

> Revisão completa em `docs/audits/2026-07-09-full-review.md`: nenhum achado
> CRITICAL/HIGH; defesa contra path traversal confirmada. M2 retirado como
> falso-positivo. Premortem (`premortem-code`, veredito REFINE): F1/F3/F4
> corrigidos, F2 corrigido; itens não-bloqueantes rastreados.

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
