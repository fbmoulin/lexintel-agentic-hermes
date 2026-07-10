# Richer Chunking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structural legal-section chunking (RELATÓRIO/FUNDAMENTAÇÃO/DISPOSITIVO, EMENTA/VOTO, DOS FATOS/DO DIREITO, DAS PRELIMINARES/DO MÉRITO) with a token-budgeted paragraph-chunker fallback and a pluggable `Extractor` interface — replacing today's one-chunk-per-document behavior.

**Architecture:** A `markers.py` detects section headers per `doc_type`; `chunking.py` gains a `Chunker` protocol with `StructuralChunker` (one chunk per detected section, subdividing oversized sections via the paragraph fallback) and `ParagraphChunker` (aggregate/split by token budget with 1-sentence overlap); a `get_chunker()` factory picks structural when ≥2 sections are found; a new `extraction.py` exposes an `Extractor` protocol + marker-rich `MockExtractor`. The pipeline's mock text is upgraded so the structural path fires end-to-end. Backward compat is preserved via a deprecated `chunk_extracted_text()` wrapper.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, pytest, ruff (`E,F,I`), mypy (`app` only). No new runtime deps.

---

## Decisions locked before Task 1 (deviations from the 2026-06-15 spec)

The spec baseline (`d261e40`, 77 tests) has drifted (now `b8a684d`, 86 tests: real Qdrant, `index_status`, best-effort indexing, removed `"failed"` status). These decisions resolve conflicts the spec predates. **They are binding — do not re-derive.**

