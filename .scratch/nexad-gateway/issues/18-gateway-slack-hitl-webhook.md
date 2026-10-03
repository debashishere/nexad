# 18: Slack HITL Webhook Handler

**What to build:** `gateway/routers/hitl_webhook.py` — `POST /webhook/hitl-callback` receives the Slack interactive payload when a human clicks Approve or Reject on a HITL escalation card. Verifies the HMAC signature, resolves the pending ledger record, updates its outcome, and if approved dispatches the actual ad network mutation. This ticket closes the full HITL approval loop end-to-end.

**Blocked by:** 04 — Crypto Utilities, 07 — Audit Ledger Repo, 09 — Google Ads Write Adapter, 17 — Auth Middleware

**Status:** ready-for-agent

- [ ] `POST /webhook/hitl-callback` accepts `application/x-www-form-urlencoded` (Slack's interactive payload format); no Bearer auth — Slack is verified by HMAC only
- [ ] **Step 1 — Signature verification:** Extract `X-Slack-Request-Timestamp` and `X-Slack-Signature` headers; call `core/crypto.verify_hmac_signature(token=action_token, timestamp=ts, incoming_sig=sig, secret_key=settings.SLACK_SIGNING_SECRET)`; return HTTP 403 immediately on failure — no further processing
- [ ] **Step 2 — Replay guard:** Reject requests where `|now - timestamp| > 300 seconds` (5-minute replay window) before HMAC check
- [ ] **Step 3 — Resolve action:** Parse `action_token` and `action` (`approve`|`reject`) from payload; call `ledger_repo.record_hitl_outcome(ledger_id=action_token, status='approved'|'declined', approved_by=slack_user_id)`
- [ ] **Step 4 — Approved path:** Call `GoogleAdsWriteAdapter.apply_budget_mutation()` with the original params stored in the ledger's `request_payload`; update ledger `network_mutation_id` and `executed_at` on success
- [ ] **Step 5 — Response:** Return Slack-compatible JSON `{"response_type": "in_channel", "text": "✅ Budget mutation executed." | "❌ Mutation rejected."}` so the Slack card updates inline
- [ ] Entire handler is idempotent: if ledger row is already `approved` or `declined`, return 200 with a "already processed" message — no double-execution
- [ ] Unit tests: valid HMAC + approve → `record_hitl_outcome` called with `'approved'`; valid HMAC + reject → called with `'declined'`; invalid HMAC → 403; stale timestamp → 403; already-processed → 200 idempotent response

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD HITL webhook + HMAC spec (4 KB) + use case 2 sequence (3 KB) | ~3,625 |
| Core Source Code | `core/crypto.py` (04) + `repositories/ledger_repo.py` (07) + `adapters/google_ads_adapter.py` (09) | ~3,500 |
| Test Suites & Ticket Spec | This ticket + unit tests for all 6 HMAC/idempotency scenarios | ~1,200 |
| Interactive Skill Phases | Single implementation pass | ~3,000 |
| Implementation & Test Runs | File writes, pytest output | ~5,000 |
| **Total** | | **~25,325 – 33,750** |

- **Peak Working Set:** ~33,750 tokens (17% of 200k ceiling)
- **Status:** 🟢 Optimal
