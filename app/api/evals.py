from fastapi import APIRouter

from app.evals.run_eval import run

router = APIRouter()


@router.get("/run")
def run_evaluation():
    """
    Trigger the evaluation process and return its result.

    Returns:
        The evaluation result object.
    """
    return run()
