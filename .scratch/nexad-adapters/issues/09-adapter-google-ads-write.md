# 09: Google Ads Write (Mutation) Adapter

**What to build:** Extends `adapters/google_ads_adapter.py` with a `GoogleAdsWriteAdapter` class that adds the single write operation the system is permitted to make: `apply_budget_mutation`. This function is intentionally thin — it contains no policy logic. It executes the mutation only when called, trusting that the Budget Firewall (ticket 11) has already cleared it. Returns a typed `MutationReceipt` for the audit ledger.

**Blocked by:** 08 — Google Ads Read Adapter

**Status:** ready-for-agent

- [ ] `GoogleAdsWriteAdapter` subclasses `GoogleAdsReadAdapter` — shares the same authenticated SDK client; no second auth initialisation
- [ ] `apply_budget_mutation(campaign_id: str, new_budget_micros: int, idempotency_key: str) → MutationReceipt` — calls `CampaignBudgetServiceClient.mutate_campaign_budgets()` using Google Ads API v17; passes `idempotency_key` as the SDK's request header to prevent duplicate execution at the API layer
- [ ] `MutationReceipt` is a `dataclass`: `resource_name: str`, `operation_id: str`, `executed_at: datetime`, `account_id: str`, `campaign_id: str`, `new_budget_micros: int`
- [ ] Function raises `GoogleAdsException` on API error and lets it propagate — callers (the firewall service) handle and record the error in the audit ledger
- [ ] `apply_budget_mutation` can only increase or decrease budget; any attempt to pass `new_budget_micros <= 0` raises `ValueError` before the API call is made
- [ ] Unit tests mock `CampaignBudgetServiceClient`; assert `MutationReceipt` fields are populated from the mock response; assert `ValueError` on non-positive budget; assert idempotency key is forwarded in the request headers
- [ ] No integration test against live Google Ads API — `pytest.mark.skip` with note pointing to manual sandbox

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD write pipeline section (4 KB) + HLD dual-gating diagram (2 KB) | ~3,375 |
| Core Source Code | `adapters/google_ads_adapter.py` from ticket 08 (the read adapter to extend) | ~2,000 |
| Test Suites & Ticket Spec | This ticket + unit tests with mocked write client | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~3,500 |
| **Total** | | **~20,775 – 27,500** |

- **Peak Working Set:** ~27,500 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
