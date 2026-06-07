from fastapi import APIRouter
from app.schemas.case import CaseInput
from app.agents.orchestrator import CaseOrchestrator

router = APIRouter()


@router.post("/intake")
def intake_case(case: CaseInput):
    orchestrator = CaseOrchestrator()
    return orchestrator.run_intake_only(case)


@router.post("/run-full-mock")
def run_full_mock(case: CaseInput):
    orchestrator = CaseOrchestrator()
    return orchestrator.run_full_mock(case)
