# 06: Safety Policy Repository

**What to build:** `repositories/policy_repo.py` — typed async read/write functions for the `safety_policies` table. The Budget Firewall service reads a policy on every mutation evaluation; this ticket makes that lookup fast, typed, and testable in isolation.

**Blocked by:** 02 — PostgreSQL Async Session Factory

**Status:** completed

- [x] `get_policy_for_connection(session, ad_connection_id: UUID) → SafetyPolicy | None` — primary lookup used by the firewall on every mutation; returns `None` if no policy configured (callers apply a system default)
- [x] `get_policy_for_org(session, org_id: UUID) → list[SafetyPolicy]` — returns all policies across an org's connections (used by management endpoints)
- [x] `upsert_policy(session, org_id, ad_connection_id, max_daily_budget_usd, max_single_budget_increase_pct, max_mutations_per_day, require_hitl_for_bid_decreases, slack_webhook_url) → SafetyPolicy` — insert or update via `ON CONFLICT DO UPDATE`; does not commit
- [x] `pytest` fixture `seed_default_policy(session, connection_id)` inserts a policy with the LLD defaults (15% velocity cap, 10 mutations/day, HITL not required for decreases) — reused by firewall service tests
- [x] Unit tests mock session; assert `upsert_policy` constructs the correct upsert statement; `get_policy_for_connection` returns `None` on miss
- [x] Integration test inserts a policy and asserts `get_policy_for_connection` returns matching values


---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD schema section (4 KB) + ADR-0001 (0.5 KB) | ~3,000 |
| Core Source Code | `core/db.py` + `repositories/models.py` (ticket 02) | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit tests + `seed_default_policy` fixture | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~3,500 |
| **Total** | | **~19,900 – 26,500** |

- **Peak Working Set:** ~26,500 tokens (13% of 200k ceiling)
- **Status:** 🟢 Optimal
