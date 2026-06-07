from app.schemas.case import CaseInput
from app.agents.intake_agent import IntakeAgent
from app.agents.security_agent import SecurityAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.normalizer_agent import LegalNormalizerAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.firac_agent import FIRACAgent
from app.agents.validator_agent import ValidatorAgent


class CaseOrchestrator:
    def __init__(self):
        self.intake_agent = IntakeAgent()
        self.security_agent = SecurityAgent()
        self.extraction_agent = ExtractionAgent()
        self.normalizer_agent = LegalNormalizerAgent()
        self.metadata_agent = MetadataAgent()
        self.firac_agent = FIRACAgent()
        self.validator_agent = ValidatorAgent()

    def run_intake_only(self, case: CaseInput):
        trace = []

        intake_result = self.intake_agent.run(case)
        trace.append(intake_result.model_dump())

        security_result = self.security_agent.run(
            case_id=case.case_id,
            text=str(intake_result.output)
        )
        trace.append(security_result.model_dump())

        if security_result.status == "blocked":
            return {
                "case_id": case.case_id,
                "status": "blocked",
                "trace": trace
            }

        return {
            "case_id": case.case_id,
            "status": "success",
            "trace": trace
        }

    def run_full_mock(self, case: CaseInput):
        trace = []

        intake_result = self.intake_agent.run(case)
        trace.append(intake_result.model_dump())

        security_result = self.security_agent.run(case.case_id, str(intake_result.output))
        trace.append(security_result.model_dump())

        if security_result.status == "blocked":
            return {"case_id": case.case_id, "status": "blocked", "trace": trace}

        documents = intake_result.output.get("detected_documents", [])

        extraction_result = self.extraction_agent.run(case.case_id, documents)
        trace.append(extraction_result.model_dump())

        normalizer_result = self.normalizer_agent.run(
            case.case_id,
            extraction_result.output.get("extracted_text", [])
        )
        trace.append(normalizer_result.model_dump())

        metadata_result = self.metadata_agent.run(case.case_id, normalizer_result.output)
        trace.append(metadata_result.model_dump())

        firac_result = self.firac_agent.run(case.case_id, normalizer_result.output)
        trace.append(firac_result.model_dump())

        mock_draft = {
            "relatorio": "Relatório simulado.",
            "fundamentacao": "Fundamentação simulada.",
            "dispositivo": "Dispositivo simulado."
        }

        validator_result = self.validator_agent.run(case.case_id, mock_draft)
        trace.append(validator_result.model_dump())

        return {
            "case_id": case.case_id,
            "status": "success" if validator_result.status != "blocked" else "blocked",
            "trace": trace,
            "mock_draft": mock_draft
        }
