import pytest
from pydantic import ValidationError

from app.schemas.case import LegalChunk


@pytest.mark.parametrize("unit_type", ["fatos", "direito", "preliminares", "merito"])
def test_legal_chunk_accepts_new_structural_unit_types(unit_type):
    chunk = LegalChunk(
        chunk_id="c1",
        case_id="caso",
        doc_id="doc_1",
        unit_type=unit_type,
        text="x",
        page_start=1,
        page_end=1,
    )
    assert chunk.unit_type == unit_type


def test_legal_chunk_rejects_unknown_unit_type():
    with pytest.raises(ValidationError):
        LegalChunk(
            chunk_id="c1",
            case_id="caso",
            doc_id="doc_1",
            unit_type="nao_existe",
            text="x",
            page_start=1,
            page_end=1,
        )
