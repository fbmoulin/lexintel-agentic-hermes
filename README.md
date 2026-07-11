# Lex Kratos Agentic Core — v0.5

Este repositório consolida o núcleo jurídico agentico local do Lex Kratos. O núcleo permanece intencionalmente pequeno e auditável — FastAPI, agentes mockados, testes automatizados, dataset de avaliação e documentação de execução — mas já cresceu além do scaffold inicial: recuperação híbrida jurídica (BM25 + fusão RRF, mock-first, Qdrant opcional), recuperação semântica real opcional com Qdrant (desligada por padrão) e chunking estrutural jurídico. A suíte tem **149 testes** (+2 de integração pulados por padrão).

## Fronteira de escopo

Este projeto não é o deploy Hermes/Conteúdo do Lex Intelligentia.

Materiais externos como `Analyzing AGENTS2.zip`, tutoriais Hermes, cron jobs, n8n, áudio, vídeo, ElevenLabs e automação de publicação podem orientar backlog futuro, mas não são fonte de código nem critério de aceite da v0.1.

Não há integrações reais com Supabase, n8n, DataJud, STJ Dados Abertos, PJe ou LLMs. A única exceção é a **recuperação semântica real com Qdrant** (PR #17), que é opcional e desligada por padrão — ver a seção "Recuperação real com Qdrant (opcional)" abaixo.

## Objetivo

Criar uma esteira jurídica auditável, inicialmente mockada, para:

- ingestão de documentos;
- extração e normalização jurídica;
- busca RAG simulada;
- análise FIRAC+;
- validação jurídica;
- segurança contra prompt injection;
- avaliação contínua por métricas.

A busca híbrida (BM25 + fusão RRF) já está implementada como `HybridRetrievalAgent`, mock-first, com o lado denso real acionável apenas via Qdrant opcional. Pesquisa jurisprudencial real e geração de minuta ficam para fases posteriores com autorização explícita.

## Decisão arquitetural central

Não criar um superagente monolítico.

Criar um orquestrador simples com agentes especializados:

1. IntakeAgent
2. SecurityAgent
3. ExtractionAgent
4. LegalNormalizerAgent
5. MetadataAgent
6. IndexingAgent
7. FIRACAgent
8. ValidatorAgent

O `HybridRetrievalAgent` (busca híbrida BM25 + fusão RRF) já está implementado e roda entre `IndexingAgent` e `FIRACAgent`. Agentes como JurisprudenceAgent, DraftingAgent e EvaluationAgent permanecem planejados para fases futuras.

## Como começar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

> Use uma `.venv` dedicada. Instalar no Python global pode gerar conflitos com outros projetos que usem FastAPI, httpx, pytest ou Supabase em versões diferentes.

No navegador:

```text
http://127.0.0.1:8000/docs
```

Depois rode:

```bash
pytest
python -m app.evals.run_eval
```

## Estado atual

Este pacote entrega um scaffold funcional com mocks. A conexão real com Supabase, LLMs e automações externas deve ser ativada apenas em fases seguintes e mediante tarefa explícita. A recuperação real com Qdrant já existe como opção (PR #17), desligada por padrão — ver seção própria abaixo.

O `docker-compose.yml` atual é apoio futuro para Qdrant e não é requisito para rodar a v0.1.

## Catálogo local

A API expõe um catálogo auditável de skills e agentes:

```text
GET /catalog/skills
GET /catalog/skills/{skill_name}
GET /catalog/agents
```

Esse catálogo apenas lê arquivos locais em `app/skills/` e registra o estado dos agentes mockados ou planejados. Ele não chama LLMs nem serviços externos.

## Avaliação RAG mockada

O runner local em `app/evals/run_eval.py` avalia o dataset dourado sem rede e sem Qdrant real.

Ele pontua com o **mesmo recuperador híbrido de referência que serve `/rag/search`** — `build_hybrid_eval_store` (fusão RRF de BM25 + Mock token-overlap, um ensemble léxico; o lado denso só entra com `QDRANT_ENABLED=1`), numa **instância própria** semeada com `golden_corpus.jsonl` (que inclui chunks distratores), não a instância singleton da API. Valida o JSONL, agrupa casos por área e retorna `retriever`, `average_recall_at_1`, `average_recall_at_3`, `average_mrr`, `area_summary` e `passed`. O limiar mínimo atual exige 24 casos (6 por área), quatro áreas obrigatórias, `recall@3 >= 0.85`, `recall@1 >= 0.9375` e MRR `>= 1.0` (pisos de não-regressão ancorados no baseline dourado do Mock, que o híbrido iguala). O CLI encerra com erro quando `passed` é `false`.

## Extração e normalização mockadas

O pipeline completo usa `ExtractionAgent`, `LegalNormalizerAgent` e `MetadataAgent` com contratos Pydantic locais. Eles simulam petição inicial, contestação, sentença e acórdão sem ler PDF real, sem OCR e sem serviço externo.

Documento não classificado recebe baixa qualidade mockada, bloqueia automação e exige revisão humana.

## Indexação e busca mockadas

O `IndexingAgent` gera chunks jurídicos determinísticos e indexa em `MockVectorStore`. A chunking é **estrutural**: `get_chunker()` detecta seções jurídicas (RELATÓRIO/FUNDAMENTAÇÃO/DISPOSITIVO em sentença; EMENTA/RELATÓRIO/VOTO/DISPOSITIVO em acórdão; DOS FATOS/DO DIREITO/DOS PEDIDOS em petição; DAS PRELIMINARES/DO MÉRITO/DOS PEDIDOS em contestação) e emite um chunk por seção via `StructuralChunker`, com fallback para `ParagraphChunker` (orçamento de tokens + overlap de 1 sentença) quando não há marcadores. A extração mockada (`MockExtractor` em `app/services/extraction.py`, atrás da interface `Extractor`) produz o texto estruturado; a função legada `chunk_extracted_text()` está **deprecada** em favor de `build_chunks()`. O endpoint `/rag/search` usa esse store mockado por padrão, reutilizando a instância em memória para que chunks indexados no pipeline possam ser buscados em chamadas seguintes.

Por padrão o Qdrant real permanece desligado (`LEX_KRATOS_ENABLE_QDRANT=false`). Para ligar a recuperação semântica real, veja a seção abaixo.

## Recuperação real com Qdrant (opcional)

Quando ligada, a busca passa a usar embeddings reais (modelo multilíngue local `paraphrase-multilingual-MiniLM-L12-v2`, 384 dim, via `fastembed`) sobre um Qdrant local — recuperando por significado, não por sobreposição de tokens. A `MockVectorStore`, a avaliação `run_eval` e o comportamento com a flag desligada permanecem inalterados.

```bash
# 1. Instale o extra opcional (baixa ~0.22 GB de pesos do modelo no 1º uso).
.venv/bin/pip install -r requirements-qdrant.txt

# 2. Suba o Qdrant pinado (v1.14.1) na porta 6533 — evita colidir com um
#    Qdrant que já ocupe :6333.
QDRANT_HOST_PORT=6533 docker compose up -d qdrant

# 3. Suba a API com a flag ligada (QDRANT_PORT deve casar com QDRANT_HOST_PORT).
LEX_KRATOS_ENABLE_QDRANT=true QDRANT_PORT=6533 uvicorn app.main:app --reload
```

Rode o pipeline (indexa no Qdrant) e então `POST /rag/search` retorna `vector_backend=qdrant` e cada hit com `retrieval_method=qdrant`. Os testes de integração ficam em `tests/integration/` e são pulados por padrão; rode-os contra o servidor vivo com `LEX_KRATOS_ENABLE_QDRANT=true QDRANT_PORT=6533 pytest tests/integration`.

## Validação local

Os comandos de aceite da v0.1 são:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # ruff, mypy, jsonschema — necessários para testes/lint
uvicorn app.main:app --reload
ruff check app tests scripts integrations && ruff format --check app tests scripts integrations
mypy app
pytest
python -m app.evals.run_eval
```

> `requirements-dev.txt` é obrigatório para rodar `pytest` (alguns testes importam `jsonschema`), `ruff` e `mypy`. Rodar a API em si só precisa de `requirements.txt`.

Também há um workflow em `.github/workflows/ci.yml` que executa lint (ruff), type-check (mypy), checagem de drift de schema, testes e avaliação mockada em Python 3.12.

No Windows, se o `pytest` falhar por permissão no diretório temporário padrão, rode com `TMP` e `TEMP` apontando para uma pasta controlada do workspace. Esse é um ajuste ambiental, não uma dependência do produto.

## Integração com o Hermes Agent

Este projeto é a **implementação** da metodologia descrita na skill Hermes
`ai-legal-development` (ver `docs/09_SKILLS_AGENTS_CATALOG.md`), não uma fonte
concorrente.

- **Plugin** `integrations/hermes/lex_kratos/` expõe o pipeline como ferramentas
  do Hermes (`lex_intake`, `lex_run_pipeline`), acessíveis pelo gateway (Telegram).
  Transporte HTTP (Hermes Py3.11 ↔ lexintel Py3.12, processos separados). Ver o
  README do plugin para instalação.
- As `app/skills/SKILL_*.md` têm frontmatter Hermes/agentskills.io e são carregáveis
  por um install do Hermes.
- Conformidade CNJ 615/2025 + LGPD mapeada em `docs/COMPLIANCE_CNJ_615.md`.
