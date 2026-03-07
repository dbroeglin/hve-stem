"""Direct GitHub API tools exposed to the Copilot SDK session.

These cover data that DevLake does not collect (Copilot settings, Copilot
usage statistics) and supplement the existing ``github`` MCP server.
"""

from __future__ import annotations

import os

from copilot.tools import define_tool
from pydantic import BaseModel, Field

from stem.tools._http import get_json

_GITHUB_API = "https://api.github.com"


def _gh_headers() -> dict[str, str]:
    """Build GitHub API request headers using ``GITHUB_TOKEN``."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ---------------------------------------------------------------------------
# Shared parameter model
# ---------------------------------------------------------------------------


class RepoParams(BaseModel):
    """Parameters identifying a GitHub repository."""

    owner: str = Field(description="Repository owner (user or org)")
    repo: str = Field(description="Repository name")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@define_tool(
    description=(
        "Get GitHub Copilot settings for an organization. "
        "Returns whether Copilot is enabled and the policy configuration."
    )
)
async def get_copilot_settings(params: RepoParams) -> dict:  # type: ignore[type-arg]
    """Fetch Copilot Business/Enterprise settings for the org."""
    url = f"{_GITHUB_API}/orgs/{params.owner}/copilot/billing"
    try:
        data = await get_json(url, headers=_gh_headers())
    except Exception as exc:
        return {"error": str(exc), "hint": "Requires org admin or Copilot API access"}
    return {
        "metric": "copilot_settings",
        "owner": params.owner,
        "data": data,
    }


@define_tool(
    description=(
        "Get GitHub Copilot usage metrics for an organization. "
        "Returns acceptance rate, suggestion count, and active users."
    )
)
async def get_copilot_usage(params: RepoParams) -> dict:  # type: ignore[type-arg]
    """Fetch Copilot usage summary for the org."""
    url = f"{_GITHUB_API}/orgs/{params.owner}/copilot/usage"
    try:
        data = await get_json(url, headers=_gh_headers())
    except Exception as exc:
        return {"error": str(exc), "hint": "Requires org admin or Copilot API access"}
    return {
        "metric": "copilot_usage",
        "owner": params.owner,
        "data": data,
    }


@define_tool(
    description=(
        "Get branch protection rules for the default branch of a repository. "
        "Returns required reviews, status checks, and enforcement settings."
    )
)
async def get_branch_protection(params: RepoParams) -> dict:  # type: ignore[type-arg]
    """Fetch branch protection rules for the repo's default branch."""
    # First get the default branch name
    repo_url = f"{_GITHUB_API}/repos/{params.owner}/{params.repo}"
    try:
        repo_data = await get_json(repo_url, headers=_gh_headers())
        default_branch = repo_data.get("default_branch", "main")
        protection_url = (
            f"{_GITHUB_API}/repos/{params.owner}/{params.repo}"
            f"/branches/{default_branch}/protection"
        )
        data = await get_json(protection_url, headers=_gh_headers())
    except Exception as exc:
        return {
            "error": str(exc),
            "hint": "Branch protection may not be configured or requires admin access",
        }
    return {
        "metric": "branch_protection",
        "owner": params.owner,
        "repo": params.repo,
        "default_branch": default_branch,
        "data": data,
    }
