"""stem assess — evaluate repos against desired SDLC blueprints."""

import asyncio
from typing import Annotated, Any

import typer
from copilot import CopilotClient, MCPServerConfig, PermissionHandler
from copilot.generated.session_events import SessionEvent, SessionEventType
from copilot.types import SystemMessageReplaceConfig
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from stem.workspace import Workspace

console = Console()

# Maps built-in tool names to (color, icon) for display.
_TOOL_STYLE: dict[str, tuple[str, str]] = {
    "bash": ("yellow", "$"),
    "shell": ("yellow", "$"),
    "view": ("blue", "📄"),
    "read_file": ("blue", "📄"),
    "read": ("blue", "📄"),
    "glob": ("blue", "🔍"),
    "ls": ("blue", "📂"),
    "report_intent": ("dim", "📋"),
    "write_file": ("green", "✏️"),
    "edit_file": ("green", "✏️"),
}


def _tool_detail(tool_name: str, mcp_server: str | None, args: Any) -> str:
    """Return a Rich-markup detail string extracted from tool arguments."""
    if not isinstance(args, dict):
        return ""

    name = tool_name.lower()
    server = (mcp_server or "").lower()

    # bash / shell — show the command, truncated
    cmd: str = args.get("command") or args.get("cmd") or ""
    if cmd and (name in ("bash", "shell") or "command" in args):
        cmd = cmd.strip().replace("\n", "; ")
        truncated = cmd[:100] + ("…" if len(cmd) > 100 else "")
        return f"[yellow]$ {truncated}[/yellow]"

    # file viewing / reading — show the path
    if name in ("view", "read_file", "read", "ls", "glob"):
        path: str = (
            args.get("path") or args.get("file_path") or args.get("pattern") or ""
        )
        if path:
            return f"[blue]{path}[/blue]"

    # GitHub MCP tools — show owner/repo/path or search query
    if server == "github" or "github" in name:
        owner: str = args.get("owner", "")
        repo: str = args.get("repo", "")
        path_gh: str = args.get("path", "")
        query: str = args.get("query") or args.get("q") or ""
        issue_num = (
            args.get("issue_number")
            or args.get("number")
            or args.get("pull_request_number")
        )

        if query:
            q = str(query)
            truncated_q = q[:70] + ("…" if len(q) > 70 else "")
            return f"[dim]search:[/dim] [italic]{truncated_q}[/italic]"

        if owner and repo:
            ref = f"[bold]{owner}/{repo}[/bold]"
            if path_gh:
                ref += f"[dim]/{path_gh.lstrip('/')}[/dim]"
            if issue_num:
                ref += f"[dim] #{issue_num}[/dim]"
            return ref

    # generic fallback: first string-valued key worth showing
    for key in ("path", "file", "url", "name", "query", "ref"):
        val = args.get(key)
        if val and isinstance(val, str):
            return f"[dim]{val[:70] + ('…' if len(val) > 70 else '')}[/dim]"

    return ""


def _format_tool_line(event: SessionEvent) -> str:
    """Build a Rich-markup string for a TOOL_EXECUTION_START event."""
    data = event.data
    tool_name: str = data.tool_name or "unknown"
    mcp_server: str | None = data.mcp_server_name
    mcp_tool: str | None = data.mcp_tool_name

    # Display name: prefer MCP server + tool breakdown
    if mcp_server and mcp_tool:
        display = (
            f"[bold magenta]{mcp_server}[/bold magenta]"
            f"[dim]/[/dim]"
            f"[cyan]{mcp_tool}[/cyan]"
        )
    elif mcp_server:
        display = (
            f"[bold magenta]{mcp_server}[/bold magenta]"
            f"[dim]/[/dim]"
            f"[cyan]{tool_name}[/cyan]"
        )
    else:
        color, _icon = _TOOL_STYLE.get(tool_name.lower(), ("cyan", "⚙"))
        display = f"[bold {color}]{tool_name}[/bold {color}]"

    detail = _tool_detail(mcp_tool or tool_name, mcp_server, data.arguments)

    line = f"  [dim]⚙ [/dim] {display}"
    if detail:
        line += f"  [dim]›[/dim]  {detail}"
    return line


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
        stem_dir = str(ws.root / "stem")
        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": PermissionHandler.approve_all,
                "mcp_servers": MCP_SERVERS,
                "system_message": SystemMessageReplaceConfig(
                    mode="replace", content=SYSTEM_MESSAGE
                ),
                "working_directory": stem_dir,
                "skill_directories": [stem_dir + "/skills"],
            }
        )

        def _on_event(event: SessionEvent) -> None:
            if event.type == SessionEventType.ASSISTANT_REASONING:
                text = (event.data.content or "").strip()
                if text:
                    _console.print(f"  [dim italic]💭 {text}[/dim italic]")
            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                _console.print(_format_tool_line(event))

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
