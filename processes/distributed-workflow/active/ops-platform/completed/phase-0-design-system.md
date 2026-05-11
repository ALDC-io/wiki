---
tags: [workflow, ops-platform, launchpad, design, ui, ux, phase-0, completed]
created: 2026-05-08
updated: 2026-05-11
completed: 2026-05-08
---

# Phase 0 — Design System + Landing Page Overhaul

**Priority:** Immediate
**Effort:** ~5 days (with Claude Code)
**Status:** ✅ Complete (2026-05-08)
**Depends on:** Nothing
**Unblocks:** All subsequent phases (consistent UI foundation)

## Objective

Transform the POC from inline-styled HTML pages into a cohesive product with a shared design system, modern landing page, and proper app identity ("ALDC Launchpad").

## Scope

### 0.1 App Rename + Branding
- Rename from "ops-platform" to **ALDC Launchpad** across all pages
- Update page titles, nav labels, footer text
- Design a simple wordmark/logo for the top nav
- Rename folder: `ops-platform/` → `launchpad/` (or keep `ops-platform/` as internal name, brand as Launchpad in UI)

### 0.2 Shared CSS Design System
- Extract a `styles/base.css` from the common patterns across all 10 pages
- Components: cards, badges, tables, forms, buttons, progress bars, ring charts, pills, callouts
- Color tokens: background, surface, text, accent (blue, green, amber, red, purple, gold)
- Typography scale: headings, body, labels, captions, mono
- Dark theme as default; light theme prep (CSS custom properties)

### 0.3 Landing Page Redesign
Current: progress ring + phase mini-rings + role summary cards + 2 lane buttons. Too sparse for a home page.

Target — a modern dashboard home page with:
- **Header bar**: Launchpad logo + client count + overall health indicator + last synced timestamp
- **Metrics row**: Total clients (active), connectors running, data volume today, alerts, days to deadline
- **Client health grid**: One card per active client showing: name, industry, connector count, data freshness (last successful run), credential health, status pill. Click to drill into engineering dashboard.
- **Recent activity feed**: Last 10 events (ticket completed, connector deployed, credential received, alert fired). Populated from `data/events.json`.
- **Active onboardings**: Which clients are mid-wizard, what step they're on
- **Quick actions**: "Onboard New Client" (→ wizard), "Sync Jira" (→ runs sync), "View Prospects" (→ prospects)
- **Role summaries**: Keep but make collapsible — CEO, EI Lead, TM, Engineer

### 0.4 App Shell Improvements
- Replace iframe with proper SPA-style page loading (fetch + innerHTML swap) for cross-page communication
- Add breadcrumbs showing current location
- Persist active tab/page in URL hash for deep linking
- Add a "last synced" indicator in the nav bar

### Zeus Integration in Phase 0
- **Landing page recent activity**: Zeus Memory can feed meeting notes, email events, decision logs into the activity feed
- **Client health grid**: Zeus can provide last-known data freshness per client from observability data

## Acceptance Criteria

- [ ] All pages share `styles/base.css` — no inline style blocks > 10 lines
- [ ] Landing page shows live client health grid (even if data is simulated for POC)
- [ ] App shell uses hash routing, not iframe
- [ ] "ALDC Launchpad" branding visible in nav + page titles
- [ ] Mobile-responsive: landing page renders cleanly on tablet

## Boot Prompt

````
You are working on **ALDC Launchpad Phase 0** (Design System + Landing Page Overhaul).

**Repo:** `C:\Users\PaulRussell\repos\aldc-shipyard\ops-platform\`
**Wiki:** Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\ops-platform\README.md` for full project context.

**Goal:** Transform the POC into a cohesive product. Three deliverables:

1. **Shared CSS design system** (`styles/base.css`) — extract common patterns from all 10 pages. Color tokens, typography, card/badge/table/form components. All pages should import this instead of inline styles.

2. **Landing page redesign** (`pages/hub/index.html`) — modern dashboard layout:
   - Metrics row (clients, connectors, volume, alerts)
   - Client health grid (per-client cards with freshness + status)
   - Recent activity feed
   - Active onboardings
   - Quick actions (Onboard, Sync, Prospects)
   - Collapsible role summaries

3. **App shell upgrade** (`index.html`) — replace iframe with fetch+innerHTML SPA pattern. Hash routing. Breadcrumbs. Last-synced indicator. Rename to "ALDC Launchpad."

**Reference the existing pages** for component patterns — don't redesign from scratch, extract and standardize.

**Important:** Keep all pages functional. Don't break the wizard, dashboard, or framework pages while refactoring CSS. Extract styles incrementally.
````
