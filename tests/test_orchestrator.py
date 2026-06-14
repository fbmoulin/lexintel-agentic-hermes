"""Orchestrator contract: a blocked step halts the pipeline before later phases."""

from app.agents.orchestrator import CaseOrchestrator
from app.schemas.case import AgentResult, CaseInput


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
