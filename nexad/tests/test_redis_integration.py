"""Integration tests for Redis — seam S6.

Requires a running Redis instance (Docker or local) at REDIS_URL.
Marked with @pytest.mark.integration so they are skipped in CI unless
explicitly enabled.

Run with:
    REDIS_URL=redis://localhost:6379/0 python -m pytest nexad/tests/test_redis_integration.py -v -m integration
"""

from __future__ import annotations

import os

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALL_REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad",
    "REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
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
# S6 — idempotency key TTL round-trip against a real Redis instance
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_idempotency_key_ttl_set_correctly():
    """After set_idempotency_key, the key TTL in real Redis is within [58, 60] seconds.

    Uses a plain synchronous redis.Redis client so no async machinery is
    needed — the real round-trip is the point, not the async wrapper.
    """
    import redis

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis not available at {redis_url}: {exc}")

    from nexad.core.redis_client import idempotency_key_exists_sync, set_idempotency_key_sync

    key = "idem:integration-test:ttl-check"
    # Clean up any leftover key from a previous run
    client.delete(key)

    set_idempotency_key_sync(client, key, ttl_seconds=60)

    ttl = client.ttl(key)
    assert 58 <= ttl <= 60, f"Expected TTL in [58, 60], got {ttl}"

    # Verify exists returns True
    assert idempotency_key_exists_sync(client, key) is True

    # Cleanup
    client.delete(key)
    client.close()
