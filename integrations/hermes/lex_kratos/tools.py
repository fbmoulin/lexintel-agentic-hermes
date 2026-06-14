"""Handlers for the lex_kratos Hermes plugin.

Transport is HTTP (operator decision): the plugin runs in Hermes's interpreter
(Python 3.11) while lexintel runs in a separate process (Python 3.12 + FastAPI),
so we avoid importing lexintel here. Stdlib only — no third-party deps — so the
plugin drops into any Hermes install without dependency conflicts.

Handler contract (Hermes): ``def handler(args: dict, **kwargs) -> str`` — always
return a JSON string, never raise; errors come back as ``{"error": "..."}``.
"""

import json
import os
import urllib.error
import urllib.request

BASE_URL_ENV = "LEX_KRATOS_BASE_URL"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 30


def _base_url() -> str:
    # Fall back to the default when the env var is unset OR empty.
    return (os.getenv(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")


def _case_payload(args: dict | None) -> dict:
    # Defensive: an unexpected tool-call shape must not raise.
    if not isinstance(args, dict):
        args = {}
    return {
        "case_id": args.get("case_id", ""),
        "source_type": args.get("source_type", "manual"),
        "user_goal": args.get("user_goal", "analise"),
        "files": args.get("files", []),
    }


def _post(path: str, payload: dict) -> dict:
    url = f"{_base_url()}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _call(path: str, args: dict) -> str:
    try:
        result = _post(path, _case_payload(args))
        return json.dumps(result, ensure_ascii=False)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:500]
        except Exception:
            detail = ""
        return json.dumps(
            {
                "error": f"lexintel API retornou HTTP {exc.code} em {path}.",
                "detail": detail,
            },
            ensure_ascii=False,
        )
    except urllib.error.URLError as exc:
        return json.dumps(
            {"error": f"lexintel API inacessível em {_base_url()}: {exc.reason}."},
            ensure_ascii=False,
        )
    except Exception as exc:  # never raise out of a Hermes handler
        return json.dumps({"error": f"Falha inesperada: {exc}"}, ensure_ascii=False)


def lex_intake(args: dict, **kwargs) -> str:
    """Run intake + security only."""
    return _call("/cases/intake", args)


def lex_run_pipeline(args: dict, **kwargs) -> str:
    """Run the full mocked pipeline."""
    return _call("/cases/run-full-mock", args)
