from app.schemas.case import AgentResult


class LegalNormalizerAgent:
    name = "LegalNormalizerAgent"

    def run(self, case_id: str, extracted_text: list[dict]) -> AgentResult:
        """
        Produce an AgentResult for the given case with empty normalized legal fields.
        
        Parameters:
            case_id (str): Identifier of the case.
            extracted_text (list[dict]): Extracted text items (accepted but currently unused).
        
        Returns:
            AgentResult: An AgentResult with `case_id` set to `case_id`, `agent_name` set to the agent's name,
            `status` set to `"success"`, and `output` containing empty lists for `parties`, `claims`,
            `defenses`, `evidence`, `procedural_events`, and `legal_issues`.
        """
        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={
                "parties": [],
                "claims": [],
                "defenses": [],
                "evidence": [],
                "procedural_events": [],
                "legal_issues": []
            }
        )
