from app.schemas.case import AgentResult


class ValidatorAgent:
    name = "ValidatorAgent"

    def run(self, case_id: str, draft: dict) -> AgentResult:
        blocking_errors = []

        text = str(draft).lower()

        if "precedente inventado" in text:
            blocking_errors.append({
                "type": "hallucinated_precedent",
                "severity": "critical",
                "description": "Possível precedente inventado."
            })

        approved = len(blocking_errors) == 0

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success" if approved else "blocked",
            output={
                "approved": approved,
                "blocking_errors": blocking_errors,
                "warnings": [],
                "final_recommendation": "approve" if approved else "block"
            }
        )
