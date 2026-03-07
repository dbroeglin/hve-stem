"""Shared async HTTP client for tool implementations."""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Return (and lazily create) a module-level async HTTP client."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def get_json(
    url: str, *, headers: dict[str, str] | None = None
) -> dict[str, object]:
    """GET *url* and return the parsed JSON body.

    Raises ``httpx.HTTPStatusError`` on non-2xx responses.
    """
    client = await get_client()
    resp = await client.get(url, headers=headers or {})
    resp.raise_for_status()
    result: dict[str, object] = resp.json()
    return result
