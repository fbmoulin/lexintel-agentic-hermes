# Lex Kratos Agentic Core - Agent Instructions

Este repositorio e o scaffold limpo v0.1 do Lex Kratos Agentic Core.

## Regras de trabalho

- Nao reutilizar codigo de repositorios antigos ou legacy sem autorizacao expressa.
- Manter a entrega v0.1 pequena, auditavel e incremental.
- Priorizar mocks locais, testes automatizados e documentacao clara.
- Nao implementar integracoes reais com Qdrant, Supabase, n8n, DataJud, STJ Dados Abertos ou LLMs nesta fase sem uma tarefa explicita.
- Preservar revisao humana obrigatoria para qualquer fluxo juridico que gere analise, minuta, recomendacao ou decisao.
- Tratar prompt injection como risco de seguranca: entradas suspeitas devem ser bloqueadas ou marcadas para revisao.
- Evitar efeitos colaterais externos nos testes. Testes devem rodar localmente e de forma deterministica.

## Comandos esperados

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # ruff, mypy, jsonschema (testes/lint)
uvicorn app.main:app --reload
ruff check app tests scripts integrations && mypy app
pytest
python -m app.evals.run_eval
```

## Estrutura esperada

- `app/main.py`: aplicacao FastAPI e registro de rotas.
- `app/api/`: endpoints HTTP mockados.
- `app/agents/`: agentes especializados com comportamento local.
- `app/skills/`: skills em Markdown para orientar futuras capacidades.
- `app/schemas/`: modelos Pydantic e schemas JSON.
- `app/evals/`: dataset dourado e avaliacao RAG mockada.
- `tests/`: testes de saude, intake, seguranca e avaliacao.
- `docs/`: documentacao tecnica, plano, backlog e tutorial.

## Criterio de aceite v0.1

O nucleo deve instalar dependencias, subir a API localmente, passar nos testes e executar a avaliacao mockada sem depender de servicos externos.
