# Architecture

This document describes the high-level architecture of HVE Stem — the control
plane for agentic software development. It covers the layered model, component
responsibilities, data flows, and module boundaries.

For the full design narrative and assessment model, see
[NARRATIVE.md](NARRATIVE.md). For individual design decisions, see the
[ADRs](docs/adr/).

---

## Three-Layer Model

Stem operates within a three-layer model. Only Layer 1 is part of this project:

```mermaid
block-beta
    columns 1
    block:L1["Layer 1 — Stem (this application)"]
        l1["Control plane: bootstrap, govern, assess, observe, improve"]
    end
    block:L2["Layer 2 — Substrate"]
        l2["Agentic workflows & agents (GitHub Actions, Copilot, gh-aw)"]
    end
    block:L3["Layer 3 — Runtime"]
        l3["Where the software runs (Azure, any cloud / runtime)"]
    end

    L1 --> L2
    L2 --> L3

    style L1 fill:#dbeafe,stroke:#3b82f6
    style L2 fill:#fef3c7,stroke:#f59e0b
    style L3 fill:#e5e7eb,stroke:#6b7280
```

- **Layer 1 (Stem):** What we are building. Manages and improves Layers 2
  and 3 configurations.
- **Layer 2 (Substrate):** The agentic workflows running on GitHub. Stem
  configures and assesses these but does not replace them.
- **Layer 3 (Runtime):** The deployment target for software produced by the
  Layer 2 SDLC. Stem may read Layer 3 state to verify that Layer 2
  configured it correctly.

---

## Component Diagram

Stem exposes three interfaces — CLI, MCP server, and Web UI — all built on
top of a shared core engine:

```mermaid
graph TB
    subgraph Interfaces
        CLI["CLI<br/><code>stem &lt;command&gt;</code>"]
        MCP["MCP Server<br/><code>stem mcp</code>"]
        WEB["Web UI<br/><code>stem serve</code>"]
    end

    subgraph Core["Shared Core"]
        ENGINE["Assessment Engine<br/><code>engine.py</code>"]
        SESSION["Copilot SDK Session<br/><code>session.py</code>"]
        WS["Workspace Discovery<br/><code>workspace.py</code>"]
    end

    subgraph External["External Services"]
        COPILOT["GitHub Copilot<br/>(via Copilot SDK)"]
        MCPEXT["External MCP Servers<br/>(GitHub, Docs, etc.)"]
        GH["GitHub API"]
    end

    subgraph State["Instance Repository (Git)"]
        direction TB
        YAML["stem.yaml"]
        BP["Blueprints"]
        AGENTS["Agent Definitions"]
        MCP_JSON["mcp.json"]
        REPORTS["Assessment Reports"]
        REMED["Remediation State"]
    end

    CLI --> ENGINE
    MCP --> ENGINE
    WEB -->|"FastAPI + SSE"| ENGINE
    ENGINE --> SESSION
    ENGINE --> WS
    SESSION --> COPILOT
    SESSION --> GH
    WS --> State
    COPILOT --> MCPEXT
    COPILOT --> MCP_JSON
    YAML ~~~ BP
    BP ~~~ AGENTS
    AGENTS ~~~ MCP_JSON
    MCP_JSON ~~~ REPORTS
    REPORTS ~~~ REMED

    style Interfaces fill:#dbeafe,stroke:#3b82f6
    style Core fill:#dcfce7,stroke:#22c55e
    style External fill:#fef3c7,stroke:#f59e0b
    style State fill:#f3e8ff,stroke:#a855f7
```

---

## Module Map

All Python source lives under `src/stem/`:

| Module               | Responsibility                                                                   |
|----------------------|----------------------------------------------------------------------------------|
| `cli.py`             | Typer application entry point; workspace initialisation; command registration     |
| `engine.py`          | Shared assessment engine — the single implementation that CLI, MCP, and web call |
| `session.py`         | Copilot SDK session management — creates sessions, loads MCP configs, runs agent |
| `workspace.py`       | Discovers skills, agents, targets, and other artefacts from the instance repo    |
| `commands/init.py`   | `stem init` — scaffolds a new instance repository with blueprints and config     |
| `commands/assess.py` | `stem assess` — CLI wrapper around the engine with Rich progress output          |
| `commands/serve.py`  | `stem serve` — FastAPI app with REST + SSE endpoints, serves the React SPA       |
| `commands/mcp.py`    | `stem mcp` — MCP server exposing `assess_repo` tool for coding agents            |

