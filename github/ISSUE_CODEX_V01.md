# Implementar Lex Kratos Agentic Core v0.1

## Objetivo

Criar scaffold FastAPI com arquitetura agentica modular para o Lex Intelligentia/Kratos.

## Escopo da primeira entrega

- Criar estrutura de pastas.
- Criar app FastAPI.
- Criar endpoint GET /health.
- Criar endpoint POST /cases/intake.
- Criar endpoint POST /cases/run-full-mock.
- Criar schemas Pydantic.
- Criar IntakeAgent.
- Criar SecurityAgent.
- Criar ExtractionAgent mockado.
- Criar LegalNormalizerAgent mockado.
- Criar MetadataAgent mockado.
- Criar FIRACAgent mockado.
- Criar ValidatorAgent mockado.
- Criar CaseOrchestrator.
- Criar golden_dataset.jsonl.
- Criar run_eval.py.
- Criar testes mínimos com pytest.

## Fora do escopo nesta primeira entrega

- Integração real com Qdrant.
- Integração real com Supabase.
- Integração real com LLM.
- Integração com n8n.
- Download de processo.
- Redação de minuta real.

## Critérios de aceitação

- `uvicorn app.main:app --reload` inicia sem erro.
- `GET /health` retorna status ok.
- `POST /cases/intake` retorna trace dos agentes.
- `POST /cases/run-full-mock` retorna fluxo ponta a ponta mockado.
- `python -m app.evals.run_eval` executa sem erro.
- `pytest` executa sem erro.

## Restrição crítica

Não reaproveitar código de repositórios legacy sem revisão explícita. Este repositório deve ser tratado como núcleo limpo.
