import re
from dataclasses import dataclass
from typing import cast

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
    doc_type: [
        (key, re.compile(pat, re.IGNORECASE | re.MULTILINE)) for key, pat in pairs
    ]
    for doc_type, pairs in _RAW_MARKERS.items()
}


@dataclass
class DetectedSection:
    unit_type: ChunkUnitType
    text: str


def detect_sections(text: str, doc_type: str) -> list[DetectedSection] | None:
    """Return ordered sections (>=2) or None when structure is absent/insufficient."""
    markers = STRUCTURAL_MARKERS.get(doc_type)
    if not markers:
        return None

    # (marker_start, body_start, unit_type): slicing bodies to the NEXT marker's
    # START excludes that marker line by construction, so no marker text leaks and
    # adjacent markers yield an empty body that is dropped below.
    hits: list[tuple[int, int, str]] = []
    for unit_type, pattern in markers:
        for match in pattern.finditer(text):
            hits.append((match.start(), match.end(), unit_type))

    if len(hits) < 2:
        return None

    hits.sort(key=lambda h: h[0])
    sections: list[DetectedSection] = []
    for index, (_marker_start, body_start, unit_type) in enumerate(hits):
        body_end = hits[index + 1][0] if index + 1 < len(hits) else len(text)
        body = text[body_start:body_end].strip()
        if body:
            sections.append(
                DetectedSection(unit_type=cast(ChunkUnitType, unit_type), text=body)
            )

    return sections if len(sections) >= 2 else None


_ACORDAO_FIELDS = {
    "orgao_julgador": re.compile(
        r"((?:PRIMEIRA|SEGUNDA|TERCEIRA|QUARTA|QUINTA)\s+C[ÂA]MARA[^\n]*|\w+\s+TURMA[^\n]*|PLENO)",
        re.IGNORECASE,
    ),
    "numero": re.compile(r"N[ºo°]?\s*([\d.\-/]{10,})"),
    "relator": re.compile(r"RELATOR[A]?\s*:?\s*([^\n]+)", re.IGNORECASE),
    "tipo_recurso": re.compile(
        r"\b(APELA[ÇC][ÃA]O|AGRAVO|EMBARGOS|RECURSO ESPECIAL)\b", re.IGNORECASE
    ),
    "data_publicacao": re.compile(r"DJe\s+de\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
}


def extract_acordao_metadata(text: str) -> dict[str, str | None]:
    """Best-effort header extraction from the first 2000 chars of an acórdão."""
    head = text[:2000]
    result: dict[str, str | None] = {}
    for field, pattern in _ACORDAO_FIELDS.items():
        match = pattern.search(head)
        result[field] = (
            match.group(1).strip().upper()
            if field == "tipo_recurso" and match
            else (match.group(1).strip() if match else None)
        )
    return result
