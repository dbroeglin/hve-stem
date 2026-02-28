"""stem serve — launch the web UI dashboard."""

import typer
from rich.console import Console

console = Console()


def serve() -> None:
    """Launch the web UI locally for a visual dashboard experience."""
    console.print("[bold green]stem serve[/] — not yet implemented")
    raise typer.Exit()
