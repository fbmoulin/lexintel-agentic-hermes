import pytest
from pathlib import Path

from app.evals.run_eval import load_dataset, run

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "evals"


def test_eval_runs():
    result = run()

    assert "average_recall" in result
    assert result["dataset_size"] == 8
    assert result["areas"] == [
        "bancario",
        "consumidor",
        "processual_civil",
        "saude",
    ]
    assert result["average_recall_at_3"] >= 0.85
    assert result["average_mrr"] >= 0.85
    assert result["passed"] is True
    assert result["threshold_failures"] == []
    assert set(result["area_summary"]) == set(result["areas"])


def test_eval_runs_outside_project_root(monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent)

    result = run()

    assert result["dataset_size"] == 8


def test_eval_dataset_validation_rejects_invalid_jsonl():
    with pytest.raises(ValueError, match="Invalid JSONL row"):
        load_dataset(FIXTURES_DIR / "invalid_jsonl.jsonl")


def test_eval_dataset_validation_rejects_missing_fields():
    with pytest.raises(ValueError, match="missing fields"):
        load_dataset(FIXTURES_DIR / "missing_fields.jsonl")


def test_eval_dataset_validation_rejects_non_object_rows():
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_dataset(FIXTURES_DIR / "not_object.jsonl")


def test_eval_dataset_validation_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="Duplicate dataset id"):
        load_dataset(FIXTURES_DIR / "duplicate_ids.jsonl")


def test_eval_thresholds_fail_when_dataset_is_too_small():
    result = run(FIXTURES_DIR / "small_dataset.jsonl")

    assert result["passed"] is False
    assert any(
        failure["metric"] == "dataset_size"
        for failure in result["threshold_failures"]
    )
