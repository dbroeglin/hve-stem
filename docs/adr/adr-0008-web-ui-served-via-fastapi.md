---
title: "ADR-0008: Web UI Served via FastAPI with Bundled Static Assets"
status: "Accepted"
date: "2026-03-07"
authors: "HVE Stem Team"
tags: ["architecture", "web-ui", "fastapi", "serve"]
supersedes: ""
superseded_by: ""
---

# ADR-0008: Web UI Served via FastAPI with Bundled Static Assets

## Status

**Accepted**

## Context

Stem exposes three interfaces with feature parity: a CLI, an MCP server,
and a web UI dashboard. The web UI (`stem serve`) needs to serve both a
browser-based frontend and an API that the frontend consumes.

The NARRATIVE.md specifies that the Next.js frontend will eventually be
built as a static HTML export, bundled directly into the Python package so
users only need a single `pip install` — no separate Node.js runtime
required. During the MVP phase, the frontend is a simple static HTML page
that will be replaced later.

The forces at play:

- **Single-package distribution.** Users should be able to `pip install
  hve-stem` and run `stem serve` without additional setup or runtime
  dependencies outside Python.
- **API + static files from one process.** The web UI must consume an API
  for assessment data, health checks, and future CRUD operations. Serving
  both the API and the static assets from a single HTTP server simplifies
  deployment and avoids CORS configuration.
- **Parity principle.** The same core logic powering the CLI and MCP
  interfaces must be accessible through the web API.
- **Fast startup, low overhead.** `stem serve` is a developer tool run
  locally. It needs to start quickly and use minimal resources.
- **Browser convenience.** Developers expect `stem serve` to open the
  dashboard in their browser automatically, similar to tools like
  `jupyter notebook` or `vite dev`.

## Decision

Implement `stem serve` as a **FastAPI application** served by **Uvicorn**,
with static frontend assets bundled inside the Python package at
`src/stem/data/static/`.

Specifically:

1. **FastAPI** provides the `/api/` routes (starting with `/api/health`).
2. **Static files** are served via `StaticFiles` middleware mounted at
   `/static`, with the root `/` returning `index.html` directly.
3. **Uvicorn** is the ASGI server, started programmatically from the Typer
   command — no separate `uvicorn` CLI invocation needed.
4. **Browser auto-open** is the default behaviour. A `--no-browser` flag
   disables it. The browser is opened via a short `threading.Timer` delay
   to allow the server to bind first.
5. **Host and port** default to `127.0.0.1:8777` and are configurable via
   `--host` / `--port` CLI options.

The `_build_app()` factory function constructs the FastAPI instance,
making it independently testable via `fastapi.testclient.TestClient`
without starting a real server.

## Consequences

**Positive:**

- A single `uv run stem serve` starts the full dashboard — no Docker, no
  Node.js, no extra processes.
- The `_build_app()` factory enables fast, isolated testing of all API
  routes and static file serving.
- FastAPI's OpenAPI integration provides automatic API documentation at
  `/docs` for free, aiding future frontend development.
- Adding new API endpoints (e.g., `/api/assess`, `/api/repos`) is
  straightforward as the project evolves.

**Negative:**

- FastAPI and Uvicorn are added as runtime dependencies, increasing the
  package's dependency footprint.
- Static assets are bundled inside the Python package; any frontend change
  requires a package rebuild. This is acceptable for MVP but will need a
  dev-mode proxy story once the Next.js frontend arrives.

**Neutral:**

- The `index.html` placeholder will be replaced by a Next.js static export
  in a future iteration. The serving infrastructure will remain unchanged.
