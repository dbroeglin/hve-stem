---
title: "ADR-0006: Blueprint Sourcing Strategy"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Stem Team"
tags: ["architecture", "blueprints", "sourcing", "cli", "init"]
supersedes: ""
superseded_by: ""
---

# ADR-0006: Blueprint Sourcing Strategy

## Status

**Accepted**

## Context

Teams need blueprints to assess their repositories against. Stem must provide
a strategy for how blueprints arrive in the `blueprints/` directory of an
instance repository. The strategy must satisfy two competing requirements:

- **Zero-config onboarding.** Running `stem init` with no extra flags should
  produce a working instance repository immediately — no network access, no
  external dependencies, no prior setup required.
- **Organisation customisation.** Enterprises and teams need the ability to
  maintain and share their own blueprint libraries, tailored to their specific
  SDLC standards, technology stacks, and compliance requirements.

Additional forces:

- **Reproducibility.** The provenance of blueprints must be recorded so that
  a future `stem init` or `stem update` can re-fetch the exact same version.
- **Simplicity.** For MVP, the sourcing mechanism should be easy to understand
  and implement without introducing complex dependency resolution.
- **Offline capability.** Developers working on planes, trains, or restricted
  networks must still be able to bootstrap a new instance.

## Decision

Implement a two-tier sourcing strategy where a bundled default blueprint is the
baseline, and a remote GitHub repository can optionally replace it:

1. **Default (bundled):** A default blueprint ships inside the `hve-stem`
   Python package at `app/stem/data/blueprints/default.md`. Running
   `stem init` with no extra flags copies this into `blueprints/`. Works
   offline, zero config.

2. **Remote override (`--blueprint <owner/repo>`):** Fetches blueprints from
   a remote GitHub repository. When specified, the remote blueprints
   **replace** the bundled default entirely (mutually exclusive, not
   additive).

3. **Ref pinning (`--blueprint-ref <branch|tag|sha>`):** Pins the remote
   source to a specific Git ref. Defaults to the repository's default branch
   if not specified.

The source is recorded in `stem.yaml` under `blueprint_source` for
reproducibility:

```yaml
blueprint_source:
  repo: "my-org/stem-blueprints"
  ref: "v1.0.0"
```

This approach was chosen because:

- The bundled default satisfies the zero-config requirement — no network
  call, no external repo, instant working state.
- The `--blueprint` flag provides a clean upgrade path to custom blueprints
  without complicating the default flow.
- Mutually exclusive sourcing (bundled *or* remote, not both) avoids
  ambiguity about which blueprint takes precedence when multiple sources
  are present.
- Recording the source in `stem.yaml` makes the provenance auditable and
  enables future `stem update` commands to re-fetch from the same source.
- Ref pinning gives organisations version control over their blueprint
  library, independent of Stem's release cycle.

## Consequences

### Positive

- **POS-001**: Zero-config experience — `stem init` works immediately with no
  network access or external dependencies.
- **POS-002**: Custom blueprints are a single CLI flag away, with no changes
  to the core workflow.
- **POS-003**: `stem.yaml` records provenance, enabling reproducible
  re-fetches and auditable configuration.
- **POS-004**: Ref pinning decouples blueprint versioning from Stem's release
  cycle, allowing organisations to update blueprints at their own pace.

### Negative

- **NEG-001**: The mutually exclusive model means teams cannot mix bundled
  and remote blueprints. An additive model may be needed in the future.
- **NEG-002**: Remote fetching implementation is deferred for MVP (a
  placeholder message is shown). The CLI contract and config schema are
  established, but the feature is not yet functional.
- **NEG-003**: The bundled default blueprint becomes stale between Stem
  releases. Users must upgrade Stem to get the latest default blueprint.
- **NEG-004**: No authentication mechanism is defined for fetching from
  private remote repositories. This will need to be addressed when remote
  fetching is implemented.

## Alternatives Considered

### Always remote

- **ALT-001**: **Description**: Require all blueprints to be fetched from a
  remote GitHub repository — no bundled default.
- **ALT-002**: **Rejection Reason**: Violates the zero-config and offline
  requirements. A fresh `stem init` would fail without network access and a
  pre-configured remote repository. This creates unnecessary onboarding
  friction, especially for evaluation and local development scenarios.

### Always bundled

- **ALT-003**: **Description**: Only support blueprints bundled inside the
  `hve-stem` package — no remote sourcing.
- **ALT-004**: **Rejection Reason**: Prevents organisations from maintaining
  their own blueprint libraries. Every custom blueprint would need to be
  contributed upstream to the `hve-stem` package, which does not scale and
  conflicts with the need for organisation-specific standards.

### Additive (bundled + remote)

- **ALT-005**: **Description**: When a remote source is specified, merge
  remote blueprints with the bundled default rather than replacing it.
- **ALT-006**: **Rejection Reason**: Creates ambiguity about which blueprint
  takes precedence when both the bundled default and a remote blueprint cover
  the same topic. For MVP, the simpler mutual-exclusion model avoids this
  complexity. The additive model may be revisited in a future iteration if
  there is demand.

### Package-manager-style blueprint dependencies

- **ALT-007**: **Description**: Treat blueprints as versioned packages with
  dependency resolution (similar to npm or pip).
- **ALT-008**: **Rejection Reason**: Massive over-engineering for MVP.
  Blueprints are simple Markdown files, not code modules. The complexity of
  dependency resolution, lock files, and version conflict handling is not
  justified by the current use case.

## Implementation Notes

- **IMP-001**: The default blueprint is bundled at
  `app/stem/data/blueprints/default.md` and installed as package data via
  hatchling.
- **IMP-002**: `stem init` copies the bundled blueprint into `blueprints/`
  by default. When `--blueprint <owner/repo>` is provided, the remote fetch
  replaces this copy step.
- **IMP-003**: Remote fetching is deferred — the CLI accepts the flag and
  records the source in `stem.yaml`, but shows a "not yet implemented"
  placeholder. The contract is stable; the implementation will follow.
- **IMP-004**: Success criteria: `stem init` creates `blueprints/default.md`
  from the bundled source, and `stem.yaml` records `blueprint: default.md`
  (or the remote source when `--blueprint` is used).

## References

- **REF-001**: [ADR-0005 — Blueprint and Policy Colocation](adr-0005-blueprint-and-policy-colocation.md) — how blueprints are organised once they arrive in the `blueprints/` directory.
- **REF-002**: [ADR-0003 — Stem Instance Repository Structure](adr-0003-stem-instance-repository-structure.md) — the overall directory layout.
- **REF-003**: NARRATIVE.md §Versioning — the upstream-to-instance flow model that this sourcing strategy implements.
