# 13: Anomaly Detection Service

**What to build:** `services/anomaly_service.py` — evaluates a snapshot of campaign performance data and flags anomalies that exceed defined safety bounds. When the kill-switch threshold is breached (CAC spike >300% over 2-hour moving average), it calls `pause_all_campaigns()` on the write adapter and records the event in the audit ledger.

**Blocked by:** 10 — Analytics Service, 09 — Google Ads Write Adapter, 07 — Audit Ledger Repo

**Status:** ready-for-agent

- [ ] `AnomalyAlert` dataclass: `campaign_id: str`, `alert_type: Literal['CPA_SPIKE','KILL_SWITCH_TRIGGERED','VELOCITY_BREACH']`, `current_value: Decimal`, `threshold_value: Decimal`, `detected_at: datetime`
- [ ] `detect_anomalies(campaigns: list[CampaignSummary], baseline_cpa: Decimal) → list[AnomalyAlert]` — iterates campaigns; flags `CPA_SPIKE` if `cost_per_conversion > baseline_cpa * 3.0` (>300% over baseline); returns list of alerts without side effects
- [ ] `run_kill_switch(account_id, connection, campaigns, session, ledger_id_prefix) → int` — called when `CPA_SPIKE` is detected and confirmed; calls `GoogleAdsWriteAdapter.pause_all_campaigns(account_id)` (added to ticket 09 scope); records each pause as a `record_auto_approved` ledger entry with `tool_invoked='kill_switch'`; returns count of campaigns paused
- [ ] `pause_all_campaigns(account_id: str) → list[MutationReceipt]` added to `GoogleAdsWriteAdapter` (ticket 09 extension) — calls Google Ads `CampaignService.mutate()` to set all active campaigns to `PAUSED` status
- [ ] Kill-switch is idempotent: if all campaigns are already paused, returns empty list without error
- [ ] Unit tests mock analytics data; assert `CPA_SPIKE` alert is raised at exactly 300.1% threshold; assert no alert at 299.9%; assert `run_kill_switch` calls `pause_all_campaigns` exactly once per invocation; assert idempotency on already-paused campaigns

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + PRD anomaly bounds spec (2 KB) + HLD kill-switch section (1 KB) | ~2,625 |
| Core Source Code | `adapters/google_ads_adapter.py` (09) + `repositories/ledger_repo.py` (07) + `services/analytics_service.py` (10) | ~3,000 |
| Test Suites & Ticket Spec | This ticket + unit tests with boundary assertions | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~21,625 – 29,000** |

- **Peak Working Set:** ~29,000 tokens (14.5% of 200k ceiling)
- **Status:** 🟢 Optimal
