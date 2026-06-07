from fastapi import APIRouter
from app.evals.run_eval import run

router = APIRouter()


@router.get("/run")
def run_evaluation():
    return run()
