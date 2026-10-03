# 22: Test Agent — Scripted MCP Client Harness

**What to build:** `test_agent/client.py` — a typed async MCP client that connects to the running NexAd server, confirms all tools are available, and exposes clean Python wrappers for each tool. `test_agent/fixtures.py` seeds the database with a test org, connection, policy, and API key so scenario tests start from a known, reproducible state.

**Blocked by:** 16 — MCP Server Bootstrap & Schema Sanitizer

**Status:** ready-for-agent

- [ ] `test_agent/client.py` — `NexAdTestClient` class:
  - `connect(server_url: str, api_key: str) → None` — opens MCP session via `mcp.ClientSession`, calls `tools/list`, asserts all three tools (`query_campaign_analytics`, `adjust_campaign_budget`, `commit_sanctioned_action`) are present; raises `AssertionError` if any are missing
  - `query_analytics(account_id: str, timeframe: str) → dict` — typed wrapper for `tools/call query_campaign_analytics`
  - `adjust_budget(account_id: str, campaign_id: str, new_budget_micros: int, rationale: str) → dict` — typed wrapper for `tools/call adjust_campaign_budget`; auto-generates `idempotency_key`
  - `commit_action(action_token: str) → dict` — typed wrapper for `tools/call commit_sanctioned_action`
  - `close() → None` — cleanly closes the MCP session
- [ ] `test_agent/fixtures.py` — `seed_test_org(session) → tuple[Organization, AdPlatformConnection, str]`:
  - Creates org with `plan_tier='agency_growth'`
  - Creates a `google_ads` connection with a test `account_id='TEST-001'` and encrypted placeholder refresh token
  - Seeds a `SafetyPolicy` with 15% cap, 10 mutations/day via `seed_default_policy` fixture from ticket 06
  - Generates and returns a raw `nx_live_...` API key for auth
- [ ] `test_agent/fixtures.py` — `seed_test_campaigns(redis_pool, account_id) → None` seeds two Redis campaign spend keys: one at 0% of cap (auto-approve candidate), one at 90% of cap (HITL escalation candidate)
- [ ] `pytest` fixture `nexad_test_client` spins up the FastAPI + FastMCP server in-process via `asyncio`, seeds the DB, yields a connected `NexAdTestClient`, and tears down after the test
- [ ] Unit test: `connect()` raises `AssertionError` when a tool is missing from `tools/list`

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (8 KB) + ADR-0001 (test agent scope) + LLD MCP tool schemas (3 KB) | ~3,500 |
| Core Source Code | `mcp_server/server.py` (16) + `repositories/` fixtures from 05, 06 + `core/db.py` (02) | ~3,000 |
| Test Suites & Ticket Spec | This ticket + fixture unit test | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, in-process server startup, pytest output | ~5,000 |
| **Total** | | **~23,400 – 31,250** |

- **Peak Working Set:** ~31,250 tokens (16% of 200k ceiling)
- **Status:** 🟢 Optimal
