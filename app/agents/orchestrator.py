from app.agents.extraction_agent import ExtractionAgent
from app.agents.firac_agent import FIRACAgent
from app.agents.indexing_agent import IndexingAgent
from app.agents.intake_agent import IntakeAgent
from app.agents.metadata_agent import MetadataAgent
from app.agents.normalizer_agent import LegalNormalizerAgent
from app.agents.security_agent import SecurityAgent
from app.agents.validator_agent import ValidatorAgent
from app.schemas.case import CaseInput


class CaseOrchestrator:
    TRACE_VERSION = "trace-v0.2"
    INTAKE_PIPELINE = "case-intake-v0.2"
    FULL_MOCK_PIPELINE = "case-full-mock-v0.2"

    def __init__(self):
        """
        Create a CaseOrchestrator and instantiate its downstream agents.

        Instantiated attributes:
            intake_agent: Handles initial case intake and detects documents.
            security_agent: Assesses case content for security or policy blocking.
            extraction_agent: Extracts text from detected documents.
            normalizer_agent: Normalizes and cleans extracted legal text.
            metadata_agent: Produces case metadata from normalized text.
            indexing_agent: Chunks and indexes extracted text in a mock vector store.
            firac_agent: Generates FIRAC-structured analysis from normalized text.
            validator_agent: Validates draft outputs and may mark them blocked or requiring review.
        """
        self.intake_agent = IntakeAgent()
        self.security_agent = SecurityAgent()
        self.extraction_agent = ExtractionAgent()
        self.normalizer_agent = LegalNormalizerAgent()
        self.metadata_agent = MetadataAgent()
        self.indexing_agent = IndexingAgent()
        self.firac_agent = FIRACAgent()
        self.validator_agent = ValidatorAgent()

    @staticmethod
    def _build_security_text(case: CaseInput, intake_output: dict) -> str:
        """
        Compose newline-separated input text for the security agent from the case's identifying fields and the intake output.

        Parameters:
            case (CaseInput): Provides `case_id`, `source_type`, `user_goal`, and `files` whose values are included in the text in that order.
            intake_output (dict): Intake agent output appended to the text as its string representation.

        Returns:
            str: A single string with the listed fields joined by newline characters.
        """
        parts = [
            case.case_id,
            case.source_type,
            case.user_goal,
            *case.files,
            str(intake_output),
        ]
        return "\n".join(parts)

    def _record_trace(self, trace: list[dict], result, step_index: int, phase: str):
        """
        Update an agent's result with propagated review/external-use flags, attach trace metadata, append its serialized form to the trace, and return the updated result.

        Parameters:
            trace (list[dict]): Mutable list representing the pipeline trace; the function appends the agent's serialized result to this list.
            result: Agent execution result object whose attributes are updated (`requires_human_review`, `external_use_allowed`, `trace_metadata`) and which must provide `output`, `status`, `agent_name`, `model_dump()` and existing flag attributes.
            step_index (int): Numeric index of the agent step within the pipeline (used in trace metadata).
            phase (str): Logical phase name for the step (used in trace metadata).

        Returns:
            The same `result` object after mutation.
        """
        output_requires_review = bool(result.output.get("requires_human_review", False))
        output_external_allowed = bool(result.output.get("external_use_allowed", False))

        result.requires_human_review = (
            result.requires_human_review
            or output_requires_review
            or result.status in {"warning", "blocked"}
        )
        result.external_use_allowed = (
            result.external_use_allowed and output_external_allowed
        )
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
        """
        Builds an aggregated summary of a pipeline run from a list of per-agent trace entries.

        Parameters:
            trace (list[dict]): Ordered list of agent trace entries. Each entry is expected to include the keys
                "agent_name", "status", "warnings" (list), "errors" (list),
                "requires_human_review" (bool), and "external_use_allowed" (bool).
            pipeline_name (str): Logical name of the pipeline being summarized.

        Returns:
            dict: Summary with the following keys:
                - trace_version (str): Trace schema/version label.
                - pipeline_name (str): The provided pipeline_name.
                - agent_count (int): Number of entries in the trace.
                - completed_agents (list[str]): Agent names in trace order.
                - blocked_at (str|None): Agent name where the first "blocked" status occurred, or None.
                - warning_count (int): Total number of warnings across all entries.
                - error_count (int): Total number of errors across all entries.
                - requires_human_review (bool): True if any entry requests human review.
                - external_use_allowed (bool): True only if all entries allow external use; False for empty traces.
        """
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
            )
            if trace
            else False,
        }

    @staticmethod
    def _response_status(trace: list[dict]) -> str:
        """
        Determine the overall pipeline status from a sequence of agent trace entries.

        Parameters:
            trace (list[dict]): Ordered list of per-agent trace dictionaries; each entry is expected to include a "status" key.

        Returns:
            str: `"blocked"` if any trace entry has `status == "blocked"`, `"warning"` if no entries are blocked but at least one has `status == "warning"`, otherwise `"success"`.
        """
        if any(entry["status"] == "blocked" for entry in trace):
            return "blocked"

        if any(entry["status"] == "failed" for entry in trace):
            return "failed"

        if any(entry["status"] == "warning" for entry in trace):
            return "warning"

        return "success"

    def run_intake_only(self, case: CaseInput):
        """
        Run intake and security steps and return their ordered trace plus an aggregated pipeline summary.

        Parameters:
            case (CaseInput): Input case data containing at minimum `case_id` and fields consumed by the intake agent.

        Returns:
            dict: A result dictionary with keys:
                - case_id (str): The input case's identifier.
                - status (str): Overall pipeline status; `"blocked"` if any step is blocked, `"warning"` if any step has warnings and none are blocked, otherwise `"success"`.
                - trace (list[dict]): Ordered list of per-agent trace entries produced by `_record_trace`.
                - pipeline_summary (dict): Aggregated pipeline metadata produced by `_summarize_trace`.
                - requires_human_review (bool): `True` if any trace entry requires human review.
                - external_use_allowed (bool): `False` for intake-only runs (external use is not permitted).

            Note:
                If the security step blocks the case, `status` will be `"blocked"`, `requires_human_review` will be `True`, and `external_use_allowed` will be `False`.
        """
        trace = []

        intake_result = self.intake_agent.run(case)
        self._record_trace(trace, intake_result, 1, "intake")

        security_result = self.security_agent.run(
            case_id=case.case_id,
            text=self._build_security_text(case, intake_result.output),
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
                "external_use_allowed": False,
            }

        return {
            "case_id": case.case_id,
            "status": self._response_status(trace),
            "trace": trace,
            "pipeline_summary": pipeline_summary,
            "requires_human_review": pipeline_summary["requires_human_review"],
            "external_use_allowed": False,
        }

    def run_full_mock(self, case: CaseInput):
        """
        Execute the full mock case processing pipeline (intake → security → extraction → normalization → metadata → indexing → FIRAC → mock draft → validation).

        Parameters:
            case (CaseInput): Input case; must include `case.case_id`. If present, `case` may include `detected_documents` used by extraction.

        Returns:
            dict: Pipeline execution result containing:
                - case_id (str): The input case's ID.
                - status (str): Overall pipeline status: `blocked`, `warning`, or `success`.
                - trace (list[dict]): Ordered per-agent trace entries produced during execution.
                - pipeline_summary (dict): Aggregated metadata about the executed pipeline.
                - mock_draft (dict, optional): The mocked draft used for validation (contains `relatorio`, `fundamentacao`, `dispositivo`, and draft flags). Present only when the pipeline proceeds past security.
                - requires_human_review (bool): True if any step requires human review.
                - external_use_allowed (bool): Whether the pipeline allows external use (always `False` for this mock pipeline).
        """
        trace = []

        intake_result = self.intake_agent.run(case)
        self._record_trace(trace, intake_result, 1, "intake")

        security_result = self.security_agent.run(
            case.case_id, self._build_security_text(case, intake_result.output)
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
                "external_use_allowed": False,
            }

        documents = intake_result.output.get("detected_documents", [])

        extraction_result = self.extraction_agent.run(case.case_id, documents)
        self._record_trace(trace, extraction_result, 3, "extraction")

        normalizer_result = self.normalizer_agent.run(
            case.case_id, extraction_result.output.get("extracted_text", [])
        )
        self._record_trace(trace, normalizer_result, 4, "normalization")

        metadata_result = self.metadata_agent.run(
            case.case_id, normalizer_result.output
        )
        self._record_trace(trace, metadata_result, 5, "metadata")

        indexing_result = self.indexing_agent.run(
            case.case_id,
            extraction_result.output.get("extracted_text", []),
        )
        self._record_trace(trace, indexing_result, 6, "indexing")

        firac_result = self.firac_agent.run(case.case_id, normalizer_result.output)
        self._record_trace(trace, firac_result, 7, "firac")

        mock_draft = {
            "relatorio": "Relatório simulado.",
            "fundamentacao": "Fundamentação simulada.",
            "dispositivo": "Dispositivo simulado.",
            "requires_human_review": True,
            "external_use_allowed": False,
            "draft_status": "mock_not_for_external_use",
        }

        validator_result = self.validator_agent.run(case.case_id, mock_draft)
        self._record_trace(trace, validator_result, 8, "validation")
        pipeline_summary = self._summarize_trace(trace, self.FULL_MOCK_PIPELINE)

        return {
            "case_id": case.case_id,
            "status": self._response_status(trace),
            "trace": trace,
            "pipeline_summary": pipeline_summary,
            "mock_draft": mock_draft,
            "requires_human_review": pipeline_summary["requires_human_review"],
            "external_use_allowed": False,
        }
