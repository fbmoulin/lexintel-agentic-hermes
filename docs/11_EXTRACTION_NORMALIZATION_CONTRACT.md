# Contrato de Extração e Normalização Mockadas

Este contrato descreve a Fase 5 do Lex Kratos Agentic Core v0.1.

A fase permanece local, mockada e sem extração real de PDF, OCR, LLM, Qdrant, DataJud ou STJ Dados Abertos.

## Extração

O texto mockado é produzido por um `MockExtractor` (em `app/services/extraction.py`), por trás da interface `Extractor` (protocolo `extract()`/`supports()` + modelo Pydantic `ExtractedDocument`) — uma interface preparada para extração real de PDF em fase futura, sem alterar o restante do pipeline. Os templates do `MockExtractor` são **marker-rich** (contêm cabeçalhos de seção como RELATÓRIO/FUNDAMENTAÇÃO/DISPOSITIVO), de modo que o chunking estrutural (ver `docs/12`) seja exercitado ponta a ponta. O `extraction_method` permanece `mock_filename_template`.

O `ExtractionAgent` recebe documentos detectados pelo `IntakeAgent`, consome o texto do extrator e retorna:

- `extraction_schema_version`
- `extracted_text`
- `quality_summary`
- `requires_human_review`
- `external_use_allowed`

Cada item de `extracted_text` segue o schema Pydantic `ExtractedText`:

- `doc_id`
- `file_path`
- `doc_type`
- `page`
- `text`
- `quality_score`
- `extraction_method`
- `warnings`

Tipos documentais aceitos:

- `peticao_inicial`
- `contestacao`
- `sentenca`
- `acordao`
- `unknown`

Documento `unknown` recebe `quality_score` abaixo de `0.70`, marca `automation_allowed = false` no resumo de qualidade e exige revisão humana. Lista vazia de documentos também bloqueia automação e exige revisão.

## Normalização

O `LegalNormalizerAgent` retorna um `NormalizedCase` validado por Pydantic com:

- `parties`
- `facts`
- `claims`
- `cause_of_action`
- `preliminary_issues`
- `merit_prejudicials`
- `defenses`
- `evidence`
- `procedural_events`
- `legal_issues`
- `normalization_warnings`

A normalização é determinística e baseada apenas no tipo documental mockado.

## Metadados

O `MetadataAgent` retorna `CaseMetadata` validado por Pydantic.

Campos reais indisponíveis continuam `null`. Campos inferíveis no mock, como `document_types`, `document_count`, `has_petition`, `has_defense`, `has_decision` e `has_appeal_decision`, são preenchidos localmente.

## Guardrails

- Saídas continuam `external_use_allowed = false`.
- Documento de baixa qualidade não autoriza automação.
- Nenhuma saída representa análise jurídica real.
- Revisão humana continua obrigatória antes de qualquer uso jurídico externo.
