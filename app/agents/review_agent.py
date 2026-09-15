from typing import Literal

from app.schemas.case import AgentResult


class ReviewAgent:
    """
    ReviewAgent performs a holistic review of the completed pipeline trace.

    This agent inspects the full execution trace to assess overall quality,
    consistency, and completeness. It identifies potential inconsistencies
    between agent outputs, calculates a confidence score, and provides
    human-readable recommendations for any issues requiring attention.

    The ReviewAgent is designed to run after the ValidatorAgent as a final
    quality gate before human review.
    """

    name = "ReviewAgent"
    review_version = "review-agent-v0.1"

    @staticmethod
    def _calculate_confidence_score(trace: list[dict]) -> float:
        """
        Calculate confidence score from trace entries.

        Parameters:
            trace: List of agent trace entries with status, warnings, and errors.

        Returns:
            float: Confidence score between 0.0 and 1.0, where 1.0 is highest confidence.
        """
        if not trace:
            return 0.0

        blocked_count = sum(1 for entry in trace if entry["status"] == "blocked")
        warning_count = sum(1 for entry in trace if entry["status"] == "warning")
        total_warnings = sum(len(entry.get("warnings", [])) for entry in trace)
        total_errors = sum(len(entry.get("errors", [])) for entry in trace)

        if blocked_count > 0:
            return 0.0

        penalty = (
            (warning_count * 0.1) + (total_warnings * 0.05) + (total_errors * 0.15)
        )

        base_score = 1.0
        confidence = max(0.0, base_score - penalty)

        return round(confidence, 3)

    @staticmethod
    def _check_trace_consistency(trace: list[dict]) -> list[dict]:
        """
        Check for logical inconsistencies in the trace.

        Parameters:
            trace: List of agent trace entries.

        Returns:
            list[dict]: List of detected consistency issues.
        """
        issues = []

        firac_entry = next(
            (entry for entry in trace if entry.get("agent_name") == "FIRACAgent"),
            None,
        )
        indexing_entry = next(
            (entry for entry in trace if entry.get("agent_name") == "IndexingAgent"),
            None,
        )
        retrieval_entry = next(
            (
                entry
                for entry in trace
                if entry.get("agent_name") == "HybridRetrievalAgent"
            ),
            None,
        )

        if indexing_entry and indexing_entry["status"] == "warning":
            index_status = indexing_entry.get("output", {}).get("index_status")
            if index_status == "upsert_failed":
                issues.append(
                    {
                        "type": "indexing_failure",
                        "severity": "medium",
                        "description": "Indexação falhou; retrieval pode estar incompleto.",
                        "agent": "IndexingAgent",
                    }
                )

        if retrieval_entry and retrieval_entry["status"] == "warning":
            retrieval_status = retrieval_entry.get("output", {}).get("retrieval_status")
            if retrieval_status == "failed":
                issues.append(
                    {
                        "type": "retrieval_failure",
                        "severity": "medium",
                        "description": "Retrieval híbrido falhou; contexto pode estar ausente.",
                        "agent": "HybridRetrievalAgent",
                    }
                )

        if (
            firac_entry
            and firac_entry["status"] == "success"
            and retrieval_entry
            and retrieval_entry["status"] == "warning"
        ):
            issues.append(
                {
                    "type": "firac_without_complete_context",
                    "severity": "low",
                    "description": "FIRAC gerado mas retrieval teve problemas.",
                    "agent": "FIRACAgent,HybridRetrievalAgent",
                }
            )

        return issues

    @staticmethod
    def _generate_recommendations(
        confidence_score: float, consistency_issues: list[dict], trace: list[dict]
    ) -> list[str]:
        """
        Generate human-readable recommendations based on review findings.

        Parameters:
            confidence_score: Calculated confidence score.
            consistency_issues: List of detected consistency issues.
            trace: Full pipeline trace.

        Returns:
            list[str]: List of recommendation strings.
        """
        recommendations = []

        if confidence_score < 0.5:
            recommendations.append(
                "Confiança muito baixa - revisão humana completa recomendada."
            )
        elif confidence_score < 0.8:
            recommendations.append(
                "Confiança moderada - verificar warnings e erros reportados."
            )

        critical_issues = [
            issue for issue in consistency_issues if issue["severity"] == "high"
        ]
        if critical_issues:
            recommendations.append(
                f"Detectados {len(critical_issues)} problemas críticos de consistência."
            )

        blocked_agents = [
            entry["agent_name"] for entry in trace if entry["status"] == "blocked"
        ]
        if blocked_agents:
            recommendations.append(
                f"Pipeline bloqueado em: {', '.join(blocked_agents)}."
            )

        warning_agents = [
            entry["agent_name"] for entry in trace if entry["status"] == "warning"
        ]
        if warning_agents:
            recommendations.append(
                f"Warnings em: {', '.join(warning_agents)} - revisar outputs."
            )

        if not recommendations:
            recommendations.append(
                "Pipeline executado com alta confiança - revisão de rotina recomendada."
            )

        return recommendations

    def run(
        self, case_id: str, trace: list[dict], draft: dict | None = None
    ) -> AgentResult:
        """
        Review the completed pipeline trace for quality and consistency.

        Parameters:
            case_id (str): Identifier for the case being reviewed.
            trace (list[dict]): Complete ordered trace of agent executions.
            draft (dict, optional): The draft output to be reviewed for consistency.

        Returns:
            AgentResult: Review assessment containing:
                - status: "blocked" if critical issues found, "warning" if moderate
                  issues exist, "success" otherwise.
                - output: dict with keys:
                    - review_status: "approved", "conditional", or "rejected".
                    - confidence_score: float between 0.0 and 1.0.
                    - consistency_issues: list of detected issues.
                    - recommendations: list of human-readable recommendations.
                    - trace_coverage: dict with agent coverage stats.
                    - review_version: version string of this review agent.
                - warnings: present when review identifies concerns.
                - requires_human_review: always True for this agent.
                - external_use_allowed: False (review output is internal).
        """
        if not trace:
            return AgentResult(
                case_id=case_id,
                agent_name=self.name,
                status="blocked",
                output={
                    "review_status": "rejected",
                    "confidence_score": 0.0,
                    "consistency_issues": [
                        {
                            "type": "empty_trace",
                            "severity": "critical",
                            "description": "Trace vazio - pipeline não executou.",
                        }
                    ],
                    "recommendations": ["Pipeline não produziu trace - investigar."],
                    "trace_coverage": {"agent_count": 0, "completed_agents": []},
                    "review_version": self.review_version,
                },
                errors=["Trace vazio - impossível revisar."],
                requires_human_review=True,
                external_use_allowed=False,
            )

        confidence_score = self._calculate_confidence_score(trace)
        consistency_issues = self._check_trace_consistency(trace)
        recommendations = self._generate_recommendations(
            confidence_score, consistency_issues, trace
        )

        blocked_count = sum(1 for entry in trace if entry["status"] == "blocked")
        warning_count = sum(1 for entry in trace if entry["status"] == "warning")

        status: Literal["success", "warning", "blocked"]
        if blocked_count > 0 or confidence_score < 0.3:
            review_status = "rejected"
            status = "blocked"
            errors = [
                f"Pipeline com {blocked_count} bloqueios e confiança {confidence_score}."
            ]
            warnings_list = []
        elif warning_count > 0 or confidence_score < 0.8:
            review_status = "conditional"
            status = "warning"
            errors = []
            warnings_list = [
                f"Pipeline com {warning_count} warnings e confiança {confidence_score}."
            ]
        else:
            review_status = "approved"
            status = "success"
            errors = []
            warnings_list = []

        trace_coverage = {
            "agent_count": len(trace),
            "completed_agents": [entry["agent_name"] for entry in trace],
            "blocked_agents": [
                entry["agent_name"] for entry in trace if entry["status"] == "blocked"
            ],
            "warning_agents": [
                entry["agent_name"] for entry in trace if entry["status"] == "warning"
            ],
        }

        return AgentResult(
            case_id=case_id,
            agent_name=self.name,
            status=status,
            output={
                "review_status": review_status,
                "confidence_score": confidence_score,
                "consistency_issues": consistency_issues,
                "recommendations": recommendations,
                "trace_coverage": trace_coverage,
                "review_version": self.review_version,
                "requires_human_review": True,
                "external_use_allowed": False,
            },
            errors=errors,
            warnings=warnings_list,
            requires_human_review=True,
            external_use_allowed=False,
        )
