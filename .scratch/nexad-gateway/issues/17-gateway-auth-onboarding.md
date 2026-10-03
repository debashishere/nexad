# 17: Auth Middleware & Org Management Endpoints

**What to build:** `gateway/middleware/auth.py` — Bearer token validation that resolves a calling org from a `nx_live_...` API key, plus the onboarding endpoints an agency uses to register itself and connect its ad accounts. Also centralises all `/health/*` routes here. A new `api_keys` table (not in the original LLD) is added to the schema to store hashed tokens.

**Blocked by:** 02 — PostgreSQL Session Factory, 04 — Crypto Utilities, 05 — Org & Connection Repo

**Status:** ready-for-agent

- [ ] **Schema addition:** `api_keys` table added via Alembic migration: `id UUID PK`, `org_id UUID FK → organizations`, `key_hash VARCHAR(64) NOT NULL UNIQUE` (SHA-256 of the raw token), `label VARCHAR(100)`, `created_at TIMESTAMPTZ`, `last_used_at TIMESTAMPTZ`; raw token is never stored
- [ ] `gateway/middleware/auth.py` — FastAPI dependency `get_current_org(request) → Organization`: extracts `Bearer nx_live_...` from `Authorization` header, SHA-256 hashes it, looks up `api_keys` table, updates `last_used_at`, attaches org to `request.state.org`; returns HTTP 401 on miss
- [ ] `POST /orgs` — creates a new `Organization` (name, plan_tier); returns `{org_id, name, plan_tier}`
- [ ] `POST /orgs/{org_id}/api-keys` — generates a cryptographically random `nx_live_<32-byte-hex>` token, stores its SHA-256 hash in `api_keys`, returns the raw token **once** (never retrievable again)
- [ ] `POST /orgs/{org_id}/connections` — accepts `{platform_type, account_id, refresh_token}`; encrypts `refresh_token` via `core/crypto.encrypt_token()` before storing; returns `{connection_id, platform_type, account_id, status}`
- [ ] `GET /orgs/{org_id}/connections` — lists connections for an org (encrypted token fields excluded from response)
- [ ] `GET /health`, `GET /health/db`, `GET /health/redis` — centralised in `gateway/routers/health.py`; supersedes the stubs from tickets 02 and 03
- [ ] Unit tests: 401 on missing/invalid token; 401 on unknown key hash; valid token resolves correct org; `POST /orgs/{org_id}/connections` stores encrypted (not plaintext) token

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD schema section (4 KB) + HLD auth section (2 KB) | ~3,375 |
| Core Source Code | `core/crypto.py` (04) + `repositories/org_repo.py` (05) + `repositories/models.py` (02) | ~3,000 |
| Test Suites & Ticket Spec | This ticket + auth unit tests + endpoint integration tests | ~1,200 |
| Interactive Skill Phases | Single implementation pass | ~3,000 |
| Implementation & Test Runs | File writes, Alembic migration, pytest output | ~5,500 |
| **Total** | | **~25,075 – 33,500** |

- **Peak Working Set:** ~33,500 tokens (17% of 200k ceiling)
- **Status:** 🟢 Optimal
