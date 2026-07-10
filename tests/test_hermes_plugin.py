"""The lex_kratos Hermes plugin handlers obey the Hermes contract: return a JSON
string and never raise. Loaded by path (the plugin lives outside the app package).
"""

import importlib.util
import json
from pathlib import Path

PLUGIN_DIR = (
    Path(__file__).resolve().parents[1] / "integrations" / "hermes" / "lex_kratos"
)


def _load(module_name: str):
    spec = importlib.util.spec_from_file_location(
        f"lexkratos_{module_name}", PLUGIN_DIR / f"{module_name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = _load("tools")
schemas = _load("schemas")


def test_case_payload_applies_defaults():
    payload = tools._case_payload({"case_id": "c1"})
    assert payload == {
        "case_id": "c1",
        "source_type": "manual",
        "user_goal": "analise",
        "files": [],
    }


def test_handlers_return_json_string_on_api_down(monkeypatch):
    # Mock the network (deterministic, no real localhost POST): URLError -> the
    # handler must return a JSON error string, never raise.
    import urllib.error

    def _raise(path, payload):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(tools, "_post", _raise)
    for handler in (tools.lex_intake, tools.lex_run_pipeline):
        out = handler({"case_id": "c1"})
        assert isinstance(out, str)
        parsed = json.loads(out)
        assert "error" in parsed


def test_handler_passes_through_successful_response(monkeypatch):
    monkeypatch.setattr(
        tools, "_post", lambda path, payload: {"status": "success", "path": path}
    )
    out = tools.lex_run_pipeline({"case_id": "c1"})
    parsed = json.loads(out)
    assert parsed["status"] == "success"
    assert parsed["path"] == "/cases/run-full-mock"


def test_schemas_declare_required_case_id():
    for schema in (schemas.LEX_INTAKE, schemas.LEX_RUN_PIPELINE):
        assert schema["parameters"]["required"] == ["case_id"]
        assert "case_id" in schema["parameters"]["properties"]


def test_call_rejects_missing_case_id_without_calling_api(monkeypatch):
    # The API requires case_id (min_length=1). The plugin must not send an empty
    # default and let the API 422 — it rejects locally with a clear error and
    # never touches the network. (Belt-and-suspenders behind the schema's
    # required:[case_id]; see F2 in the 2026-07-10 premortem.)
    calls = []
    monkeypatch.setattr(
        tools, "_post", lambda path, payload: calls.append(payload) or {"status": "ok"}
    )

    for handler in (tools.lex_intake, tools.lex_run_pipeline):
        for bad_args in ({}, {"case_id": ""}, {"case_id": "   "}):
            parsed = json.loads(handler(bad_args))
            assert "case_id" in parsed["error"]

    assert calls == []  # the API was never contacted
