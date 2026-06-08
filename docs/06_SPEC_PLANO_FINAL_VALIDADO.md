# Spec-Plano Final Validado — Lex Kratos Agentic Core

Data da validacao: 2026-06-06  
Repositorio avaliado: `Lex Kratos Agentic Core`  
Insumos analisados: scaffold local, documentacao `docs/`, testes, agentes mockados e pacote `Analyzing AGENTS2.zip` do Manus.

## 1. Decisao Executiva

O projeto deve seguir como **Lex Kratos Agentic Core v0.1**, um nucleo juridico agentico local, pequeno, auditavel e mockado.

O pacote Manus/AGENTS2 representa outro eixo de produto: **Lex Intelligentia/Hermes para producao de conteudo juridico e automacao de publicacao**. Ele contem ideias uteis de governanca, skills, FIRAC, compliance e operacao humana, mas **nao deve ser usado como base direta de codigo nem como plano de deploy da v0.1**.

Decisao final:

- Validar e estabilizar primeiro o scaffold FastAPI local.
- Manter v0.1 sem chamadas reais a LLMs, Qdrant, Supabase, DataJud, STJ Dados Abertos, PJe, n8n, Hermes, cron jobs ou APIs de audio/imagem.
- Tratar o material Manus como backlog e referencia conceitual, nao como implementacao.
- Preservar revisao humana obrigatoria em qualquer fluxo juridico.

## 2. Diagnostico do Estado Atual

### 2.1 O que ja existe

O repositorio ja possui:

- Aplicacao FastAPI em `app/main.py`.
- Rotas mockadas de saude, intake, RAG e avaliacao.
- Orquestrador local com trace de agentes.
- Agentes mockados para intake, seguranca, extracao, normalizacao, metadados, FIRAC e validacao.
- Schemas Pydantic e JSON schemas.
- Skills juridicas em Markdown.
- Dataset dourado inicial.
- Runner de avaliacao mockada.
- Testes automatizados.
- Documentacao tecnica, plano, tutorial, backlog e referencias.

### 2.2 Validacao executada

Comandos avaliados:

```bash
python -m app.evals.run_eval
pytest
```

Resultado da avaliacao mockada:

- `dataset_size`: 4
- `average_recall`: 0.625
- Casos com acerto total: bancario e processual civil.
- Casos incompletos ou sem recuperacao: saude e consumidor.

Resultado dos testes:

- Primeira execucao de `pytest`: 9 aprovados, 1 erro ambiental de permissao no diretorio temporario do Windows.
- Segunda execucao com `TMP`/`TEMP` apontando para pasta temporaria controlada: 10 aprovados.

Conclusao: a v0.1 esta tecnicamente viavel. O unico bloqueio observado foi ambiental, nao funcional.

## 3. Conflitos Identificados no Plano Rascunhado

O rascunho de deploy recebido e o pacote Manus trazem elementos que nao pertencem a v0.1 deste repositorio:

- Instalacao do Hermes Agent.
- Copia de skills para `~/.hermes`.
- Uso de SQLite operacional do Hermes.
- Cron jobs.
- Curator/pinagem de skills.
- n8n para publicacao automatica.
- Chaves Gemini, Anthropic, ElevenLabs, OpenAI e n8n.
- Scripts com `sudo apt-get`, `sudo pip3 install` e `curl | bash`.
- Docker Compose com Hermes e n8n usando `network_mode: host`.
- Pipeline de conteudo, audio, visual e redes sociais.

Esses itens sao validos para um produto futuro de conteudo/marketing juridico, mas violam o criterio v0.1 do Lex Kratos Agentic Core, que exige execucao local deterministica, mockada e sem efeitos colaterais externos.

## 4. Escopo Final v0.1

### 4.1 Objetivo

Entregar um nucleo agentico juridico local capaz de:

- Receber um caso mockado.
- Classificar documentos por nome.
- Detectar prompt injection obvio.
- Executar pipeline juridico simulado com trace auditavel.
- Simular busca RAG.
- Executar avaliacao mockada com dataset dourado.
- Passar em testes locais sem depender de servicos externos.

