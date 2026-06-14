# Plano de Execução

Este plano segue a decisão da spec final validada: a v0.1 permanece local, mockada e sem integrações reais. Material Manus/AGENTS2, Hermes, n8n, cron jobs, audio/video e automação de publicação pertencem a backlog futuro separado.

## Fase 0 — Congelamento da v0.1

Objetivo: estabilizar o scaffold atual e remover ambiguidade de escopo antes de novas implementações.

Entregas:

- README alinhado à v0.1 mockada.
- Tutorial sem dependência de Hermes/n8n/LLMs.
- Backlog marcando o que já está concluído.
- Registro de validação local.
- Nota explícita: Manus/AGENTS2 é referência, não fonte de código.

Critério de aceite:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
python -m app.evals.run_eval
```

## Fase Base — Trilho agentico local

Status: entregue na v0.1 inicial.

Objetivo: rodar localmente o fluxo mínimo.

Entregas:

- FastAPI funcionando.
- `/health`
- `/cases/intake`
- IntakeAgent.
- SecurityAgent.
- Orquestrador.
- Testes.

Critério de aceite:

```bash
uvicorn app.main:app --reload
pytest
```

## Fase 1 — Hardening de segurança local

Status: implementada.

Objetivo: reforçar a detecção determinística de prompt injection antes de qualquer integração real.

Entregas:

- Normalização local de texto com remoção de acentos, controles invisíveis e separadores.
- Detecção por regras estruturadas com severidade.
- Saídas `security_status`, `detected_risks`, `risk_details`, `max_severity`, `recommended_action` e `requires_human_review`.
- Bloqueio para riscos `high` e `critical`.
- Marcação de revisão humana para riscos `medium`.
- Saídas jurídicas mockadas marcadas com `requires_human_review = true` e `external_use_allowed = false`.
- Testes adversariais de prompt injection.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase Base — Skills e avaliação

Status: entregue na v0.1 inicial.

Objetivo: versionar conhecimento operacional e criar métrica.

Entregas:

- Skills em Markdown.
- `golden_dataset.jsonl`
- `run_eval.py`
- Endpoint `/eval/run`.

Critério de aceite:

```bash
python -m app.evals.run_eval
```

## Fase 2 — Qualidade do pipeline mockado

Status: implementada.

Objetivo: tornar o pipeline local mais auditável sem adicionar integrações reais.

Entregas:

- Contrato `AgentResult` ampliado com `requires_human_review`, `external_use_allowed` e `trace_metadata`.
- Metadados determinísticos de trace por etapa.
- Resumo `pipeline_summary` nas respostas de intake e pipeline completo mockado.
- Contagem de agentes, warnings e errors.
- Identificação de `blocked_at` quando o pipeline para antes do fim.
- Teste de parada antecipada por bloqueio do SecurityAgent.
- Documentação do contrato de trace.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase 3 — Skills e agentes locais

Status: implementada.

Objetivo: tornar as skills Markdown e os agentes locais descobertos, validados e vinculados por contrato.

Entregas:

- Loader de skills robusto e independente do diretório de execução.
- Rejeição de path traversal no carregamento de skills.
- Catálogo das 12 skills em `app/skills/`.
- Registry das 12 capacidades agenticas previstas.
- Marcação explícita de agentes implementados e planejados.
- Endpoints `/catalog/skills`, `/catalog/skills/{skill_name}` e `/catalog/agents`.
- Testes de integridade do catálogo.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase 4 — Avaliação RAG mockada

Status: implementada.

Objetivo: melhorar o dataset e as métricas antes de integrar busca real.

Entregas:

- `golden_dataset.jsonl` expandido para **24 casos** (6 por área) — atualizado na v0.2.
- Dataset separado por `area` com cobertura bancária, saúde, consumidor e processual civil.
- Métricas `average_recall_at_1`, `average_recall_at_3`, `average_mrr` e resumo por área.
- Validação rígida do JSONL com falha em CI se houver linha inválida, campo ausente, campo textual inválido ou ID duplicado.
- A avaliação pontua o `MockVectorStore` servido (corpus `golden_corpus.jsonl` com distratores), não um stub. Ver `docs/10_RAG_EVAL_CONTRACT.md`.
- Limiar mínimo local: dataset com **24 casos**, áreas obrigatórias, `average_recall_at_3 >= 0.85` e `average_mrr >= 0.85`.
- CLI de avaliação encerra com erro quando os limiares não são atendidos.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase 5 — Extração e normalização

Status: implementada.

Objetivo: transformar documentos em estrutura jurídica.

Entregas:

- Contratos Pydantic `ExtractedText`, `ExtractionQualitySummary`, `NormalizedCase` e `CaseMetadata`.
- `ExtractionAgent` com texto mockado por tipo documental, `quality_score`, `quality_summary` e warning para baixa qualidade.
- `LegalNormalizerAgent` com partes, fatos, pedidos, causa de pedir, defesas, provas, eventos processuais e questões jurídicas.
- `MetadataAgent` com metadados mockados derivados de tipos documentais e questões jurídicas normalizadas.
- Testes para petição inicial, contestação, sentença, acórdão e documento desconhecido.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase 6 — Qdrant e indexação

Status: implementada.

Objetivo: preparar indexação de chunks sem ativar Qdrant real por padrão.

Entregas:

- Docker Compose Qdrant opcional.
- `QdrantService` protegido por `LEX_KRATOS_ENABLE_QDRANT`.
- `MockVectorStore` para testes sem container.
- `IndexingAgent` implementado e registrado no catálogo.
- Chunking por unidade jurídica com `chunk_id` determinístico.
- Endpoint `/rag/search` usando store mockado por padrão.

Critério de aceite:

```bash
pytest
python -m app.evals.run_eval
```

## Fase 7 — Retrieval híbrido

Objetivo: melhorar qualidade de recuperação.

Entregas:

- Dense retrieval.
- Sparse/BM25-like retrieval.
- Fusão RRF/DBSF.
- RerankerService.
- Métricas comparativas.

## Fase 8 — FIRAC+ e minuta

Objetivo: gerar análise antes da decisão.

Entregas:

- FIRACAgent.
- JurisprudenceAgent.
- DraftingAgent.
- ValidatorAgent.

## Fase 9 — n8n

Objetivo: automatizar fluxo externo somente após aprovação explícita.

Entregas:

- Webhook.
- HTTP Request para FastAPI.
- Registro em Google Sheets.
- Geração opcional de Google Docs.

## Fase 10 — CI de qualidade

Objetivo: evitar regressão.

Entregas:

- GitHub Actions.
- Pytest.
- Eval runner.
- Security tests.
- Bloqueio se métricas caírem.
