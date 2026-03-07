# Contributing to HVE Stem

Thank you for your interest in contributing to **HVE Stem**! This guide will
help you get started.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report
unacceptable behaviour to the project maintainers.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 22+ and npm (for frontend work)
- A GitHub personal access token (`GITHUB_TOKEN`)

### Development Setup

1. Clone the repository and install dependencies:

   ```bash
   git clone https://github.com/<org>/hve-stem.git
   cd hve-stem
   uv sync
   ```

2. For frontend development, also install the Node dependencies:

   ```bash
   cd app && npm ci
   ```

See the [README](README.md) for full setup instructions.

## Making Changes

### Branch Naming

Use descriptive branch names with a category prefix:

| Prefix      | Purpose              |
|-------------|----------------------|
| `feat/`     | New feature          |
| `fix/`      | Bug fix              |
| `docs/`     | Documentation only   |
| `refactor/` | Code refactoring     |
| `test/`     | Adding/updating tests |
| `chore/`    | Maintenance tasks    |

Example: `feat/add-remediation-endpoint`

### Code Style

- **Python:** Follow PEP 8, use type hints, format with `ruff format`. See
  [AGENTS.md](AGENTS.md) for detailed conventions.
- **TypeScript:** Use strict mode, functional React components, and
  `@primer/react` components. See [AGENTS.md](AGENTS.md) for detailed
  conventions.

### Running Validation

Before submitting a pull request, run the full validation suites:

**Python:**

```bash
uv run ruff format --check . && uv run mypy src/ && uv run ruff check src/ && uv run pytest
```

**Frontend:**

```bash
cd app && npm run lint && npm test && npm run build
```

## Submitting a Pull Request

1. Create a feature branch from `main`.
2. Make your changes in small, focused commits.
3. Ensure all validation checks pass (see above).
4. Push your branch and open a pull request.
5. Fill in the PR template — include a summary, related issues, and
   screenshots if applicable.

### PR Checklist

- [ ] I have read this Contributing Guide.
- [ ] I have added or updated tests for my changes.
- [ ] I have added or updated documentation as needed.
- [ ] All validation checks pass locally.

## Reporting Issues

- **Bugs:** Use the bug report issue template. Include version info,
  reproduction steps, and relevant logs.
- **Feature requests:** Use the feature request issue template. Describe the
  use case and expected behaviour.

## Questions?

If you have questions that aren't covered here, open a discussion or issue and
we'll be happy to help.
