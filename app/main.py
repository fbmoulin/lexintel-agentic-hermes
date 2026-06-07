from fastapi import FastAPI
from app.api import health, cases, rag, evals

app = FastAPI(
    title="Lex Kratos Agentic Core",
    version="0.1.0",
    description="Núcleo agentico modular para automação jurídica auditável."
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(evals.router, prefix="/eval", tags=["eval"])
