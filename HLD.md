High-Level Design (HLD): Project NexAd

System: Enterprise Agentic Ad Mediation & Execution Gateway

Document Version: 1.0.0

Classification: Technical Architecture Specification

1. System Overview & Architectural Topology

Project NexAd is structured as a decoupled, multi-tier distributed system. The platform exposes standard Model Context Protocol (MCP) endpoints to autonomous agents (Anthropic Claude, OpenAI, custom enterprise frameworks) while proxying, validating, and rate-limiting write operations to advertising ad networks (Google Ads, Meta Marketing API, programmatic DSPs).

                      ┌────────────────────────────────────────────────────────┐
                      │              AGENT RUNTIMES / MCP CLIENTS              │
                      │   (Claude Desktop, Custom LangGraph, Enterprise Bots)  │
                      └──────────────────────────┬─────────────────────────────┘
                                                 │ Standard MCP / JSON-RPC
                                                 │ (SSE or stdio over mTLS)
                                                 ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ INGRESS & GATEWAY SUBSYSTEM (TypeScript / Node.js 20+ Fastify)                                                 │
│                                                                                                                │
│   ┌───────────────────────────┐      ┌───────────────────────────┐      ┌──────────────────────────────────┐   │
│   │   Auth & Client Tenant    │ ---> │  Schema Validation & Sanitizer   │ ---> │   MCP Session / Tool Router      │   │
│   │   Token Verification      │      │  (Anti-Prompt-Injection)  │      │   Dispatcher                     │   │
│   └───────────────────────────┘      └───────────────────────────┘      └────────────────┬─────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┼─────────────────────────────┘
                                                                                   │
                                           ┌───────────────────────────────────────┴────────────────────────┐
                                           │ Read-Only Queries (GAQL, Metrics)     │ Mutations / Write Actions      │
                                           ▼                                       ▼
┌──────────────────────────────────────────────────────────────┐ ┌────────────────────────────────────────────────┐
│ ANALYTICS RETRIEVAL WORKER                                   │ │ SAFETY FIREWALL & HITL BROKER (Python 3.12)    │
│ (Stateless Python Service)                                   │ │                                                │
│                                                              │ │  ┌──────────────────────────────────────────┐  │
│  • Google Ads Query Language (GAQL) Runner                   │ │  │ Deterministic Budget & Velocity Evaluator│  │
│  • Meta Graph Reporting Engine                               │ │  └────────────────────┬─────────────────────┘  │
│  • Token Budget Optimization / Context Truncator             │ │                       │                        │
└──────────────────────────────┬───────────────────────────────┘ │  ┌────────────────────▼─────────────────────┐  │
                               │                                 │  │ HITL Escalation Router (Slack/Teams/App) │  │
                               │                                 │  └────────────────────┬─────────────────────┘  │
                               │                                 └───────────────────────┼────────────────────────┘
                               │                                                         │ Approved Mutations
                               ▼                                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ EXECUTION & INTEGRATION ADAPTERS (Python 3.12 + Google Ads / Meta SDKs)                                        │
│                                                                                                                │
│   ┌───────────────────────────┐      ┌───────────────────────────┐      ┌──────────────────────────────────┐   │
│   │   Google Ads API Adapter  │      │  Meta Marketing API Engine│      │   Programmatic OpenDirect Adapter│   │
│   │   (REST v17 / gRPC)       │      │  (Graph API v20.0)        │      │   (AAMP / JSON-LD Engine)        │   │
│   └─────────────┬─────────────┘      └─────────────┬─────────────┘      └────────────────┬─────────────────┘   │
└─────────────────┼──────────────────────────────────┼─────────────────────────────────────┼─────────────────────┘
                  │                                  │                                     │
                  ▼                                  ▼                                     ▼
        Google Ads Services                Meta Graph Services                     DSP / Ad Exchanges

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────
PERSISTENCE & EVENT FABRIC:
  • Redis Cluster: Real-time velocity counters, idempotency keys, atomic spend trackers.
  • PostgreSQL 16: Tenant accounts, API credentials (AES-256-GCM), immutable audit trails, policy rules.
  • Apache Kafka / Redpanda: Asynchronous audit event stream for SOC2 telemetry.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────


