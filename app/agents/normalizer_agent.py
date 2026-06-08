from app.schemas.case import (
    AgentResult,
    LegalClaim,
    LegalDefense,
    LegalEvidence,
    LegalIssue,
    LegalParty,
    NormalizedCase,
    ProceduralEvent,
)


class LegalNormalizerAgent:
    name = "LegalNormalizerAgent"

    def run(self, case_id: str, extracted_text: list[dict]) -> AgentResult:
        doc_ids = [
            item["doc_id"] for item in extracted_text
            if item.get("doc_id")
        ]
        document_types = sorted({
            item.get("doc_type", "unknown") for item in extracted_text
        })
        source_ids_by_type = {
            doc_type: self._doc_ids_by_type(extracted_text, doc_type)
            for doc_type in document_types
        }

        parties = []
        claims = []
        defenses = []
        evidence = []
        procedural_events = []
        legal_issues = []
        facts = []
        cause_of_action = []
        normalization_warnings = []

        if "peticao_inicial" in document_types:
            parties.extend([
                LegalParty(
                    role="author",
                    name="Consumidor Alfa",
                    source_doc_ids=source_ids_by_type["peticao_inicial"],
                ),
                LegalParty(
                    role="defendant",
                    name="Banco Beta",
                    source_doc_ids=source_ids_by_type["peticao_inicial"],
                ),
            ])
            claims.append(LegalClaim(
                claim_type="indenizacao_dano_moral_material",
                summary="Pedido mockado de indenização por fraude bancária via pix.",
                source_doc_ids=source_ids_by_type["peticao_inicial"],
            ))
            evidence.extend([
                LegalEvidence(
                    evidence_type="comprovante_transferencia",
                    summary="Comprovante de transferência citado na petição inicial mockada.",
                    source_doc_ids=source_ids_by_type["peticao_inicial"],
                ),
                LegalEvidence(
                    evidence_type="boletim_ocorrencia",
                    summary="Boletim de ocorrência citado na petição inicial mockada.",
                    source_doc_ids=source_ids_by_type["peticao_inicial"],
                ),
            ])
            facts.append({
                "fact_type": "fraude_bancaria_pix",
                "summary": "Fraude bancária via pix narrada em documento mockado.",
                "source_doc_ids": source_ids_by_type["peticao_inicial"],
            })
            cause_of_action.append({
                "cause_type": "falha_prestacao_servico_bancario",
                "summary": "Causa de pedir mockada fundada em responsabilidade objetiva.",
                "source_doc_ids": source_ids_by_type["peticao_inicial"],
            })

        if "contestacao" in document_types:
            defenses.append(LegalDefense(
                defense_type="culpa_exclusiva_terceiro",
                summary="Defesa mockada de culpa exclusiva de terceiro e ausência de falha.",
                source_doc_ids=source_ids_by_type["contestacao"],
            ))
            evidence.append(LegalEvidence(
                evidence_type="logs_autenticacao",
                summary="Logs de autenticação indicados na contestação mockada.",
                source_doc_ids=source_ids_by_type["contestacao"],
            ))

        if "sentenca" in document_types:
            procedural_events.append(ProceduralEvent(
                event_type="sentenca_publicada",
                summary="Sentença mockada parcialmente procedente.",
                source_doc_ids=source_ids_by_type["sentenca"],
            ))

        if "acordao" in document_types:
            procedural_events.append(ProceduralEvent(
                event_type="julgamento_colegiado",
                summary="Acórdão mockado que mantém a sentença.",
                source_doc_ids=source_ids_by_type["acordao"],
            ))

        if {"peticao_inicial", "contestacao"} & set(document_types):
            legal_issues.append(LegalIssue(
                issue_type="responsabilidade_bancaria_fraude",
                summary="Questão mockada sobre responsabilidade objetiva em fraude bancária.",
                source_doc_ids=doc_ids,
            ))

        if "unknown" in document_types:
            normalization_warnings.append(
                "Documento sem classificação jurídica suficiente para normalização completa."
            )

        normalized_case = NormalizedCase(
            case_id=case_id,
            source_doc_ids=doc_ids,
            document_types=document_types,
            parties=parties,
            facts=facts,
            claims=claims,
            cause_of_action=cause_of_action,
            preliminary_issues=[],
            merit_prejudicials=[],
            defenses=defenses,
            evidence=evidence,
            procedural_events=procedural_events,
            legal_issues=legal_issues,
            normalization_warnings=normalization_warnings,
        )

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status="warning" if normalization_warnings else "success",
            output=normalized_case.model_dump(),
            warnings=normalization_warnings,
            requires_human_review=bool(normalization_warnings),
            external_use_allowed=False,
        )

    @staticmethod
    def _doc_ids_by_type(extracted_text: list[dict], doc_type: str) -> list[str]:
        return [
            item["doc_id"] for item in extracted_text
            if item.get("doc_type") == doc_type and item.get("doc_id")
        ]
