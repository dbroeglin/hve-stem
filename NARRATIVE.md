# HVE Stem — Seed Document

## What is Stem?

**Stem is a control plane for agentic software development.** It sits above the actual agentic workflows and developer tools, providing a single surface to **bootstrap, govern, assess, and continuously improve** how a team's agentic SDLC operates — across one or many repositories.

### The problem

Teams adopting agentic development (AI-assisted code review, automated issue triage, agentic CI/CD) face fragmentation: capabilities are scattered across tools (Copilot, Actions, gh-aw), there's no unified view of maturity or health, and no systematic way to enforce policies or improve over time.

### What Stem does

Stem is the answer to: *"How mature is our agentic SDLC, what should we improve next, and how do we enforce our standards?"*

| Concern | What Stem provides |
|---|---|
| **Bootstrapping** | Scaffold new repos or onboard existing ones with opinionated-but-customizable SDLC blueprints (agentic workflows, CI/CD, policies) |
| **Governance** | Define and enforce policies, guardrails, and instructions that constrain what agents can do across repos |
| **Assessment** | Evaluate SDLC maturity, code/repo health, and drift from desired blueprints — per repo or across an org |
| **Observability** | Surface how the agentic SDLC is performing (quality signals, pipeline health, policy compliance) |
| **Continuous Improvement** | Learn from assessment outcomes and iteratively refine agent configurations, prompts, and workflows |

### Primary user

**Team leads and DevOps engineers** who are responsible for setting up and governing agentic workflows for their team or organization.

### Scope

Stem operates at the **organization / multi-repo level**. It manages a portfolio of repositories, each with their own SDLC configuration, while enforcing org-wide policies and tracking maturity across the portfolio.

---

## Architecture — Three Layers

```
┌─────────────────────────────────────────────────┐
│  Layer 1: Stem (this application)               │
│  Control plane — bootstrap, govern, assess,     │
│  observe, improve the agentic SDLC              │
├─────────────────────────────────────────────────┤
│  Layer 2: Substrate (NOT part of this app)       │
│  The agentic workflows and agents themselves     │
│  (GitHub Actions, Copilot, gh-aw, etc.)          │
├─────────────────────────────────────────────────┤
│  Layer 3: Runtime (NOT part of this app)         │
│  Where the software built through Layer 2 runs   │
│  (Azure, or any other cloud/runtime)             │
└─────────────────────────────────────────────────┘
```

- **Layer 1 (Stem):** What we are building. Manages and improves Layers 2 and 3 configurations.
- **Layer 2 (Substrate):** The agentic workflows running on GitHub. Stem configures and assesses these but does not replace them. GitHub-first, with an abstraction layer for future extensibility to other platforms.
- **Layer 3 (Runtime):** The deployment target for software produced by the Layer 2 SDLC. Azure for now; designed to be runtime-agnostic.

---

## Stem State & Storage

Stem persists its state in **Markdown files** (human-readable, version-controllable). Three categories of state:

| Category | Purpose | Examples |
|---|---|---|
| **Connection config** | How Stem accesses and interacts with Layer 2 repos/orgs | Org/repo targets, auth references, API endpoints |
| **Policies & instructions** | The rules and guardrails Stem enforces on Layer 2 | Approval policies, agent permissions, required workflows, blueprint definitions |
| **Reports & audit trail** | Historical assessment results and change logs | Maturity scores over time, drift reports, remediation history |

---

## CLI Commands

Stem exposes both a **CLI** (primary interface) and a **Web UI** (visual dashboard). It also surfaces as an **MCP server** for use from coding agents.

| Command | Purpose |
|---|---|
| `stem init` | Bootstrap a new project or onboard an existing repo with a Stem-managed SDLC blueprint. Sets up the necessary config files and directory structure within a Git repository. |
| `stem assess` | Evaluate one or more repos against the desired SDLC blueprint. Reports on: **SDLC maturity** (which agentic capabilities are configured), **code/repo health** (test coverage, dependency freshness, security posture), and **drift detection** (current state vs. desired blueprint). |
| `stem serve` | Launch the web UI locally for a visual dashboard experience. |
| `stem mcp` | Start an MCP server so Stem can be driven from coding agents (GitHub Copilot, Claude Code, etc.). |

### Blueprints

Stem ships with **opinionated default blueprints** (e.g., "Python microservice with full agentic CI/CD") that are **fully customizable**. Blueprints define:

- Which agentic workflows should be present
- Required GitHub Actions / CI/CD pipelines
- Agent configurations and permissions
- Policy and guardrail settings
- Expected repo structure conventions

---

## Tech Stack

### Python CLI

| Tool | Role |
|---|---|
| **UV** | Python package/project management |
| **Typer** | CLI framework |
| **Rich** | Terminal output formatting |
| **GitHub Copilot CLI SDK** | Integration with GitHub Copilot agent capabilities |
| **GitHub MCP** | Connect to GitHub from agents |
| **WorkIQ MCP** | Additional MCP integration |
| **GitHub API (PyGithub / httpx)** | Direct GitHub API access when MCP is not needed |
| **Black & mypy** | Code formatting and type checking |
| **pytest** | Testing framework |

### Web UI / API

| Tool | Role |
|---|---|
| **FastAPI** | Backend API for the web UI |
| **Next.js** | Frontend web application |
| **FastMCP** | MCP server implementation (for `stem mcp`) |

### Developer Experience

- **Codespaces** — ready-to-code dev environment
- **Architecture Decision Records (ADRs)** — document key design choices
- **Spec-driven development** — TBD: define interfaces and contracts before implementation

---

## Layer 2: Substrate (reference, not built here)

Starting points and references for the agentic workflows Stem will manage:

- [OctoCat Supply](https://github.com/msft-common-demos/octocat_supply-obscure-umbrella) — existing demo to reuse as a sample Layer 2 target
- [Agentic Workflows (gh-aw)](https://github.com/github/gh-aw) — see [documentation](https://github.github.com/gh-aw/)

---

## Layer 3: Runtime (reference, not built here)

- **Azure** is the initial target runtime
- Designed to be runtime-agnostic — any platform where Layer 2 can deploy applications

---

## Open Questions

- [ ] What does the blueprint file format look like? (YAML, TOML, Markdown with front matter?)
- [ ] How does Stem authenticate across multiple repos/orgs? (GitHub App, PAT, OAuth?)
- [ ] What is the assessment scoring model? (Numeric maturity score, checklist, traffic lights?)
- [ ] How does continuous improvement feed back into blueprints? (Auto-PR, suggestion reports, manual review?)
- [ ] What is the relationship between `stem mcp` and the CLI — same capabilities or subset?
- [ ] How are policies versioned and propagated across repos?