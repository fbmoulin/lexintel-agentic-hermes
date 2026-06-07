from app.schemas.case import CaseInput
from app.agents.intake_agent import IntakeAgent
from app.agents.security_agent import SecurityAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.normalizer_agent import LegalNormalizerAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.firac_agent import FIRACAgent
from app.agents.validator_agent import ValidatorAgent


class CaseOrchestrator:
    TRACE_VERSION = "trace-v0.2"
    INTAKE_PIPELINE = "case-intake-v0.2"
    FULL_MOCK_PIPELINE = "case-full-mock-v0.2"

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

    @staticmethod
    def _build_security_text(case: CaseInput, intake_output: dict) -> str:
        parts = [
            case.case_id,
            case.source_type,
            case.user_goal,
            *case.files,
            str(intake_output),
        ]
        return "\n".join(parts)

    def _record_trace(self, trace: list[dict], result, step_index: int, phase: str):
        output_requires_review = bool(result.output.get("requires_human_review", False))
        output_external_allowed = bool(result.output.get("external_use_allowed", False))

        result.requires_human_review = (
            result.requires_human_review
            or output_requires_review
            or result.status in {"warning", "blocked"}
        )
        result.external_use_allowed = result.external_use_allowed and output_external_allowed
        result.trace_metadata = {
            "trace_version": self.TRACE_VERSION,
            "step_index": step_index,
            "phase": phase,
            "agent_name": result.agent_name,
            "status": result.status,
        }

        trace.append(result.model_dump())
        return result

    def _summarize_trace(self, trace: list[dict], pipeline_name: str) -> dict:
        blocked_entry = next(
            (entry for entry in trace if entry["status"] == "blocked"),
            None,
        )

        return {
            "trace_version": self.TRACE_VERSION,
            "pipeline_name": pipeline_name,
            "agent_count": len(trace),
            "completed_agents": [entry["agent_name"] for entry in trace],
            "blocked_at": blocked_entry["agent_name"] if blocked_entry else None,
            "warning_count": sum(len(entry["warnings"]) for entry in trace),
            "error_count": sum(len(entry["errors"]) for entry in trace),
            "requires_human_review": any(
                entry["requires_human_review"] for entry in trace
            ),
            "external_use_allowed": all(
                entry["external_use_allowed"] for entry in trace
            ) if trace else False,
        }

    @staticmethod
    def _response_status(trace: list[dict]) -> str:
        if any(entry["status"] == "blocked" for entry in trace):
            return "blocked"

        if any(entry["status"] == "warning" for entry in trace):
            return "warning"

        return "success"

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
        self._record_trace(trace, intake_result, 1, "intake")

        security_result = self.security_agent.run(
            case_id=case.case_id,
            text=self._build_security_text(case, intake_result.output)
        )
        self._record_trace(trace, security_result, 2, "security")
        pipeline_summary = self._summarize_trace(trace, self.INTAKE_PIPELINE)

        if security_result.status == "blocked":
            return {
                "case_id": case.case_id,
                "status": "blocked",
                "trace": trace,
                "pipeline_summary": pipeline_summary,
                "requires_human_review": True,
                "external_use_allowed": False
            }

        return {
            "case_id": case.case_id,
            "status": self._response_status(trace),
            "trace": trace,
            "pipeline_summary": pipeline_summary,
            "requires_human_review": pipeline_summary["requires_human_review"],
            "external_use_allowed": False
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
        self._record_trace(trace, intake_result, 1, "intake")

        security_result = self.security_agent.run(
            case.case_id,
            self._build_security_text(case, intake_result.output)
        )
        self._record_trace(trace, security_result, 2, "security")

        if security_result.status == "blocked":
            pipeline_summary = self._summarize_trace(trace, self.FULL_MOCK_PIPELINE)
            return {
                "case_id": case.case_id,
                "status": "blocked",
                "trace": trace,
                "pipeline_summary": pipeline_summary,
                "requires_human_review": True,
                "external_use_allowed": False
            }

        documents = intake_result.output.get("detected_documents", [])

        extraction_result = self.extraction_agent.run(case.case_id, documents)
        self._record_trace(trace, extraction_result, 3, "extraction")

        normalizer_result = self.normalizer_agent.run(
            case.case_id,
            extraction_result.output.get("extracted_text", [])
        )
        self._record_trace(trace, normalizer_result, 4, "normalization")

        metadata_result = self.metadata_agent.run(case.case_id, normalizer_result.output)
        self._record_trace(trace, metadata_result, 5, "metadata")

        firac_result = self.firac_agent.run(case.case_id, normalizer_result.output)
        self._record_trace(trace, firac_result, 6, "firac")

        mock_draft = {
            "relatorio": "Relatório simulado.",
            "fundamentacao": "Fundamentação simulada.",
            "dispositivo": "Dispositivo simulado.",
            "requires_human_review": True,
            "external_use_allowed": False,
            "draft_status": "mock_not_for_external_use"
        }

        validator_result = self.validator_agent.run(case.case_id, mock_draft)
        self._record_trace(trace, validator_result, 7, "validation")
        pipeline_summary = self._summarize_trace(trace, self.FULL_MOCK_PIPELINE)

        return {
            "case_id": case.case_id,
            "status": self._response_status(trace),
            "trace": trace,
            "pipeline_summary": pipeline_summary,
            "mock_draft": mock_draft,
            "requires_human_review": pipeline_summary["requires_human_review"],
            "external_use_allowed": False
        }
