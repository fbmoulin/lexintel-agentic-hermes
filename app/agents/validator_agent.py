import re
import unicodedata

from app.schemas.case import AgentResult


class ValidatorAgent:
    name = "ValidatorAgent"

    def run(self, case_id: str, draft: dict) -> AgentResult:
        """
        Validate a draft for disallowed indications of a hallucinated precedent and return an AgentResult.
        
        Checks the provided draft for occurrences of the phrase "precedente inventado" and, if present, records a critical blocking error indicating a possible invented precedent. The returned AgentResult has status "success" when no blocking errors are found, otherwise "blocked". The AgentResult.output contains: `approved` (bool), `blocking_errors` (list), `warnings` (empty list), and `final_recommendation` ("approve" or "block").
        
        Parameters:
            case_id (str): Identifier of the case being validated.
            draft (dict): Draft content to validate.
        
        Returns:
            AgentResult: Result containing case_id, agent_name, status, and an output dict with validation details.
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
