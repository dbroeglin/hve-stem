"""Stem CLI — the primary interface for HVE Stem."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from stem.commands import assess, init, mcp, serve
from stem.workspace import Workspace, load_workspace

console = Console()

app = typer.Typer(
    name="stem",
    help="Control plane for agentic software development.",
    no_args_is_help=True,
)

# Module-level workspace populated by the app callback before any command runs.
_workspace: Workspace | None = None

# Commands that do not require a pre-existing workspace.
_SKIP_WORKSPACE_COMMANDS = {"init"}


def get_workspace() -> Workspace:
    """Return the current workspace. Must be called after CLI initialisation."""
    if _workspace is None:
        msg = "Workspace not initialised — this is a bug."
        raise RuntimeError(msg)
    return _workspace


def _version_callback(value: bool) -> None:  # noqa: FBT001
    if value:
        from stem import __version__

        console.print(f"stem {__version__}")
        raise typer.Exit()


def _running_command() -> str | None:
    """Return the subcommand name from sys.argv, or None."""
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            return arg
    return None


@app.callback()
def main(
    workdir: Optional[Path] = typer.Option(  # noqa: UP007, UP045
        None,
        "--workdir",
        "-w",
        help="Root of the workspace to scan for skills and agents.",
        envvar="STEM_WORKDIR",
    ),
    version: bool = typer.Option(  # noqa: FBT001
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Control plane for agentic software development."""
    global _workspace  # noqa: PLW0603
    cmd = _running_command()
    if cmd in _SKIP_WORKSPACE_COMMANDS:
        return
    resolved = (workdir or Path.cwd()).resolve()
    _workspace = load_workspace(resolved)


app.command()(init.init)
app.command()(assess.assess)
app.command()(serve.serve)
app.command()(mcp.mcp)
