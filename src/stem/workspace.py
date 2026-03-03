"""Discover skills, agents, and other metadata from a workspace directory."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
class Workspace:
    """Aggregated view of all discoverable artefacts in a workspace."""

    root: Path
    skills: list[Skill] = field(default_factory=list)
    agents: list[Agent] = field(default_factory=list)


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

    Expected layout::

        <root>/
          .agents/skills/<skill-name>/SKILL.md
          .github/agents/<agent-name>.agent.md
    """
    root = root.resolve()

    # --- skills ---
    skills: list[Skill] = []
    skills_dir = root / ".agents" / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir():
                skill = _parse_skill(child)
                if skill is not None:
                    skills.append(skill)

    # --- agents ---
    agents: list[Agent] = []
    agents_dir = root / ".github" / "agents"
    if agents_dir.is_dir():
        for child in sorted(agents_dir.iterdir()):
            if child.suffix == ".md" and child.stem.endswith(".agent"):
                agent = _parse_agent(child)
                if agent is not None:
                    agents.append(agent)

    return Workspace(root=root, skills=skills, agents=agents)
