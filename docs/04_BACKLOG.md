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

- [ ] Normalização de texto no SecurityAgent.
- [ ] Severidade de risco.
- [ ] Testes adversariais de prompt injection.
- [ ] Campo padronizado `security_status`.
- [ ] Campo `requires_human_review` nos outputs jurídicos.

## P2 — Qualidade do pipeline mockado

- [ ] Contrato padronizado de `AgentResult`.
- [ ] Warnings e errors consistentes.
- [ ] Trace documentado.
- [ ] Testes mais completos para `/cases/run-full-mock`.

## P3 — Avaliação RAG mockada

- [ ] Expandir `golden_dataset.jsonl`.
- [ ] Separar dataset por área.
- [ ] Adicionar métricas além de recall médio.
- [ ] Definir limiar mínimo de aceite.

## P4 — Extração e normalização estruturadas

- [ ] Enriquecer contrato de extração mockada.
- [ ] Enriquecer normalização jurídica mockada.
- [ ] Validar outputs com Pydantic.

## P5 — RAG real preparado, mas desligado por padrão

- [x] QdrantService inicial.
- [ ] Chunking jurídico.
- [ ] IndexingAgent.
- [ ] HybridRetrievalAgent.
- [ ] RerankerService.
- [ ] Métricas retrieval.
- [ ] Feature flag para Qdrant real.
- [ ] MockVectorStore para testes sem container.

## P6 — Jurisprudência

- [ ] JurisprudenceAgent.
- [ ] Validação de formato de citação.
- [ ] Integração STJ Dados Abertos.
- [ ] Validação de súmulas/temas.

## P7 — Produção e integrações externas

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
