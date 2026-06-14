# lex_kratos — Hermes Agent plugin

Expõe o pipeline jurídico **Lex Kratos** (mock v0.1) como ferramentas do
[Hermes Agent](https://github.com/NousResearch/hermes-agent), acessíveis pelo
gateway (Telegram, CLI, etc.).

## Por que HTTP (e não import direto)

O Hermes roda em **Python 3.11**; o lexintel fixa **Python 3.12** + FastAPI/pydantic.
Importar o orquestrador no interpretador do Hermes arriscaria conflito de
dependências (o próprio README do lexintel alerta para isso). Por isso o plugin
fala **apenas HTTP** com a API lexintel rodando em processo separado. Sem
dependências de terceiros (só stdlib), então cai em qualquer install do Hermes.

## Pré-requisito: subir a API lexintel

Em um terminal separado (no repositório lexintel, Python 3.12):

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

(ou via container; qualquer endpoint que sirva `/cases/intake` e
`/cases/run-full-mock`.)

## Instalação no Hermes

```bash
cp -r integrations/hermes/lex_kratos ~/.hermes/plugins/lex_kratos
# opcional: apontar para outra URL
hermes config set lex_kratos.base_url http://127.0.0.1:8000   # ou export LEX_KRATOS_BASE_URL=...
hermes            # inicia o TUI
/plugins          # confirme que lex_kratos carregou
```

Variável de ambiente: `LEX_KRATOS_BASE_URL` (default `http://127.0.0.1:8000`).

## Ferramentas

| Tool | Faz | Endpoint |
|---|---|---|
| `lex_intake` | intake + segurança (triagem, prompt-injection) | `POST /cases/intake` |
| `lex_run_pipeline` | pipeline completo mockado + trace auditável | `POST /cases/run-full-mock` |

Parâmetros: `case_id` (obrigatório), `source_type`, `user_goal`, `files`.

Exemplo no chat do Hermes:

> roda o pipeline lex_kratos no caso caso-2026-001 com o arquivo peticao_inicial.pdf

## Contrato

Handlers seguem o contrato do Hermes: retornam **string JSON**, nunca lançam
exceção (erros viram `{"error": "..."}`). Toda saída jurídica do lexintel
mantém `requires_human_review=true` e `external_use_allowed=false`.
