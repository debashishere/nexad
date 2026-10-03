Architectural Specification: NVIDIA OpenShell Integration
1. Executive Summary & Purpose
NVIDIA OpenShell is an open-source, kernel-isolated runtime designed for executing autonomous AI agents in zero-trust sandboxes. In the context of Project NexusAd, incorporating OpenShell replaces generic Docker/VM agent runners with an environment enforced by:   
NVIDIA
Kernel-level confinement: System-call filtering and filesystem sandboxing (via Landlock/eBPF).   
GitHub
Credential Blindness: Agents never see production OAuth tokens or API keys; OpenShell dynamically injects credentials only at authorized endpoint boundaries.   
GitHub
Outbound Network Filtering: Restricting agent traffic exclusively to vetted ad network endpoints (Google Ads, Meta Graph, programmatic SSPs).   
GitHub
Formal Policy Verification: Verifying via mathematical proof that dynamic agent policy changes remain within defined safety bounds prior to execution.   
GitHub

2. Requirements Specification

2.1 Functional Requirements (FR)
FR-1 (Sandbox Lifecycle Management): The system must provision, monitor, and tear down ephemeral OpenShell sandboxes per agency tenant or per execution task using the OpenShell Gateway API/CLI.

FR-2 (Credential Isolation via Provider Profiles): The system must register Google Ads, Meta Ads, and internal API credentials as OpenShell Provider Profiles. Ad management agents running inside the sandbox must send unauthenticated requests that OpenShell proxies and signs with real credentials only for approved destination hostnames.   
GitHub

FR-3 (Restricted Outbound Network Egress): The agent network policy must block all egress traffic except explicitly whitelisted CIDRs and domains (googleads.googleapis.com, graph.facebook.com, and internal NexusAd core services).

FR-4 (MCP Interoperability): The FastMCP ad-management server and tools must run within or communicate directly through the OpenShell sandbox supervisor without bypassing kernel-level audits.

FR-5 (Formal Policy Prover Integration): Any proposal by an agent to modify its execution boundary (e.g., requesting access to a new ad platform or webhook) must pass through the OpenShell Policy Prover and be routed to the Human-in-the-Loop (HITL) approval gateway if risks are flagged.

2.2 Non-Functional & Security Requirements (NFR)
NFR-1 (Zero-Trust Isolation): Agent processes must have zero read/write access to host filesystems outside ephemeral /tmp allocations.

NFR-2 (Prompt Injection Containment): Indirect prompt injections retrieved via web feeds or third-party ad copy must be bounded inside the sandbox, preventing the agent from exfiltrating environment variables or establishing unauthorized sockets.

NFR-3 (Audit Trail & Telemetry): Every allow/deny decision, system call, and network dispatch must be piped into the NexusAd Immutable Audit Ledger.

NFR-4 (Cold-Start Latency): Sandbox creation and tool provisioning overhead must not exceed 2.5 seconds for interactive user queries.

