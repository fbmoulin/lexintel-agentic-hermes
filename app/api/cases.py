from fastapi import APIRouter

from app.agents.orchestrator import CaseOrchestrator
from app.schemas.case import CaseInput

router = APIRouter()


@router.post("/intake")
def intake_case(case: CaseInput):
    """
    Trigger intake processing for the given case and return the orchestrator's intake result.

    Parameters:
        case (CaseInput): The case data submitted in the request body.

    Returns:
        The intake processing result produced by the orchestrator (structure depends on the orchestrator's implementation).
    """
    orchestrator = CaseOrchestrator()
    return orchestrator.run_intake_only(case)


@router.post("/run-full-mock")
def run_full_mock(case: CaseInput):
    """
    Run the full mock workflow for the given case.

    Parameters:
        case (CaseInput): Case data to process.

    Returns:
        The result produced by the full mock orchestration (typically a dict or model representing the workflow output).
    """
    orchestrator = CaseOrchestrator()
    return orchestrator.run_full_mock(case)
