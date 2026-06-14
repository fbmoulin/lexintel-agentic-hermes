from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health_check():
    """
    Return a static health-status payload for the service.

    Returns:
        dict: A JSON-serializable dictionary containing:
            - "status": "ok"
            - "service": the service identifier ("lex-kratos-agentic-core")
            - "version": the service version ("0.1.0")
    """
    return {"status": "ok", "service": "lex-kratos-agentic-core", "version": "0.1.0"}
