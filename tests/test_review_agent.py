from app.agents.review_agent import ReviewAgent


def test_review_agent_rejects_empty_trace():
    """ReviewAgent should block when trace is empty."""
    ra = ReviewAgent()
    result = ra.run("case_empty_001", trace=[])

    assert result.status == "blocked"
    assert result.output["review_status"] == "rejected"
    assert result.output["confidence_score"] == 0.0
    assert len(result.output["consistency_issues"]) > 0
    assert result.output["consistency_issues"][0]["type"] == "empty_trace"
    assert result.requires_human_review is True
    assert result.external_use_allowed is False


def test_review_agent_approves_clean_trace():
    """ReviewAgent should approve a trace with all success statuses."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "IntakeAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "SecurityAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "FIRACAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "output": {"firac_analysis": "mocked"},
            "requires_human_review": True,
            "external_use_allowed": False,
        },
    ]

    result = ra.run("case_clean_001", trace)

    assert result.status == "success"
    assert result.output["review_status"] == "approved"
    assert result.output["confidence_score"] >= 0.8
    assert result.output["trace_coverage"]["agent_count"] == 3
    assert result.requires_human_review is True


def test_review_agent_warns_on_warnings():
    """ReviewAgent should produce warning status when agents have warnings."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "IntakeAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "IndexingAgent",
            "status": "warning",
            "warnings": ["Indexação degradada"],
            "errors": [],
            "output": {"index_status": "upsert_failed"},
            "requires_human_review": True,
            "external_use_allowed": False,
        },
    ]

    result = ra.run("case_warning_001", trace)

    assert result.status == "warning"
    assert result.output["review_status"] == "conditional"
    assert result.output["confidence_score"] < 1.0
    assert len(result.output["consistency_issues"]) > 0
    assert any(
        issue["type"] == "indexing_failure"
        for issue in result.output["consistency_issues"]
    )
    assert len(result.warnings) > 0


def test_review_agent_blocks_on_blocked_trace():
    """ReviewAgent should block when any agent in trace is blocked."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "IntakeAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "SecurityAgent",
            "status": "blocked",
            "warnings": [],
            "errors": ["Prompt injection detectado"],
            "requires_human_review": True,
            "external_use_allowed": False,
        },
    ]

    result = ra.run("case_blocked_001", trace)

    assert result.status == "blocked"
    assert result.output["review_status"] == "rejected"
    assert result.output["confidence_score"] == 0.0
    assert len(result.errors) > 0
    assert any("bloqueado" in rec for rec in result.output["recommendations"])


def test_review_agent_detects_firac_without_retrieval():
    """ReviewAgent should detect when FIRAC succeeds but retrieval failed."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "IndexingAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "output": {"index_status": "ok"},
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "HybridRetrievalAgent",
            "status": "warning",
            "warnings": ["Retrieval falhou"],
            "errors": [],
            "output": {"retrieval_status": "failed"},
            "requires_human_review": True,
            "external_use_allowed": False,
        },
        {
            "agent_name": "FIRACAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "output": {"firac_analysis": "mocked"},
            "requires_human_review": True,
            "external_use_allowed": False,
        },
    ]

    result = ra.run("case_firac_no_context_001", trace)

    assert result.status == "warning"
    assert result.output["confidence_score"] < 1.0
    consistency_issue_types = [
        issue["type"] for issue in result.output["consistency_issues"]
    ]
    assert "retrieval_failure" in consistency_issue_types
    assert "firac_without_complete_context" in consistency_issue_types


def test_review_agent_calculates_confidence_score():
    """ReviewAgent should calculate proper confidence scores based on trace quality."""
    ra = ReviewAgent()

    perfect_trace = [
        {
            "agent_name": "Agent1",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        }
    ]
    result_perfect = ra.run("case_score_001", perfect_trace)
    assert result_perfect.output["confidence_score"] == 1.0

    warning_trace = [
        {
            "agent_name": "Agent1",
            "status": "warning",
            "warnings": ["Warning 1"],
            "errors": [],
            "requires_human_review": True,
            "external_use_allowed": False,
        }
    ]
    result_warning = ra.run("case_score_002", warning_trace)
    assert 0.0 < result_warning.output["confidence_score"] < 1.0

    blocked_trace = [
        {
            "agent_name": "Agent1",
            "status": "blocked",
            "warnings": [],
            "errors": ["Error 1"],
            "requires_human_review": True,
            "external_use_allowed": False,
        }
    ]
    result_blocked = ra.run("case_score_003", blocked_trace)
    assert result_blocked.output["confidence_score"] == 0.0


def test_review_agent_provides_recommendations():
    """ReviewAgent should provide actionable recommendations."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "SecurityAgent",
            "status": "warning",
            "warnings": ["Entrada suspeita"],
            "errors": [],
            "requires_human_review": True,
            "external_use_allowed": False,
        }
    ]

    result = ra.run("case_recs_001", trace)

    assert len(result.output["recommendations"]) > 0
    assert any("warning" in rec.lower() for rec in result.output["recommendations"])


def test_review_agent_trace_coverage():
    """ReviewAgent should report accurate trace coverage statistics."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "IntakeAgent",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": False,
        },
        {
            "agent_name": "SecurityAgent",
            "status": "warning",
            "warnings": ["Warning"],
            "errors": [],
            "requires_human_review": True,
            "external_use_allowed": False,
        },
        {
            "agent_name": "FIRACAgent",
            "status": "blocked",
            "warnings": [],
            "errors": ["Error"],
            "requires_human_review": True,
            "external_use_allowed": False,
        },
    ]

    result = ra.run("case_coverage_001", trace)

    coverage = result.output["trace_coverage"]
    assert coverage["agent_count"] == 3
    assert "IntakeAgent" in coverage["completed_agents"]
    assert "SecurityAgent" in coverage["warning_agents"]
    assert "FIRACAgent" in coverage["blocked_agents"]


def test_review_agent_always_requires_human_review():
    """ReviewAgent output always requires human review."""
    ra = ReviewAgent()
    trace = [
        {
            "agent_name": "Agent1",
            "status": "success",
            "warnings": [],
            "errors": [],
            "requires_human_review": False,
            "external_use_allowed": True,
        }
    ]

    result = ra.run("case_human_001", trace)

    assert result.requires_human_review is True
    assert result.external_use_allowed is False
    assert result.output["requires_human_review"] is True
    assert result.output["external_use_allowed"] is False
