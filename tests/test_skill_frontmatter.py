"""The app/skills/*.md files carry Hermes/agentskills.io frontmatter so they are
loadable by a Hermes Agent install, while keeping the catalog contract
(`# SKILL_*` heading + `## Objetivo`)."""

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[1] / "app" / "skills"


def _split_frontmatter(text: str) -> tuple[str, str]:
    assert text.startswith("---\n"), "missing opening frontmatter delimiter"
    end = text.find("\n---\n", 4)
    assert end != -1, "unterminated frontmatter"
    return text[4:end], text[end + 5 :]


def test_all_skills_have_hermes_frontmatter_and_keep_catalog_contract():
    files = sorted(SKILLS_DIR.glob("SKILL_*.md"))
    # The exact count (12) is owned by test_catalog; here we only require that
    # every skill present carries frontmatter, so adding a skill won't break this.
    assert files, "Nenhum SKILL_*.md encontrado em app/skills/"

    for path in files:
        frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))

        # Hermes/agentskills.io required keys.
        for key in ("name:", "description:", "version:"):
            assert key in frontmatter, f"{path.name} frontmatter missing {key}"
        assert "hermes:" in frontmatter

        # Catalog contract preserved (skill_loader reads the heading + sections).
        assert "# SKILL_" in body, f"{path.name} lost its SKILL heading"
        assert "## Objetivo" in body, f"{path.name} lost ## Objetivo"
