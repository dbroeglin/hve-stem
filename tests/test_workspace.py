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
    assert "foo" in names
    assert "summarize-repo" in names


def test_skill_fields_populated() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    foo = next(s for s in ws.skills if s.name == "foo")

    assert isinstance(foo, Skill)
    assert foo.description == "Fetch and summarise the README of a GitHub repository"
    assert "README" in foo.body
    assert (
        foo.path
        == (WORKSPACE_ROOT / ".agents" / "skills" / "foo" / "SKILL.md").resolve()
    )


def test_discovers_agents() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assert len(ws.agents) >= 1

    names = [a.name for a in ws.agents]
    assert "assessor" in names
    assert "stem-tester" in names


def test_agent_fields_populated() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    assessor = next(a for a in ws.agents if a.name == "assessor")

    assert isinstance(assessor, Agent)
    assert "SDLC" in assessor.body
    assert (
        assessor.path
        == (WORKSPACE_ROOT / ".github" / "agents" / "assessor.agent.md").resolve()
    )


def test_stem_dir_skill_fields() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    summarizer = next(s for s in ws.skills if s.name == "summarize-repo")
    assert (
        summarizer.description
        == "Produce a structured SDLC maturity summary for a GitHub repository"
    )
    assert "SDLC" in summarizer.body


def test_stem_dir_agent_fields() -> None:
    ws = load_workspace(WORKSPACE_ROOT)
    tester = next(a for a in ws.agents if a.name == "stem-tester")
    assert "namespace separation" in tester.body
    assert (
        tester.path
        == (WORKSPACE_ROOT / "stem" / "agents" / "stem-tester.agent.md").resolve()
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
