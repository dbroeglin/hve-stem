---
title: "ADR-0001: Python CLI as the Foundation Technology"
status: "Accepted"
date: "2026-03-06"
authors: "HVE Stem Team"
tags: ["architecture", "language", "cli", "mvp", "foundation"]
supersedes: ""
superseded_by: ""
---

# ADR-0001: Python CLI as the Foundation Technology

## Status

**Accepted**

## Context

Stem is a control plane for agentic software development. It must provide
three interfaces with feature parity: a CLI (`stem <command>`), a local MCP
server (`stem mcp`) for coding agents like GitHub Copilot, and a web UI
dashboard (`stem serve`). The primary users are team leads and DevOps
engineers.

The team needed to choose a language and application framework to build the
MVP. The decision is foundational — it determines development velocity,
ecosystem access, and how easily the three interfaces can be delivered.

The forces at play:

- **Speed to first demo.** The MVP must deliver a working `stem init` and
  `stem assess` flow as fast as possible to validate the product concept.
  A slow start risks losing momentum and stakeholder confidence.
- **Triple interface from one codebase.** The CLI, MCP server, and web UI
  must share the same core logic. The language must have mature libraries
  for all three: terminal UI, the Model Context Protocol, and HTTP serving.
- **AI/LLM ecosystem alignment.** Stem drives agentic workflows via the
  GitHub Copilot SDK and consumes LLM responses. The AI/ML ecosystem is
  overwhelmingly Python-first — SDKs, examples, and community support are
  strongest there.
- **Team familiarity.** The founding team is fluent in Python. Choosing a
  less familiar language would slow the MVP without delivering compensating
  benefits at this stage.
- **Operational simplicity.** Stem is a developer tool, not a
  high-throughput data service. Raw runtime performance is not a primary
  concern; developer productivity and iteration speed are.

## Decision

Build Stem as a **Python 3.12 CLI application** using the following stack:

