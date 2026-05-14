---
tags: [workflow, aldc-launchpad, monorepo, onboarding, client-ops, project, active]
aliases: [ALDC Launchpad, Launchpad Monorepo]
created: 2026-05-13
updated: 2026-05-13
---

# ALDC Launchpad — Client Delivery Platform

**Repo:** `aldc-launchpad/` (monorepo, graduating from `aldc-shipyard/ops-platform/`)
**Status:** Active — monorepo restructure + credential exchange hub in progress
**Owner:** Paul Russell
**Goal:** Two-sided AI-powered delivery platform. Onboard any client at scale — from prospect qualification to production data delivery — with a master platform (ALDC) and per-client portal (analytics, Zeus Chat, credential submission).

## Prior Art

This workstream supersedes [[../ops-platform/README|ops-platform]] (Phases 0-2 completed 2026-05-08/09). The POC proved the design system, data layer, and platform dashboard. The product now graduates into a monorepo with expanded scope: credential exchange, client boards, tracker, client portal.

## Product Architecture

**ALDC Master Platform** (internal delivery engine):
- Tracker: UI-driven roadmap/plan/workflow generation (Claude API + Zeus Memory + LLM wiki as AI backend)
- Connector management: deploy, configure, monitor Prefect connectors
- Warehouse management: Snowflake schemas, SQL templates, industry models
- Credential exchange: collect, validate, provision credentials into Prefect Blocks
- All-client overview: health, capacity, revenue, alerts

**Client Portal** (per-client product):
- Analytics: Superset-embedded dashboards with RLS
- Zeus Chat: per-client AI instance, improvement suggestions
- Communication: replaces Slack/email threads with ALDC
- Credential submission: secure forms, OAuth authorization
- Board views: roadmap (read-only), bugs, data health
- No access to: delivery engine, connector code, roadmaps/plans/workflows, other clients

## Monorepo Structure

```
aldc-launchpad/
├── platform/master/        # ALDC internal dashboard (vanilla HTML/CSS/JS SPA)
├── platform/portal/        # Client-facing dashboard (future)
├── connectors/             # git submodule → prefect-connectors
├── warehouse/              # Snowflake schemas, SQL templates
├── tracker/                # Jira replacement engine (future)
├── api/credential-exchange/ # Azure Functions (Python)
├── shared/                 # client-registry.json, shared schemas
├── infra/                  # Terraform/Bicep
└── .claude/commands/       # Skills and boot prompts
```

## Key Decisions

- 2026-05-13 — Monorepo over multi-repo: all components linked via client registry
- 2026-05-13 — Azure Functions (Python) for backend, not FastAPI/NestJS
- 2026-05-13 — Azure Key Vault → Prefect Blocks (Key Vault = source of truth, Blocks = runtime cache)
- 2026-05-13 — Single deployment, multi-tenant, client-scoped (not 20 separate deployments)
- 2026-05-13 — Tracker is UI-driven with AI backend (Claude API + Zeus + wiki)
- 2026-05-13 — Ops-platform owns data lifecycle (replaces Jira as master tracker over time)
- 2026-05-13 — Per-client Zeus Memory instances, seeded from onboarding context
- 2026-05-13 — Apache Superset replaces Power BI (open-source, self-hosted)
- 2026-05-13 — 5-minute OAuth code expiry solved by server-side `oauth-callback` Azure Function

## Skills

| Skill | Purpose |
|---|---|
| `/launchpad-phase0r` | Monorepo restructure (DONE) |
| `/launchpad-phase0c` | Connector framework + live deployment pipeline (DEMO) |
| `/launchpad-phase1a` | Credential tracking dashboard + client boards (DEMO) |
| `/launchpad-phase1b` | Secure credential submission (Azure Functions + Key Vault) |
| `/launchpad-phase1c` | Prefect Block provisioning (Key Vault → Blocks) |
| `/launchpad-wiki-sync` | Sync project state to wiki (no Jira) |
| `/launchpad-wiki-lint` | Check wiki consistency (no Jira) |

## Phase Pages

```
aldc-launchpad/
├── active/        ← currently being worked on
├── completed/     ← shipped and verified
└── backlog/       ← planned, not yet started
```

### Active
- [[phase-0c-connector-framework]] — Connector framework analysis, migration catalog, live deployment pipeline. DEMO PRIORITY. `/launchpad-phase0c`
- [[phase-1a-credential-dashboard]] — Credential tracking dashboard + client boards + client selector. DEMO PRIORITY. `/launchpad-phase1a`
- [[phase-1b-credential-submission]] — Azure Functions + Key Vault + OAuth callback (5-min fix). `/launchpad-phase1b`
- [[phase-1c-prefect-provisioning]] — One-click Key Vault → Prefect Block provisioning. `/launchpad-phase1c`
- [[phase-1d-automation]] — Reminder chains, health monitoring, Windsor auto-verify. Deferred.

