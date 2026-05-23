---
tags: [workflow, ops-platform, onboarding, client-ops, project, active]
aliases: [Ops Platform, ALDC Ops, Launchpad]
created: 2026-05-08
updated: 2026-05-15
phase0_complete: 2026-05-08
phase1_complete: 2026-05-08
phase2_complete: 2026-05-09
phase7a_complete: 2026-05-15
phase7b_complete: 2026-05-15
---

# ALDC Launchpad — Client Operations Platform

**Repo:** `aldc-launchpad/` (monorepo, graduated from `aldc-shipyard/ops-platform/`)
**Status:** Phase 7b complete (2026-05-15) — Session Orchestrator with pipeline engine, Zeus Chat, voice alerts, deploy board, 5 AI agents. Orchestrator production hardening planned (2026-05-22) — see [[orchestrator-production-readiness]]. Sprint 3 ticket audit: 9 tickets updated (GP-242/246/219/269/199/267/257/259/244).
**Owner:** Paul Russell
**Goal:** Onboard any client at scale — from prospect qualification to production data delivery — using a single app that generates all artifacts and deploys them.

## Project Rename

**Old name:** "ops-platform" (internal working name during POC)
**New name:** **ALDC Launchpad** — the platform that launches new clients into production.

## What Exists Today (POC)

Built in a single session (2026-05-08):

| Page | Status | Description |
|---|---|---|
| App shell (`index.html`) | POC | Top nav + iframe. Functional but basic. |
| Hub (`pages/hub/`) | POC | Landing page with progress bars, role summaries. Needs modern redesign. |
| Engineering Dashboard | POC | 8-tab Navira status dashboard. Jira-synced. Most complete page. |
| Prospect Intelligence | POC | 8 prospect profiles, cost model, security matrix, engineering backlog. |
| Onboarding Wizard | POC | 6-step wizard: profile → framework → profiler → infra → security → generate. Core workflow. |
| Onboarding Framework | POC | 6-phase framework reference + generators. |
| Onboarding Guide | POC | Step-by-step runbook with pipeline architecture diagram. |
| Infrastructure Planner | POC | Capacity calculator with cost projections + build plan. |
| Progress Report | POC | Simplified meeting view. |

## Gaps — What's Missing for Production

### Design / UI / UX
1. **Landing page is too sparse** — needs real-time metrics, recent activity feed, client health grid, pipeline status
2. **No consistent design system** — each page has inline styles, no shared CSS, no components
3. **Mobile/responsive is broken** — most pages only work on desktop
4. **No dark/light mode toggle** — all pages hardcoded dark theme
5. **App shell is basic** — iframe approach limits cross-page communication; should consider SPA routing
6. **No loading states or animations** — pages feel static when generating

### Data & Integration
7. **No persistent data layer** — all numbers are hardcoded in HTML; should be `data.json` written by sync scripts
8. **Zeus Memory suggestions are simulated** — wizard has hardcoded prospect data instead of live MCP queries
9. **Data profiler is simulated** — shows fake profiling results; real Prefect flow not built
10. **No artifact persistence** — generated onboarding packages disappear on page refresh
11. **No deploy step** — wizard generates artifacts but doesn't execute `aldc onboard` CLI

### Onboarding Workflow
12. **No client.yaml file generation** — wizard shows YAML but doesn't write to disk
13. **No credential portal** — `connect.analyticlabs.io` not built
14. **No connector catalog API** — source picker is a static list; should query live catalog
15. **No onboarding email sending** — email draft is display-only; should integrate with Graph API or SMTP
16. **Build plan doesn't derive from framework mapping** — they're partially merged but still have duplicate data

### Missing Pages
17. **Client health dashboard** — per-client: connector status, data freshness, credential health, Snowflake usage
18. **Active onboardings tracker** — which clients are mid-onboarding, what step they're on, what's blocking
19. **Changelog / audit log** — what changed, when, who triggered it

## Zeus Integration Opportunities

Zeus Memory and Zeus Chat should be leveraged at every step to reduce friction:

| Step | Zeus Integration | Current | Target |
|---|---|---|---|
| Prospect qualification | Zeus Memory search for meeting notes, emails, prospect research | Simulated | Live MCP query on name input |
| Framework mapping | Zeus Memory for industry-specific patterns from existing clients | None | Pull patterns from similar client deployments |
| Data profiler | Zeus Chat to explain profiling results in plain language | None | "Your Google Ads has 23 campaigns averaging 2.5K rows/day. Recommend daily refresh with 7-day lookback." |
| Infrastructure sizing | Zeus Memory for actual Snowflake costs from QBO invoices | Hardcoded | Live cost data from Zeus accounting memories |
| Security checklist | Zeus Memory for compliance requirements from client meetings | Static list | Dynamic: "Proef's Marieke mentioned GDPR in the Mar 31 call" |
| Generated artifacts | Zeus Chat to review and improve generated client.yaml | None | "I notice you selected Google Ads but no MCC ID in the YAML — should I add a field?" |
| Post-deploy monitoring | Zeus Memory to track onboarding progress and flag stalls | None | "FBC credentials have been pending 8 days — should I draft a follow-up email?" |

## Roadmap — 5 Phases

