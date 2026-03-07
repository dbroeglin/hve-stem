## Project Specifics

- Language: Python 3.12.
- Package manager: uv; `pyproject.toml` is the single source of truth for all project metadata, dependencies, and tool configurations.
- Environment manager: uv. Use commands like `uv run` to execute within the virtual environment.
- Dependencies: Runtime dependencies are in `[project.dependencies]`; dev tools (e.g., mypy, pytest, ruff) are in the `dev` group under `[dependency-groups]`. No `requirements.txt` files are used.
- Layout: `src/stem/` for package code, `tests/` for pytest.
- Builds: hatchling backend.
- Entry point: `stem` CLI command via Typer (`stem.cli:app`).
- The narrative for this application is in `NARRATIVE.md`. 
- ADRs for this projects are in `docs/adr/` and follow the `adr-NNNN-title.md` naming convention.

## UI/UX

- The UI uses the Github `@primer/react` component library and design system. 
- The UI should follow Primer's design tokens and best practices for accessibility and responsiveness. 
- The UI should look good in both light and dark modes without custom theming.
- The UI should look similar to GitHub.com in its look and feel, using Primer components and styles.

## Code style

### Python 

- Follow PEP 8 guidelines and use `snake_case` for variables and functions.
- Format all Python code with `ruff format`.
- Use explicit type hints for all function signatures.
- Keep functions small, focused, and pure where practical.
- Write clear docstrings for all public modules, classes, and functions.
- Use absolute imports from the `stem` package (e.g., `from stem.module import ...`).

### Typescript

- Use TypeScript strict mode (`"strict": true` in `tsconfig.json`).
- Use `camelCase` for variables and functions, `PascalCase` for components and types.
- Use explicit return types for non-trivial functions.
- Prefer named exports over default exports.
- Use functional React components with hooks — no class components.
- Use `@primer/react` components instead of raw HTML elements whenever a Primer equivalent exists (Button, Text, Box, Flash, DataTable, TreeView, ActionMenu, PageLayout, etc.).
- Import Primer components from `@primer/react` (e.g., `import { Button, Box } from '@primer/react'`).
- Wrap the application root with Primer's `ThemeProvider` and `BaseStyles`.
- Use `@primer/primitives` design tokens via CSS variables for any custom styling — do not hardcode colours, spacing, or typography values.
- Keep components small and composable. Place route-level components in `app/src/pages/` and shared UI components in `app/src/components/`.
- Place API client code and SSE hook wrappers in `app/src/api/`.
- Use `react-router` for client-side routing.
- For real-time updates (assessment progress, remediation status), use Server-Sent Events (SSE) via the browser `EventSource` API wrapped in React hooks — not WebSockets.

## Testing

### Python 

- Use `pytest` as the test runner.
- Write clear, focused unit tests for all new logic.
- Run validation: `uv run ruff format --check . && uv run mypy src/ && uv run ruff check src/ && uv run pytest`

### React/Typescript

- Use Vitest as the test runner and React Testing Library for component tests.
- Co-locate test files next to the source file using the `*.test.tsx` / `*.test.ts` naming convention.
- Run frontend tests: `cd app && npm test`
- Run frontend lint: `cd app && npm run lint`
- Run full frontend validation: `cd app && npm run lint && npm test && npm run build`

## Build & Packaging

### Frontend build

The React frontend in `app/` builds with Vite and outputs directly into `src/stem/data/static/` (configured via `build.outDir` in `app/vite.config.ts`). This directory is gitignored — only a `.gitkeep` is committed.

```bash
cd app && npm ci && npm run build
```

After building, `uv run stem serve` serves the full React UI.

### Python package

The Python wheel includes the built frontend assets via the `artifacts` setting in `pyproject.toml`. To build a distributable package:

```bash
cd app && npm ci && npm run build && cd ..
uv build
```

The resulting wheel in `dist/` is fully self-contained — no Node.js required at runtime.

### Frontend dev inner loop

For day-to-day frontend work, run the FastAPI backend and Vite dev server side by side (no Python rebuild needed):

```bash
# Terminal 1 — API server
uv run stem serve --no-browser

# Terminal 2 — Vite dev server with HMR + API proxy
cd app && npm run dev
```

Open `http://localhost:5173`. The Vite config proxies `/api/*` to the FastAPI backend at port 8777.

## When working with Markdown files.

Format tables in a human readable way align the columns and use `|` to separate the columns. For example:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```
