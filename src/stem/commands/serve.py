"""stem serve — launch the web UI dashboard backed by FastAPI."""

from __future__ import annotations

import asyncio
import importlib.resources
import json
import threading
import uuid
import webbrowser
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated, Any

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from stem.engine import AssessEvent, run_assessment
from stem.workspace import load_workspace

console = Console()

STATIC_ROOT = importlib.resources.files("stem") / "data" / "static"

# In-memory store for running jobs keyed by job ID.
_jobs: dict[str, dict[str, Any]] = {}


async def _run_assess_job(job_id: str, repo: str, model: str) -> None:
    """Run an assessment in the background, streaming events into the job store."""
    job = _jobs[job_id]
    job["status"] = "running"

    def _on_event(event: AssessEvent) -> None:
        entry: dict[str, str] = {"type": event.type}
        if event.message:
            entry["message"] = event.message
        if event.tool:
            entry["tool"] = event.tool
        if event.detail:
            entry["detail"] = event.detail
        job["events"].append(entry)

    try:
        ws = load_workspace(Path.cwd().resolve())
        result = await run_assessment(
            repo=repo,
            ws=ws,
            model=model,
            on_event=_on_event,
        )
        job["result"] = result
        job["status"] = "completed"
    except Exception as exc:
        job["status"] = "failed"
        job["events"].append({"type": "error", "message": str(exc)})


def _build_app() -> FastAPI:
    """Construct the FastAPI application with API routes and static files."""
    app = FastAPI(title="HVE Stem", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/targets")
    def get_targets() -> list[str]:
        """Return the list of target repositories from stem.yaml."""
        ws = load_workspace(Path.cwd().resolve())
        return ws.targets

    @app.post("/api/assess")
    async def start_assess(
        repo: str,
        model: str = "claude-sonnet-4.6",
    ) -> dict[str, str]:
        """Start an assessment job and return the job ID."""
        job_id = str(uuid.uuid4())
        _jobs[job_id] = {
            "id": job_id,
            "repo": repo,
            "model": model,
            "status": "pending",
            "events": [],
            "result": None,
        }
        asyncio.create_task(_run_assess_job(job_id, repo, model))
        return {"job_id": job_id}

    @app.get("/api/assess/{job_id}/stream")
    async def stream_assess(job_id: str) -> StreamingResponse:
        """Stream assessment events as SSE."""

        async def event_generator() -> AsyncGenerator[str, None]:
            sent = 0
            while True:
                job = _jobs.get(job_id)
                if job is None:
                    msg = json.dumps({"type": "error", "message": "Job not found"})
                    yield f"data: {msg}\n\n"
                    return

                # Send any new events since last check
                events = job["events"]
                while sent < len(events):
                    yield f"data: {json.dumps(events[sent])}\n\n"
                    sent += 1

                if job["status"] in ("completed", "failed"):
                    # Send the final result
                    done = json.dumps(
                        {
                            "type": "done",
                            "status": job["status"],
                            "result": job.get("result"),
                        }
                    )
                    yield f"data: {done}\n\n"
                    return

                await asyncio.sleep(0.3)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    @app.get("/api/assess/{job_id}")
    async def get_assess_job(job_id: str) -> dict[str, Any]:
        """Get the current state of an assessment job."""
        job = _jobs.get(job_id)
        if job is None:
            return {"error": "Job not found"}
        return {
            "id": job["id"],
            "repo": job["repo"],
            "status": job["status"],
            "result": job.get("result"),
            "event_count": len(job["events"]),
        }

    # Serve bundled static assets.
    static_dir = Path(str(STATIC_ROOT))
    index_path = static_dir / "index.html"

    if index_path.is_file():
        app.mount(
            "/assets",
            StaticFiles(
                directory=str(static_dir / "assets")
                if (static_dir / "assets").is_dir()
                else str(static_dir)
            ),
            name="assets",
        )

        @app.get("/{path:path}")
        def spa_fallback(path: str) -> FileResponse:
            """Serve the SPA — try static file first, fall back to index.html."""
            candidate = static_dir / path
            if path and candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(index_path))

    return app


def _open_browser(url: str) -> None:
    """Open *url* in the default browser (best-effort, failures are ignored)."""
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass


def serve(
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Bind address."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to listen on."),
    ] = 8777,
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="Do not open a browser automatically."),
    ] = False,
) -> None:
    """Launch the web UI locally for a visual dashboard experience."""
    app = _build_app()
    url = f"http://{host}:{port}"

    console.print(f"[bold green]stem serve[/] — starting at [link={url}]{url}[/link]")

    if not no_browser:
        threading.Timer(1.0, _open_browser, args=[url]).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
