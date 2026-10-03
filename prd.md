Agentic Ad-Tech Infrastructure

Document Version: 1.0.0

Project Codename: Project NexAd (Agentic Ad Mediation & Execution Gateway)

Target Financial Milestone: $1.0M–$1.5M ARR / $5.0M Enterprise Acquisition Exit

Target Horizon: 7-10 days

1. Executive Summary & Vision

1.1 Executive Summary

As autonomous software agents begin handling retrieval, comparison, and procurement tasks on behalf of human principals, programmatic advertising shifts from client-side visual display (CPM/CTR) to protocol-level programmatic execution (API utilities, structured incentives, dynamic parameter negotiation).

Project NexAd is an enterprise-grade agentic ad mediation gateway. It bridges foundational Large Language Models (LLMs) and user task agents with commercial advertising channels (Google Ads, Meta Marketing API, programmatic SSPs) via the Model Context Protocol (MCP). NexAd adds an essential enterprise execution layer missing from open-source wrappers: deterministic budget firewalls, safety-gated write operations, and Human-in-the-Loop (HITL) synthetic justification cards.

1.2 Target Financial Goal & Exit Thesis

Target Valuation: $5,000,000 USD.

Valuation Multiple: 3.5x – 5x ARR (standard for defensible, high-growth B2B AI/Ad-Tech middleware).

Target Traction Metrics:

ARR Run Rate: $1.0M – $1.4M ARR.

Customer Profile: 60 to 90 Performance Marketing Agencies / Mid-Market Brands paying $1,000 – $2,000/month.

Gross Revenue Retention (GRR): >90%.

Target Strategic Acquirers:

Performance ad-tech consolidation platforms (e.g., The Trade Desk, AppLovin, Klaviyo).

Major agency holding networks (e.g., Omnicom, WPP, Publicis) modernizing their algorithmic media buying tech stack.

Enterprise AI workflow automation platforms (e.g., Zapier, Make, UiPath) acquiring turnkey agentic ad execution capabilities.

2. Market Analysis & Positioning

2.1 The Paradigm Shift

The advertising landscape is bifurcating into two operational tracks:

L1: Agent-Targeted Delivery (Functional/Utility Layer): Task agents consume deterministic, machine-readable payloads (JSON-LD, MCP tools) optimizing for utility, price discounts, SLA, and inventory APIs.

L2: Human-Targeted Delivery (Deliberative/Framing Layer): Agents surface synthetic explanation cards and interactive summaries to the human principal for consent, brand justification, and payment clearance.

       TRADITIONAL AD TECH                       AGENTIC AD TECH (NEXAD)
┌─────────────────────────────────┐        ┌────────────────────────────────────┐
│ Brand -> DSP/SSP -> Browser Tag │        │ Brand / Ad-Manager Agent           │
│ -> Impression to Human Eye      │        └─────────────────┬──────────────────┘
└─────────────────────────────────┘                          │ Tool Offer (MCP)
                                           ┌─────────────────▼──────────────────┐
                                           │ User Task Agent / Context Engine   │
                                           └─────────────────┬──────────────────┘
                                                             │ HITL Escalation
                                           ┌─────────────────▼──────────────────┐
                                           │ Human Decision-Maker (Approval UX) │
                                           └────────────────────────────────────┘



2.2 Formal Research Track Alignment

NexAd positions its intellectual property along established computer science research vectors:

Algorithmic Mechanism Design & Multi-Attribute Auctions (ACM EC / AAMAS): Moving beyond single-scalar bidding (eCPM) to evaluate dynamic multi-attribute parameter matching (Price, SLA, Latency, Warranty).

Adversarial Security & Indirect Prompt Injection Defense (IEEE S&P): Sandboxing commercial sponsored payloads against malicious goal hijacking before tools enter an agent’s context window.

Synthetic Persuasion & HITL Framing (ACM CHI / FAccT): Translating raw tool payloads into objective, non-hallucinated visual cards for human sign-off.

2.3 Competitive Gap

Google's Open-Source google-ads-mcp: Free, read-only analytics tool using GAQL. It cannot execute writes, modify budgets, coordinate cross-network campaigns (Google + Meta + Amazon), or enforce organizational safety governance.

Traditional Bid Managers (Bid-namic, Skai, Marin): Monolithic web dashboards lacking native MCP support, direct LLM context integration, or multi-agent negotiation primitives.

NexAd Moat: The secure, verified Write-Execution Layer with programmatic budget firewalls and cross-channel MCP endpoints.

