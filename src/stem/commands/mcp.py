"""stem mcp — start an MCP server for coding agent integration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from mcp.server.fastmcp import FastMCP
from rich.console import Console

from stem.session import load_agent_message, run_agent
from stem.workspace import load_workspace

_mcp = FastMCP(
    "stem",
    instructions=(
        "You have access to Stem — the HVE control plane for agentic"
        " software development."
        " Use the `assess_repo` tool to evaluate a GitHub repository's SDLC maturity."
    ),
)


@_mcp.tool()
async def assess_repo(
    repo: str,
    model: str = "claude-sonnet-4.6",
    timeout: float = 300.0,
) -> str:
    """Assess a GitHub repository against the desired SDLC blueprint.

    Args:
        repo: GitHub repository to assess in ``owner/repo`` format.
        model: Copilot model to use for the assessment.
        timeout: Maximum seconds to wait for the assessment to complete.

    Returns:
        A Markdown-formatted SDLC assessment report.
    """
    from stem.cli import get_workspace

    ws = get_workspace()
    system_message = load_agent_message(ws.root, "assessor")
    _console = Console(stderr=True)
    return await run_agent(
        prompt=(
            f"Assess the GitHub repository **{repo}**. "
            "Use the available Microsoft Docs, WorkIQ and GitHub "
            "tools to inspect the repo contents, workflows, "
            "configuration files, and community health files. "
            "Then produce the full SDLC assessment report."
        ),
        system_message=system_message,
        model=model,
        timeout=timeout,
        ws=ws,
        output=_console,
    )


def mcp(
    workdir: Annotated[
        Optional[Path],  # noqa: UP007, UP045
        typer.Option(
            "--workdir",
            "-w",
            help="Root of the Stem instance repository.",
            envvar="STEM_WORKDIR",
        ),
    ] = None,
) -> None:
    """Start an MCP server so Stem can be driven from coding agents."""
    from stem.cli import set_workspace

    resolved = (workdir or Path.cwd()).resolve()
    set_workspace(load_workspace(resolved))
    _mcp.run()
