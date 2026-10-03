# 07: Audit Ledger Repository

**What to build:** `repositories/ledger_repo.py` — append-only write and targeted read functions for the `execution_audit_ledger` table. The ledger is never updated in place except for the `hitl_status` transition column. Every agent action — auto-approved, escalated, or rejected — lands here before the API response is returned.

**Blocked by:** 02 — PostgreSQL Async Session Factory

**Status:** ready-for-agent

- [ ] `record_auto_approved(session, org_id, ad_connection_id, idempotency_key, agent_id, tool_invoked, request_payload, network_mutation_id) → ExecutionAuditLedger` — inserts row with `evaluation_result='auto_approved'`, `hitl_status='none'`, `executed_at=now()`
- [ ] `record_escalated_to_hitl(session, org_id, ad_connection_id, idempotency_key, agent_id, tool_invoked, request_payload) → ExecutionAuditLedger` — inserts row with `evaluation_result='escalated_to_hitl'`, `hitl_status='pending'`; returns the row (callers use `id` as the action token)
- [ ] `record_hitl_outcome(session, ledger_id: UUID, status: Literal['approved','declined','expired'], approved_by: str | None) → ExecutionAuditLedger` — the **only** update allowed: sets `hitl_status`, `approved_by`, `executed_at`; raises `ValueError` if row is not in `'pending'` state
- [ ] `get_pending_hitl_actions(session, org_id: UUID) → list[ExecutionAuditLedger]` — returns all rows where `hitl_status='pending'` for an org; used by the gateway's open-approvals endpoint
- [ ] `idempotency_key_exists_in_ledger(session, key: str) → bool` — secondary idempotency guard (primary guard is Redis in ticket 03; this is the durable fallback)
- [ ] Unit tests assert no raw `UPDATE` SQL is issued on the main row body; only `hitl_status`, `approved_by`, `executed_at` columns transition; `record_hitl_outcome` raises `ValueError` on a non-pending row
- [ ] Integration test inserts an escalated row, calls `record_hitl_outcome`, asserts `hitl_status='approved'`

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD schema + sequence diagram (5 KB) + ADR-0001 (0.5 KB) | ~3,250 |
| Core Source Code | `core/db.py` + `repositories/models.py` (ticket 02) | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit tests asserting no raw UPDATE | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~20,750 – 27,500** |

- **Peak Working Set:** ~27,500 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
