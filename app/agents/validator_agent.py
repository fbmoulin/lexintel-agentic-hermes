import re
import unicodedata

from app.schemas.case import AgentResult


class ValidatorAgent:
    name = "ValidatorAgent"

    def run(self, case_id: str, draft: dict) -> AgentResult:
        """
        Validate a draft for disallowed wording that indicates a hallucinated precedent.

        Scans the provided draft (converted to string and normalized) for the Portuguese phrase "precedente inventado" (including gender variants) and records a critical blocking error if found.

        Parameters:
            case_id (str): Identifier for the case being validated.
            draft (dict): Draft content to inspect; it will be converted to a string and normalized before scanning.

        Returns:
            AgentResult: Result object whose `status` is "success" when approved or "blocked" when a blocking error is found.
            The `output` payload includes:
                - `approved` (bool): `true` if no blocking errors were detected, `false` otherwise.
                - `blocking_errors` (list): List of blocking error dicts when violations are found.
                - `warnings` (list): Any non-blocking warnings (empty if none).
                - `final_recommendation` (str): "approve" if approved, otherwise "block".
            The returned AgentResult sets `requires_human_review` to `True` and `external_use_allowed` to `False`.
        """
        blocking_errors = []

        text = unicodedata.normalize("NFKD", str(draft)).lower()
        text = re.sub(r"\s+", " ", text)

        if re.search(r"\bprecedente\s+inventad[oa]\b", text):
            blocking_errors.append(
                {
                    "type": "hallucinated_precedent",
                    "severity": "critical",
                    "description": "Possível precedente inventado.",
                }
            )

        approved = len(blocking_errors) == 0

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success" if approved else "blocked",
            output={
                "approved": approved,
                "blocking_errors": blocking_errors,
                "warnings": [],
                "final_recommendation": "approve" if approved else "block",
                "requires_human_review": True,
                "external_use_allowed": False,
            },
            requires_human_review=True,
            external_use_allowed=False,
        )
