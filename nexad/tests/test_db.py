"""nexad/tests/test_db.py — Unit tests for core/db.py (S3) and GET /health/db (S5).

S3: Session factory unit tests — no real DB, all async mocked.
S5: Health route tests via FastAPI TestClient.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

FAKE_DB_URL = "postgresql+asyncpg://test:test@localhost:5432/testdb"
FAKE_ENV = {
    "DATABASE_URL": FAKE_DB_URL,
    "REDIS_URL": "redis://localhost:6379/0",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/fake",
    "SLACK_SIGNING_SECRET": "fakesecret",
    "GOOGLE_ADS_DEVELOPER_TOKEN": "faketoken",
    "AWS_REGION": "us-east-1",
    "AES_SECRET_KEY": "a" * 64,
}


@pytest.fixture(autouse=True)
def _strip_nexad_env(monkeypatch):
    """Remove any real NEXAD env vars so Settings can be constructed safely."""
    nexad_keys = [
        "DATABASE_URL",
        "REDIS_URL",
        "SLACK_WEBHOOK_URL",
        "SLACK_SIGNING_SECRET",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "AWS_REGION",
        "AES_SECRET_KEY",
    ]
    for key in nexad_keys:
        monkeypatch.delenv(key, raising=False)
    for key, val in FAKE_ENV.items():
        monkeypatch.setenv(key, val)


# ---------------------------------------------------------------------------
# S3 — get_db_session() unit tests (no real DB)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_db_session_is_asynccontextmanager():
    """get_db_session() must behave as an asynccontextmanager."""
    from contextlib import asynccontextmanager

    from nexad.core.db import get_db_session

    # The function itself must be an async context manager (usable with `async with`)
    # We patch the engine's session creation to avoid real DB calls.
    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    with patch("nexad.core.db.AsyncSessionLocal", return_value=mock_session):
        async with get_db_session() as session:
            assert session is mock_session


@pytest.mark.anyio
async def test_get_db_session_yields_session_with_expire_on_commit_false():
    """The session factory must be configured with expire_on_commit=False."""
    from nexad.core.db import AsyncSessionLocal

    # Inspect the session factory configuration directly via its kw_args.
    # SQLAlchemy's async_sessionmaker stores this in kw or class_kw.
    factory_kw = AsyncSessionLocal.kw
    assert factory_kw.get("expire_on_commit") is False, (
        "AsyncSessionLocal must be created with expire_on_commit=False"
    )


@pytest.mark.anyio
async def test_get_db_session_happy_path_no_rollback():
    """On a clean exit (no exception), rollback must NOT be called."""
    from nexad.core.db import get_db_session

    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    with patch("nexad.core.db.AsyncSessionLocal", return_value=mock_session):
        async with get_db_session() as session:
            pass  # no exception

    mock_session.rollback.assert_not_called()
    mock_session.close.assert_called_once()


@pytest.mark.anyio
async def test_get_db_session_rollback_on_exception():
    """On exception inside the context, rollback() must be called before close()."""
    from nexad.core.db import get_db_session

    call_order: list[str] = []

    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock(side_effect=lambda: call_order.append("rollback"))
    mock_session.close = AsyncMock(side_effect=lambda: call_order.append("close"))

    with patch("nexad.core.db.AsyncSessionLocal", return_value=mock_session):
        with pytest.raises(ValueError, match="boom"):
            async with get_db_session() as session:
                raise ValueError("boom")

    # Verify rollback was called
    mock_session.rollback.assert_called_once()
    # Verify close was called
    mock_session.close.assert_called_once()
    # Verify ORDER: rollback before close
    assert call_order == ["rollback", "close"], (
        f"Expected rollback then close, got: {call_order}"
    )


@pytest.mark.anyio
async def test_get_db_session_exception_propagates():
    """The exception must be re-raised after rollback (not swallowed)."""
    from nexad.core.db import get_db_session

    mock_session = AsyncMock()

    with patch("nexad.core.db.AsyncSessionLocal", return_value=mock_session):
        with pytest.raises(RuntimeError, match="propagated"):
            async with get_db_session() as session:
                raise RuntimeError("propagated")


# ---------------------------------------------------------------------------
# S5 — GET /health/db route tests
# ---------------------------------------------------------------------------


def _make_test_client():
    """Return a synchronous TestClient for the NexAd FastAPI app."""
    from fastapi.testclient import TestClient
    from nexad.main import app

    return TestClient(app)


def test_health_db_returns_ok_when_db_available():
    """GET /health/db → {"postgres":"ok"} when SELECT 1 succeeds."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("nexad.gateway.routers.health.get_db_session") as mock_get_db:
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        client = _make_test_client()
        response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"postgres": "ok"}


def test_health_db_returns_error_when_db_unavailable():
    """GET /health/db → {"postgres":"error","detail":"..."} on DB failure."""
    with patch("nexad.gateway.routers.health.get_db_session") as mock_get_db:
        mock_get_db.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("connection refused")
        )
        mock_get_db.return_value.__aexit__ = AsyncMock(return_value=False)

        client = _make_test_client()
        response = client.get("/health/db")

    assert response.status_code == 200  # never 500 — always 200
    body = response.json()
    assert body["postgres"] == "error"
    assert "detail" in body
    assert "connection refused" in body["detail"]