### ✅ Phase 0: Design System + Landing Page Overhaul — COMPLETE 2026-05-08
- `styles/base.css` design system (color tokens, all shared components)
- All 10 pages migrated to base.css; inline styles stripped
- App shell: SPA hash routing, breadcrumbs, last-synced, dual iframe/fetch modes
- Hub redesigned: metrics, client health grid, activity feed, onboardings, quick actions, collapsible roles
- Dual-mode navigation: fetch+innerHTML (HTTP) + iframe+postMessage (file://)

### ✅ Phase 1: Data Layer + Live Integrations — COMPLETE 2026-05-08
- `data/state.json` schema: metrics, clients, onboardings, navira phases, activity feed, deadline
- `data/prospects.json` schema: 8 prospect profiles, scores, Zeus notes, cost models
- SPA shell pre-loads JSON data layer on boot (`window.LaunchpadData`)
- Hub page: all metrics, client grid, activity feed, onboardings hydrate from JSON with hardcoded fallback
- Prospects page: KPIs + comparison bars hydrate from JSON
- Wizard: Zeus suggestions load from prospects.json; artifact persistence to localStorage + downloadable JSON
- Progress report: ring charts + deadline counter hydrate from state.json
- Infrastructure planner: auto-fills from state.json metrics
- `/navira-sync` skill updated: writes to JSON data layer + queries Zeus Memory + legacy HTML backward compat
- `data/onboardings/` directory for wizard artifact persistence
- `CLAUDE.md` created with Zeus Memory usage rule + data layer docs
### ✅ Phase 2: Platform Dashboard — COMPLETE 2026-05-09
- `pages/platform/dashboard.html`: 8-tab client-agnostic dashboard (Overview, Roadmap, Architecture, Readiness, Integrations, Capacity, Pipeline, Zeus)
- `data/platform.json`: 26 features across 9 categories, 7 industry readiness profiles, 7 integrations, scaling projections
- Architecture decisions: multi-tenant Snowflake + automated RLS, Apache Superset (replacing Power BI), client registry as alignment layer
- Boot prompt skills `/launchpad-phase{2-7}` + `/launchpad-poc-validation` for full phased workflow
- Wiki phase pages created for Phases 2-7 with boot prompt references
- SPA shell: Platform route + nav link added, platform.json pre-loaded
- **Known gaps (deferred):** Tabs 4 (Readiness matrix), 6 (Capacity chart), 7 (Pipeline scatter) render hardcoded HTML/SVG rather than binding to `platform.json` — changes to JSON won't auto-update these views

### Phase 3: Multi-Tenant Foundation (Priority: high)
- ALDC_WAREHOUSE single database: RAW, ANALYTICS, REFERENCE, ADMIN schemas
- Client registry (ADMIN.client_registry), automated RLS, `aldc onboard` CLI

### Phase 4: Superset Integration (Priority: high)
- Apache Superset deployment, dashboard template engine per industry
- Programmatic dashboard generation via Superset API + RLS per client

### Phase 5: Credential Portal & Self-Serve Onboarding (Priority: high)
- connect.analyticlabs.io credential portal, onboarding email, self-serve flow

### Phase 6: Zeus Deep Integration (Priority: medium)
- Zeus Memory + Chat at every wizard step (7 integration points)
- Attribution scoring, CRM pipeline integration

### Phase 7: E2E Testing (Priority: final gate)
- Synthetic test client, full onboarding validation, security review

See individual phase pages for boot prompts, acceptance criteria, and detailed scope.

## Phase Pages

Phases are organized by lifecycle state in subdirectories:

```
ops-platform/
├── completed/     ← shipped and verified
├── active/        ← currently being worked on
└── backlog/       ← planned, not yet started
```

### Completed
- [[phase-0-design-system]] — ✅ 2026-05-08: Design system, landing page overhaul, app rename to Launchpad
- [[phase-1-data-layer]] — ✅ 2026-05-09: JSON data layer, live Jira/Zeus integration, persistent state
- [[phase-2-platform-dashboard]] — ✅ 2026-05-09: Client-agnostic dashboard, multi-tenant architecture, Superset, phased workflow

### Validation
- `/launchpad-poc-validation` — POC golden-path test (run before starting Phase 3)

### Active
_(none currently — this workstream is superseded by [[../aldc-launchpad/README|aldc-launchpad]] as of 2026-05-13)_

> **Note:** The ops-platform POC (Phases 0-2) is complete and preserved here as history. The product has graduated into a monorepo (`aldc-launchpad`) with a new phase structure. See [[../aldc-launchpad/README]] for the active workstream.

### Backlog
- [[phase-3-multitenant]] — ALDC_WAREHOUSE, client_registry, automated RLS, aldc onboard CLI
- [[phase-4-superset]] — Apache Superset deployment, template engine, per-client dashboard generation
- [[phase-5-credentials]] — connect.analyticlabs.io portal, onboarding email, self-serve flow
- [[phase-6-zeus]] — Deep Zeus Memory + Chat integration at every wizard step
- [[phase-7-e2e-testing]] — Full end-to-end validation with synthetic test client

> These backlog phases may be re-scoped or absorbed into the new aldc-launchpad workstream.

## See Also

- [[aldc-shipyard]] — parent repo
- [[navira]] — first client tracked in this platform
- [[GEP]] — client entity page
- [[fusion92]] — second tracked client
