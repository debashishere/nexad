# Project NexAd — Domain Glossary & Shared Context

> Living document. Updated as architectural decisions crystallize.

---

## Core Product Identity

**NexAd** is an enterprise-grade **Agentic Ad Mediation & Execution Gateway**.  
Its primary product is the **B2B Agency Write-Execution Firewall** — a safety-gated middleware layer that allows autonomous LLM agents to read advertising data and propose budget/bid mutations across Google Ads and Meta, subject to deterministic policy enforcement and Human-in-the-Loop (HITL) approval workflows.

A **Simple Consumer Test Agent** is included in scope as an internal integration harness to validate the MCP gateway and tool contracts before production — it is *not* a production product.

_Avoid_: "consumer platform", "two-sided marketplace", "merchant negotiation engine" as product descriptors for the MVP.

### Out of MVP Scope
- **Ad Creative Generation** (Image / Text / SVG creation, CDN management, creative approval) — future phase.
- **Competitor Research / Reinforcement Learning** — future phase.
- **Consumer Agent Commercial Incentive Negotiation** (Use Case 1 in the use case spec) — future phase.
- **Meta Marketing API Adapter** — Month 4–8 per GTM roadmap.
- **Custom DSP/SSP Adapters** — future phase.
- **OpenShell Phase 3 (Formal Policy Prover + CI/CD mutation validation)** — post-MVP.
- **Teams & Web Dashboard HITL channels** — Slack is the sole MVP HITL delivery channel.
- **TypeScript/Node.js Gateway & Next.js Dashboard** — V2; MVP is a Python-only monolith.
- **Kafka / Redpanda audit event stream** — direct PostgreSQL `execution_audit_ledger` writes for MVP; Kafka added in Phase 2 as SOC2 SIEM export pipeline.
- **ECS Fargate / GCP Cloud Run** — MVP deploys on ECS on EC2 (AL2023) for OpenShell kernel access.

---

## Domain Terms

### Agency
A performance marketing agency managing multiple client ad accounts. The primary paying customer of NexAd. Mapped to the `organizations` table.  
_Avoid_: "tenant" (use "organization" in data models; "agency" in product/UX copy).

### Ad Account / Ad Platform Connection
A single advertiser account on a specific ad network (e.g., one Google Ads Customer ID or one Meta Ad Account ID), linked to an Organization and secured with encrypted credentials.  
_Avoid_: "campaign account" (ambiguous with campaign entity).

### Campaign
A named advertising campaign within an Ad Account on a specific ad network. The atomic unit of budget and bid management.

### Mutation / Write Action
Any API call that modifies state on an ad network — including budget adjustments, bid changes, and campaign status changes. All mutations traverse the Safety Firewall.  
_Avoid_: "update", "change" (use "mutation" in code and system docs for precision).

### Safety Firewall / Budget Firewall
The deterministic, LLM-independent policy engine that evaluates every proposed mutation against spend velocity limits, absolute caps, and anomaly bounds before allowing execution or escalating to HITL.  
_Avoid_: "guardrails" (too vague); use "firewall" or "policy engine".

### HITL (Human-in-the-Loop) Gateway
The escalation subsystem that generates cryptographically signed approval cards (delivered via Slack/Teams/Web) when a proposed mutation exceeds automated policy thresholds. Requires a human operator's HMAC-signed approval before the mutation is dispatched.  
_Avoid_: "approval flow" (too generic); use "HITL escalation" or "HITL gateway".

### Action Token
A short-lived, cryptographically signed identifier representing a single pending HITL-escalated mutation. Used to correlate the Slack approval click back to the exact pending database record.  
_Avoid_: "approval token", "auth token" (collision with API auth bearer tokens).

### Audit Ledger
The immutable PostgreSQL log of every agent action, firewall decision, HITL escalation, and mutation outcome. Append-only; never updated in place.  
_Avoid_: "log table", "event log" (use "audit ledger" to signal immutability intent).

