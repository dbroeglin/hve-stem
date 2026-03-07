"""Tests for stem mcp — MCP server registration and assess_repo tool."""

import asyncio
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from stem.commands.mcp import _mcp, assess_repo
from stem.workspace import Workspace


# -- FastMCP server introspection ------------------------------------------


def test_mcp_server_name() -> None:
    assert _mcp.name == "stem"


def test_mcp_server_instructions_mention_assess_repo() -> None:
    assert _mcp.instructions is not None
    assert "assess_repo" in _mcp.instructions


def test_mcp_server_has_assess_repo_tool() -> None:
    assert "assess_repo" in _mcp._tool_manager._tools


def test_assess_repo_tool_schema() -> None:
    tools = asyncio.run(_mcp.list_tools())
    tool = next(t for t in tools if t.name == "assess_repo")
    assert "repo" in tool.inputSchema["required"]
    assert "model" in tool.inputSchema["properties"]
    assert "timeout" in tool.inputSchema["properties"]


def test_assess_repo_default_timeout_is_600_seconds() -> None:
    signature = inspect.signature(assess_repo)
    assert signature.parameters["timeout"].default == 600.0


# -- assess_repo tool behaviour -------------------------------------------


def test_assess_repo_missing_workspace() -> None:
    """assess_repo raises RuntimeError when workspace is not initialised."""
    with patch(
        "stem.cli.get_workspace",
        side_effect=RuntimeError("Workspace not initialised — this is a bug."),
    ):
        with pytest.raises(RuntimeError, match="Workspace not initialised"):
            asyncio.run(assess_repo(repo="owner/repo"))


def test_assess_repo_missing_agent_file(tmp_path: Path) -> None:
    """assess_repo raises FileNotFoundError when assessor agent is absent."""
    ws = Workspace(root=tmp_path)
    with (
        patch("stem.cli.get_workspace", return_value=ws),
        patch(
            "stem.commands.mcp.run_assessment",
            new_callable=AsyncMock,
            side_effect=FileNotFoundError("Agent file not found"),
        ),
    ):
        with pytest.raises(FileNotFoundError, match="Agent file not found"):
            asyncio.run(assess_repo(repo="owner/repo"))


def test_assess_repo_success(tmp_path: Path) -> None:
    """assess_repo returns the Markdown report produced by run_assessment."""
    ws = Workspace(root=tmp_path)
    expected_report = "# Assessment Report\n\nAll checks passed."

    with (
        patch("stem.cli.get_workspace", return_value=ws),
        patch(
            "stem.commands.mcp.run_assessment",
            new_callable=AsyncMock,
            return_value=expected_report,
        ),
    ):
        result = asyncio.run(assess_repo(repo="acme/my-service"))

    assert result == expected_report


def test_assess_repo_passes_model_and_timeout(tmp_path: Path) -> None:
    """assess_repo forwards model and timeout to run_assessment."""
    ws = Workspace(root=tmp_path)
    mock_run = AsyncMock(return_value="report")

    with (
        patch("stem.cli.get_workspace", return_value=ws),
        patch("stem.commands.mcp.run_assessment", mock_run),
    ):
        asyncio.run(assess_repo(repo="org/repo", model="gpt-4o", timeout=60.0))

    call_kwargs = mock_run.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["timeout"] == 60.0
    assert call_kwargs["repo"] == "org/repo"


# -- mcp command --workdir wiring ------------------------------------------


def test_mcp_command_accepts_workdir_option() -> None:
    """The mcp CLI command should show --workdir in its help text."""
    import re

    from typer.testing import CliRunner

    from stem.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    # Strip ANSI escape codes — Rich emits them even inside CliRunner.
    plain = re.sub(r"\x1b\[[0-9;]*m", "", result.output)
    assert "--workdir" in plain


def test_mcp_command_sets_workspace_from_workdir(tmp_path: Path) -> None:
    """mcp --workdir should initialise the workspace from the given path."""
    from unittest.mock import MagicMock

    import stem.cli as cli_module

    with patch.object(_mcp, "run", new_callable=MagicMock):
        from stem.commands.mcp import mcp as mcp_cmd

        mcp_cmd(workdir=tmp_path)

    ws = cli_module.get_workspace()
    assert ws.root == tmp_path.resolve()
