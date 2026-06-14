# Validação Local v0.1

Data: 2026-06-06  
Ambiente: Windows, Python 3.12.8  
Escopo: Lex Kratos Agentic Core local, mockado, sem serviços externos.

> **Atualização v0.3 (2026-06-14):** após a otimização (PRs #13/#15) e a
> recuperação real com Qdrant (PR #17), a suíte tem **77 testes** (eram 53; +2 de
> integração com Qdrant vivo, pulados por padrão) e a CI roda, nesta ordem:
> `ruff check` + `ruff format --check` (app/tests/scripts/integrations),
> `mypy app`, drift de schema (`scripts.gen_schemas` + `git diff`), `pytest`,
> `python -m app.evals.run_eval`. Para rodar testes localmente é preciso instalar
> também `requirements-dev.txt` (ruff, mypy, jsonschema, qdrant-client). A
> avaliação RAG passou a pontuar o `MockVectorStore` servido com corpus de
> distratores (recall@3 = 1.0, recall@1 = 0.9375, MRR = 1.0) e permanece
> mock-only. Ver `CHANGELOG.md`.

## Comandos executados

```bash
python -m pip install -r requirements.txt
```

Resultado:

- Dependências já satisfeitas no ambiente local.
- Instalação concluída sem erro.

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8766
```

Validação via `GET /health`:

```json
{"status":"ok","service":"lex-kratos-agentic-core","version":"0.1.0"}
```

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 4
- `average_recall`: 0.625
- Execução concluída sem erro.

```bash
pytest
```

Primeira execução:

- 9 testes aprovados.
- 1 erro ambiental ao criar fixture `tmp_path` em `AppData\Local\Temp\pytest-of-fbmou`.

Reexecução com `TMP` e `TEMP` apontando para pasta temporária controlada no workspace:

- 10 testes aprovados.

## Interpretação

A falha inicial foi ambiental, relacionada a permissão do diretório temporário do Windows. O comportamento do produto foi validado com sucesso quando o diretório temporário foi controlado.

## Fronteira confirmada

Durante esta validação não foram usados:

- Hermes Agent;
- n8n;
- Qdrant real;
- Supabase;
- DataJud;
- STJ Dados Abertos;
- PJe;
- LLMs;
- APIs de áudio, imagem ou publicação.

O pacote `Analyzing AGENTS2.zip` foi usado apenas como referência de arquitetura/backlog e não como fonte de código.

## Validação da Fase 1 — Hardening de segurança local

Data: 2026-06-07

Mudanças validadas:

- Normalização determinística no `SecurityAgent`.
- Severidade e detalhes estruturados de risco.
- Bloqueio de prompt injection com acentos removidos, caixa alterada e controles invisíveis.
- Marcação de revisão humana para risco médio.
- Campo `requires_human_review` em saídas jurídicas mockadas.
- Campo `external_use_allowed = false` em saídas jurídicas mockadas.

Comandos executados:

```bash
pytest
```

Resultado:

- 15 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 4
- `average_recall`: 0.625
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.

## Validação da Fase 2 — Qualidade do pipeline mockado

Data: 2026-06-07

Mudanças validadas:

- `AgentResult` com campos top-level de revisão humana, uso externo e metadados de trace.
- `pipeline_summary` nas respostas de `/cases/intake` e `/cases/run-full-mock`.
- Índice determinístico de etapas no trace.
- Consistência de `warnings` e `errors` como listas.
- Parada antecipada do pipeline completo quando o `SecurityAgent` bloqueia a entrada.

Comandos executados:

```bash
pytest
```

Resultado:

- 16 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 4
- `average_recall`: 0.625
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.

## Validação da Fase 3 — Skills e agentes locais

Data: 2026-06-07

Mudanças validadas:

- Catálogo local de 12 skills Markdown.
- Registry local de 12 agentes/capacidades.
- 7 agentes implementados e importáveis.
- 5 agentes planejados vinculados a skills existentes.
- Endpoints `/catalog/skills`, `/catalog/skills/{skill_name}` e `/catalog/agents`.
- Bloqueio de path traversal no carregamento de skills.

Comandos executados:

```bash
pytest
```

Resultado:

- 23 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 4
- `average_recall`: 0.625
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.

## Validação da Fase 4 — Avaliação RAG mockada

Data: 2026-06-08

Mudanças validadas:

- Dataset dourado expandido para 8 casos.
- Agrupamento por área: bancário, saúde, consumidor e processual civil.
- Métricas `average_recall_at_1`, `average_recall_at_3` e `average_mrr`.
- Resumo `area_summary` com casos abaixo de `recall@3`.
- Validação rígida de JSONL inválido, campos obrigatórios, `id` não textual e dataset pequeno.
- Limiar local de aceite via `passed` e `threshold_failures`.

Comandos executados:

```bash
pytest
```

Resultado:

- 34 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 8
- `average_recall_at_3`: 0.9166666666666666
- `average_mrr`: 0.9166666666666666
- `passed`: true
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.

## Validação da Fase 5 — Extração e normalização estruturadas

Data: 2026-06-08

Mudanças validadas:

- Contratos Pydantic para extração, resumo de qualidade, normalização e metadados.
- `ExtractionAgent` com texto mockado por tipo documental e `quality_score`.
- Documento `unknown` ou lista vazia com automação bloqueada e revisão humana.
- `LegalNormalizerAgent` com partes, fatos, pedidos, causa de pedir, defesas, provas, eventos e questões jurídicas.
- `MetadataAgent` com metadados derivados de tipos documentais mockados.
- Pipeline completo expondo extração, normalização e metadados estruturados no trace.

Comandos executados:

```bash
pytest
```

Resultado:

- 39 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 8
- `average_recall_at_3`: 0.9166666666666666
- `average_mrr`: 0.9166666666666666
- `passed`: true
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.

## Validação da Fase 6 — Qdrant e indexação mockada

Data: 2026-06-08

Mudanças validadas:

- `QdrantService` protegido por feature flag.
- `MockVectorStore` determinístico em memória.
- `IndexingAgent` implementado e incluído no pipeline completo.
- Chunking jurídico por unidade mockada com `chunk_id` determinístico.
- `/rag/search` usando store mockado por padrão.
- Catálogo de agentes atualizado para `IndexingAgent` implementado.

Comandos executados:

```bash
pytest
```

Resultado:

- 53 testes aprovados.

```bash
python -m app.evals.run_eval
```

Resultado:

- `dataset_size`: 8
- `average_recall_at_3`: 0.9166666666666666
- `average_mrr`: 0.9166666666666666
- `passed`: true
- Execução concluída sem erro.

Durante esta fase, nenhuma integração real externa foi ativada.