### Completed
- [[phase-0-monorepo-restructure]] — Monorepo created, ops-platform migrated, submodule added. `/launchpad-phase0r` (2026-05-13)

_(Also inherited from ops-platform POC — see [[../ops-platform/README]] for legacy Phases 0-2)_

### Backlog
- Tracker Foundation — UI-driven Jira replacement with AI backend
- Client Portal — Per-client dashboard with Superset + Zeus Chat
- Existing Client Migration — Navira + Fusion92 onto new onboarding framework
- Multi-Tenant Snowflake — (re-scoped from ops-platform Phase 3)
- Superset Integration — (re-scoped from ops-platform Phase 4)
- Zeus Deep Integration — (re-scoped from ops-platform Phase 6)
- E2E Testing — (re-scoped from ops-platform Phase 7)

## Session Log

### 2026-05-13 — Phase 0R completed + Phase 0C created

- did: Executed Phase 0R monorepo restructure. Created `aldc-launchpad/` with full directory tree, migrated all ops-platform files to `platform/master/`, added prefect-connectors submodule, created client-registry.json (GEP + Fusion92), CLAUDE.md, 16 skill files with updated paths, placeholder READMEs. Verified all 11 SPA routes resolve correctly. Created Phase 0C (Connector Framework & Live Deployment) — new demo-priority phase for analyzing legacy connectors and building a deploy-from-dashboard pipeline. Updated execution-path.md with Lane D. Created `migrations/connectors/` directory and wiki tracker for Phase 0C.
- decided: Phase 0C runs alongside Phase 1A for maximum demo impact. Amazon Ads US is the live deploy candidate. core_api analyzed as read-only reference (extract patterns, leave the rest). Four parallel lanes after 0R: D (connectors), A (frontend), B (backend), C (data).
- next: `/launchpad-phase0c` from aldc-launchpad repo for connector framework. `/launchpad-phase1a` for credential dashboard.

### 2026-05-13 18:00 — Workstream created: product architecture + credential exchange hub plan

- did: Deep research across design doc, wiki, Zeus Memory, ops-platform codebase. Reviewed credential_exchange_hub_design_doc.md. Created approved implementation plan (4 phases: 0R restructure, 1A dashboard, 1B submission, 1C provisioning, 1D automation). Created 5 wiki phase trackers, 6 skill/command files, CLAUDE.md draft for monorepo. Created new `aldc-launchpad` workstream separate from old `ops-platform` workstream.
- decided: Azure Functions (Python) for backend. Azure Key Vault → Prefect Blocks for secrets. Monorepo structure. UI-driven tracker with AI backend. Per-client Zeus Memory instances. OAuth callback solves 5-min code expiry. Ops-platform replaces Jira as master tracker. Fusion92 included in client selector alongside Navira.
- next: Run `/launchpad-phase0r` to create aldc-launchpad repo + migrate ops-platform code. Then `/launchpad-phase1a` for credential dashboard + client boards (demo priority).

## Parallel Execution Path

After Phase 0R (DONE), four lanes run in parallel:

```
              Phase 0R ✅ DONE
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
  LANE D           LANE A+B            LANE C
  Connectors       Frontend+Backend    Data + Boards
  /phase0c         /phase1a /phase1b   (credentials.json,
  1-2 days         3-5 / 5-7 days     board cards, F92)
  migrations/      pages/ api/        data/, shared/
  connectors/
     │                  │                  │
     │            ┌─────┴─────┐            │
     │            ▼           ▼            │
     │      Integration  (1 day)           │
     │            ▼                        │
     └──────► Phase 1C (3-4 days) ◄────────┘
                  ▼
             Phase 1D (deferred)
```

**Lane isolation**: A writes pages/styles, B writes api/infra, C writes data/shared, D writes migrations/ + connector templates. No cross-lane edits.

**Critical path to full demo**: 0R ✅ → 0C + 1A + C in parallel (Day 2-3) = demo in 3 days (credentials + live deploy).
**Critical path to full flow**: 0R ✅ → 1A + 1B + 0C parallel → integrate → 1C = ~9 days.

Full execution path with day-by-day schedule: `aldc-launchpad/api/credential-exchange/execution-path.md`

## Approved Plan

Full implementation plan with all phases, data models, architecture diagrams, and verification steps:
`C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md`

## See Also

- [[../ops-platform/README]] — Prior POC workstream (Phases 0-2 completed)
- [[GEP]] — Navira, primary client for PoC
- [[fusion92]] — Second active client
- [[prefect]] — Connector runtime (submodule)
- [[eclipse]] — Legacy connector system being replaced
