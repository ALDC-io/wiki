---
tags: [distributed-workflow, active, dv-444, eclipse, gep, navira]
aliases: [DV-444 Tracker, Dashboard Rename Tracker]
sources: []
created: 2026-04-21
updated: 2026-04-21
---

# DV-444 — Dashboard Rename Tracker

Rename the Navira-demo sidebar **Apps** group entry from "Dashboard" to "SKU Profitability" for GEP/Navira and its downstream shared customers. Data change on an `application_metadata` CosmosDB document; no eclipse-2.1 code change.

## Goal

"Done" = Navira users (and downstream sharers) see "SKU Profitability" in the left sidebar's Apps group in production. The feature branch `feature/paulrussell/dv-444/change-display-name-of-dashboard` is expected to close with zero commits.

## Lane

Wiki: ALDC

Owned paths:
- `tickets/dv/DV-444.md` (new; created in this workstream)
- `processes/distributed-workflow/active/dv-444-dashboard-rename.md` (this file)

**Shared-file updates** applied directly in this session (no concurrent workstreams on these files): `entities/repos/core_api.md`, `action-items.md`, `index.md`, `log.md`. See *Applied Wiki Updates* below.

**Out of lane**: the feature branch exists but will not receive commits — no eclipse-2.1 code edit is required.

Read-only everywhere else.

## Required Context

- [[DV-444]] — the ticket page (scope + target record + decision path)
- [[core_api]] — has the *Known API Gaps* section noting the missing v2 PATCH for `application_metadata`
- [[dashboard]] — dashboard feature primer
- [[cosmosdb-schema]] — CosmosDB container reference
- [[GEP]] — client

## Plan-Mode Rule

Plan-mode-first was applied for Phase 1 (scope discovery). Lifted after the rename surface was confirmed (Apps-group entry → data change). Execution sessions proceed without plan-mode. Re-enter plan-mode only if scope changes.

## Session Log

### 2026-04-21 — Phase 1 discovery + Option C chosen

- did: confirmed target element is the `navira-demo` Application's `app_name` field (not a code label, not a dashboard's `name`). Started local eclipse (`:3000`) + core_api v2 FastAPI (`:8000`). Located record in QA cosmos (`aldcdevcsdb3c01`) → `application_metadata` container → partition `da8904db` → id `6d26400a-618a-46a2-8fa8-5d53a48928ab`, current `app_name = "Dashboard"`. Dispatched Sonnet discovery subagent; surfaced blocker that v2 API has no update endpoint. Chose Option C (direct CosmosDB patch) over A (uncomment legacy router — too broad) and B (add v2 PATCH — scope creep). Wrote this tracker + `tickets/dv/DV-444.md` + *Known API Gaps* section on [[core_api]] + follow-up action item.
- decided: new value is `"SKU Profitability"` (verbatim from ticket). Option C for DV-444 execution. Option B (v2 PATCH endpoint) becomes a separate core_api follow-up.
- next: Paul executes the QA patch via Azure Portal Data Explorer. Verify via browser reload. Once confirmed, progress to PROD patch in a coordinated window.

### 2026-04-21 — Phase 1 QA patch complete ✅

- did: Paul patched `application_metadata` doc (id `6d26400a-618a-46a2-8fa8-5d53a48928ab`, partition `da8904db`) in `aldcdevcsdb3c01` via Azure Portal Data Explorer. Changed `app_name` from `"Dashboard"` to `"SKU Profitability"`. Verified visually: after a hard refresh of `http://localhost:3000`, the Apps group entry now reads "SKU Profitability" and still links to `/application/navira-demo`.
- decided: Phase 1 complete. Sharing propagation working as predicted (single document, automatic fan-out to all viewers).
- next: Phase 2 — repeat the same patch on `aldcprodcsdb1c01` during a coordinated window with GEP/Navira. Confirm prod cosmos access first (see Blockers).

### 2026-04-21 — Phase 2 PROD patch complete ✅

- did: Patched `application_metadata` doc in `aldcprodcsdb1c01` via Data Explorer → `app_name = "SKU Profitability"`. Initial UI verification attempt via the Azure default URL (`https://aldcprodwbapeclipse1c01.azurewebsites.net/`) was blocked by CORS — prod core_api only allowlists `https://eclipse.analyticlabs.io`. Discovered the real prod URLs: **eclipse-2.1 UI = `https://eclipse.analyticlabs.io/`** and **prod core_api = `https://api.eclipse.analyticlabs.io/v2/`**. Logged in at `eclipse.analyticlabs.io`; sidebar now shows "SKU Profitability" in the Apps group, linking to `/application/navira-demo`. Sharing propagation (single document) means GEP/Navira + all downstream sharers see the new label.
- decided: DV-444 complete. No eclipse-2.1 code change was ever needed — pure data fix. Feature branch `feature/paulrussell/dv-444/change-display-name-of-dashboard` can be deleted.
- next: Close Jira DV-444. Delete the unused feature branch. Address secondary findings (PostHog `/ingest/*` middleware misconfig on prod eclipse-2.1) as separate tickets.

