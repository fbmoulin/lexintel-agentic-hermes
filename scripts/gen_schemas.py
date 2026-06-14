"""Generate JSON Schema for the *modelled* contracts from Pydantic — the single
source of truth. Run via `python -m scripts.gen_schemas`; CI re-runs it and
fails on drift (`git diff --exit-code`).

Scope:
- ValidationResult  -> app/schemas/validation_result.schema.json
- RetrievedContext  -> app/schemas/retrieved_context.schema.json

NOT generated (intentionally):
- agent_run.schema.json    : future-spec for an unbuilt run-ledger / cost layer
                             (run_id/started_at/latency_ms/cost_usd). No model yet.
- retrieval_result.schema.json : the /rag/search response envelope (hand-authored).
"""

import json
from pathlib import Path

from app.schemas.case import RetrievedContext, ValidationResult

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "app" / "schemas"

TARGETS = {
    "validation_result.schema.json": ValidationResult,
    "retrieved_context.schema.json": RetrievedContext,
}


def generate() -> None:
    for filename, model in TARGETS.items():
        schema = model.model_json_schema()
        path = SCHEMAS_DIR / filename
        path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(SCHEMAS_DIR.parents[1])}")


if __name__ == "__main__":
    generate()
