# Resumo Executivo

> **Status v0.5 (2026-07-11):** sobre a v0.4, a v0.5 adiciona **busca híbrida
> jurídica** (PR #22): `BM25Retriever` (Okapi, esparso) + `reciprocal_rank_fusion`
> (RRF) compostos no `HybridRetrievalAgent`, agora o **retriever de registro
> único** em `/rag/search`, no passo `retrieval` do pipeline (trace-v0.3, entre
> indexação e FIRAC; FIRAC ainda não é alimentado) e na avaliação (thresholds de
> não-regressão recall@1≥0.9375, MRR≥1.0). Offline funde dois sinais léxicos
> (BM25 + token-overlap do Mock); o lado denso (Qdrant) só participa com
> `QDRANT_ENABLED`. **150 testes** (+2 de integração pulados por padrão). Detalhes
> em `CHANGELOG.md`, `docs/10_RAG_EVAL_CONTRACT.md` e `docs/08_TRACE_CONTRACT.md`.
>
> _Histórico v0.4 (2026-07-10):_ ciclo de revisão + premortem (PRs #18–#20:
> indexação best-effort, piso de recall@3 por área, caps de entrada, tag
> `index_status`) e chunking estrutural jurídico (PR #21). 77→123 testes; nenhum
> achado CRITICAL/HIGH na revisão completa.
>
> _Histórico v0.3 (2026-06-14):_ sobre a v0.2 (otimização pós-revisão —
> avaliação RAG religada ao recuperador servido com distratores, `blocked`
> interrompe o pipeline, validator vivo, contrato Pydantic único, CI com
> ruff/mypy/drift, plugin Hermes `lex_kratos`, mapa CNJ 615/2025), a v0.3
> adicionou recuperação semântica real opcional com Qdrant (PR #17, atrás de
> `LEX_KRATOS_ENABLE_QDRANT`, desligada por padrão; embeddings locais `fastembed`).

O objetivo do projeto é transformar o Lex Intelligentia/Kratos em um app jurídico auditável, modular e mensurável.

A prioridade não é migrar imediatamente banco vetorial ou criar um sistema altamente complexo. A prioridade é construir um trilho confiável:

```text
Entrada → Segurança → Extração → Normalização → Indexação → Retrieval → FIRAC+ → Jurisprudência → Minuta → Validação → Revisão Humana
```

## Premissas consolidadas do chat

1. O projeto deve evitar deriva para repositórios legacy.
2. O MVP deve começar com baixo custo.
3. O fluxo deve ser compatível com FastAPI, n8n, Qdrant, Supabase e futura integração com DataJud/STJ.
4. A arquitetura deve preservar HITL obrigatório.
5. O sistema deve medir qualidade por benchmark próprio.
6. O módulo de segurança contra prompt injection é obrigatório.
7. A base vetorial recomendada para esta fase é Qdrant, com avaliação posterior de Weaviate.
8. O ganho de qualidade deve vir primeiro de:
   - metadados jurídicos;
   - chunking jurídico;
   - busca híbrida;
   - reranking;
   - validação de precedentes;
   - avaliação contínua.

## Entregável inicial

Este pacote contém:

- spec técnico completo;
- tutorial de execução;
- scaffold FastAPI;
- agentes mockados;
- skills em Markdown;
- schemas;
- dataset inicial de avaliação;
- testes;
- Docker Compose para Qdrant;
- template de issue para Codex/GitHub;
- template de workflow n8n.
