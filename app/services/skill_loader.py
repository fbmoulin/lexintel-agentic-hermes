from pathlib import Path


def load_skill(skill_name: str) -> str:
    path = Path("app/skills") / skill_name
    if not path.exists():
        raise FileNotFoundError(f"Skill não encontrada: {skill_name}")
    return path.read_text(encoding="utf-8")
