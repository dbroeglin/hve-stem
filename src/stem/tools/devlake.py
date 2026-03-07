"""DevLake metric tools exposed to the Copilot SDK session.

Each tool queries the Apache DevLake REST API and returns a structured
dict that the assessment agent interprets to score DORA / SDLC dimensions.
"""

from __future__ import annotations

from copilot.tools import define_tool
from pydantic import BaseModel, Field

from stem.tools._http import get_json

# Module-level DevLake API base URL, set via ``configure()``.
_api_url: str = ""


def configure(api_url: str) -> None:
    """Set the DevLake API base URL for all tools in this module."""
    global _api_url  # noqa: PLW0603
    _api_url = api_url.rstrip("/")


# ---------------------------------------------------------------------------
# Shared parameter model
# ---------------------------------------------------------------------------


class DevLakeMetricParams(BaseModel):
    """Parameters accepted by every DevLake metric tool."""

    project_name: str = Field(description="DevLake project name")
    period_days: int = Field(
        default=90, description="Lookback period in days for the metric query"
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _metric_url(path: str) -> str:
    if not _api_url:
        raise RuntimeError(
            "DevLake API URL not configured. Call devlake.configure() first."
        )
    return f"{_api_url}{path}"


# ---------------------------------------------------------------------------
# DORA metric tools
# ---------------------------------------------------------------------------


@define_tool(
    description=(
        "Get DORA deployment frequency metric from DevLake. "
        "Returns deployment count, median deployment days per week, "
        "and DORA benchmark level (Elite/High/Medium/Low)."
    )
)
async def get_deployment_frequency(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for deployment frequency."""
    url = _metric_url(
        f"/api/plugins/dora/deployment_frequency"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "deployment_frequency",
        "period_days": params.period_days,
        "data": data,
    }


@define_tool(
    description=(
        "Get DORA change lead time metric from DevLake. "
        "Returns median time from first commit to production deployment."
    )
)
async def get_change_lead_time(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for change lead time."""
    url = _metric_url(
        f"/api/plugins/dora/change_lead_time"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "change_lead_time",
        "period_days": params.period_days,
        "data": data,
    }


@define_tool(
    description=(
        "Get DORA change failure rate from DevLake. "
        "Returns ratio of failed deployments to total deployments."
    )
)
async def get_change_failure_rate(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for change failure rate."""
    url = _metric_url(
        f"/api/plugins/dora/change_failure_rate"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "change_failure_rate",
        "period_days": params.period_days,
        "data": data,
    }


@define_tool(
    description=(
        "Get DORA failed deployment recovery time from DevLake. "
        "Returns median time from failed deployment to next successful deployment."
    )
)
async def get_failed_deployment_recovery_time(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for failed deployment recovery time."""
    url = _metric_url(
        f"/api/plugins/dora/recovery_time"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "failed_deployment_recovery_time",
        "period_days": params.period_days,
        "data": data,
    }


# ---------------------------------------------------------------------------
# SDLC metric tools
# ---------------------------------------------------------------------------


@define_tool(
    description=(
        "Get PR metrics from DevLake: cycle time, pickup time, review time, "
        "review depth, merge rate, and size distribution."
    )
)
async def get_pr_metrics(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for pull-request metrics."""
    url = _metric_url(
        f"/api/plugins/dora/pr_metrics"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "pr_metrics",
        "period_days": params.period_days,
        "data": data,
    }


@define_tool(
    description=(
        "Get CI/CD build metrics from DevLake: build count, success rate, "
        "and average duration."
    )
)
async def get_build_metrics(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for CI/CD build metrics."""
    url = _metric_url(
        f"/api/plugins/dora/build_metrics"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "build_metrics",
        "period_days": params.period_days,
        "data": data,
    }


@define_tool(
    description=(
        "Get issue tracking metrics from DevLake: triage time, bug age, "
        "incident count, and resolution time."
    )
)
async def get_issue_metrics(params: DevLakeMetricParams) -> dict:  # type: ignore[type-arg]
    """Query DevLake for issue-tracking metrics."""
    url = _metric_url(
        f"/api/plugins/dora/issue_metrics"
        f"?project={params.project_name}&period_days={params.period_days}"
    )
    data = await get_json(url)
    return {
        "metric": "issue_metrics",
        "period_days": params.period_days,
        "data": data,
    }
