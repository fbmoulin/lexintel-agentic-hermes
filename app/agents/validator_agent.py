import re
import unicodedata

from app.schemas.case import AgentResult


class ValidatorAgent:
    name = "ValidatorAgent"

    def run(self, case_id: str, draft: dict) -> AgentResult:
        """
        Validate a draft for disallowed indications of a hallucinated precedent.

        Checks the provided draft for occurrences of the phrase "precedente
        inventado" and records a critical blocking error when found.
        """
        blocking_errors = []

        text = unicodedata.normalize("NFKD", str(draft)).lower()
        text = re.sub(r"\s+", " ", text)

        if re.search(r"\bprecedente\s+inventad[oa]\b", text):
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
