# 11: Budget Firewall Service

**What to build:** `services/firewall_service.py` — `evaluate_and_route()`, the heart of NexAd. Fetches the org's safety policy, runs the Redis atomic Lua budget check, decides auto-approve vs HITL escalation, dispatches the write or creates the pending ledger record, and returns a typed `FirewallResult`. This is the only function that orchestrates across Redis, the DB, the write adapter, and the HITL notifier.

**Blocked by:** 03 — Redis Pool, 06 — Safety Policy Repo, 07 — Audit Ledger Repo, 09 — Google Ads Write Adapter

**Status:** ready-for-agent

- [ ] `FirewallResult` dataclass: `status: Literal['EXECUTED','ESCALATED_TO_HITL','REJECTED_BY_POLICY']`, `message: str`, `action_token: UUID | None`, `execution_receipt: MutationReceipt | None`, `requires_human_approval: bool`
- [ ] `evaluate_and_route(account_id, campaign_id, new_budget_micros, rationale, idempotency_key, session, redis_pool, connection) → FirewallResult`:
  1. Check Redis idempotency key — return cached result if already processed
  2. Fetch `SafetyPolicy` via `policy_repo.get_policy_for_connection()`; apply system defaults if none found (15% cap, 10 mutations/day)
  3. Fetch current budget via `analytics_service.get_campaign_budget()`
  4. Compute `delta_pct = (new - current) / current * 100`
  5. Run `core/redis_client.run_budget_check()` Lua script atomically
  6. **Auto-approve path** (delta ≤ cap AND daily spend ≤ max): call `write_adapter.apply_budget_mutation()`, call `ledger_repo.record_auto_approved()`, return `EXECUTED`
  7. **Escalation path** (delta > cap OR spend > max): call `ledger_repo.record_escalated_to_hitl()`, call `hitl_notifier.trigger_slack_escalation()`, return `ESCALATED_TO_HITL`
- [ ] Mutation count per day is tracked in Redis (`mutations:{org_id}:{campaign_id}:{date}` counter, TTL 86400s); if count exceeds `policy.max_mutations_per_day` the action is `REJECTED_BY_POLICY` without HITL escalation
- [ ] All exceptions from the write adapter are caught, logged, and recorded in the ledger as `error_details` before re-raising a clean `ExecutionError`
- [ ] Unit tests cover all three result paths (EXECUTED / ESCALATED / REJECTED) with mocked Redis, policy, ledger, and write adapter; assert idempotency key prevents double-execution

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD firewall section + sequence diagram (6 KB) + HLD dual-gating (3 KB) | ~4,125 |
| Core Source Code | `core/redis_client.py` (03) + `repositories/policy_repo.py` (06) + `repositories/ledger_repo.py` (07) + `adapters/google_ads_adapter.py` (09) + `services/analytics_service.py` (10) | ~4,500 |
| Test Suites & Ticket Spec | This ticket + unit tests for all 3 result paths | ~1,200 |
| Interactive Skill Phases | Single implementation pass | ~3,000 |
| Implementation & Test Runs | File writes, pytest output (3 test paths) | ~5,000 |
| **Total** | | **~26,825 – 36,000** |

- **Peak Working Set:** ~36,000 tokens (18% of 200k ceiling)
- **Status:** 🟢 Optimal
