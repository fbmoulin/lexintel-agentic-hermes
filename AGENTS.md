# Lex Kratos Agentic Core - Agent Instructions

Este repositorio e o nucleo do Lex Kratos Agentic Core (v0.5.1: pipeline mockado + busca hibrida BM25/RRF com Qdrant opcional). Memoria operacional do Claude Code em `CLAUDE.md`; estado autoritativo em `docs/HANDOFF.md`.

## Regras de trabalho

- Nao reutilizar codigo de repositorios antigos ou legacy sem autorizacao expressa.
- Manter as entregas pequenas, auditaveis e incrementais.
- Priorizar mocks locais, testes automatizados e documentacao clara.
- Nao implementar integracoes reais com Supabase, n8n, DataJud, STJ Dados Abertos ou LLMs sem uma tarefa explicita. Excecao ja aprovada: Qdrant opcional atras de LEX_KRATOS_ENABLE_QDRANT (desligado por padrao).
- Preservar revisao humana obrigatoria para qualquer fluxo juridico que gere analise, minuta, recomendacao ou decisao.
- Tratar prompt injection como risco de seguranca: entradas suspeitas devem ser bloqueadas ou marcadas para revisao.
- Evitar efeitos colaterais externos nos testes. Testes devem rodar localmente e de forma deterministica.

## Comandos esperados

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # ruff, mypy, jsonschema (testes/lint)
uvicorn app.main:app --reload
ruff check app tests scripts integrations && ruff format --check app tests scripts integrations
python -m mypy app   # usar o Python do projeto (mypy externo nao enxerga qdrant-client)
pytest
python -m app.evals.run_eval
```

## Estrutura esperada

- `app/main.py`: aplicacao FastAPI e registro de rotas.
- `app/api/`: endpoints HTTP mockados.
- `app/agents/`: agentes especializados com comportamento local.
- `app/services/`: serviços de dominio (chunking estrutural, markers, extracao mockada, embeddings, Qdrant, vector store, skill loader).
- `app/skills/`: skills em Markdown para orientar futuras capacidades.
- `app/schemas/`: modelos Pydantic e schemas JSON.
- `app/evals/`: dataset dourado e avaliacao RAG mockada.
- `tests/`: testes de saude, intake, seguranca e avaliacao.
- `docs/`: documentacao tecnica, plano, backlog e tutorial.

## Criterio de aceite

O nucleo deve instalar dependencias, subir a API localmente, passar nos testes (156 + 2 pulados), no lint/type-check/drift de schema e executar a avaliacao mockada sem depender de servicos externos.
