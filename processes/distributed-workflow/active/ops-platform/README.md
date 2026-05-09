---
tags: [workflow, ops-platform, onboarding, client-ops, project, active]
aliases: [Ops Platform, ALDC Ops, Launchpad]
created: 2026-05-08
updated: 2026-05-08
phase0_complete: 2026-05-08
---

# ALDC Launchpad — Client Operations Platform

**Repo:** `aldc-shipyard/ops-platform/`
**Status:** POC built (2026-05-08). Design/UX overhaul + production hardening needed.
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

### Phase 1: Data Layer + Live Integrations (Priority: high)
### Phase 2: Artifact Generation + Deploy Step (Priority: high)
### Phase 3: Client Health + Monitoring (Priority: medium)
### Phase 4: Zeus Deep Integration (Priority: medium)
### Phase 5: POC End-to-End Testing (Priority: final gate)

See individual phase pages for boot prompts, acceptance criteria, and detailed scope.

## Phase Pages

### Active
- [[phase-1-data-layer]] — JSON data layer, live Jira/Zeus integration, persistent state
- [[phase-2-artifacts-deploy]] — Real artifact generation, CLI execution, credential portal stub
- [[phase-3-client-health]] — Per-client health dashboard, active onboardings tracker
- [[phase-4-zeus-integration]] — Deep Zeus Memory + Chat integration at every wizard step
- [[phase-5-poc-e2e-testing]] — Full end-to-end validation with synthetic test client before production rollout

### Completed
- [[phase-0-design-system]] — ✅ 2026-05-08: Design system, landing page overhaul, app rename to Launchpad

## See Also

- [[aldc-shipyard]] — parent repo
- [[navira]] — first client tracked in this platform
- [[GEP]] — client entity page
- [[fusion92]] — second tracked client
