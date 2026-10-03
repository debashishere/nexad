# NVIDIA OpenShell as MVP Execution Sandbox

NexAd's V1 runs autonomous ad agents inside NVIDIA OpenShell kernel-isolated sandboxes rather than plain Docker containers. This was chosen to deliver credential blindness (agents never see OAuth tokens), outbound network filtering (egress restricted to whitelisted ad network CIDRs), and a formal audit trail at the kernel syscall level from day one — making the security story credible to enterprise agency buyers without retrofitting later.

**MVP scope: Phase 1 (Foundation) + Phase 2 (Policy & Enforcement) only.** Phase 3 (Formal Policy Prover + CI/CD mutation validation) is deferred post-MVP — shipping a half-baked formal verifier is worse than not shipping it, and Phases 1+2 already deliver the core credential-blindness and egress-filtering moat.
