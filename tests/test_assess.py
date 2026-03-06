"""Tests for stem assess — MCP configuration loading."""

import json
from pathlib import Path

import pytest

from stem.commands.assess import _load_mcp_servers


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

    servers = _load_mcp_servers(tmp_path)
    assert "github" in servers
    assert servers["github"]["type"] == "http"


def test_load_mcp_servers_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="MCP configuration file not found"):
        _load_mcp_servers(tmp_path)


def test_load_mcp_servers_empty_servers(tmp_path: Path) -> None:
    mcp_dir = tmp_path / "stem"
    mcp_dir.mkdir()
    (mcp_dir / "mcp.json").write_text(json.dumps({"mcpServers": {}}))

    servers = _load_mcp_servers(tmp_path)
    assert servers == {}
