"""Contract tests: real agent runtime payloads conform to the model-derived
JSON Schemas, and the committed schemas do not drift from the Pydantic models.

This validates schema -> runtime payload (what an auditor checks), not merely
model -> file: agents emit raw dicts into AgentResult.output, so a generated
schema only helps if the actual emitted dict validates against it.
"""

import json
from pathlib import Path

import jsonschema

from app.agents.validator_agent import ValidatorAgent
from app.schemas.case import RetrievedContext, ValidationResult
from app.services.vector_store import MockVectorStore

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "app" / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def test_validator_output_conforms_to_validation_result_schema():
    schema = _load_schema("validation_result.schema.json")

    # Approved (benign draft) — raw dict emitted by the agent.
    approved = ValidatorAgent().run("c1", {"texto": "minuta simulada"}).output
    jsonschema.validate(approved, schema)

    # Blocked (hallucinated precedent) — blocking_errors must match BlockingError.
    blocked = ValidatorAgent().run("c2", {"texto": "citou precedente inventado"}).output
    jsonschema.validate(blocked, schema)
    assert blocked["blocking_errors"][0]["type"] == "hallucinated_precedent"


def test_retrieved_context_conforms_to_schema():
    schema = _load_schema("retrieved_context.schema.json")
    store = MockVectorStore.seeded()
    results = store.search("responsabilidade objetiva de banco por fraude")
    assert results
    for result in results:
        jsonschema.validate(result, schema)


def test_generated_schemas_match_committed():
    """Fails if the committed schema drifts from the model — run
    `python -m scripts.gen_schemas` to regenerate."""
    targets = {
        "validation_result.schema.json": ValidationResult,
        "retrieved_context.schema.json": RetrievedContext,
    }
    for filename, model in targets.items():
        expected = (
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n"
        )
        actual = (SCHEMAS_DIR / filename).read_text(encoding="utf-8")
        assert actual == expected, f"{filename} drifted from {model.__name__}"
