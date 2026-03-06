---
title: "ADR-0003: Stem Instance Repository Structure"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Team"
tags: ["architecture", "repository", "instance", "git"]
supersedes: ""
superseded_by: ""
---

# ADR-0003: Stem Instance Repository Structure

## Status

**Accepted**

## Context

Stem needs a Git-native, human-readable directory structure for the **instance
repository** — the control plane for a team's agentic SDLC portfolio. Every
piece of Stem state (configuration, blueprints, assessment reports, remediation
tracking) lives in this repository and must be version-controlled and auditable.

The structure must satisfy several competing forces:

- **Human navigability.** Team leads and DevOps engineers must be able to
  browse the repository and understand its layout without documentation.
- **Agent discoverability.** The `load_workspace()` function scans specific
  paths (`stem/agents/`, `stem/skills/`) to discover Copilot SDK artefacts.
  The directory layout must align with this discovery logic.
- **Auto-commit friendliness.** Assessment reports and remediation state are
  written by automated processes and committed directly. The directory layout
  must support per-target-repo output without merge conflicts.
- **Minimal configuration.** A single config file is preferred over multiple
  scattered files to reduce onboarding friction and config-file sprawl.

## Decision

Adopt a flat, single-root-config directory layout for Stem instance
repositories. The layout is:

```
<instance-repo>/
  stem.yaml               # Instance metadata, scoring thresholds, target repos
  README.md
  .gitignore
  blueprints/             # Blueprints and policies (flat, front-matter typed)
  stem/agents/            # Stem internal Copilot SDK agents
  stem/skills/            # Stem internal Copilot SDK skills
  .github/                # Developer-facing Copilot agents/skills/prompts
  reports/<owner>/<repo>/ # Auto-committed assessment output per target repo
  remediation/<owner>/<repo>/  # Remediation state per target repo
```

A single `stem.yaml` at the repository root holds all instance metadata:
scoring thresholds, the list of portfolio target repositories, and blueprint
source configuration. This was chosen because:

- It keeps all configuration discoverable in one file, reducing cognitive load
  for new contributors.
- It aligns with the project convention of YAML for structured configuration
  (see NARRATIVE.md §File formats).
- The `<owner>/<repo>` sub-directory pattern under `reports/` and
  `remediation/` provides natural namespacing, avoids filename collisions, and
  maps directly to the GitHub repository coordinate.

## Consequences

### Positive

- **POS-001**: All instance state is version-controlled and auditable through
  standard Git history — no external databases or binary state files.
- **POS-002**: Teams can review assessment changes and remediation plans via
  standard Git diffs and pull requests, leveraging existing code-review
  workflows.
- **POS-003**: The flat layout is immediately navigable for new contributors
  without requiring documentation.
- **POS-004**: The `<owner>/<repo>` sub-directory pattern eliminates merge
  conflicts when multiple target repos are assessed concurrently.

### Negative

- **NEG-001**: A single `stem.yaml` may become unwieldy for very large
  portfolios (hundreds of target repos). Splitting into separate files would
  require a future ADR.
- **NEG-002**: The `reports/` and `remediation/` directories grow linearly
  with the number of targets and assessment runs. At scale, index files or
  filtering mechanisms may be needed.
- **NEG-003**: Auto-committing report files directly increases repository size
  over time. A retention or archival strategy is not yet defined.

## Alternatives Considered

### Separate `targets.yaml` file

- **ALT-001**: **Description**: Maintain a dedicated `targets.yaml` alongside
  `stem.yaml` to hold the list of portfolio target repositories.
- **ALT-002**: **Rejection Reason**: Adds config-file sprawl without
  meaningful benefit. The targets list is small and logically belongs with
  other instance metadata. A single `stem.yaml` keeps everything in one place
  and reduces onboarding friction.

### Nested blueprint directories

- **ALT-003**: **Description**: Organise blueprints into subdirectories by
  type or domain (e.g., `blueprints/python/`, `blueprints/node/`) instead of
  a flat directory.
- **ALT-004**: **Rejection Reason**: Over-engineering for MVP. A flat directory
  with front-matter differentiation (`type: blueprint` vs `type: policy`) is
  simpler and sufficient. Nested directories can be introduced later without
  breaking changes.

### Database-backed configuration

- **ALT-005**: **Description**: Store instance configuration and state in a
  database (SQLite, PostgreSQL) rather than in Git-tracked files.
- **ALT-006**: **Rejection Reason**: Violates Stem's core design principle
  that all state lives in Git. A database would lose version history, diffs,
  and pull-request-based governance out of the box. It would also add
  infrastructure requirements (a running database) for what should be a
  lightweight, portable control plane.

## Implementation Notes

- **IMP-001**: `stem init` scaffolds this directory structure automatically,
  creating `stem.yaml`, `blueprints/`, `stem/agents/`, `stem/skills/`,
  `reports/`, and `remediation/` directories.
- **IMP-002**: The `load_workspace()` function in `src/stem/workspace.py`
  scans `stem/agents/` and `stem/skills/` for Copilot SDK artefacts. Any
  changes to the directory layout must be reflected there.
- **IMP-003**: Success criteria: running `stem init` in an empty Git
  repository produces a valid instance layout, and subsequent `stem assess`
  writes reports to the correct `reports/<owner>/<repo>/` path.

## References

- **REF-001**: [ADR-0004 — Agent/Skill Namespace Separation](adr-0004-agent-skill-namespace-separation.md) — explains why `stem/` and `.github/` are separate.
- **REF-002**: [ADR-0005 — Blueprint and Policy Colocation](adr-0005-blueprint-and-policy-colocation.md) — details the `blueprints/` directory layout.
- **REF-003**: NARRATIVE.md §Stem State & Storage — the design principle that all Stem state lives in Git.
