# Lex Kratos Agentic Core — v0.1

Este repositório consolida o núcleo jurídico agentico local do Lex Kratos. A v0.1 é intencionalmente pequena: FastAPI, agentes mockados, testes automatizados, dataset de avaliação e documentação de execução.

## Fronteira de escopo

Este projeto não é o deploy Hermes/Conteúdo do Lex Intelligentia.

Materiais externos como `Analyzing AGENTS2.zip`, tutoriais Hermes, cron jobs, n8n, áudio, vídeo, ElevenLabs e automação de publicação podem orientar backlog futuro, mas não são fonte de código nem critério de aceite da v0.1.

Nesta fase não há integrações reais com Qdrant, Supabase, n8n, DataJud, STJ Dados Abertos, PJe ou LLMs.

## Objetivo

Criar uma esteira jurídica auditável, inicialmente mockada, para:

- ingestão de documentos;
- extração e normalização jurídica;
- busca RAG simulada;
- análise FIRAC+;
- validação jurídica;
- segurança contra prompt injection;
- avaliação contínua por métricas.

Indexação vetorial, busca híbrida real, pesquisa jurisprudencial real e geração de minuta ficam para fases posteriores com autorização explícita.

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

Agentes como HybridRetrievalAgent, JurisprudenceAgent, DraftingAgent e EvaluationAgent permanecem planejados para fases futuras.

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

Este pacote entrega um scaffold funcional com mocks. A conexão real com Qdrant, Supabase, LLMs e automações externas deve ser ativada apenas em fases seguintes e mediante tarefa explícita.

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

Ele valida o JSONL, agrupa casos por área e retorna métricas como `average_recall_at_1`, `average_recall_at_3`, `average_mrr`, `area_summary` e `passed`. O limiar mínimo atual exige 8 casos, quatro áreas obrigatórias e médias globais `>= 0.85` para `recall@3` e MRR. O CLI encerra com erro quando `passed` é `false`.

## Extração e normalização mockadas

O pipeline completo usa `ExtractionAgent`, `LegalNormalizerAgent` e `MetadataAgent` com contratos Pydantic locais. Eles simulam petição inicial, contestação, sentença e acórdão sem ler PDF real, sem OCR e sem serviço externo.

Documento não classificado recebe baixa qualidade mockada, bloqueia automação e exige revisão humana.

## Indexação e busca mockadas

O `IndexingAgent` gera chunks jurídicos determinísticos e indexa em `MockVectorStore`. O endpoint `/rag/search` usa esse store mockado por padrão, reutilizando a instância em memória para que chunks indexados no pipeline possam ser buscados em chamadas seguintes.

Qdrant real permanece desligado. `get_qdrant_client()` só cria cliente quando `LEX_KRATOS_ENABLE_QDRANT=true`, e essa ativação deve ocorrer apenas em tarefa explícita de integração.

## Validação local

Os comandos de aceite da v0.1 são:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
python -m app.evals.run_eval
```

Também há um workflow em `.github/workflows/ci.yml` que executa testes e avaliação mockada em Python 3.12.

No Windows, se o `pytest` falhar por permissão no diretório temporário padrão, rode com `TMP` e `TEMP` apontando para uma pasta controlada do workspace. Esse é um ajuste ambiental, não uma dependência do produto.
