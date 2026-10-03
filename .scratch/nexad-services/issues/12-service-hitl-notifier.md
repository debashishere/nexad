# 12: HITL Notifier Service

**What to build:** `services/hitl_notifier.py` — builds and posts the HMAC-signed Slack Block Kit approval card when the Budget Firewall escalates a mutation. The notifier is a pure side-effect service: it receives all data it needs from the caller, has no DB dependency, and returns a `bool` indicating whether Slack accepted the payload.

**Blocked by:** 04 — Crypto Utilities, 07 — Audit Ledger Repo (for `action_token`/`ledger_id`)

**Status:** ready-for-agent

- [ ] `trigger_slack_escalation(webhook_url, ledger_id, campaign_id, current_budget, proposed_budget, rationale, slack_signing_secret) → bool` — constructs the Block Kit card matching the LLD spec exactly (campaign ID, current budget, proposed budget, delta %, agent rationale, action token) and POSTs to `webhook_url` via `slack_sdk.WebhookClient`
- [ ] The Approve button payload encodes `action_token=str(ledger_id)` and a HMAC signature `v0:{timestamp}:{ledger_id}` generated via `core/crypto.verify_hmac_signature()` — the gateway's webhook handler will verify this on callback
- [ ] The Reject button payload encodes the same `action_token` with `action=reject`
- [ ] `SlackDeliveryError` is raised if the Slack webhook returns non-200; the firewall service catches this and still returns `ESCALATED_TO_HITL` (the ledger row is already written; Slack failure is non-fatal but logged)
- [ ] Card text is non-hallucinated: only numeric fields and the agent-provided `rationale` string are rendered; no LLM-generated copy
- [ ] Unit tests mock `slack_sdk.WebhookClient`; assert Block Kit payload structure matches expected schema; assert HMAC signature is present in button payloads; assert `SlackDeliveryError` on non-200 response

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD HITL card spec (3 KB) + use case 2 Slack flow (2 KB) | ~3,125 |
| Core Source Code | `core/crypto.py` (ticket 04) + Slack Block Kit schema reference | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit tests asserting Block Kit payload structure | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~20,625 – 27,500** |

- **Peak Working Set:** ~27,500 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
