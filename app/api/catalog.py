from fastapi import APIRouter, HTTPException

from app.agents.registry import list_agent_registry, validate_agent_registry
from app.services.skill_loader import get_skill_manifest, list_skills, load_skill

router = APIRouter()


@router.get("/skills")
def get_skills():
    skills = list_skills()
    return {
        "count": len(skills),
        "skills": skills,
    }


@router.get("/skills/{skill_name}")
def get_skill(skill_name: str):
    try:
        manifest = get_skill_manifest(skill_name)
        return {
            **manifest,
            "content": load_skill(skill_name),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/agents")
def get_agents():
    agents = list_agent_registry()
    validation = validate_agent_registry()
    return {
        "count": len(agents),
        "implemented_count": validation["implemented_count"],
        "planned_count": validation["planned_count"],
        "skill_count": validation["skill_count"],
        "valid": validation["valid"],
        "issues": validation["issues"],
        "agents": agents,
    }
