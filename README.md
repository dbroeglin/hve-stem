# HyperVelocity Stem

**Stem is a control plane for agentic software development.** It sits above agentic workflows and developer tools, providing a single surface to bootstrap, govern, assess, and continuously improve how a team's agentic SDLC operates — across one or many repositories.

## Quick Start

```bash
# Install dependencies (requires uv)
uv sync --group dev

# Run the CLI
stem --help

# Run tests
uv run pytest -v
```

## CLI Commands

| Command        | Purpose                                                                 |
| -------------- | ----------------------------------------------------------------------- |
| `stem init`    | Bootstrap a new project or onboard an existing repo with an SDLC blueprint |
| `stem assess`  | Evaluate repos against desired SDLC blueprints                          |
| `stem serve`   | Launch the web UI dashboard                                             |
| `stem mcp`     | Start an MCP server for coding agent integration                        |

## Project Structure

```
src/stem/              # Python package
  cli.py               # Typer CLI entry point
  commands/            # Subcommands (init, assess, serve, mcp)
tests/                 # pytest test suite
.devcontainer/         # Dev container configuration
```

## Tech Stack

- **Python 3.12** with **UV** for package management
- **Typer** + **Rich** for the CLI
- **hatchling** build backend
- **ruff**, **mypy**, **pytest** for dev tooling

## Development

```bash
# Format
ruff format .

# Type check
mypy src/

# Lint
ruff check src/

# Test
pytest
```

For the full project narrative, see [NARRATIVE.md](NARRATIVE.md).
