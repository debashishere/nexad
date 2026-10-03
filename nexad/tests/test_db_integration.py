"""nexad/tests/test_db_integration.py — S4 integration tests.

These tests require a running Docker Postgres instance and a completed
Alembic migration.  They are skipped by default unless you pass:

    python -m pytest -m integration

Run pre-requisites:
    docker-compose up -d db
    alembic upgrade head
"""

from __future__ import annotations

import pytest
import pytest


# ---------------------------------------------------------------------------
# Integration marker — these tests require -m integration to run
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.integration

DATABASE_URL = "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad"


@pytest.fixture(autouse=True)
def _set_db_env(monkeypatch):
    """Point Settings at the Docker Postgres instance."""
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/fake")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "fakesecret")
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "faketoken")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AES_SECRET_KEY", "a" * 64)


@pytest.mark.anyio
async def test_all_four_tables_exist_after_migration():
    """All four LLD tables must exist after `alembic upgrade head`."""
    from sqlalchemy import inspect, text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            # Use information_schema to check table existence
            result = await conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = ANY(:names)
                    ORDER BY table_name
                    """
                ),
                {"names": [
                    "organizations",
                    "ad_platform_connections",
                    "safety_policies",
                    "execution_audit_ledger",
                ]},
            )
            found = {row[0] for row in result.fetchall()}
    finally:
        await engine.dispose()

    expected = {
        "organizations",
        "ad_platform_connections",
        "safety_policies",
        "execution_audit_ledger",
    }
    assert found == expected, (
        f"Missing tables after migration: {expected - found}"
    )


@pytest.mark.anyio
async def test_idx_ledger_org_status_index_exists():
    """The idx_ledger_org_status composite index must exist after migration."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'execution_audit_ledger'
                      AND indexname = 'idx_ledger_org_status'
                    """
                )
            )
            rows = result.fetchall()
    finally:
        await engine.dispose()

    assert len(rows) == 1, (
        "Expected index 'idx_ledger_org_status' not found on execution_audit_ledger"
    )
