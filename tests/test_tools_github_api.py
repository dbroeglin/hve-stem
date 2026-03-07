"""Tests for stem.tools.github_api — GitHub API tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest


def _make_invocation(owner: str = "octo", repo: str = "hello") -> dict[str, object]:
    return {"arguments": {"owner": owner, "repo": repo}}


def _parse_result(raw: dict[str, object]) -> dict[str, object]:
    """Extract the inner dict from the SDK wrapper."""
    return json.loads(str(raw["textResultForLlm"]))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_copilot_settings_success() -> None:
    from stem.tools.github_api import get_copilot_settings

    fake = {"seat_management_setting": "assign_all"}
    with patch("stem.tools.github_api.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_copilot_settings.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "copilot_settings"
    assert result["data"] == fake


@pytest.mark.asyncio
async def test_get_copilot_settings_error() -> None:
    from stem.tools.github_api import get_copilot_settings

    with patch(
        "stem.tools.github_api.get_json",
        new_callable=AsyncMock,
        side_effect=Exception("403 Forbidden"),
    ):
        raw = await get_copilot_settings.handler(_make_invocation())
    result = _parse_result(raw)
    assert "error" in result


@pytest.mark.asyncio
async def test_get_copilot_usage() -> None:
    from stem.tools.github_api import get_copilot_usage

    fake = {"total_active_users": 42}
    with patch("stem.tools.github_api.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_copilot_usage.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "copilot_usage"


@pytest.mark.asyncio
async def test_get_branch_protection() -> None:
    from stem.tools.github_api import get_branch_protection

    repo_data: dict[str, object] = {"default_branch": "main"}
    protection_data: dict[str, object] = {"required_pull_request_reviews": {"required_approving_review_count": 1}}

    call_count = 0

    async def _mock_get_json(url: str, **kwargs: object) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return repo_data
        return protection_data

    with patch("stem.tools.github_api.get_json", side_effect=_mock_get_json):
        raw = await get_branch_protection.handler(_make_invocation())

    result = _parse_result(raw)
    assert result["metric"] == "branch_protection"
    assert result["default_branch"] == "main"
    assert result["data"] == protection_data
