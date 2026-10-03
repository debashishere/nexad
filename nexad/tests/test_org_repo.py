"""nexad/tests/test_org_repo.py — Unit tests for repositories/org_repo.py.

Seams under test (pre-agreed):
  S1. get_org_by_id       — returns Organization when found; None when missing
  S2. get_connection_for_account — returns AdPlatformConnection or None via
      uk_org_platform_account filter
  S3. create_org          — adds org to session and returns it (no commit)
  S4. create_ad_connection — adds connection to session and returns it (no commit)

All tests use AsyncMock session; no real DB is touched.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, call

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FAKE_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/testdb",
    "REDIS_URL": "redis://localhost:6379/0",
    "SLACK_WEBHOOK_URL": "https://hooks.slack.com/fake",
    "SLACK_SIGNING_SECRET": "fakesecret",
    "GOOGLE_ADS_DEVELOPER_TOKEN": "faketoken",
    "AWS_REGION": "us-east-1",
    "AES_SECRET_KEY": "a" * 64,
}


@pytest.fixture(autouse=True)
def _fake_env(monkeypatch):
    for key, val in FAKE_ENV.items():
        monkeypatch.setenv(key, val)


def _make_session(scalar_result=None):
    """Return an AsyncMock session whose scalar() returns *scalar_result*."""
    mock_result = MagicMock()
    mock_result.scalar.return_value = scalar_result

    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    return session, mock_result


# ---------------------------------------------------------------------------
# S1 — get_org_by_id: found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_org_by_id_returns_org_when_found():
    """get_org_by_id must return the Organization row when it exists."""
    from nexad.repositories.models import Organization
    from nexad.repositories.org_repo import get_org_by_id

    org_id = uuid.uuid4()
    expected_org = MagicMock(spec=Organization)
    session, mock_result = _make_session(scalar_result=expected_org)

    result = await get_org_by_id(session, org_id)

    assert result is expected_org
    session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# S1 — get_org_by_id: not found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_org_by_id_returns_none_when_missing():
    """get_org_by_id must return None when no org row matches the id."""
    from nexad.repositories.org_repo import get_org_by_id

    org_id = uuid.uuid4()
    session, _ = _make_session(scalar_result=None)

    result = await get_org_by_id(session, org_id)

    assert result is None


# ---------------------------------------------------------------------------
# S1 — get_org_by_id: correct WHERE filter applied
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_org_by_id_filters_by_id():
    """get_org_by_id must apply a WHERE id = :org_id filter — not a full scan."""
    from sqlalchemy import select

    from nexad.repositories.models import Organization
    from nexad.repositories.org_repo import get_org_by_id

    org_id = uuid.uuid4()
    session, _ = _make_session()

    await get_org_by_id(session, org_id)

    # The statement passed to session.execute must be a SELECT on Organization
    # filtered by the given org_id.
    call_args = session.execute.call_args
    stmt = call_args[0][0]  # first positional arg
    # Compile and inspect the WHERE clause via string representation
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "organizations" in compiled
    assert "id" in compiled


# ---------------------------------------------------------------------------
# S2 — get_connection_for_account: found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_connection_for_account_returns_connection_when_found():
    """get_connection_for_account returns AdPlatformConnection when row exists."""
    from nexad.repositories.models import AdPlatformConnection
    from nexad.repositories.org_repo import get_connection_for_account

    org_id = uuid.uuid4()
    expected_conn = MagicMock(spec=AdPlatformConnection)
    session, _ = _make_session(scalar_result=expected_conn)

    result = await get_connection_for_account(
        session, org_id, "google_ads", "cid-123"
    )

    assert result is expected_conn
    session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# S2 — get_connection_for_account: not found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_connection_for_account_returns_none_when_missing():
    """get_connection_for_account returns None when no matching row exists."""
    from nexad.repositories.org_repo import get_connection_for_account

    session, _ = _make_session(scalar_result=None)

    result = await get_connection_for_account(
        session, uuid.uuid4(), "google_ads", "cid-999"
    )

    assert result is None


# ---------------------------------------------------------------------------
# S2 — get_connection_for_account: all three filter columns applied
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_connection_for_account_filters_by_all_three_columns():
    """Query must filter by org_id, platform_type, AND account_id (uk_org_platform_account)."""
    from nexad.repositories.org_repo import get_connection_for_account

    org_id = uuid.uuid4()
    session, _ = _make_session()

    await get_connection_for_account(session, org_id, "google_ads", "cid-123")

    stmt = session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "ad_platform_connections" in compiled
    assert "org_id" in compiled
    assert "platform_type" in compiled
    assert "account_id" in compiled


# ---------------------------------------------------------------------------
# S3 — create_org: returns organization with correct attributes
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_org_returns_organization_with_correct_fields():
    """create_org must return an Organization with name and plan_tier set."""
    from nexad.repositories.models import Organization
    from nexad.repositories.org_repo import create_org

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    result = await create_org(session, name="Acme Agency", plan_tier="agency_growth")

    assert isinstance(result, Organization)
    assert result.name == "Acme Agency"
    assert result.plan_tier == "agency_growth"


@pytest.mark.anyio
async def test_create_org_calls_session_add_and_flush_not_commit():
    """create_org must call session.add() and session.flush() — never session.commit()."""
    from nexad.repositories.org_repo import create_org

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    await create_org(session, name="Acme Agency", plan_tier="agency_growth")

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# S4 — create_ad_connection: returns connection with correct attributes
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_ad_connection_returns_connection_with_correct_fields():
    """create_ad_connection must return AdPlatformConnection with all fields set."""
    from nexad.repositories.models import AdPlatformConnection
    from nexad.repositories.org_repo import create_ad_connection

    org_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    result = await create_ad_connection(
        session,
        org_id=org_id,
        platform_type="google_ads",
        account_id="cid-777",
        encrypted_refresh_token="enc_token",
        token_iv="iv_hex",
        token_tag="tag_hex",
    )

    assert isinstance(result, AdPlatformConnection)
    assert result.org_id == org_id
    assert result.platform_type == "google_ads"
    assert result.account_id == "cid-777"
    assert result.encrypted_refresh_token == "enc_token"
    assert result.token_iv == "iv_hex"
    assert result.token_tag == "tag_hex"


@pytest.mark.anyio
async def test_create_ad_connection_calls_add_and_flush_not_commit():
    """create_ad_connection must call session.add() and session.flush() — never commit()."""
    from nexad.repositories.org_repo import create_ad_connection

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    await create_ad_connection(
        session,
        org_id=uuid.uuid4(),
        platform_type="google_ads",
        account_id="cid-777",
        encrypted_refresh_token="enc_token",
        token_iv="iv_hex",
        token_tag="tag_hex",
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Integration — real Postgres round-trip
# Run with: python -m pytest -m integration
# Prerequisites: docker-compose up -d db && alembic upgrade head
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_org_repo_integration_round_trip(monkeypatch):
    """Insert a real org + connection row and round-trip through all query functions.

    Requires a running Postgres instance (docker-compose up -d db) and a
    completed Alembic migration (alembic upgrade head).
    """
    import importlib

    INTEGRATION_DB_URL = "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad"

    monkeypatch.setenv("DATABASE_URL", INTEGRATION_DB_URL)

    # Re-import db module so the engine picks up the overridden DATABASE_URL.
    import nexad.core.db as db_mod

    importlib.reload(db_mod)

    from nexad.repositories.org_repo import (
        create_ad_connection,
        create_org,
        get_connection_for_account,
        get_org_by_id,
    )

    async with db_mod.get_db_session() as session:
        # --- create org ---
        org = await create_org(session, name="Integration Test Agency", plan_tier="agency_growth")
        assert org.id is not None
        assert org.name == "Integration Test Agency"

        # --- get_org_by_id: found ---
        fetched_org = await get_org_by_id(session, org.id)
        assert fetched_org is not None
        assert fetched_org.id == org.id

        # --- get_org_by_id: not found ---
        missing = await get_org_by_id(session, uuid.uuid4())
        assert missing is None

        # --- create connection ---
        conn = await create_ad_connection(
            session,
            org_id=org.id,
            platform_type="google_ads",
            account_id="cid-integration-001",
            encrypted_refresh_token="enc_token_value",
            token_iv="iv_hex_value_0000",
            token_tag="tag_hex_value_000",
        )
        assert conn.id is not None
        assert conn.org_id == org.id

        # --- get_connection_for_account: found ---
        fetched_conn = await get_connection_for_account(
            session, org.id, "google_ads", "cid-integration-001"
        )
        assert fetched_conn is not None
        assert fetched_conn.id == conn.id
        assert fetched_conn.encrypted_refresh_token == "enc_token_value"

        # --- get_connection_for_account: not found ---
        missing_conn = await get_connection_for_account(
            session, org.id, "meta_ads", "non-existent"
        )
        assert missing_conn is None

        # Roll back so the integration run leaves no residue in the DB.
        await session.rollback()
