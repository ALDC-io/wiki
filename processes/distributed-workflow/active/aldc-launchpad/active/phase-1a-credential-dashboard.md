---
tags: [ops-platform, launchpad, credentials, dashboard, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 1A: Credential Tracking Dashboard

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1a.md` → `/launchpad-phase1a`
**Status:** Active — DEMO PRIORITY (team demo 2026-05-14)
**Effort:** 3–5 days
**Depends on:** Phase 0R (monorepo restructure)

## Goal

Build a data-driven, client-agnostic credential tracking dashboard inside the master platform. Replace hardcoded credential views in navira.html. Add Kanban board views (roadmap, bugs) per client. Include global client selector for Navira and Fusion92. Seed with real credential data.

## Deliverables

1. `platform/master/data/credentials.json` — 9 Navira + 6 Fusion92 credentials seeded
2. `platform/master/pages/credentials/index.html` — credential exchange hub page (KPIs, table, expandable detail, add form)
3. Client selector dropdown in topnav (reads from client-registry.json)
4. Client board views: Roadmap (Kanban), Bugs & Improvements (issue list), Credentials (filtered), Data Health, Migration
5. Updated `navira.html` — credential tab reads from credentials.json
6. Updated `index.html` — new route, topnav link, credentials.json pre-load
7. Updated `hub/index.html` — credential health metric card

## Credential Data Model

Status flow: `draft` → `link_sent` → `pending_client` → `submitted` → `validating` → `validated` → `provisioned`
Terminal: `expired`, `failed`

Each credential record: id, client, clientCode, provider, providerType, status, priority, statusHistory[], contact, expiresAt, prefectBlock, keyVaultRef, notes, zeusContext[]

The `zeusContext` array captures all events for future seeding into the client's own Zeus Memory instance.

## Board Views (per client)

Tab strip: `[Overview] [Roadmap] [Bugs] [Credentials] [Data Health] [Migration]`

- **Roadmap**: Kanban columns (Backlog → Planned → In Progress → Review → Done) with ticket cards
- **Bugs**: Sortable issue list with priority, status, assignee
- **Credentials**: Filtered view from credentials.json
- **Data Health**: Connector freshness, pipeline status
- **Migration**: Framework adoption tracking for existing clients

## Seed Data

### Navira (GEP) — 9 credentials
Google Ads (Windsor, pending), Meta (Windsor, pending), Amazon US (provisioned), Amazon UK (validated), Amazon CA (validated), Sellercloud (provisioned), SP-API (provisioned), TikTok (draft), Email Marketing (draft)

### Fusion92 — 6 credentials
Google Ads (Windsor, provisioned), Meta (Windsor, provisioned), LinkedIn (provisioned), DV360 (provisioned), CM360 (provisioned), SA360 (provisioned)

## Next Session Boot Prompt

````
You are working on **ALDC Launchpad Phase 1A** (Credential Tracking Dashboard).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\aldc-launchpad\active\phase-1a-credential-dashboard.md`
3. Read the approved plan: `C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md` — Phase 1A section
4. Read `C:\Users\PaulRussell\repos\aldc-launchpad\platform\master\styles\base.css` — design system tokens
5. Read `C:\Users\PaulRussell\repos\aldc-launchpad\platform\master\index.html` — SPA shell, routing, data pre-load pattern
6. Read `C:\Users\PaulRussell\repos\aldc-launchpad\shared\client-registry.json` — client list for selector

Goal: Build credential dashboard page, client selector, board views. Demo-ready for team presentation.
Design system: dark theme, use existing base.css tokens (cards, badges, tables, forms, buttons).
Pattern: vanilla HTML/CSS/JS, reads from window.LaunchpadData, standalone fetch fallback.
````

## See Also

- [[phase-0-monorepo-restructure]] — Prerequisite
- [[phase-1b-credential-submission]] — Backend (Azure Functions + Key Vault)
- [[phase-1c-prefect-provisioning]] — Block provisioning bridge
