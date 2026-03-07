"""Shared assessment engine.

The single implementation that both CLI and web UI call.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from stem.session import load_agent_message, run_agent
from stem.workspace import Workspace

# ---------------------------------------------------------------------------
# Event types emitted during an assessment
# ---------------------------------------------------------------------------

EventType = Literal["status", "reasoning", "tool", "permission", "error"]


@dataclass
class AssessEvent:
    """A progress event emitted during an assessment run."""

    type: EventType
    message: str = ""
    tool: str = ""
    detail: str = ""
    kind: str = ""


EventCallback = Callable[[AssessEvent], None]

ASSESS_PROMPT_TEMPLATE = (
    "Assess the GitHub repository **{repo}**. "
    "Use the available Microsoft Docs, WorkIQ and GitHub "
    "tools to inspect the repo contents, workflows, "
    "configuration files, and community health files. "
    "Then produce the full SDLC assessment report."
)


async def run_assessment(
    *,
    repo: str,
    ws: Workspace,
    model: str = "claude-sonnet-4.6",
    timeout: float = 300.0,
    on_event: EventCallback | None = None,
) -> str:
    """Run a full SDLC assessment and return the report markdown.

    Args:
        repo: GitHub repository in ``owner/repo`` format.
        ws: Loaded workspace with MCP config and agent definitions.
        model: Copilot model identifier.
        timeout: Seconds to wait for completion.
        on_event: Optional callback invoked for every progress event.

    Returns:
        The assessment report as Markdown text.
    """
    emit = on_event or (lambda _e: None)

    emit(AssessEvent(type="status", message=f"Starting assessment of {repo}…"))

    system_message = load_agent_message(ws.root, "assessor")
    prompt = ASSESS_PROMPT_TEMPLATE.format(repo=repo)

    report = await run_agent(
        prompt=prompt,
        system_message=system_message,
        model=model,
        timeout=timeout,
        ws=ws,
        on_event=emit,
    )

    emit(AssessEvent(type="status", message="Assessment complete."))
    return report
