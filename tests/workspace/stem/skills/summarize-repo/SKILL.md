---
name: summarize-repo
description: Produce a structured SDLC maturity summary for a GitHub repository
---

Given a GitHub repository slug (`owner/repo`), retrieve the repository's
key SDLC artefacts (README, workflows, branch-protection rules, issue
templates, CODEOWNERS) and produce a structured Markdown summary with
the following sections:

1. **Repository Health** — README, licence, contributing guide.
2. **CI/CD Maturity** — workflows present, test and lint coverage.
3. **Security Posture** — secret scanning, dependency review, CODEOWNERS.
4. **Agentic Readiness** — Copilot instructions, MCP config.

Finish with a one-sentence overall verdict.
