"""Smoke tests for the stem CLI."""

from typer.testing import CliRunner

from stem.cli import app

runner = CliRunner()


def test_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Control plane for agentic software development" in result.output


def test_init_command_exists() -> None:
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "bootstrap" in result.output.lower() or "instance" in result.output.lower()


def test_assess_command_exists() -> None:
    result = runner.invoke(app, ["assess", "--help"])
    assert result.exit_code == 0
    assert "owner/repo" in result.output.lower() or "REPO" in result.output


def test_serve_command_exists() -> None:
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0


def test_mcp_command_exists() -> None:
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "MCP" in result.output or "mcp" in result.output.lower()
