from app.evals.run_eval import run
from pathlib import Path


def test_eval_runs():
    result = run()
    assert "average_recall" in result
    assert result["dataset_size"] > 0


def test_eval_runs_outside_project_root(monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent)

    result = run()

    assert result["dataset_size"] == 4