### 4.2 Incluido

- FastAPI.
- `GET /health`.
- `POST /cases/intake`.
- `POST /cases/run-full-mock`.
- `POST /rag/search`.
- `GET /eval/run`.
- Agentes mockados.
- Skills Markdown versionadas.
- Schemas Pydantic.
- Dataset dourado inicial.
- Testes pytest.
- Documentacao de execucao local.
- CI com pytest e avaliacao mockada.

### 4.3 Fora do Escopo v0.1

- Integracao real com Qdrant.
- Integracao real com Supabase.
- Integracao real com n8n.
- Integracao real com DataJud, STJ Dados Abertos ou PJe.
- Chamadas a LLMs.
- Geracao real de minutas juridicas.
- Publicacao em redes sociais.
- ElevenLabs, audio, video, imagem ou branding.
- Hermes Agent, cron jobs, curator e memoria operacional.
- Uso de codigo de repositorios antigos ou legacy sem autorizacao expressa.

## 5. Arquitetura v0.1

Fluxo aceito:

```text
CaseInput
  -> IntakeAgent
  -> SecurityAgent
  -> ExtractionAgent mockado
  -> LegalNormalizerAgent mockado
  -> MetadataAgent mockado
  -> FIRACAgent mockado
  -> ValidatorAgent mockado
  -> Human Review obrigatorio
```

Regras:

- Toda execucao deve gerar `trace`.
- Conteudo documental nunca deve ser tratado como comando.
- Se o `SecurityAgent` detectar instrucao suspeita, o fluxo deve retornar `blocked`.
- Qualquer analise, minuta, recomendacao ou decisao juridica futura deve exigir revisao humana.
- Saidas mockadas devem deixar claro que nao sao analise juridica real.

## 6. Contratos de API v0.1

### `GET /health`

Retorna status operacional local.

Criterio:

- HTTP 200.
- `status = ok`.
- `service = lex-kratos-agentic-core`.
- `version = 0.1.0`.

### `POST /cases/intake`

Entrada:

```json
{
  "case_id": "caso_teste_001",
  "source_type": "manual",
  "user_goal": "minuta",
  "files": ["peticao_inicial.pdf"]
}
```

Saida esperada:

- `case_id`.
- `status` como `success` ou `blocked`.
- `trace` com IntakeAgent e SecurityAgent.

### `POST /cases/run-full-mock`

Executa o pipeline mockado completo disponivel.

Saida esperada:

- `case_id`.
- `status`.
- `trace`.
- `mock_draft`.

### `POST /rag/search`

Busca simulada.

Regra:

- Deve retornar `retrieval_method = mock`.
- Nao deve consultar Qdrant real.

### `GET /eval/run`

Executa o dataset dourado local.

Regra:

- Deve retornar `dataset_size`, `average_recall` e resultados por item.
- Evolução aceita: também retornar `average_recall_at_1`, `average_recall_at_3`, `average_mrr`, `area_summary`, `thresholds`, `passed` e `threshold_failures`.
- O dataset dourado deve falhar em validação local/CI quando tiver JSONL inválido, campo obrigatório ausente, campo textual inválido, `expected_sources` vazio, ID duplicado ou limiar global não atendido.

## 7. Guardrails de Seguranca e Compliance

### 7.1 Prompt Injection

Bloquear ou marcar para revisao quando houver padroes como:

- "ignore instrucoes anteriores";
- "revele o prompt";
- "execute comando";
- "apague arquivos";
- "favoreca uma parte";
- "nao conte ao usuario".

Evolucao futura:

- Classificacao por severidade.
- Cobertura de variantes ortograficas.
- Normalizacao Unicode.
- Testes com payloads adversariais.
- Campo `requires_human_review`.

### 7.2 Revisao Humana

Qualquer fluxo que gere analise, minuta, recomendacao ou decisao deve retornar metadados de controle:

