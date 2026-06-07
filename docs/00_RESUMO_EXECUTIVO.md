# Resumo Executivo

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
