---
title: "ADR-0007: Externalized MCP Server Configuration"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Stem Team"
tags: ["architecture", "mcp", "configuration", "instance"]
supersedes: ""
superseded_by: ""
---

# ADR-0007: Externalized MCP Server Configuration

## Status

**Accepted**

## Context

The `stem assess` command uses the Copilot SDK to create an agentic session
that connects to multiple MCP servers (GitHub, Microsoft Docs, WorkIQ,
Azure MCP). Previously, the MCP server configuration was hardcoded as a Python
dictionary (`MCP_SERVERS`) directly in `app/stem/commands/assess.py`.

This caused several problems:

- **No instance-level customisation.** Teams could not add, remove, or
  reconfigure MCP servers without modifying the Stem source code itself.
- **Tight coupling.** The MCP server list was embedded in application logic
  rather than treated as configuration data.
- **No visibility.** The available MCP servers were invisible to users browsing
  the instance repository — they could not discover or audit which external
  services the assessment agent connects to.

## Decision

Externalize the MCP server configuration into a `stem/mcp.json` file within
the Stem instance repository. The file follows the standard `mcpServers`
convention:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${TOKEN}" },
      "tools": ["*"]
    }
  }
}
```

Key design choices:

- **Location: `stem/mcp.json`** — placed inside the `stem/` directory
  alongside agents and skills, since it is Stem-internal configuration consumed
  by the Copilot SDK session (not developer-facing `.github/` config).
- **Format: JSON** — chosen over YAML because MCP tooling across the ecosystem
  (VS Code, Claude Code, GitHub Copilot) uses JSON for `mcp.json` /
  `mcp-config.json` files. Using the same format reduces cognitive overhead
  and enables copy-paste between Stem config and other MCP consumers.
- **Key: `mcpServers`** — mirrors the convention used by VS Code MCP
  configuration and the Copilot SDK, making the format instantly recognizable
  to developers already familiar with MCP tooling.
- **Bundled default** — a default `mcp.json` ships with Stem in
  `app/stem/data/stem/mcp.json` and is copied into new instance repositories
  by `stem init`.
- **Runtime loading** — `assess.py` loads the file at runtime via
  `_load_mcp_servers(workspace_root)`, which reads and parses
  `<workspace_root>/stem/mcp.json`. A clear error is raised if the file is
  missing.

## Consequences

### Positive

- **POS-001**: Teams can customise MCP servers per instance by editing
  `stem/mcp.json` — adding private MCP servers, removing unused ones, or
  tuning tool filters — without forking Stem.
- **POS-002**: MCP configuration is version-controlled and auditable alongside
  all other Stem instance state.
- **POS-003**: The configuration is visible and discoverable by browsing the
  instance repository.
- **POS-004**: The format aligns with the broader MCP ecosystem (VS Code,
  Copilot SDK), reducing learning curve.

### Negative

- **NEG-001**: Adding a new file to the instance layout increases the number
  of artefacts users must understand (mitigated by placing it in the
  already-established `stem/` directory).
- **NEG-002**: JSON does not support comments, so inline documentation within
  the file is not possible. This is accepted as a trade-off for ecosystem
  alignment.

## Alternatives Considered

### Keep MCP config in `stem.yaml`

- **Description**: Add an `mcp_servers:` key to the existing `stem.yaml`.
- **Rejection Reason**: YAML is not the standard format for MCP configuration
  in the ecosystem. It would require a translation layer and diverge from
  conventions used by VS Code and other MCP consumers.

### Keep MCP config hardcoded in Python

- **Description**: Leave the `MCP_SERVERS` dictionary in `assess.py`.
- **Rejection Reason**: Prevents instance-level customisation and violates the
  principle that all Stem instance state lives in Git-tracked configuration
  files.

### Use `.github/mcp.json`

- **Description**: Place the file in `.github/` alongside developer-facing
  Copilot configuration.
- **Rejection Reason**: The MCP servers in this file are consumed by Stem's
  internal Copilot SDK session, not by developer-facing tools. Per ADR-0004
  (Namespace Separation), Stem-internal artefacts belong in `stem/`, not
  `.github/`.

## Implementation Notes

- **IMP-001**: `stem init` copies the default `mcp.json` from the bundled
  `app/stem/data/stem/` directory into the new instance's `stem/` directory.
- **IMP-002**: `_load_mcp_servers()` in `assess.py` raises
  `FileNotFoundError` with a helpful message if `stem/mcp.json` is missing.
- **IMP-003**: Existing instance repositories created before this change will
  need to manually add `stem/mcp.json` (or re-run a future `stem upgrade`
  command once available).

## References

- **REF-001**: [ADR-0003 — Stem Instance Repository Structure](adr-0003-stem-instance-repository-structure.md) — defines the instance directory layout.
- **REF-002**: [ADR-0004 — Agent/Skill Namespace Separation](adr-0004-agent-skill-namespace-separation.md) — explains why `stem/` is the correct location.
- **REF-003**: NARRATIVE.md §File formats — JSON is an accepted format for machine-readable configuration.
