# HVE Stem

**Control plane for agentic software development.**

Stem sits above your agentic workflows and developer tools, providing a single
surface to **bootstrap, govern, assess, and continuously improve** how your
team's agentic SDLC operates — across one or many repositories.

---

## Problem

Teams adopting agentic development (AI-assisted code review, automated issue
triage, agentic CI/CD) face fragmentation: capabilities are scattered across
tools, there is no unified view of maturity or health, and no systematic way to
enforce policies or improve over time.

## Solution

Stem answers: *"How mature is our agentic SDLC, what should we improve next,
and how do we enforce our standards?"*

| Concern                    | What Stem provides                                                                              |
|----------------------------|-------------------------------------------------------------------------------------------------|
| **Bootstrapping**          | Scaffold new repos or onboard existing ones with opinionated-but-customizable SDLC blueprints   |
| **Governance**             | Define and enforce policies and guardrails that constrain what agents can do across repos        |
| **Assessment**             | Evaluate SDLC maturity, code/repo health, and drift from desired blueprints — per repo or org   |
| **Observability**          | Surface how the agentic SDLC is performing (quality signals, pipeline health, policy compliance) |
| **Continuous improvement** | Learn from assessment outcomes and iteratively refine agent configurations and workflows         |

---

## Architecture

Stem uses a three-layer model. Only Layer 1 is part of this project:

```text
┌─────────────────────────────────────────────────┐
│  Layer 1 — Stem (this application)              │
│  Control plane: bootstrap, govern, assess,      │
│  observe, and improve the agentic SDLC          │
├─────────────────────────────────────────────────┤
│  Layer 2 — Substrate                            │
│  The agentic workflows and agents themselves    │
│  (GitHub Actions, Copilot, gh-aw, etc.)         │
├─────────────────────────────────────────────────┤
│  Layer 3 — Runtime                              │
│  Where the software built through Layer 2 runs  │
│  (Azure, or any other cloud / runtime)          │
└─────────────────────────────────────────────────┘
```

Stem exposes **three interfaces** with shared core capabilities:

| Interface    | Surface                          | Command          |
|--------------|----------------------------------|------------------|
| **CLI**      | Terminal commands                 | `stem <command>` |
| **MCP**      | Coding agents (Copilot, Claude…) | `stem mcp`       |
| **Web UI**   | Browser-based dashboard          | `stem serve`     |

All three interfaces expose the same operations — the CLI is the reference
implementation, and MCP + Web UI are built on top of the same core logic.

### Key commands

| Command          | Purpose                                                                                  |
|------------------|------------------------------------------------------------------------------------------|
| `stem init`      | Bootstrap a new project or onboard an existing repo with a Stem-managed SDLC blueprint   |
| `stem assess`    | Evaluate repos against the desired blueprint (maturity, health, drift detection)          |
| `stem remediate` | Create GitHub issues for each assessment finding with contextual fix suggestions          |
| `stem serve`     | Launch the web UI dashboard                                                              |
| `stem mcp`       | Start an MCP server for coding-agent integration                                         |

---

## Quick start

### 1. Install

```bash
uv tool install git+https://github.com/dbroeglin/hve-stem
```

### 2. Bootstrap a Stem instance repository

```bash
mkdir my-stem && cd my-stem
stem init
```

This creates the directory structure, default blueprints, and configuration
files that Stem uses to manage your portfolio.

### 3. Assess a repository

```bash
stem assess <owner/repo>
```

Stem inspects the target repository's workflows, configuration files, and
community health files, then produces a Markdown assessment report covering
delivery performance, code health, collaboration processes, agentic maturity,
and governance compliance.

### 4. Launch the web dashboard

```bash
stem serve
```

Opens a browser-based dashboard where you can run assessments and review results
visually.

---

## Documentation

- [NARRATIVE.md](NARRATIVE.md) — full design narrative and assessment model
- [MCP Server for Coding Agents](docs/mcp.md) — configure and run the `stem mcp` stdio server
- [Architecture Decision Records](docs/adr/) — ADRs documenting key design choices

---

## Setup and development

### Prerequisites

| Tool       | Required for       | Install                                                                                                    |
|------------|--------------------|------------------------------------------------------------------------------------------------------------|
| **uv**     | Python env & deps  | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js**| Frontend build only| [nodejs.org](https://nodejs.org/) (LTS recommended) — **not** needed at runtime                           |
| **Playwright CLI** | Browser testing | `npm install -g @playwright/cli@latest`                                                              |

### Install dependencies

```bash
# Python — sync all dependencies (including dev tools)
uv sync --group dev

# Frontend — install Node.js dependencies
cd app && npm ci
```

### Run the CLI locally (editable install)

```bash
uv tool install --editable /path/to/hve-stem
```

Then run commands from a Stem instance directory:

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

### Validation

**Python** (lint, type-check, test):

```bash
uv run ruff format --check . && uv run mypy src/ && uv run ruff check src/ && uv run pytest
```

**Frontend** (lint, build):

```bash
cd app && npm run lint && npm run build
```

### Build the Python package

```bash
# Build the frontend first
cd app && npm ci && npm run build && cd ..

# Build the Python package (wheel + sdist)
uv build
```

The resulting wheel in `dist/` includes the compiled frontend assets and can be
installed with `pip install` — no Node.js required at runtime.

### Deployment

Stem is designed to run **locally** or in **CI/CD pipelines**. There is no
dedicated cloud deployment target for the Stem application itself.

- **Local use:** Install via `uv tool install` and run `stem` commands directly.
- **CI/CD:** Add `stem assess` to a GitHub Actions workflow to evaluate
  repositories on a schedule or on pull requests. Authentication is resolved at
  runtime via `GITHUB_TOKEN` or `STEM_GITHUB_TOKEN` environment variables —
  no secrets are stored in Git.
- **Org-level automation:** Use a GitHub App installation to provide scoped,
  rotatable tokens across multiple repos without personal credentials.

---

## Responsible AI

Stem uses AI models (via the [GitHub Copilot SDK](https://github.com/github/copilot-sdk))
to perform assessments and generate recommendations. The following principles
guide its design:

- **Human-in-the-loop.** Stem follows a *passive assessment + active
  recommendation* model. It reports findings and opens issues but does **not**
  automatically modify code or repository settings without explicit user action.
- **Transparency.** Every assessment produces a full Markdown report with
  per-check reasoning. The event log surfaces all tool calls and model
  interactions so users can audit how conclusions were reached.
- **Grounded evaluation.** Assessment checks are rooted in established research
  frameworks (DORA, SPACE, DevEx) rather than arbitrary opinions. Each check
  maps to a documented metric or capability.
- **No secrets in state.** All Stem state lives in Git as human-readable
  Markdown and YAML. Authentication credentials are never stored in the
  repository — they are resolved from the environment at runtime.
- **Graceful degradation.** When data sources or APIs are unavailable, Stem
  documents what is missing rather than fabricating results or silently skipping
  checks.
- **Scope limits.** Stem reads Layer 2 (GitHub) and optionally Layer 3
  (runtime) data in a **read-only** capacity for assessment purposes. Write
  operations (issue creation, PR suggestions) are gated behind explicit
  commands (`stem remediate`) and user confirmation.

---

## License

See [LICENSE.md](LICENSE.md).
