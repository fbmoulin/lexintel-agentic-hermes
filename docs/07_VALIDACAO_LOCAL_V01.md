# Validação Local v0.1

Data: 2026-06-06  
Ambiente: Windows, Python 3.12.8  
Escopo: Lex Kratos Agentic Core local, mockado, sem serviços externos.

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
