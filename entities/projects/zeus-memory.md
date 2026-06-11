---
tags: [entity, project, zeus-memory, opentribe, enterprise-knowledge, documentation-sync]
aliases: [Zeus Memory, OpenTribe, opentribe]
sources: [sources/obsidian-import/research/OpenTribe/Zeus Memory - Wedge, MVP, and Enterprise Adoption Strategy.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Lululemon Demand Forecasting Knowledge Integrity Use Case.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Zeus Memory Prototype Brief - Lululemon Demand Forecasting Documentation Auto-Sync.md, sources/obsidian-import/research/OpenTribe/Research and Planning/PAULS MOONSHOTS.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Action Items.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Zeus Memory FAQ - CEO, Product, and AI Engineering.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Zeus Memory Prototype Architecture - Trigger, Drift Detection, and Writeback.md, sources/obsidian-import/research/OpenTribe/Research and Planning/Zeus Memory Demo Script - 5-Minute Lululemon Walkthrough.md]
created: 2026-04-16
updated: 2026-06-11
---

# Zeus Memory (OpenTribe)

OpenTribe is a product initiative centered on **Zeus Memory** — an integration-first knowledge integrity layer for enterprises. Rather than replacing existing documentation systems like Confluence, Zeus ingests signals from source systems (Git, Jira, Confluence, cloud platforms, meeting notes), detects when documentation has drifted from operational reality, and proposes traceable updates with evidence and human approval.

## Vision / Goal

Solve the fundamental enterprise problem: **"What is actually true right now?"**

Tribal knowledge is fragmented across codebases, docs, tickets, chats, meetings, cloud platforms, and internal tools. Documentation becomes stale after every code merge, Jira epic closure, and business decision. Zeus operates as a near-zero-touch system that continuously keeps memory and docs in sync as source systems change.

The product wedge is: **Confluence doc accuracy + auto-sync, powered by cross-source drift detection.**

Two deployment modes are envisioned:
- **Integration mode** (preferred by large enterprises): overlays existing systems without migration
- **Full migration mode** (suited for startups/small companies): replaces documentation systems entirely

## Current State

As of May 2026, Zeus Memory has evolved beyond the prototype stage into a real product:

- **Multi-tenant architecture** in use — companies onboard as tenants with unique tenant IDs and API keys
- **Live demos** — Food Bank Canada demo to ~75 people
- **CCE integration** — Zeus Memory is the backend for [[cce|Claude Code Enhanced]]'s cross-session knowledge persistence, team messaging, task tracking, and auto-learn capture
- **AI-Driven Development pivot** — Zeus and Zeus Memory are central to ALDC's AI-Driven Development initiative

### Active Workstream

An **Automated Tenant Data Source Ingestion** workstream is in progress — see [[processes/distributed-workflow/active/zeus-memory/README|zeus-memory workstream]]. Goal: when a new tenant onboards, automatically ingest their existing tools (Confluence, Jira, Git) into their Zeus Memory knowledge base. Phased approach: prove with Confluence first, then expand to batch multi-source migration.

### Prototype (Lululemon Demand Forecasting Use Case)

The original prototype demonstrated the core workflow using mocked Lululemon artifacts:

### Prototype (Lululemon Demand Forecasting Use Case)

The prototype demonstrates a single end-to-end workflow:

1. **Load current state**: Existing Confluence-like forecasting documentation
2. **Ingest source change**: A markdown-sensitive SKU override rule changes in Git, with corresponding Jira epic and meeting decision note
3. **Detect impact**: Zeus identifies which docs are affected and which sections are stale
4. **Explain drift**: Human-readable explanation of what changed and why the doc is no longer accurate
5. **Draft update**: Proposed updated section for forecasting assumptions, override logic, runbook guidance
6. **Human approval**: Reviewer approves or rejects the proposed update
7. **Save and preserve traceability**: Updated doc linked to code change, Jira artifact, and decision artifact

### Technical Architecture

- **Deterministic components**: File loading, source parsing, candidate doc mapping, section selection, diff rendering, save/update flow
- **LLM-assisted components**: Drift explanation, stale section rewrite, confidence reasoning summary
- **Stack**: Python + Streamlit for prototype; local mocked files simulating Git PRs, Jira tickets, Confluence pages, and meeting notes

## Key Decisions

