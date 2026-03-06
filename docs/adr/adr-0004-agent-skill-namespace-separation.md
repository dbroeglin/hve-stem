---
title: "ADR-0004: Agent/Skill Namespace Separation"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Team"
tags: ["architecture", "agents", "skills", "copilot-sdk", "namespace"]
supersedes: ""
superseded_by: ""
---

# ADR-0004: Agent/Skill Namespace Separation

## Status

**Accepted**

## Context

Stem uses the GitHub Copilot SDK to discover agents and skills from a
workspace directory. GitHub Copilot (the IDE assistant) independently discovers
agents and skills from `.github/agents/` and `.github/skills/`. This creates a
namespace collision problem: if Stem's internal agents (e.g., the assessment
agent) and developer-facing Copilot agents (e.g., coding assistants,
repository-specific helpers) live in the same directory, they become
indistinguishable to the discovery mechanisms.

The forces at play are:

- **Stem runtime isolation.** Stem's internal agents drive its core
  capabilities (assessment, remediation) and must not be polluted or
  accidentally overridden by developer-created agents.
- **GitHub convention compatibility.** `.github/agents/` and `.github/skills/`
  are the standard GitHub locations for developer-facing Copilot extensions.
  Stem should not break this convention.
- **Discoverability for contributors.** The directory hosting Stem's internal
  agents should be visible and easy to find for contributors working on Stem
  itself, not hidden in a dot-directory.
- **`load_workspace()` alignment.** The workspace discovery function must know
  where to scan for each category of artefact.

## Decision

Separate Stem internal agents/skills from developer-facing Copilot agents by
placing them in distinct top-level directories:

| Concern                | Directory                          |
|------------------------|------------------------------------|
| Stem internal agents   | `stem/agents/`                     |
| Stem internal skills   | `stem/skills/`                     |
| Developer agents       | `.github/agents/`                  |
| Developer skills       | `.github/skills/`                  |
| Developer prompts      | `.github/prompts/`                 |
| Copilot instructions   | `.github/copilot-instructions.md`  |

The `stem/` directory at the repository root serves as the Copilot SDK workdir
for Stem's own runtime. This approach was chosen because:

- It creates an unambiguous ownership boundary: `stem/` is Stem's domain,
  `.github/` is the developer's domain.
- The `stem/` directory is visible in the repository root, making it easy for
  Stem contributors to find and modify internal agents.
- It preserves full compatibility with the standard GitHub Copilot discovery
  paths in `.github/`.
- The `load_workspace()` function can scan both paths with clear intent:
  `stem/agents/` and `stem/skills/` for the SDK workdir, `.github/agents/`
  for developer agents.

## Consequences

### Positive

- **POS-001**: Clean separation between Stem runtime artefacts and
  developer-facing tooling — no namespace collisions.
- **POS-002**: Contributors can work on developer-facing agents in `.github/`
  without risk of breaking Stem's internal operation.
- **POS-003**: The standard GitHub Copilot agent/skill discovery paths remain
  unmodified, ensuring compatibility with the broader GitHub ecosystem.
- **POS-004**: The `stem/` directory is visible and self-documenting in the
  repository root, lowering the learning curve for new Stem contributors.

### Negative

- **NEG-001**: Two separate directory trees for agent/skill discovery increase
  the number of paths `load_workspace()` must scan.
- **NEG-002**: Contributors unfamiliar with Stem may be confused by the
  `stem/` directory alongside `.github/`, requiring documentation to explain
  the split.
- **NEG-003**: If GitHub introduces new conventions for Copilot discovery
  paths in the future, the dual-directory approach may need to be reconciled.

## Alternatives Considered

### `.stem/` hidden directory

- **ALT-001**: **Description**: Place Stem's internal agents in a hidden
  `.stem/` directory (e.g., `.stem/agents/`, `.stem/skills/`) to keep them out
  of the visible directory listing.
- **ALT-002**: **Rejection Reason**: Hidden directories are harder to discover
  for new contributors. Since Stem is an actively developed tool, visibility
  of its internal structure is a feature, not a bug.

### Top-level `agents/` directory

- **ALT-003**: **Description**: Use a generic top-level `agents/` directory
  for Stem's internal agents.
- **ALT-004**: **Rejection Reason**: A generic name conflicts with potential
  user code directories and provides no ownership signal. The `stem/` prefix
  makes it unambiguous that these artefacts belong to the Stem runtime.

### Everything in `.github/`

- **ALT-005**: **Description**: Place all agents (Stem internal and
  developer-facing) in `.github/agents/` and differentiate them via naming
  conventions or front-matter metadata.
- **ALT-006**: **Rejection Reason**: Causes direct namespace collisions in
  the GitHub Copilot discovery path. Developer-facing IDE agents would see
  Stem's internal agents in their agent list, creating confusion and
  potentially surfacing internal implementation details to end users.

## Implementation Notes

- **IMP-001**: The `load_workspace()` function in `src/stem/workspace.py`
  scans `stem/agents/` and `stem/skills/` for the Copilot SDK workdir, and
  `.github/agents/` for developer-facing agents. Both paths must be kept in
  sync with this ADR.
- **IMP-002**: `stem init` should scaffold both `stem/agents/` and
  `.github/` directory structures in new instance repositories.
- **IMP-003**: Documentation should clearly explain the two-directory
  convention in the repository README and the Stem contributor guide.

## References

- **REF-001**: [ADR-0003 — Stem Instance Repository Structure](adr-0003-stem-instance-repository-structure.md) — the overall directory layout that this decision fits within.
- **REF-002**: [GitHub Copilot SDK](https://github.com/github/copilot-sdk) — the SDK whose discovery mechanism drives the workspace scanning logic.
- **REF-003**: NARRATIVE.md §Architecture — the three-layer model (Layer 1 Stem, Layer 2 Substrate) that motivates the separation.
