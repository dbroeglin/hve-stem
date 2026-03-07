"""Tests for stem session — MCP configuration and agent message loading."""

import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from stem.engine import save_report
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


# ---------------------------------------------------------------------------
# save_report
# ---------------------------------------------------------------------------


def test_save_report_creates_file(tmp_path: Path) -> None:
    """Report is written to reports/<owner>/<repo>/<date>.md."""
    fake_date = datetime.date(2026, 2, 27)
    with patch("stem.engine.datetime") as mock_dt:
        mock_dt.date.today.return_value = fake_date

        path = save_report(tmp_path, "my-org/my-repo", "# Report")

    assert path == tmp_path / "reports" / "my-org" / "my-repo" / "2026-02-27.md"
    assert path.read_text(encoding="utf-8") == "# Report"


def test_save_report_creates_directories(tmp_path: Path) -> None:
    """Intermediate directories are created automatically."""
    fake_date = datetime.date(2026, 3, 7)
    with patch("stem.engine.datetime") as mock_dt:
        mock_dt.date.today.return_value = fake_date

        path = save_report(tmp_path, "acme/widgets", "content")

    assert path.parent.is_dir()
    assert path.name == "2026-03-07.md"


def test_save_report_overwrites_existing(tmp_path: Path) -> None:
    """Running an assessment twice on the same day overwrites the report."""
    fake_date = datetime.date(2026, 2, 27)
    with patch("stem.engine.datetime") as mock_dt:
        mock_dt.date.today.return_value = fake_date

        save_report(tmp_path, "org/repo", "old content")
        path = save_report(tmp_path, "org/repo", "new content")

    assert path.read_text(encoding="utf-8") == "new content"
