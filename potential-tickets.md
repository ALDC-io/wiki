---
tags: [potential-tickets, improvements, pre-jira, index]
aliases: [Potential Tickets, Improvement Tickets, Pre-Jira Catalog]
sources: []
created: 2026-04-21
updated: 2026-04-21
---

# Potential Tickets

Catalog of potential Jira tickets — gaps, bugs, tech-debt, and improvements surfaced during work on other issues. Each entry is a **pre-Jira draft**: enough detail that when it's time to act, a Jira ticket can be filed from the entry without re-discovery.

**Not a TODO list.** For general personal follow-ups and reminders, use [[action-items]]. This file is specifically for *would-become-a-Jira-ticket* items that need scope, evidence, and a proposed fix captured before they can be worked on.

## How to use

When you run into a gap or bug that isn't in scope for your current work:

1. Add an entry under **Open** below, using the format in *Entry format*.
2. Link back to the ticket / page / session that surfaced it so the breadcrumb to the original context survives.
3. When you file the Jira ticket, move the entry to **Filed** and append `· filed as <JIRA-ID>` on the first line.
4. If the proposal is declined or becomes moot, move it to **Rejected** with a one-line reason.

## Entry format

```
### <Title> — <area or client>

- **Surfaced:** `YYYY-MM-DD` during [[source ticket or page]]
- **Category:** bug | tech-debt | improvement | security | docs
- **Priority:** low | medium | high | critical
- **Description:** <one or two sentences on the observable problem or gap>
- **Root cause / evidence:** <code refs with file:line, observed behaviour, or data anomalies>
- **Proposed fix:** <what a Jira ticket would scope to>
- **Estimated effort:** S | M | L (optional)
```

---

## Open

### `_BASE_ACT_SALE_RET` DAX measure references a missing column — GEP PBI

- **Surfaced:** `2026-04-21` during Phase 6 Tranche A XMLA smoke test against [[GEP]] sandbox dataset (seeded from live TEST PBIX, `repos/power_bi/custom/GEP/2026_03 Data Model/Data Model.pbix`)
- **Category:** bug / tech-debt
- **Priority:** low
- **Description:** Tabular Editor flagged an error on measure `_BASE_ACT_SALE_RET` when the sandbox dataset was loaded: *"Expression Column 'in table' cannot be found or may not be used in this expression"*. The underscore prefix is ALDC's convention for hidden base measures. The DAX references a column that doesn't exist in its expected table — same error would appear in the live TEST PBIX since the sandbox was seeded from it.
- **Root cause / evidence:** Not caused by Phase 6 M edits (only Source + Tenant_Database steps were changed; no column renames). Most likely a Power Query column rename happened at some point (e.g. `SALES_RETURNED` → `Sales Returned` via `Table.RenameColumns` in the `Order Line` query) but the dependent DAX measure still references the pre-rename name. Classic model-drift tech debt in a long-lived `.pbix`.
- **Proposed fix:** Open the live TEST PBIX in Power BI Desktop → Model view → find `_BASE_ACT_SALE_RET` → inspect DAX → identify the broken column reference → update to match the current (post-rename) column name → Close & Apply → republish to GEP Test Models workspace. Low risk — the measure is hidden so clients won't see any report change; only measures that reference `_BASE_ACT_SALE_RET` (if any) regain functionality. Repeat for the Production PBIX after TEST validates.
- **Estimated effort:** S

### Committed credential: `CORE_API_CLIENT_TOKEN` in GEP PBIX files — security