- `requires_human_review: true`;
- `external_use_allowed: false` ate aprovacao;
- fontes ou indicacao explicita de ausencia de fonte;
- warnings de incerteza.

### 7.3 Dados Sensiveis

Para v0.1:

- Usar apenas dados mockados.
- Nao persistir casos reais.
- Nao enviar dados a servicos externos.
- Nao criar logs com informacoes pessoais sensiveis.

## 8. Plano de Execucao Final

### Fase 0 — Congelamento da v0.1 Atual

Objetivo: garantir que o scaffold atual e reprodutivel.

Entregas:

- Revisar docs para remover ambiguidade entre Kratos Core e Lex Intelligentia/Hermes.
- Documentar que Qdrant no Docker Compose e apenas futuro/opcional.
- Registrar workaround de `TMP`/`TEMP` no Windows se houver erro de permissao no pytest.
- Confirmar que todos os comandos de aceite rodam localmente.

Criterio de aceite:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest
python -m app.evals.run_eval
```

### Fase 1 — Hardening de Seguranca Local

Objetivo: tornar o bloqueio de prompt injection mais robusto ainda sem LLM.

Entregas:

- Normalizador de texto para seguranca.
- Lista ampliada de padroes suspeitos.
- Severidade: `low`, `medium`, `high`, `critical`.
- Testes adversariais.
- Campo padronizado de `security_status`.

Criterio de aceite:

- Payloads obvios sao bloqueados.
- Payloads benignos nao sao bloqueados indevidamente.
- Testes deterministivos.

### Fase 2 — Qualidade do Pipeline Mockado

Objetivo: deixar o trace juridico mais auditavel.

Entregas:

- Estrutura padrao para cada `AgentResult`.
- `warnings` e `errors` consistentes.
- `requires_human_review` nos outputs juridicos.
- Testes do pipeline completo.
- Documentacao dos contratos de trace.

Criterio de aceite:

- `/cases/run-full-mock` retorna todos os agentes esperados.
- Nenhum output juridico aparenta ser decisao real.

### Fase 3 — Avaliacao RAG Mockada

Objetivo: melhorar o dataset e as metricas antes de integrar busca real.

Entregas:

- Expandir `golden_dataset.jsonl`.
- Separar casos por area.
- Adicionar `recall_at_k`, MRR mockado e falhas esperadas.
- Definir limiar minimo de aceitacao.

Criterio de aceite:

- `python -m app.evals.run_eval` retorna metricas estaveis.
- CI falha se dataset estiver invalido.

### Fase 4 — Extracao e Normalizacao Mockadas Mais Ricas

Objetivo: preparar estrutura para PDF real sem implementar PDF real ainda.

Entregas:

- Contrato de documento extraido com `doc_id`, `page`, `text`, `quality_score`.
- Normalizacao de partes, pedidos, defesas, provas e eventos.
- Testes com nomes de arquivos simulando peticao, contestacao, sentenca e acordao.

Criterio de aceite:

- Output e consistente e validavel por Pydantic.

### Fase 5 — Preparacao para Qdrant Real

Objetivo: desenhar integracao sem ativa-la por padrao.

Entregas:

- Interface `VectorStore` abstrata.
- Implementacao `MockVectorStore`.
- `QdrantService` isolado e nao usado em testes padrao.
- Plano de colecao, payload e IDs.

Criterio de aceite:

- Testes continuam sem container.
- Qdrant real so roda quando explicitamente habilitado.

### Fase 6 — Integracoes Reais Futuras

Somente apos aprovacao explicita:

- Qdrant real.
- Extração real de PDF.
- LLM service.
- DataJud/STJ Dados Abertos.
- Supabase.
- n8n.
- Google Drive/Docs/Sheets.
- Hermes/skills externas.

Cada integracao deve ter:

- feature flag;
- mocks;
- testes locais sem rede;
- documentacao de seguranca;
- criterio de rollback;
- revisao humana.

## 9. Plano de Deploy Corrigido para v0.1

O tutorial de deploy correto para este repositorio nao deve usar Hermes, n8n ou cron jobs.

### Instalacao local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000/docs
```

