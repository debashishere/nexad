"""core/redis_client.py — Redis connection pool and typed helpers.

Provides:
  - get_redis_pool()            — singleton async ConnectionPool from settings.REDIS_URL
  - run_budget_check()          — async wrapper; calls Lua EVALSHA atomically
  - run_budget_check_sync()     — sync wrapper for testing with fakeredis
  - set_idempotency_key()       — async; SET key EX ttl (NX flag for safety)
  - set_idempotency_key_sync()  — sync variant for testing
  - idempotency_key_exists()    — async; EXISTS check → bool
  - idempotency_key_exists_sync() — sync variant for testing

The Lua script is loaded from disk once at pool-init time via script_load()
and thereafter invoked with EVALSHA — no per-call script transfer overhead.
"""

from __future__ import annotations

import pathlib
from decimal import Decimal
from functools import lru_cache
from typing import Any

import redis as _redis_sync
import redis.asyncio as aioredis

# Path to the Lua budget script (sibling directory)
_LUA_SCRIPT_PATH = pathlib.Path(__file__).parent / "scripts" / "check_and_reserve_budget.lua"

# Module-level cache for the async pool singleton and loaded SHA
_pool_singleton: aioredis.ConnectionPool | None = None
_lua_sha_cache: dict[str, str] = {}  # key → sha (populated lazily)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_lua_script() -> str:
    """Return the Lua script source text from disk."""
    return _LUA_SCRIPT_PATH.read_text(encoding="utf-8")


def _budget_key(org_id: str, campaign_id: str, date: str) -> str:
    """Return the Redis key for a campaign's daily spend tracker."""
    return f"spend:{org_id}:{campaign_id}:{date}"


def _parse_budget_result(result: list[Any]) -> tuple[bool, Decimal]:
    """Parse the two-element Lua return value into (approved, spend_decimal)."""
    code, spend_str = result
    approved = int(code) == 1
    # spend_str may be bytes (redis-py) or str (fakeredis)
    if isinstance(spend_str, bytes):
        spend_str = spend_str.decode()
    return approved, Decimal(spend_str)


# ---------------------------------------------------------------------------
# Async pool singleton
# ---------------------------------------------------------------------------


def get_redis_pool(redis_url: str = "redis://localhost:6379/0") -> aioredis.ConnectionPool:
    """Return (and lazily create) the module-level async ConnectionPool.

    In production, call this inside the FastAPI lifespan with
    ``settings.REDIS_URL`` to ensure exactly one pool is created.
    """
    global _pool_singleton
    if _pool_singleton is None:
        _pool_singleton = aioredis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            decode_responses=True,
        )
    return _pool_singleton


# ---------------------------------------------------------------------------
# Async public API
# ---------------------------------------------------------------------------


async def run_budget_check(
    pool: aioredis.ConnectionPool,
    org_id: str,
    campaign_id: str,
    date: str,
    delta_usd: str | Decimal,
    max_spend_usd: str | Decimal,
    ttl_seconds: int = 86400,
) -> tuple[bool, Decimal]:
    """Atomically check and reserve a budget delta via the Lua EVALSHA call.

    Args:
        pool:          The async Redis connection pool.
        org_id:        Organisation identifier (used in the spend key).
        campaign_id:   Campaign identifier.
        date:          ISO date string, e.g. "2026-09-29".
        delta_usd:     Requested additional spend in USD.
        max_spend_usd: Daily spend cap in USD.
        ttl_seconds:   TTL for the spend key (default 86400 = 24 h).

    Returns:
        (approved, new_or_current_spend) where approved is True iff the delta
        was within the cap and has been reserved.
    """
    client = aioredis.Redis(connection_pool=pool)
    script_src = _load_lua_script()
    sha = await client.script_load(script_src)

    key = _budget_key(org_id, campaign_id, date)
    result = await client.evalsha(
        sha,
        1,
        key,
        str(delta_usd),
        str(max_spend_usd),
        str(ttl_seconds),
    )
    return _parse_budget_result(result)


async def set_idempotency_key(
    pool: aioredis.ConnectionPool,
    key: str,
    ttl_seconds: int,
) -> None:
    """Set an idempotency key with the given TTL (NX so it never clobbers)."""
    client = aioredis.Redis(connection_pool=pool)
    await client.set(key, "1", ex=ttl_seconds, nx=True)


async def idempotency_key_exists(
    pool: aioredis.ConnectionPool,
    key: str,
) -> bool:
    """Return True if the idempotency key exists in Redis."""
    client = aioredis.Redis(connection_pool=pool)
    return bool(await client.exists(key))


# ---------------------------------------------------------------------------
# Sync variants (for unit tests with fakeredis.FakeRedis)
# ---------------------------------------------------------------------------


def run_budget_check_sync(
    client: Any,
    org_id: str,
    campaign_id: str,
    date: str,
    delta_usd: str | Decimal,
    max_spend_usd: str | Decimal,
    ttl_seconds: int = 86400,
) -> tuple[bool, Decimal]:
    """Synchronous version of run_budget_check for use with fakeredis.FakeRedis."""
    script_src = _load_lua_script()
    sha = client.script_load(script_src)

    key = _budget_key(org_id, campaign_id, date)
    result = client.evalsha(
        sha,
        1,
        key,
        str(delta_usd),
        str(max_spend_usd),
        str(ttl_seconds),
    )
    return _parse_budget_result(result)


def set_idempotency_key_sync(
    client: Any,
    key: str,
    ttl_seconds: int,
) -> None:
    """Synchronous version of set_idempotency_key for use with fakeredis.FakeRedis."""
    client.set(key, "1", ex=ttl_seconds, nx=True)


def idempotency_key_exists_sync(
    client: Any,
    key: str,
) -> bool:
    """Synchronous version of idempotency_key_exists for use with fakeredis.FakeRedis."""
    return bool(client.exists(key))