3. Proposed Architecture & System Design
3.1 Topology Diagram
                        ┌────────────────────────────────────────┐
                        │      HITL & Orchestration Gateway      │
                        │       (TypeScript / Node.js Host)      │
                        └───────────────────┬────────────────────┘
                                            │ Job Dispatch / Approvals
                                            ▼
                        ┌────────────────────────────────────────┐
                        │        OpenShell Gateway Daemon        │
                        │        (Tenant & Policy Manager)       │
                        └───────────────────┬────────────────────┘
                                            │ Provisions Container & Landlock
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ NVIDIA OpenShell Sandbox (Kernel-Enforced Isolation Boundary)                          │
│                                                                                        │
│   ┌──────────────────────────────────┐      RPC / stdio      ┌─────────────────────┐   │
│   │ Autonomous Ad Agent (Python)     │ ───────────────────►  │ NexusAd FastMCP Core│   │
│   │ (LangGraph / CrewAI Runner)      │                       │ (Ad Read/Write Tools│   │
│   └──────────────────────────────────┘                       └──────────┬──────────┘   │
│                   │                                                     │              │
│                   │ Outbound HTTP (Unauthenticated)                     │              │
│                   ▼                                                     ▼              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ OpenShell Supervisor & Proxy                                                   │   │
│   │  - Evaluates Landlock & eBPF policy rules                                      │   │
│   │  - Injects Provider Credentials (Google Ads / Meta Tokens) at network egress   │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
└───────────────────────────────────────────┼────────────────────────────────────────────┘
                                            │ Filtered, Signed HTTPS Requests Only
                                            ▼
                    ┌────────────────────────────────────────┐
                    │    Approved Ad Network API Endpoints   │
                    │  (googleads.googleapis.com, Meta API)  │
                    └────────────────────────────────────────┘
3.2 Key Integration Components
1. OpenShell Provider Profiles (Credential Vaulting)
Credentials never reside in container environment variables. A provider definition is imported into the OpenShell daemon:
YAML
# config/providers/google-ads-provider.yaml
apiVersion: openshell.nvidia.com/v1alpha1
kind: ProviderProfile
metadata:
  name: google-ads-service
spec:
  type: http-bearer
  allowed_endpoints:
    - host: "googleads.googleapis.com"
      port: 443
      protocol: https
  credential_mapping:
    header: "Authorization"
    format: "Bearer ${GOOGLE_ADS_OAUTH_TOKEN}"
Mechanism: When the agent calls [https://googleads.googleapis.com/](https://googleads.googleapis.com/)..., the OpenShell Supervisor intercepts the socket at the kernel layer, validates destination alignment, injects the authorization header from its encrypted enclave, and dispatches the request. If the agent tries to send this token to any other IP, egress is instantly dropped.
2. Declarative Sandbox Policy (policy.yaml)
Restricts local filesystem operations and outbound network targets using kernel primitives (Landlock LSM):
YAML
# config/policies/ad-agent-policy.yaml
apiVersion: openshell.nvidia.com/v1alpha1
kind: SandboxPolicy
metadata:
  name: nexusad-agent-restricted
spec:
  filesystem:
    read_only:
      - /app
      - /usr
      - /lib
    read_write:
      - /tmp/agent_run
    deny:
      - /etc/shadow
      - /proc/kcore
  network:
    default_action: deny
    egress:
      - allow:
          host: "googleads.googleapis.com"
          ports: [443]
      - allow:
          host: "graph.facebook.com"
          ports: [443]
      - allow:
          host: "nexusad-internal-api.internal"
          ports: [8080]
  process:
    allow_fork: true
    deny_ptrace: true
3. Formal Policy Prover in the CI/CD & Mutation Pipeline
When agents dynamically request operational expansion (e.g., executing changes across new campaigns or external reporting hooks), the request triggers the OpenShell Policy Prover:
The prover mathematically tests whether the updated policy breaches organizational safety invariants.
If the prover flags unverified transitive access paths (e.g., arbitrary webhook exfiltration), the mutation is blocked and escalated to the NexusAd HITL Slack/Web dashboard.
4. Integration Roadmap
Phase 1 : Foundation
├── Deploy NVIDIA OpenShell Gateway service in development cluster
├── Containerize base NexusAd Python FastMCP engine using stock OCI image
└── Configure Google Ads & Meta Ads OpenShell Provider Profiles

Phase 2 : Policy & Enforcement
├── Write declarative policy.yaml rules for Landlock filesystem & egress confinement
├── Implement credential-blind outbound proxy routing for ad mutations
└── Verify isolation against indirect prompt injection test vectors

Phase 3 : Orchestration & Formal Verification
├── Integrate OpenShell CLI/gRPC API into the TypeScript HITL Gateway
├── Enable OpenShell Policy Prover to automatically validate rule mutations
└── Route unverified policy changes to Human-in-the-Loop review queues