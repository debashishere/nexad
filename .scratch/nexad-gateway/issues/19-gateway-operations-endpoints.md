# 19: Open Approvals & Anomaly Scan Endpoints

**What to build:** `gateway/routers/operations.py` — two operational endpoints an account director uses to monitor the system between Slack notifications: a list of pending HITL approvals and an on-demand anomaly scan. Both are authenticated via the Bearer middleware from ticket 17.

**Blocked by:** 07 — Audit Ledger Repo, 13 — Anomaly Detection Service, 17 — Auth Middleware

**Status:** ready-for-agent

- [ ] `GET /orgs/{org_id}/pending-approvals` — authenticated; calls `ledger_repo.get_pending_hitl_actions(session, org_id)`; returns list of pending escalations with: `action_token`, `campaign_id`, `current_budget`, `proposed_budget`, `delta_pct`, `agent_rationale`, `created_at`; paginated (default limit 20, cursor-based)
- [ ] `POST /orgs/{org_id}/scan-anomalies` body: `{"account_id": str}`; authenticated; fetches campaigns via `analytics_service.get_campaign_performance()`, calls `anomaly_service.detect_anomalies()`, returns `{"alerts": [{"campaign_id", "alert_type", "current_value", "threshold_value", "detected_at"}]}`
- [ ] `POST /orgs/{org_id}/scan-anomalies` — if any `KILL_SWITCH_TRIGGERED` alert is returned, also calls `anomaly_service.run_kill_switch()` and appends `{"kill_switch_activated": true, "campaigns_paused": N}` to the response
- [ ] Both endpoints enforce org scoping: if `org_id` in the path does not match `request.state.org.id`, return HTTP 403 — no cross-org data leakage
- [ ] Unit tests: pending-approvals returns correct ledger rows; scan-anomalies returns `AnomalyAlert` list; kill-switch activated on `KILL_SWITCH_TRIGGERED` alert; 403 on org mismatch

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + PRD use case 2 (3 KB) + LLD ledger query (2 KB) | ~3,125 |
| Core Source Code | `repositories/ledger_repo.py` (07) + `services/anomaly_service.py` (13) + `gateway/middleware/auth.py` (17) | ~3,000 |
| Test Suites & Ticket Spec | This ticket + unit tests for org-scoping | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~22,025 – 29,500** |

- **Peak Working Set:** ~29,500 tokens (15% of 200k ceiling)
- **Status:** 🟢 Optimal