---

## Assessment Pipeline

The `stem assess` command triggers a multi-step pipeline that evaluates a
repository against the desired SDLC blueprint:

```mermaid
flowchart LR
    A["<b>Trigger</b><br/>CLI / MCP / Web UI"] --> B["<b>Load Workspace</b><br/>Parse stem.yaml,<br/>discover agents & MCP config"]
    B --> C["<b>Create Copilot Session</b><br/>Connect to Copilot SDK<br/>with MCP servers"]
    C --> D["<b>Agent Execution</b><br/>Assessor agent inspects repo<br/>via GitHub + MCP tools"]
    D --> E["<b>Generate Report</b><br/>Markdown assessment with<br/>dimension scores & findings"]
    E --> F["<b>Deliver Result</b><br/>CLI: Rich output<br/>Web: SSE stream<br/>MCP: tool response"]
```

### Step-by-step

1. **Trigger:** The user invokes `stem assess owner/repo` via CLI, the Web UI
   assess form, or the `assess_repo` MCP tool.
2. **Load workspace:** The `Workspace` is loaded from the instance repository,
   parsing `stem.yaml` for targets/config and discovering agent files and MCP
   server configuration.
3. **Create Copilot session:** A `CopilotClient` session is created via the
   Copilot SDK with the configured model (default: `claude-sonnet-4.6`) and
   external MCP servers (GitHub, Microsoft Docs, etc.).
4. **Agent execution:** The assessor agent receives a prompt to evaluate the
   target repository. It uses MCP tools to inspect repo contents, workflows,
   configuration files, and community health files.
5. **Generate report:** The agent produces a comprehensive Markdown assessment
   covering delivery performance, code health, collaboration, agentic maturity,
   and governance compliance.
6. **Deliver result:** The report is returned to the originating interface —
   Rich console output for CLI, SSE-streamed events for Web UI, or a direct
   tool response for MCP.

---

## Remediation Pipeline

Assessment findings feed into the remediation pipeline, which creates
actionable GitHub issues on target repositories:

```mermaid
flowchart TB
    A["<b>stem remediate owner/repo</b>"] --> B["Read latest assessment<br/>from reports/"]
    B --> C["Extract actionable findings<br/>(🔴 Missing / 🟡 Basic)"]
    C --> D{Already tracked in<br/>remediation state?}
    D -->|Yes| E["Skip"]
    D -->|No| F["Generate contextual<br/>GitHub issue via<br/>Copilot SDK agent"]
    F --> G["Create issue on<br/>target repository"]
    G --> H["Record issue URL &<br/>finding ID in<br/>remediation/issues.yaml"]
    H --> I["Commit updated state<br/>to instance repo"]
```

Key properties:

- **Idempotent** — re-running does not create duplicate issues.
- **Contextual** — issues reference actual file paths and configurations.
- **Tracked** — remediation state in `remediation/<owner>/<repo>/issues.yaml`
  links findings to GitHub issues.

---

## Request Lifecycle

All three interfaces share the same core path. The differences are only in how
the request enters and how the result is delivered:

```mermaid
sequenceDiagram
    participant User
    participant Interface as CLI / MCP / Web UI
    participant Engine as engine.py
    participant Session as session.py
    participant Copilot as Copilot SDK
    participant MCP_Ext as External MCP Servers
    participant GitHub as GitHub API

    User->>Interface: stem assess owner/repo
    Interface->>Engine: run_assessment(repo, ws, model)
    Engine->>Session: run_agent(prompt, system_message, ...)
    Session->>Copilot: create_session(model, MCP servers)
    Copilot->>MCP_Ext: Tool calls (GitHub, Docs, ...)
    MCP_Ext->>GitHub: API requests (repo content, workflows, ...)
    GitHub-->>MCP_Ext: Repository data
    MCP_Ext-->>Copilot: Tool results
    Copilot-->>Session: Assessment report (Markdown)
    Session-->>Engine: Report text
    Engine-->>Interface: Report + events
    Interface-->>User: Formatted output
```

