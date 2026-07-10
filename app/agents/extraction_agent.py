from app.schemas.case import (
    AgentResult,
    ExtractedText,
    ExtractionQualitySummary,
)
from app.services.extraction import Extractor, MockExtractor

_KNOWN_DOC_TYPES = {"peticao_inicial", "contestacao", "sentenca", "acordao"}


class ExtractionAgent:
    name = "ExtractionAgent"

    def __init__(self, extractor: Extractor | None = None):
        self._extractor = extractor or MockExtractor()

    def run(self, case_id: str, documents: list[dict]) -> AgentResult:
        extracted = []
        warnings = []

        if not documents:
            warnings.append(
                "Nenhum documento detectado para extração mockada; revisão humana obrigatória."
            )

        for doc in documents:
            doc_type = doc.get("doc_type", "unknown")
            if doc_type not in _KNOWN_DOC_TYPES:
                doc_type = "unknown"

            quality_score = 0.92 if doc_type != "unknown" else 0.68
            page_warnings = []
            if quality_score < 0.70:
                warning = (
                    f"Baixa qualidade de extração mockada em {doc.get('doc_id')}; "
                    "revisão humana obrigatória."
                )
                page_warnings.append(warning)
                warnings.append(warning)

            extracted_item = ExtractedText(
                doc_id=doc.get("doc_id") or "doc_unknown",
                file_path=doc.get("file_path") or "",
                doc_type=doc_type,
                page=1,
                text=self._extractor.extract(doc.get("file_path") or "", doc_type).text,
                quality_score=quality_score,
                warnings=page_warnings,
            )
            extracted.append(extracted_item.model_dump())

        quality_scores = [item["quality_score"] for item in extracted] or [0.0]
        low_quality_pages = [
            f"{item['doc_id']}:p{item['page']}"
            for item in extracted
            if item["quality_score"] < 0.70
        ]
        quality_summary = ExtractionQualitySummary(
            document_count=len(documents),
            page_count=len(extracted),
            min_quality_score=min(quality_scores),
            average_quality_score=sum(quality_scores) / len(quality_scores),
            low_quality_pages=low_quality_pages,
            automation_allowed=bool(extracted) and not low_quality_pages,
        )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="warning" if warnings else "success",
            output={
                "extraction_schema_version": "extraction-mock-v0.1",
                "extracted_text": extracted,
                "quality_summary": quality_summary.model_dump(),
                "requires_human_review": bool(warnings),
                "external_use_allowed": False,
            },
            warnings=warnings,
            requires_human_review=bool(warnings),
            external_use_allowed=False,
        )
