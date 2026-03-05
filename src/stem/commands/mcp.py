"""stem mcp — start an MCP server for coding agent integration."""

from mcp.server.fastmcp import FastMCP
from rich.console import Console

from stem.commands.assess import _run_assessment

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
    _console = Console(stderr=True)
    return await _run_assessment(repo, model, timeout, ws, _console)


def mcp() -> None:
    """Start an MCP server so Stem can be driven from coding agents."""
    _mcp.run()
