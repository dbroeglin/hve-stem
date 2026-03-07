## Project Specifics

- Language: Python 3.12.
- Package manager: uv; `pyproject.toml` is the single source of truth for all project metadata, dependencies, and tool configurations.
- Environment manager: uv. Use commands like `uv run` to execute within the virtual environment.
- Dependencies: Runtime dependencies are in `[project.dependencies]`; dev tools (e.g., mypy, pytest, ruff) are in the `dev` group under `[dependency-groups]`. No `requirements.txt` files are used.
- Layout: `app/stem/` for package code, `tests/` for pytest.
- Builds: hatchling backend.
- Entry point: `stem` CLI command via Typer (`stem.cli:app`).
- The narrative for this application is in `NARRATIVE.md`. 
- ADRs for this projects are in `docs/adr/` and follow the `adr-NNNN-title.md` naming convention.

## Code style

- Follow PEP 8 guidelines and use `snake_case` for variables and functions.
- Format all Python code with `ruff format`.
- Use explicit type hints for all function signatures.
- Keep functions small, focused, and pure where practical.
- Write clear docstrings for all public modules, classes, and functions.
- Use absolute imports from the `stem` package (e.g., `from stem.module import ...`).

## Testing

- Use `pytest` as the test runner.
- Write clear, focused unit tests for all new logic.
- Run validation: `uv run ruff format --check . && uv run mypy app/ && uv run ruff check app/ && uv run pytest`

## When working with Markdown files.

Format tables in a human readable way align the columns and use `|` to separate the columns. For example:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```
