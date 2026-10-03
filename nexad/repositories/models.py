"""nexad/repositories/models.py — SQLAlchemy ORM models matching the LLD DDL.

All four tables from LLD Section 1 are declared here:
  - Organization
  - AdPlatformConnection
  - SafetyPolicy
  - ExecutionAuditLedger (+ idx_ledger_org_status index)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Shared declarative base for all NexAd ORM models."""


# ---------------------------------------------------------------------------
# organizations
# ---------------------------------------------------------------------------


class Organization(Base):
    """Core tenant entity — every other table references this."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="agency_growth"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    ad_platform_connections: Mapped[list["AdPlatformConnection"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    safety_policies: Mapped[list["SafetyPolicy"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    audit_ledger_entries: Mapped[list["ExecutionAuditLedger"]] = relationship(
        back_populates="organization"
    )


# ---------------------------------------------------------------------------
# ad_platform_connections
# ---------------------------------------------------------------------------


class AdPlatformConnection(Base):
    """Ad platform credentials, encrypted at rest via AES-256-GCM."""

    __tablename__ = "ad_platform_connections"
    __table_args__ = (
        UniqueConstraint("org_id", "platform_type", "account_id", name="uk_org_platform_account"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform_type: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_iv: Mapped[str] = mapped_column(String(32), nullable=False)
    token_tag: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        back_populates="ad_platform_connections"
    )
    safety_policies: Mapped[list["SafetyPolicy"]] = relationship(
        back_populates="ad_connection", cascade="all, delete-orphan"
    )
    audit_ledger_entries: Mapped[list["ExecutionAuditLedger"]] = relationship(
        back_populates="ad_connection"
    )


# ---------------------------------------------------------------------------
# safety_policies
# ---------------------------------------------------------------------------


class SafetyPolicy(Base):
    """Financial governance & policy thresholds per ad connection."""

    __tablename__ = "safety_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    ad_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ad_platform_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    max_daily_budget_usd: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    max_single_budget_increase_pct: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="15.00"
    )
    max_mutations_per_day: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="10"
    )
    require_hitl_for_bid_decreases: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    slack_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        back_populates="safety_policies"
    )
    ad_connection: Mapped["AdPlatformConnection"] = relationship(
        back_populates="safety_policies"
    )


# ---------------------------------------------------------------------------
# execution_audit_ledger
# ---------------------------------------------------------------------------


class ExecutionAuditLedger(Base):
    """Immutable ledger of all agent actions and approvals."""

    __tablename__ = "execution_audit_ledger"
    __table_args__ = (
        Index("idx_ledger_org_status", "org_id", "evaluation_result", "hitl_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
    )
    ad_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ad_platform_connections.id"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True
    )
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_invoked: Mapped[str] = mapped_column(String(100), nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    evaluation_result: Mapped[str] = mapped_column(String(50), nullable=False)
    hitl_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default="none"
    )
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    network_mutation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        back_populates="audit_ledger_entries"
    )
    ad_connection: Mapped["AdPlatformConnection"] = relationship(
        back_populates="audit_ledger_entries"
    )
