from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


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


DocumentType = Literal[
    "peticao_inicial",
    "contestacao",
    "sentenca",
    "acordao",
    "unknown",
]


class ExtractedText(BaseModel):
    doc_id: str
    file_path: str
    doc_type: DocumentType
    page: int = Field(ge=1)
    text: str = Field(min_length=1)
    quality_score: float = Field(ge=0.0, le=1.0)
    extraction_method: Literal["mock_filename_template"] = "mock_filename_template"
    warnings: list[str] = Field(default_factory=list)


class ExtractionQualitySummary(BaseModel):
    document_count: int = Field(ge=0)
    page_count: int = Field(ge=0)
    min_quality_score: float = Field(ge=0.0, le=1.0)
    average_quality_score: float = Field(ge=0.0, le=1.0)
    low_quality_pages: list[str] = Field(default_factory=list)
    automation_allowed: bool = False


class LegalParty(BaseModel):
    role: Literal["author", "defendant", "court", "appellant", "appellee", "unknown"]
    name: str
    source_doc_ids: list[str] = Field(default_factory=list)


class LegalClaim(BaseModel):
    claim_type: str
    summary: str
    source_doc_ids: list[str] = Field(default_factory=list)


class LegalDefense(BaseModel):
    defense_type: str
    summary: str
    source_doc_ids: list[str] = Field(default_factory=list)


class LegalEvidence(BaseModel):
    evidence_type: str
    summary: str
    source_doc_ids: list[str] = Field(default_factory=list)


class ProceduralEvent(BaseModel):
    event_type: str
    summary: str
    source_doc_ids: list[str] = Field(default_factory=list)


class LegalIssue(BaseModel):
    issue_type: str
    summary: str
    source_doc_ids: list[str] = Field(default_factory=list)


class NormalizedCase(BaseModel):
    case_id: str
    normalization_schema_version: str = "normalization-mock-v0.1"
    source_doc_ids: list[str] = Field(default_factory=list)
    document_types: list[DocumentType] = Field(default_factory=list)
    parties: list[LegalParty] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[LegalClaim] = Field(default_factory=list)
    cause_of_action: list[dict[str, Any]] = Field(default_factory=list)
    preliminary_issues: list[dict[str, Any]] = Field(default_factory=list)
    merit_prejudicials: list[dict[str, Any]] = Field(default_factory=list)
    defenses: list[LegalDefense] = Field(default_factory=list)
    evidence: list[LegalEvidence] = Field(default_factory=list)
    procedural_events: list[ProceduralEvent] = Field(default_factory=list)
    legal_issues: list[LegalIssue] = Field(default_factory=list)
    normalization_warnings: list[str] = Field(default_factory=list)


class CaseMetadata(BaseModel):
    metadata_schema_version: str = "metadata-mock-v0.1"
    tribunal: Optional[str] = None
    classe: Optional[str] = None
    assunto: Optional[str] = None
    relator: Optional[str] = None
    orgao_julgador: Optional[str] = None
    data_julgamento: Optional[str] = None
    data_publicacao: Optional[str] = None
    ramo_direito: Optional[str] = None
    tipo_documento: Optional[str] = None
    tese_juridica: Optional[str] = None
    resultado: Optional[str] = None
    document_types: list[DocumentType] = Field(default_factory=list)
    document_count: int = Field(default=0, ge=0)
    has_petition: bool = False
    has_defense: bool = False
    has_decision: bool = False
    has_appeal_decision: bool = False


ChunkUnitType = Literal[
    "ementa",
    "relatorio",
    "voto",
    "fundamentos",
    "dispositivo",
    "pedido",
    "contestacao",
    "prova",
    "tese",
    "precedente_citado",
    "documento",
]


class LegalChunk(BaseModel):
    chunk_id: str
    case_id: str
    doc_id: str
    unit_type: ChunkUnitType
    text: str = Field(min_length=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    source: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_page_range(self):
        if self.page_end < self.page_start:
            raise ValueError("page_end must be greater than or equal to page_start")
        return self


class IndexingSummary(BaseModel):
    indexing_schema_version: str = "indexing-mock-v0.1"
    vector_backend: str
    qdrant_enabled: bool = False
    chunk_count: int = Field(ge=0)
    indexed_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    chunk_unit_types: list[ChunkUnitType] = Field(default_factory=list)
    external_use_allowed: bool = False


class RetrievedContext(BaseModel):
    chunk_id: str
    doc_id: str
    score: float
    text: str
    source: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BlockingError(BaseModel):
    type: Literal[
        "missing_claim",
        "hallucinated_precedent",
        "unsupported_fact",
        "contradiction",
        "security_risk",
    ]
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    suggested_fix: Optional[str] = None


class ValidationResult(BaseModel):
    approved: bool
    blocking_errors: list[BlockingError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    final_recommendation: Literal["approve", "revise", "block"]
