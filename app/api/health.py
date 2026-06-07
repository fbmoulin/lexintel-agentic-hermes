from fastapi import APIRouter

router = APIRouter()

@router.get("")
def health_check():
    return {
        "status": "ok",
        "service": "lex-kratos-agentic-core",
        "version": "0.1.0"
    }