## Decisions Log

- 2026-04-21 — Rename target value is `"SKU Profitability"` (verbatim from ticket). Explicitly not `"SKU Profitability Dashboard"` — the word "Dashboard" in the label is the root of the client's confusion.
- 2026-04-21 — Surface is data (CosmosDB application record), not code. No eclipse-2.1 PR will be opened. Feature branch closes with zero commits.
- 2026-04-21 — **Option C** (direct CosmosDB patch via Data Explorer) chosen. A rejected (would expose all legacy v1 routes). B deferred to its own core_api follow-up ticket.
- 2026-04-21 — **Phase 1 QA verified** ✅ — `app_name` rename in `aldcdevcsdb3c01` propagated to the Navira sidebar entry on `http://localhost:3000` after a browser reload. Confirms both the patch approach and the sharing-propagation prediction.
- 2026-04-21 — **Prod URLs discovered during verification**: eclipse-2.1 UI at `https://eclipse.analyticlabs.io/`, prod core_api at `https://api.eclipse.analyticlabs.io/v2/`. Neither was in the wiki before DV-444. Documented on [[entities/repos/eclipse|eclipse (repo)]], [[deployment-groups]] Production 2 table, and [[core_api]] § Known API Gaps. Earlier assumption that `aldcprodwbapeclipse1c01` would eventually cut over to `eclipse.aldc.io` was **wrong** — the two prod deploys are on separate brand domains (`aldc.io` vs `analyticlabs.io`), not a pending CNAME flip. Wiki corrected.
- 2026-04-21 — **Phase 2 PROD verified** ✅ — `eclipse.analyticlabs.io` sidebar now shows "SKU Profitability". DV-444 closed.

## Applied Wiki Updates

Applied directly in this session (no concurrent workstream on these files):

- `entities/repos/core_api.md` — added `## Known API Gaps` section documenting the missing v2 update endpoint for `application_metadata`, the commented-out legacy handler, and the DV-444 workaround.
- `action-items.md` — added Open item for the core_api v2 PATCH follow-up.
- `index.md` — added `### DV (Eclipse 2.1)` ticket section with `[[DV-444]]`; added `[[processes/distributed-workflow/active/dv-444-dashboard-rename]]` under *Distributed Workflow*.
- `log.md` — appended row for this workstream's Phase-1 discovery; second row added 2026-04-21 for the eclipse-2.1 prod URL documentation.
- `concepts/architecture/deployment-groups.md` — added Eclipse-2.1 Web App (`aldcprodwbapeclipse1c01`, `https://aldcprodwbapeclipse1c01.azurewebsites.net/`) to Production 2 — DG1 table, with a callout disambiguating it from the legacy `aldcprodwbapportal1c01` portal. Surfaced during DV-444 prod verification (2026-04-21).
- `entities/repos/eclipse.md` — added a staleness callout to the top disambiguation noting the page describes the legacy Next 14 version, with a pointer to the current eclipse-2.1 prod URL. Full page refresh still pending.

## Pending Wiki Updates

_None._

## Blockers / Open Questions

- 2026-04-21 — **Prod cosmos credentials** needed for Phase-2 PROD patch. Assumed to live under `vault/core-api-local-settings.md`'s prod block — confirm access before the prod window.

## Cross-Lane Requests

- 2026-04-21 — `entities/repos/eclipse.md` describes Pages Router Next 14; the actual `eclipse` repo on disk is Next 15 App Router pointing at a FastAPI backend on `:8000/v2/`. Out of scope for DV-444. Raise as a standalone wiki-refresh task.
- 2026-04-21 — `entities/repos/core_api.md` (beyond the *Known API Gaps* section added here) describes only the Azure Functions v1 side; the repo also exposes a v2 FastAPI surface on `:8000/v2/` which is the active backend for the current eclipse repo. Full page refresh is out of scope for DV-444.

## Next Session Boot Prompt

````
You are resuming the DV-444 workstream. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\dv-444-dashboard-rename.md`.
3. Read the ticket page: `C:\Users\PaulRussell\repos\wiki\tickets\dv\DV-444.md`.
4. Pick up at the *next:* line of the most recent Session Log entry.

Plan-mode rule: execution sessions proceed without plan-mode. Re-enter plan-mode only if scope changes.

When done, follow the checkpoint procedure in
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## See Also

- [[DV-444]]
- [[../README]]
- [[../orchestration-pattern]]
- [[../session-lifecycle]]
- [[core_api]]
- [[GEP]]
