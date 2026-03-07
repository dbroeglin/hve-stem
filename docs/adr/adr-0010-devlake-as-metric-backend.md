---
title: "ADR-0010: Apache DevLake as Metric Computation Backend for Assessment"
status: "Proposed"
date: "2026-03-07"
authors: "HVE Stem Team"
tags: ["architecture", "assessment", "devlake", "dora", "metrics", "integration"]
supersedes: ""
superseded_by: ""
---

# ADR-0010: Apache DevLake as Metric Computation Backend for Assessment

## Status

**Proposed**

## Context

The Stem assessment engine (see NARRATIVE.md §Assessment Model) evaluates
repositories across five dimensions — Delivery Performance, Code & Repo
Health, Collaboration & Process, Agentic Maturity, and Governance & Policy —
using a Checks-as-Code architecture defined in `plan-assess-agent.md`.

Many of these checks require computing non-trivial SDLC metrics:

| Metric Category          | Examples                                                         |
|--------------------------|------------------------------------------------------------------|
| **DORA (5 metrics)**     | Deployment frequency, change lead time, change fail rate, failed deployment recovery time, rework rate |
| **PR metrics**           | Cycle time, review depth, pickup time, size distribution, merge rate |
| **CI/CD metrics**        | Build success rate, build duration                               |
| **Issue tracking**       | Triage time, bug age, first response time                        |

The original plan (`plan-assess-agent.md`) proposed computing all of these
directly from raw GitHub API calls within Stem's Python code. While
functionally correct, this approach has significant drawbacks:

1. **Reimplements commodity ETL.** Deployment frequency calculation alone
   requires temporal analysis, deployment-day counting, and median
   computation. Change lead time requires correlating commits, PRs, and
   deployments across timelines. These are solved problems.
2. **GitHub-only.** The narrative says "GitHub-first with abstraction layer
   for future extensibility," but building metric ETL for one tool and then
   abstracting it later is substantial additional work.
3. **No historical trending.** Raw API calls produce point-in-time snapshots.
   Trending requires storing and querying metric time series — another system
   to build and maintain.
4. **API rate limits at scale.** Computing DORA metrics for a portfolio of
   50+ repos hits GitHub API rate limits quickly, requiring incremental sync
   and caching infrastructure.

