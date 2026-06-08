# Contrato da Avaliação RAG Mockada

Este contrato descreve a avaliação local em `python -m app.evals.run_eval`.

A avaliação permanece mockada, determinística e sem acesso a Qdrant, LLMs, STJ Dados Abertos, DataJud ou qualquer serviço externo.

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

- `dataset_size >= 8`
- áreas obrigatórias presentes
- `average_recall_at_3 >= 0.85`
- `average_mrr >= 0.85`

O campo `passed` só retorna `true` quando todos os limiares são atendidos.

Quando executado via CLI, `python -m app.evals.run_eval` encerra com código diferente de zero se `passed` for `false`.
