from app.schemas.case import AgentResult


class MetadataAgent:
    name = "MetadataAgent"

    def run(self, case_id: str, normalized_case: dict) -> AgentResult:
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
