# Spec — HybridRetrievalAgent (P6): busca híbrida jurídica, mock-first

- **Data:** 2026-07-10
- **Fase:** P6 — RAG real preparado, mas desligado por padrão
- **Backlog fechado por este spec:** `HybridRetrievalAgent`, `RerankerService` (parcial — rerank leve por fusão; cross-encoder fica fora), `Métricas retrieval` (via `run_eval` medindo o híbrido)
- **Slot pré-existente:** `AGENT_REGISTRY` já registra `HybridRetrievalAgent` como `status="planned"`, `phase="retrieval"`, `skill_name="SKILL_HYBRID_LEGAL_RETRIEVAL.md"` (skill já escrita).

## 1. Objetivo e filosofia

Completar a fase P6 entregando **busca híbrida real** — fusão Reciprocal Rank Fusion (RRF) de um sinal esparso (BM25) e um sinal denso/léxico — mantendo a doutrina do projeto:

- **Offline e determinístico por padrão.** Nenhum serviço externo, LLM ou download de modelo no caminho default.
- **Auditável.** Cada resultado carrega de quais rankers veio (rastro para CNJ 615/2025).
- **Qdrant permanece opt-in** por feature flag (`is_qdrant_enabled()`), como na v0.4.

Fora de escopo nesta fase: reranking por cross-encoder (modelo pesado, não-determinístico), expansão de query por sinônimos jurídicos via LLM, jurisprudência real (P7), integrações externas (P8).

## 2. Rótulo honesto do "híbrido" offline

No modo default (Qdrant desligado), os dois sinais fundidos são:

1. **BM25** (novo, esparso) — Okapi BM25 sobre o texto dos chunks.
2. **Token-overlap** do `MockVectorStore` (existente, léxico).

**Ambos são léxicos sobre o mesmo tokenizer** (`_tokenize`, com accent-fold). Portanto o modo offline é um **ensemble de dois sinais léxicos**, *não* um híbrido dense+sparse verdadeiro. A fusão dense+sparse real só ocorre quando `QDRANT_ENABLED=1`, quando o lado denso (`QdrantVectorStore`) substitui o token-overlap:

```
OFFLINE (default):   RRF( BM25 , Mock.token_overlap )
QDRANT ON:           RRF( QdrantVectorStore.dense , BM25 )
```

O valor do ensemble offline é real e limitado: (a) exercita o código de fusão no CI padrão (sem depender dos 2 testes Qdrant, que ficam `skipped`); (b) BM25 introduz saturação de TF e raridade de termo (IDF) que o overlap puro não captura. O spec declara isto explicitamente para que um leitor futuro não confunda o modo offline com recuperação densa.

## 3. Componentes e interfaces

Três unidades novas, cada uma com um propósito e testável isoladamente:

### 3.1 `app/services/bm25.py` → `BM25Retriever`

- Índice Okapi BM25 (`k1=1.5`, `b=0.75`) construído a partir de uma lista de `LegalChunk` (mesmo dict shape dos outros stores).
- Reusa `_tokenize` de `vector_store.py` (accent-fold já existente) — **um único tokenizer** em todo o retrieval, evitando drift.
- `search(query, top_k, filters) -> list[dict]` emite o **mesmo `RetrievedContext`** que Mock/Qdrant (`retrieval_method="bm25"`). Determinístico; desempate por `chunk_id`.
- Puro Python, sem dependência nova. Injetável nos testes.
- `backend_name = "bm25"`.

### 3.2 `app/services/fusion.py` → `reciprocal_rank_fusion`

- Função **pura**: `reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]`.
- Score fundido por chunk = `Σ 1/(k + rank)` sobre cada ranking em que o chunk aparece (rank 1-indexado).
- Determinística; desempate por `chunk_id` (espelha o tie-break do `MockVectorStore`).
- Preserva, para cada chunk fundido, `fusion_detail`: lista de `{ranker, rank, score}` de origem — o rastro auditável.
- `k=60` é o default canônico de RRF; parametrizável para o spike de tuning (§7).

### 3.3 `app/agents/retrieval_agent.py` → `HybridRetrievalAgent`

