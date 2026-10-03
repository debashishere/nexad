# 01: `core/` Config & Project Scaffold

**What to build:** The runnable monorepo skeleton for NexAd. After this ticket lands an agent can clone the repo, copy `.env.example`, run `docker compose up`, and get a live stack (Postgres 16 + Redis 7 + the NexAd app container) with no import errors. The FastAPI app starts and serves a root route; `core/config.py` reads all required env vars via `pydantic-settings` and fails fast with a clear error if any are missing.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `pyproject.toml` defines the `nexad` package with dependencies: `fastmcp`, `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg`, `redis[hiredis]`, `google-ads`, `slack-sdk`, `cryptography`, `pytest`, `pytest-asyncio`, `fakeredis`
- [ ] Top-level `nexad/` package with sub-packages: `mcp_server/`, `gateway/`, `services/`, `adapters/`, `repositories/`, `sandbox/`, `core/`, `test_agent/`, `tests/` — each with an `__init__.py`
- [ ] `core/config.py` uses `pydantic-settings` `BaseSettings` to load: `DATABASE_URL`, `REDIS_URL`, `SLACK_WEBHOOK_URL`, `SLACK_SIGNING_SECRET`, `GOOGLE_ADS_DEVELOPER_TOKEN`, `AWS_REGION`, `AES_SECRET_KEY` (32-byte hex). Missing vars raise `ValidationError` at startup.
- [ ] `docker-compose.yml` defines three services: `postgres` (image: postgres:16, with healthcheck), `redis` (image: redis:7-alpine, with healthcheck), `nexad-app` (builds from `Dockerfile`, depends_on both with condition `service_healthy`)
- [ ] `Dockerfile` builds the Python app image on `python:3.12-slim`
- [ ] `.env.example` lists every required env var with placeholder values and inline comments
- [ ] `nexad/main.py` creates the FastAPI app, registers routers, and runs via `uvicorn`. `GET /` returns `{"service":"nexad","status":"starting"}`
- [ ] Running `docker compose up` starts all three containers without errors; `curl localhost:8000/` returns the status JSON

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + ADR-0001–0004 (2.5 KB) + LLD scaffold section (3 KB) | ~3,250 |
| Core Source Code | New files only — no existing source to read | ~500 |
| Test Suites & Ticket Spec | This ticket markdown + startup smoke test | ~800 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, docker compose output, import check | ~4,000 |
| **Total** | | **~19,550 – 26,000** |

- **Peak Working Set:** ~26,000 tokens (13% of 200k ceiling)
- **Status:** 🟢 Optimal
