# Contrato da Avaliação RAG Mockada

Este contrato descreve a avaliação local em `python -m app.evals.run_eval`.

A avaliação permanece mockada, determinística e sem acesso a Qdrant, LLMs, STJ Dados Abertos, DataJud ou qualquer serviço externo.

## Recuperador avaliado (importante)

A avaliação pontua a **mesma classe/código de recuperação que o endpoint `/rag/search` usa** (`MockVectorStore` — mesmo `_tokenize` e scoring) — não um stub. Usa uma **instância separada** semeada com o corpus dourado (a avaliação precisa de ground truth conhecido, então não reutiliza o `DEFAULT_MOCK_CHUNKS` do singleton da API). `evaluate_item` chama `store.search(query)` e mapeia cada chunk recuperado para seu `source_ref`. Uma regressão na lógica de recuperação (tokenizer, scoring, ranking) reduz as métricas e reprova o gate; uma regressão apenas na fiação/seed do singleton da API é coberta pelos testes da API, não pela avaliação. A função `_smoke_retrieve` (mapa de keywords) permanece apenas como teste de fumaça rotulado; **não** mede qualidade de recuperação.

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
- `average_mrr >= 0.85`

Os limiares de métrica ficam abaixo do baseline medido sobre o store real (recall@3 = 1.0, recall@1 = 0.9375, MRR = 1.0), dando margem para detectar regressões sem reprovar por ruído.

O campo `passed` só retorna `true` quando todos os limiares são atendidos.

Quando executado via CLI, `python -m app.evals.run_eval` encerra com código diferente de zero se `passed` for `false`.
