"""Orchestrator contract: a blocked step halts the pipeline before later phases."""

import pytest
from pydantic import ValidationError

from app.agents.indexing_agent import IndexingAgent
from app.agents.orchestrator import CaseOrchestrator
from app.schemas.case import AgentResult, CaseInput


def test_agent_result_rejects_orphan_failed_status():
    # No pipeline agent emits "failed" (indexing degrades to "warning"), and the
    # per-step guards halt only on "blocked". Keeping "failed" in the vocabulary
    # would advertise a terminal state the control flow doesn't back — so it is
    # removed. A hard terminal error uses "blocked" (which halts).
    with pytest.raises(ValidationError):
        AgentResult(case_id="c", agent_name="X", status="failed", output={})


def _case() -> CaseInput:
    return CaseInput(
        case_id="caso_halt_001",
        source_type="manual",
        user_goal="analise",
        files=["peticao_inicial.pdf"],
    )


class _BlockingExtractionAgent:
    name = "ExtractionAgent"

    def run(self, case_id, documents):
        return AgentResult(
            case_id=case_id,
            agent_name="ExtractionAgent",
            status="blocked",
            output={},
            errors=["bloqueio simulado na extração"],
            requires_human_review=True,
        )


def test_full_mock_halts_on_midpipeline_block():
    orchestrator = CaseOrchestrator()
    orchestrator.extraction_agent = _BlockingExtractionAgent()

    result = orchestrator.run_full_mock(_case())

    assert result["status"] == "blocked"
    assert result["requires_human_review"] is True
    completed = [entry["agent_name"] for entry in result["trace"]]
    # Intake + Security ran, Extraction blocked — nothing downstream executed.
    assert completed == ["IntakeAgent", "SecurityAgent", "ExtractionAgent"]
    assert result["pipeline_summary"]["blocked_at"] == "ExtractionAgent"

    phases = {entry["trace_metadata"]["phase"] for entry in result["trace"]}
    assert "normalization" not in phases
    assert "validation" not in phases


def test_full_mock_completes_when_no_block():
    result = CaseOrchestrator().run_full_mock(_case())

    completed = [entry["agent_name"] for entry in result["trace"]]
    assert completed[-1] == "ValidatorAgent"
    assert result["status"] in {"success", "warning"}


def test_full_mock_pipeline_runs_retrieval_after_indexing():
    result = CaseOrchestrator().run_full_mock(_case())

    phases = [entry["trace_metadata"]["phase"] for entry in result["trace"]]
    assert "retrieval" in phases
    assert phases.index("retrieval") == phases.index("indexing") + 1
    retrieval_entry = next(
        e for e in result["trace"] if e["trace_metadata"]["phase"] == "retrieval"
    )
    assert retrieval_entry["output"]["retrieval_method"] == "hybrid"
    assert result["pipeline_summary"]["trace_version"] == "trace-v0.3"


class _HallucinatingFIRACAgent:
    name = "FIRACAgent"

    def run(self, case_id, normalized_case, retrieved_contexts=None):
        # FIRAC output is routed into the draft; this reaches the validator.
        return AgentResult(
            case_id=case_id,
            agent_name="FIRACAgent",
            status="success",
            output={
                "conclusion": ["O modelo citou um precedente inventado."],
                "requires_human_review": True,
                "external_use_allowed": False,
            },
            requires_human_review=True,
        )


def test_validator_blocks_on_hallucinated_precedent_through_pipeline():
    orchestrator = CaseOrchestrator()
    orchestrator.firac_agent = _HallucinatingFIRACAgent()

    result = orchestrator.run_full_mock(_case())

    assert result["status"] == "blocked"
    assert result["pipeline_summary"]["blocked_at"] == "ValidatorAgent"
    completed = [entry["agent_name"] for entry in result["trace"]]
    assert completed[-1] == "ValidatorAgent"


class _FailingUpsertStore:
    backend_name = "mock"

    def upsert(self, chunks):
        raise RuntimeError("falha simulada de upsert")

    def search(self, query, top_k=5, filters=None):
        return []


def test_failed_indexing_degrades_to_warning_without_halting():
    orchestrator = CaseOrchestrator()
    orchestrator.indexing_agent = IndexingAgent(vector_store=_FailingUpsertStore())

    result = orchestrator.run_full_mock(_case())

    # Indexing is best-effort: an upsert failure surfaces as a review-flagged
    # WARNING, does not halt the pipeline, and does not stamp the whole run
    # "failed" (the legal analysis downstream is unaffected by a broken index).
    assert result["status"] == "warning"
    assert result["requires_human_review"] is True
    completed = [entry["agent_name"] for entry in result["trace"]]
    assert completed[-1] == "ValidatorAgent"
