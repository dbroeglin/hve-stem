"""Tests for stem session — MCP configuration and agent message loading."""

import json
from pathlib import Path

import pytest

from stem.session import load_agent_message, load_mcp_servers


def test_load_mcp_servers_reads_json(tmp_path: Path) -> None:
    mcp_dir = tmp_path / "stem"
    mcp_dir.mkdir()
    config = {
        "mcpServers": {
            "github": {
                "type": "http",
                "url": "https://api.githubcopilot.com/mcp/",
                "tools": ["*"],
            }
        }
    }
    (mcp_dir / "mcp.json").write_text(json.dumps(config))

    servers = load_mcp_servers(tmp_path)
    assert "github" in servers
    assert servers["github"]["type"] == "http"


def test_load_mcp_servers_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="MCP configuration file not found"):
        load_mcp_servers(tmp_path)


def test_load_mcp_servers_empty_servers(tmp_path: Path) -> None:
    mcp_dir = tmp_path / "stem"
    mcp_dir.mkdir()
    (mcp_dir / "mcp.json").write_text(json.dumps({"mcpServers": {}}))

    servers = load_mcp_servers(tmp_path)
    assert servers == {}


def test_load_agent_message_reads_file(tmp_path: Path) -> None:
    agents_dir = tmp_path / "stem" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "assessor.agent.md").write_text("You are an assessor.")

    message = load_agent_message(tmp_path, "assessor")
    assert message == "You are an assessor."


def test_load_agent_message_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Agent file not found"):
        load_agent_message(tmp_path, "assessor")
