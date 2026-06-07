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
        """
        Initialize the orchestrator by creating and assigning its downstream agent instances.
        
        Attributes:
            intake_agent: Processes initial case intake and extracts detected documents.
            security_agent: Evaluates case content for security or policy blocking.
            extraction_agent: Extracts raw text from detected documents.
            normalizer_agent: Normalizes and cleans extracted legal text.
            metadata_agent: Generates case metadata from normalized text.
            firac_agent: Produces FIRAC-structured analysis from normalized text.
            validator_agent: Validates (or blocks) draft outputs.
        """
        self.intake_agent = IntakeAgent()
        self.security_agent = SecurityAgent()
        self.extraction_agent = ExtractionAgent()
        self.normalizer_agent = LegalNormalizerAgent()
        self.metadata_agent = MetadataAgent()
        self.firac_agent = FIRACAgent()
        self.validator_agent = ValidatorAgent()

    def run_intake_only(self, case: CaseInput):
        """
        Run intake and security checks for a case and collect the per-step results.
        
        Parameters:
            case (CaseInput): Case data including `case_id` and any fields used by intake.
        
        Returns:
            dict: A summary containing:
                - `case_id` (str): The input case's identifier.
                - `status` (str): `"blocked"` if the security check blocked the case, otherwise `"success"`.
                - `trace` (list): Ordered list of model-dumped results from each agent call (intake then security).
        """
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
        """
        Execute the full mock processing pipeline for a case and return the aggregated results and a mocked draft.
        
        Runs intake, security, extraction, normalization, metadata, FIRAC, and validation agents in sequence, collecting each agent's model_dump() output into a trace. If the security agent blocks the case, the pipeline stops early and returns a blocked status. Validation runs against a fixed mocked draft; the overall status is "blocked" if validation is blocked, otherwise "success".
        
        Parameters:
            case (CaseInput): Input case object; must include `case.case_id`. If present, `case` may contain detected documents under `detected_documents` used by the extraction step.
        
        Returns:
            dict: A dictionary with keys:
                - `case_id`: the input case's ID.
                - `status`: `"success"` if validation did not block the case, `"blocked"` otherwise (or if security blocked earlier).
                - `trace`: a list of each agent's `model_dump()` results in execution order.
                - `mock_draft`: the mocked draft dictionary used for validation with keys `relatorio`, `fundamentacao`, and `dispositivo`.
        """
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
