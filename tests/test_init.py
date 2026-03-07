"""Tests for stem init — instance repository scaffolding."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
import yaml

from stem.commands.init import _scaffold


def test_scaffold_creates_directory_structure(tmp_path: Path) -> None:
    dest = tmp_path / "my-instance"
    dest.mkdir()
    _scaffold(dest, targets=[], name="my-instance")

    assert (dest / "stem.yaml").is_file()
    assert (dest / "README.md").is_file()
    assert (dest / ".gitignore").is_file()
    assert (dest / "blueprints").is_dir()
    assert (dest / "reports").is_dir()
    assert (dest / "remediation").is_dir()
    assert (dest / "stem" / "agents").is_dir()
    assert (dest / "stem" / "skills").is_dir()
    assert (dest / ".github" / "agents").is_dir()
    assert (dest / ".github" / "skills").is_dir()
    assert (dest / ".github" / "prompts").is_dir()
    assert (dest / ".github" / "workflows").is_dir()
    assert (dest / ".github" / "copilot-instructions.md").is_file()


def test_scaffold_copies_default_blueprint(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="inst")

    default_bp = dest / "blueprints" / "default.md"
    assert default_bp.is_file()
    assert "blueprint" in default_bp.read_text().lower()


def test_scaffold_copies_assessor_agent(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="inst")

    agent = dest / "stem" / "agents" / "assessor.agent.md"
    assert agent.is_file()
    assert "assessment" in agent.read_text().lower()


def test_scaffold_renders_stem_yaml_no_targets(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="my-team")

    data = yaml.safe_load((dest / "stem.yaml").read_text())
    assert data["name"] == "my-team"
    assert data["targets"] == []
    assert data["blueprint"] == "default.md"
    assert "stem_version" in data
    assert data["scoring"] == {"green": 80, "amber": 50}


def test_scaffold_seeds_target(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=["my-org/api-service"], name="inst")

    data = yaml.safe_load((dest / "stem.yaml").read_text())
    assert len(data["targets"]) == 1
    assert data["targets"][0]["repo"] == "my-org/api-service"


def test_scaffold_seeds_multiple_targets(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(
        dest,
        targets=["my-org/api-service", "my-org/web-app", "my-org/infra"],
        name="inst",
    )

    data = yaml.safe_load((dest / "stem.yaml").read_text())
    assert len(data["targets"]) == 3
    assert data["targets"][0]["repo"] == "my-org/api-service"
    assert data["targets"][1]["repo"] == "my-org/web-app"
    assert data["targets"][2]["repo"] == "my-org/infra"


def test_scaffold_records_blueprint_source(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(
        dest,
        targets=[],
        name="inst",
        blueprint_source={"repo": "acme/blueprints", "ref": "v2.0"},
    )

    data = yaml.safe_load((dest / "stem.yaml").read_text())
    assert data["blueprint_source"]["repo"] == "acme/blueprints"
    assert data["blueprint_source"]["ref"] == "v2.0"
    # No bundled blueprints when remote source is specified
    assert not (dest / "blueprints" / "default.md").exists()


def test_scaffold_creates_git_repo(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="inst")

    assert (dest / ".git").is_dir()


def test_scaffold_copies_workflow(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="inst")

    wf = dest / ".github" / "workflows" / "stem-assess.yml"
    assert wf.is_file()
    assert "assess" in wf.read_text().lower()


def test_scaffold_readme_contains_name(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="cool-team")

    readme = (dest / "README.md").read_text()
    assert "cool-team" in readme


def test_scaffold_creates_mcp_json(tmp_path: Path) -> None:
    dest = tmp_path / "inst"
    dest.mkdir()
    _scaffold(dest, targets=[], name="inst")

    mcp_json = dest / "stem" / "mcp.json"
    assert mcp_json.is_file()

    data = json.loads(mcp_json.read_text())
    assert "mcpServers" in data
    assert "github" in data["mcpServers"]


def test_scaffold_fails_when_git_user_not_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_scaffold raises typer.Exit when git user.name/user.email are unset."""
    dest = tmp_path / "inst"
    dest.mkdir()

    # Clear env-var fallbacks so only git-config is consulted.
    for var in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.delenv(var, raising=False)

    original_run = subprocess.run

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if cmd[:2] == ["git", "config"] and cmd[2] in ("user.name", "user.email"):
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")
        return original_run(cmd, **kwargs)

    with patch("stem.commands.init.subprocess.run", side_effect=fake_run):
        with pytest.raises(typer.Exit) as exc_info:
            _scaffold(dest, targets=[], name="inst")
        assert exc_info.value.exit_code == 1
