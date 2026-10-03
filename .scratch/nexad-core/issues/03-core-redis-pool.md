# 03: `core/` Redis Async Connection Pool

**What to build:** `core/redis_client.py` — an `aioredis` connection pool with typed helpers and the atomic Lua budget-check script pre-loaded. A `GET /health/redis` route verifies the connection. The Budget Firewall service (ticket in `services/`) will import `get_redis_pool` and call the Lua script by name without re-reading the file.

**Blocked by:** 01 — `core/` Config & Project Scaffold

**Status:** ready-for-agent

- [ ] `core/redis_client.py` creates an `aioredis.ConnectionPool` from `settings.REDIS_URL` with configurable max connections; `get_redis_pool()` returns the shared pool instance (singleton, initialised once at startup via FastAPI lifespan)
- [ ] `check_and_reserve_budget.lua` (from the LLD) is loaded from disk at startup and registered as a named script via `client.script_load()`; `run_budget_check(pool, org_id, campaign_id, date, delta_usd, max_spend_usd) → tuple[bool, Decimal]` wraps the Lua `EVALSHA` call
- [ ] Typed helper `set_idempotency_key(pool, key, ttl_seconds)` and `idempotency_key_exists(pool, key) → bool` implemented for duplicate-execution prevention
- [ ] `gateway/routers/health.py` adds `GET /health/redis` that pings the pool and returns `{"redis":"ok"}` or `{"redis":"error","detail":"..."}`
- [ ] Unit tests use `fakeredis.aioredis` — assert Lua script returns `(False, current_spend)` when delta exceeds cap; `(True, new_spend)` when within cap
- [ ] Integration test (marked `@pytest.mark.integration`) hits the Dockerised Redis; asserts idempotency key TTL is set correctly

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + ADR-0002 (OpenShell/Redis context) + LLD Redis section (2 KB) | ~3,000 |
| Core Source Code | `core/config.py` from ticket 01 + new `core/redis_client.py` + Lua script | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit tests (fakeredis) + integration test stub | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, fakeredis test output, integration test output | ~4,500 |
| **Total** | | **~21,000 – 28,000** |

- **Peak Working Set:** ~28,000 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
