"""stem serve — launch the web UI dashboard backed by FastAPI."""

from __future__ import annotations

import importlib.resources
import threading
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from rich.console import Console

console = Console()

STATIC_ROOT = importlib.resources.files("stem") / "data" / "static"


def _build_app() -> FastAPI:
    """Construct the FastAPI application with API routes and static files."""
    app = FastAPI(title="HVE Stem", version="0.1.0")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Serve bundled static assets.
    static_dir = Path(str(STATIC_ROOT))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(static_dir / "index.html"))

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
