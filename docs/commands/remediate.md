# stem remediate

Create GitHub issues for each assessment finding with contextual fix
suggestions.

> **Status:** This command is planned but not yet implemented. The interface
> described below reflects the intended design from
> [NARRATIVE.md](../../NARRATIVE.md).

## Usage

```
stem remediate <repo> [options]
```

## Arguments

| Argument | Required | Description                                  |
|----------|----------|----------------------------------------------|
| `repo`   | Yes      | GitHub repository to remediate (`owner/repo`) |

## What It Does

1. Loads the most recent assessment report for the target repository.
2. For each finding in the report, creates a GitHub issue with:
   - A clear title describing the gap
   - Context from the assessment (dimension, check, current state)
   - Suggested remediation steps
3. Links issues back to the assessment report for traceability.

## Environment Variables

| Variable            | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `GITHUB_TOKEN`      | GitHub API authentication (required for issue creation)                                |
| `STEM_GITHUB_TOKEN` | Override token used by Stem (falls back to `GITHUB_TOKEN`)                            |
| `STEM_WORKDIR`      | Path to the Stem instance repository (alternative to `--workdir` on the root command) |

## Related

- [stem assess](assess.md) — generate the assessment that feeds remediation
- [stem init](init.md) — bootstrap the instance repository
- [stem serve](serve.md) — view assessments in the web UI
- [stem mcp](mcp.md) — expose Stem tools to coding agents
- [NARRATIVE.md](../../NARRATIVE.md) — full design narrative including remediation model
