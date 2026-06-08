from app.schemas.case import AgentResult, CaseMetadata


class MetadataAgent:
    name = "MetadataAgent"

    def run(self, case_id: str, normalized_case: dict) -> AgentResult:
        document_types = normalized_case.get("document_types", [])
        legal_issues = normalized_case.get("legal_issues", [])
        procedural_events = normalized_case.get("procedural_events", [])

        metadata = CaseMetadata(
            tribunal="TJ-MOCK" if "acordao" in document_types else None,
            classe="Procedimento Comum Cível"
            if "peticao_inicial" in document_types else None,
            assunto="Responsabilidade civil bancária"
            if legal_issues else None,
            relator="Relator Mockado" if "acordao" in document_types else None,
            orgao_julgador="Câmara Cível Mockada"
            if "acordao" in document_types else None,
            data_julgamento="2026-01-15" if "acordao" in document_types else None,
            data_publicacao="2026-01-20"
            if procedural_events else None,
            ramo_direito="Direito do Consumidor"
            if legal_issues else None,
            tipo_documento="conjunto_processual_mockado"
            if document_types else None,
            tese_juridica="Responsabilidade objetiva por fraude bancária"
            if legal_issues else None,
            resultado="parcialmente_procedente"
            if "sentenca" in document_types else None,
            document_types=document_types,
            document_count=len(normalized_case.get("source_doc_ids", [])),
            has_petition="peticao_inicial" in document_types,
            has_defense="contestacao" in document_types,
            has_decision="sentenca" in document_types,
            has_appeal_decision="acordao" in document_types,
        )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="success",
            output=metadata.model_dump(),
            external_use_allowed=False,
        )
