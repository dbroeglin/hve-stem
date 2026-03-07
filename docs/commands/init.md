# stem init

Bootstrap a Stem instance repository in the current directory.

## Usage

```
stem init [repo] [options]
```

## Arguments

| Argument | Required | Description                                 |
|----------|----------|---------------------------------------------|
| `repo`   | No       | Optional target repo to seed (`owner/repo`) |

## Flags

| Flag              | Short | Default | Description                                                                              |
|-------------------|-------|---------|------------------------------------------------------------------------------------------|
| `--blueprint`     | —     | —       | Fetch blueprints from a remote GitHub repo (`owner/repo`) instead of the bundled default |
| `--blueprint-ref` | —     | —       | Pin the remote blueprint source to a branch, tag, or SHA                                 |

## What It Does

1. Verifies that `stem.yaml` does not already exist in the current directory.
2. Creates the instance directory structure:

   ```
   .
   ├── blueprints/          # SDLC blueprint definitions
   ├── remediation/         # Remediation tracking
   ├── reports/             # Assessment reports
   ├── stem/                # Internal config, agents, skills
   │   ├── agents/
   │   ├── mcp.json
   │   └── skills/
   ├── .github/
   │   ├── agents/
   │   ├── copilot-instructions.md
   │   ├── prompts/
   │   ├── skills/
   │   └── workflows/
   ├── stem.yaml            # Instance configuration
   ├── README.md
   └── .gitignore
   ```

3. Copies the default blueprint (or prepares for a remote blueprint source).
4. Renders `stem.yaml` with instance metadata and optional target repositories.
5. Copies bundled Copilot SDK configuration, agents, and skills.
6. Copies GitHub Actions workflows.
7. Initialises a Git repository and creates an initial commit.

## Examples

Bootstrap an empty instance repository:

```bash
mkdir my-stem && cd my-stem
stem init
```

Bootstrap with a target repository pre-configured:

```bash
mkdir my-stem && cd my-stem
stem init octocat/Hello-World
```

Use blueprints from a remote repository:

```bash
stem init --blueprint my-org/sdlc-blueprints
```

Pin the remote blueprint source to a specific ref:

```bash
stem init --blueprint my-org/sdlc-blueprints --blueprint-ref v2.0
```

## Environment Variables

| Variable       | Description                                                                           |
|----------------|---------------------------------------------------------------------------------------|
| `STEM_WORKDIR` | Path to the Stem instance repository (alternative to `--workdir` on the root command) |

## Related

- [stem assess](assess.md) — evaluate a repository after initialising
- [stem remediate](remediate.md) — create issues from assessment findings
- [stem serve](serve.md) — launch the web UI dashboard
- [stem mcp](mcp.md) — expose Stem tools to coding agents
- [NARRATIVE.md](../../NARRATIVE.md) — full design narrative and instance model
- [ADR-0003](../adr/adr-0003-stem-instance-repository-structure.md) — instance repository structure
- [ADR-0006](../adr/adr-0006-blueprint-sourcing-strategy.md) — blueprint sourcing strategy
