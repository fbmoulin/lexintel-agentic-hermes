# Richer Chunking Design Spec

> **Status:** Approved
> **Date:** 2026-06-15
> **Baseline:** master @ `d261e40`, 77 tests, v0.3

## Summary

Implementar chunking estrutural jurídico com fallback para chunking por parágrafo. O sistema detecta seções estruturais em documentos jurídicos (RELATÓRIO, FUNDAMENTAÇÃO, DISPOSITIVO, etc.) e cria chunks semanticamente coerentes. Quando marcadores não são detectáveis, aplica fallback de parágrafo com limite de tokens.

## Goals

1. **Chunking estrutural** — detectar e dividir por seções jurídicas (sentença, acórdão, petição, contestação)
2. **Fallback robusto** — chunking por parágrafo com agregação/split baseado em tokens
3. **Extractor plugável** — interface para extração real de PDF no futuro
4. **Metadados de acórdão** — extrair órgão julgador, relator, número, data de publicação
5. **Retrocompatibilidade** — manter função `chunk_extracted_text()` existente

## Non-Goals

- Extração real de PDF (futuro — só interface preparada)
- OCR de documentos escaneados
- Chunking semântico com embeddings
- Religar eval ao novo chunking (escopo separado)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         app/services/                                │
├─────────────────────────────────────────────────────────────────────┤
│  extraction.py (NOVO)                                                │
│  ├── Extractor(Protocol)     # interface para extração              │
│  └── MockExtractor           # texto estruturado por doc_type       │
│                                                                      │
│  markers.py (NOVO)                                                   │
│  ├── STRUCTURAL_MARKERS      # regex patterns por doc_type          │
│  ├── detect_sections()       # retorna List[DetectedSection] | None │
│  └── extract_acordao_metadata()  # metadados específicos            │
│                                                                      │
│  chunking.py (MODIFICADO)                                           │
│  ├── Chunker(Protocol)       # interface para chunking              │
│  ├── StructuralChunker       # detecta seções jurídicas             │
│  ├── ParagraphChunker        # fallback com limite de tokens        │
│  └── get_chunker()           # factory que escolhe estratégia       │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. ExtractionAgent → Extractor.extract(file_path, doc_type)
2. Extractor → ExtractedDocument (texto real ou mock)
3. IndexingAgent → get_chunker(text, doc_type)
4. Factory detecta marcadores:
   - SIM → StructuralChunker
   - NÃO → ParagraphChunker
5. Chunker.chunk() → List[LegalChunk]
6. Chunks indexados no VectorStore
```

---

## Structural Markers

### Patterns por Tipo Documental

| Tipo | Seções Detectadas |
|------|-------------------|
| **sentenca** | RELATÓRIO, FUNDAMENTAÇÃO, DISPOSITIVO |
| **acordao** | EMENTA, RELATÓRIO, VOTO, DISPOSITIVO/ACÓRDÃO |
| **peticao_inicial** | DOS FATOS, DO DIREITO, DOS PEDIDOS |
| **contestacao** | DAS PRELIMINARES, DO MÉRITO, DOS PEDIDOS |

### Regex Patterns

```python
STRUCTURAL_MARKERS = {
    "sentenca": [
        ("relatório", r"^\s*R\s*E\s*L\s*A\s*T\s*Ó\s*R\s*I\s*O\s*$"),
        ("fundamentação", r"^\s*(FUNDAMENTA[ÇC][ÃA]O|MOTIVA[ÇC][ÃA]O)\s*$"),
        ("dispositivo", r"^\s*DISPOSITIVO\s*$"),
    ],
    "acordao": [
        ("ementa", r"^\s*EMENTA\s*:?\s*$"),
        ("relatório", r"^\s*R\s*E\s*L\s*A\s*T\s*Ó\s*R\s*I\s*O\s*$"),
        ("voto", r"^\s*V\s*O\s*T\s*O\s*$"),
        ("dispositivo", r"^\s*(DISPOSITIVO|ACÓRDÃO)\s*$"),
    ],
    "peticao_inicial": [
        ("fatos", r"^\s*(DOS?\s+FATOS?|DA\s+NARRATIVA)\s*$"),
        ("direito", r"^\s*(DO\s+DIREITO|DOS?\s+FUNDAMENTOS?)\s*$"),
        ("pedidos", r"^\s*(DOS?\s+PEDIDOS?|DO\s+REQUERIMENTO)\s*$"),
    ],
    "contestacao": [
        ("preliminares", r"^\s*(DAS?\s+PRELIMINARES?|PRELIMINARMENTE)\s*$"),
        ("merito", r"^\s*(DO\s+M[ÉE]RITO|NO\s+M[ÉE]RITO)\s*$"),
        ("pedidos", r"^\s*(DOS?\s+PEDIDOS?|DO\s+REQUERIMENTO)\s*$"),
    ],
}
```

### Metadados de Acórdão

Extraídos do cabeçalho (primeiros 2000 chars):
- `orgao_julgador` — TURMA, CÂMARA, SEÇÃO, PLENO
- `relator` — RELATOR: ...
- `numero` — PROCESSO/RECURSO Nº ...
- `tipo_recurso` — APELAÇÃO, AGRAVO, EMBARGOS
- `data_publicacao` — DJe de DD/MM/YYYY

---

## Chunker Implementations

### StructuralChunker

- Usa `detect_sections()` para encontrar seções
- Se seção > `max_tokens` (800), subdivide com `ParagraphChunker`
- Cada chunk recebe `unit_type` da seção (relatório, fundamentação, etc.)
- Metadados de acórdão anexados a todos os chunks
- `chunking_strategy: "structural_v0.2"`

### ParagraphChunker (Fallback)

Parâmetros:
| Param | Valor | Comportamento |
|-------|-------|---------------|
| `target_tokens` | 500 | Tamanho alvo |
| `min_tokens` | 200 | Agrega parágrafos pequenos |
| `max_tokens` | 800 | Split em sentenças se exceder |
| `overlap_sentences` | 1 | Última sentença repete no próximo |

Comportamento:
1. Parágrafos < 200 tokens: agrega até atingir ~400
2. Parágrafos 200-800 tokens: chunk único
3. Parágrafos > 800 tokens: split em sentenças
4. Overlap: última sentença prefixada com `[...]`
5. `chunking_strategy: "paragraph_v0.2"`

### Factory: get_chunker()

```python
def get_chunker(text: str, doc_type: str) -> Chunker:
    sections = detect_sections(text, doc_type)
    if sections and len(sections) >= 2:
        return StructuralChunker()
    return ParagraphChunker()