- Implementa o slot `planned` do registry. Contrato `.run(...) -> AgentResult` como os demais agentes.
- Injeção de retrievers (mirror de `IndexingAgent(vector_store=...)`): recebe os retrievers ativos; se não injetados, monta a configuração default conforme a flag Qdrant (§2).
- Fluxo: consulta cada retriever ativo → aplica **filtro de alvo** (§4) e filtros de metadados da skill → funde por RRF → devolve `RetrievedContext[]` com `retrieval_method="hybrid"` + `metadata.fusion_detail`.
- Respeita o **guard de completude do índice** (§5).
- `metadata` de saída inclui `fusion_detail` e `rankers_used` (para auditoria e depuração).

Reusa o registry existente: ao implementar, mudar a entrada de `HybridRetrievalAgent` para `status="implemented"`, `module_path/class_name` preenchidos; `validate_agent_registry()` passa a exigir a classe importável.

## 4. Alvo da recuperação (decisão aprovada)

O `IndexingAgent` faz upsert dos chunks **do próprio caso** no mesmo store singleton semeado com precedentes mock (`DEFAULT_MOCK_CHUNKS`). Recuperar cegamente traria o texto do próprio caso de volta, misturado com os precedentes — ruído para um RAG cujo objetivo é *surfacear precedentes*.

**Decisão:** o `HybridRetrievalAgent`, no passo de pipeline, **filtra os chunks do próprio caso** (`chunk.case_id != caso_atual`), retornando apenas precedentes/seed. É um filtro pequeno, explícito e auditável.

- No endpoint `/rag/search` (sem "caso atual"), não há filtro por `case_id` — busca todo o corpus indexado, como hoje.
- No `run_eval` (corpus dourado semeado, sem chunks de caso), o filtro é no-op.

## 5. Guard de completude do índice

Respeita o aviso já cravado em `registry.py` e `indexing_agent.py`: uma run com `index_status="upsert_failed"` **completou sem indexar seus chunks**. O `HybridRetrievalAgent`, no pipeline, recebe o resultado do passo de indexing; se `index_status != "ok"`:

- Não assume que o índice contém os chunks do caso.
- Emite `status="warning"`, `requires_human_review=True`, com warning explícito.
- **Não halta** o pipeline (retrieval é best-effort, como indexing).
- Ainda retorna precedentes recuperáveis (seed/corpus), apenas sinaliza incompletude.

## 6. Integração (retriever-de-registro único)

Fonte única de verdade — o híbrido é o único caminho de retrieval, sem drift entre pipeline, endpoint e eval.

### 6.1 Orquestrador (`app/agents/orchestrator.py`)

Novo passo `retrieval` entre `indexing` (step 6) e `firac` (step 7):

- `query = user_goal + texto normalizado` (concatenação determinística).
- Grava `retrieved_context[]` no `output` do passo e no `trace` (auditável).
- **FIRAC permanece inalterado** — não recebe o contexto nesta fase (decisão aprovada; fiação retrieval→FIRAC vira item futuro quando FIRAC deixar de ser mock).
- Segue o padrão de `_record_trace` / `_blocked_response`; retrieval não halta (best-effort), então nunca produz `blocked`.
- `TRACE_VERSION` / `FULL_MOCK_PIPELINE` sobem de `v0.2` para `v0.3` (o trace ganha um passo — mudança de contrato de trace; atualizar `docs/08_TRACE_CONTRACT.md` e testes que fixam a contagem/ordem de agentes).

### 6.2 Endpoint (`app/api/rag.py`)

- `/rag/search` passa a usar `HybridRetrievalAgent` em vez de `get_vector_store().search(...)` direto.
- **Shape de resposta inalterado** (mesmos campos; `retrieval_method` agora `"hybrid"`). O guard de segurança (`SecurityAgent` block/warning) e o try/except client-safe permanecem.

### 6.3 Eval (`app/evals/run_eval.py`)

- `evaluate_item` passa a pontuar o `HybridRetrievalAgent` (mesma configuração offline: BM25 + token-overlap), não o `MockVectorStore` direto.
- Mantém instância separada semeada com o corpus dourado (ground truth conhecido).
- Atualiza `docs/10_RAG_EVAL_CONTRACT.md` para descrever o recuperador avaliado como o híbrido.

## 7. Gate empírico — "híbrido ≥ baseline do Mock" (correção bloqueante)

