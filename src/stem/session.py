"""Reusable Copilot SDK session management."""

import json
from collections.abc import Callable
from pathlib import Path

from copilot import CopilotClient, MCPServerConfig, Tool
from copilot.generated.session_events import SessionEvent, SessionEventType
from copilot.types import (
    PermissionRequest,
    PermissionRequestResult,
    SystemMessageReplaceConfig,
)

from stem.workspace import Workspace


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


PermissionHandler = Callable[
    [PermissionRequest, dict[str, str]], PermissionRequestResult
]


async def run_agent(
    *,
    prompt: str,
    system_message: str,
    model: str,
    timeout: float,
    ws: Workspace,
    on_permission_request: PermissionHandler,
    on_event: Callable[..., None] | None = None,
    tools: list[Tool] | None = None,
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
        on_permission_request: Permission callback passed to the Copilot
            session.  The caller decides the approval policy.
        on_event: Optional callback receiving structured ``AssessEvent`` objects
            for each progress event (tool calls, reasoning).
        tools: Optional list of custom tool functions (from ``@define_tool``)
            to register on the Copilot session.

    Returns:
        The model's response text.
    """
    from stem.engine import AssessEvent

    _emit = on_event or (lambda _e: None)

    client = CopilotClient()
    await client.start()

    try:
        stem_dir = str(ws.root / "stem")
        mcp_servers = load_mcp_servers(ws.root)

        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": on_permission_request,
                "mcp_servers": mcp_servers,
                "tools": tools or [],
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
                    _emit(AssessEvent(type="reasoning", message=text))
            elif event.type == SessionEventType.TOOL_EXECUTION_START:
                data = event.data
                tool_name = data.tool_name or "unknown"
                mcp_server = data.mcp_server_name
                mcp_tool = data.mcp_tool_name
                display = (
                    f"{mcp_server}/{mcp_tool}" if mcp_server and mcp_tool else tool_name
                )
                args = data.arguments or {}
                detail = ""
                if isinstance(args, dict):
                    cmd = args.get("command") or args.get("cmd") or ""
                    if cmd:
                        detail = str(cmd).strip().replace("\n", "; ")[:120]
                    else:
                        for key in ("owner", "path", "query", "url", "name", "repo"):
                            val = args.get(key)
                            if val and isinstance(val, str):
                                detail = val[:80]
                                break
                _emit(AssessEvent(type="tool", tool=display, detail=detail))

        session.on(_on_event)

        response = await session.send_and_wait({"prompt": prompt}, timeout=timeout)

        if response and response.data:
            return str(response.data.content)
        return "No response received."
    finally:
        await client.stop()
