"""Tests for the stem serve command."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from stem.cli import app
from stem.commands.serve import _build_app

runner = CliRunner()


# -- FastAPI app tests --------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """Return a test client for the serve FastAPI app."""
    return TestClient(_build_app())


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_returns_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HVE Stem" in response.text


def test_static_files_served(client: TestClient) -> None:
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "HVE Stem" in response.text


# -- CLI tests ----------------------------------------------------------------


def test_serve_help() -> None:
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "Launch the web UI" in result.output


def test_serve_starts_uvicorn() -> None:
    """Verify that `stem serve` calls uvicorn.run with the right defaults."""
    with (
        patch("stem.commands.serve.uvicorn.run") as mock_run,
        patch("stem.commands.serve._open_browser"),
    ):
        result = runner.invoke(app, ["serve", "--no-browser"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        _args, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8777


def test_serve_custom_port() -> None:
    with (
        patch("stem.commands.serve.uvicorn.run") as mock_run,
        patch("stem.commands.serve._open_browser"),
    ):
        result = runner.invoke(app, ["serve", "--port", "9000", "--no-browser"])
        assert result.exit_code == 0
        _args, kwargs = mock_run.call_args
        assert kwargs["port"] == 9000


def test_serve_opens_browser_by_default() -> None:
    with (
        patch("stem.commands.serve.uvicorn.run"),
        patch("stem.commands.serve.threading.Timer") as mock_timer,
    ):
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 0
        mock_timer.assert_called_once()


def test_serve_no_browser_flag() -> None:
    with (
        patch("stem.commands.serve.uvicorn.run"),
        patch("stem.commands.serve.threading.Timer") as mock_timer,
    ):
        result = runner.invoke(app, ["serve", "--no-browser"])
        assert result.exit_code == 0
        mock_timer.assert_not_called()