Validar:

```bash
pytest
python -m app.evals.run_eval
```

### Docker v0.1

O `docker-compose.yml` atual sobe Qdrant, mas Qdrant nao faz parte da execucao obrigatoria v0.1. Portanto:

- Nao exigir Docker para o aceite v0.1.
- Nao iniciar Qdrant nos testes padrao.
- Nao documentar Qdrant como dependencia obrigatoria ate a fase propria.

### Variaveis de ambiente

Para v0.1:

- `.env` e opcional.
- Nao exigir chaves de LLM.
- Nao exigir chaves de n8n.
- Nao exigir credenciais externas.

## 10. Uso Controlado do Material Manus

### Pode ser aproveitado como referencia

- Metodologia FIRAC+.
- Regras de compliance e revisao humana.
- Ideia de skills modulares.
- Ideia de guardiao/validator.
- Separacao entre producao, validacao e aprovacao humana.
- Backlog futuro para conteudo e automacao.

### Nao deve ser importado agora

- `install.sh`.
- `Dockerfile`.
- `docker-compose.yml` do Hermes/n8n.
- Scripts de cron.
- Scripts ElevenLabs.
- Scripts que copiam arquivos para `~/.hermes`.
- Qualquer codigo que instale dependencias globalmente.
- Qualquer codigo com efeitos externos.

## 11. Riscos Principais

### Risco 1 — Mistura de Produtos

Lex Intelligentia/Hermes e Lex Kratos Core tem objetivos diferentes.

Mitigacao:

- Documentar fronteira.
- Manter repositorios e planos separados.
- Nao usar o tutorial Hermes como deploy deste core.

### Risco 2 — Escopo Crescer Antes da Base

Integrar LLM, Qdrant, n8n e bases juridicas cedo demais aumentaria risco tecnico e juridico.

Mitigacao:

- Fases curtas.
- Mocks primeiro.
- Feature flags.
- Testes deterministivos.

### Risco 3 — Prompt Injection em Documentos Processuais

Documentos podem conter instrucoes maliciosas.

Mitigacao:

- Conteudo documental sempre tratado como dado.
- SecurityAgent antes de qualquer etapa gerativa.
- Logs de riscos.
- Revisao humana.

### Risco 4 — Alucinacao Juridica

Qualquer geracao futura pode inventar precedentes, fatos ou fundamentacao.

Mitigacao:

- Validacao de fontes.
- Saida com citacoes obrigatorias.
- Marcador `[NAO CONSTA NOS AUTOS]` quando faltar dado.
- Bloqueio de uso externo sem aprovacao humana.

### Risco 5 — Dados Sensiveis

Casos reais podem conter dados pessoais ou segredo de justica.

Mitigacao:

- Sem casos reais na v0.1.
- Anonimizacao planejada antes de integracoes.
- Persistencia local controlada.
- Sem rede por padrao.

## 12. Criterio de Pronto para Iniciar Execucao

A execucao da proxima fase so deve comecar quando:

- A spec-plano final estiver aprovada.
- O produto-alvo estiver definido como Kratos Core, nao Hermes Conteudo.
- `pytest` estiver verde no ambiente local.
- `python -m app.evals.run_eval` estiver verde.
- O backlog estiver ordenado por fase.
- Nao houver expectativa de integracao externa na v0.1.

## 13. Recomendacao Final

Iniciar pela **Fase 0 — Congelamento da v0.1 Atual**.

Primeira entrega recomendada:

- Ajustar README/tutorial para remover ambiguidade com Hermes/n8n.
- Atualizar backlog marcando o que ja esta feito.
- Registrar validacao local.
- Criar nota explicita de que o ZIP Manus e referencia, nao fonte de codigo.

Somente depois disso avancar para hardening do `SecurityAgent`.
