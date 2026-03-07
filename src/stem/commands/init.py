"""stem init — bootstrap a Stem instance repository."""

from __future__ import annotations

import importlib.resources
import shutil
import subprocess
from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml
from rich.console import Console

from stem import __version__

console = Console()

DATA_ROOT = importlib.resources.files("stem") / "data"


def _data_path(relative: str) -> Path:
    """Resolve a path inside the bundled ``stem/data`` directory."""
    traversable = DATA_ROOT / relative
    # importlib.resources may return a Traversable; coerce to Path.
    return Path(str(traversable))


def _copy_tree(src: Path, dst: Path) -> None:
    """Recursively copy *src* into *dst*, creating parents as needed."""
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            shutil.copy2(item, target)


def _render_stem_yaml(
    dest: Path,
    *,
    name: str,
    targets: list[str],
    blueprint_source: dict[str, str] | None = None,
) -> None:
    """Write ``stem.yaml`` to *dest*."""
    data: dict[str, object] = {
        "stem_version": __version__,
        "name": name,
        "description": f"SDLC control plane — {name}",
    }
    if blueprint_source:
        data["blueprint_source"] = blueprint_source
    data["blueprint"] = "default.md"
    data["scoring"] = {"green": 80, "amber": 50}
    data["targets"] = [{"repo": t} for t in targets] if targets else []

    (dest / "stem.yaml").write_text(
        yaml.dump(data, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def _render_readme(dest: Path, name: str) -> None:
    """Generate a minimal README.md."""
    (dest / "README.md").write_text(
        f"# {name}\n\n"
        "Stem instance repository — control plane for agentic software development.\n\n"
        "## Getting started\n\n"
        "```bash\n"
        "pip install hve-stem\n"
        "stem assess <owner/repo>\n"
        "```\n",
        encoding="utf-8",
    )


def _scaffold(
    dest: Path,
    *,
    targets: list[str],
    name: str,
    blueprint_source: dict[str, str] | None = None,
) -> None:
    """Create the full instance repository directory structure at *dest*."""
    dest.mkdir(parents=True, exist_ok=True)

    # 1. Create empty directories
    for subdir in [
        "reports",
        "remediation",
        "stem/skills",
        ".github/agents",
        ".github/skills",
        ".github/prompts",
    ]:
        (dest / subdir).mkdir(parents=True, exist_ok=True)

    # 2. Copy or fetch blueprints
    blueprints_dst = dest / "blueprints"
    blueprints_dst.mkdir(parents=True, exist_ok=True)
    if blueprint_source is None:
        _copy_tree(_data_path("blueprints"), blueprints_dst)

    # 3. Render stem.yaml
    _render_stem_yaml(
        dest,
        name=name,
        targets=targets,
        blueprint_source=blueprint_source,
    )

    # 4. Copy Stem's internal config, agents, and skills (Copilot SDK workdir)
    _copy_tree(_data_path("stem"), dest / "stem")

    # 5. Copy developer-facing Copilot config into .github/
    copilot_src = _data_path("copilot")
    if copilot_src.is_dir():
        for item in sorted(copilot_src.iterdir()):
            target = dest / ".github" / item.name
            if item.is_dir():
                _copy_tree(item, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    # 6. Copy GitHub Actions workflow
    workflows_dst = dest / ".github" / "workflows"
    workflows_dst.mkdir(parents=True, exist_ok=True)
    _copy_tree(_data_path("workflows"), workflows_dst)

    # 7. Generate README.md, .gitignore
    _render_readme(dest, name)
    gitignore_src = _data_path("templates/.gitignore")
    if gitignore_src.is_file():
        shutil.copy2(gitignore_src, dest / ".gitignore")

    # 8. git init + initial commit
    #    Pre-check: git requires user.name and user.email for commits.
    missing: list[str] = []
    for key in ("user.name", "user.email"):
        result = subprocess.run(  # noqa: S603, S607
            ["git", "config", key], capture_output=True, text=True
        )
        if result.returncode != 0 or not result.stdout.strip():
            missing.append(key)
    if missing:
        console.print(
            f"[bold red]Error:[/bold red] Git is not fully configured — "
            f"{' and '.join(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} not set.\n"
            "Please configure them before running 'stem init':\n\n"
            '  git config --global user.name "Your Name"\n'
            '  git config --global user.email "you@example.com"'
        )
        raise typer.Exit(code=1)

    subprocess.run(["git", "init"], cwd=dest, check=True, capture_output=True)  # noqa: S603, S607
    subprocess.run(["git", "add", "."], cwd=dest, check=True, capture_output=True)  # noqa: S603, S607
    subprocess.run(  # noqa: S603, S607
        ["git", "commit", "-m", "chore: initialise Stem instance repository"],
        cwd=dest,
        check=True,
        capture_output=True,
    )


def init(
    repo: Annotated[
        Optional[str],  # noqa: UP007, UP045
        typer.Argument(
            help="Optional target repo to seed (owner/repo).",
        ),
    ] = None,
    blueprint: Annotated[
        Optional[str],  # noqa: UP007, UP045
        typer.Option(
            "--blueprint",
            help=(
                "Fetch blueprints from a remote GitHub repo"
                " (owner/repo) instead of the bundled default."
            ),
        ),
    ] = None,
    blueprint_ref: Annotated[
        Optional[str],  # noqa: UP007, UP045
        typer.Option(
            "--blueprint-ref",
            help="Pin the remote blueprint source to a branch, tag, or SHA.",
        ),
    ] = None,
) -> None:
    """Bootstrap a Stem instance repository in the current directory."""
    dest = Path.cwd()

    if (dest / "stem.yaml").exists():
        console.print(
            "[bold red]Error:[/bold red] stem.yaml already exists in this directory."
        )
        raise typer.Exit(code=1)

    targets: list[str] = []
    if repo:
        targets.append(repo)

    blueprint_source: dict[str, str] | None = None
    if blueprint:
        blueprint_source = {"repo": blueprint}
        if blueprint_ref:
            blueprint_source["ref"] = blueprint_ref
        console.print(
            f"[dim]Fetching blueprints from [cyan]{blueprint}[/cyan]"
            " is not yet implemented — creating structure"
            " without remote blueprints.[/dim]"
        )

    name = dest.name

    console.print(
        "[bold green]stem init[/bold green] — creating instance"
        f" repo in [cyan]{dest}[/cyan]"
    )
    _scaffold(
        dest,
        targets=targets,
        name=name,
        blueprint_source=blueprint_source,
    )
    console.print(
        "[bold green]\u2713[/bold green] Instance repository initialised and committed."
    )
