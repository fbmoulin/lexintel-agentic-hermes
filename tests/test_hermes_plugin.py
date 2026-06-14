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


def test_handlers_return_json_string_on_api_down():
    # No server here: URLError -> handler must return a JSON error string, not raise.
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
