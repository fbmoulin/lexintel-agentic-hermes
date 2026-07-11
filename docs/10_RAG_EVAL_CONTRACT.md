# Contrato da Avaliação RAG Mockada

Este contrato descreve a avaliação local em `python -m app.evals.run_eval`.

A avaliação permanece mockada, determinística e sem acesso a Qdrant, LLMs, STJ Dados Abertos, DataJud ou qualquer serviço externo.

## Recuperador avaliado (importante)

O recuperador de referência avaliado agora é o **HÍBRIDO** (`build_hybrid_eval_store`: RRF de BM25 + Mock token-overlap sobre o corpus dourado), não mais o Mock diretamente. Isso alinha a avaliação ao mesmo recuperador que serve `/rag/search`.

**O híbrido offline é um ENSEMBLE DE DOIS SINAIS LÉXICOS** (BM25 + sobreposição de tokens sobre o **mesmo** `_tokenize`), **não** um híbrido denso+esparso real. O lado denso (Qdrant) só participa quando `QDRANT_ENABLED=1`; na avaliação local (default) o Qdrant nunca é acionado, então ambos os rankers são léxicos e determinísticos.

A avaliação usa uma **instância separada** semeada com o corpus dourado (a avaliação precisa de ground truth conhecido, então não reutiliza o `DEFAULT_MOCK_CHUNKS` do singleton da API). `evaluate_item` chama `store.search(query)` (agora a busca híbrida com fusão RRF) e mapeia cada chunk recuperado para seu `source_ref`. Uma regressão na lógica de recuperação (tokenizer, scoring, ranking, fusão) reduz as métricas e reprova o gate; uma regressão apenas na fiação/seed do singleton da API é coberta pelos testes da API, não pela avaliação. A função `_smoke_retrieve` (mapa de keywords) permanece apenas como teste de fumaça rotulado; **não** mede qualidade de recuperação.

O dicionário de resultado inclui o campo `retriever` (`"hybrid"`), identificando o recuperador de referência avaliado.

## Corpus

Arquivo: `app/evals/golden_corpus.jsonl` — chunks semeados no store. Contém chunks "gold" (um por fonte canônica) **e chunks distratores** de outras áreas (trabalhista, penal, tributário, ambiental, família, locação, administrativo). Os distratores são obrigatórios: sem eles a recuperação por sobreposição de tokens acerta trivialmente e o gate não consegue reprovar por qualidade.

## Dataset

Arquivo: `app/evals/golden_dataset.jsonl`

Campos obrigatórios por linha:

- `id`: identificador único do caso.
- `query`: pergunta jurídica simulada.
- `expected_sources`: lista não vazia de fontes esperadas.
- `area`: área jurídica usada para agrupamento.

Áreas obrigatórias:

- `bancario`
- `consumidor`
- `processual_civil`
- `saude`

O loader falha com `ValueError` quando encontra JSON inválido, linha que não seja objeto, campo ausente, `id`, `query` ou `area` não textual, `expected_sources` vazio ou ID duplicado.

## Métricas

O resultado mantém `average_recall` por compatibilidade e adiciona:

- `average_recall_at_1`
- `average_recall_at_3`
- `average_mrr`
- `area_summary`
- `thresholds`
- `passed`
- `threshold_failures`

Cada item em `results` inclui:

- `matched_expected`
- `missed_expected`
- `matched_expected_at_3`
- `missed_expected_at_3`
- `recall`
- `recall_at_1`
- `recall_at_3`
- `mrr`

## Limiar de Aceite

O limiar local atual é:

- `dataset_size >= 24` (mínimo 6 casos por área obrigatória)
- áreas obrigatórias presentes
- `average_recall_at_3 >= 0.85`
- `min_average_recall_at_1 >= 0.9375`
- `min_average_mrr >= 1.0`
- `min_per_area_recall_at_3 >= 0.85` (nenhuma área forte pode mascarar uma quebrada)

Os limiares de não-regressão `min_average_recall_at_1 = 0.9375` e `min_average_mrr = 1.0` são ancorados no baseline dourado do Mock — o recuperador híbrido de referência **iguala esse baseline exatamente**: recall@1 = 0.9375, recall@3 = 1.0, MRR = 1.0. Qualquer degradação da fusão RRF ou dos rankers derruba a métrica abaixo do piso e reprova o gate.

O campo `passed` só retorna `true` quando todos os limiares são atendidos.

Quando executado via CLI, `python -m app.evals.run_eval` encerra com código diferente de zero se `passed` for `false`.
