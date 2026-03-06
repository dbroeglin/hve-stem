# HVE Stem — Seed Document

## What is Stem?

**Stem is a control plane for agentic software development.** It sits above the actual agentic workflows and developer tools, providing a single surface to **bootstrap, govern, assess, and continuously improve** how a team's agentic SDLC operates — across one or many repositories.

### The problem

Teams adopting agentic development (AI-assisted code review, automated issue triage, agentic CI/CD) face fragmentation: capabilities are scattered across tools (Copilot, Actions, gh-aw), there's no unified view of maturity or health, and no systematic way to enforce policies or improve over time.

### What Stem does

Stem is the answer to: *"How mature is our agentic SDLC, what should we improve next, and how do we enforce our standards?"*

| Concern                    | What Stem provides                                                                                                               |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| **Bootstrapping**          | Scaffold new repos or onboard existing ones with opinionated-but-customizable SDLC blueprints (agentic workflows, CI/CD, policies) |
| **Governance**             | Define and enforce policies, guardrails, and instructions that constrain what agents can do across repos                         |
| **Assessment**             | Evaluate SDLC maturity, code/repo health, and drift from desired blueprints — per repo or across an org                          |
| **Observability**          | Surface how the agentic SDLC is performing (quality signals, pipeline health, policy compliance)                                 |
| **Continuous Improvement** | Learn from assessment outcomes and iteratively refine agent configurations, prompts, and workflows                               |

### Primary user

**Team leads and DevOps engineers** who are responsible for setting up and governing agentic workflows for their team or organization.

### Operating model

Stem operates at the **organization / multi-repo level**. It manages a portfolio of repositories, each with their own SDLC configuration, while enforcing org-wide policies and tracking maturity across the portfolio.

Stem follows a **passive assessment + active recommendation** model:

1. **Bootstrapping (MVP):** Generate an initial SDLC configuration for a new repository.
2. **Assessment (MVP):** For existing repositories, Stem does *not* automatically overwrite configurations. It assesses current state vs. blueprint and records findings in the Stem instance repository.
3. **Remediation (MVP):** Open issues on target (Layer 2) repositories with drift details, implementation guidance, and a remediation plan.
4. **Remediation (Future):** Optionally generate pull requests to remediate drift automatically.

---

## Architecture — Three Layers

```text
┌─────────────────────────────────────────────────┐
│  Layer 1: Stem (this application)               │
│  Control plane — bootstrap, govern, assess,     │
│  observe, improve the agentic SDLC              │
├─────────────────────────────────────────────────┤
│  Layer 2: Substrate (NOT part of this app)      │
│  The agentic workflows and agents themselves    │
│  (GitHub Actions, Copilot, gh-aw, etc.)         │
├─────────────────────────────────────────────────┤
│  Layer 3: Runtime (NOT part of this app)        │
│  Where the software built through Layer 2 runs  │
│  (Azure, or any other cloud/runtime)            │
└─────────────────────────────────────────────────┘
```

