"""Build the custom tool list for a Copilot SDK session.

``build_tools(ws)`` inspects the workspace configuration and returns the
list of tool functions to pass as ``tools=`` to ``create_session()``.
DevLake tools are included only when a DevLake instance is configured.
"""

from __future__ import annotations

from copilot import Tool

from stem.workspace import Workspace


def build_tools(ws: Workspace) -> list[Tool]:
    """Assemble the tool list based on workspace configuration.

    Always includes the direct GitHub API tools.  DevLake metric tools
    are added only when ``ws.devlake_config`` is present and enabled.
    """
    from stem.tools.github_api import (
        get_branch_protection,
        get_copilot_settings,
        get_copilot_usage,
    )

    tools: list[Tool] = [
        get_copilot_settings,
        get_copilot_usage,
        get_branch_protection,
    ]

    if ws.devlake_config and ws.devlake_config.enabled:
        from stem.tools import devlake
        from stem.tools.devlake import (
            get_build_metrics,
            get_change_failure_rate,
            get_change_lead_time,
            get_deployment_frequency,
            get_failed_deployment_recovery_time,
            get_issue_metrics,
            get_pr_metrics,
        )

        devlake.configure(ws.devlake_config.api_url)
        tools.extend(
            [
                get_deployment_frequency,
                get_change_lead_time,
                get_change_failure_rate,
                get_failed_deployment_recovery_time,
                get_pr_metrics,
                get_build_metrics,
                get_issue_metrics,
            ]
        )

    return tools
