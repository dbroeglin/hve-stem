"""stem assess — evaluate repos against desired SDLC blueprints."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from stem.engine import AssessEvent, run_assessment

console = Console()

# ---------------------------------------------------------------------------
# Rich formatting helpers for CLI display
# ---------------------------------------------------------------------------

_TOOL_STYLE: dict[str, str] = {
    "bash": "yellow",
    "shell": "yellow",
    "view": "blue",
    "read_file": "blue",
    "read": "blue",
    "glob": "blue",
    "ls": "blue",
    "report_intent": "dim",
    "write_file": "green",
    "edit_file": "green",
}


def _print_event(event: AssessEvent) -> None:
    """Render an ``AssessEvent`` to the console."""
    if event.type == "status":
        console.print(f"  [bold]{event.message}[/bold]")
    elif event.type == "reasoning":
        console.print(f"  [dim italic]💭 {event.message}[/dim italic]")
    elif event.type == "tool":
        tool = event.tool
        # Format MCP tools as server/tool with colour
        if "/" in tool:
            server, tool_name = tool.split("/", 1)
            display = (
                f"[bold magenta]{server}[/bold magenta]"
                f"[dim]/[/dim]"
                f"[cyan]{tool_name}[/cyan]"
            )
        else:
            color = _TOOL_STYLE.get(tool.lower(), "cyan")
            display = f"[bold {color}]{tool}[/bold {color}]"
        line = f"  [dim]⚙ [/dim] {display}"
        if event.detail:
            line += f"  [dim]›[/dim]  [dim]{event.detail}[/dim]"
        console.print(line)
    elif event.type == "error":
        console.print(f"  [bold red]Error:[/bold red] {event.message}")


def assess(
    repo: Annotated[
        str,
        typer.Argument(
            help="GitHub repository to assess (owner/repo).",
        ),
    ],
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Copilot model to use for the assessment.",
        ),
    ] = "claude-sonnet-4.6",
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            "-t",
            help="Seconds to wait for the assessment to complete.",
        ),
    ] = 300.0,
) -> None:
    """Evaluate a GitHub repo against the desired SDLC blueprint."""
    console.print(
        Panel(
            Text.from_markup(
                f"[bold]Assessing[/bold] [cyan]{repo}[/cyan] "
                f"with model [green]{model}[/green]"
            ),
            title="[bold green]stem assess[/bold green]",
            border_style="green",
        )
    )

    try:
        from stem.cli import get_workspace

        ws = get_workspace()

        report = asyncio.run(
            run_assessment(
                repo=repo,
                ws=ws,
                model=model,
                timeout=timeout,
                on_event=_print_event,
            )
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print()
    console.print(Markdown(report))
    console.print()
    console.print("[bold green]Assessment complete.[/bold green]")
