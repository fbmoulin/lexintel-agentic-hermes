import pytest
from fastapi.testclient import TestClient

from app.agents import registry as agent_registry
from app.agents.registry import list_agent_registry, validate_agent_registry
from app.main import app
from app.services.skill_loader import list_skills, load_skill


client = TestClient(app)


def test_skill_loader_lists_all_versioned_skills():
    skills = list_skills()

    assert len(skills) == 12
    assert {skill["skill_name"] for skill in skills} == {
        "SKILL_DOCUMENT_INTAKE.md",
        "SKILL_FIRAC_PLUS_CIVIL.md",
        "SKILL_HYBRID_LEGAL_RETRIEVAL.md",
        "SKILL_JUDICIAL_DRAFTING_CIVIL.md",
        "SKILL_JUDICIAL_VALIDATION.md",
        "SKILL_LEGAL_CHUNKING_AND_INDEXING.md",
        "SKILL_LEGAL_METADATA_ENRICHMENT.md",
        "SKILL_LEGAL_NORMALIZATION.md",
        "SKILL_LEGAL_PDF_EXTRACTION.md",
        "SKILL_LLM_SECURITY_GUARDRAILS.md",
        "SKILL_PRECEDENT_VALIDATION.md",
        "SKILL_RAG_EVALUATION.md",
    }
    assert all(skill["title"].startswith("SKILL_") for skill in skills)
    assert all("Objetivo" in skill["sections"] for skill in skills)


def test_skill_loader_rejects_path_traversal():
    with pytest.raises(ValueError):
        load_skill("../AGENTS.md")


def test_agent_registry_is_valid_and_links_skills():
    validation = validate_agent_registry()
    agents = list_agent_registry()

    assert validation["valid"] is True
    assert validation["issues"] == []
    assert validation["agent_count"] == 12
    assert validation["implemented_count"] == 7
    assert validation["planned_count"] == 5
    assert validation["skill_count"] == 12

    implemented_agents = [agent for agent in agents if agent["implemented"]]
    assert all(agent["class_importable"] is True for agent in implemented_agents)
    assert all(agent["skill"]["exists"] is True for agent in agents)

    human_review_agents = [
        agent for agent in agents
        if agent["phase"] in agent_registry.HUMAN_REVIEW_PHASES
    ]
    assert all(
        agent.get("requires_human_review") is True
        for agent in human_review_agents
    )


def test_agent_registry_rejects_missing_human_review_for_validation(monkeypatch):
    patched_registry = [
        dict(entry) for entry in agent_registry.AGENT_REGISTRY
    ]
    validator_entry = next(
        entry for entry in patched_registry
        if entry["phase"] == "validation"
    )
    validator_entry.pop("requires_human_review", None)
    monkeypatch.setattr(agent_registry, "AGENT_REGISTRY", patched_registry)

    validation = agent_registry.validate_agent_registry()

    assert validation["valid"] is False
    assert {
        "type": "missing_human_review_flag",
        "agent_name": "ValidatorAgent",
        "phase": "validation",
    } in validation["issues"]


def test_agent_registry_missing_skill_manifest_is_structured(monkeypatch):
    patched_registry = [
        {
            **agent_registry.AGENT_REGISTRY[0],
            "skill_name": "SKILL_MISSING.md",
        }
    ]
    monkeypatch.setattr(agent_registry, "AGENT_REGISTRY", patched_registry)

    agents = agent_registry.list_agent_registry()
    validation = agent_registry.validate_agent_registry()

    assert agents[0]["missing_skill"] is True
    assert agents[0]["skill"] == {
        "skill_name": "SKILL_MISSING.md",
        "title": "SKILL_MISSING",
        "sections": [],
        "line_count": 0,
        "char_count": 0,
        "exists": False,
    }
    assert {
        "type": "missing_skill",
        "agent_name": "IntakeAgent",
        "skill_name": "SKILL_MISSING.md",
    } in validation["issues"]


def test_catalog_skills_endpoint_lists_skills():
    response = client.get("/catalog/skills")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 12
    assert data["skills"][0]["skill_name"].startswith("SKILL_")


def test_catalog_skill_detail_endpoint_returns_content():
    response = client.get("/catalog/skills/SKILL_DOCUMENT_INTAKE.md")

    assert response.status_code == 200
    data = response.json()
    assert data["skill_name"] == "SKILL_DOCUMENT_INTAKE.md"
    assert data["title"] == "SKILL_DOCUMENT_INTAKE"
    assert "## Objetivo" in data["content"]


def test_catalog_skill_detail_rejects_invalid_name():
    response = client.get("/catalog/skills/nonexistent.md")

    assert response.status_code == 400


def test_catalog_skill_detail_missing_skill_returns_404():
    response = client.get("/catalog/skills/SKILL_nonexistent.md")

    assert response.status_code == 404


def test_catalog_agents_endpoint_returns_registry():
    response = client.get("/catalog/agents")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["count"] == 12
    assert data["implemented_count"] == 7
    assert data["planned_count"] == 5
    assert data["issues"] == []

    intake = next(
        agent for agent in data["agents"]
        if agent["agent_name"] == "IntakeAgent"
    )
    assert intake["phase"] == "intake"
    assert intake["skill"]["skill_name"] == "SKILL_DOCUMENT_INTAKE.md"