---

## SSE Streaming (Web UI)

The Web UI uses Server-Sent Events to stream real-time progress from the
FastAPI backend to the React frontend:

```mermaid
sequenceDiagram
    participant Browser as React App
    participant FastAPI as FastAPI Backend
    participant Engine as Assessment Engine
    participant Copilot as Copilot SDK

    Browser->>FastAPI: POST /api/assess?repo=owner/repo
    FastAPI-->>Browser: { job_id: "uuid" }
    FastAPI->>Engine: asyncio.create_task(run_assessment)

    Browser->>FastAPI: GET /api/assess/{job_id}/stream
    Note over Browser,FastAPI: SSE connection opened

    loop During assessment
        Engine->>FastAPI: on_event(AssessEvent)
        FastAPI-->>Browser: data: {"type":"status","message":"..."}
        Engine->>Copilot: Agent tool calls
        Copilot-->>Engine: Tool results
        Engine->>FastAPI: on_event(AssessEvent)
        FastAPI-->>Browser: data: {"type":"tool","tool":"..."}
    end

    Engine-->>FastAPI: Assessment complete
    FastAPI-->>Browser: data: {"type":"done","result":"# Report..."}
    Note over Browser,FastAPI: SSE connection closed
```

### Frontend architecture

The React frontend (in `app/`) is built with Vite and uses the GitHub Primer
design system:

| Directory            | Contents                                                    |
|----------------------|-------------------------------------------------------------|
| `app/src/pages/`     | Route-level components — `AssessPage`, `RemediatePage`      |
| `app/src/components/`| Shared UI — `AppHeader`, `EventLog`, `MarkdownReport`      |
| `app/src/api/`       | API client (`client.ts`), SSE hook (`useAssess.ts`), types  |

The `useAssess` React hook encapsulates the full assess flow: it calls
`POST /api/assess` to start a job, then opens an `EventSource` on
`/api/assess/{jobId}/stream` to receive real-time events until the
assessment completes.

---

## Init / Bootstrap Flow

`stem init` scaffolds a new instance repository with the directory structure,
configuration, and default blueprints that Stem needs to operate:

```mermaid
flowchart LR
    A["<b>stem init</b>"] --> B["Create directory<br/>structure"]
    B --> C["Copy default<br/>blueprints"]
    C --> D["Copy agent<br/>definitions"]
    D --> E["Copy MCP<br/>configuration"]
    E --> F["Render<br/>stem.yaml"]
    F --> G["Generate<br/>README.md"]
    G --> H["git init +<br/>initial commit"]
```

The resulting instance repository structure:

```text
my-stem/
├── stem.yaml                    # Instance configuration (targets, scoring)
├── README.md                    # Generated README
├── stem/
│   ├── mcp.json                 # MCP server configuration
│   └── agents/
│       └── assessor.agent.md    # Assessment agent system prompt
├── blueprints/
│   └── default.md               # Default SDLC blueprint
├── reports/                     # Assessment reports (populated by stem assess)
├── remediation/                 # Remediation state (populated by stem remediate)
└── .github/
    ├── agents/                  # Custom agent definitions
    ├── skills/                  # Copilot skills
    └── prompts/                 # Reusable prompts
```

---

## Blueprint & Policy Resolution

Blueprints define the desired SDLC state for target repositories. During
assessment, the engine compares the actual repository state against the
blueprint's expectations:

