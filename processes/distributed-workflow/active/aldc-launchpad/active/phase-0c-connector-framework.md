---
tags: [launchpad, connectors, framework, deployment, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 0C: Connector Framework & Live Deployment

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase0c.md` → `/launchpad-phase0c`
**Status:** Active
**Effort:** 1–2 days
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

### 2026-05-13 — Phase created

- did: Created phase tracker and `/launchpad-phase0c` boot prompt skill
- decided: This phase runs before/alongside Phase 1A to enable the full demo story
- next: Analyze prefect-connectors and core_api, build migration catalog, implement deploy flow

## See Also

- [[phase-0-monorepo-restructure]] — Repo structure this phase builds on
- [[phase-1a-credential-dashboard]] — Credential tracking that feeds into deployment
- [[../README]] — Launchpad project overview