3. Target User Personas & Pain Points

3.1 Primary Persona: The Overloaded Performance Marketing Agency Director

Name: "Agency Alex" (VP of Media / Founder at a 40-person agency managing 60 accounts).

Pain Points:

Account managers waste 15+ hours weekly per client pulling GAQL/Meta reports, finding budget bleed, and adjusting bids manually.

Direct API integration with custom LLMs is high-risk: one hallucinated prompt could spend a client’s entire monthly budget in 30 minutes.

Lack of a single interface to let client agents query live performance data and execute parameter shifts safely.

3.2 Secondary Persona: Autonomous Commerce Agent Builders

Name: "Developer Dev" (Building consumer task agents / shopping assistants).

Pain Points:

Cannot safely allow merchant promotions into an agent’s reasoning engine due to prompt injection vulnerabilities.

Lacks a standardized protocol to query live commercial incentives, dynamic coupons, and inventory tools across multiple merchant networks.

4. Product Functional Architecture

   ┌────────────────────────────────────────────────────────────────────────┐
   │                   NEXAD AGENTIC PLATFORM                             │
   ├────────────────────────────────────────────────────────────────────────┤
   │                     LAYER 1: GATEWAY & HITL                            │
   │  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  │
   │  │ Anthropic/OpenAI MCP Hub│  │ Slack / Teams / Web Approval Cards  │  │
   │  └───────────┬─────────────┘  └──────────────────┬──────────────────┘  │
   ├──────────────┼───────────────────────────────────┼─────────────────────┤
   │              │ Secure JSON-RPC / gRPC            │ Event Webhooks      │
   │              ▼                                   ▼                     │
   │                     LAYER 2: SAFETY & FIREWALL                         │
   │  ┌──────────────────────────────────────────────────────────────────┐  │
   │  │ Adversarial Sanitizer (Prompt Injection / Schema Boundary Filter)│  │
   │  ├──────────────────────────────────────────────────────────────────┤  │
   │  │ Deterministic Budget Firewalls & Velocity Circuit Breakers       │  │
   │  └───────────────────────────┬──────────────────────────────────────┘  │
   ├──────────────────────────────┼─────────────────────────────────────────┤
   │                              ▼                                         │
   │                     LAYER 3: EXECUTION ENGINES                         │
   │  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────┐ │
   │  │ Google Ads API Client │ │ Meta Graph API Client │ │ Custom DSP/SSP│ │
   │  │ (Read + Gated Write)  │ │ (Read + Gated Write)  │ │ Adapters      │ │
   │  └───────────────────────┘ └───────────────────────┘ └───────────────┘ │
   └────────────────────────────────────────────────────────────────────────┘



4.1 Core Functional Modules

1. Adversarial Schema Sanitizer & Injection Guard

Purpose: Sanitizes external promotional payloads before injecting them into the agent's context.

Mechanism: Strictly validates incoming tool definitions and outputs against typed JSON schemas; strips raw instruction tokens, system-prompt override attempts, or dynamic script tags.

2. Deterministic Budget Firewall (The Safety Circuit Breaker)

Purpose: Prevents unauthorized, catastrophic media spend caused by model hallucination or autonomous drift.

Rules Engine:

Spend Velocity Limit: No campaign daily spend can be increased by more than $\Delta = 15\%$ per 24-hour cycle autonomously.

Absolute Hard-Cap: Hard dollar cap per account, enforced via Redis atomic locks before API dispatch.

Kill Switch: Triggers an immediate API pause across all active campaigns if anomaly bounds (e.g., CAC spikes $>300\%$ over a 2-hour moving average) are breached.

3. Human-in-the-Loop (HITL) Interactive Approval Gateway

Purpose: Generates justification cards for human verification prior to critical mutations.

Workflow:

Agent proposes: update_target_cpa(campaign_id="123", new_cpa=18.50).

Firewall flags action as Gated.

Gateway pushes interactive card to Agency Alex's Slack/Teams channel:

"Agent proposes reducing Target CPA by 12% on Campaign 'US-Search' due to conversion plateau over last 48 hours. Projected daily spend: $420. Approve / Reject?"

Upon HMAC-signed human approval, the write executes deterministically.

4. Multi-Network Normalized MCP Server

Exposes unified tools to any MCP-compatible client (Claude Desktop, custom enterprise agents, LangGraph environments):

nexus_get_cross_network_performance(timeframe, metrics)

nexus_propose_budget_reallocation(source_campaign, target_campaign, amount)

