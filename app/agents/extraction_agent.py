from app.schemas.case import AgentResult


class ExtractionAgent:
    name = "ExtractionAgent"

    def run(self, case_id: str, documents: list[dict]) -> AgentResult:
        extracted = []
        warnings = []

        for doc in documents:
            extracted.append({
                "doc_id": doc.get("doc_id"),
                "page": 1,
                "text": f"Texto simulado extraído de {doc.get('file_path')}.",
                "quality_score": 0.90
            })

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={"extracted_text": extracted},
            warnings=warnings
        )
