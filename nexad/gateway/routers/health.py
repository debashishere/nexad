"""nexad/gateway/routers/health.py — Health check routes.

GET /health/db    — verifies Postgres connectivity via SELECT 1.
                    Returns {"postgres":"ok"} or {"postgres":"error","detail":"..."}.
GET /health/redis — verifies Redis connectivity via PING.
                    Returns {"redis":"ok"} or {"redis":"error","detail":"..."}.

Neither route ever raises HTTP 500; all exceptions are caught and returned
as structured JSON so load-balancer health checks can always parse a response.
"""

from __future__ import annotations

import redis as _sync_redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from nexad.core.db import get_db_session

router = APIRouter(prefix="/health", tags=["health"])


# ---------------------------------------------------------------------------
# Internal ping helper — top-level so tests can monkeypatch cleanly
# ---------------------------------------------------------------------------


def _ping_redis() -> bool:
    """Ping Redis and return True on success.

    Uses a synchronous client with a short connect timeout so the health
    endpoint stays fast even when Redis is unreachable.
    """
    client = _sync_redis.Redis.from_url(
        "redis://localhost:6379/0",
        socket_connect_timeout=2,
    )
    result = client.ping()
    client.close()
    return bool(result)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/db")
async def health_db() -> dict:
    """Check PostgreSQL connectivity.

    Returns:
        {"postgres": "ok"} when the database is reachable.
        {"postgres": "error", "detail": "<message>"} on any failure.
        The HTTP status code is always 200 — callers should inspect the
        ``postgres`` field to determine health.
    """
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        return {"postgres": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"postgres": "error", "detail": str(exc)}


@router.get("/redis")
def health_redis() -> JSONResponse:
    """Check Redis connectivity.

    Returns:
        200 {"redis": "ok"} when Redis responds to PING.
        200 {"redis": "error", "detail": "<message>"} on any failure.
        Never returns HTTP 500.
    """
    try:
        _ping_redis()
        return JSONResponse({"redis": "ok"})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"redis": "error", "detail": str(exc)})
