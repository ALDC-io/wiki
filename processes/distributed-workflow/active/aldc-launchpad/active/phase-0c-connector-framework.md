---
tags: [launchpad, connectors, framework, deployment, complete]
created: 2026-05-13
updated: 2026-05-13
deliverables_built: 2026-05-13
deliverables_complete: 2026-05-13
---

# Phase 0C: Connector Framework & Live Deployment

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase0c.md` → `/launchpad-phase0c`
**Status:** Complete
**Effort:** 1 day
**Demo target:** Tomorrow — deploy a connector live from the Launchpad dashboard

## Goal

Analyze legacy connector code (prefect-connectors + core_api), create a migration catalog, standardize the connector creation/deployment pattern, and build a UI-driven deployment pipeline. Enable fast migration of all non-priority connectors and live demo of end-to-end deployment.

## Motivation

- prefect-connectors mixes framework code with per-connector implementations
- core_api patterns are not well-designed — extract useful bits, leave the rest
- Navira has 20+ connectors to build; standardizing the framework accelerates all of them
- Demo impact: showing credential tracking + live connector deployment = full pipeline story

## Deliverables

1. `migrations/connectors/catalog.json` — every legacy connector cataloged with auth, schema, schedule, migration status
2. Connector template/generator — standardized creation pattern
3. Platform UI deploy flow — button to trigger connector deployment from dashboard
4. Live deployment pipeline — UI → Prefect deployment → data lands

## Key Decisions

- 2026-05-13 — Run from aldc-launchpad repo (submodule access to prefect-connectors, UI in platform/master)
- 2026-05-13 — core_api is read-only reference, not modified
- 2026-05-13 — Amazon Ads US is the demo candidate (already provisioned, known-good)

## Session Log

### 2026-05-13 — wiki-sync: Phase 0C complete — all 4 deliverables shipped

- did: Built all remaining Phase 0C deliverables. Deploy modal with animated 6-step pipeline (verify credential → resolve image → register deployment → push to work pool → trigger test run → verify data in Snowflake). Framework column added (Eclipse/Prefect Legacy/Prefect v3) — confirmed with Paul that only Exchange Rates is on Prefect (legacy core_api design), all other active connectors are Eclipse template-based. Environment column + filter (QA/UAT/Prod/Not Deployed). Corrected work pool names to actual Azure infrastructure: `azure-aci-qa`, `azure-aci-uat`, `azure-aci-production`. Filter panel redesigned into labeled groups (Client, Environment, Framework, Status, Credential). Freshness monitoring: schedule-aware overdue/stale warnings with pulsing dots, freshness KPI card. Prefect UI link (`prefect.analyticlabs.io`) in header + deep-link "View in Prefect" buttons on active connectors. Inactive status filter for paused/error connectors.
- decided: core_api is NOT in the Prefect data path — architecture is clean (Prefect → Azure Storage → Snowflake). `global_config.py` env vars (CORE_URL, CORE_API_TOKEN) only needed by legacy connectors. New framework connectors use Prefect Blocks only. Paul confirmed: 0 connectors on Prefect v3 yet, 2 on Prefect Legacy (Exchange Rates), 21 on Eclipse.
- status: All 4 deliverables complete. Migration catalog (50 connectors), connector template docs, deploy flow UI, live deployment pipeline. Demo-ready.
- next: Phase 1A — credential tracking dashboard (`/launchpad-phase1a` in new session).

### 2026-05-13 — wiki-sync: deliverables verified

- did: Connector catalog built (`data/connectors.json` — 42 connectors: 8 active, 2 deploying, 4 ready, 28 planned across GEP/F92/ALDC_QA). Connector management page (`pages/connectors/index.html`) built and registered in SPA shell. Data pre-loaded via `window.LaunchpadData.connectors`. By-client breakdown: GEP 17 (4 active, 2 deploying, 3 ready, 8 planned), Fusion92 9 (7 active, 2 planned), ALDC_QA 1 (active).
- status: Core deliverables 1 (catalog) and 3 (UI page) complete. Deliverable 2 (connector template/generator) and 4 (live deployment pipeline triggering Prefect from UI) not yet built — these are the demo-day items.
- next: Build deploy flow (UI button → Prefect deployment → data lands). Amazon Ads US is the demo candidate.

### 2026-05-13 — Phase created

- did: Created phase tracker and `/launchpad-phase0c` boot prompt skill
- decided: This phase runs before/alongside Phase 1A to enable the full demo story
- next: Analyze prefect-connectors and core_api, build migration catalog, implement deploy flow

## See Also

- [[phase-0-monorepo-restructure]] — Repo structure this phase builds on
- [[phase-1a-credential-dashboard]] — Credential tracking that feeds into deployment
- [[../README]] — Launchpad project overview