- **Surfaced:** `2026-04-21` during Phase 6 Tranche A.0.6 parameterisation of the GEP seed PBIX
- **Category:** security
- **Priority:** medium
- **Description:** Every dated GEP `.pbix` in `repos/power_bi/custom/GEP/*/Data Model.pbix` has `CORE_API_CLIENT_TOKEN` baked in as a Power Query parameter with literal value `RkZGRkZGRkYwMDAwOmFsRGM5ODc2IQ==` (base64 decodes to `FFFFFFFF0000:alDc9876!` — a basic-auth-style credential for core_api). Wiki rule #2 forbids credentials in non-vault locations; this is a binary-file-credential leak reaching into every PBIX version committed since the parameter was introduced.
- **Root cause / evidence:** The PBIX template (per [[Power BI]] tool page § Report Template) uses `CORE_API_*` parameters to hit core_api's `/v1/report/describe` endpoint for glossary and short-code resolution. The token was hardcoded into the parameter default value rather than injected at publish-time via dataset-level parameter overrides. Inspect any GEP `.pbix` → Home → Transform data → Manage Parameters → `CORE_API_CLIENT_TOKEN` to reproduce.
- **Proposed fix:** (a) Extract the literal value to `wiki/vault/credentials.md` under a new `Core API — GEP` section (unique if it's GEP-only; if other clients share the token, generalise). (b) Decide on rotation: the token format `FFFFFFFF0000:alDc9876!` looks like a static service account credential — rotating requires coordination with whoever owns the core_api auth model. (c) Long-term: parameterise the token externally via workspace-level dataset parameters at publish time rather than PBIX default. Check [[powerbi-secret-refresh]] for whether a similar rotation runbook already applies. (d) After rotation, republish every GEP PBIX with the new value so historical `.pbix` files don't stay pinned to the old token. Note that old `.pbix` files in Git LFS history will retain the leaked token until repo GC/rewrite — probably acceptable if rotated, since the token is then inert.
- **Estimated effort:** M (rotation coordination + republish) — or S if "just vault and leave token in place" is acceptable v1.

### v2 PATCH endpoint for `application_metadata` — core_api

- **Surfaced:** `2026-04-21` during [[DV-444]]
- **Category:** improvement / tech-debt
- **Priority:** medium
- **Description:** The FastAPI v2 surface on core_api has GET endpoints for applications (`/hierarchy/`, `/metadata/`) but no PATCH/PUT for updating `application_metadata` records. Renaming `app_name` (or any other field) currently requires direct CosmosDB bypass via Azure Portal Data Explorer.
- **Root cause / evidence:** `core_api/api/applications/router.py` — only GET routes. `core_api/v1/route_application.py:308-329` has `update_metadata_item`, but `core_api/api/main.py:164` commented out the legacy router so it's unreachable. See [[core_api]] § *Known API Gaps*.
- **Proposed fix:** Add `PATCH /v2/applications/{id}` on the v2 applications router that validates input and writes via the same CosmosDB layer used by the legacy handler. Handle camelCase-vs-snake_case translation (v2 schema = `appName`; raw doc = `app_name`). Gate behind an `Application_Edit` RBAC permission check.
- **Estimated effort:** S

### PostHog `/ingest/*` auth-gating on prod eclipse-2.1 — eclipse

- **Surfaced:** `2026-04-21` during [[DV-444]] prod verification
- **Category:** bug
- **Priority:** low
- **Description:** PostHog analytics requests through the `/ingest/*` reverse-proxy on prod eclipse-2.1 (`https://eclipse.analyticlabs.io/`) are being 307-redirected to `/login`. Browser console shows `Uncaught SyntaxError: Unexpected token '<'` on `exception-autocapture.js`, `config.js`, etc. — the scripts return login-page HTML instead of JavaScript. Analytics is silently broken for authenticated users.
- **Root cause / evidence:** Observed on `https://eclipse.analyticlabs.io/` 2026-04-21. The NextAuth middleware matcher likely covers `/ingest/*` when it should exclude it. PostHog requests to `/ingest/static/exception-autocapture.js?v=1.350.0`, `/ingest/array/phc_*/config.js`, `/ingest/e/`, and `/ingest/flags/` all receive a 307 redirect to the login page.
- **Proposed fix:** Exclude `/ingest/` from the NextAuth middleware matcher in `eclipse/middleware.ts` (or equivalent in the App Router middleware config). Reference: [[entities/repos/eclipse|eclipse (repo)]].
- **Estimated effort:** S

### Wiki refresh — eclipse repo page (Next 15 App Router)

- **Surfaced:** `2026-04-21` during [[DV-444]] scope discovery
- **Category:** docs
- **Priority:** low
- **Description:** [[entities/repos/eclipse|eclipse (repo)]] describes the legacy Next 14 Pages Router version of the repo in detail (`pages/` layout, Mantine 7, NextUI, dual UI kits, etc.). The repo on disk has since been rewritten to Next 15 App Router (branch `eclipse-2.1`, `src/app/` route groups, Mantine 8, TanStack Query, typed `src/app/api/coreAPI/` per-domain modules). Only a staleness callout has been added so far.
- **Root cause / evidence:** Current architecture visible in `C:/Users/PaulRussell/repos/eclipse/src/app/` and `package.json` (`next: ^15.4.3`). Staleness callout at the top of [[entities/repos/eclipse|eclipse (repo)]] added 2026-04-21.
- **Proposed fix:** Full page refresh covering the new architecture (App Router route groups, `src/app/api/coreAPI/` typed modules, Mantine 8, TanStack Query v5, `libServer.ts` proxy pattern, NextAuth with camelCase-aliased JWT claims). Keep a short *Legacy (Pages Router, archived)* section for historical reference. Pair with the companion core_api refresh below.
- **Estimated effort:** M

### Wiki refresh — core_api FastAPI v2 coverage

- **Surfaced:** `2026-04-21` during [[DV-444]] scope discovery
- **Category:** docs
- **Priority:** low
- **Description:** [[core_api]] primarily documents the Azure Functions v1 surface (port 7071, `/v1/`, `func start`, `local.settings.json`, `route_*.py` modules). The repo also exposes a FastAPI v2 surface (port 8000, `/v2/`, `python run.py`, `.env`-based config, `api/*/router.py` per-domain routers) which is the **active backend** for the current eclipse frontend. Only the *Known API Gaps* section touches v2 so far.
- **Root cause / evidence:** `core_api/api/main.py` (FastAPI app definition), `core_api/run.py` + `run_debug.py` (uvicorn entrypoints), `core_api/api/*/router.py` (per-domain routers — applications, dashboards, catalog, users, rbac, etc.). Prod v2 lives at `https://api.eclipse.analyticlabs.io/v2/`. See [[core_api]] § *Known API Gaps*.
- **Proposed fix:** Add companion v2 documentation covering: entrypoints (`run.py` vs `run_debug.py`, uvicorn config), auth (JWT via `/v2/users/login/` signed with `JWT_SECRET`), per-domain router organisation, prod URL, env-var-driven config (`.env` replacing `local.settings.json`), and how v2 and v1 coexist in the same repo. Tie into the paired eclipse-2.1 frontend refresh.
- **Estimated effort:** M

### `.pbip` format migration — power_bi repo

- **Surfaced:** `2026-04-20` during [[entities/repos/power_bi|power_bi (repo)]] documentation execution session
- **Category:** tech-debt / improvement
- **Priority:** medium
- **Description:** The `power_bi` repo stores 94 Power BI reports as opaque `.pbix` binaries tracked via Git LFS (~16 GB total). Binaries cannot be diffed, reviewed in PRs, merged, or text-searched. Every report change is an all-or-nothing LFS blob swap, which also means no PR review is possible for data-model changes. Migrating to the `.pbip` (Power BI Project) folder format would unpack each report into `Model/` (TMDL) + `Report/` (JSON) directories that ARE diff-able, review-able, and partially merge-able — closing most of the "binary file problem" documented on the repo wiki page and enabling review-gated model changes for the first time.
- **Root cause / evidence:** All reports are `.pbix`/`.pbit` binary — only 9 text-readable files out of ~100 artefacts (confirmed in [[entities/repos/power_bi|power_bi (repo)]] § Repo Layout, § Tech Debt). Power BI Desktop has supported `.pbip` export since 2024; ALDC has not adopted it. The binary model is also why the repo is ~16 GB on disk — `.pbip` folder format is vastly smaller.
- **Proposed fix:** (1) Pilot: convert one active GEP `.pbix` to `.pbip` in a branch; confirm `publish-from-.pbip` → PBI Service still works end-to-end (data source refresh, gateway, RLS, permissions). (2) If the pipeline holds, convert the active client reports (GEP, FUSION_92, ALDC_SALES) incrementally. (3) Leave frozen/legacy client reports (DISH_DUER, KIT_ACE, BOOK_DEPOT, ALDC_FINANCE) as `.pbix` — they won't receive further changes and conversion is wasted effort. (4) Update [[model-deploy-production]] and [[gep-snowflake-pbi-deployment]] runbooks to reflect `.pbip` publish steps. (5) Pairs well with the archive-repo split (would split `power_bi_archive` off the frozen clients and cut ~30% of LFS bandwidth).
- **Estimated effort:** L (per-report conversion + publish-pipeline verification + runbook updates + team training; can be done incrementally across multiple sprints)

### Prod-to-test data share stability — GEP

- **Surfaced:** `2026-04-21` during [[GP-197]] feature-update dry-run (sandbox task chain failed on `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK`)
- **Category:** improvement / ops
- **Priority:** medium
- **Description:** The `PROD_DG1_GEP` outbound share silently loses tables — either when Eclipse refreshes a table via `CREATE OR REPLACE TABLE` (drops object-level grant) or when a new table is added to PROD but never added to the share. Gaps only surface at runtime when the task chain fails, not at deploy time.
- **Root cause / evidence:** Three known incidents in 6 weeks (CURRENT_MAIN_INVENTORY_PANDL, CURRENT_MAIN_PURCHASEITEM, CURRENT_REPORT_ALL_ORDERS_UK). Confirmed object exists in PROD but is absent from share. See [[GP-PENDING-data-share-stability]] for full research with four solution options.
- **Proposed fix:** Option A — replace per-table share grants with schema-level `FUTURE` grants (ACCOUNTADMIN required, one-time fix, prevents recurrence). Fall back to Option B — `deploy.py --check-share` scan (now implemented) as detection layer. Full option analysis in [[GP-PENDING-data-share-stability]].
- **Estimated effort:** S (Option A — one SQL statement per schema if ACCOUNTADMIN access confirmed)

---

## Filed

_Entries that have been filed as Jira tickets — move here with `· filed as <JIRA-ID>` appended to the first line._

---

## Rejected

_Proposals decided against — kept for context so they aren't re-proposed._

---

## See Also

- [[action-items]] — personal TODO registry (different purpose: items that don't need to become Jira tickets)
- [[CLAUDE]] — wiki schema and conventions
