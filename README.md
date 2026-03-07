# HVE Stem

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![CI](https://img.shields.io/github/actions/workflow/status/dbroeglin/hve-stem/ci.yml?label=CI)

> **Control plane for agentic software development.**

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

> For a detailed breakdown of components, data flows, and module boundaries see
> [ARCHITECTURE.md](ARCHITECTURE.md).

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

| Command                                  | Purpose                                                                                  |
|------------------------------------------|------------------------------------------------------------------------------------------|
| [`stem init`](docs/commands/init.md)           | Bootstrap a new project or onboard an existing repo with a Stem-managed SDLC blueprint   |
| [`stem assess`](docs/commands/assess.md)       | Evaluate repos against the desired blueprint (maturity, health, drift detection)          |
| [`stem remediate`](docs/commands/remediate.md) | Create GitHub issues for each assessment finding with contextual fix suggestions          |
| [`stem serve`](docs/commands/serve.md)         | Launch the web UI dashboard                                                              |
| [`stem mcp`](docs/commands/mcp.md)             | Start an MCP server for coding-agent integration                                         |

### Using the Stem as an MCP server from VS Code or Copilot CLI

Add the following configuration to your coding agent to leverage Stem as a MCP server:

```json
{
  "mcpServers": {
    "stem": {
      "type": "stdio",
      "command": "stem",
      "args": ["mcp"],
      "tools": ["*"]
    }
  }
}
```

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

When configured, Stem can also query [Apache DevLake](https://devlake.apache.org/)
for computed DORA metrics, PR statistics, and CI/CD health data — see
[ADR-0010](docs/adr/adr-0010-devlake-as-metric-backend.md) for details.

### 4. Launch the web dashboard

```bash
stem serve
```

Opens a browser-based dashboard where you can run assessments and review results
visually.

---

## Documentation

- [NARRATIVE.md](NARRATIVE.md) — full design narrative and assessment model
- [Architecture Decision Records](docs/adr/) — ADRs documenting key design choices

### Command reference

| Command                                  | Reference                                               |
|------------------------------------------|---------------------------------------------------------|
| [`stem init`](docs/commands/init.md)           | Arguments, flags, directory structure created            |
| [`stem assess`](docs/commands/assess.md)       | Arguments, flags, output format, examples               |
| [`stem remediate`](docs/commands/remediate.md) | Planned — issue creation behaviour                      |
| [`stem serve`](docs/commands/serve.md)         | Flags, API endpoints, dev server setup                  |
| [`stem mcp`](docs/commands/mcp.md)             | MCP server configuration and coding-agent integration   |

---

## Setup and development

### Prerequisites

| Tool       | Required for       | Install                                                                                                    |
|------------|--------------------|------------------------------------------------------------------------------------------------------------|
| **uv**     | Python env & deps  | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js**| Frontend build only| [nodejs.org](https://nodejs.org/) (LTS recommended) — **not** needed at runtime                           |                                                          |

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

## Integrations

Stem is designed to sit within the **Microsoft developer ecosystem**, combining
GitHub, Azure, and Microsoft productivity tools into a unified improvement loop
for engineering teams.

| Integration                                                       | Signal provided                                    | Used by                    |
|-------------------------------------------------------------------|----------------------------------------------------|----------------------------|
| [GitHub Copilot SDK](https://github.com/github/copilot-sdk)      | AI-powered assessment & recommendations            | Core engine                |
| [GitHub API](https://docs.github.com/en/rest)                    | Repo structure, workflows, Copilot settings        | `stem assess`              |
| [Apache DevLake](https://devlake.apache.org/)                    | DORA metrics, PR statistics, CI/CD health          | `stem assess`              |
| [Work IQ](https://workiq.com/)                                   | Retrospective transcripts, team sentiment & themes | `stem remediate` (planned) |

### Copilot CLI SDK MCP configuration

The file [`stem/mcp.json`](src/stem/data/stem/mcp.json) configures which MCP
servers the **GitHub Copilot CLI SDK** has access to. Stem loads this file
dynamically at runtime so the assessment engine can call external MCP servers
(e.g. Microsoft Docs, Work IQ, Azure MCP) during `stem assess` runs. The
default configuration is bundled with Stem and copied into the instance
repository by `stem init`. Teams can customise their copy to add private MCP
servers or remove unused ones — see
[ADR-0007](docs/adr/adr-0007-externalized-mcp-server-configuration.md) for the
full design rationale.

### Microsoft ecosystem story

Stem leverages Microsoft products across the full assess-and-improve cycle:

```text
┌──────────────────────────────────────────────────────────────────────┐
│  GitHub Copilot SDK      AI engine powering assessments & reports    │
│  GitHub API / Actions    Data source + CI/CD automation target       │
│  Apache DevLake on Azure DORA & SDLC metrics at scale                │
│  Work IQ                 Qualitative team signals from retros        │
└──────────────────────────────────────────────────────────────────────┘
```

These products are **optional and composable** — Stem works with just a GitHub
token, but each additional integration enriches the picture.

### Apache DevLake on Azure

DevLake is an open-source dev data platform that computes DORA metrics, PR
statistics, CI/CD health, and issue tracking metrics from 15+ DevOps tools.
Stem delegates commodity metric computation to DevLake rather than
reimplementing it (see [ADR-0010](docs/adr/adr-0010-devlake-as-metric-backend.md)).

For teams running on Azure, DevLake can be deployed locally as Docker Compose, as an
[Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
service or via [Azure Kubernetes Service (AKS)](https://learn.microsoft.com/en-us/azure/aks/),
making it a managed part of the team's Azure infrastructure. 

Follow the [DevLake deployment guide](https://devlake.apache.org/docs/GettingStarted/QuickStart) 
to set up your instance, then point Stem at it through the following configuration in `stem.yaml`:

```yaml
# stem.yaml — point Stem at your Azure-hosted DevLake instance
devlake:
  enabled: true
  api_url: "http://localhost:8080"
  project_name: "my-team"
```

When no DevLake instance is configured, metric-dependent checks are
gracefully skipped and Stem continues to run structural and agentic maturity
checks using the GitHub API alone.

### Work IQ + Stem remediation workflow

Teams that run retrospectives through **Work IQ** can feed the meeting
transcript into a remediation cycle alongside Stem's assessment results.
Combining quantitative findings (assessment gaps, metric drift) with
qualitative team insights (pain points, root causes surfaced in the retro)
produces remediation proposals that reflect both *what* needs to change and
*why* the team believes it matters.

Planned workflow:

1. Run `stem assess <repo>` to produce an assessment report.
2. Export the retrospective transcript from Work IQ.
3. Run `stem remediate <repo>` with the transcript as additional context.
4. Stem creates GitHub issues that combine assessment findings with relevant
   retro themes, giving each issue richer context and team-informed priority.

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
