# 14: MCP Tool — `query_campaign_analytics`

**What to build:** `mcp_server/tools/analytics.py` — a `@mcp.tool()` decorated function exposing campaign performance data to any MCP-compatible agent. The tool resolves tenant context from the Bearer token, delegates entirely to `analytics_service`, and returns structured JSON. Agents call this tool first to understand the current state of an account before proposing mutations.

**Blocked by:** 10 — Analytics Service

**Status:** ready-for-agent

- [ ] `QueryAnalyticsInput(BaseModel)`: `account_id: str`, `timeframe: Literal['LAST_7_DAYS','LAST_14_DAYS','LAST_30_DAYS']` (defaults to `LAST_7_DAYS`)
- [ ] `@mcp.tool() async def query_campaign_analytics(params: QueryAnalyticsInput) -> dict` — resolves `AdPlatformConnection` for the `account_id` from DB, calls `analytics_service.get_campaign_performance()`, serialises `CampaignSummary` list to dict
- [ ] Tool response schema: `{"campaigns": [{"campaign_id": str, "name": str, "status": str, "cost_micros": int, "conversions": float, "cost_per_conversion_micros": int}]}`
- [ ] Returns `{"error": "ACCOUNT_NOT_FOUND"}` (not a Python exception) when `account_id` has no matching connection — MCP tools must never raise unhandled exceptions to the agent
- [ ] Unit tests mock `analytics_service` and `org_repo`; assert correct tool response schema on success; assert `ACCOUNT_NOT_FOUND` error dict on missing account

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD MCP server section (3 KB) + use case 2 analytics flow (2 KB) | ~3,125 |
| Core Source Code | `services/analytics_service.py` (10) + `repositories/org_repo.py` (05) + `repositories/models.py` | ~2,500 |
| Test Suites & Ticket Spec | This ticket + unit tests | ~800 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~3,500 |
| **Total** | | **~20,925 – 28,000** |

- **Peak Working Set:** ~28,000 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