- **D1 — Unit-type names are UNACCENTED (house style).** The schema already has `"relatorio"`, `"fundamentos"`, `"voto"`, `"ementa"`, `"dispositivo"`, `"pedido"`, `"contestacao"`. Reuse them. The spec's accented `"relatório"`/`"fundamentação"` map to existing `"relatorio"`/`"fundamentos"`. Only **four genuinely new** values are added: `"fatos"`, `"direito"`, `"preliminares"`, `"merito"` (all unaccented). The `pedidos` section maps to the existing `"pedido"`.
- **D2 — `ExtractedDocument` is a Pydantic `BaseModel`, NOT `@dataclass`.** The repo has zero dataclasses; the data flow is `.model_dump()` dicts consumed via `.get()`. A dataclass would be the only one and needs conversion glue.
- **D3 — `ParagraphChunker.chunk()` takes `unit_type` as a parameter** (does not derive it from `doc_type`). It has two callers: the top-level fallback (unit_type from the doc_type map) and structural-section subdivision (unit_type = the section's type). Deriving from `doc_type` would mislabel a subdivided `fundamentos` section as `dispositivo`.
- **D4 — The pipeline mock text becomes marker-rich** (`MockExtractor` templates), so the structural path fires end-to-end (spec success criterion #3 requires it). Blast radius is only the two pipeline `chunk_count` assertions (recomputed below); no test asserts mock text verbatim.
- **D5 — DISSOLVED.** `ExtractionAgent` keeps emitting `ExtractedText` with `extraction_method="mock_filename_template"` unchanged and consumes only `extractor.extract(...).text`. So `ExtractedText.extraction_method`'s closed `Literal` need NOT be widened, and quality-score tests (`0.92`/`0.68`) stay green.
- **R1 — `build_chunk_id` gains a CONDITIONAL ordinal.** Today's id is `chunk_{case}_{doc}_p{page}_{unit}`; two chunks from the same `(doc, page, unit)` collide, and `MockVectorStore.upsert` dedups by `chunk_id` → silent chunk loss. Append `_{ordinal}` **only when a `(doc, page, unit)` group yields >1 chunk**, so single-chunk ids stay byte-identical (preserves the exact-id assertions in `test_indexing_vector_store.py`).
- **Verified safe:** eval is import-decoupled from the chunker (`run_eval` seeds from `golden_corpus.jsonl`) → eval numbers cannot move. `gen_schemas` targets only `ValidationResult`/`RetrievedContext` → new `ChunkUnitType` values and new models cause **no schema drift**. `_ALLOWED_UNIT_TYPES` + `IndexingSummary.chunk_unit_types` widen automatically → **no `indexing_agent` edit needed** for new unit types. No `filterwarnings` config → the `DeprecationWarning` wrapper is CI-safe. mypy checks `app/` only.

### Section → unit_type map (canonical; used by markers.py and templates)

| doc_type | sections (in order) → unit_type |
|---|---|
| `sentenca` | relatório→`relatorio`, fundamentação→`fundamentos`, dispositivo→`dispositivo` |
| `acordao` | ementa→`ementa`, relatório→`relatorio`, voto→`voto`, dispositivo→`dispositivo` |
| `peticao_inicial` | fatos→`fatos`, direito→`direito`, pedidos→`pedido` |
| `contestacao` | preliminares→`preliminares`, merito→`merito`, pedidos→`pedido` |

### Deterministic chunk counts (per-template section counts drive every count assertion)

Each template has one chunk per section (bodies kept `< max_tokens=800`, so no sub-split): **peticao=3, contestacao=3, sentenca=3, acordao=4, unknown=1** (no markers → ParagraphChunker → single chunk).
- `test_structured_extraction_normalization.py:179-180` input `[peticao, contestacao, sentenca, acordao]` → **13**.
- `test_api_routes.py:215-216` input `[peticao_inicial, sentenca]` → **6**.
- `test_indexing_vector_store.py` uses the marker-free `EXTRACTED_TEXT` fixture → ParagraphChunker single chunk per doc → **counts/ids/unit_types UNCHANGED**; only its `chunking_strategy` string changes (`legal_unit_mock_v0.1` → `paragraph_v0.2`).

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `app/schemas/case.py` | Modify | Add 4 `ChunkUnitType` values |
| `app/services/markers.py` | **New** | `STRUCTURAL_MARKERS`, `DetectedSection`, `detect_sections()`, `extract_acordao_metadata()`, `SECTION_UNIT_TYPE` map |
| `app/services/chunking.py` | Modify | `estimate_tokens()`, `split_sentences()`, `Chunker` protocol, `ParagraphChunker`, `StructuralChunker`, `get_chunker()`, `build_chunk_id` (ordinal), `build_chunks()`, deprecated `chunk_extracted_text()` wrapper |
| `app/services/extraction.py` | **New** | `Extractor` protocol, `ExtractedDocument` (Pydantic), `MockExtractor` (marker-rich templates) |
| `app/agents/extraction_agent.py` | Modify | Inject `MockExtractor`; consume `.text` |
| `app/agents/indexing_agent.py` | Modify | Call `build_chunks()` (not the deprecated wrapper) |
| `tests/test_markers.py` | **New** | ~10 tests |
| `tests/test_chunkers.py` | **New** | ~12 tests |
| `tests/test_extraction_service.py` | **New** | ~6 tests |
| `tests/test_indexing_vector_store.py` | Modify | Update `chunking_strategy` assertion (:50) |
| `tests/test_structured_extraction_normalization.py` | Modify | `chunk_count`/`indexed_count` 4 → 13 (:179-180) |
| `tests/test_api_routes.py` | Modify | `chunk_count`/`indexed_count` 2 → 6 (:215-216) |

**Commit rhythm:** one commit per task. Run the full gate (`pytest -q`, `ruff check app tests scripts integrations`, `ruff format --check ...`, `mypy app`, `python -m app.evals.run_eval`) before Tasks 11–13 (the integration tasks) since those touch the pipeline.

---

### Task 1: Add the four new ChunkUnitType values

**Files:**
- Modify: `app/schemas/case.py` (the `ChunkUnitType = Literal[...]` block)
- Test: `tests/test_chunkers.py` (new file — first test lives here)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chunkers.py
import pytest
from pydantic import ValidationError

from app.schemas.case import LegalChunk


@pytest.mark.parametrize("unit_type", ["fatos", "direito", "preliminares", "merito"])
def test_legal_chunk_accepts_new_structural_unit_types(unit_type):
    chunk = LegalChunk(
        chunk_id="c1", case_id="caso", doc_id="doc_1",
        unit_type=unit_type, text="x", page_start=1, page_end=1,
    )
    assert chunk.unit_type == unit_type


def test_legal_chunk_rejects_unknown_unit_type():
    with pytest.raises(ValidationError):
        LegalChunk(
            chunk_id="c1", case_id="caso", doc_id="doc_1",
            unit_type="nao_existe", text="x", page_start=1, page_end=1,
        )
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q`
Expected: FAIL — `ValidationError` for `"fatos"` (not yet a valid literal).

- [ ] **Step 3: Add the values**

In `app/schemas/case.py`, extend the `ChunkUnitType` Literal (keep existing members, append the four):

```python
ChunkUnitType = Literal[
    "ementa",
    "relatorio",
    "voto",
    "fundamentos",
    "dispositivo",
    "pedido",
    "contestacao",
    "prova",
    "tese",
    "precedente_citado",
    "documento",
    # Richer-chunking sections (unaccented, house style — see plan D1):
    "fatos",
    "direito",
    "preliminares",
    "merito",
]
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q`
Expected: PASS (3 params + rejection = green).

- [ ] **Step 5: Commit**

```bash
git add app/schemas/case.py tests/test_chunkers.py
git commit -m "feat(chunking): add fatos/direito/preliminares/merito unit types"
```

---

### Task 2: Token estimator + sentence splitter (chunking helpers)

**Files:**
- Modify: `app/services/chunking.py` (add module-level helpers near the top)
- Test: `tests/test_chunkers.py`

**Design:** `estimate_tokens` = whitespace word count (O(1)-ish, deterministic, good enough for budgets). `split_sentences` = dumb split on `.!?` followed by whitespace; keep the terminator with the sentence. Templates deliberately avoid abbreviations (`art.`, `nº`, `STJ.`) so a dumb splitter is correct (see Task 10).

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
from app.services.chunking import estimate_tokens, split_sentences


def test_estimate_tokens_counts_words():
    assert estimate_tokens("um dois tres quatro") == 4
    assert estimate_tokens("   ") == 0


def test_split_sentences_keeps_terminators_and_ignores_trailing_space():
    text = "Primeira frase. Segunda frase! Terceira frase?"
    assert split_sentences(text) == [
        "Primeira frase.",
        "Segunda frase!",
        "Terceira frase?",
    ]


def test_split_sentences_single_sentence_without_terminator():
    assert split_sentences("sem ponto final") == ["sem ponto final"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k "estimate_tokens or split_sentences"`
Expected: FAIL — `ImportError: cannot import name 'estimate_tokens'`.

- [ ] **Step 3: Implement**

Add to the top of `app/services/chunking.py` (below existing imports):

```python
import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def estimate_tokens(text: str) -> int:
    """Cheap deterministic token proxy: whitespace-delimited word count."""
    return len(text.split())


def split_sentences(text: str) -> list[str]:
    """Split on sentence terminators, keeping the terminator with each sentence.

    Deliberately dumb: mock/legal templates avoid abbreviations (art., nº, STJ.)
    so no abbreviation handling is needed. Returns [text] when no boundary found.
    """
    parts = [part.strip() for part in _SENTENCE_BOUNDARY.split(text.strip())]
    return [part for part in parts if part]
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k "estimate_tokens or split_sentences"`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "feat(chunking): add estimate_tokens + split_sentences helpers"
```

---

### Task 3: markers.py — detect_sections()

**Files:**
- Create: `app/services/markers.py`
- Test: `tests/test_markers.py` (new)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_markers.py
from app.services.markers import detect_sections

SENTENCA = (
    "RELATÓRIO\n"
    "Trata-se de acao de indenizacao.\n\n"
    "FUNDAMENTAÇÃO\n"
    "A responsabilidade do banco e objetiva.\n\n"
    "DISPOSITIVO\n"
    "Julgo parcialmente procedentes os pedidos.\n"
)


def test_detects_three_sections_in_sentenca():
    sections = detect_sections(SENTENCA, "sentenca")
    assert [s.unit_type for s in sections] == ["relatorio", "fundamentos", "dispositivo"]
    assert "Trata-se" in sections[0].text
    assert "objetiva" in sections[1].text


def test_returns_none_without_markers():
    assert detect_sections("um paragrafo qualquer sem cabecalhos", "sentenca") is None


def test_returns_none_with_single_marker():
    assert detect_sections("RELATÓRIO\nso um cabecalho aqui", "sentenca") is None


def test_unknown_doc_type_returns_none():
    assert detect_sections(SENTENCA, "algo_desconhecido") is None


def test_marker_mid_line_not_detected():
    # "RELATÓRIO" must be its own line (^\s*...\s*$), not embedded.
    text = "no meio do RELATÓRIO texto\noutra linha DISPOSITIVO aqui"
    assert detect_sections(text, "sentenca") is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_markers.py -q`
Expected: FAIL — module `app.services.markers` does not exist.

- [ ] **Step 3: Implement `app/services/markers.py`**

```python
import re
from dataclasses import dataclass

from app.schemas.case import ChunkUnitType

# (marker-key, compiled line-anchored regex) per doc_type. Spacing tolerant to
# survive PDF letter-spacing (R E L A T Ó R I O). Accents optional in the regex,
# but the emitted unit_type is the UNACCENTED house-style value (plan D1).
_RAW_MARKERS: dict[str, list[tuple[str, str]]] = {
    "sentenca": [
        ("relatorio", r"^\s*R\s*E\s*L\s*A\s*T\s*[ÓO]\s*R\s*I\s*O\s*$"),
        ("fundamentos", r"^\s*(FUNDAMENTA[ÇC][ÃA]O|MOTIVA[ÇC][ÃA]O)\s*$"),
        ("dispositivo", r"^\s*DISPOSITIVO\s*$"),
    ],
    "acordao": [
        ("ementa", r"^\s*EMENTA\s*:?\s*$"),
        ("relatorio", r"^\s*R\s*E\s*L\s*A\s*T\s*[ÓO]\s*R\s*I\s*O\s*$"),
        ("voto", r"^\s*V\s*O\s*T\s*O\s*$"),
        ("dispositivo", r"^\s*(DISPOSITIVO|ACÓRD[ÃA]O)\s*$"),
    ],
    "peticao_inicial": [
        ("fatos", r"^\s*(DOS?\s+FATOS?|DA\s+NARRATIVA)\s*$"),
        ("direito", r"^\s*(DO\s+DIREITO|DOS?\s+FUNDAMENTOS?)\s*$"),
        ("pedido", r"^\s*(DOS?\s+PEDIDOS?|DO\s+REQUERIMENTO)\s*$"),
    ],
    "contestacao": [
        ("preliminares", r"^\s*(DAS?\s+PRELIMINARES?|PRELIMINARMENTE)\s*$"),
        ("merito", r"^\s*(DO\s+M[ÉE]RITO|NO\s+M[ÉE]RITO)\s*$"),
        ("pedido", r"^\s*(DOS?\s+PEDIDOS?|DO\s+REQUERIMENTO)\s*$"),
    ],
}

STRUCTURAL_MARKERS: dict[str, list[tuple[str, re.Pattern]]] = {
    doc_type: [(key, re.compile(pat, re.IGNORECASE | re.MULTILINE)) for key, pat in pairs]
    for doc_type, pairs in _RAW_MARKERS.items()
}


@dataclass
class DetectedSection:
    unit_type: ChunkUnitType
    text: str
    order: int


def detect_sections(text: str, doc_type: str) -> list[DetectedSection] | None:
    """Return ordered sections (>=2) or None when structure is absent/insufficient."""
    markers = STRUCTURAL_MARKERS.get(doc_type)
    if not markers:
        return None

    hits: list[tuple[int, str]] = []  # (start_offset_of_body, unit_type)
    for unit_type, pattern in markers:
        for match in pattern.finditer(text):
            hits.append((match.end(), unit_type))

    if len(hits) < 2:
        return None

    hits.sort(key=lambda h: h[0])
    sections: list[DetectedSection] = []
    for index, (body_start, unit_type) in enumerate(hits):
        body_end = hits[index + 1][0] if index + 1 < len(hits) else len(text)
        # trim the trailing marker line of the NEXT section off this body:
        body = text[body_start:body_end]
        body = re.split(r"\n\s*\S", body)[0] if index + 1 < len(hits) else body
        body = text[body_start:body_end].strip()
        if index + 1 < len(hits):
            # cut the next marker's own line from the tail
            body = body.rsplit("\n", 1)[0].strip() if "\n" in body else body
        if body:
            sections.append(DetectedSection(unit_type=unit_type, text=body, order=index))

    return sections if len(sections) >= 2 else None
```

> **Note for the implementer:** the body-trimming above is fiddly. Simplify to a line-scan if a test fails: iterate `text.splitlines()`, tag each line as a marker (which unit_type) or content, then group content lines under the most recent marker. That is easier to get right than offset math — prefer it if the offset version resists the Task-3 tests. The observable contract is fixed by the tests: sections in document order, `unit_type` per the D1 map, body excludes the marker line, `None` when `< 2` markers.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_markers.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/markers.py tests/test_markers.py
git commit -m "feat(chunking): detect_sections() for legal document structure"
```

---

### Task 4: markers.py — extract_acordao_metadata()

**Files:**
- Modify: `app/services/markers.py`
- Test: `tests/test_markers.py`

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_markers.py
from app.services.markers import extract_acordao_metadata

ACORDAO_HEADER = (
    "TRIBUNAL DE JUSTICA - QUARTA CAMARA CIVEL\n"
    "APELACAO CIVEL Nº 0001234-56.2026.8.08.0001\n"
    "RELATOR: Desembargador Fulano de Tal\n"
    "Publicado no DJe de 15/01/2026\n"
    "EMENTA\n...\n"
)


def test_extract_acordao_metadata_pulls_header_fields():
    meta = extract_acordao_metadata(ACORDAO_HEADER)
    assert meta["orgao_julgador"] == "QUARTA CAMARA CIVEL"
    assert meta["numero"] == "0001234-56.2026.8.08.0001"
    assert meta["relator"] == "Desembargador Fulano de Tal"
    assert meta["tipo_recurso"] == "APELACAO"
    assert meta["data_publicacao"] == "15/01/2026"


def test_extract_acordao_metadata_missing_fields_are_none():
    meta = extract_acordao_metadata("texto sem cabecalho estruturado")
    assert all(meta[k] is None for k in meta)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_markers.py -q -k acordao_metadata`
Expected: FAIL — `extract_acordao_metadata` not defined.

- [ ] **Step 3: Implement (append to `markers.py`)**

```python
_ACORDAO_FIELDS = {
    "orgao_julgador": re.compile(r"((?:PRIMEIRA|SEGUNDA|TERCEIRA|QUARTA|QUINTA)\s+C[ÂA]MARA[^\n]*|\w+\s+TURMA[^\n]*|PLENO)", re.IGNORECASE),
    "numero": re.compile(r"N[ºo°]?\s*([\d.\-/]{10,})"),
    "relator": re.compile(r"RELATOR[A]?\s*:?\s*([^\n]+)", re.IGNORECASE),
    "tipo_recurso": re.compile(r"\b(APELA[ÇC][ÃA]O|AGRAVO|EMBARGOS|RECURSO ESPECIAL)\b", re.IGNORECASE),
    "data_publicacao": re.compile(r"DJe\s+de\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
}


def extract_acordao_metadata(text: str) -> dict[str, str | None]:
    """Best-effort header extraction from the first 2000 chars of an acórdão."""
    head = text[:2000]
    result: dict[str, str | None] = {}
    for field, pattern in _ACORDAO_FIELDS.items():
        match = pattern.search(head)
        result[field] = match.group(1).strip().upper() if field == "tipo_recurso" and match else (
            match.group(1).strip() if match else None
        )
    return result
```

> **Implementer note:** the templates in Task 10 must contain these exact header shapes, or this test and the acórdão-metadata chunk test (Task 6) cannot pass. Keep the acórdão template header aligned with `_ACORDAO_FIELDS`.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_markers.py -q`
Expected: PASS (all marker tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/markers.py tests/test_markers.py
git commit -m "feat(chunking): extract_acordao_metadata() header parser"
```

---

### Task 5: ParagraphChunker (fallback, unit_type parameterized)

**Files:**
- Modify: `app/services/chunking.py`
- Test: `tests/test_chunkers.py`

**Params:** `target_tokens=500`, `min_tokens=200`, `max_tokens=800`, `overlap_sentences=1`. Behavior: split text into paragraphs (blank-line separated); aggregate consecutive paragraphs until ≥ `target_tokens`; if a single unit > `max_tokens`, split by sentences into ≤ `max_tokens` groups with the last sentence of the previous chunk prefixed (`[...] `) onto the next. `chunking_strategy: "paragraph_v0.2"`. **`unit_type` is a required parameter (D3).**

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
from app.services.chunking import ParagraphChunker


def test_paragraph_chunker_single_small_text_one_chunk():
    chunks = ParagraphChunker().chunk("texto curto de teste", unit_type="documento")
    assert len(chunks) == 1
    assert chunks[0]["unit_type"] == "documento"
    assert chunks[0]["metadata"]["chunking_strategy"] == "paragraph_v0.2"
    assert chunks[0]["text"] == "texto curto de teste"


def test_paragraph_chunker_respects_unit_type_param():
    chunks = ParagraphChunker().chunk("conteudo", unit_type="fundamentos")
    assert chunks[0]["unit_type"] == "fundamentos"


def test_paragraph_chunker_splits_oversized_text_with_overlap():
    # 900 one-word "sentences." -> exceeds max_tokens=800 -> splits; overlap marker present.
    sentence = "palavra."
    big = " ".join([sentence] * 900)
    chunks = ParagraphChunker(max_tokens=800).chunk(big, unit_type="documento")
    assert len(chunks) >= 2
    assert all(c["unit_type"] == "documento" for c in chunks)
    assert chunks[1]["text"].startswith("[...]")


def test_paragraph_chunker_empty_text_returns_empty():
    assert ParagraphChunker().chunk("   ", unit_type="documento") == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k paragraph_chunker`
Expected: FAIL — `ParagraphChunker` not defined.

- [ ] **Step 3: Implement (add to `chunking.py`)**

```python
class ParagraphChunker:
    """Token-budgeted fallback chunker. unit_type is supplied by the caller (D3)."""

    strategy = "paragraph_v0.2"

    def __init__(self, target_tokens=500, min_tokens=200, max_tokens=800, overlap_sentences=1):
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap_sentences = overlap_sentences

    def chunk(self, text: str, unit_type: str) -> list[dict]:
        text = text.strip()
        if not text:
            return []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        units = paragraphs or [text]

        # Aggregate small paragraphs toward target; flush oversize via sentence split.
        bodies: list[str] = []
        buffer = ""
        for para in units:
            candidate = f"{buffer}\n\n{para}".strip() if buffer else para
            if estimate_tokens(candidate) > self.max_tokens:
                if buffer:
                    bodies.append(buffer)
                bodies.extend(self._split_oversized(para))
                buffer = ""
            elif estimate_tokens(candidate) >= self.target_tokens:
                bodies.append(candidate)
                buffer = ""
            else:
                buffer = candidate
        if buffer:
            bodies.append(buffer)

        bodies = self._apply_overlap(bodies)
        return [{"text": body, "unit_type": unit_type,
                 "metadata": {"chunking_strategy": self.strategy}} for body in bodies]

    def _split_oversized(self, para: str) -> list[str]:
        sentences = split_sentences(para)
        out, buffer = [], ""
        for sentence in sentences:
            candidate = f"{buffer} {sentence}".strip()
            if buffer and estimate_tokens(candidate) > self.max_tokens:
                out.append(buffer)
                buffer = sentence
            else:
                buffer = candidate
        if buffer:
            out.append(buffer)
        return out or [para]

    def _apply_overlap(self, bodies: list[str]) -> list[str]:
        if self.overlap_sentences <= 0 or len(bodies) < 2:
            return bodies
        result = [bodies[0]]
        for previous, current in zip(bodies, bodies[1:]):
            tail = split_sentences(previous)[-self.overlap_sentences:]
            result.append(f"[...] {' '.join(tail)} {current}".strip())
        return result
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k paragraph_chunker`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "feat(chunking): ParagraphChunker with token budget + sentence overlap"
```

---

### Task 6: StructuralChunker

**Files:**
- Modify: `app/services/chunking.py`
- Test: `tests/test_chunkers.py`

**Behavior:** call `detect_sections`; one chunk per section (`unit_type` = section's); a section body > `max_tokens` is subdivided via `ParagraphChunker(...).chunk(body, unit_type=section.unit_type)` (D3); for `acordao`, attach `extract_acordao_metadata()` output to every chunk's `metadata["acordao"]`; `chunking_strategy: "structural_v0.2"`.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
from app.services.chunking import StructuralChunker
from tests.test_markers import SENTENCA, ACORDAO_HEADER  # reuse fixtures


def test_structural_chunker_sentenca_three_sections():
    chunks = StructuralChunker().chunk(SENTENCA, "sentenca")
    assert [c["unit_type"] for c in chunks] == ["relatorio", "fundamentos", "dispositivo"]
    assert all(c["metadata"]["chunking_strategy"] == "structural_v0.2" for c in chunks)


def test_structural_chunker_acordao_attaches_metadata_to_all_chunks():
    acordao = ACORDAO_HEADER + "Corpo da ementa.\n\nVOTO\nCorpo do voto.\n\nDISPOSITIVO\nNego provimento.\n"
    chunks = StructuralChunker().chunk(acordao, "acordao")
    assert len(chunks) >= 2
    assert all(c["metadata"]["acordao"]["relator"] == "Desembargador Fulano de Tal" for c in chunks)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k structural_chunker`
Expected: FAIL — `StructuralChunker` not defined.

- [ ] **Step 3: Implement (add to `chunking.py`)**

```python
from app.services.markers import detect_sections, extract_acordao_metadata


class StructuralChunker:
    strategy = "structural_v0.2"

    def __init__(self, max_tokens=800):
        self.max_tokens = max_tokens
        self._fallback = ParagraphChunker(max_tokens=max_tokens)

    def chunk(self, text: str, doc_type: str) -> list[dict]:
        sections = detect_sections(text, doc_type) or []
        acordao_meta = extract_acordao_metadata(text) if doc_type == "acordao" else None
        chunks: list[dict] = []
        for section in sections:
            if estimate_tokens(section.text) > self.max_tokens:
                pieces = self._fallback.chunk(section.text, unit_type=section.unit_type)
            else:
                pieces = [{"text": section.text, "unit_type": section.unit_type,
                           "metadata": {}}]
            for piece in pieces:
                piece["metadata"]["chunking_strategy"] = self.strategy
                if acordao_meta is not None:
                    piece["metadata"]["acordao"] = acordao_meta
                chunks.append(piece)
        return chunks
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k structural_chunker`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "feat(chunking): StructuralChunker (one chunk per legal section)"
```

---

### Task 7: get_chunker() factory

**Files:**
- Modify: `app/services/chunking.py`
- Test: `tests/test_chunkers.py`

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
from app.services.chunking import get_chunker, StructuralChunker, ParagraphChunker
from tests.test_markers import SENTENCA


def test_get_chunker_returns_structural_when_markers_present():
    assert isinstance(get_chunker(SENTENCA, "sentenca"), StructuralChunker)


def test_get_chunker_returns_paragraph_without_markers():
    assert isinstance(get_chunker("texto plano sem cabecalhos", "sentenca"), ParagraphChunker)


def test_get_chunker_paragraph_for_unknown_doc_type():
    assert isinstance(get_chunker(SENTENCA, "algo"), ParagraphChunker)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k get_chunker`
Expected: FAIL — `get_chunker` not defined.

- [ ] **Step 3: Implement**

```python
def get_chunker(text: str, doc_type: str):
    sections = detect_sections(text, doc_type)
    if sections and len(sections) >= 2:
        return StructuralChunker()
    return ParagraphChunker()
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k get_chunker`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "feat(chunking): get_chunker() factory (structural vs paragraph)"
```

---

### Task 8: build_chunk_id conditional ordinal + build_chunks() orchestrator

**Files:**
- Modify: `app/services/chunking.py`
- Test: `tests/test_chunkers.py`

**`build_chunks(case_id, extracted_text)`** replaces the per-item loop: for each item, pick the chunker via `get_chunker(item.text, item.doc_type)`, produce section/paragraph chunks, then assemble `LegalChunk` dicts. `chunk_id` = `build_chunk_id(case, doc, page, unit)` when a `(doc,page,unit)` group has exactly one chunk, else `..._{ordinal}` (R1). For `ParagraphChunker` top-level, `unit_type` comes from `UNIT_TYPE_BY_DOC_TYPE.get(doc_type, "documento")` (D3 backward-compat).

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
from app.services.chunking import build_chunks


def _item(doc_id, doc_type, text, page=1):
    return {"doc_id": doc_id, "doc_type": doc_type, "text": text,
            "file_path": f"{doc_id}.pdf", "page": page, "quality_score": 0.9}


def test_build_chunks_single_chunk_keeps_bare_id():
    # marker-free short text -> paragraph -> one chunk -> id has NO ordinal suffix.
    chunks = build_chunks("caso", [_item("doc_1", "peticao_inicial", "texto curto")])
    assert chunks[0]["chunk_id"] == "chunk_caso_doc_1_p1_pedido"
    assert chunks[0]["unit_type"] == "pedido"


def test_build_chunks_multichunk_section_gets_unique_ordinal_ids(monkeypatch):
    # Force an oversized single section so one (doc,page,unit) yields >1 chunk.
    big = "palavra. " * 2000
    text = f"RELATÓRIO\n{big}\n\nDISPOSITIVO\nfim.\n"
    chunks = build_chunks("caso", [_item("doc_1", "sentenca", text)])
    relatorio_ids = [c["chunk_id"] for c in chunks if c["unit_type"] == "relatorio"]
    assert len(relatorio_ids) >= 2
    assert len(set(relatorio_ids)) == len(relatorio_ids)  # no collisions
    assert relatorio_ids[0].endswith("_relatorio_0")


def test_build_chunks_skips_empty_text():
    assert build_chunks("caso", [_item("doc_1", "sentenca", "   ")]) == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k build_chunks`
Expected: FAIL — `build_chunks` not defined.

- [ ] **Step 3: Implement** — modify `build_chunk_id` to accept an optional ordinal, add `build_chunks`:

```python
def build_chunk_id(case_id, doc_id, page, unit_type, ordinal=None):
    base = f"chunk_{_slug(case_id)}_{_slug(doc_id)}_p{page}_{_slug(unit_type)}"
    return base if ordinal is None else f"{base}_{ordinal}"


def build_chunks(case_id: str, extracted_text: list[dict]) -> list[dict]:
    from app.schemas.case import LegalChunk

    out: list[dict] = []
    for item in extracted_text:
        text = str(item.get("text", "") or "").strip()
        if not text:
            continue
        doc_type = item.get("doc_type", "unknown")
        doc_id = item.get("doc_id", "doc_unknown")
        try:
            page = max(int(item.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        chunker = get_chunker(text, doc_type)
        if isinstance(chunker, StructuralChunker):
            pieces = chunker.chunk(text, doc_type)
        else:
            fallback_unit = UNIT_TYPE_BY_DOC_TYPE.get(doc_type, "documento")
            pieces = chunker.chunk(text, unit_type=fallback_unit)

        # conditional ordinal: only suffix when a (doc,page,unit) group has >1 chunk
        by_unit: dict[str, int] = {}
        for piece in pieces:
            by_unit[piece["unit_type"]] = by_unit.get(piece["unit_type"], 0) + 1
        seen: dict[str, int] = {}
        for piece in pieces:
            unit = piece["unit_type"]
            multi = by_unit[unit] > 1
            ordinal = seen.get(unit, 0) if multi else None
            seen[unit] = seen.get(unit, 0) + 1
            chunk = LegalChunk(
                chunk_id=build_chunk_id(case_id, doc_id, page, unit, ordinal),
                case_id=case_id, doc_id=doc_id, unit_type=unit,
                text=piece["text"], page_start=page, page_end=page,
                source=item.get("file_path"),
                metadata={
                    "doc_type": doc_type,
                    "quality_score": item.get("quality_score"),
                    "extraction_method": item.get("extraction_method"),
                    **piece["metadata"],
                },
            )
            out.append(chunk.model_dump())
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k build_chunks`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "feat(chunking): build_chunks() + conditional-ordinal chunk ids (R1)"
```

---

### Task 9: Deprecate chunk_extracted_text() as a wrapper

**Files:**
- Modify: `app/services/chunking.py`
- Test: `tests/test_chunkers.py`

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_chunkers.py
import warnings as _warnings
from app.services.chunking import chunk_extracted_text


def test_chunk_extracted_text_is_deprecated_but_delegates():
    item = {"doc_id": "doc_1", "doc_type": "peticao_inicial", "text": "texto curto",
            "file_path": "a.pdf", "page": 1, "quality_score": 0.9}
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        result = chunk_extracted_text("caso", [item])
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert result == build_chunks("caso", [item])
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q -k deprecated`
Expected: FAIL — no `DeprecationWarning` emitted.

- [ ] **Step 3: Rewrite `chunk_extracted_text` as a wrapper** (replace the old loop body):

```python
import warnings


def chunk_extracted_text(case_id: str, extracted_text: list[dict]) -> list[dict]:
    """DEPRECATED: use build_chunks(). Kept for backward compatibility."""
    warnings.warn(
        "chunk_extracted_text() is deprecated; use build_chunks().",
        DeprecationWarning,
        stacklevel=2,
    )
    return build_chunks(case_id, extracted_text)
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_chunkers.py -q`
Expected: PASS (all chunker tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/chunking.py tests/test_chunkers.py
git commit -m "refactor(chunking): chunk_extracted_text -> deprecated build_chunks wrapper"
```

---

### Task 10: extraction.py — Extractor protocol, ExtractedDocument, MockExtractor

**Files:**
- Create: `app/services/extraction.py`
- Test: `tests/test_extraction_service.py` (new)

**Templates (compact, marker-rich, abbreviation-free):** one header line per section + 1–2 sentences. The acórdão template carries the four header fields `extract_acordao_metadata` expects. Section counts: peticao=3, contestacao=3, sentenca=3, acordao=4.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_extraction_service.py
from app.services.extraction import ExtractedDocument, MockExtractor
from app.services.markers import detect_sections


def test_mock_extractor_returns_extracted_document():
    doc = MockExtractor().extract("sentenca.pdf", "sentenca")
    assert isinstance(doc, ExtractedDocument)
    assert doc.doc_type == "sentenca"


def test_mock_extractor_sentenca_has_three_detectable_sections():
    doc = MockExtractor().extract("sentenca.pdf", "sentenca")
    sections = detect_sections(doc.text, "sentenca")
    assert [s.unit_type for s in sections] == ["relatorio", "fundamentos", "dispositivo"]


def test_mock_extractor_acordao_has_four_sections_and_header():
    doc = MockExtractor().extract("acordao.pdf", "acordao")
    sections = detect_sections(doc.text, "acordao")
    assert len(sections) == 4
    assert "RELATOR" in doc.text and "DJe" in doc.text


def test_mock_extractor_infers_doc_type_from_filename():
    assert MockExtractor().extract("peticao_inicial.pdf").doc_type == "peticao_inicial"


def test_mock_extractor_unknown_has_no_sections():
    doc = MockExtractor().extract("random.pdf", "unknown")
    assert detect_sections(doc.text, "unknown") is None


def test_mock_extractor_supports_pdf():
    assert MockExtractor().supports("x.pdf") is True
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_extraction_service.py -q`
Expected: FAIL — module missing.

- [ ] **Step 3: Implement `app/services/extraction.py`**

```python
from typing import Protocol

from pydantic import BaseModel, Field

_MARKER_TEMPLATES: dict[str, str] = {
    "peticao_inicial": (
        "DOS FATOS\n"
        "O autor Consumidor Alfa sofreu fraude bancaria via pix realizada por terceiro.\n\n"
        "DO DIREITO\n"
        "A responsabilidade do fornecedor de servico e objetiva na forma do CDC.\n\n"
        "DOS PEDIDOS\n"
        "Requer a condenacao do reu ao pagamento de indenizacao por danos morais e materiais.\n"
    ),
    "contestacao": (
        "DAS PRELIMINARES\n"
        "O reu Banco Beta suscita a ausencia de interesse processual do autor.\n\n"
        "DO MERITO\n"
        "Sustenta a culpa exclusiva de terceiro e a inexistencia de falha na prestacao do servico.\n\n"
        "DOS PEDIDOS\n"
        "Requer a total improcedencia dos pedidos formulados na inicial.\n"
    ),
    "sentenca": (
        "RELATÓRIO\n"
        "Trata-se de acao de indenizacao proposta por Consumidor Alfa em face de Banco Beta.\n\n"
        "FUNDAMENTAÇÃO\n"
        "A responsabilidade do banco e objetiva conforme entendimento consolidado dos tribunais superiores.\n\n"
        "DISPOSITIVO\n"
        "Julgo parcialmente procedentes os pedidos para condenar o reu ao pagamento de danos morais.\n"
    ),
    "acordao": (
        "TRIBUNAL DE JUSTICA - QUARTA CAMARA CIVEL\n"
        "APELACAO CIVEL Nº 0001234-56.2026.8.08.0001\n"
        "RELATOR: Desembargador Fulano de Tal\n"
        "Publicado no DJe de 15/01/2026\n"
        "EMENTA\n"
        "Responsabilidade civil bancaria. Fraude praticada por terceiro. Responsabilidade objetiva.\n\n"
        "RELATÓRIO\n"
        "O banco apelou da sentenca que reconheceu a falha na prestacao do servico.\n\n"
        "VOTO\n"
        "A tese da culpa exclusiva de terceiro nao afasta a responsabilidade objetiva do banco.\n\n"
        "DISPOSITIVO\n"
        "Nego provimento ao recurso e mantenho a sentenca por seus proprios fundamentos.\n"
    ),
    "unknown": (
        "Documento nao classificado. Conteudo insuficiente para extracao juridica confiavel.\n"
    ),
}

_DOC_TYPES = ("peticao_inicial", "contestacao", "sentenca", "acordao")


class ExtractedDocument(BaseModel):
    text: str = Field(min_length=1)
    doc_type: str
    doc_id: str = "doc_unknown"
    file_path: str | None = None
    page_count: int = Field(default=1, ge=1)
    quality_score: float = Field(default=0.95, ge=0.0, le=1.0)
    extraction_method: str = "mock"
    metadata: dict = Field(default_factory=dict)


class Extractor(Protocol):
    def extract(self, file_path: str, doc_type: str | None = None) -> ExtractedDocument: ...
    def supports(self, file_path: str) -> bool: ...


class MockExtractor:
    """Returns marker-rich structured text per doc_type (prepared interface; no real IO)."""

    def supports(self, file_path: str) -> bool:
        return str(file_path).lower().endswith((".pdf", ".txt"))

    def extract(self, file_path: str, doc_type: str | None = None) -> ExtractedDocument:
        resolved = doc_type or self._infer(file_path)
        text = _MARKER_TEMPLATES.get(resolved, _MARKER_TEMPLATES["unknown"])
        return ExtractedDocument(
            text=text, doc_type=resolved, file_path=file_path,
            extraction_method="mock",
        )

    @staticmethod
    def _infer(file_path: str) -> str:
        lowered = str(file_path).lower()
        for candidate in _DOC_TYPES:
            if candidate.split("_")[0] in lowered:
                return candidate
        return "unknown"
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_extraction_service.py -q`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add app/services/extraction.py tests/test_extraction_service.py
git commit -m "feat(extraction): Extractor protocol + marker-rich MockExtractor"
```

---

### Task 11: Wire MockExtractor into ExtractionAgent

**Files:**
- Modify: `app/agents/extraction_agent.py`
- Test: `tests/test_structured_extraction_normalization.py` (add a marker-presence assertion)

**Seam (D5):** inject the extractor; use only its `.text`. Keep `quality_score` (0.92/0.68), `warnings`, and `extraction_method="mock_filename_template"` exactly as today so the extraction-quality tests stay green.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_structured_extraction_normalization.py
from app.agents.extraction_agent import ExtractionAgent


def test_extraction_agent_emits_marker_rich_text():
    result = ExtractionAgent().run("caso", [{"doc_id": "doc_1", "file_path": "sentenca.pdf",
                                             "doc_type": "sentenca"}])
    text = result.output["extracted_text"][0]["text"]
    assert "RELATÓRIO" in text and "DISPOSITIVO" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_structured_extraction_normalization.py -q -k marker_rich`
Expected: FAIL — current flat mock text has no `RELATÓRIO`.

- [ ] **Step 3: Modify `extraction_agent.py`** — replace the `MOCK_TEXT_BY_DOC_TYPE[doc_type]` lookup:

Add constructor injection and use the extractor's text (keep everything else):

```python
from app.services.extraction import Extractor, MockExtractor

class ExtractionAgent:
    name = "ExtractionAgent"

    def __init__(self, extractor: Extractor | None = None):
        self._extractor = extractor or MockExtractor()

    # inside run(), replace: text=MOCK_TEXT_BY_DOC_TYPE[doc_type]
    #   with:                text=self._extractor.extract(
    #                            doc.get("file_path") or "", doc_type).text
```

Delete the now-unused `MOCK_TEXT_BY_DOC_TYPE` dict (or keep only if another test references it — grep first: `grep -rn MOCK_TEXT_BY_DOC_TYPE app tests`). Keep the `doc_type not in ...` guard by checking against `_DOC_TYPES`/`"unknown"` (quality_score logic unchanged).

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_structured_extraction_normalization.py -q -k marker_rich`
Expected: PASS. (Other tests in this file will FAIL on counts — fixed in Task 13.)

- [ ] **Step 5: Commit**

```bash
git add app/agents/extraction_agent.py tests/test_structured_extraction_normalization.py
git commit -m "feat(extraction): ExtractionAgent consumes MockExtractor marker-rich text"
```

---

### Task 12: Point IndexingAgent at build_chunks()

**Files:**
- Modify: `app/agents/indexing_agent.py:38`
- Test: (covered by existing indexing + integration tests; no new test)

- [ ] **Step 1: Change the import + call** (avoid the deprecation warning in production):

```python
# app/agents/indexing_agent.py
from app.services.chunking import build_chunks   # was: chunk_extracted_text
# ...
chunks = build_chunks(case_id, extracted_text)   # line 38
```

- [ ] **Step 2: Run the indexing + integration tests**

Run: `.venv/bin/python -m pytest tests/test_indexing_vector_store.py -q`
Expected: One FAIL — `test_chunk_..._deterministic_legal_chunks` at the `chunking_strategy == "legal_unit_mock_v0.1"` assertion (:50). Ids/unit_types/counts still pass (marker-free fixture → ParagraphChunker single chunk). This failure is fixed in Task 13.

- [ ] **Step 3: Commit** (WIP is acceptable here since the strategy-string test is updated next task; or squash 12+13)

```bash
git add app/agents/indexing_agent.py
git commit -m "refactor(indexing): use build_chunks() (structural/paragraph chunkers)"
```

---

### Task 13: Update the count/strategy assertions broken by the new chunkers

**Files:**
- Modify: `tests/test_indexing_vector_store.py:50`
- Modify: `tests/test_structured_extraction_normalization.py:179-180`
- Modify: `tests/test_api_routes.py:215-216`

- [ ] **Step 1: Update `test_indexing_vector_store.py:49-52`** — the marker-free fixture now routes through ParagraphChunker:

```python
    assert all(
        chunk["metadata"]["chunking_strategy"] == "paragraph_v0.2"
        for chunk in chunks
    )
```

- [ ] **Step 2: Update `test_structured_extraction_normalization.py:179-180`** (4 docs → 3+3+3+4):

```python
    assert indexing_output["chunk_count"] == 13
    assert indexing_output["indexed_count"] == 13
```

- [ ] **Step 3: Update `test_api_routes.py:215-216`** (peticao+sentenca → 3+3):

```python
    assert indexing_trace["chunk_count"] == 6
    assert indexing_trace["indexed_count"] == 6
```

- [ ] **Step 4: Run the full gate**

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check app tests scripts integrations && .venv/bin/ruff format --check app tests scripts integrations
.venv/bin/mypy app
.venv/bin/python -m scripts.gen_schemas && git diff --exit-code app/schemas
.venv/bin/python -m app.evals.run_eval
```

Expected: all green (`~86 + ~28 new − 0 = ~114 passed`), ruff/mypy clean, schema drift none, eval exit 0. If a `chunk_count` is off, recount the failing document's template sections (Task 10) — the count is exactly the number of section headers.

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: update chunk_count/strategy assertions for richer chunking"
```

---

### Task 14: Docs + changelog

**Files:**
- Modify: `CHANGELOG.md`, `README.md` (chunking section), the spec's Non-Goal note

- [ ] **Step 1:** In `README.md`'s "Indexação e busca mockadas" section, note that indexing now uses structural chunking (per legal section) with a paragraph fallback, via `get_chunker()`, and that `chunk_extracted_text()` is deprecated in favor of `build_chunks()`.
- [ ] **Step 2:** Add a `CHANGELOG.md` entry under the current version: structural + paragraph chunkers, `Extractor`/`MockExtractor`, four new `ChunkUnitType` values, deprecated `chunk_extracted_text`.
- [ ] **Step 3:** In `docs/superpowers/specs/2026-06-15-richer-chunking-design.md`, update the Status line to `Implemented (2026-07-10)` and note the D1–D5/R1 deviations point to this plan.
- [ ] **Step 4: Commit**

```bash
git add README.md CHANGELOG.md docs/
git commit -m "docs: document richer chunking (structural + paragraph, Extractor)"
```

---

## Self-Review

**1. Spec coverage.** Goal 1 (structural) → Tasks 3,6. Goal 2 (paragraph fallback) → Task 5. Goal 3 (Extractor interface) → Task 10. Goal 4 (acórdão metadata) → Tasks 4,6. Goal 5 (backward-compat) → Task 9. Success criteria #1 (~109 tests) → ~114 after Task 13; #2 (`get_chunker`) → Task 7; #3 (sentença→3) → Task 6 + the pipeline count (13) in Task 13; #4 (acórdão metadata) → Task 6; #5 (no markers→paragraph) → Task 7; #6 (deprecated wrapper) → Task 9; #7 (CI green) → Task 13. **Covered.**

**2. Placeholder scan.** All code steps carry real code; all counts are computed (13, 6) from the Task-10 templates; no "TBD"/"handle edge cases". The one soft spot — the `detect_sections` body-trimming offset math (Task 3) — carries an explicit fallback strategy and a fixed observable contract, not a placeholder.

**3. Type consistency.** `build_chunk_id(case, doc, page, unit_type, ordinal=None)` used consistently (Tasks 8). `ParagraphChunker.chunk(text, unit_type=...)` and `StructuralChunker.chunk(text, doc_type)` signatures are stable across Tasks 5,6,8. `DetectedSection.unit_type/.text/.order` consistent Tasks 3,6. `build_chunks(case_id, extracted_text)` consistent Tasks 8,9,12. Piece dict shape `{"text","unit_type","metadata"}` consistent across ParagraphChunker/StructuralChunker/build_chunks.

**Open risk to watch during execution:** the `test_indexing_vector_store.py` exact-id assertions (:41-44, :79-81, :108) and unit-type list (:45-48, :121-123) are predicted to stay green (marker-free fixture → single ParagraphChunker chunk → bare id, `pedido`/`contestacao` via `UNIT_TYPE_BY_DOC_TYPE`). If Task 12 turns any of them red, the cause is ParagraphChunker not preserving the doc_type→unit_type mapping or the ordinal firing on a single chunk — fix the chunker, not the test.

---

## Success Criteria

1. [ ] ~114 tests pass (86 baseline + ~28 new); the three updated count/strategy assertions are green with values 13, 6, `paragraph_v0.2`.
2. [ ] `get_chunker()` returns `StructuralChunker` for marker-rich text, `ParagraphChunker` otherwise.
3. [ ] A `sentenca` mock document produces exactly 3 chunks (`relatorio`, `fundamentos`, `dispositivo`).
4. [ ] An `acordao` mock document attaches `metadata["acordao"]` (relator, numero, orgao_julgador, tipo_recurso, data_publicacao) to every chunk.
5. [ ] Marker-free text uses `ParagraphChunker`; `chunk_extracted_text()` still works and emits `DeprecationWarning`.
6. [ ] No chunk-id collisions when a section subdivides (conditional ordinal).
7. [ ] CI green: ruff, mypy, schema-drift (none), pytest, eval (numbers unchanged — decoupled).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-10-richer-chunking.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
