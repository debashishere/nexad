# 10: Analytics Service

**What to build:** `services/analytics_service.py` — the single entry point for all read-only ad performance data. Decrypts the connection's refresh token, builds a `GoogleAdsReadAdapter`, executes the GAQL query, and returns structured `CampaignSummary` results. MCP tools and the anomaly detector call only this function — never the adapter directly.

**Blocked by:** 08 — Google Ads Read Adapter

**Status:** ready-for-agent

- [ ] `get_campaign_performance(account_id: str, connection: AdPlatformConnection) → list[CampaignSummary]` — decrypts `connection.encrypted_refresh_token` via `core/crypto.decrypt_token()`, instantiates `GoogleAdsReadAdapter`, calls `list_campaigns()`, returns results
- [ ] `get_campaign_budget(account_id: str, campaign_id: str, connection: AdPlatformConnection) → int` — decrypts token, calls `get_campaign_budget_micros()`; used by the firewall service to fetch current budget before delta computation
- [ ] Both functions are `async` and accept a pre-fetched `AdPlatformConnection` — they do not query the DB themselves (caller fetches connection from `org_repo`)
- [ ] `InvalidCredentialsError` is raised (not propagated raw `GoogleAdsException`) when the decrypted token is rejected by the SDK — allows callers to return a clean `401` without leaking SDK internals
- [ ] Unit tests mock `GoogleAdsReadAdapter` and `core/crypto.decrypt_token`; assert `InvalidCredentialsError` is raised on bad token; assert `CampaignSummary` list is returned on success

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD analytics section (2 KB) + use case 2 (3 KB) | ~3,125 |
| Core Source Code | `core/crypto.py` (ticket 04) + `adapters/google_ads_adapter.py` (ticket 08) + `repositories/models.py` | ~2,500 |
| Test Suites & Ticket Spec | This ticket + unit tests | ~800 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~3,500 |
| **Total** | | **~20,925 – 28,000** |

- **Peak Working Set:** ~28,000 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
