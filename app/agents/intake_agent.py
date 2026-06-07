from app.schemas.case import CaseInput, AgentResult


class IntakeAgent:
    name = "IntakeAgent"

    def run(self, case: CaseInput) -> AgentResult:
        detected_documents = []

        for index, file in enumerate(case.files):
            lowered = file.lower()
            if "inicial" in lowered:
                doc_type = "peticao_inicial"
                confidence = 0.80
            elif "contestacao" in lowered or "contestação" in lowered:
                doc_type = "contestacao"
                confidence = 0.80
            elif "sentenca" in lowered or "sentença" in lowered:
                doc_type = "sentenca"
                confidence = 0.80
            elif "acordao" in lowered or "acórdão" in lowered:
                doc_type = "acordao"
                confidence = 0.80
            else:
                doc_type = "unknown"
                confidence = 0.50

            detected_documents.append({
                "doc_id": f"doc_{index + 1}",
                "file_path": file,
                "doc_type": doc_type,
                "confidence": confidence
            })

        return AgentResult(
            case_id=case.case_id,
            agent_name=self.name,
            status="success",
            output={
                "detected_documents": detected_documents,
                "next_agent": "SecurityAgent"
            }
        )
