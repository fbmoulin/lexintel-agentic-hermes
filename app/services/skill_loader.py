from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


def _resolve_skill_path(skill_name: str) -> Path:
    if not skill_name:
        raise ValueError("Nome da skill não pode ser vazio.")

    candidate = Path(skill_name)
    if candidate.name != skill_name:
        raise ValueError("Nome de skill deve ser apenas o arquivo, sem caminho.")

    if not skill_name.startswith("SKILL_") or candidate.suffix != ".md":
        raise ValueError("Skill deve seguir o padrão SKILL_*.md.")

    path = (SKILLS_DIR / skill_name).resolve()
    if path.parent != SKILLS_DIR.resolve():
        raise ValueError("Caminho de skill inválido.")

    return path


def parse_skill_document(skill_name: str, content: str) -> dict:
    lines = content.splitlines()
    title = next(
        (line.removeprefix("#").strip() for line in lines if line.startswith("# ")),
        Path(skill_name).stem,
    )
    sections = [
        line.removeprefix("##").strip() for line in lines if line.startswith("## ")
    ]

    return {
        "skill_name": skill_name,
        "title": title,
        "sections": sections,
        "line_count": len(lines),
        "char_count": len(content),
    }


def load_skill(skill_name: str) -> str:
    """
    Load and return the text contents of a skill file located under app/skills.

    Parameters:
        skill_name (str): File name or relative path of the skill under app/skills.

    Returns:
        str: The UTF-8 decoded contents of the skill file.

    Raises:
        FileNotFoundError: If no file exists at app/skills/{skill_name}.
    """
    path = _resolve_skill_path(skill_name)
    if not path.exists():
        raise FileNotFoundError(f"Skill não encontrada: {skill_name}")
    return path.read_text(encoding="utf-8")


def get_skill_manifest(skill_name: str) -> dict:
    content = load_skill(skill_name)
    manifest = parse_skill_document(skill_name, content)
    manifest["exists"] = True
    return manifest


def list_skills() -> list[dict]:
    skills = []
    for path in sorted(SKILLS_DIR.glob("SKILL_*.md")):
        content = path.read_text(encoding="utf-8")
        manifest = parse_skill_document(path.name, content)
        manifest["exists"] = True
        skills.append(manifest)
    return skills
