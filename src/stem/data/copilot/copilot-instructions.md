## Stem Instance Repository

This is a Stem instance repository — the control plane for a team's
agentic SDLC portfolio.

### Key files

- `stem.yaml` — Instance configuration and portfolio targets.
- `blueprints/` — SDLC blueprints and policy documents.
- `reports/` — Auto-generated assessment reports per target repo.
- `remediation/` — Tracked remediation state per target repo.

### Conventions

- Assessment reports are auto-committed to `reports/<owner>/<repo>/`.
- Blueprints use YAML front-matter with `type: blueprint` or `type: policy`.
- Target repos are listed in `stem.yaml` under the `targets` key.
