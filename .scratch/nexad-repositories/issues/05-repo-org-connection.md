# 05: Organization & Ad Platform Connection Repository

**What to build:** `repositories/org_repo.py` — typed async query functions for the `organizations` and `ad_platform_connections` tables. Services resolve tenant context at the start of every firewall evaluation by calling these functions. Credential fields are returned encrypted; decryption is the caller's responsibility via `core/crypto.py`.

**Blocked by:** 02 — PostgreSQL Async Session Factory

**Status:** ready-for-agent

- [ ] `get_org_by_id(session, org_id: UUID) → Organization | None` — fetches org row; returns `None` if not found (callers raise `404`)
- [ ] `get_connection_for_account(session, org_id: UUID, platform_type: str, account_id: str) → AdPlatformConnection | None` — resolves the unique connection row matching the `uk_org_platform_account` constraint
- [ ] `create_org(session, name: str, plan_tier: str) → Organization` — inserts and returns new org
- [ ] `create_ad_connection(session, org_id, platform_type, account_id, encrypted_refresh_token, token_iv, token_tag) → AdPlatformConnection` — inserts a new connection row
- [ ] All functions are async, accept an `AsyncSession`, and do not commit — callers manage the transaction boundary
- [ ] Unit tests use `pytest-asyncio` + `AsyncMock` session; assert correct SQL filter expressions are applied
- [ ] Integration test (marked `@pytest.mark.integration`) inserts a real org + connection row and round-trips through all query functions

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD schema section (4 KB) + ADR-0001–0004 (2.5 KB) | ~3,500 |
| Core Source Code | `core/db.py` (ticket 02) + `repositories/models.py` (ticket 02) | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit + integration test stubs | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~20,900 – 28,000** |

- **Peak Working Set:** ~28,000 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
