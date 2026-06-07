from app.schemas.case import AgentResult


class FIRACAgent:
    name = "FIRACAgent"

    def run(self, case_id: str, normalized_case: dict, retrieved_contexts: list | None = None) -> AgentResult:
        """
        Produce a fixed AgentResult for the specified case.
        
        Parameters:
            case_id (str): Identifier for the case; included in the returned AgentResult.
            normalized_case (dict): Accepted but not used by this implementation.
            retrieved_contexts (list | None): Optional contexts; accepted but not used.
        
        Returns:
            AgentResult: Result with `case_id` set to `case_id`, `agent_name` set to the agent's `name`, `status` "success", and `output` containing empty lists for "facts", "issues", "rules", "application", "conclusion", "risks", and "missing_information", plus `"recommended_decision_type": "analise"`.
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