nexus_commit_sanctioned_action(action_id, human_signature)

5. Technology Stack Selection

To achieve maximum development velocity toward the $1M ARR goal without sacrificing maintainability, the platform uses a polyglot two-tier architecture:

| Component | Technology | Rationale |
| Execution Engine & API Connectors | Python 3.12+ (FastMCP, google-ads, facebook-business, pydantic v2) | First-class official SDKs from Google and Meta; rapid iteration on data models and mathematical anomaly algorithms. |
| Gateway, Auth & Webhooks | TypeScript / Node.js 20+ (NestJS or Fastify, @modelcontextprotocol/sdk) | Standard for protocol-level event streaming; unified typing with React-based approval dashboard. |
| State & Policy Store | Redis (Upstash/Redis Enterprise) + PostgreSQL | In-memory distributed atomic counters for velocity rate-limiting; PostgreSQL for immutable audit trails and SOC2-compliant logging. |
| Human Interface Layer | Next.js 14, TailwindCSS, Slack Bolt SDK | Clean interfaces for team management and webhook-driven interactive approval cards. |
| Container & Deployment | Docker, AWS ECS (Fargate) or GCP Cloud Run | Stateless, horizontally scalable microservices with isolated secrets management for API tokens. |

6. Go-To-Market (GTM) & Sales Plan to $5M Exit

6.1 Pricing Model

Agency Starter: $499 / month (Up to 10 managed ad accounts, read-only analytics, basic budget monitoring, standard Slack alerts).

Agency Growth (Core Driver): $1,499 / month (Up to 35 managed accounts, gated autonomous write actions, cross-platform Google + Meta support, custom MCP endpoints).

Enterprise Custom: $3,000+ / month (Unlimited accounts, custom internal agent integrations, SOC2 single-tenant data isolation).

6.2 Sales Pipeline & Customer Acquisition Strategy

Direct Outbound to Performance Agencies: Target mid-market agencies (20–100 employees) handling performance e-commerce. Value proposition: "Replace 20 hours of manual campaign maintenance per account manager while guaranteeing zero hallucinated ad-spend."

Open-Core Lead Magnet: Maintain a lightweight, free open-source utility (e.g., an enhanced Google Ads Read-Audit MCP) on GitHub that detects budget waste. The free tool promotes the hosted, enterprise-grade NexAd write/firewall platform.

Co-Marketing with Agent Ecosystems: List NexAd in official MCP server directories and AI workflow registries (Smithery, LangChain Hub, Anthropic ecosystem lists).

6.3 Acquisition Roadmap (18-Month Target)

Month 0-3: MVP & Validation   Month 4-8: Early Traction   Month 9-14: Scale & Hardening  Month 15-18: Strategic Exit
┌──────────────────────────┐  ┌────────────────────────┐  ┌───────────────────────────┐  ┌─────────────────────────┐
│ • Fork google-ads-mcp    │  │ • 15 Paying Agencies   │  │ • 70 Paying Agencies      │  │ • Run M&A outreach      │
│ • Build FastMCP writes   │  │ • Launch Meta adapter  │  │ • \$1.1M ARR run-rate     │  │ • Engage Trade Desk,    │
│ • Implement Firewalls    │  │ • \$20K MRR            │  │ • Full SOC2 Type I audit  │  │   Omnicom, Klaviyo      │
│ • 3 Beta Agency Pilots   │  │ • Refine Slack HITL    │  │ • Zero-injection cert     │  │ • Target \$5M Exit      │
└──────────────────────────┘  └────────────────────────┘  └───────────────────────────┘  └─────────────────────────┘



7. Key Risks & Mitigation

Platform API Deprecation / Provider Hostility:

Risk: Google or Meta alters developer terms to ban automated agent tools.

Mitigation: Connect via official, approved Marketing Partner APIs; adhere strictly to rate limits; ensure all mutations are signed with human-in-the-loop authorization tokens.

LLM Execution Liability:

Risk: Agent causes unintended ad budget burn, resulting in agency churn and legal exposure.

Mitigation: Hardcode deterministic budget caps in the database/Redis layer, completely outside the LLM's control. Explicitly state in the Terms of Service that mutations require human escalation past configured financial thresholds.

Open-Source Cannibalization:

Risk: Google expands its official open-source repository to include write actions.

Mitigation: Maintain the competitive moat around cross-platform orchestration (unifying Google, Meta, and DSPs under a single standard), policy enforcement, and enterprise compliance reporting.