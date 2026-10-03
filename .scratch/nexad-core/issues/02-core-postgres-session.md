# 02: `core/` PostgreSQL Async Session Factory

**What to build:** `core/db.py` — an async SQLAlchemy engine and session factory that all repositories will use. A `GET /health/db` FastAPI route opens a session, runs `SELECT 1`, and returns `{"postgres":"ok"}`. An agent implementing a repository can import `get_db_session` and get a working, transaction-scoped async session with no further setup.

**Blocked by:** 01 — `core/` Config & Project Scaffold

**Status:** ready-for-agent

- [ ] `core/db.py` creates an `AsyncEngine` from `settings.DATABASE_URL` using `create_async_engine` with pool size configuration
- [ ] `get_db_session()` is an `asynccontextmanager` yielding an `AsyncSession` with `expire_on_commit=False`; rolls back on exception, closes on exit
- [ ] All four PostgreSQL schemas from the LLD are expressed as SQLAlchemy `DeclarativeBase` mapped classes in `repositories/models.py`: `Organization`, `AdPlatformConnection`, `SafetyPolicy`, `ExecutionAuditLedger` — with correct column types, constraints, and relationships matching the LLD DDL exactly
- [ ] Alembic is configured; an initial migration generates the four tables with all indexes (`idx_ledger_org_status`)
- [ ] `gateway/routers/health.py` adds `GET /health/db` that calls `SELECT 1` via the session factory and returns `{"postgres":"ok"}` or `{"postgres":"error","detail":"..."}` on failure
- [ ] Unit test mocks `AsyncEngine` and asserts rollback is called on exception
- [ ] Integration test (marked `@pytest.mark.integration`) hits the Dockerised Postgres container and asserts all four tables exist after migration

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + ADR-0001–0004 (2.5 KB) + LLD schema section (4 KB) | ~3,500 |
| Core Source Code | `core/config.py` from ticket 01 + new `core/db.py` + `repositories/models.py` | ~2,000 |
| Test Suites & Ticket Spec | This ticket + unit + integration test stubs | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, alembic migration output, test runner output | ~5,000 |
| **Total** | | **~22,500 – 30,000** |

- **Peak Working Set:** ~30,000 tokens (15% of 200k ceiling)
- **Status:** 🟢 Optimal
