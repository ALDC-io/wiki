---
tags: [workflow, ops-platform, launchpad, data, integration, phase-1, completed]
created: 2026-05-08
updated: 2026-05-11
completed: 2026-05-09
---

# Phase 1 — Data Layer + Live Integrations

**Priority:** High
**Effort:** ~5 days (with Claude Code)
**Status:** ✅ Complete (2026-05-09)
**Depends on:** Phase 0 (design system for consistent rendering)
**Unblocks:** Phase 2 (artifacts need data), Phase 3 (health needs live data)

## Objective

Replace all hardcoded numbers with a JSON data layer that sync scripts populate. Wire up live Jira + Zeus Memory integrations so the app reflects real-time project state.

## Scope

### 1.1 JSON Data Layer
- Create `data/state.json` — single file holding all dynamic state:
  - Ticket counts per phase (from Jira sync)
  - Prospect scores + pipeline stage
  - Infrastructure current capacity numbers
  - Last sync timestamp
  - Recent events / activity log
- All pages read from this file on load (fetch + render)
- Sync scripts write to this file (not to HTML)

### 1.2 Jira Sync → JSON
- Update `/navira-sync` skill to write to `data/state.json` instead of editing HTML
- Dashboard reads from JSON and renders dynamically
- Landing page metrics read from same JSON
- Add: ticket-level detail (key, summary, status, assignee, last updated)

### 1.3 Zeus Memory Integration
- Replace simulated Zeus suggestions in the wizard with live MCP calls during `/navira-sync`
- Write Zeus prospect data to `data/prospects.json`
- Wizard reads from this file for auto-fill suggestions
- Include: meeting notes summaries, decision log entries, prospect briefs

### 1.4 Persistent State for Generated Artifacts
- When wizard generates an onboarding package, save it to `data/onboardings/{client-code}.json`
- Packages persist across page refreshes
- Active onboardings list on landing page reads from this directory
- Each saved onboarding has: timestamp, inputs, generated tickets, client.yaml, status (draft/active/complete)

### Zeus Integration in Phase 1
- **Sync script**: Pull from both Jira (tickets) and Zeus Memory (decisions, meetings, prospect data) in one pass
- **Auto-fill**: Wizard queries `data/prospects.json` which was populated from Zeus Memory — no simulated data
- **Activity feed**: Zeus Memory provides meeting notes, email events, decision logs for the landing page feed

## Acceptance Criteria

- [ ] No hardcoded numbers in any HTML page — all read from `data/state.json`
- [ ] `/navira-sync` writes to JSON, pages render from JSON
- [ ] Wizard auto-fill works from Zeus-populated prospect data
- [ ] Generated onboarding packages persist in `data/onboardings/`
- [ ] Landing page activity feed shows real events

## Boot Prompt

````
You are working on **ALDC Launchpad Phase 1** (Data Layer + Live Integrations).

**Repo:** `C:\Users\PaulRussell\repos\aldc-shipyard\ops-platform\`
**Wiki:** Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\ops-platform\README.md` and `phase-0-design-system.md` for prior context.

**Goal:** Replace all hardcoded data with a JSON layer that sync scripts populate.

**Deliverables:**

1. **`data/state.json` schema** — design + implement. Holds: ticket counts per phase, prospect scores, infra capacity, last sync timestamp, recent events. All pages `fetch()` this on load.

2. **Update `/navira-sync` skill** (`skills/navira-sync.md` + `.claude/commands/navira-sync.md`) — instead of editing HTML, the sync now:
   a. Queries Jira via Atlassian MCP (cloudId: `239c1bf0-93f4-4201-95fe-ab73ce4a6eff`)
   b. Queries Zeus Memory via `mcp__ccx__cce_memory_search` for prospect data + decisions
   c. Writes everything to `data/state.json` + `data/prospects.json`
   d. Reports summary to user

3. **Update all pages** to read from JSON instead of hardcoded values. Priority: landing page, dashboard KPIs, wizard auto-fill.

4. **Artifact persistence** — when wizard generates a package, save to `data/onboardings/{code}.json`. Landing page reads this directory for "Active Onboardings" section.

**Key constraint:** Pages must work both with AND without the JSON files (graceful fallback to current hardcoded values if JSON not yet generated). This lets the POC keep working while the data layer is being built.
````
