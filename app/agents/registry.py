from importlib import import_module

from app.services.skill_loader import get_skill_manifest, list_skills


AGENT_REGISTRY = [
    {
        "agent_name": "IntakeAgent",
        "phase": "intake",
        "module_path": "app.agents.intake_agent",
        "class_name": "IntakeAgent",
        "skill_name": "SKILL_DOCUMENT_INTAKE.md",
        "status": "implemented",
        "mocked": True,
        "description": "Classifica documentos e monta o pacote inicial mockado.",
    },
    {
        "agent_name": "SecurityAgent",
        "phase": "security",
        "module_path": "app.agents.security_agent",
        "class_name": "SecurityAgent",
        "skill_name": "SKILL_LLM_SECURITY_GUARDRAILS.md",
        "status": "implemented",
        "mocked": True,
        "description": "Detecta prompt injection e comandos maliciosos locais.",
    },
    {
        "agent_name": "ExtractionAgent",
        "phase": "extraction",
        "module_path": "app.agents.extraction_agent",
        "class_name": "ExtractionAgent",
        "skill_name": "SKILL_LEGAL_PDF_EXTRACTION.md",
        "status": "implemented",
        "mocked": True,
        "description": "Simula extração de texto preservando contrato de qualidade.",
    },
    {
        "agent_name": "LegalNormalizerAgent",
        "phase": "normalization",
        "module_path": "app.agents.normalizer_agent",
        "class_name": "LegalNormalizerAgent",
        "skill_name": "SKILL_LEGAL_NORMALIZATION.md",
        "status": "implemented",
        "mocked": True,
        "description": "Normaliza estrutura jurídica em campos mockados.",
    },
    {
        "agent_name": "MetadataAgent",
        "phase": "metadata",
        "module_path": "app.agents.metadata_agent",
        "class_name": "MetadataAgent",
        "skill_name": "SKILL_LEGAL_METADATA_ENRICHMENT.md",
        "status": "implemented",
        "mocked": True,
        "description": "Gera metadados jurídicos mockados.",
    },
    {
        "agent_name": "IndexingAgent",
        "phase": "indexing",
        "module_path": None,
        "class_name": None,
        "skill_name": "SKILL_LEGAL_CHUNKING_AND_INDEXING.md",
        "status": "planned",
        "mocked": True,
        "description": "Planejado para chunking e indexação jurídica.",
    },
    {
        "agent_name": "HybridRetrievalAgent",
        "phase": "retrieval",
        "module_path": None,
        "class_name": None,
        "skill_name": "SKILL_HYBRID_LEGAL_RETRIEVAL.md",
        "status": "planned",
        "mocked": True,
        "description": "Planejado para busca híbrida e reranking.",
    },
    {
        "agent_name": "FIRACAgent",
        "phase": "firac",
        "module_path": "app.agents.firac_agent",
        "class_name": "FIRACAgent",
        "skill_name": "SKILL_FIRAC_PLUS_CIVIL.md",
        "status": "implemented",
        "mocked": True,
        "requires_human_review": True,
        "description": "Produz análise FIRAC+ mockada com revisão humana obrigatória.",
    },
    {
        "agent_name": "JurisprudenceAgent",
        "phase": "precedent_validation",
        "module_path": None,
        "class_name": None,
        "skill_name": "SKILL_PRECEDENT_VALIDATION.md",
        "status": "planned",
        "mocked": True,
        "requires_human_review": True,
        "description": "Planejado para validação jurisprudencial.",
    },
    {
        "agent_name": "DraftingAgent",
        "phase": "drafting",
        "module_path": None,
        "class_name": None,
        "skill_name": "SKILL_JUDICIAL_DRAFTING_CIVIL.md",
        "status": "planned",
        "mocked": True,
        "requires_human_review": True,
        "description": "Planejado para geração de minutas com revisão humana.",
    },
    {
        "agent_name": "ValidatorAgent",
        "phase": "validation",
        "module_path": "app.agents.validator_agent",
        "class_name": "ValidatorAgent",
        "skill_name": "SKILL_JUDICIAL_VALIDATION.md",
        "status": "implemented",
        "mocked": True,
        "description": "Audita saídas mockadas e bloqueia sinais de precedente inventado.",
    },
    {
        "agent_name": "EvaluationAgent",
        "phase": "evaluation",
        "module_path": None,
        "class_name": None,
        "skill_name": "SKILL_RAG_EVALUATION.md",
        "status": "planned",
        "mocked": True,
        "description": "Planejado como agente; avaliação mockada já existe em app.evals.",
    },
]


def _is_importable(module_path: str | None, class_name: str | None) -> bool:
    if not module_path or not class_name:
        return False

    try:
        module = import_module(module_path)
        return hasattr(module, class_name)
    except (ImportError, ModuleNotFoundError):
        return False


def list_agent_registry() -> list[dict]:
    agents = []
    for entry in AGENT_REGISTRY:
        try:
            skill_manifest = get_skill_manifest(entry["skill_name"])
            missing_skill = False
        except (FileNotFoundError, ValueError):
            skill_manifest = {"exists": False}
            missing_skill = True

        agent_dict = {
            **entry,
            "implemented": entry["status"] == "implemented",
            "class_importable": _is_importable(
                entry["module_path"],
                entry["class_name"],
            ),
            "skill": skill_manifest,
        }

        if missing_skill:
            agent_dict["missing_skill"] = True

        agents.append(agent_dict)
    return agents


def validate_agent_registry() -> dict:
    issues = []
    agents = list_agent_registry()
    skill_names = {skill["skill_name"] for skill in list_skills()}
    mapped_skill_names = {agent["skill_name"] for agent in agents}

    for agent in agents:
        if agent["implemented"] and not agent["class_importable"]:
            issues.append({
                "type": "missing_agent_class",
                "agent_name": agent["agent_name"],
                "module_path": agent["module_path"],
                "class_name": agent["class_name"],
            })

        if not agent["skill"]["exists"]:
            issues.append({
                "type": "missing_skill",
                "agent_name": agent["agent_name"],
                "skill_name": agent["skill_name"],
            })

        # Validate that agents in legal-analysis/drafting phases require human review
        if agent["phase"] in {"firac", "precedent_validation", "drafting"}:
            if not agent.get("requires_human_review", False):
                issues.append({
                    "type": "missing_human_review_flag",
                    "agent_name": agent["agent_name"],
                    "phase": agent["phase"],
                })

    unmapped_skills = sorted(skill_names - mapped_skill_names)
    for skill_name in unmapped_skills:
        issues.append({
            "type": "unmapped_skill",
            "skill_name": skill_name,
        })

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "agent_count": len(agents),
        "implemented_count": sum(agent["implemented"] for agent in agents),
        "planned_count": sum(not agent["implemented"] for agent in agents),
        "skill_count": len(skill_names),
    }
