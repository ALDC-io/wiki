---
tags: [ops-platform, launchpad, credentials, dashboard, active]
created: 2026-05-13
updated: 2026-05-14
deliverables_built: 2026-05-13
deliverables_complete: 2026-05-13
---

# Phase 1A: Credential Tracking Dashboard

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase1a.md` → `/launchpad-phase1a`
**Status:** Demo-ready — all 7 deliverables complete (team demo 2026-05-14)
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

## Session Log

### 2026-05-13 — wiki-sync: deliverables verified

- did: Credential data seeded (`data/credentials.json` — 15 credentials: 9 GEP + 6 F92, matching full seed spec). Credential exchange hub page built (`pages/credentials/index.html`). Client board views built (`pages/clients/boards/index.html`). Both routes registered in SPA shell with data pre-loaded via `window.LaunchpadData.credentials`. Hub page and navira.html updated (modified in working tree). Credential breakdown: 9 provisioned, 2 validated (Amazon UK/CA), 2 pending_client (Google Ads, Meta), 2 draft (TikTok, Email Marketing).
- status: Deliverables 1 (credentials.json), 2 (credentials page), 4 (board views), 6 (SPA routes + pre-load) complete. Deliverable 3 (client selector in topnav) and 5 (navira.html credential tab reads from JSON) need verification. Deliverable 7 (hub credential metric card) updated but needs verification.
- next: Verify client selector, navira.html integration, hub metric card. Visual QA before demo.

### 2026-05-13 — wiki-sync: Phase 1A demo-ready — all 7 deliverables complete

- did: Verified all 7 deliverables against demo checklist. (1) `credentials.json` — 15 credentials seeded (9 GEP + 6 F92, matching full spec: 9 provisioned, 2 validated, 2 pending_client, 2 draft). (2) Credential Exchange Hub page — KPIs, filterable table (All/GEP/F92), expandable detail rows with timeline + action buttons, Add Credential modal with auto-suggested auth types. (3) Global client selector added to SPA topnav — `Client: [▾ All | Navira (GEP) | Fusion92]` in status bar, reads from client-registry.json with hardcoded fallback, navigates to boards page filtered to selected client. (4) Client board views — 6-tab board page (Overview, Roadmap Kanban with drag-and-drop, Bugs, Credentials, Data Health, Migration) with GEP + F92 data. (5) navira.html credentials tab reads from `window.LaunchpadData.credentials` filtered to GEP. (6) SPA shell — `credentials` and `boards` routes registered, topnav Credentials link, `credentials.json` in data pre-load. (7) Hub credential health metric card — shows pending count, click-to-navigate.
- status: All 7 deliverables verified and complete. Demo checklist fully passing. Phase 1A is demo-ready.
- next: Demo (2026-05-14). Phase 1B (Azure Functions + Key Vault backend) is a separate session — start with `/launchpad-phase1b`.

### 2026-05-14 — Phase 1B integration: dashboard buttons wired to API

- did: Dashboard action buttons now call Phase 1B Azure Functions. "Request from Client" → `generate-link` (API key types) or `generate-oauth-url` (OAuth types), generates HMAC-signed URLs with copy+email buttons. "Enter Credential" → `enter-credential` (engineer direct entry to Key Vault). "Validate" → `get-status` (checks Key Vault for secret existence). Windsor OAuth remains status-only (managed externally). Added toast notification system, link result display with copy-to-clipboard, and mailto integration for sending links to clients.
- status: Phase 1A dashboard fully wired to Phase 1B backend. Frontend + backend integration complete.

## See Also

- [[phase-0-monorepo-restructure]] — Prerequisite
- [[phase-1b-credential-submission]] — Backend (Azure Functions + Key Vault) — dashboard buttons wired 2026-05-14
- [[phase-1c-prefect-provisioning]] — Block provisioning bridge
