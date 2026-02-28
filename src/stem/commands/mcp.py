"""stem mcp — start an MCP server for coding agent integration."""

import typer
from rich.console import Console

console = Console()


def mcp() -> None:
    """Start an MCP server so Stem can be driven from coding agents."""
    console.print("[bold green]stem mcp[/] — not yet implemented")
    raise typer.Exit()
