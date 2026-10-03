# 16: MCP Server Bootstrap & Adversarial Schema Sanitizer

**What to build:** `mcp_server/server.py` — the `FastMCP` server instance with all tools registered, plus the adversarial schema sanitizer middleware (Use Case 3 from the use case spec). After this ticket, running the server and calling `tools/list` returns all three tools correctly. Bearer token auth lives in the gateway layer (ticket 18), not here.

**Blocked by:** 14 — `query_campaign_analytics` tool, 15 — `adjust_campaign_budget` & `commit_sanctioned_action` tools

**Status:** ready-for-agent

- [ ] `mcp_server/server.py` creates `mcp = FastMCP("NexAd-Execution-Engine")` and imports all tools from `mcp_server/tools/analytics.py` and `mcp_server/tools/budget.py` — no tool logic lives in `server.py` itself
- [ ] `mcp_server/sanitizer.py` — `sanitize_tool_params(raw_params: dict, schema: dict) → dict` adversarial sanitizer:
  - Strips HTML/Markdown comments (`<!-- ... -->`, `/* ... */`)
  - Rejects any string field containing control sequences: `<|im_start|>`, `system:`, `role: assistant`, `\x00`–`\x1f` control chars
  - Accepts only fields declared in the tool's Pydantic schema — unknown properties are dropped silently
  - Returns the cleaned dict; raises `InjectionAttemptError` (logged as security event) if control sequences are found
- [ ] Sanitizer is applied as a FastMCP middleware hook on every `tools/call` invocation before the tool handler executes
- [ ] `InjectionAttemptError` is caught at the server level and returns `{"error": "INVALID_TOOL_PARAMS", "detail": "Injection attempt detected"}` to the calling agent — never a stack trace
- [ ] `tools/list` response includes all three tools with correct input schemas
- [ ] Unit tests for sanitizer: HTML comment stripped; control sequence raises `InjectionAttemptError`; unknown property dropped; clean input passes through unchanged
- [ ] Integration test: start the FastMCP server in-process, call `tools/list` via the MCP Python SDK, assert all three tools are present with correct schemas

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + use case 3 injection spec (3 KB) + HLD sanitizer section (2 KB) | ~3,125 |
| Core Source Code | `mcp_server/tools/analytics.py` (14) + `mcp_server/tools/budget.py` (15) | ~2,500 |
| Test Suites & Ticket Spec | This ticket + sanitizer unit tests + in-process integration test | ~1,200 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output including in-process server test | ~5,000 |
| **Total** | | **~22,825 – 30,500** |

- **Peak Working Set:** ~30,500 tokens (15% of 200k ceiling)
- **Status:** 🟢 Optimal