[Apache DevLake](https://devlake.apache.org/) is an open-source dev data
platform (Apache incubating) that already solves all of these problems:

- Ingests data from 15+ DevOps tools (GitHub, GitLab, Jira, Jenkins,
  BitBucket, Azure DevOps, etc.)
- Normalizes everything into a unified domain layer schema across 5 domains
  (issue tracking, source code management, code review, CI/CD, code quality)
- Computes DORA metrics with established benchmarks aligned to Google's
  Accelerate research (Elite / High / Medium / Low)
- Provides 30+ pre-built metrics with SQL query examples
- Stores historical data in MySQL/PostgreSQL for trending
- Runs as a Docker Compose stack (API server + database + Grafana dashboards)
- Exposes a REST API for programmatic access

The narrative's own design principle — *"Don't reinvent the wheel. Ground
checks in established research frameworks."* — argues for delegating metric
computation to a platform purpose-built for this task, rather than
reimplementing it.

## Decision

Use **Apache DevLake as an optional metric computation backend** for Stem's
assessment engine. When a DevLake instance is configured (via
`devlake.api_url` in `stem.yaml`), Stem queries DevLake for DORA and SDLC
metrics instead of computing them from raw API data. When no DevLake
instance is configured, metric-based checks gracefully degrade to
`CheckResult(status=CheckStatus.SKIPPED, reason="No DevLake instance configured")`.

This introduces a third data source category alongside the existing two:

```
┌─────────────────────────────────────────────────────────────────┐
│  Data Source 1: Repo Inspection (unchanged)                     │
│  Files, directories, configs (.github/, workflows, CODEOWNERS)  │
│  → Dimensions: Code Health, Agentic Maturity, Governance        │
├─────────────────────────────────────────────────────────────────┤
│  Data Source 2: GitHub API (direct, for Stem-specific data)     │
│  Copilot settings/usage, branch protection, labels              │
│  → Dimensions: Agentic Maturity, Code Health, Governance        │
├─────────────────────────────────────────────────────────────────┤
│  Data Source 3: DevLake API (for computed metrics)              │
│  DORA metrics, PR metrics, CI/CD metrics, issue metrics         │
│  → Dimensions: Delivery Performance, Collaboration & Process    │
└─────────────────────────────────────────────────────────────────┘
```

### Responsibility split

Stem focuses on what only Stem can do (unique value), while DevLake handles
commodity metric ETL:

| Stem's Job (unique value)                        | DevLake's Job (commodity metric ETL)              |
|--------------------------------------------------|---------------------------------------------------|
| Agentic maturity assessment (Dimension 4)        | DORA metrics (deployment freq, lead time, CFR…)   |
| Governance & policy compliance (Dimension 5)     | PR metrics (cycle time, review depth, size…)       |
| Repo file inspection (CODEOWNERS, workflows…)    | CI/CD metrics (build success, build duration…)     |
| Blueprint drift detection                        | Issue tracking metrics (triage time, bug age…)     |
| LLM-augmented quality checks (Layer B)           | Historical trending and benchmarking               |
| Report generation & remediation                  | Data normalization across 15+ tools                |
| Scoring model & traffic lights                   | Incremental sync & API rate limit handling         |

### Configuration

```yaml
# stem.yaml
devlake:
  enabled: true
  api_url: "http://localhost:8080"
  project_name: "my-team"     # DevLake project that maps to this Stem portfolio
```

### Graceful degradation model

If `devlake` is not present in `stem.yaml` or `devlake.enabled` is `false`,
all DevLake-backed checks return:

```python
CheckResult(
    status=CheckStatus.SKIPPED,
    score=0,
    reason="No DevLake instance configured. Set devlake.api_url in stem.yaml.",
    data_source="devlake",
)
```

File inspection checks (CODEOWNERS, workflows, templates) and direct GitHub
API checks (Copilot settings, branch protection) continue to run normally.
This means Stem remains fully functional for teams who only need structural
repo health checks and agentic maturity assessment.

### Revised check inventory by data source

**Delivery Performance (Dimension 1)** — all via DevLake:

| Check ID                        | DevLake Metric / Table                         |
|---------------------------------|------------------------------------------------|
| `delivery/deployment-frequency` | `cicd_deployment_commits` → Deployment Freq    |
| `delivery/change-lead-time`     | `project_pr_metrics` → Lead Time for Changes   |
| `delivery/recovery-time`        | Failed Deployment Recovery Time metric          |
| `delivery/change-fail-rate`     | `cicd_deployment_commits` → Change Fail Rate   |
| `delivery/ci-pipeline-exists`   | Repo inspection + `cicd_pipelines` pass rate   |
| `delivery/rework-rate`          | Custom query on deployment rework patterns     |

**Collaboration & Process (Dimension 3)** — mostly via DevLake:

| Check ID                      | Data Source   | DevLake Metric / Table               |
|-------------------------------|---------------|--------------------------------------|
| `collab/pr-review-turnaround` | DevLake       | `pull_requests` → PR Pickup Time     |
| `collab/pr-size`              | DevLake       | `pull_requests` → PR Size metric     |
| `collab/pr-review-depth`      | DevLake       | PR Review Depth metric               |
| `collab/pr-merge-rate`        | DevLake       | PR Merge Rate metric                 |
| `collab/issue-triage-time`    | DevLake       | `issues` → first response time       |
| `collab/templates-exist`      | Repo inspect  | *(unchanged — no DevLake needed)*    |
| `collab/contributing-guide`   | Repo inspect  | *(unchanged — no DevLake needed)*    |

**Code & Repo Health (Dimension 2)** — mixed sources, one new DevLake check:

| Check ID                       | Data Source   |
|--------------------------------|---------------|
| `code-health/build-success-rate` | DevLake (NEW) — `cicd_pipelines` success rate |
| All other code-health checks   | Repo inspection / GitHub API *(unchanged)*    |

**Agentic Maturity (Dimension 4)** and **Governance & Policy (Dimension 5)**
remain entirely unchanged — these use repo inspection and GitHub API only,
as they assess Stem-specific concerns that DevLake does not cover.

### What stays the same

The following architectural elements from `plan-assess-agent.md` are
**unchanged** by this decision:

1. Checks-as-Code architecture — decorator-based registry, `CheckResult`
   dataclass, `CheckContext`
2. Two-layer model — Layer A (deterministic) + Layer B (LLM-augmented)
3. Scoring model — 0–100 per check → dimension → repo → portfolio
4. Traffic lights — 🟢 ≥80%, 🟡 50–79%, 🔴 <50%
5. Report generation — Markdown reports committed to Stem instance repo
6. Remediation model — GitHub issues created from findings

## Consequences

### Positive

- **POS-001**: Avoids reimplementing complex metric ETL. Deployment
  frequency calculation, change lead time correlation, and DORA benchmark
  classification are non-trivial algorithms that DevLake has already built,
  tested, and validated against Google's Accelerate research.
- **POS-002**: Immediately supports 15+ data sources (GitHub, GitLab, Jira,
  Jenkins, BitBucket, Azure DevOps, etc.) without Stem building
  tool-specific integrations. Teams using mixed toolchains benefit on day
  one.
- **POS-003**: Historical trending comes for free. DevLake stores metric
  history in its database, enabling Stem to query "deployment frequency over
  the last 6 months" without building its own time-series storage.
- **POS-004**: DevLake's DORA benchmarks (Elite / High / Medium / Low) are
  directly aligned with Google's published Accelerate research, providing
  authoritative and well-understood performance classifications.
- **POS-005**: Aligns with the narrative's own design principle: *"Don't
  reinvent the wheel."* Stem's engineering effort stays focused on unique
  value — agentic maturity, governance, blueprints, and LLM-augmented
  assessment.
- **POS-006**: DevLake handles GitHub API rate limit management and
  incremental data sync, removing a significant operational concern for
  portfolio-scale assessment (50+ repos).

### Negative

- **NEG-001**: Adds optional infrastructure complexity. Teams wanting full
  DORA metrics must run a DevLake Docker Compose stack (API server + MySQL
  + Grafana), which adds operational overhead even when self-hosted locally.
- **NEG-002**: DevLake queries may be slower than direct GitHub API calls
  for small repositories with limited history, because the data path
  includes an ETL pipeline and database layer instead of a single API call.
- **NEG-003**: Introduces a dependency on an external open-source project.
  DevLake is an Apache incubating project with active development, but its
  API and schema may evolve between versions, requiring Stem to track and
  adapt to upstream changes.
- **NEG-004**: DevLake does NOT cover Stem-unique assessment dimensions:
  agentic maturity (Dimension 4), governance and policy compliance
  (Dimension 5), repo file inspection, LLM-augmented quality checks, and
  blueprint drift detection. These remain Stem's sole responsibility and
  cannot be delegated.
- **NEG-005**: The graceful degradation model means that teams without
  DevLake will see a significant number of checks in `SKIPPED` status
  (all DORA metrics, all PR metrics, CI/CD build success rate, issue
  triage time). This may create a perception that Stem is incomplete
  without DevLake, even though the skipped checks are clearly documented.

## Alternatives Considered

### Compute all metrics in Stem from GitHub API (original plan)

- **ALT-001**: **Description**: Stem calls the GitHub Deployments, Pull
  Requests, Actions, and Issues APIs directly and computes all DORA/SDLC
  metrics in Python code. This was the approach described in
  `plan-assess-agent.md`.
- **ALT-002**: **Rejection Reason**: Reimplements metric ETL that DevLake
  already provides — deployment frequency alone requires temporal analysis,
  deployment-day counting, and median computation. Additionally, this
  approach is GitHub-only (no GitLab, Jira, Jenkins support), provides no
  historical trending without building a separate storage layer, and hits
  GitHub API rate limits at portfolio scale (50+ repos).

### Require DevLake as a mandatory dependency

- **ALT-003**: **Description**: Make DevLake a required component of every
  Stem installation. All metric checks assume DevLake is available and fail
  (not skip) when it is not.
- **ALT-004**: **Rejection Reason**: Many teams adopting Stem will initially
  want only file inspection and GitHub API checks (agentic maturity,
  governance, branch protection, code owners). Requiring a Docker Compose
  stack for these lightweight use cases would create an unnecessarily high
  adoption barrier and violate the principle of progressive disclosure.

### Build a custom lightweight metric store in Stem

- **ALT-005**: **Description**: Implement a minimal metric database within
  Stem (e.g., SQLite) that stores computed metrics from GitHub API calls
  and supports historical trending.
- **ALT-006**: **Rejection Reason**: Requires more implementation effort
  than the original plan (Option ALT-001) while still being GitHub-only.
  The resulting system would be a partial, inferior reimplementation of
  DevLake without the multi-tool support, established DORA benchmarks, or
  community-maintained metric definitions.

### Use a commercial metrics platform (LinearB, Sleuth, Swarmia)

- **ALT-007**: **Description**: Integrate with a commercial engineering
  metrics platform instead of an open-source one.
- **ALT-008**: **Rejection Reason**: Stem is an open-source tool. Requiring
  a paid SaaS dependency would limit adoption and contradict the project's
  open-source ethos. DevLake provides equivalent metric capabilities as a
  fully self-hosted, Apache-licensed project.

## Implementation Notes

- **IMP-001**: The `DevLakeClient` is added to `CheckContext` as an
  optional field (`devlake_client: DevLakeClient | None`). Checks that
  depend on DevLake must guard on `ctx.devlake_client is not None` and
  return a `SKIPPED` result when it is absent.
- **IMP-002**: DevLake integration is implemented as Phase 3 in the revised
  implementation plan, after the core check framework (Phase 1) and repo
  inspection checks (Phase 2) are complete. This ensures Stem is useful
  before DevLake support lands.
- **IMP-003**: A Docker Compose template for local DevLake setup should be
  provided in the Stem documentation (or optionally bootstrapped by
  `stem init`), lowering the barrier for teams that want full DORA metrics.
- **IMP-004**: DevLake query results should be cached per assessment run to
  avoid redundant round-trips. Multiple checks within the same dimension
  (e.g., all Delivery Performance checks) can share a single DevLake query
  batch.
- **IMP-005**: Success criteria: all DORA metric checks produce correct
  `PASSED`/`FAILED`/`WARNING` results when connected to a DevLake instance
  with ingested data, and produce `SKIPPED` results when DevLake is not
  configured. No Stem check should error due to DevLake absence.

## References

- **REF-001**: [Apache DevLake documentation](https://devlake.apache.org/docs/Overview/WhatIsDevLake)
- **REF-002**: [DevLake DORA metrics dashboard](https://devlake.apache.org/docs/DORA/)
- **REF-003**: [Google DORA / Accelerate State of DevOps Reports](https://dora.dev/guides/dora-metrics-four-keys/)
- **REF-004**: [DORA 2024 — Five metrics (including Rework Rate)](https://dora.dev/)
- **REF-005**: NARRATIVE.md §Assessment Model — checklist-based assessment design principles
- **REF-006**: `.github/plans/plan-assess-agent.md` — original Checks-as-Code architecture
- **REF-007**: Revised assessment plan incorporating DevLake — session plan document
