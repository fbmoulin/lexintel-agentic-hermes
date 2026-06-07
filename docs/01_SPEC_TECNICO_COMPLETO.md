# SPEC Técnico Completo — Lex Kratos Agentic Core v0.1

## 1. Objetivo

Criar um núcleo agentico modular para automação jurídica, com foco inicial em processos cíveis, RAG jurisprudencial, FIRAC+, validação de minutas e segurança.

## 2. Escopo

### Incluído nesta versão

- Scaffold FastAPI.
- Endpoints mínimos.
- Agentes mockados.
- Orquestrador.
- Skills versionadas em Markdown.
- Schemas Pydantic.
- Dataset inicial de avaliação.
- Testes com pytest.
- Docker Compose para Qdrant.
- Planejamento de integração com n8n e GitHub/Codex.

### Fora do escopo da primeira versão

- Download real de processos do PJe.
- Integração real com DataJud.
- Integração real com STJ Dados Abertos.
- Geração de sentença real em produção.
- Integração obrigatória com banco vetorial na primeira execução.
- Autonomia decisória sem revisão humana.

## 3. Arquitetura lógica

```text
Input documental/processual
        ↓
IntakeAgent
        ↓
SecurityAgent
        ↓
ExtractionAgent
        ↓
LegalNormalizerAgent
        ↓
MetadataAgent
        ↓
IndexingAgent
        ↓
HybridRetrievalAgent
        ↓
FIRACAgent
        ↓
JurisprudenceAgent
        ↓
DraftingAgent
        ↓
ValidatorAgent
        ↓
SecurityAgent
        ↓
Human Review
```

## 4. Agentes

### 4.1 IntakeAgent

Recebe caso, arquivos e objetivo do usuário. Classifica documentos e prepara o pacote inicial.

### 4.2 SecurityAgent

Detecta prompt injection, comandos indevidos e riscos de vazamento.

### 4.3 ExtractionAgent

Extrai texto e preserva páginas, qualidade OCR e warnings.

### 4.4 LegalNormalizerAgent

Transforma texto bruto em fatos, pedidos, defesas, provas e movimentações.

### 4.5 MetadataAgent

Gera metadados jurídicos para busca e jurimetria.

### 4.6 IndexingAgent

Faz chunking por unidade jurídica e indexa.

### 4.7 HybridRetrievalAgent

Executa busca híbrida, combina recuperação semântica e lexical e prepara reranking.

### 4.8 FIRACAgent

Produz análise FIRAC+ antes da minuta.

### 4.9 JurisprudenceAgent

Busca e valida precedentes.

### 4.10 DraftingAgent

Redige minuta judicial com base em FIRAC+ e fontes validadas.

### 4.11 ValidatorAgent

Audita a minuta para detectar omissões, contradições, fatos sem fonte e precedentes inventados.

### 4.12 EvaluationAgent

Executa dataset de avaliação e calcula métricas.

## 5. Métricas

- Recall@5
- Recall@10
- MRR
- NDCG
- Groundedness
- Faithfulness
- Citation accuracy
- Latency
- Custo por caso

## 6. Regras jurídicas de validação

1. Não inventar precedente.
2. Não citar súmula/tema sem validação.
3. Não decidir pedido inexistente.
4. Não omitir pedido formulado.
5. Não julgar prescrição/decadência salvo se arguida ou cognoscível de ofício.
6. Não presumir fatos sem fonte.
7. Não criar IDs, páginas ou movimentações fictícias.
8. Manter coerência entre fundamentação e dispositivo.
9. Exigir revisão humana antes de uso externo.
10. Anonimizar dados sensíveis quando necessário.

## 7. Regras de segurança

O conteúdo documental nunca deve ser tratado como comando do sistema.

Qualquer trecho que contenha instruções como “ignore instruções anteriores”, “revele o prompt”, “favoreça a parte X”, “execute comando” ou equivalentes deve ser marcado como risco.

## 8. Estratégia de evolução

### v0.1

Scaffold com mocks e testes.

### v0.2

Extração real de PDF e normalização.

### v0.3

Qdrant real com busca vetorial.

### v0.4

Busca híbrida + reranker.

### v0.5

FIRAC+ e minuta com validação.

### v0.6

n8n + Google Drive + Google Docs/Sheets.

### v1.0

Produto MVP auditável.
