# stem assess

Evaluate a GitHub repository against the desired SDLC blueprint.

## Usage

```
stem assess <repo> [options]
```

## Arguments

| Argument | Required | Description                                  |
|----------|----------|----------------------------------------------|
| `repo`   | Yes      | GitHub repository to assess (`owner/repo`)   |

## Flags

| Flag        | Short | Default              | Description                                    |
|-------------|-------|----------------------|------------------------------------------------|
| `--model`   | `-m`  | `claude-sonnet-4.6`  | Copilot model to use for the assessment        |
| `--timeout` | `-t`  | `300.0`              | Seconds to wait for the assessment to complete |

## What It Does

1. Loads the workspace configuration (`stem.yaml`) and the active blueprint.
2. Connects to the GitHub API using the configured token
   (`STEM_GITHUB_TOKEN` or `GITHUB_TOKEN`).
3. Inspects the target repository's workflows, configuration files, and
   community health files.
4. Sends the collected data and blueprint to the configured AI model via the
   GitHub Copilot SDK.
5. Streams progress events to the terminal (tool calls, reasoning steps,
   status updates) in real time.
6. Produces a Markdown assessment report covering delivery performance, code
   health, collaboration processes, agentic maturity, and governance
   compliance.

## Examples

Assess a repository with default settings:

```bash
stem assess octocat/Hello-World
```

Assess using a specific model:

```bash
stem assess octocat/Hello-World --model gpt-4.1
```

Assess with a longer timeout for large repositories:

```bash
stem assess octocat/Hello-World --timeout 600
```

## Environment Variables

| Variable            | Description                                                                               |
|---------------------|-------------------------------------------------------------------------------------------|
| `GITHUB_TOKEN`      | GitHub API authentication                                                                 |
| `STEM_GITHUB_TOKEN` | Override token used by Stem (falls back to `GITHUB_TOKEN`)                                |
| `STEM_WORKDIR`      | Path to the Stem instance repository (alternative to `--workdir` on the root command)     |

## Related

- [stem init](init.md) — bootstrap the instance repository before assessing
- [stem remediate](remediate.md) — create issues from assessment findings
- [stem serve](serve.md) — run assessments from the web UI
- [stem mcp](mcp.md) — expose `assess_repo` to coding agents
- [NARRATIVE.md](../../NARRATIVE.md) — full design narrative and assessment model
