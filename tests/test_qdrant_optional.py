"""qdrant-client is an optional extra: the mocked v0.1 pipeline must run without it."""

import sys

from app.schemas.case import CaseInput


def test_qdrant_service_imports_without_client(monkeypatch):
    # Simulate qdrant-client not being installed (None in sys.modules → ImportError).
    monkeypatch.setitem(sys.modules, "qdrant_client", None)
    import importlib

    import app.services.qdrant_service as qs

    importlib.reload(qs)
    # Module imports fine and the flag works without the client present.
    assert qs.is_qdrant_enabled() is False


def test_full_mock_pipeline_runs_without_qdrant_client(monkeypatch):
    monkeypatch.setitem(sys.modules, "qdrant_client", None)

    from app.agents.orchestrator import CaseOrchestrator

    case = CaseInput(
        case_id="caso_sem_qdrant_001",
        source_type="manual",
        user_goal="analise",
        files=["peticao_inicial.pdf"],
    )
    result = CaseOrchestrator().run_full_mock(case)

    assert result["status"] in {"success", "warning"}
    assert result["external_use_allowed"] is False


def test_get_qdrant_client_raises_when_disabled(monkeypatch):
    monkeypatch.delenv("LEX_KRATOS_ENABLE_QDRANT", raising=False)
    from app.services.qdrant_service import get_qdrant_client

    try:
        get_qdrant_client()
        raise AssertionError("expected RuntimeError when Qdrant is disabled")
    except RuntimeError as exc:
        assert "LEX_KRATOS_ENABLE_QDRANT" in str(exc)
