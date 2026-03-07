"""Tests for stem.tools.devlake — DevLake metric tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from stem.tools.devlake import (
    DevLakeMetricParams,
    configure,
    get_build_metrics,
    get_change_failure_rate,
    get_change_lead_time,
    get_deployment_frequency,
    get_failed_deployment_recovery_time,
    get_issue_metrics,
    get_pr_metrics,
)


@pytest.fixture(autouse=True)
def _configure_devlake() -> None:
    """Ensure the DevLake API URL is set for every test."""
    configure("http://devlake.test:8080")


def _make_invocation(project: str = "proj", days: int = 90) -> dict[str, object]:
    """Build a tool invocation dict matching the SDK calling convention."""
    return {"arguments": {"project_name": project, "period_days": days}}


def _parse_result(raw: dict[str, object]) -> dict[str, object]:
    """Extract the inner dict from the SDK wrapper."""
    return json.loads(str(raw["textResultForLlm"]))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_deployment_frequency() -> None:
    fake = {"deployment_count": 10}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_deployment_frequency.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "deployment_frequency"
    assert result["data"] == fake
    assert result["period_days"] == 90


@pytest.mark.asyncio
async def test_get_change_lead_time() -> None:
    fake = {"median_hours": 24}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_change_lead_time.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "change_lead_time"
    assert result["data"] == fake


@pytest.mark.asyncio
async def test_get_change_failure_rate() -> None:
    fake = {"rate": 0.05}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_change_failure_rate.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "change_failure_rate"


@pytest.mark.asyncio
async def test_get_failed_deployment_recovery_time() -> None:
    fake = {"median_hours": 2}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_failed_deployment_recovery_time.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "failed_deployment_recovery_time"


@pytest.mark.asyncio
async def test_get_pr_metrics() -> None:
    fake = {"cycle_time_hours": 12}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_pr_metrics.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "pr_metrics"


@pytest.mark.asyncio
async def test_get_build_metrics() -> None:
    fake = {"success_rate": 0.95}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_build_metrics.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "build_metrics"


@pytest.mark.asyncio
async def test_get_issue_metrics() -> None:
    fake = {"triage_hours": 4}
    with patch("stem.tools.devlake.get_json", new_callable=AsyncMock, return_value=fake):
        raw = await get_issue_metrics.handler(_make_invocation())
    result = _parse_result(raw)
    assert result["metric"] == "issue_metrics"


def test_params_model_defaults() -> None:
    p = DevLakeMetricParams(project_name="x")
    assert p.period_days == 90


def test_configure_strips_trailing_slash() -> None:
    import stem.tools.devlake as mod

    configure("http://example.com/api/")
    assert mod._api_url == "http://example.com/api"
