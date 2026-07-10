import re

from app.schemas.case import ChunkUnitType, LegalChunk
from app.services.markers import detect_sections, extract_acordao_metadata

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


class ParagraphChunker:
    """Token-budgeted fallback chunker. unit_type is supplied by the caller (D3)."""

    strategy = "paragraph_v0.2"

    def __init__(
        self, target_tokens=500, min_tokens=200, max_tokens=800, overlap_sentences=1
    ):
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
        return [
            {
                "text": body,
                "unit_type": unit_type,
                "metadata": {"chunking_strategy": self.strategy},
            }
            for body in bodies
        ]

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
            tail = split_sentences(previous)[-self.overlap_sentences :]
            result.append(f"[...] {' '.join(tail)} {current}".strip())
        return result


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
                pieces = [
                    {
                        "text": section.text,
                        "unit_type": section.unit_type,
                        "metadata": {},
                    }
                ]
            for piece in pieces:
                piece["metadata"]["chunking_strategy"] = self.strategy
                if acordao_meta is not None:
                    piece["metadata"]["acordao"] = acordao_meta
                chunks.append(piece)
        return chunks


def get_chunker(text: str, doc_type: str) -> StructuralChunker | ParagraphChunker:
    sections = detect_sections(text, doc_type)
    if sections and len(sections) >= 2:
        return StructuralChunker()
    return ParagraphChunker()


UNIT_TYPE_BY_DOC_TYPE: dict[str, ChunkUnitType] = {
    "peticao_inicial": "pedido",
    "contestacao": "contestacao",
    "sentenca": "dispositivo",
    "acordao": "ementa",
    "unknown": "documento",
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return slug.strip("_") or "unknown"


def build_chunk_id(
    case_id: str, doc_id: str, page: int, unit_type: str, ordinal: int | None = None
) -> str:
    base = f"chunk_{_slug(case_id)}_{_slug(doc_id)}_p{page}_{_slug(unit_type)}"
    return base if ordinal is None else f"{base}_{ordinal}"


def build_chunks(case_id: str, extracted_text: list[dict]) -> list[dict]:
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
                case_id=case_id,
                doc_id=doc_id,
                unit_type=unit,
                text=piece["text"],
                page_start=page,
                page_end=page,
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


def chunk_extracted_text(case_id: str, extracted_text: list[dict]) -> list[dict]:
    chunks = []

    for item in extracted_text:
        text = item.get("text", "")
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        text = text.strip()
        if not text:
            continue

        doc_type = item.get("doc_type", "unknown")
        unit_type = UNIT_TYPE_BY_DOC_TYPE.get(doc_type, "documento")
        try:
            page = int(item.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        page = max(page, 1)
        doc_id = item.get("doc_id", "doc_unknown")
        chunk = LegalChunk(
            chunk_id=build_chunk_id(case_id, doc_id, page, unit_type),
            case_id=case_id,
            doc_id=doc_id,
            unit_type=unit_type,
            text=text,
            page_start=page,
            page_end=page,
            source=item.get("file_path"),
            metadata={
                "doc_type": doc_type,
                "quality_score": item.get("quality_score"),
                "extraction_method": item.get("extraction_method"),
                "chunking_strategy": "legal_unit_mock_v0.1",
            },
        )
        chunks.append(chunk.model_dump())

    return chunks
