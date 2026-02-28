"""stem init — bootstrap a new project or onboard an existing repo."""

import typer
from rich.console import Console

console = Console()


def init() -> None:
    """Bootstrap a new project or onboard an existing repo with a Stem-managed SDLC blueprint."""
    console.print("[bold green]stem init[/] — not yet implemented")
    raise typer.Exit()
