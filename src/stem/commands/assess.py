"""stem assess — evaluate repos against desired SDLC blueprints."""

import typer
from rich.console import Console

console = Console()


def assess() -> None:
    """Evaluate one or more repos against the desired SDLC blueprint."""
    console.print("[bold green]stem assess[/] — not yet implemented")
    raise typer.Exit()
