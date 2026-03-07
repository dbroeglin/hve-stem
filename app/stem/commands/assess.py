"""stem assess — evaluate repos against desired SDLC blueprints."""

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from stem.session import load_agent_message, run_agent

console = Console()


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
        system_message = load_agent_message(ws.root, "assessor")

        prompt = (
            f"Assess the GitHub repository **{repo}**. "
            "Use the available Microsoft Docs, WorkIQ and GitHub "
            "tools to inspect the repo contents, workflows, "
            "configuration files, and community health files. "
            "Then produce the full SDLC assessment report."
        )

        report = asyncio.run(
            run_agent(
                prompt=prompt,
                system_message=system_message,
                model=model,
                timeout=timeout,
                ws=ws,
            )
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print()
    console.print(Markdown(report))
    console.print()
    console.print("[bold green]Assessment complete.[/bold green]")