Os thresholds atuais (`recall@3 ≥ 0.85`, `MRR ≥ 0.85`) estão **bem abaixo** do baseline medido do Mock (`recall@3=1.0`, `recall@1=0.9375`, `MRR=1.0`). Um híbrido *pior* que o Mock passaria no gate — regressão de qualidade disfarçada de feature. Portanto:

- **Primeiro passo do TDD é um spike de medição.** Construir `BM25Retriever` + `reciprocal_rank_fusion` e medir a configuração offline (BM25 + token-overlap) contra o `golden_dataset.jsonl` **antes** de fiar orquestrador/endpoint.
- **Critério de aceite não é "passa 0.85"**, é **híbrido ≥ baseline atual do Mock**:
  - `recall@1 ≥ 0.9375`
  - `recall@3 = 1.0`
  - `average_mrr = 1.0`
- Se o spike **não clarear**: PARAR e replanejar (tunar `k` do RRF; ou pesos por ranker; ou dense-only-quando-Qdrant; ou voltar ao modo aditivo do fork). Descobrir agora, antes de construir a fiação.
- Se clarear: prosseguir. Adicionar ao contrato de eval um threshold de **não-regressão** ancorado no baseline do Mock (ex.: `min_average_recall_at_1`, `min_average_mrr` fixados no baseline), para que futuras mudanças de fusão não regridam silenciosamente.

## 8. Testes e rollout (TDD)

Suíte sobe de **123 verdes** (2 Qdrant skipped mantidos). Cobertura nova:

- **`tests/test_bm25_retriever.py`** — ranking BM25, accent-fold, saturação TF/IDF, filtros, tie-break determinístico, `RetrievedContext` shape.
- **`tests/test_fusion.py`** — RRF determinístico, `fusion_detail` correto, desempate por `chunk_id`, comportamento com 1 vs N rankings, chunk presente em só um ranking.
- **`tests/test_hybrid_retrieval_agent.py`** — fusão offline (BM25+overlap), fusão com Qdrant injetado (fake), filtro de alvo (`case_id` do caso excluído), guard `upsert_failed`, filtros de metadados da skill, `AgentResult` shape.
- **`tests/test_rag_api.py`** (existente) — atualizar para `retrieval_method="hybrid"`, shape inalterado.
- **`tests/` orquestrador** — novo passo `retrieval` no trace, ordem/contagem de agentes (`trace-v0.3`), FIRAC inalterado.
- **`tests/test_eval_*`** — eval pontua o híbrido; gate de não-regressão no baseline do Mock.
- **Registry** — `HybridRetrievalAgent` passa a `implemented`; `validate_agent_registry()` verde.

Rollout em ordem: spike de medição → BM25 + fusão (unit) → HybridRetrievalAgent (unit) → wiring endpoint → wiring orquestrador + trace-v0.3 → eval + gate de não-regressão → docs (08, 10, README, backlog, registry). Commit por checkpoint verde.

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Fusão RRF reordena e piora MRR vs Mock puro | Gate empírico §7 é o **primeiro** passo; para-e-replaneja se não clarear |
| Dois caminhos de retrieval divergem | Retriever-de-registro único (§6): pipeline, endpoint e eval usam a mesma classe |
| Retrieval traz o próprio caso de volta como ruído | Filtro de alvo por `case_id` (§4) |
| Run indexou parcialmente e retrieval finge completude | Guard `upsert_failed` (§5) |
| Mudança de trace quebra testes de contagem/ordem | `trace-v0.3` explícito + atualização de `08_TRACE_CONTRACT.md` e testes |
| Threshold baixo mascara regressão futura | Gate de não-regressão ancorado no baseline do Mock (§7) |

## 10. Definição de pronto

- Suíte verde (≥ 123 + novos testes; 2 Qdrant skipped).
- Eval passa com gate de não-regressão ancorado no baseline do Mock.
- `validate_agent_registry()` verde com `HybridRetrievalAgent` implementado.
- `/rag/search` shape inalterado; `retrieval_method="hybrid"`.
- Docs sincronizados: `08_TRACE_CONTRACT.md` (trace-v0.3), `10_RAG_EVAL_CONTRACT.md` (recuperador = híbrido), `README.md`, `04_BACKLOG.md` (P6 fechado), `registry.py`.
- Filosofia preservada: default offline, determinístico, sem serviço externo; Qdrant opt-in.
