"""Stem CLI — the primary interface for HVE Stem."""

import typer
from rich.console import Console

from stem.commands import assess, init, mcp, serve

console = Console()

app = typer.Typer(
    name="stem",
    help="Control plane for agentic software development.",
    no_args_is_help=True,
)

app.command()(init.init)
app.command()(assess.assess)
app.command()(serve.serve)
app.command()(mcp.mcp)
