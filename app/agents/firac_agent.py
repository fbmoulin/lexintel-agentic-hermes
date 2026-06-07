from app.schemas.case import AgentResult


class FIRACAgent:
    name = "FIRACAgent"

    def run(self, case_id: str, normalized_case: dict, retrieved_contexts: list | None = None) -> AgentResult:
        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={
                "facts": [],
                "issues": [],
                "rules": [],
                "application": [],
                "conclusion": [],
                "risks": [],
                "missing_information": [],
                "recommended_decision_type": "analise"
            }
        )
