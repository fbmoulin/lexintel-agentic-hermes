from pydantic import BaseModel, Field
from typing import Literal, Optional, Any


class CaseInput(BaseModel):
    case_id: str
    source_type: Literal["pdf", "datajud", "manual", "drive", "pje_export"]
    user_goal: Literal["minuta", "analise", "triagem", "jurimetria", "relatorio"]
    files: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    case_id: str
    agent_name: str
    status: Literal["success", "warning", "failed", "blocked"]
    output: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    external_use_allowed: bool = False
    trace_metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedContext(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    text: str
    source: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    approved: bool
    blocking_errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    final_recommendation: Literal["approve", "revise", "block"]
