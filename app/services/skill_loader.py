from pathlib import Path


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
    path = Path("app/skills") / skill_name
    if not path.exists():
        raise FileNotFoundError(f"Skill não encontrada: {skill_name}")
    return path.read_text(encoding="utf-8")
