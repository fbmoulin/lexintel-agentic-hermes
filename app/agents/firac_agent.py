from app.schemas.case import AgentResult


class FIRACAgent:
    name = "FIRACAgent"

    def run(self, case_id: str, normalized_case: dict, retrieved_contexts: list | None = None) -> AgentResult:
        """
        Produce a fixed mock AgentResult for the provided case identifier.
        
        Parameters:
        	case_id (str): Case identifier to include in the returned AgentResult.
        	normalized_case (dict): Accepted but not used by this implementation.
        	retrieved_contexts (list | None): Optional contexts; accepted but not used.
        
        Returns:
        	AgentResult: An AgentResult with `case_id` set to the provided `case_id`, `agent_name` set to the agent's `name`, `status` set to `"success"`, and `output` including empty lists for `facts`, `issues`, `rules`, `application`, `conclusion`, `risks`, and `missing_information`, plus `"recommended_decision_type": "analise"` and `"output_status": "mock_analysis_not_for_external_use"`. The returned object's top-level flags are `requires_human_review=True` and `external_use_allowed=False`.
        """
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
                "recommended_decision_type": "analise",
                "requires_human_review": True,
                "external_use_allowed": False,
                "output_status": "mock_analysis_not_for_external_use"
            },
            requires_human_review=True,
            external_use_allowed=False,
        )
