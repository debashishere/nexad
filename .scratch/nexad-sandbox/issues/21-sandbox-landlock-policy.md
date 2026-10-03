# 21: OpenShell Phase 2 — Landlock Policy & Credential-Blind Egress

**What to build:** `sandbox/policies/nexad-agent-policy.yaml` — the declarative Landlock filesystem confinement and network egress rules that enforce credential blindness and outbound filtering when `NEXAD_SANDBOX_ENABLED=true`. When the flag is false this ticket's files are present on disk but have no runtime effect. Includes an integration test suite that only runs on Linux and verifies the kernel-level enforcement works correctly.

**Blocked by:** 20 — OpenShell Foundation & Stub Mode

**Status:** ready-for-agent

- [ ] `sandbox/policies/nexad-agent-policy.yaml` — exactly matching the open-shell-int.md spec:
  - `filesystem.read_only: [/app, /usr, /lib]`
  - `filesystem.read_write: [/tmp/agent_run]`
  - `filesystem.deny: [/etc/shadow, /proc/kcore]`
  - `network.default_action: deny`
  - `network.egress.allow: [{host: "googleads.googleapis.com", ports: [443]}, {host: "nexad-internal-api.internal", ports: [8080]}]`
  - `process.allow_fork: true`, `process.deny_ptrace: true`
- [ ] `sandbox/manager.py` updated (from ticket 20): real `provision_sandbox()` registers the policy YAML via OpenShell Gateway API before returning the `SandboxHandle`
- [ ] `sandbox/verifier.py` — `verify_egress_isolation(handle: SandboxHandle) → bool` attempts an outbound HTTP request from within the sandbox to a non-whitelisted host (`https://example.com`) and asserts it is refused; returns `True` if isolation is confirmed; only callable when `handle.is_stub=False`
- [ ] `sandbox/verifier.py` — `verify_filesystem_isolation(handle: SandboxHandle) → bool` attempts to `open('/etc/shadow')` inside the sandbox and asserts `EPERM` is raised
- [ ] Integration tests marked `@pytest.mark.linux_only` and `@pytest.mark.openShell` — skipped automatically when `NEXAD_SANDBOX_ENABLED=false` or when `sys.platform != 'linux'`; CI pipeline on EC2 runs these with `NEXAD_SANDBOX_ENABLED=true`
- [ ] `Makefile` (or `justfile`) target `test-sandbox` runs only the `openShell`-marked tests: `pytest -m openShell tests/`
- [ ] Unit tests (platform-independent): assert `verify_egress_isolation` raises `RuntimeError` when called on a stub handle; assert policy YAML is valid against the OpenShell schema

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (8 KB) + ADR-0002 + ADR-0005 + open-shell-int.md policy spec (4 KB) | ~4,250 |
| Core Source Code | `sandbox/manager.py` (ticket 20) + `sandbox/provider_profiles/google-ads-provider.yaml` | ~1,500 |
| Test Suites & Ticket Spec | This ticket + linux-only integration test stubs | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output (unit only; linux tests skipped locally) | ~4,000 |
| **Total** | | **~21,750 – 29,000** |

- **Peak Working Set:** ~29,000 tokens (14.5% of 200k ceiling)
- **Status:** 🟢 Optimal
