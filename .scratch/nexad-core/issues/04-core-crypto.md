# 04: `core/` Crypto Utilities

**What to build:** `core/crypto.py` — three pure-Python utility functions with no DB or Redis dependency: AES-256-GCM encrypt/decrypt for credential storage, and HMAC-SHA256 signature verification for Slack HITL approval callbacks. Any service can import these without pulling in DB or Redis dependencies.

**Blocked by:** 01 — `core/` Config & Project Scaffold

**Status:** ready-for-agent

- [ ] `encrypt_token(plaintext: str, secret_key: bytes) → tuple[str, str, str]` returns `(ciphertext_b64, iv_hex, tag_hex)` using AES-256-GCM via the `cryptography` library
- [ ] `decrypt_token(ciphertext_b64: str, iv_hex: str, tag_hex: str, secret_key: bytes) → str` reverses the above; raises `InvalidToken` on tampered ciphertext
- [ ] `verify_hmac_signature(token: str, timestamp: str, incoming_sig: str, secret_key: str) → bool` implements the Slack signing formula `v0:{timestamp}:{token}` with `hmac.compare_digest` for timing-safe comparison — matching the LLD spec exactly
- [ ] `AES_SECRET_KEY` is read from `settings` as a 32-byte hex string and decoded once at module import; misconfigured key length raises `ValueError` with a clear message
- [ ] Unit tests cover: round-trip encrypt→decrypt returns original plaintext; tampered tag raises `InvalidToken`; correct HMAC returns `True`; wrong HMAC returns `False`; known test vectors for both AES and HMAC match expected outputs

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (7.5 KB) + LLD HMAC section (1 KB) | ~2,125 |
| Core Source Code | `core/config.py` from ticket 01 + new `core/crypto.py` | ~800 |
| Test Suites & Ticket Spec | This ticket + unit tests with known vectors | ~900 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~3,500 |
| **Total** | | **~18,325 – 24,000** |

- **Peak Working Set:** ~24,000 tokens (12% of 200k ceiling)
- **Status:** 🟢 Optimal
