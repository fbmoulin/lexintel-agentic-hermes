from app.schemas.case import AgentResult


class LegalNormalizerAgent:
    name = "LegalNormalizerAgent"

    def run(self, case_id: str, extracted_text: list[dict]) -> AgentResult:
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
