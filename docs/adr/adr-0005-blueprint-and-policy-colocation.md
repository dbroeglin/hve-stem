---
title: "ADR-0005: Blueprint and Policy Colocation"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Stem Team"
tags: ["architecture", "blueprints", "policies", "content-model"]
supersedes: ""
superseded_by: ""
---

# ADR-0005: Blueprint and Policy Colocation

## Status

**Accepted**

## Context

Stem uses two categories of reference documents to drive its assessment engine:

- **Blueprints** describe the desired state of an SDLC — what capabilities,
  workflows, and configurations a repository should have.
- **Policies** describe constraints and rules — what must or must not be true
  (e.g., "all PRs require at least one approval", "no secrets in code").

Both document types are consumed by the assessment agent as Markdown reference
material. The key question is how to organise them in the instance repository.

The forces at play are:

- **Simplicity.** Fewer directories mean less cognitive overhead and faster
  onboarding.
- **Discovery.** The assessment agent needs to find and load all reference
  documents efficiently. Fewer scan paths are better.
- **Differentiation.** Despite living together, blueprints and policies serve
  different conceptual purposes and must remain distinguishable.
- **Future extensibility.** The layout must accommodate features like blueprint
  inheritance (`extends:` key) without requiring a restructuring.

## Decision

Colocate blueprints and policies in a single flat `blueprints/` directory at
the instance repository root. Documents are differentiated by YAML
front-matter metadata, not by directory structure:

```yaml
---
type: blueprint   # or "policy"
name: default
description: Default SDLC blueprint for a modern software project.
---
```

No inheritance or `extends:` mechanism is implemented for MVP.

This approach was chosen because:

- Both document types serve the same functional purpose from the assessment
  agent's perspective: they are reference material to compare target repos
  against. A single directory reflects this shared purpose.
- Front-matter-based differentiation is more flexible than directory-based
  differentiation — adding new document types (e.g., `type: checklist`) only
  requires a new front-matter value, not a new directory.
- A flat layout eliminates debates about where mixed-concern documents
  (e.g., a blueprint that includes policy constraints) should live.
- The YAML front-matter conventions established now are designed to
  accommodate future features (`extends:`, `tags:`, `applies_to:`) without
  breaking changes.

## Consequences

### Positive

- **POS-001**: Simple, flat layout is easy to understand and maintain — a
  single `ls blueprints/` shows all reference documents.
- **POS-002**: Both blueprints and policies are discovered with a single
  directory scan, simplifying the assessment agent's loading logic.
- **POS-003**: Front-matter conventions established now provide a stable
  extension point for future features (inheritance, tagging, scoping) without
  requiring directory restructuring.
- **POS-004**: Adding new document types only requires defining a new
  `type:` value in front-matter, not creating new directories or updating
  scan paths.

### Negative

- **NEG-001**: With both document types in one directory, a large organisation
  with many blueprints and policies may find the flat listing hard to navigate.
  Naming conventions (e.g., `policy-*` prefix) can partially mitigate this.
- **NEG-002**: The assessment agent must parse front-matter to distinguish
  document types, adding a small amount of processing overhead compared to
  directory-based filtering.
- **NEG-003**: Developers unfamiliar with the project may expect a separate
  `policies/` directory and be initially confused by the colocation.

## Alternatives Considered

### Separate `policies/` directory

- **ALT-001**: **Description**: Maintain a dedicated `policies/` directory
  alongside `blueprints/` to hold organisational constraints and rules.
- **ALT-002**: **Rejection Reason**: Adds directory sprawl with minimal
  benefit. Both document types serve the same purpose (input to the assessment
  agent) and are processed identically. Splitting them creates an artificial
  boundary and doubles the number of directories to scan.

### Nested subdirectories per blueprint

- **ALT-003**: **Description**: Organise each blueprint as a directory
  containing multiple files (e.g., `blueprints/python-microservice/main.md`,
  `blueprints/python-microservice/checks.yaml`).
- **ALT-004**: **Rejection Reason**: Over-engineering for MVP. Each blueprint
  is a single Markdown file with front-matter. A flat directory is simpler
  and sufficient. If multi-file blueprints are needed in the future, this can
  be introduced without breaking existing single-file blueprints.

### Policy inheritance (`extends:` key)

- **ALT-005**: **Description**: Implement an inheritance mechanism where
  blueprints and policies can extend a base document (e.g.,
  `extends: base-policy`).
- **ALT-006**: **Rejection Reason**: Deferred to a future iteration. The
  added complexity is not justified for MVP, where teams typically have one
  or a small number of blueprints. The front-matter schema is designed to
  accommodate `extends:` when needed, so adding it later is non-breaking.

## Implementation Notes

- **IMP-001**: `stem init` copies the bundled default blueprint from
  `app/stem/data/blueprints/default.md` into the `blueprints/` directory
  during instance initialisation.
- **IMP-002**: The assessment agent should load all `*.md` files from
  `blueprints/` and use the `type:` front-matter field to categorise them.
  Files without front-matter should be treated as blueprints by default.
- **IMP-003**: Success criteria: `stem init` creates a `blueprints/`
  directory containing at least the default blueprint, and `stem assess`
  successfully loads it as reference material.

## References

- **REF-001**: [ADR-0003 — Stem Instance Repository Structure](adr-0003-stem-instance-repository-structure.md) — the overall layout in which `blueprints/` sits.
- **REF-002**: [ADR-0006 — Blueprint Sourcing Strategy](adr-0006-blueprint-sourcing-strategy.md) — how blueprints arrive in the `blueprints/` directory (bundled vs remote).
- **REF-003**: NARRATIVE.md §File formats — the convention that Markdown with YAML front-matter is the primary document format.
