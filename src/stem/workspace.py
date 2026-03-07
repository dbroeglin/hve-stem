"""Discover skills, agents, and other metadata from a workspace directory."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Skill:
    """A skill discovered from `.agents/skills/<name>/SKILL.md`."""

    name: str
    description: str
    body: str
    path: Path


@dataclass(frozen=True)
class Agent:
    """An agent definition discovered from `.github/agents/<name>.agent.md`."""

    name: str
    body: str
    path: Path


@dataclass(frozen=True)
class DevLakeConfig:
    """Configuration for an Apache DevLake instance parsed from ``stem.yaml``."""

    enabled: bool
    api_url: str
    project_name: str


@dataclass(frozen=True)
class Workspace:
    """Aggregated view of all discoverable artefacts in a workspace."""

    root: Path
    skills: list[Skill] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    devlake_config: DevLakeConfig | None = None


def _parse_skill(skill_dir: Path) -> Skill | None:
    """Parse a single SKILL.md file and return a ``Skill``, or *None* on failure.

    Supports two front-matter styles:

    1. YAML front-matter delimited by ``---`` lines.
    2. Code-fence front-matter: `````skill`` … ``---`` … ```````.
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None

    text = skill_file.read_text(encoding="utf-8")

    name = skill_dir.name
    description = ""

    lines = text.splitlines()
    in_frontmatter = False
    frontmatter_end = 0
    fence_style = False  # True when front-matter is inside a ````skill fence

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect opening delimiter
        if not in_frontmatter and frontmatter_end == 0:
            if stripped.startswith("````skill") or stripped.startswith("```skill"):
                in_frontmatter = True
                fence_style = True
                continue
            if stripped == "---":
                in_frontmatter = True
                continue

        # Detect closing delimiter
        if in_frontmatter and stripped == "---":
            frontmatter_end = i + 1
            in_frontmatter = False
            continue

        # Parse key-value pairs inside front-matter
        if in_frontmatter:
            if stripped.startswith("name:"):
                name = stripped.removeprefix("name:").strip()
            elif stripped.startswith("description:"):
                description = stripped.removeprefix("description:").strip()

    # Body is everything after front-matter, up to an optional closing fence.
    remaining = lines[frontmatter_end:]
    body_lines: list[str] = []
    for line in remaining:
        if fence_style and line.strip() in ("````", "```"):
            break
        body_lines.append(line)
    body = "\n".join(body_lines).strip()

    return Skill(name=name, description=description, body=body, path=skill_file)


def _parse_agent(agent_file: Path) -> Agent | None:
    """Parse a ``.agent.md`` file and return an ``Agent``, or *None* on failure."""
    if not agent_file.is_file():
        return None

    text = agent_file.read_text(encoding="utf-8")

    # Derive agent name from filename: assessor.agent.md -> assessor
    stem = agent_file.stem  # "assessor.agent"
    name = stem.removesuffix(".agent") if stem.endswith(".agent") else stem

    # Strip wrapping code fence (```chatagent ... ```) if present
    lines = text.splitlines()
    body_lines: list[str] = []
    inside_fence = False
    for line in lines:
        stripped = line.strip()
        if not inside_fence and stripped.startswith("```"):
            inside_fence = True
            continue
        if inside_fence and stripped == "```":
            break
        if inside_fence:
            body_lines.append(line)
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()

    return Agent(name=name, body=body, path=agent_file)


def load_workspace(root: Path) -> Workspace:
    """Scan *root* for skills and agents and return a populated ``Workspace``.

    Searches two sets of directories:

    1. **Stem internal** (Copilot SDK workdir):
       ``<root>/stem/skills/<skill-name>/SKILL.md``
       ``<root>/stem/agents/<agent-name>.agent.md``

    2. **Legacy / developer-facing**:
       ``<root>/.agents/skills/<skill-name>/SKILL.md``
       ``<root>/.github/agents/<agent-name>.agent.md``
    """
    root = root.resolve()

    # --- skills ---
    skills: list[Skill] = []
    skill_dirs = [
        root / "stem" / "skills",
        root / ".agents" / "skills",
    ]
    for skills_dir in skill_dirs:
        if skills_dir.is_dir():
            for child in sorted(skills_dir.iterdir()):
                if child.is_dir():
                    skill = _parse_skill(child)
                    if skill is not None:
                        skills.append(skill)

    # --- agents ---
    agents: list[Agent] = []
    agent_dirs = [
        root / "stem" / "agents",
        root / ".github" / "agents",
    ]
    for agents_dir in agent_dirs:
        if agents_dir.is_dir():
            for child in sorted(agents_dir.iterdir()):
                if child.suffix == ".md" and child.stem.endswith(".agent"):
                    agent = _parse_agent(child)
                    if agent is not None:
                        agents.append(agent)

    return Workspace(
        root=root,
        skills=skills,
        agents=agents,
        targets=_load_targets(root),
        devlake_config=_load_devlake_config(root),
    )


def _load_targets(root: Path) -> list[str]:
    """Read target repos from ``stem.yaml`` in *root*."""
    stem_yaml = root / "stem.yaml"
    if not stem_yaml.is_file():
        return []
    data = yaml.safe_load(stem_yaml.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    raw_targets = data.get("targets", [])
    if not isinstance(raw_targets, list):
        return []
    repos: list[str] = []
    for entry in raw_targets:
        if isinstance(entry, dict) and isinstance(entry.get("repo"), str):
            repos.append(entry["repo"])
        elif isinstance(entry, str):
            repos.append(entry)
    return repos


def _load_devlake_config(root: Path) -> DevLakeConfig | None:
    """Read the optional ``devlake:`` section from ``stem.yaml``.

    Returns ``None`` when the section is missing or ``enabled`` is false.
    """
    stem_yaml = root / "stem.yaml"
    if not stem_yaml.is_file():
        return None
    data = yaml.safe_load(stem_yaml.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    devlake = data.get("devlake")
    if not isinstance(devlake, dict):
        return None
    enabled = bool(devlake.get("enabled", False))
    if not enabled:
        return None
    api_url = str(devlake.get("api_url", "http://localhost:8080"))
    project_name = str(devlake.get("project_name", ""))
    return DevLakeConfig(enabled=True, api_url=api_url, project_name=project_name)
