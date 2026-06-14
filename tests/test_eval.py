from copy import deepcopy
from pathlib import Path

import pytest

from app.evals.run_eval import _smoke_retrieve, load_corpus, load_dataset, run

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "evals"


def test_eval_runs():
    result = run()

    assert "average_recall" in result
    assert result["dataset_size"] == 24
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
    # The eval exercises the served retriever: retrieved sources are populated.
    assert any(score["retrieved"] for score in result["results"])


def test_eval_scores_served_store_not_smoke_stub():
    # The smoke stub still exists but is NOT what run() uses.
    assert _smoke_retrieve("fraude no banco") == ["Súmula 479/STJ", "CDC art. 14"]


def test_eval_discriminates_on_retrieval_quality():
    """Mis-seeding a gold chunk must measurably lower recall — proves the gate
    tracks the served retriever's ranking, not a hardcoded answer."""
    good = run()

    broken_corpus = deepcopy(load_corpus())
    for chunk in broken_corpus:
        if chunk["metadata"].get("source_ref") == "Súmula 479/STJ":
            chunk["text"] = "conteudo irrelevante sem relacao com a consulta"

    degraded = run(corpus=broken_corpus)

    assert degraded["average_recall_at_3"] < good["average_recall_at_3"]


def test_eval_fails_with_empty_corpus():
    result = run(corpus=[])

    assert result["average_recall_at_3"] == 0.0
    assert result["passed"] is False


def test_eval_runs_outside_project_root(monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent)

    result = run()

    assert result["dataset_size"] == 24


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


def test_eval_dataset_validation_rejects_non_text_id_before_duplicate_lookup():
    """
    Verify that loading a dataset with a non-text `id` raises a `ValueError` and that the loader validates the `id` type before checking for duplicate IDs.

    Calls `load_dataset` with the `non_text_id.jsonl` fixture and expects a `ValueError` whose message matches "field id must be text".
    """
    with pytest.raises(ValueError, match="field id must be text"):
        load_dataset(FIXTURES_DIR / "non_text_id.jsonl")


def test_eval_thresholds_fail_when_dataset_is_too_small():
    result = run(FIXTURES_DIR / "small_dataset.jsonl")

    assert result["passed"] is False
    assert any(
        failure["metric"] == "dataset_size" for failure in result["threshold_failures"]
    )


def test_eval_threshold_overrides_can_be_partial():
    result = run(thresholds={"min_dataset_size": 1})

    assert result["passed"] is True
    assert result["thresholds"]["min_dataset_size"] == 1
    assert result["thresholds"]["min_average_recall_at_3"] == 0.85
    assert result["thresholds"]["min_average_mrr"] == 0.85
    assert result["thresholds"]["required_areas"] == [
        "bancario",
        "consumidor",
        "processual_civil",
        "saude",
    ]


def test_eval_thresholds_do_not_reuse_default_mutable_values():
    result = run()
    result["thresholds"]["required_areas"].append("mutated")

    next_result = run()

    assert "mutated" not in next_result["thresholds"]["required_areas"]
