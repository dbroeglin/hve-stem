"""Tests for stem.workspace — skill and agent discovery."""

from pathlib import Path

from stem.workspace import Agent, Skill, Workspace, load_workspace

WORKSPACE_ROOT = Path(__file__).parent / "workspace"


def test_load_workspace_returns_workspace() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assert isinstance(ws, Workspace)
    assert ws.root == WORKSPACE_ROOT.resolve()


def test_discovers_skills() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assert len(ws.skills) >= 1

    names = [s.name for s in ws.skills]
    assert "toto" in names


def test_skill_fields_populated() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    toto = next(s for s in ws.skills if s.name == "toto")

    assert isinstance(toto, Skill)
    assert toto.description == "This is a skill for Totos"
    assert "I'm a Toto!!!" in toto.body
    assert (
        toto.path
        == (WORKSPACE_ROOT / ".agents" / "skills" / "toto" / "SKILL.md").resolve()
    )


def test_discovers_agents() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assert len(ws.agents) >= 1

    names = [a.name for a in ws.agents]
    assert "assessor" in names


def test_agent_fields_populated() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assessor = next(a for a in ws.agents if a.name == "assessor")

    assert isinstance(assessor, Agent)
    assert "SDLC" in assessor.body
    assert (
        assessor.path
        == (WORKSPACE_ROOT / ".github" / "agents" / "assessor.agent.md").resolve()
    )


def test_empty_workspace(tmp_path: Path) -> None:
    ws = load_workspace(tmp_path)
    assert ws.skills == []
    assert ws.agents == []


def test_workspace_missing_skill_md(tmp_path: Path) -> None:
    """A skill directory without SKILL.md should be silently skipped."""
    skill_dir = tmp_path / ".agents" / "skills" / "broken"
    skill_dir.mkdir(parents=True)
    (skill_dir / "README.md").write_text("not a skill")

    ws = load_workspace(tmp_path)
    assert ws.skills == []
