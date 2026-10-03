"""Tests for core/redis_client.py and GET /health/redis.

Seam S5 — unit tests with fakeredis (no real Redis needed):
  - Lua check_and_reserve_budget returns (False, current_spend) on cap breach
  - Lua check_and_reserve_budget returns (True, new_spend) when within cap
  - idempotency_key_exists() returns False for an unseen key
  - idempotency_key_exists() returns True after set_idempotency_key()

Seam S7 — HTTP seam GET /health/redis via FastAPI TestClient:
  - ping succeeds → {"redis": "ok"}
  - Redis unavailable → {"redis": "error", "detail": "..."} (never 500)
"""

from __future__ import annotations

import pytest
import fakeredis

# ---------------------------------------------------------------------------
# Shared env-var fixture
# ---------------------------------------------------------------------------

ALL_REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad",
    "REDIS_URL": "redis://localhost:6379/0",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T000/B000/xxxx",
    "SLACK_SIGNING_SECRET": "slack_signing_secret_example",
    "GOOGLE_ADS_DEVELOPER_TOKEN": "google_ads_dev_token_example",
    "AWS_REGION": "us-east-1",
    "AES_SECRET_KEY": "a" * 64,
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Strip all NexAd env vars so pydantic-settings only reads kwargs."""
    for key in ALL_REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_client() -> fakeredis.FakeRedis:
    """Return a synchronous FakeRedis client with Lua scripting enabled."""
    return fakeredis.FakeRedis()


# ---------------------------------------------------------------------------
# S5-A  Budget Lua script — cap breach → (False, current_spend)
# ---------------------------------------------------------------------------


def test_budget_lua_cap_breach():
    """Lua script returns (False, current_spend) when delta would exceed max_spend."""
    from nexad.core.redis_client import run_budget_check_sync

    client = _fake_client()
    # Pre-seed current spend to 480.00
    client.set("spend:org1:cmp1:2026-09-29", "480.00")

    # delta 50.00, max 500.00 → 480 + 50 = 530 > 500 → cap breach
    approved, spend = run_budget_check_sync(
        client=client,
        org_id="org1",
        campaign_id="cmp1",
        date="2026-09-29",
        delta_usd="50.00",
        max_spend_usd="500.00",
        ttl_seconds=86400,
    )

    assert approved is False
    from decimal import Decimal
    assert spend == Decimal("480.00")


# ---------------------------------------------------------------------------
# S5-B  Budget Lua script — within cap → (True, new_spend)
# ---------------------------------------------------------------------------


def test_budget_lua_within_cap():
    """Lua script returns (True, new_spend) when delta is within cap."""
    from nexad.core.redis_client import run_budget_check_sync

    client = _fake_client()
    client.set("spend:org2:cmp2:2026-09-29", "100.00")

    # delta 50.00, max 500.00 → 100 + 50 = 150 ≤ 500 → approved
    approved, spend = run_budget_check_sync(
        client=client,
        org_id="org2",
        campaign_id="cmp2",
        date="2026-09-29",
        delta_usd="50.00",
        max_spend_usd="500.00",
        ttl_seconds=86400,
    )

    assert approved is True
    from decimal import Decimal
    assert spend == Decimal("150.00")


# ---------------------------------------------------------------------------
# S5-C  idempotency_key_exists — returns False for unseen key
# ---------------------------------------------------------------------------


def test_idempotency_key_exists_false_for_new_key():
    """idempotency_key_exists returns False when key has never been set."""
    from nexad.core.redis_client import idempotency_key_exists_sync

    client = _fake_client()
    assert idempotency_key_exists_sync(client, "idem:never-set-key") is False


# ---------------------------------------------------------------------------
# S5-D  idempotency_key_exists — returns True after set_idempotency_key
# ---------------------------------------------------------------------------


def test_idempotency_key_exists_true_after_set():
    """idempotency_key_exists returns True after set_idempotency_key is called."""
    from nexad.core.redis_client import idempotency_key_exists_sync, set_idempotency_key_sync

    client = _fake_client()
    key = "idem:my-request-uuid"
    set_idempotency_key_sync(client, key, ttl_seconds=60)
    assert idempotency_key_exists_sync(client, key) is True


# ---------------------------------------------------------------------------
# S7  GET /health/redis — via FastAPI TestClient
# ---------------------------------------------------------------------------


@pytest.fixture()
def app_with_fake_redis(monkeypatch):
    """Return a FastAPI TestClient with the redis health route.

    We set all required env vars BEFORE importing the router because
    nexad.core.db calls Settings() at module load time.
    """
    for key, val in ALL_REQUIRED_ENV.items():
        monkeypatch.setenv(key, val)

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from nexad.gateway.routers.health import router

    test_app = FastAPI()
    test_app.include_router(router)
    return TestClient(test_app)


def test_health_redis_ok(app_with_fake_redis, monkeypatch):
    """GET /health/redis returns {"redis":"ok"} when ping succeeds."""
    import nexad.gateway.routers.health as health_mod

    # Patch _ping_redis to return True
    monkeypatch.setattr(health_mod, "_ping_redis", lambda: True)

    resp = app_with_fake_redis.get("/health/redis")
    assert resp.status_code == 200
    assert resp.json() == {"redis": "ok"}


def test_health_redis_error(app_with_fake_redis, monkeypatch):
    """GET /health/redis returns error JSON (not 500) when Redis is unavailable."""
    import nexad.gateway.routers.health as health_mod

    def _raise():
        raise ConnectionError("Redis refused connection")

    monkeypatch.setattr(health_mod, "_ping_redis", _raise)

    resp = app_with_fake_redis.get("/health/redis")
    assert resp.status_code == 200  # never 500
    body = resp.json()
    assert body["redis"] == "error"
    assert "detail" in body
    assert len(body["detail"]) > 0
