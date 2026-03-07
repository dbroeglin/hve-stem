"""Tests for stem.tools — build_tools() assembly logic."""

from __future__ import annotations

from pathlib import Path

from stem.tools import build_tools
from stem.workspace import DevLakeConfig, Workspace


def test_build_tools_without_devlake() -> None:
    ws = Workspace(root=Path("/tmp"))
    tools = build_tools(ws)
    names = [t.name for t in tools]
    assert "get_copilot_settings" in names
    assert "get_copilot_usage" in names
    assert "get_branch_protection" in names
    assert len(tools) == 3


def test_build_tools_with_devlake() -> None:
    cfg = DevLakeConfig(enabled=True, api_url="http://dl:8080", project_name="p")
    ws = Workspace(root=Path("/tmp"), devlake_config=cfg)
    tools = build_tools(ws)
    names = [t.name for t in tools]
    # GitHub API tools always present
    assert "get_copilot_settings" in names
    # DevLake tools present
    assert "get_deployment_frequency" in names
    assert "get_change_lead_time" in names
    assert "get_change_failure_rate" in names
    assert "get_failed_deployment_recovery_time" in names
    assert "get_pr_metrics" in names
    assert "get_build_metrics" in names
    assert "get_issue_metrics" in names
    assert len(tools) == 10


def test_build_tools_devlake_disabled() -> None:
    """DevLakeConfig with enabled=False should not add DevLake tools."""
    cfg = DevLakeConfig(enabled=False, api_url="http://dl:8080", project_name="p")
    ws = Workspace(root=Path("/tmp"), devlake_config=cfg)
    tools = build_tools(ws)
    # Note: _load_devlake_config returns None for enabled=False,
    # but build_tools checks the config directly.
    assert len(tools) == 3
