# 08: Google Ads Read Adapter

**What to build:** `adapters/google_ads_adapter.py` — a `GoogleAdsReadAdapter` class that wraps the `google-ads` Python SDK for read-only operations. The adapter receives an already-decrypted refresh token from the calling service (decryption is the service layer's responsibility via `core/crypto.py`). It exposes typed read methods the analytics service and firewall evaluator will consume.

**Blocked by:** 01 — Config & Project Scaffold, 05 — Org & Connection Repository

**Status:** ready-for-agent

- [ ] `GoogleAdsReadAdapter(developer_token, refresh_token, customer_id)` — initialises the `GoogleAdsClient` from the SDK using OAuth2 credentials built from the constructor args; no secrets read directly from env (caller decrypts and passes in)
- [ ] `get_campaign_budget_micros(campaign_id: str) → int` — fetches the current daily budget in micros for a specific campaign; used by the firewall to compute the delta percentage
- [ ] `list_campaigns(account_id: str) → list[CampaignSummary]` — runs a GAQL query returning `campaign.id`, `campaign.name`, `campaign.status`, `metrics.cost_micros`, `metrics.conversions`, `metrics.cost_per_conversion` for the last 7 days; returns a typed `CampaignSummary` dataclass list
- [ ] `run_gaql_query(query: str) → list[dict]` — raw GAQL runner; strips the query of any non-SELECT statements before execution (injection guard at the adapter boundary)
- [ ] `CampaignSummary` is a `dataclass` (not a DB model): `campaign_id`, `name`, `status`, `cost_micros`, `conversions`, `cost_per_conversion_micros`
- [ ] Unit tests mock the `GoogleAdsClient` SDK entirely — assert correct GAQL is constructed, `get_campaign_budget_micros` returns an `int`, non-SELECT queries are rejected
- [ ] No integration test against real Google Ads API — use `pytest.mark.skip` with a note pointing to manual sandbox testing

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD adapter section (3 KB) + HLD adapter diagram (2 KB) | ~3,125 |
| Core Source Code | `core/config.py` (ticket 01) + `repositories/models.py` (ticket 02) + `core/crypto.py` (ticket 04) | ~2,000 |
| Test Suites & Ticket Spec | This ticket + unit tests with mocked SDK | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output with mocked client | ~4,000 |
| **Total** | | **~21,125 – 28,000** |

- **Peak Working Set:** ~28,000 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