```mermaid
flowchart TB
    subgraph Sources["Blueprint Sources"]
        DEFAULT["Default blueprint<br/>(bundled with Stem)"]
        CUSTOM["Custom blueprints<br/>(instance repo)"]
        REMOTE["Remote blueprints<br/>(Git URL — future)"]
    end

    subgraph Resolution["Resolution"]
        LOAD["Load blueprint<br/>from stem.yaml config"]
        MERGE["Merge with<br/>scoring thresholds"]
    end

    subgraph Assessment["Assessment"]
        COMPARE["Compare repo state<br/>vs. blueprint checks"]
        SCORE["Score per dimension<br/>(0–100 + traffic light)"]
        REPORT["Generate report<br/>with findings"]
    end

    DEFAULT --> LOAD
    CUSTOM --> LOAD
    REMOTE -.-> LOAD
    LOAD --> MERGE
    MERGE --> COMPARE
    COMPARE --> SCORE
    SCORE --> REPORT

    style Sources fill:#f3e8ff,stroke:#a855f7
    style Resolution fill:#fef3c7,stroke:#f59e0b
    style Assessment fill:#dcfce7,stroke:#22c55e
```

Blueprint sourcing follows [ADR-0006](docs/adr/adr-0006-blueprint-sourcing-strategy.md):
blueprints are copied into the instance repo at `stem init` time. Future
versions may support pulling blueprints from a remote Git repository.

---

## Scoring & Aggregation

Assessment results roll up from individual checks to a portfolio-level view:

```mermaid
flowchart TB
    CHECKS["Individual checks<br/>(pass/fail or 0–100)"]
    DIM["Dimension scores<br/>(0–100 + traffic light)"]
    REPO["Repository score<br/>(0–100 + traffic light)"]
    PORT["Portfolio dashboard<br/>(heatmap: repos × dimensions)"]

    CHECKS -->|"aggregate per dimension"| DIM
    DIM -->|"aggregate per repo"| REPO
    REPO -->|"aggregate across portfolio"| PORT
```

Traffic-light thresholds (configurable per blueprint):

| Colour | Meaning                                               | Default |
|--------|-------------------------------------------------------|---------|
| 🟢     | Healthy — meets or exceeds blueprint expectations     | ≥ 80%   |
| 🟡     | Needs attention — partial compliance or degrading     | 50–79%  |
| 🔴     | Action required — significant gaps or violations      | < 50%   |

---

## Assessment Dimensions

The assessment model organises checks into five dimensions, each grounded in
established research frameworks:

```mermaid
mindmap
  root((Assessment<br/>Model))
    Delivery Performance
      DORA metrics
      Deployment frequency
      Change lead time
      Change fail rate
      CI pipeline health
    Code & Repo Health
      Test automation
      Dependency freshness
      Security scanning
      Documentation
      Branch protection
    Collaboration & Process
      PR review turnaround
      PR size guidelines
      Issue triage time
      Templates & guides
    Agentic Maturity
      Copilot enablement
      Agentic workflows
      AI code review
      Agent instructions
      MCP configuration
    Governance & Compliance
      Blueprint drift
      Required workflows
      Branch protection policy
      License compliance
```

| Dimension                      | Framework basis                | Stem-specific?   |
|--------------------------------|--------------------------------|------------------|
| Delivery Performance           | DORA                           | No               |
| Code & Repo Health             | SPACE (Performance) + DevEx    | No               |
| Collaboration & Process        | SPACE (Communication) + DevEx  | No               |
| Agentic Maturity               | —                              | **Yes** (unique) |
| Governance & Policy Compliance | —                              | **Yes** (unique) |

---

## Technology Stack

| Layer        | Technology                                                          |
|--------------|---------------------------------------------------------------------|
| **Language** | Python 3.12, TypeScript                                             |
| **CLI**      | Typer + Rich                                                        |
| **AI**       | GitHub Copilot SDK                                                  |
| **Backend**  | FastAPI + Uvicorn                                                   |
| **Frontend** | React 19, Primer Design System (`@primer/react`), Vite              |
| **MCP**      | `mcp` Python SDK (`FastMCP`)                                        |
| **Testing**  | pytest, mypy, Vitest, React Testing Library                         |
| **Linting**  | Ruff (format + lint)                                                |
| **Build**    | hatchling (Python), Vite (frontend)                                 |
| **CI/CD**    | GitHub Actions                                                      |
