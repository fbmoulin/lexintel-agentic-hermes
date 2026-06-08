# Backlog

## Estado v0.1

- [x] Scaffold FastAPI.
- [x] Health check.
- [x] Intake endpoint.
- [x] Endpoint de pipeline completo mockado.
- [x] Endpoint RAG mockado.
- [x] Endpoint de avaliação mockada.
- [x] IntakeAgent.
- [x] SecurityAgent.
- [x] ExtractionAgent mockado.
- [x] LegalNormalizerAgent mockado.
- [x] MetadataAgent mockado.
- [x] FIRACAgent mockado.
- [x] ValidatorAgent mockado.
- [x] Orquestrador com trace.
- [x] Skills Markdown versionadas.
- [x] Schemas Pydantic e JSON schemas.
- [x] Testes pytest.
- [x] Dataset inicial.
- [x] Evaluation runner.
- [x] CI com pytest e avaliação mockada.
- [x] Spec-plano final validado.

## P0 — Congelamento e documentação

- [x] Separar Lex Kratos Core de Lex Intelligentia/Hermes.
- [x] Documentar que Manus/AGENTS2 é referência, não fonte de código.
- [x] Documentar que Qdrant é opcional/futuro na v0.1.
- [x] Registrar validação local.
- [ ] Revisão humana final da spec-plano e dos docs de Fase 0.

## P1 — Hardening de segurança local

- [x] Normalização de texto no SecurityAgent.
- [x] Severidade de risco.
- [x] Testes adversariais de prompt injection.
- [x] Campo padronizado `security_status`.
- [x] Campo `requires_human_review` nos outputs jurídicos.
- [x] Metadados estruturados `risk_details`, `max_severity` e `scan_version`.
- [x] Marcação de `external_use_allowed = false` em saídas jurídicas mockadas.

## P2 — Qualidade do pipeline mockado

- [x] Contrato padronizado de `AgentResult`.
- [x] Warnings e errors consistentes.
- [x] Trace documentado.
- [x] Testes mais completos para `/cases/run-full-mock`.
- [x] `pipeline_summary` determinístico nas respostas.
- [x] Metadados `trace_metadata` por etapa.
- [x] Teste de parada antecipada quando o SecurityAgent bloqueia.

## P3 — Skills e agentes locais

- [x] Loader de skills robusto e independente do diretório de execução.
- [x] Rejeição de path traversal no carregamento de skills.
- [x] Catálogo de 12 skills versionadas.
- [x] Registry de 12 agentes/capacidades.
- [x] Marcação de agentes implementados e planejados.
- [x] Endpoint `GET /catalog/skills`.
- [x] Endpoint `GET /catalog/skills/{skill_name}`.
- [x] Endpoint `GET /catalog/agents`.
- [x] Testes de integridade do registry e das skills.

## P4 — Avaliação RAG mockada

- [x] Expandir `golden_dataset.jsonl`.
- [x] Separar dataset por área.
- [x] Adicionar métricas além de recall médio.
- [x] Definir limiar mínimo de aceite.

## P5 — Extração e normalização estruturadas

- [x] Enriquecer contrato de extração mockada.
- [x] Enriquecer normalização jurídica mockada.
- [x] Validar outputs com Pydantic.

## P6 — RAG real preparado, mas desligado por padrão

- [x] QdrantService inicial.
- [x] Chunking jurídico.
- [x] IndexingAgent.
- [ ] HybridRetrievalAgent.
- [ ] RerankerService.
- [ ] Métricas retrieval.
- [x] Feature flag para Qdrant real.
- [x] MockVectorStore para testes sem container.

## P7 — Jurisprudência

- [ ] JurisprudenceAgent.
- [ ] Validação de formato de citação.
- [ ] Integração STJ Dados Abertos.
- [ ] Validação de súmulas/temas.

## P8 — Produção e integrações externas

- [ ] n8n.
- [ ] Logs.
- [ ] Auditoria.
- [ ] LGPD/CNJ.
- [x] CI inicial.
- [ ] CI/CD completo.
- [ ] Deploy Vercel/Railway/AWS.
- [ ] Supabase.
- [ ] DataJud.
- [ ] PJe.
- [ ] LLM service.
- [ ] Hermes Agent.
