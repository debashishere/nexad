Low-Level Design (LLD): Project NexAd

System: Enterprise Agentic Ad Mediation & Execution Gateway

Document Version: 1.0.0

Classification: Technical Implementation Details

1. Data Models & Database Schemas (PostgreSQL 16)

The relational schema maintains strict multi-tenancy, immutable audit trails, and deterministic policy enforcement.

-- Core Tenants & Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'agency_growth',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ad Platform Credentials (Encrypted at Rest via AES-256-GCM)
CREATE TABLE ad_platform_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    platform_type VARCHAR(50) NOT NULL, -- 'google_ads', 'meta_marketing', 'amazon_ads'
    account_id VARCHAR(100) NOT NULL,    -- e.g., Google Ads Customer ID (CID)
    encrypted_refresh_token TEXT NOT NULL,
    token_iv VARCHAR(32) NOT NULL,
    token_tag VARCHAR(32) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uk_org_platform_account UNIQUE (org_id, platform_type, account_id)
);

-- Financial Governance & Policy Thresholds
CREATE TABLE safety_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    ad_connection_id UUID NOT NULL REFERENCES ad_platform_connections(id) ON DELETE CASCADE,
    max_daily_budget_usd NUMERIC(12, 2) NOT NULL,
    max_single_budget_increase_pct NUMERIC(5, 2) NOT NULL DEFAULT 15.00,
    max_mutations_per_day INT NOT NULL DEFAULT 10,
    require_hitl_for_bid_decreases BOOLEAN NOT NULL DEFAULT FALSE,
    slack_webhook_url TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Immutable Ledger of Agent Actions & Approvals
CREATE TABLE execution_audit_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    ad_connection_id UUID NOT NULL REFERENCES ad_platform_connections(id),
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    agent_id VARCHAR(100) NOT NULL,
    tool_invoked VARCHAR(100) NOT NULL,
    request_payload JSONB NOT NULL,
    evaluation_result VARCHAR(50) NOT NULL, -- 'auto_approved', 'escalated_to_hitl', 'rejected_by_policy'
    hitl_status VARCHAR(50) DEFAULT 'none', -- 'pending', 'approved', 'declined', 'expired'
    approved_by VARCHAR(255),
    network_mutation_id VARCHAR(255),
    error_details TEXT,
    executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ledger_org_status ON execution_audit_ledger(org_id, evaluation_result, hitl_status);


2. In-Memory Concurrency & Rate Limiting (Redis)

To prevent race conditions across parallel task agents attempting concurrent spend adjustments, atomic rate checks are implemented via Redis Lua scripts:

Atomic Budget Delta Script (check_and_reserve_budget.lua)

-- KEYS[1]: org_campaign_spend_key (e.g., "spend:org_123:cmp_456:2026-09-29")
-- ARGV[1]: requested_delta_usd (e.g., "50.00")
-- ARGV[2]: max_allowed_daily_spend (e.g., "500.00")
-- ARGV[3]: ttl_seconds (e.g., 86400)

local current_spend = redis.call('GET', KEYS[1])
if not current_spend then
    current_spend = 0
else
    current_spend = tonumber(current_spend)
end

local delta = tonumber(ARGV[1])
local max_spend = tonumber(ARGV[2])

if (current_spend + delta) > max_spend then
    return {0, tostring(current_spend)} -- Code 0: Policy Violation
else
    local new_spend = current_spend + delta
    redis.call('SET', KEYS[1], tostring(new_spend), 'EX', tonumber(ARGV[3]))
    return {1, tostring(new_spend)} -- Code 1: Approved and Reserved
end


3. Core Component Interfaces & Class Definitions

3.1 Python FastMCP Ad Server (mcp_server.py)

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Literal
import uuid

mcp = FastMCP("NexAd-Execution-Engine")

class BudgetAdjustmentInput(BaseModel):
    account_id: str = Field(description="Google Ads Customer ID or Meta Account ID")
    campaign_id: str = Field(description="Platform-specific campaign identifier")
    new_daily_budget_micros: int = Field(
        gt=0, 
        description="New daily budget in currency micros (e.g., $100.00 = 100000000)"
    )
    justification_rationale: str = Field(
        min_length=10, 
        max_length=500, 
        description="Reasoning trail provided by the agent for verification"
    )
    idempotency_key: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request key to guarantee once-only execution"
    )

@mcp.tool()
async def adjust_campaign_budget(params: BudgetAdjustmentInput) -> dict:
    """
    Safely adjusts the daily budget for a specific advertising campaign.
    Subject to deterministic budget firewalls and potential HITL human escalation.
    """
    from services.firewall_service import evaluate_and_route
    result = await evaluate_and_route(
        account_id=params.account_id,
        campaign_id=params.campaign_id,
        new_budget_micros=params.new_daily_budget_micros,
        rationale=params.justification_rationale,
        idempotency_key=params.idempotency_key
    )
    return result


