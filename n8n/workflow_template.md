# n8n Workflow Template — Lex Kratos v0.1

## Fluxo mínimo

```text
Manual Trigger
↓
Set Node
↓
HTTP Request
↓
Google Sheets / Google Docs
```

## Set Node — JSON de teste

```json
{
  "case_id": "caso_n8n_001",
  "source_type": "manual",
  "user_goal": "analise",
  "files": ["peticao_inicial.pdf", "contestacao.pdf"]
}
```

## HTTP Request

Método:

```text
POST
```

URL local:

```text
http://host.docker.internal:8000/cases/intake
```

Ou, se rodando fora do Docker:

```text
http://127.0.0.1:8000/cases/intake
```

Headers:

```json
{
  "Content-Type": "application/json"
}
```

Body:

```text
JSON vindo do Set Node
```

## Próxima evolução

Quando o endpoint estiver estável, trocar para:

```text
POST /cases/run-full-mock
```

Depois, substituir mocks por:

```text
PDF real → extração → normalização → indexação → FIRAC+ → minuta → validação
```
