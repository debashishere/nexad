"""Initial schema — creates all four NexAd tables matching the LLD DDL exactly.

Revision ID: 4bd8ec031974
Revises:
Create Date: 2026-10-03

Tables created:
  - organizations
  - ad_platform_connections  (+ UNIQUE constraint uk_org_platform_account)
  - safety_policies
  - execution_audit_ledger   (+ INDEX idx_ledger_org_status)
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers — used by Alembic
# ---------------------------------------------------------------------------

revision = "4bd8ec031974"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "plan_tier",
            sa.String(50),
            server_default="agency_growth",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # ad_platform_connections
    # ------------------------------------------------------------------
    op.create_table(
        "ad_platform_connections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_type", sa.String(50), nullable=False),
        sa.Column("account_id", sa.String(100), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text, nullable=False),
        sa.Column("token_iv", sa.String(32), nullable=False),
        sa.Column("token_tag", sa.String(32), nullable=False),
        sa.Column(
            "status", sa.String(50), server_default="active", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "org_id", "platform_type", "account_id", name="uk_org_platform_account"
        ),
    )

    # ------------------------------------------------------------------
    # safety_policies
    # ------------------------------------------------------------------
    op.create_table(
        "safety_policies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "ad_connection_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("max_daily_budget_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "max_single_budget_increase_pct",
            sa.Numeric(5, 2),
            server_default="15.00",
            nullable=False,
        ),
        sa.Column(
            "max_mutations_per_day",
            sa.Integer,
            server_default="10",
            nullable=False,
        ),
        sa.Column(
            "require_hitl_for_bid_decreases",
            sa.Boolean,
            server_default="false",
            nullable=False,
        ),
        sa.Column("slack_webhook_url", sa.Text, nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["org_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["ad_connection_id"],
            ["ad_platform_connections.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # execution_audit_ledger
    # ------------------------------------------------------------------
    op.create_table(
        "execution_audit_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "ad_connection_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("tool_invoked", sa.String(100), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evaluation_result", sa.String(50), nullable=False),
        sa.Column(
            "hitl_status", sa.String(50), server_default="none", nullable=True
        ),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("network_mutation_id", sa.String(255), nullable=True),
        sa.Column("error_details", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(
            ["ad_connection_id"], ["ad_platform_connections.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    # Composite index on the audit ledger (from LLD)
    op.create_index(
        "idx_ledger_org_status",
        "execution_audit_ledger",
        ["org_id", "evaluation_result", "hitl_status"],
    )


def downgrade() -> None:
    op.drop_index("idx_ledger_org_status", table_name="execution_audit_ledger")
    op.drop_table("execution_audit_ledger")
    op.drop_table("safety_policies")
    op.drop_table("ad_platform_connections")
    op.drop_table("organizations")