```

---

## Extractor Protocol

### Interface

```python
@dataclass
class ExtractedDocument:
    text: str
    doc_type: str
    doc_id: str
    file_path: str | None
    page_count: int
    quality_score: float
    extraction_method: str
    metadata: dict

class Extractor(Protocol):
    def extract(self, file_path: str, doc_type: str | None = None) -> ExtractedDocument: ...
    def supports(self, file_path: str) -> bool: ...
```

### MockExtractor

- Retorna texto com estrutura jurídica realista por `doc_type`
- Templates incluem marcadores detectáveis (RELATÓRIO, FUNDAMENTAÇÃO, etc.)
- Infere `doc_type` do nome do arquivo se não fornecido
- `extraction_method: "mock"`, `quality_score: 0.95`

---

## Integration

### Files Modified

| Arquivo | Ação |
|---------|------|
| `app/services/extraction.py` | **NOVO** |
| `app/services/markers.py` | **NOVO** |
| `app/services/chunking.py` | **MODIFICAR** |
| `app/agents/extraction_agent.py` | **MODIFICAR** |
| `app/agents/indexing_agent.py` | **MODIFICAR** |
| `app/schemas/case.py` | **MODIFICAR** (novos ChunkUnitType) |

### Backward Compatibility

- `chunk_extracted_text()` mantida como wrapper deprecated
- Emite `DeprecationWarning` ao ser chamada
- Internamente usa `get_chunker().chunk()`

### New ChunkUnitType Values

```python
ChunkUnitType = Literal[
    # Existentes
    "pedido", "contestacao", "dispositivo", "ementa", "documento",
    # Novos
    "relatório", "fundamentação", "voto", "fatos", "direito",
    "preliminares", "merito",
]
```

---

## Error Handling

### Graceful Degradation

```
StructuralChunker (seções detectadas)
    ↓ fallback se seção > max_tokens
ParagraphChunker (subdivide seção)
    ↓ fallback se nenhum marcador
ParagraphChunker (texto inteiro)
    ↓ fallback se texto < min_tokens
Chunk único
    ↓ fallback se texto vazio
Lista vazia + warning log
```

### Edge Cases

| Caso | Tratamento |
|------|------------|
| Texto vazio | Retorna `[]`, log warning |
| Texto < min_tokens | Chunk único |
| Marcador no meio de palavra | Não detecta (regex exige `^\s*`) |
| Marcadores fora de ordem | Ordena por posição |
| Seção vazia | Ignora |
| doc_type desconhecido | Fallback ParagraphChunker |

---

## Testing Strategy

### New Test Files

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_markers.py` | 10 | 95%+ |
| `test_chunkers.py` | 12 | 90%+ |
| `test_extraction_service.py` | 6 | 95%+ |
| **Total** | **~32** | |

### Key Test Cases

**Markers:**
- Detecta 3 seções em sentença
- Detecta 4 seções em acórdão
- Retorna None sem marcadores
- Retorna None com apenas 1 marcador
- Extrai metadados de acórdão

**Chunkers:**
- StructuralChunker divide em seções
- Seção grande subdividida com ParagraphChunker
- Acórdão inclui metadados em todos chunks
- ParagraphChunker agrega parágrafos pequenos
- ParagraphChunker split parágrafos grandes
- Overlap entre chunks consecutivos

**Factory:**
- Retorna StructuralChunker com marcadores
- Retorna ParagraphChunker sem marcadores

---

## Risks & Mitigations

| Risco | Mitigação |
|-------|-----------|
| Regex não cobre variações reais | Começar com templates mock, ajustar com PDFs reais |
| Performance em textos grandes | `estimate_tokens()` é O(1); split é O(n) |
| Overlap duplica conteúdo | Apenas 1 sentença (~30-50 tokens), aceitável |
| Breaking change em testes existentes | Wrapper deprecated mantém compatibilidade |

---

## Success Criteria

1. [ ] 77+ testes passando (baseline) + ~32 novos = ~109
2. [ ] `get_chunker()` seleciona corretamente Structural vs Paragraph
3. [ ] Sentença mock dividida em 3 chunks (relatório, fundamentação, dispositivo)
4. [ ] Acórdão mock inclui metadados extraídos
5. [ ] Texto sem marcadores usa ParagraphChunker
6. [ ] Retrocompatibilidade: `chunk_extracted_text()` funciona com warning
7. [ ] CI verde (ruff, mypy, pytest, eval)
