---
type: blueprint
name: default
description: Default SDLC blueprint for a modern software project.
---

# Default SDLC Blueprint

This blueprint describes the desired state for a well-managed software
project following modern SDLC best practices.

## Repository Health

- **README**: Clear project description, setup instructions, and usage examples.
- **LICENSE**: An OSI-approved license file at the repository root.
- **CONTRIBUTING**: Contribution guidelines covering branching strategy, PR process, and code style.
- **CODEOWNERS**: Defined code ownership for critical paths.
- **Issue templates**: Bug report and feature request templates.
- **PR template**: Pull request template with checklist.
- **Branch protection**: Main branch requires PR reviews and passing CI.

## CI/CD Maturity

- **Build**: Automated build on every push and PR.
- **Test**: Automated test suite with coverage reporting.
- **Lint**: Linting and formatting checks enforced in CI.
- **Deploy**: Automated deployment pipeline with environment gates.
- **Reusable workflows**: Shared CI/CD components to reduce duplication.
- **Secrets management**: No hard-coded secrets; use environment variables or vault.

## Code Quality

- **Linting**: Configured linter with project-specific rules.
- **Type checking**: Static type analysis enabled (where applicable).
- **Test coverage**: Coverage tooling integrated; target ≥ 80%.
- **Dependency management**: Automated dependency updates (Dependabot or Renovate).
- **Code review**: All changes reviewed by at least one peer.

## Security Posture

- **Dependency scanning**: Automated vulnerability scanning for dependencies.
- **Secret scanning**: Enabled to prevent accidental credential leaks.
- **SBOM**: Software Bill of Materials generated for releases.
- **Signed commits**: Encouraged or required for main branch contributions.

## Agentic Readiness

- **Copilot instructions**: `.github/copilot-instructions.md` with project context.
- **Agent definitions**: Purpose-built agents for common workflows.
- **Skill definitions**: Reusable skills for domain-specific tasks.
- **MCP integration**: MCP server configuration for coding agent integration.
- **Automated triage**: AI-assisted issue triage and labeling.
