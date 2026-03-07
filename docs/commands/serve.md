# stem serve

Launch the web UI locally for a visual dashboard experience.

## Usage

```
stem serve [options]
```

## Flags

| Flag           | Short | Default      | Description                         |
|----------------|-------|--------------|-------------------------------------|
| `--host`       | `-h`  | `127.0.0.1`  | Bind address                       |
| `--port`       | `-p`  | `8777`       | Port to listen on                  |
| `--no-browser` | —     | `false`      | Do not open a browser automatically |

## What It Does

1. Builds a FastAPI application with API routes and static file serving.
2. Exposes the following API endpoints:

   | Method | Endpoint                      | Description                        |
   |--------|-------------------------------|------------------------------------|
   | GET    | `/api/health`                 | Health check                       |
   | GET    | `/api/targets`                | List target repos from `stem.yaml` |
   | POST   | `/api/assess?repo=…&model=…` | Start an assessment job            |
   | GET    | `/api/assess/{job_id}`        | Get assessment job status          |
   | GET    | `/api/assess/{job_id}/stream` | Stream assessment events via SSE   |

3. Serves the bundled React frontend (Primer design system) as a single-page
   application.
4. Opens the dashboard in your default browser (unless `--no-browser` is set).

## Examples

Start the dashboard with default settings (opens browser):

```bash
stem serve
```

Start without opening a browser, on a custom port:

```bash
stem serve --no-browser --port 9000
```

Bind to all interfaces (e.g. for container deployments):

```bash
stem serve --host 0.0.0.0 --no-browser
```

## Development Setup

For day-to-day frontend work, run the FastAPI backend and the Vite dev server
side by side:

```bash
# Terminal 1 — API server
uv run stem serve --no-browser

# Terminal 2 — Vite dev server with HMR + API proxy
cd app && npm run dev
```

Open `http://localhost:5173`. The Vite config proxies `/api/*` to the FastAPI
backend at port 8777.

## Environment Variables

| Variable            | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `GITHUB_TOKEN`      | GitHub API authentication (used by assessments triggered from the UI)                 |
| `STEM_GITHUB_TOKEN` | Override token used by Stem (falls back to `GITHUB_TOKEN`)                            |
| `STEM_WORKDIR`      | Path to the Stem instance repository (alternative to `--workdir` on the root command) |

## Related

- [stem assess](assess.md) — run assessments from the CLI
- [stem init](init.md) — bootstrap the instance repository
- [stem remediate](remediate.md) — create issues from assessment findings
- [stem mcp](mcp.md) — expose Stem tools to coding agents
- [ADR-0008](../adr/adr-0008-web-ui-served-via-fastapi.md) — web UI served via FastAPI
- [ADR-0009](../adr/adr-0009-frontend-framework-and-primer-design-system.md) — frontend framework and Primer design system