2. Ingress & Security Boundary

2.1 The Agent-to-Gateway Interface

Agents interface with NexAd via JSON-RPC 2.0 over Server-Sent Events (SSE) or WebSockets conforming strictly to the Model Context Protocol (MCP) standard.

Agent Client                  NexAd Ingress               Safety Sandbox
    │                                │                            │
    │── 1. tools/list ──────────────>│                            │
    │<── 2. Available Tool Registry ─│                            │
    │                                │                            │
    │── 3. tools/call (Action) ─────>│                            │
    │                                │── 4. Structural Schema ───>│
    │                                │      Validation & Scrub    │
    │                                │<── 5. Cleaned Payload ─────│


Token Authentication: Requests must present a Bearer API Token (nx_live_...) mapped to an active Organization and Tenant Workspace.

Schema Scrubbing (Indirect Injection Sanitizer): Incoming tool parameters are strictly parsed through explicit Pydantic/JSON schemas. Any fields containing control sequences (e.g., system:, <|im_start|>, or natural language directives embedded inside numeric or enum slots) are rejected at the edge before context compilation.

3. The Write-Execution Pipeline & Dual-Gating

Every mutation (budget_update, bid_adjustment, campaign_status_change) traverses a two-tier evaluation gate:

[Agent Action Received]
          │
          ▼
┌───────────────────┐
│ Tier 1: Automated │  Rule: Is $\Delta \text{Budget} \le 15\%$ AND Cumulative Daily $\le \text{MaxCap}$?
│ Policy Firewall   │
└─────────┬─────────┘
          │
          ├─────────────────────────┐
          │ (Passes Auto-Threshold)  │ (Exceeds Auto-Threshold or Anomaly Detected)
          ▼                         ▼
┌───────────────────┐     ┌────────────────────────────────────────────────────────┐
│ Immediate Atomic  │     │ Tier 2: HITL Escalation Queue                          │
│ API Execution     │     │  • Generate cryptographically signed Action Token      │
└───────────────────┘     │  • Push interactive card to Slack/Teams/Web            │
                          └──────────────────────────┬─────────────────────────────┘
                                                     │
                                            [Human Operator Signs]
                                                     │
                                                     ▼
                                          ┌───────────────────────┐
                                          │ Deterministic Dispatch│
                                          │ to Ad Network APIs    │
                                          └───────────────────────┘


4. Scalability, Latency & Reliability SLAs

Read Queries (Reporting/GAQL): SLA $P_{95} \le 1200\text{ ms}$ (dominated by upstream Google/Meta API response times). Cached analytical reports leverage Redis TTL to serve repeated agent queries in $< 45\text{ ms}$.

Write Actions (Synchronous validation + Queue): SLA $P_{99} \le 150\text{ ms}$.

High Availability: Ingress nodes and Python execution workers are stateless containers orchestrated via AWS ECS Fargate across multiple Availability Zones with automatic scale-out triggers based on CPU utilization ($>70\%$) and active SSE connection volume.

Idempotency Guarantee: Every write mutation accepts a mandatory idempotency_key (UUIDv4) cached in Redis for 24 hours to prevent duplicate executions from LLM agent retries.

5. Security & Threat Modeling

Threat Vector

Attack Scenario

Architectural Mitigation

Indirect Prompt Injection

Competitor ad payload or poisoned GAQL string commands the agent to dump client data.

Schema Boundary Isolation: Payloads are typed JSON primitives only. Free text is never passed back to system instructions.

Financial Bleed (Runaway Loop)

Agent enters a recursive self-correction loop, increasing bids exponentially.

Distributed Redis token bucket: Max 10 mutations per campaign per 24-hour rolling window. Hard velocity cap $\le 15\%$.

Credential Exfiltration

Attacker crafts a prompt asking the agent to print customer Google Ads Refresh Tokens.

Credential Abstraction: Secrets are stored in AWS Secrets Manager / Vault. The agent never receives or handles raw credentials.