3.2 Firewall & Evaluation Engine (firewall_service.py)

from decimal import Decimal
from typing import Dict, Any
from core.redis_client import get_redis_pool
from core.db import get_db_session
from adapters.google_ads_adapter import GoogleAdsExecutionAdapter
from services.hitl_notifier import trigger_slack_escalation

async def evaluate_and_route(
    account_id: str, 
    campaign_id: str, 
    new_budget_micros: int, 
    rationale: str,
    idempotency_key: str
) -> Dict[str, Any]:
    db = await get_db_session()
    redis = await get_redis_pool()
    
    # 1. Fetch current policy & platform state
    policy = await db.get_policy_for_account(account_id)
    adapter = GoogleAdsExecutionAdapter(account_id)
    current_budget_micros = await adapter.get_campaign_budget_micros(campaign_id)
    
    current_budget = Decimal(current_budget_micros) / Decimal(1_000_000)
    proposed_budget = Decimal(new_budget_micros) / Decimal(1_000_000)
    delta_pct = ((proposed_budget - current_budget) / current_budget) * Decimal(100)
    
    # 2. Evaluate Velocity Threshold
    if delta_pct > policy.max_single_budget_increase_pct or proposed_budget > policy.max_daily_budget_usd:
        # Escalation path: Record in ledger and dispatch HITL card
        action_token = await db.create_pending_hitl_action(
            account_id=account_id,
            campaign_id=campaign_id,
            proposed_budget=proposed_budget,
            rationale=rationale,
            idempotency_key=idempotency_key
        )
        
        await trigger_slack_escalation(
            webhook_url=policy.slack_webhook_url,
            action_token=action_token,
            campaign_id=campaign_id,
            current_budget=current_budget,
            proposed_budget=proposed_budget,
            rationale=rationale
        )
        
        return {
            "status": "ESCALATED_TO_HITL",
            "message": "Proposed budget increase exceeds automated policy threshold. Dispatched to human supervisor for cryptographic approval.",
            "action_token": action_token,
            "requires_human_approval": True
        }
        
    # 3. Automated Execution Path
    execution_receipt = await adapter.apply_budget_mutation(campaign_id, new_budget_micros)
    await db.record_successful_execution(idempotency_key, execution_receipt)
    
    return {
        "status": "EXECUTED",
        "message": "Budget successfully modified within policy bounds.",
        "execution_receipt": execution_receipt,
        "requires_human_approval": False
    }


4. Cryptographic Human Approval Flow (HITL Webhook)

When an operation requires human intervention, NexAd dispatches an HMAC-signed payload to Slack or the management console:

┌────────────────────────────────────────────────────────┐
│               NEXAD SAFETY ESCALATION                │
├────────────────────────────────────────────────────────┤
│ Campaign ID: CMP-8921-US                               │
│ Current Budget:  $400.00 / day                         │
│ Proposed Budget: $520.00 / day (+30.0%)                │
│                                                        │
│ Agent Rationale:                                       │
│ "ROAS exceeded 4.2x over 4-hour window on SKU-78.      │
│ Scaling spend to capture conversion spike."            │
├────────────────────────────────────────────────────────┤
│ Action Token: 9b2d...f4a1                              │
│ [ ✅ APPROVE MUTATION ]       [ ❌ REJECT MUTATION ]   │
└────────────────────────────────────────────────────────┘


Signature Verification Algorithm

import hmac
import hashlib

def verify_approval_signature(token: str, timestamp: str, incoming_sig: str, secret_key: str) -> bool:
    message = f"v0:{timestamp}:{token}".encode("utf-8")
    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        message,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, incoming_sig)


5. End-to-End Sequence Diagram (Write Path)

Agent Task         FastMCP Engine       Redis/Policy DB      Slack HITL Gateway       Google Ads API
    │                     │                     │                     │                     │
    │── 1. tools/call ───>│                     │                     │                     │
    │   (adjust_budget)   │── 2. Lua Check ────>│                     │                     │
    │                     │<── 3. Delta > 15% ──│                     │                     │
    │                     │                                           │                     │
    │                     │── 4. Create Pending Action & Ledger Entry │                     │
    │                     │── 5. Push Signed Interactive Card ───────>│                     │
    │<── 6. Tool Response─│                                           │                     │
    │   ("ESCALATED_...") │                                           │                     │
    │                     │                                 [Human Reviews & Clicks]        │
    │                     │                                           │                     │
    │                     │<── 7. POST /webhook/hitl-callback ────────│                     │
    │                     │   (HMAC Signed Approval)                  │                     │
    │                     │                                                                 │
    │                     │── 8. Mutate Campaign Budget ───────────────────────────────────>│
    │                     │<── 9. Mutation Confirmed (200 OK) ──────────────────────────────│
    │                     │                                                                 │
    │                     │── 10. Update Audit Ledger (status='approved')                   │
