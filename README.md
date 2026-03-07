# hve-stem

Stem instance repository — control plane for agentic software development.

## Getting started

```bash
uv tool install git+https://github.com/dbroeglin/hve-stem

stem assess <owner/repo>
```

## Development

### Prerequisites

#### UV

Install UV by following the instructions at [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/). For example, on Unix systems you can run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Node.js

Node.js is required **only for building the frontend** — it is NOT needed at
runtime. Install via [https://nodejs.org/](https://nodejs.org/) (LTS
recommended) or your preferred version manager (nvm, fnm, etc.).

#### Playwright CLI

Install the Playwright CLI by following the instructions at [https://github.com/microsoft/playwright-cli](https://github.com/microsoft/playwright-cli). For example, you can run:

```bash
npm install -g @playwright/cli@latest
playwright-cli --help
```

### Install dependencies

```bash
# Python — sync all dependencies (including dev tools)
uv sync --group dev

# Frontend — install Node.js dependencies
cd app && npm ci
```

### Run the CLI locally (editable install)

Install the `stem` command referencing your local copy of the repository:

```bash
uv tool install --editable /path/to/hve-stem
```

Then you can run the command as normal from a Stem instance directory:

```bash
stem init
```

### Build the frontend

The React frontend in `app/` is built with Vite and outputs directly into
`src/stem/data/static/` so it is bundled inside the Python package:

```bash
cd app && npm run build
```

After this, `uv run stem serve` will serve the full React UI.

### Run `stem serve`

```bash
# Serve the web UI (opens browser automatically)
uv run stem serve

# Serve without opening a browser, on a custom port
uv run stem serve --no-browser --port 9000
```

### Frontend development inner loop

For day-to-day frontend work you do **not** need to rebuild the Python package.
Run the FastAPI backend and the Vite dev server side by side:

```bash
# Terminal 1 — Start the API server
uv run stem serve --no-browser

# Terminal 2 — Start the Vite dev server with HMR + API proxy
cd app && npm run dev
```

Open `http://localhost:5173` in your browser. Vite provides instant Hot Module
Replacement — changing a React component updates the browser in under a second.
The `/api/*` requests are proxied to the FastAPI backend at port 8777.

### Python validation (lint, type-check, test)

```bash
uv run ruff format --check .
uv run ruff check src/
uv run mypy src/
uv run pytest
```

Or all at once:

```bash
uv run ruff format --check . && uv run mypy src/ && uv run ruff check src/ && uv run pytest
```

### Frontend validation (lint, test, build)

```bash
cd app && npm run lint && npm run build
```

### Build the Python package

Build the wheel with the frontend assets included:

```bash
# Build the frontend first
cd app && npm ci && npm run build && cd ..

# Build the Python package (wheel + sdist)
uv build
```

The resulting wheel in `dist/` includes the compiled frontend assets and can be
installed with `pip install` — no Node.js required at runtime.