| Concern           | Library                                                                   |
|-------------------|---------------------------------------------------------------------------|
| CLI framework     | [Typer](https://typer.tiangolo.com/)                                      |
| Terminal output   | [Rich](https://rich.readthedocs.io/)                                      |
| MCP server        | [mcp](https://pypi.org/project/mcp/) (official Python MCP SDK)            |
| Copilot SDK       | [github-copilot-sdk](https://github.com/github/copilot-sdk)               |
| Configuration     | [PyYAML](https://pyyaml.org/)                                             |
| Build system      | [Hatchling](https://hatch.pypa.io/)                                       |
| Package manager   | [uv](https://github.com/astral-sh/uv)                                     |
| Linting/Formatting| [Ruff](https://docs.astral.sh/ruff/)                                      |
| Type checking     | [mypy](https://mypy-lang.org/) (strict mode)                              |
| Testing           | [pytest](https://docs.pytest.org/)                                        |

The CLI entry point is `stem` (via `stem.cli:app`), registered as a
`[project.scripts]` console entry point.

This stack was chosen because:

- **Typer + Rich** deliver a polished CLI with argument parsing, help
  generation, colour output, and progress bars out of the box — a
  production-quality terminal experience with minimal code.
- **The official MCP Python SDK** (`mcp` package with `FastMCP`) makes
  exposing Stem commands as MCP tools trivial. Adding a new MCP tool is a
  single decorated function wrapping the same core logic the CLI uses.
  This directly enables the `stem mcp` interface for GitHub Copilot and
  other coding agents.
- **Python's HTTP ecosystem** (FastAPI, Starlette, Flask) makes the future
  `stem serve` web UI straightforward. Typer itself is built on Click, which
  integrates cleanly with ASGI frameworks.
- **The GitHub Copilot SDK** and the broader AI/ML ecosystem are Python-first.
  LangChain, OpenAI, Anthropic, and similar libraries all have Python as
  their primary language. Choosing Python avoids friction when integrating
  with these tools.
- **uv + Ruff + Hatchling** provide a modern, fast Python toolchain.
  Dependency resolution, formatting, linting, and building are all
  sub-second operations, keeping the development feedback loop tight.

## Consequences

### Positive

- **POS-001**: Fastest path to a working MVP. Python's expressiveness and
  the maturity of Typer/Rich mean the team can ship a functional CLI in
  days, not weeks.
- **POS-002**: All three interfaces (CLI, MCP, Web UI) can be delivered from
  a single Python codebase with shared core logic, fulfilling the parity
  principle with minimal duplication.
- **POS-003**: The MCP server (`stem mcp`) is trivially implemented via
  `FastMCP`, making Stem immediately consumable by GitHub Copilot, Claude
  Code, and other MCP-compatible agents.
- **POS-004**: Direct access to the AI/ML ecosystem — the GitHub Copilot
  SDK, LLM client libraries, and document-processing tools are all
  Python-native with first-class support.
- **POS-005**: The modern Python toolchain (uv, Ruff, mypy strict) keeps
  code quality high and the development loop fast despite Python's dynamic
  nature.

### Negative

- **NEG-001**: Python is slower at runtime than compiled languages (Go, Rust).
  For Stem's use case (orchestration, API calls, report generation) this is
  not a bottleneck, but could matter if Stem later needs high-throughput
  data processing.
- **NEG-002**: Distributing Python CLI tools to end users is more complex
  than distributing a single static binary. Users need a Python runtime or
  a tool like `pipx`/`uv tool install` to install Stem.
- **NEG-003**: Python's dynamic typing, even with mypy strict, provides
  weaker compile-time guarantees than statically typed languages. Bugs that
  would be caught at compile time in Go or Rust may only surface at runtime.
- **NEG-004**: Pinning to Python `>=3.12,<3.13` limits compatibility with
  environments that have not yet upgraded to 3.12.

## Alternatives Considered

### Go CLI

- **ALT-001**: **Description**: Build Stem as a Go application using Cobra
  for CLI, with a compiled binary distribution. Go excels at producing single
  static binaries and has strong concurrency primitives.
- **ALT-002**: **Rejection Reason**: The AI/ML ecosystem is Python-centric.
  The GitHub Copilot SDK, the MCP Python SDK (`FastMCP`), and most LLM
  client libraries are Python-first. Using Go would require maintaining
  custom bindings or shelling out to Python sub-processes, slowing down
  the MVP and creating ongoing maintenance burden. Go's static binary
  advantage is less relevant for a developer tool that targets environments
  where Python is typically already available.

### TypeScript / Node.js CLI

- **ALT-003**: **Description**: Build Stem as a Node.js CLI application
  using frameworks like Commander or oclif, leveraging the JavaScript
  ecosystem.
- **ALT-004**: **Rejection Reason**: While TypeScript has decent MCP support
  and web UI frameworks, the AI/ML ecosystem integration is weaker than
  Python's. The Copilot SDK's primary language is Python. Additionally,
  the founding team has deeper Python expertise, and Node.js would
  introduce a runtime dependency (Node) that is less commonly
  pre-installed in DevOps-oriented environments compared to Python.

### Rust CLI

- **ALT-005**: **Description**: Build Stem in Rust for maximum performance
  and a single compiled binary, using Clap for CLI argument parsing.
- **ALT-006**: **Rejection Reason**: Rust's development velocity for a
  prototype is significantly slower than Python's due to the borrow
  checker, longer compile times, and more verbose code. The MCP and
  Copilot SDK ecosystems have no mature Rust support. The performance
  advantages of Rust are irrelevant for Stem's workload (network I/O
  bound orchestration, not CPU-bound computation). The MVP timeline
  would be extended by weeks to months.

### Python with Click (instead of Typer)

- **ALT-007**: **Description**: Use Click directly as the CLI framework
  instead of Typer, which is a wrapper around Click.
- **ALT-008**: **Rejection Reason**: Typer provides the same functionality
  as Click with less boilerplate by leveraging Python type hints for
  argument definitions. Since Stem already uses type hints throughout
  (mypy strict), Typer is a natural fit. The thin wrapper adds negligible
  overhead and reduces CLI definition code by roughly 40% compared to
  raw Click decorators.

## Implementation Notes

- **IMP-001**: The CLI entry point is `stem = "stem.cli:app"` in
  `pyproject.toml`. All commands are registered in `src/stem/cli.py` via
  `app.command()`.
- **IMP-002**: Core command logic lives in `src/stem/commands/<command>.py`.
  Each command module exports a function that is registered on the Typer
  app. Both the CLI and MCP interfaces call the same underlying functions,
  ensuring parity.
- **IMP-003**: The MCP server (`src/stem/commands/mcp.py`) wraps core
  command functions with `@_mcp.tool()` decorators from `FastMCP`. Adding
  new MCP tools requires only a decorated async wrapper function.
- **IMP-004**: The validation pipeline is:
  `ruff format --check . && mypy src/ && ruff check src/ && pytest`.
  All four checks must pass before merging.

## References

- **REF-001**: NARRATIVE.md §Interfaces & Commands — the parity principle requiring CLI, MCP, and Web UI from a shared core.
- **REF-002**: [Typer documentation](https://typer.tiangolo.com/) — the CLI framework.
- **REF-003**: [MCP Python SDK (FastMCP)](https://pypi.org/project/mcp/) — the library enabling `stem mcp`.
- **REF-004**: [GitHub Copilot SDK](https://github.com/github/copilot-sdk) — the SDK for agentic workflow integration.
- **REF-005**: [uv](https://github.com/astral-sh/uv) — the package manager and Python project toolchain.
