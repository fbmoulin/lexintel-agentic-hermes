# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [0.2.0] — 2026-06-14

Otimização pós-revisão (PRs #13 Strand A + #15 Strand B). 53 → **71 testes**.
Base: revisão em `docs/audits/2026-06-13-deep-review.md`; spec/plan em
`docs/superpowers/`.

### Strand A — corretude interna e gate honesto

- **Avaliação RAG religada ao recuperador servido.** `run_eval` agora pontua o
  mesmo `MockVectorStore` (classe + scoring) que `/rag/search` usa, semeado com
  `golden_corpus.jsonl` que inclui **chunks distratores**. Antes, pontuava um
  stub de keywords (`fake_retrieve`, hoje `_smoke_retrieve`, só fumaça) e o gate
  não podia reprovar por qualidade. Dataset 8 → **24 casos** (6 por área);
  teste de discriminação (mis-seed reduz recall). `_tokenize` agora dobra acentos.
- **`blocked` para o pipeline.** Qualquer etapa `blocked` interrompe as fases
  jurídicas seguintes (antes só o gate de segurança), conforme `08_TRACE_CONTRACT`.
- **Validator vivo.** A saída do FIRAC é roteada para o `ValidatorAgent`; o
  caminho de bloqueio (precedente inventado) é alcançável e testado; `failed`
  coberto.
- **Contrato único.** Schemas JSON gerados dos modelos Pydantic
  (`scripts/gen_schemas.py`) + gate de drift na CI + teste de validação de
  payload real. `agent_run.schema.json` mantido como **future-spec**.
- **CI endurecida.** `ruff` + `mypy` + drift de schema antes dos testes.
- **`qdrant-client` opcional** (import lazy; `requirements-qdrant.txt`).
- Higiene: remoção de código morto, fim do vazamento de `str(exc)` ao cliente,
  imagem Qdrant pinada, isolamento de teste via fixture autouse.

### Strand B — integração com o Hermes Agent

- **Plugin `lex_kratos`** (`integrations/hermes/lex_kratos/`) expõe o pipeline
  como ferramentas do Hermes (`lex_intake`, `lex_run_pipeline`) via **HTTP**
  (Hermes Py3.11 ↔ lexintel Py3.12, processos separados), handlers stdlib-only.
- **Frontmatter Hermes/agentskills.io** nas 12 `app/skills/SKILL_*.md`.
- **`docs/COMPLIANCE_CNJ_615.md`** — mapa CNJ 615/2025 + LGPD verificado contra a
  resolução (categorias de risco: FIRAC/minuta/precedente = **alto risco**;
  registro Sinapses; regras de IA generativa), com lacunas declaradas.
- Repo posicionado como **implementação** da skill `ai-legal-development`.

### Notas

- Decisões do operador: `agent_run.schema.json` mantido como future-spec; plugin
  via HTTP (não import direto).
- 13 achados de bots de revisão nas 3 rodadas; 12 corrigidos, 1 informativo.
