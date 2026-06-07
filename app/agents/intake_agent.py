from app.schemas.case import CaseInput, AgentResult


class IntakeAgent:
    name = "IntakeAgent"

    def run(self, case: CaseInput) -> AgentResult:
        """
        Classifies each file in the given case by simple keyword matching and returns a structured detection result for the next agent.
        
        Parameters:
            case (CaseInput): Input case containing `case_id` and an iterable `files` of file path or name strings.
        
        Returns:
            AgentResult: Result object with:
                - case_id: echoed from `case.case_id`
                - agent_name: this agent's name
                - status: "success"
                - output: dict containing:
                    - detected_documents (list): Per-file dictionaries with keys:
                        - doc_id (str): generated as "doc_<n>" where n is 1-based index
                        - file_path (str): original file string
                        - doc_type (str): one of "peticao_inicial", "contestacao", "sentenca", "acordao", or "unknown"
                        - confidence (float): 0.80 for recognized types, 0.50 for "unknown"
                    - next_agent (str): "SecurityAgent"
        """
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
