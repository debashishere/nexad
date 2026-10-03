"""nexad/repositories/org_repo.py — Typed async query functions for the
organizations and ad_platform_connections tables.

All functions:
  - Are async and accept an AsyncSession
  - Do NOT commit — transaction management is the caller's responsibility
  - Return encrypted credential fields as-is; decryption is via core/crypto.py
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexad.repositories.models import AdPlatformConnection, Organization


# ---------------------------------------------------------------------------
# Organization queries
# ---------------------------------------------------------------------------


async def get_org_by_id(
    session: AsyncSession,
    org_id: uuid.UUID,
) -> Organization | None:
    """Fetch an org row by primary key.

    Returns ``None`` if not found — callers are responsible for raising HTTP 404.
    """
    result = await session.execute(
        select(Organization).where(Organization.id == org_id)
    )
    return result.scalar()


async def get_connection_for_account(
    session: AsyncSession,
    org_id: uuid.UUID,
    platform_type: str,
    account_id: str,
) -> AdPlatformConnection | None:
    """Resolve the unique AdPlatformConnection for a (org, platform, account) triple.

    Matches the ``uk_org_platform_account`` unique constraint.
    Returns ``None`` if not found.
    """
    result = await session.execute(
        select(AdPlatformConnection).where(
            AdPlatformConnection.org_id == org_id,
            AdPlatformConnection.platform_type == platform_type,
            AdPlatformConnection.account_id == account_id,
        )
    )
    return result.scalar()


# ---------------------------------------------------------------------------
# Write functions
# ---------------------------------------------------------------------------


async def create_org(
    session: AsyncSession,
    name: str,
    plan_tier: str,
) -> Organization:
    """Insert a new Organization row and return it.

    Does NOT commit — the caller owns the transaction boundary.
    Uses ``session.flush()`` so that server-generated defaults (e.g. ``id``,
    ``created_at``) are populated before returning.
    """
    org = Organization(name=name, plan_tier=plan_tier)
    session.add(org)
    await session.flush()
    await session.refresh(org)
    return org


async def create_ad_connection(
    session: AsyncSession,
    org_id: uuid.UUID,
    platform_type: str,
    account_id: str,
    encrypted_refresh_token: str,
    token_iv: str,
    token_tag: str,
) -> AdPlatformConnection:
    """Insert a new AdPlatformConnection row and return it.

    Credential fields must be pre-encrypted by the caller via ``core/crypto.py``
    before passing them here. Does NOT commit — caller manages the transaction.
    """
    conn = AdPlatformConnection(
        org_id=org_id,
        platform_type=platform_type,
        account_id=account_id,
        encrypted_refresh_token=encrypted_refresh_token,
        token_iv=token_iv,
        token_tag=token_tag,
    )
    session.add(conn)
    await session.flush()
    await session.refresh(conn)
    return conn
