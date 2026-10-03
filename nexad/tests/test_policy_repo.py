"""nexad/tests/test_policy_repo.py — Unit & integration tests for repositories/policy_repo.py.

Seams under test (pre-agreed):
  S1. get_policy_for_connection — returns SafetyPolicy when found; None on miss
  S2. get_policy_for_connection — filters by ad_connection_id (not a full scan)
  S3. get_policy_for_org        — returns list[SafetyPolicy]; empty list when none
  S4. upsert_policy             — constructs the correct upsert (ON CONFLICT) statement
  S5. upsert_policy             — calls add/flush/refresh; never commit
  S6. upsert_policy             — returned SafetyPolicy carries all passed values
  S7. seed_default_policy       — fixture inserts LLD defaults (15% cap, 10/day, HITL=False)

Unit tests use AsyncMock session; no real DB is touched.
Integration test (marked @pytest.mark.integration) requires a live Postgres instance.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Shared helpers
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


def _make_session(scalar_result=None, scalars_result=None):
    """Return an AsyncMock session.

    scalar_result  — returned by result.scalar()
    scalars_result — returned by result.scalars().all()
    """
    mock_result = MagicMock()
    mock_result.scalar.return_value = scalar_result
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_result if scalars_result is not None else []
    mock_result.scalars.return_value = mock_scalars

    session = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session, mock_result



# ---------------------------------------------------------------------------
# S1 — get_policy_for_connection: found
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_policy_for_connection_returns_policy_when_found():
    """get_policy_for_connection must return SafetyPolicy when a row exists."""
    from nexad.repositories.models import SafetyPolicy
    from nexad.repositories.policy_repo import get_policy_for_connection

    connection_id = uuid.uuid4()
    expected = MagicMock(spec=SafetyPolicy)
    session, _ = _make_session(scalar_result=expected)

    result = await get_policy_for_connection(session, connection_id)

    assert result is expected
    session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# S1 — get_policy_for_connection: not found (miss)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_policy_for_connection_returns_none_on_miss():
    """get_policy_for_connection must return None when no policy is configured."""
    from nexad.repositories.policy_repo import get_policy_for_connection

    connection_id = uuid.uuid4()
    session, _ = _make_session(scalar_result=None)

    result = await get_policy_for_connection(session, connection_id)

    assert result is None


# ---------------------------------------------------------------------------
# S2 — get_policy_for_connection: filters by ad_connection_id
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_policy_for_connection_filters_by_connection_id():
    """Query must WHERE on ad_connection_id — not a full scan of safety_policies."""
    from nexad.repositories.policy_repo import get_policy_for_connection

    connection_id = uuid.uuid4()
    session, _ = _make_session()

    await get_policy_for_connection(session, connection_id)

    stmt = session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "safety_policies" in compiled
    assert "ad_connection_id" in compiled

# ---------------------------------------------------------------------------
# S3 — get_policy_for_org: returns all policies for an org
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_policy_for_org_returns_all_policies_for_org():
    """get_policy_for_org must return all SafetyPolicy rows for the given org."""
    from nexad.repositories.models import SafetyPolicy
    from nexad.repositories.policy_repo import get_policy_for_org

    org_id = uuid.uuid4()
    p1 = MagicMock(spec=SafetyPolicy)
    p2 = MagicMock(spec=SafetyPolicy)
    session, _ = _make_session(scalars_result=[p1, p2])

    result = await get_policy_for_org(session, org_id)

    assert result == [p1, p2]
    session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# S3 — get_policy_for_org: empty list when none configured
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_policy_for_org_returns_empty_list_when_none():
    """get_policy_for_org must return [] when no policies exist for the org."""
    from nexad.repositories.policy_repo import get_policy_for_org

    session, _ = _make_session(scalars_result=[])

    result = await get_policy_for_org(session, uuid.uuid4())

    assert result == []

# ---------------------------------------------------------------------------
# S4 — upsert_policy: constructs ON CONFLICT upsert statement
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_policy_executes_upsert_statement():
    """upsert_policy must execute an INSERT ... ON CONFLICT DO UPDATE statement."""
    from nexad.repositories.policy_repo import upsert_policy

    org_id = uuid.uuid4()
    connection_id = uuid.uuid4()

    session, _ = _make_session()

    await upsert_policy(
        session,
        org_id=org_id,
        ad_connection_id=connection_id,
        max_daily_budget_usd=5000.00,
        max_single_budget_increase_pct=15.0,
        max_mutations_per_day=10,
        require_hitl_for_bid_decreases=False,
        slack_webhook_url=None,
    )

    # Must execute exactly one statement (the upsert)
    session.execute.assert_awaited_once()
    stmt = session.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    # SQLAlchemy's PostgreSQL insert ON CONFLICT emits "ON CONFLICT"
    assert "ON CONFLICT" in compiled.upper()
    assert "safety_policies" in compiled


# ---------------------------------------------------------------------------
# S5 — upsert_policy: session discipline (flush/refresh, no commit)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_policy_flushes_and_does_not_commit():
    """upsert_policy must call session.flush() and never session.commit()."""
    from nexad.repositories.policy_repo import upsert_policy

    session, _ = _make_session()

    await upsert_policy(
        session,
        org_id=uuid.uuid4(),
        ad_connection_id=uuid.uuid4(),
        max_daily_budget_usd=1000.00,
        max_single_budget_increase_pct=15.0,
        max_mutations_per_day=10,
        require_hitl_for_bid_decreases=False,
        slack_webhook_url=None,
    )

    session.flush.assert_awaited_once()
    session.commit.assert_not_called()



# ---------------------------------------------------------------------------
# S6 — upsert_policy: returned SafetyPolicy carries all passed values
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_upsert_policy_returns_safety_policy_with_correct_fields():
    """upsert_policy must return SafetyPolicy with every supplied field populated."""
    from nexad.repositories.models import SafetyPolicy
    from nexad.repositories.policy_repo import upsert_policy

    org_id = uuid.uuid4()
    connection_id = uuid.uuid4()

    # scalar_result=None triggers the fallback SafetyPolicy(**values) path,
    # which lets us verify every field without a real DB.
    session, _ = _make_session(scalar_result=None)


    result = await upsert_policy(
        session,
        org_id=org_id,
        ad_connection_id=connection_id,
        max_daily_budget_usd=9999.99,
        max_single_budget_increase_pct=20.0,
        max_mutations_per_day=5,
        require_hitl_for_bid_decreases=True,
        slack_webhook_url="https://hooks.slack.com/test",
    )

    assert isinstance(result, SafetyPolicy)
    assert result.org_id == org_id
    assert result.ad_connection_id == connection_id
    assert float(result.max_daily_budget_usd) == 9999.99
    assert float(result.max_single_budget_increase_pct) == 20.0
    assert result.max_mutations_per_day == 5
    assert result.require_hitl_for_bid_decreases is True
    assert result.slack_webhook_url == "https://hooks.slack.com/test"


# ---------------------------------------------------------------------------
# S7 — seed_default_policy fixture: inserts LLD defaults
# ---------------------------------------------------------------------------


@pytest.fixture
def seed_default_policy(request):
    """Pytest fixture that inserts a SafetyPolicy with LLD defaults.

    Accepts ``connection_id`` via indirect parametrize or direct call. For
    unit tests the fixture is imported and called directly.

    LLD defaults (from issue spec):
      - max_single_budget_increase_pct = 15.0  (velocity cap)
      - max_mutations_per_day          = 10
      - require_hitl_for_bid_decreases = False
    """
    from nexad.repositories.policy_repo import seed_default_policy as _seed

    return _seed


@pytest.mark.anyio
async def test_seed_default_policy_inserts_with_lld_defaults():
    """seed_default_policy must insert a policy with the LLD-specified defaults."""
    from nexad.repositories.models import SafetyPolicy
    from nexad.repositories.policy_repo import seed_default_policy

    connection_id = uuid.uuid4()
    org_id = uuid.uuid4()
    session, _ = _make_session(scalar_result=None)

    result = await seed_default_policy(session, org_id=org_id, connection_id=connection_id)

    assert isinstance(result, SafetyPolicy)
    # Velocity cap: 15%
    assert float(result.max_single_budget_increase_pct) == 15.0
    # Max mutations per day: 10
    assert result.max_mutations_per_day == 10
    # HITL not required for decreases
    assert result.require_hitl_for_bid_decreases is False


@pytest.mark.anyio
async def test_seed_default_policy_links_org_and_connection():
    """seed_default_policy must associate the policy with the given org and connection."""
    from nexad.repositories.models import SafetyPolicy
    from nexad.repositories.policy_repo import seed_default_policy

    org_id = uuid.uuid4()
    connection_id = uuid.uuid4()
    session, _ = _make_session(scalar_result=None)


    result = await seed_default_policy(session, org_id=org_id, connection_id=connection_id)

    assert result.org_id == org_id
    assert result.ad_connection_id == connection_id


# ---------------------------------------------------------------------------
# Integration — real Postgres round-trip
# Run with: python -m pytest -m integration
# Prerequisites: docker-compose up -d db && alembic upgrade head
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.anyio
async def test_policy_repo_integration_round_trip(monkeypatch):
    """Insert a real policy and round-trip through all policy query functions.

    Requires a running Postgres instance (docker-compose up -d db) and a
    completed Alembic migration (alembic upgrade head).
    """
    import importlib

    INTEGRATION_DB_URL = "postgresql+asyncpg://nexad:nexad@localhost:5432/nexad"

    monkeypatch.setenv("DATABASE_URL", INTEGRATION_DB_URL)

    import nexad.core.db as db_mod

    importlib.reload(db_mod)

    from nexad.repositories.org_repo import create_ad_connection, create_org
    from nexad.repositories.policy_repo import (
        get_policy_for_connection,
        get_policy_for_org,
        upsert_policy,
    )

    async with db_mod.get_db_session() as session:
        # 1. Setup prerequisites (Organization + AdPlatformConnection)
        org = await create_org(session, name="Policy Test Agency", plan_tier="agency_growth")
        conn = await create_ad_connection(
            session,
            org_id=org.id,
            platform_type="google_ads",
            account_id=f"cid-{uuid.uuid4().hex[:8]}",
            encrypted_refresh_token="enc_token",
            token_iv="iv_hex_value_0000",
            token_tag="tag_hex_value_000",
        )

        # 2. Miss case
        missing_policy = await get_policy_for_connection(session, conn.id)
        assert missing_policy is None

        # 3. Upsert policy (INSERT)
        policy = await upsert_policy(
            session=session,
            org_id=org.id,
            ad_connection_id=conn.id,
            max_daily_budget_usd=3000.00,
            max_single_budget_increase_pct=15.0,
            max_mutations_per_day=10,
            require_hitl_for_bid_decreases=False,
            slack_webhook_url="https://hooks.slack.com/services/test",
        )
        assert policy.id is not None
        assert policy.ad_connection_id == conn.id

        # 4. Lookup by connection
        fetched = await get_policy_for_connection(session, conn.id)
        assert fetched is not None
        assert fetched.id == policy.id
        assert float(fetched.max_daily_budget_usd) == 3000.00
        assert float(fetched.max_single_budget_increase_pct) == 15.0
        assert fetched.max_mutations_per_day == 10
        assert fetched.require_hitl_for_bid_decreases is False
        assert fetched.slack_webhook_url == "https://hooks.slack.com/services/test"

        # 5. Lookup by org
        org_policies = await get_policy_for_org(session, org.id)
        assert len(org_policies) == 1
        assert org_policies[0].id == policy.id

        # 6. Upsert policy update (ON CONFLICT DO UPDATE)
        updated_policy = await upsert_policy(
            session=session,
            org_id=org.id,
            ad_connection_id=conn.id,
            max_daily_budget_usd=4500.00,
            max_single_budget_increase_pct=25.0,
            max_mutations_per_day=15,
            require_hitl_for_bid_decreases=True,
            slack_webhook_url="https://hooks.slack.com/services/updated",
        )
        assert updated_policy.id == policy.id
        assert float(updated_policy.max_daily_budget_usd) == 4500.00
        assert float(updated_policy.max_single_budget_increase_pct) == 25.0
        assert updated_policy.max_mutations_per_day == 15
        assert updated_policy.require_hitl_for_bid_decreases is True

        # Roll back so the integration test leaves no residue
        await session.rollback()
