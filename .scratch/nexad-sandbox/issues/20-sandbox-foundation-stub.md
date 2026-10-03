# 20: OpenShell Foundation — Gateway Daemon, Provider Profiles & Stub Mode

**What to build:** `sandbox/manager.py` — the single entry point for all sandbox lifecycle operations. Implements a clean `NEXAD_SANDBOX_ENABLED` feature flag: when `false` (local macOS dev), returns a no-op `SandboxHandle` with `is_stub=True` and the full stack runs without kernel isolation. When `true` (Linux CI/prod), provisions a real OpenShell sandbox and registers the Google Ads Provider Profile. Every caller receives the same `SandboxHandle` interface regardless of mode.

**Blocked by:** 01 — Config & Project Scaffold

**Status:** ready-for-agent

- [ ] `SandboxHandle` dataclass: `sandbox_id: str`, `org_id: UUID`, `connection_id: UUID`, `status: Literal['active','terminated','stub']`, `is_stub: bool`
- [ ] `sandbox/manager.py` reads `settings.NEXAD_SANDBOX_ENABLED: bool` (defaults `False`):
  - **Stub path (`False`):** `provision_sandbox(org_id, connection_id) → SandboxHandle` returns `SandboxHandle(sandbox_id=str(uuid4()), is_stub=True, status='stub')` immediately; `teardown_sandbox(handle)` is a no-op
  - **Real path (`True`):** calls OpenShell Gateway gRPC API `CreateSandbox(policy_ref='nexad-agent-restricted')`, waits for `status=READY`, returns `SandboxHandle(sandbox_id=response.id, is_stub=False, status='active')`
- [ ] `sandbox/provider_profiles/google-ads-provider.yaml` — exactly matching the open-shell-int.md spec: `kind: ProviderProfile`, `type: http-bearer`, `allowed_endpoints: [{host: "googleads.googleapis.com", port: 443}]`, credential injected from `GOOGLE_ADS_OAUTH_TOKEN` env var
- [ ] `docker-compose.yml` updated (from ticket 01): adds an `openshell-gateway` service behind a `profiles: ["openShell"]` Docker Compose profile — opt-in via `docker compose --profile openShell up`; omitted by default for local dev
- [ ] `NEXAD_SANDBOX_ENABLED=false` is the default in `.env.example` with a clear comment: `# Set to true only on Linux hosts with OpenShell Gateway installed (see ADR-0005)`
- [ ] Unit tests: `provision_sandbox` with `NEXAD_SANDBOX_ENABLED=false` returns `is_stub=True` without any network call; with `true` calls the gRPC client (mocked); `teardown_sandbox` on stub handle is a no-op

---

### Context-ETA (for the implementing agent)

> **Active model:** Claude Sonnet 4.6 · **Ceiling:** 200,000 tokens · **Workflow:** Direct Implementation (1.5× – 2.0×)

| Component | Scope | ~Tokens |
|:---|:---|:---|
| System & Skill Instructions | Base prompt + tool definitions | ~9,000 |
| Domain Model & History | CONTEXT.md (8 KB) + ADR-0002 (OpenShell) + ADR-0005 (stub) + open-shell-int.md provider profile spec (3 KB) | ~4,000 |
| Core Source Code | `core/config.py` (01) + `docker-compose.yml` (01, to extend) | ~1,500 |
| Test Suites & Ticket Spec | This ticket + unit tests for both stub and real paths | ~1,000 |
| Interactive Skill Phases | Single implementation pass | ~2,000 |
| Implementation & Test Runs | File writes, pytest output | ~4,000 |
| **Total** | | **~21,500 – 28,750** |

- **Peak Working Set:** ~28,750 tokens (14% of 200k ceiling)
- **Status:** 🟢 Optimal
