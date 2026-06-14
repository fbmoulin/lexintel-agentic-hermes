import re

from app.schemas.case import LegalChunk

UNIT_TYPE_BY_DOC_TYPE = {
    "peticao_inicial": "pedido",
    "contestacao": "contestacao",
    "sentenca": "dispositivo",
    "acordao": "ementa",
    "unknown": "documento",
}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return slug.strip("_") or "unknown"


def build_chunk_id(case_id: str, doc_id: str, page: int, unit_type: str) -> str:
    return f"chunk_{_slug(case_id)}_{_slug(doc_id)}_p{page}_{_slug(unit_type)}"


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