- **Layer 1 (Stem):** What we are building. Manages and improves Layers 2 and 3 configurations.
- **Layer 2 (Substrate):** The agentic workflows running on GitHub. Stem configures and assesses these but does not replace them. GitHub-first, with an abstraction layer for future extensibility to other platforms. Layer 2 is responsible for setting up all elements of proper observability, monitoring, and governance for the application deployed in Layer 3. Agentic capabilities within this layer are implemented through the **[GitHub Copilot SDK](https://github.com/github/copilot-sdk)**, which provides the programmatic interface for interacting with GitHub Copilot's agent capabilities (code assistance, code review, issue triage, etc.).
- **Layer 3 (Runtime):** The deployment target for software produced by the Layer 2 SDLC. Azure for now; designed to be runtime-agnostic. Stem is *not* part of the normal monitoring and observability of Layer 3. However, Stem may access Layer 3 (in a read-only capacity) solely for the purpose of verifying that Layer 2 successfully configured the runtime environment as expected.

---

## Stem State & Storage

All Stem state lives in a **Git repository** — human-readable, version-controllable, diffable. **No binary files.**

### File formats

| Format | Used for | Examples |
| --- | --- | --- |
| **Markdown** (primary) | Blueprints, policies, instructions, narrative docs, assessment reports | `blueprints/python-microservice.md`, `policies/code-review.md`, `reports/2026-02-assess.md` |
| **Markdown + frontmatter** | Linking related documents, adding metadata | YAML frontmatter for tags, relationships, timestamps |
| **YAML** | Structured configuration, data-heavy settings | `stem.yaml` (project config, repo inventory), workflow definitions |
| **JSON / CSV** | Tabular data, machine-readable exports | Assessment score history, metric exports |

### State categories

| Category | Purpose | Examples |
| --- | --- | --- |
| **Connection config** | How Stem accesses and interacts with Layer 2 repos/orgs | Org/repo targets, API endpoints (authentication is external; see Authentication below) |
| **Policies & instructions** | The rules and guardrails Stem enforces on Layer 2 | Approval policies, agent permissions, required workflows, blueprint definitions |
| **Reports & audit trail** | Historical assessment results and change logs | Maturity scores over time, drift reports, remediation history |

### Versioning

There are two levels of versioning, both using **Git**:

| Repo | What it is | How it's versioned |
| --- | --- | --- |
| **`hve-stem`** (this repo) | The Stem tool itself — CLI code, default blueprints, default policies | Git tags and releases. This is the **upstream source of truth**. Updates to blueprints, policies, and tool code ship as new versions. |
| **Stem instance repos** (created via `stem init`) | Individual control-plane repos for a team/org | Each is its own Git repo with its own commit history. Blueprints and policies are copied/rendered at `stem init` time. |

Updates flow **downstream** from `hve-stem` to instance repos via pull requests — keeping the process simple, auditable, and version-controlled.

---

## Authentication

**No secrets are stored in Git.** Stem needs access to Layer 2 (GitHub Enterprise/Organization) and optionally Layer 3 (runtime environments), but credentials stay outside the repository and are resolved at runtime.

Authentication is resolved at runtime through one of the following mechanisms (in priority order):

| Mechanism | When to use |
| --- | --- |
| **`gh` CLI auth** | Default for local development. If the user is authenticated via `gh auth login`, Stem piggybacks on that session. Zero config needed. |
| **Environment variables** | CI/CD and automation. `GITHUB_TOKEN` or `STEM_GITHUB_TOKEN` for GitHub access; similar patterns for runtime credentials. |
| **GitHub App** | Org-level deployments. A GitHub App installation provides scoped, rotatable tokens across multiple repos without personal credentials. |
| **Keyring / OS credential store** | Optional. Stem can read tokens from the OS keychain (via Python `keyring`) for users who prefer not to use env vars or `gh`. |

The Stem config files (e.g., `stem.yaml`) reference *what* to connect to (org name, repo list, API endpoints) but never *how* to authenticate — that is always resolved from the environment at runtime.

---

## Interfaces & Commands

Stem exposes **three interfaces** with shared core capabilities:

| Interface | Surface | How it's started |
| --- | --- | --- |
| **CLI** | Terminal commands | `stem <command>` |
| **MCP server** | Coding agents (GitHub Copilot, Claude Code, etc.) | `stem mcp` |
| **Web UI** | Browser-based visual dashboard | `stem serve` |

**Agentic implementation:** All agentic capabilities (workflow automation) are implemented through the **[GitHub Copilot CLI SDK](https://github.com/github/copilot-sdk)**. The SDK provides the core integration layer between Stem and GitHub Copilot's agent platform, enabling Stem to programmatically configure, invoke, and govern Copilot-powered workflows across target repositories.

**Parity principle:** All three interfaces expose the same capabilities. A user should be able to `init`, `assess`, or any other Stem operation from the CLI, from a coding agent via MCP, or from the Web UI. If a capability is CLI-only, there must be a documented reason (e.g., interactive terminal prompts that have no MCP/Web equivalent). The CLI is the reference implementation — MCP and Web UI are built on top of the same core logic.

Supported commands (invoked via CLI and available through parity across MCP/Web where applicable):

| Command | Purpose |
| --- | --- |
| `stem init` | Bootstrap a new project or onboard an existing repo with a Stem-managed SDLC blueprint. Sets up the necessary config files and directory structure within a Git repository. |
| `stem assess`     | Evaluate one or more repos against the desired SDLC blueprint. Reports on: **SDLC maturity** (which agentic capabilities are configured), **code/repo health** (test coverage, dependency freshness, security posture), and **drift detection** (current state vs. desired blueprint). |
| `stem remediate`  | Read assessment findings and create GitHub issues on the target repository for each finding, with contextual fix suggestions. Tracks created issues locally to avoid duplicates on re-runs. |
| `stem serve`      | Launch the web UI locally for a visual dashboard experience. |
| `stem mcp`        | Start an MCP server so Stem can be driven from coding agents (GitHub Copilot, Claude Code, etc.). |

---

## Assessment Model

Stem's assessment is **checklist-based**: individual yes/no or scored checks, grouped into dimensions, aggregated into numeric scores and traffic-light indicators (green / amber / red) per repo and across the portfolio.

### Design principles

- **Don't reinvent the wheel.** Ground checks in established research frameworks: DORA, SPACE, and DevEx.
- **Extend for agentic.** None of these frameworks explicitly cover agentic SDLC maturity — Stem adds a dedicated dimension for this.
- **Checklist first, scores second.** Each check is a concrete, actionable item. Scores and traffic lights are roll-ups for dashboards, not the primary artifact.
- **Data from the repo.** Stem gathers data through repo config/content inspection (`.github/`, workflows, READMEs, agent configs) and GitHub API metrics (PR stats, Actions runs, Copilot usage). No surveys in v1.
- **Graceful degradation.** If specific APIs (like Copilot Metrics) or conventions (like DORA incident labels) are unavailable, Stem documents the missing access/data rather than failing. If conventions are missing, Stem provides an opinionated way to set them up.

### Theoretical backbone

| Framework | Focus | How Stem uses it |
| --- | --- | --- |
| **[DORA](https://dora.dev/guides/dora-metrics-four-keys/)** | Software delivery performance: throughput (change lead time, deployment frequency, failed deployment recovery time) and stability (change fail rate, deployment rework rate) | Map delivery-related checks to DORA's five metrics. Use as the benchmark for "is the pipeline healthy?" |
| **[SPACE](https://queue.acm.org/detail.cfm?id=3454124)** | Developer productivity across 5 dimensions: Satisfaction, Performance, Activity, Communication & Collaboration, Efficiency & Flow | Organize repo/team-level checks into SPACE categories. Ensures Stem doesn't over-index on activity metrics alone. |
| **[DevEx](https://queue.acm.org/detail.cfm?id=3595878)** | Developer experience through: feedback loops, cognitive load, flow state | Inform checks about developer-facing friction: CI speed, documentation quality, onboarding ease |
| **Agentic Maturity** *(Stem-specific)* | How fully and effectively agentic capabilities are adopted in the SDLC | New dimension — no existing framework covers this. See below. |

### Assessment dimensions

Stem organizes its checklist into **five assessment dimensions**. Each dimension contains concrete checks that are evaluated per repository.

#### 1. Delivery Performance (grounded in DORA)

Measures the health and speed of the software delivery pipeline.

| Check | Data source | Maps to |
| --- | --- | --- |
| Deployment frequency meets target | GitHub API (deployments/releases) | DORA: Deployment Frequency |
| Change lead time within threshold | GitHub API (commit-to-deploy time) | DORA: Change Lead Time |
| Failed deployment recovery time acceptable | GitHub API (incident/hotfix PRs) | DORA: Failed Deployment Recovery Time |
| Change fail rate below threshold | GitHub API (rollback/hotfix ratio) | DORA: Change Fail Rate |
| CI pipeline exists and passes | Repo inspection (`.github/workflows/`) | DORA: Continuous Integration |

#### 2. Code & Repo Health (grounded in SPACE: Performance + DevEx: Cognitive Load)

Measures the structural quality and maintainability of the codebase.

| Check | Data source | Maps to |
| --- | --- | --- |
| Test automation present and configured | Repo inspection (test directories, CI test steps) | SPACE: Performance |
| Dependency freshness (no critical outdated deps) | Repo inspection (lockfiles) + Dependabot alerts | SPACE: Performance |
| Security scanning enabled (CodeQL, secret scanning) | Repo inspection + GitHub API | DORA capability: Pervasive Security |
| README and documentation exist and are current | Repo content inspection | DevEx: Cognitive Load |
| Branch protection rules configured | GitHub API (branch protection settings) | DORA capability: Streamlining Change Approval |
| Code owners defined | Repo inspection (`CODEOWNERS`) | SPACE: Communication & Collaboration |

#### 3. Collaboration & Process (grounded in SPACE: Communication + DevEx: Feedback Loops)

Measures how well team processes support collaboration and fast feedback.

| Check | Data source | Maps to |
| --- | --- | --- |
| PR review turnaround within threshold | GitHub API (PR review times) | SPACE: Efficiency & Flow |
| PR size within guidelines (small batches) | GitHub API (PR diff stats) | DORA capability: Working in Small Batches |
| Issue triage time within threshold | GitHub API (issue response times) | SPACE: Communication |
| Templates exist for PRs and issues | Repo inspection (`.github/ISSUE_TEMPLATE/`, etc.) | DevEx: Cognitive Load |
| Contributing guide present | Repo inspection (`CONTRIBUTING.md`) | DevEx: Feedback Loops |

#### 4. Agentic Maturity (Stem-specific)

Measures how fully and effectively agentic capabilities are adopted in the SDLC. **This dimension has no external framework equivalent — it is Stem's unique contribution.**

| Check | Data source | Maps to |
| --- | --- | --- |
| GitHub Copilot enabled for the repo/org | GitHub API (Copilot settings) | Agentic: Code assistance |
| Copilot usage metrics above adoption threshold | GitHub API (Copilot metrics) | Agentic: Code assistance |
| Agentic workflows configured (gh-aw) | Repo inspection (`.github/` agentic config) | Agentic: Workflow automation |
| AI-powered code review enabled | Repo inspection (Copilot PR review config) | Agentic: Code review |
| AI-assisted issue triage configured | Repo inspection (issue automation config) | Agentic: Issue management |
| Agent instructions/guardrails defined | Repo inspection (`.github/copilot-instructions.md`, policy files) | Agentic: Governance |
| Agentic CI/CD steps present | Repo inspection (workflow files for AI-driven steps) | Agentic: Pipeline automation |
| MCP server configuration present | Repo inspection (MCP config files) | Agentic: Tool integration |

#### 5. Governance & Policy Compliance (Stem-specific enforcement)

Measures adherence to org-wide policies defined in Stem blueprints.

| Check | Data source | Maps to |
| --- | --- | --- |
| Repo matches assigned blueprint | Repo inspection vs. blueprint definition | Stem: Drift detection |
| Required workflows present and unmodified | Repo inspection vs. blueprint | Stem: Policy compliance |
| Required branch protection matches policy | GitHub API vs. policy definition | Stem: Policy compliance |
| License file present and correct | Repo inspection | Org policy |
| Required labels/issue types configured | GitHub API (labels, issue types) | Org policy |

### Scoring and aggregation

```text
Individual checks (pass/fail or 0–100)
    ↓ aggregate per dimension
Dimension scores (0–100 numeric + traffic light)
    ↓ aggregate per repo
Repo score (0–100 numeric + traffic light)
    ↓ aggregate across portfolio
Portfolio dashboard (heatmap of repos × dimensions)
```

**Traffic-light thresholds** (configurable per blueprint):

| Color | Meaning | Default threshold |
| --- | --- | --- |
| Green | Healthy — meets or exceeds blueprint expectations | ≥ 80% |
| Amber | Needs attention — partial compliance or degrading trend | 50–79% |
| Red | Action required — significant gaps or policy violations | < 50% |

### Assessment output

`stem assess` produces:

1. **Per-repo checklist** — every check with pass/fail, current value, and target (Markdown report)
2. **Dimension summary** — score + traffic light per dimension (table in report + dashboard)
3. **Portfolio heatmap** — repos as rows, dimensions as columns, traffic-light colors (Web UI + CSV export)
4. **Drift report** — specific deviations from the assigned blueprint, with remediation suggestions
5. **Trend data** — scores over time stored in `reports/` for historical comparison

**Automation & State Lifecycle:**
When `stem assess` runs, it **automatically commits** the resulting Markdown and CSV reports back to the Stem instance Git repository with a clear, structured commit message (e.g., `chore(assess): update assessment for repo-x [2026-02-27]`). This default behavior ensures a traceable history of SDLC maturity and can be made configurable per blueprint or instance policy as the product evolves. The primary MVP use case is local CLI execution, but it is designed to run on a schedule via GitHub Actions.

---

## Remediation Model

Remediation is the bridge between assessment and action. Where `stem assess` identifies gaps, `stem remediate` turns those findings into trackable work items on the target repository — giving developers clear, contextual guidance on what to fix and how.

### Design principles

- **Idempotent.** Running `stem remediate` multiple times against the same assessment must not create duplicate issues. Stem tracks which findings have already been filed and skips them.
- **Contextual suggestions.** Issues are not generic checklists — they include concrete guidance tailored to the target repository (e.g., "add a `ruff.toml` at the repo root" rather than "configure a linter").
- **Minimal noise.** Only actionable findings produce issues. Informational or already-passing checks are omitted.
- **Agentic authoring.** Issue bodies are generated by the same Copilot SDK agent that performed the assessment, so they can reference actual file paths, workflow names, and configuration snippets found in the repo.

### How it works

```text
stem assess repo-x          stem remediate repo-x
      │                              │
      ▼                              ▼
┌──────────────┐            ┌──────────────────┐
│  Assessment  │───────────▶│  Read latest     │
│  report      │            │  assessment for  │
│  (Markdown)  │            │  repo-x          │
└──────────────┘            └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │  For each finding │
                            │  with status      │
                            │  🔴 or 🟡:        │
                            └────────┬─────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ Already tracked in  │──yes──▶ skip
                          │ remediation state?  │
                          └──────────┬──────────┘
                                     │ no
                          ┌──────────▼──────────┐
                          │ Create GitHub issue │
                          │ on target repo with │
                          │ title, body, labels │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │ Record issue URL &  │
                          │ finding ID in local │
                          │ remediation state   │
                          └─────────────────────┘
```

1. **Parse the latest assessment.** `stem remediate` reads the most recent assessment report for the target repo from the Stem instance's `reports/` directory.
2. **Extract actionable findings.** Each check marked 🔴 (Missing) or 🟡 (Basic) is a candidate for remediation.
3. **Check local state.** For each finding, Stem looks up the local remediation state file to see if an issue has already been created for that finding+repo combination.
4. **Generate contextual issue.** Using the Copilot SDK agent, Stem produces an issue body that includes:
   - A summary of the finding and why it matters.
   - Concrete steps to remediate, referencing actual files, configs, and workflows in the target repo.
   - Links to relevant documentation (e.g., GitHub Docs, framework guides).
   - The assessment dimension and check ID for traceability.
5. **Create the issue on GitHub.** The issue is opened on the target (Layer 2) repository with appropriate labels (e.g., `stem:remediation`, the dimension name).
6. **Record in local state.** The issue URL, finding ID, creation timestamp, and assessment report reference are appended to the remediation state file.
7. **Commit state.** Like assessment reports, the updated remediation state is auto-committed to the Stem instance repo.

### Remediation state

Remediation state is stored per target repository in the Stem instance repo:

```text
remediation/
  <owner>/<repo>/
    issues.yaml          # Tracked issues for this target
```

The `issues.yaml` file records every issue Stem has created, keyed by a stable finding identifier (dimension + check ID):

```yaml
# remediation/my-org/my-repo/issues.yaml
- finding_id: "code-health/test-automation"
  dimension: "Code & Repo Health"
  check: "Test automation present and configured"
  issue_url: "https://github.com/my-org/my-repo/issues/42"
  issue_number: 42
  issue_state: open          # Synced on subsequent runs
  created_at: "2026-02-27T14:30:00Z"
  assessment_report: "reports/my-org/my-repo/2026-02-27.md"
  maturity_at_creation: "missing"   # 🔴
```

**State synchronisation:** When `stem remediate` runs, it also checks the current state of previously created issues (open / closed). If a developer has closed an issue (i.e., the fix was applied), Stem updates `issue_state` to `closed`. On the next `stem assess` + `stem remediate` cycle, if the finding is now green, Stem leaves it alone. If the finding is still red/amber despite the issue being closed, Stem reopens or creates a follow-up issue.

### Issue format

Issues created by Stem follow a consistent template:

```markdown
## 🔍 SDLC Assessment Finding: {check title}

**Dimension:** {dimension name}
**Current maturity:** {🔴 Missing | 🟡 Basic}
**Target maturity:** 🟢 Mature
**Assessment date:** {date}
**Assessment report:** {link to report in Stem instance repo}

---

### What was found

{Description of the current state, referencing actual repo files/configs}

### Why it matters

{Brief explanation of the impact on SDLC health}

### Suggested remediation

{Step-by-step instructions tailored to this repository}

---

> 📋 This issue was created by [HVE Stem](https://github.com/dbroeglin/hve-stem) as part of an automated SDLC assessment.
> Finding ID: `{finding_id}` | Dimension: `{dimension}`
```

### Labels

Stem creates and applies the following labels on the target repository (creating them if they don't exist):

| Label              | Purpose                                        |
|--------------------|------------------------------------------------|
| `stem:remediation` | All issues created by Stem remediation         |
| `stem:{dimension}` | Dimension grouping (e.g., `stem:code-health`)  |
| `priority:high`    | For 🔴 Missing findings                        |
| `priority:medium`  | For 🟡 Basic findings                          |

### CLI usage

```bash
# Remediate findings for a specific repo (uses latest assessment)
stem remediate my-org/my-repo

# Dry-run: show what issues would be created without actually filing them
stem remediate my-org/my-repo --dry-run

# Remediate all repos in the portfolio
stem remediate --all

# Use a specific assessment report instead of the latest
stem remediate my-org/my-repo --report reports/my-org/my-repo/2026-02-27.md
```

---

### Blueprints

Stem ships with **opinionated default blueprints** (e.g., "Python microservice with full agentic CI/CD") that are **fully customizable**. Blueprints define:

- Which agentic workflows should be present
- Required GitHub Actions / CI/CD pipelines
- Agent configurations and permissions
- Policy and guardrail settings
- Expected repo structure conventions

**Blueprint Syntax & Extensibility:**
Blueprints are written in **plain Markdown with YAML frontmatter** and are designed to be interpreted by both humans and coding agents.

- **MVP:** No custom plugin system or complex templating engine. Customization is done by editing markdown instructions and frontmatter settings.
- **Future:** More advanced templating and extension points may be added if needed, without changing the blueprint-as-document principle.

---

## Tech Stack

### Python CLI

| Tool | Role |
| --- | --- |
| **UV** | Python package/project management |
| **Typer** | CLI framework |
| **Rich** | Terminal output formatting |
| **[GitHub Copilot SDK](https://github.com/github/copilot-sdk)** | Implementation of agentic capabilities — programmatic access to Copilot's code assistance, code review, and agent platform |
| **GitHub MCP** | Connect to GitHub from agents |
| **WorkIQ MCP** | Additional MCP integration |
| **GitHub API (PyGithub / httpx)** | Direct GitHub API access when MCP is not needed |
| **Ruff & mypy** | Code formatting, linting, and type checking |
| **pytest** | Testing framework |

### Web UI / API

| Tool | Role |
| --- | --- |
| **FastAPI** | Backend API for the web UI |
| **Next.js** | Frontend web application |
| **FastMCP** | MCP server implementation (for `stem mcp`) |

**Packaging Logistics:**
To simplify distribution, the Next.js frontend will be built as a static HTML export. These static assets will be bundled directly into the Python package. When a user runs `stem serve`, FastAPI will serve these static files alongside the API routes, ensuring users only need to install a single Python package without requiring a separate Node.js runtime.

### Developer Experience

- **Codespaces** — ready-to-code dev environment
- **Architecture Decision Records (ADRs)** — document key design choices
- **Spec-driven development** — TBD: define interfaces and contracts before implementation

## User journey

To create a new Stem instance for your team, you run:

```bash
stem init my-org/repository
```

This sets up a new Git repository with the Stem-managed SDLC blueprint, including all necessary configuration files and directory structure. You can then run:

```bash
stem assess
```

This evaluates the repository against the blueprint, producing a detailed report of SDLC maturity, code health, and agentic adoption. The report is automatically committed back to the Stem instance repository for historical tracking.

Once the assessment is complete, you can turn findings into actionable issues on the target repo:

```bash
stem remediate my-org/my-repo
```

This reads the latest assessment report, generates GitHub issues for every 🔴 or 🟡 finding with contextual remediation guidance, and tracks the created issues locally so subsequent runs won't create duplicates. Use `--dry-run` to preview what would be filed without actually creating issues.

You can also serve the web UI with:

```bash
stem serve 
```

This launches a local server where you can visualize the assessment results, track trends over time, and explore specific checks and recommendations. You can also run assessments or remediations from the web UI or trigger them from coding agents via the MCP server.

To run the MCP server for agentic interactions, you execute:

```bash
stem mcp
```

This starts the local MCP server. You can use it from GitHub Copilot CLI by adding the following configuration to your `mcp-config.json`:

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

## Open Questions
