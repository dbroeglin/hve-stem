"""stem assess — evaluate repos against desired SDLC blueprints."""

import asyncio
from typing import Annotated

import typer
from copilot import CopilotClient, MCPServerConfig, PermissionHandler
from copilot.generated.session_events import SessionEvent, SessionEventType
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from stem.workspace import Workspace

console = Console()

SYSTEM_MESSAGE = """\
You are HVE Stem — an expert SDLC assessment agent.

Given a GitHub repository, perform a thorough assessment covering:

1. **Repository Health**: README quality, license, contributing guidelines,
   issue/PR templates, branch protection, code owners.
2. **CI/CD Maturity**: Workflow coverage (build, test, lint, deploy),
   use of reusable workflows, secrets management, environment gates.
3. **Code Quality**: Linting configuration, type checking, test coverage
   tooling, dependency management (Dependabot/Renovate).
4. **Security Posture**: Dependency scanning, secret scanning, CODEOWNERS,
   signed commits, SBOM generation.
5. **Agentic Readiness**: Copilot instructions, MCP server configs,
   GitHub Actions bot integration, automated issue triage, AI-assisted
   code review setup.

For each area, assign a maturity level:
- 🔴 **Missing** — not present at all
- 🟡 **Basic** — present but minimal
- 🟢 **Mature** — well-configured and maintained

Finish with a prioritised list of **recommended next steps** the team
should take to improve their SDLC posture.

Format your entire response as Markdown.
"""

MCP_SERVERS: dict[str, MCPServerConfig] = {
    "microsoftdocs": {
        "type": "http",
        "url": "https://learn.microsoft.com/api/mcp",
        "tools": ["*"],
    },
    "workiq": {
        "type": "local",
        "command": "npx",
        "args": ["-y", "@microsoft/workiq@latest", "mcp"],
        "tools": ["*"],
    },
    "azure-mcp": {
        "type": "local",
        "command": "npx",
        "args": ["-y", "@azure/mcp@latest", "server", "start"],
        "tools": ["*"],
    },
    "github": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {"Authorization": "Bearer ${TOKEN}"},
        "tools": ["*"],
    },
}


def _build_system_message(ws: Workspace) -> str:
    """Combine the base system message with workspace-discovered context."""
    parts = [SYSTEM_MESSAGE]

    if ws.agents:
        parts.append("\n## Agent Definitions\n")
        for agent in ws.agents:
            parts.append(f"### {agent.name}\n{agent.body}\n")

    if ws.skills:
        parts.append("\n## Available Skills\n")
        for skill in ws.skills:
            header = f"### {skill.name}"
            if skill.description:
                header += f" — {skill.description}"
            parts.append(f"{header}\n{skill.body}\n")

    return "\n".join(parts)


async def _run_assessment(
    repo: str,
    model: str,
    timeout: float,
    ws: Workspace,
    output: Console | None = None,
) -> str:
    """Create a Copilot session and run the SDLC assessment.

    Args:
        repo: GitHub repository slug (owner/repo).
        model: Copilot model identifier.
        timeout: Seconds to wait for the Copilot session to respond.
        ws: Workspace containing discovered agents and skills.
        output: Console to write progress messages to. Defaults to stdout.
            Pass ``Console(stderr=True)`` when calling from an MCP tool handler
            to keep stdout free for the JSON-RPC protocol stream.
    """
    _console = output if output is not None else console
    client = CopilotClient()
    await client.start()

    try:
        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": PermissionHandler.approve_all,
                "mcp_servers": MCP_SERVERS,
                "system_message": _build_system_message(ws),
            }
        )

        def _on_event(event: SessionEvent) -> None:
            if event.type == SessionEventType.ASSISTANT_REASONING:
                _console.print(
                    f"  [dim]💭 reasoning:[/dim] [italic]{event.data.content}[/italic]"
                )
            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                _console.print(
                    f"  [dim]⚙  calling tool:[/dim] [cyan]{event.data.tool_name}[/cyan]"
                )

        session.on(_on_event)

        prompt = (
            f"Assess the GitHub repository **{repo}**. "
            "Use the available Microsoft Docs, WorkIQ and GitHub "
            "tools to inspect the repo contents, workflows, "
            "configuration files, and community health files. "
            "Then produce the full SDLC assessment report."
        )

        response = await session.send_and_wait({"prompt": prompt}, timeout=timeout)

        if response and response.data:
            return str(response.data.content)
        return "No response received."
    finally:
        await client.stop()


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
        report = asyncio.run(_run_assessment(repo, model, timeout, ws))
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    console.print()
    console.print(Markdown(report))
    console.print()
    console.print("[bold green]Assessment complete.[/bold green]")
