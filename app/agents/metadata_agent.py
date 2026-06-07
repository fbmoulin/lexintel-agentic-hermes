from app.schemas.case import AgentResult


class MetadataAgent:
    name = "MetadataAgent"

    def run(self, case_id: str, normalized_case: dict) -> AgentResult:
        """
        Produce an AgentResult containing metadata fields (all set to None) for the given case.
        
        Parameters:
            case_id (str): Identifier of the case.
            normalized_case (dict): Normalized case payload (not used by this agent).
        
        Returns:
            AgentResult: Result with `case_id`, `agent_name`, `status` set to "success", and an `output` dictionary containing the metadata keys `tribunal`, `classe`, `assunto`, `relator`, `orgao_julgador`, `data_julgamento`, `data_publicacao`, `ramo_direito`, `tipo_documento`, `tese_juridica`, and `resultado`, each assigned `None`.
        """
        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output={
                "tribunal": None,
                "classe": None,
                "assunto": None,
                "relator": None,
                "orgao_julgador": None,
                "data_julgamento": None,
                "data_publicacao": None,
                "ramo_direito": None,
                "tipo_documento": None,
                "tese_juridica": None,
                "resultado": None
            }
        )
