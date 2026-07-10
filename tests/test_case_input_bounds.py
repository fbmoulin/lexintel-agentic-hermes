"""CaseInput hardening: bound the unauthenticated pipeline's input surface.

`_build_security_text` concatenates case_id + all files and runs NFKD +
regex over the blob, so unbounded case_id / files is a DoS vector. These
bounds reject oversized input at the Pydantic edge (HTTP 422) before any
agent runs.
"""

import pytest
from pydantic import ValidationError

from app.schemas.case import CaseInput


def test_case_input_rejects_oversized_case_id():
    with pytest.raises(ValidationError):
        CaseInput(case_id="a" * 200, source_type="manual", user_goal="analise")


def test_case_input_rejects_too_many_files():
    with pytest.raises(ValidationError):
        CaseInput(
            case_id="caso_001",
            source_type="manual",
            user_goal="analise",
            files=["f.pdf"] * 1000,
        )


def test_case_input_rejects_oversized_file_path():
    with pytest.raises(ValidationError):
        CaseInput(
            case_id="caso_001",
            source_type="manual",
            user_goal="analise",
            files=["a" * 5000],
        )


def test_case_input_accepts_realistic_bounds():
    case = CaseInput(
        case_id="0001234-56.2026.8.08.0001",
        source_type="manual",
        user_goal="analise",
        files=["peticao_inicial.pdf", "contestacao.pdf"],
    )

    assert case.case_id == "0001234-56.2026.8.08.0001"
    assert len(case.files) == 2
