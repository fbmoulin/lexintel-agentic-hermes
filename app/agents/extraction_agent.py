from app.schemas.case import AgentResult


class ExtractionAgent:
    name = "ExtractionAgent"

    def run(self, case_id: str, documents: list[dict]) -> AgentResult:
        """
        Extracts simulated text records from a list of document metadata for a case.
        
        Parameters:
            case_id (str): Identifier of the case the documents belong to.
            documents (list[dict]): List of document metadata dictionaries. Each dictionary is expected to contain keys like `doc_id` and `file_path`; missing keys result in `None` values in the extracted records.
        
        Returns:
            AgentResult: Result object with `case_id`, `agent_name`, `status` set to `"success"`, `output` containing `{"extracted_text": [...]}` where each extracted record is a dict with keys:
                - `doc_id`: original document id or `None`
                - `page`: page number (always `1`)
                - `text`: simulated extracted text constructed from `file_path`
                - `quality_score`: extraction quality score (always `0.90`)
            and `warnings` as a list (empty by default).
        """
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
