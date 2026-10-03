# 15: MCP Tools — `adjust_campaign_budget` & `commit_sanctioned_action`

**What to build:** `mcp_server/tools/budget.py` — two tightly coupled MCP tools that form the complete write cycle. `adjust_campaign_budget` proposes a mutation through the firewall (which may auto-execute or escalate to HITL). `commit_sanctioned_action` allows an agent to poll for and acknowledge a previously HITL-approved action token — completing the async approval loop programmatically.

**Blocked by:** 11 — Budget Firewall Service, 12 — HITL Notifier Service

**Status:** ready-for-agent

- [ ] `BudgetAdjustmentInput(BaseModel)`: `account_id: str`, `campaign_id: str`, `new_daily_budget_micros: int = Field(gt=0)`, `justification_rationale: str = Field(min_length=10, max_length=500)`, `idempotency_key: str = Field(default_factory=lambda: str(uuid4()))` — exactly matching the LLD spec
- [ ] `@mcp.tool() async def adjust_campaign_budget(params: BudgetAdjustmentInput) -> dict` — resolves connection, calls `firewall_service.evaluate_and_route()`, returns `FirewallResult` serialised to dict with keys: `status`, `message`, `action_token`, `requires_human_approval`
- [ ] `CommitSanctionedActionInput(BaseModel)`: `action_token: str`
- [ ] `@mcp.tool() async def commit_sanctioned_action(params: CommitSanctionedActionInput) -> dict` — queries `ledger_repo.get_pending_hitl_actions()` for the token; if `hitl_status='approved'` (human already clicked), dispatches the write via `write_adapter.apply_budget_mutation()`, records final ledger outcome, returns `{"status": "COMMITTED", "execution_receipt": {...}}`; if still pending returns `{"status": "PENDING_HUMAN_APPROVAL"}`
- [ ] Both tools return structured error dicts (never raise) for: `ACCOUNT_NOT_FOUND`, `POLICY_VIOLATION`, `DUPLICATE_REQUEST`
- [ ] Unit tests cover all `FirewallResult` states; `commit_sanctioned_action` returns `PENDING` on pending token and `COMMITTED` on approved token

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD MCP server + firewall sequence (7 KB) | ~3,625 |
| Core Source Code | `services/firewall_service.py` (11) + `repositories/ledger_repo.py` (07) + `adapters/google_ads_adapter.py` (09) | ~4,000 |
| Test Suites & Ticket Spec | This ticket + unit tests for all firewall result states | ~1,200 |
| Interactive Skill Phases | Single implementation pass | ~3,000 |
| Implementation & Test Runs | File writes, pytest output | ~5,000 |
| **Total** | | **~25,825 – 34,500** |

- **Peak Working Set:** ~34,500 tokens (17% of 200k ceiling)
- **Status:** 🟢 Optimal