1. **Integration-first, not migration-first**: Zeus overlays existing systems (Confluence, Jira, Git) rather than asking enterprises to migrate. This is the critical product positioning.
2. **Conservative update behavior**: Updates one section at a time, only when evidence is visible, only after human approval. No autonomous production writeback.
3. **Evidence-based trust**: Every proposed update includes provenance linking back to code changes, Jira artifacts, and decision records. Without visible provenance, trust drops immediately.
4. **Not a chatbot**: The product must feel like "maintain enterprise knowledge" rather than "ask AI a question."

## Knowledge Types Zeus Maintains

For the Lululemon use case, Zeus tracks five categories of high-value knowledge:
1. **Forecasting formulas and thresholds** (markdown sensitivity, override rules, fallback logic, regional exceptions)
2. **Feature and model assumptions** (seasonality, stockout handling, promotional uplift, cold-start rules)
3. **Decision records** (who approved changes, why, whether temporary or durable)
4. **Integration knowledge** (upstream data feeds, cloud job changes, downstream consumers)
5. **Operational runbooks** (validation procedures, alerts, planner notifications)

## Value Timeline

- **Day 1**: Immediate visibility into which docs are stale, which rules are misaligned, where knowledge gaps exist
- **Day 30**: Rule changes more consistently reflected; teams spend less time in alignment meetings
- **Day 90**: Zeus becomes part of the change workflow; documentation freshness improves materially
- **Day 365**: Compounding institutional memory; knowledge less dependent on specific individuals

## Moonshot Ideas

Broader ideas from Paul's notes for leveraging Zeus:
- Company-wide conflict resolution between code and docs (raises GitHub issues with solutions)
- Integration with [[PhaseLab]] for dashboard management of regulatory changes
- Dev pipeline triggered when doc-code conflicts are detected (with approval before merge)

## Documents Prepared

| Document | Audience | Purpose |
|----------|----------|---------|
| Wedge, MVP, and Enterprise Adoption Strategy | CEO | Commercial framing |
| Prototype Brief | All | What the prototype does and proves |
| Lululemon Use Case Brief | Product Owner, CEO | Domain credibility |
| Architecture One-Pager | Senior AI Engineer | Technical credibility |
| FAQ | All | Objection handling |
| Demo Script (5-min walkthrough) | All | Live presentation guide |

## Open Questions / Next Steps

- Real Confluence/Jira/Git provider integrations (currently mocked)
- Full memory graph for cross-document relationship tracking
- Enterprise permissions model and multi-tenant architecture
- Autonomous production writeback with configurable guardrails
- Confidence scoring calibration
- Policy/governance engine for update approval workflows

## CCE Learning Storage — Paul's tenant (operational)

CCE auto-learn (`/learn`, `cce learn`) and any direct Zeus `/api/store` writes for Paul **must post to
his DEVELOPMENT tenant, NOT the ALDC Management tenant.**

> **Correction (2026-06-11):** the `cce-learn` skill hardcodes ALDC Management
> (`11111111-1111-1111-1111-111111111111`) as "CRITICAL — always use." That is **wrong for Paul** — his
> learnings (and leaderboard attribution) belong in the **Developers-team development tenant**. The tenant
> is inferred from the API key, so using Paul's key routes correctly. Don't swap back to ALDC Management.

| Field | Value |
|-------|-------|
| Tenant ID (Development) | `c1234567-0000-0000-000a-000000000001` |
| User ID | `e1234567-0000-0000-0003-000000000001` |
| Username / Slug | `paul` / `paul-russell` |
| Email | `paul.russell@aldc.io` |
| Parent Tenant | Developers team (`dddddddd-dddd-dddd-dddd-dddddddddddd`) |
| Role / Tier | member (ALDC Org + Developers team) / standard |
| **API Key** | in `vault/credentials.md` → "Zeus Memory — Paul's user/tenant" (DB-seeded, migration 034; not in `.env` yet) |

Write: `POST https://zeus.aldc.io/api/store`, `X-API-Key: <Paul's key>`,
`{"content": "...", "source": "cce_success_log|cce_failed_approach|cce_decision_log", "metadata": {"user": "paul"}}`.
Do not pass `tenant_id` (inferred from key); `metadata.user="paul"` is required for leaderboard attribution.

## See Also

- [[cce]] — uses Zeus Memory as its backend for cross-session knowledge persistence
- [[factoria]] — another ALDC project with artefact-driven workflows (different domain)
- [[cpma]] — related ideas about regulatory change management
- [[phaselab]] — related product concept (integration envisioned at Phase 7)