### Spend Velocity Limit
The maximum percentage by which a campaign's daily budget may be increased in a single autonomous mutation (default: 15%). Enforced atomically via Redis Lua scripts.  
_Avoid_: "rate limit" (collision with API rate limiting); use "velocity limit" or "velocity cap".

### MCP (Model Context Protocol)
The wire protocol (JSON-RPC 2.0 over SSE or stdio) through which LLM agents discover and invoke NexAd's tools. NexAd acts as an MCP *server*; agent runtimes are MCP *clients*.

### FastMCP
The Python library used to implement NexAd's MCP server endpoints. The execution engine layer.

### OpenShell Sandbox
An NVIDIA OpenShell kernel-isolated runtime (using Landlock LSM + eBPF) that wraps every autonomous ad agent execution. Provides credential blindness (agents send unauthenticated requests; OpenShell injects credentials at the kernel egress boundary), outbound network filtering (only whitelisted ad-network endpoints allowed), and filesystem confinement. In scope for MVP.  
_Avoid_: "container", "Docker sandbox" when referring to the agent execution boundary — NexAd uses OpenShell, not plain containers.

### OpenShell Provider Profile
A declarative YAML definition registered with the OpenShell Gateway Daemon that maps an ad network credential (Google Ads OAuth token, Meta access token) to a set of approved hostnames. Agents inside the sandbox never receive the raw token.

### OpenShell Policy Prover
The formal verification component of OpenShell that mathematically validates agent policy changes against safety invariants before allowing execution. Flags unverified transitive access paths to the HITL gateway.

### SandboxHandle
A typed object returned by `sandbox/manager.py` representing an active (or stub) execution environment for an agent. Contains `sandbox_id`, `status`, and `is_stub: bool`. When `NEXAD_SANDBOX_ENABLED=false`, `is_stub` is `True` and no kernel isolation is applied.

### `NEXAD_SANDBOX_ENABLED`
Environment flag controlling whether the real OpenShell kernel sandbox is used (`true` — Linux/CI/prod only) or a no-op stub (`false` — local macOS development). Not a test mock; a permanent environment-capability split. See ADR-0005.

### Simple Consumer Test Agent
A deterministic scripted Python `asyncio` MCP client used during development and QA to exercise NexAd's full tool contract (read analytics → propose mutation → trigger HITL escalation → verify approval flow) with fixed, reproducible inputs and assertable outputs. Uses the `mcp` Python SDK directly — no LangGraph, CrewAI, or LLM inference dependency. **Not a production product.**  
_Avoid_: "demo agent", "mock agent" (it must exercise real code paths, not stubs); "autonomous agent" (it is scripted and deterministic, not LLM-driven).

---

## MVP Package Layout (Python Monorepo)

```
nexad/
├── mcp_server/         # FastMCP tool definitions — MCP protocol controllers
├── gateway/            # FastAPI app — auth middleware, Slack HITL webhook callbacks
├── services/           # Business logic — firewall evaluation, HITL notifier, analytics
├── adapters/           # Google Ads API adapter (sole network for MVP)
├── repositories/       # Data access — PostgreSQL queries (audit ledger, policies, orgs)
├── sandbox/            # OpenShell lifecycle — sandbox provisioning, Provider Profiles, policy.yaml
├── core/               # Shared infra — Redis client, DB session, config, crypto utils
├── test_agent/         # Simple Consumer Test Agent — deterministic scripted MCP client
└── tests/              # pytest suite
```

**Package boundary rules** (from Interfaces.md):
- Business logic lives in `services/`
- Data & DB manipulation lives in `repositories/`
- OpenShell sandbox creation & execution lives in `sandbox/`
- MCP tool definitions (controllers) live in `mcp_server/`
- No cross-cutting imports: `adapters/` and `sandbox/` never import from each other

---

*Last updated: 2026-10-02*
