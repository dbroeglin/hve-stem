"""Reusable Copilot SDK session management."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from copilot import CopilotClient, MCPServerConfig
from copilot.generated.session_events import SessionEvent, SessionEventType
from copilot.types import (
    PermissionRequest,
    PermissionRequestResult,
    SystemMessageReplaceConfig,
)
from rich.console import Console

from stem.workspace import Workspace

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


_PERMISSION_KIND_STYLE: dict[str, str] = {
    "shell": "yellow",
    "write": "green",
    "read": "blue",
    "mcp": "magenta",
    "url": "dim",
    "custom-tool": "cyan",
}


def _format_permission_line(
    request: PermissionRequest, invocation: dict[str, str]
) -> str:
    """Build a Rich-markup string for a permission approval."""
    kind: str = request.get("kind") or "unknown"
    color = _PERMISSION_KIND_STYLE.get(kind, "cyan")
    kind_display = f"[bold {color}]{kind}[/bold {color}]"

    detail = ""
    cmd: str = invocation.get("command") or invocation.get("cmd") or ""
    path: str = invocation.get("path") or invocation.get("file") or ""
    tool_name: str = invocation.get("tool_name") or invocation.get("name") or ""

    if cmd:
        cmd = cmd.strip().replace("\n", "; ")
        truncated = cmd[:100] + ("…" if len(cmd) > 100 else "")
        detail = f"[yellow]$ {truncated}[/yellow]"
    elif path:
        detail = f"[blue]{path}[/blue]"
    elif tool_name:
        detail = f"[dim]{tool_name}[/dim]"

    line = f"  [dim]🔐 [/dim] [bold green]✓[/bold green]  {kind_display}"
    if detail:
        line += f"  [dim]›[/dim]  {detail}"
    return line


def _make_permission_handler(
    output: Console,
) -> Callable[[PermissionRequest, dict[str, str]], PermissionRequestResult]:
    """Return a permission handler that logs approvals to *output*."""

    def _handler(
        request: PermissionRequest, invocation: dict[str, str]
    ) -> PermissionRequestResult:
        # Auto-accept MCP tool calls silently — they are already displayed
        # via the TOOL_EXECUTION_START event handler.
        if request.get("kind") != "mcp":
            output.print(_format_permission_line(request, invocation))
        return PermissionRequestResult(kind="approved")

    return _handler


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


def load_mcp_servers(workspace_root: Path) -> dict[str, MCPServerConfig]:
    """Load MCP server configuration from the instance ``stem/mcp.json``."""
    mcp_json = workspace_root / "stem" / "mcp.json"
    if not mcp_json.is_file():
        msg = (
            f"MCP configuration file not found: {mcp_json}\n"
            "Run 'stem init' to create a Stem instance with the default configuration."
        )
        raise FileNotFoundError(msg)
    data = json.loads(mcp_json.read_text(encoding="utf-8"))
    servers: dict[str, MCPServerConfig] = data.get("mcpServers", {})
    return servers


def load_agent_message(workspace_root: Path, agent_name: str) -> str:
    """Load a system message from an agent file in the stem instance.

    Args:
        workspace_root: Root of the workspace containing the ``stem/`` directory.
        agent_name: Base name of the agent (e.g. ``"assessor"``).

    Returns:
        The raw text content of the agent file.
    """
    agent_file = workspace_root / "stem" / "agents" / f"{agent_name}.agent.md"
    if not agent_file.is_file():
        msg = (
            f"Agent file not found: {agent_file}\n"
            "Run 'stem init' to create a Stem instance with the default configuration."
        )
        raise FileNotFoundError(msg)
    return agent_file.read_text(encoding="utf-8")


async def run_agent(
    *,
    prompt: str,
    system_message: str,
    model: str,
    timeout: float,
    ws: Workspace,
    output: Console | None = None,
) -> str:
    """Create a Copilot session and send a prompt.

    This is the reusable core that any command can call to run an
    agent-driven interaction via the Copilot SDK.

    Args:
        prompt: The user-facing prompt to send to the model.
        system_message: The system message that defines the agent persona.
        model: Copilot model identifier.
        timeout: Seconds to wait for the session to respond.
        ws: Workspace containing discovered agents and skills.
        output: Console to write progress messages to. Defaults to stdout.
            Pass ``Console(stderr=True)`` when calling from an MCP tool handler
            to keep stdout free for the JSON-RPC protocol stream.

    Returns:
        The model's response text.
    """
    _console = output if output is not None else Console()
    client = CopilotClient()
    await client.start()

    try:
        stem_dir = str(ws.root / "stem")
        mcp_servers = load_mcp_servers(ws.root)
        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": _make_permission_handler(_console),
                "mcp_servers": mcp_servers,
                "system_message": SystemMessageReplaceConfig(
                    mode="replace", content=system_message
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

        response = await session.send_and_wait({"prompt": prompt}, timeout=timeout)

        if response and response.data:
            return str(response.data.content)
        return "No response received."
    finally:
        await client.stop()
