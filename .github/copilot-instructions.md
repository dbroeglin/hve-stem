## Project Specifics

- Language: Python 3.12.
- Package manager: uv; `pyproject.toml` is the single source of truth for all project metadata, dependencies, and tool configurations.
- Dependencies: Runtime dependencies are in `[project.dependencies]`; dev tools (e.g., black, mypy, pytest, ruff) are in the `dev` group under `[dependency-groups]`. No `requirements.txt` files are used.
- Layout: `src/stem/` for package code, `tests/` for pytest, `scripts/` for helpers.
- Builds: hatchling backend.
- Entry point: `stem` CLI command via Typer (`stem.cli:app`).

## Code style

- Follow PEP 8 guidelines and use `snake_case` for variables and functions.
- Format all Python code with `black`.
- Use explicit type hints for all function signatures.
- Keep functions small, focused, and pure where practical.
- Write clear docstrings for all public modules, classes, and functions.
- Default to absolute imports relative to the `src` directory (e.g., `from stem.module import ...`).

## Testing

- Use `pytest` as the test runner.
- Write clear, focused unit tests for all new logic.
- Run validation: `black . && mypy src/ && ruff check src/ && pytest`

## When working with Mardkown files.

Format tables in a human readable way align the columns and use `|` to separate the columns. For example:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```
