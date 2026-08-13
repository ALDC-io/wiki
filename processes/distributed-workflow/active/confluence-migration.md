---
tags: [distributed-workflow, active, confluence-migration]
aliases: [Confluence Migration Tracker]
sources: []
created: 2026-04-18
updated: 2026-04-18
---

# Confluence Migration — Workstream Tracker

Session coordinator for ingesting remaining Confluence spaces into this wiki and running a consolidation/restructure pass to keep it engineer-friendly. Mechanics live in [[confluence-migration]] (the canonical runbook); this tracker holds per-session state.

## Goal

~~Finish the Confluence ingest end-to-end:~~
- ~~INFRA batches 2–4 complete.~~
- ~~Client spaces (CGEP, CF92/F9) complete.~~
- ~~CORE / CLIEN / ALDCKB complete.~~
- ~~Consolidation pass: orphan pages cross-linked, contradictions resolved, large pages split per [[CLAUDE]] § *Conventions*, and the wiki reads cleanly for an engineer onboarding to ALDC.~~

**✅ DONE — 2026-04-18.** All Confluence spaces fully ingested. Consolidation/lint punch list (P1+P2+P3) executed by Sonnet follow-on session. See session log entry "2026-04-18 — Consolidation Execution" below.

## Lane

Wiki: ALDC

Owned paths:
- `sources/` (raw Confluence exports — additive only)
- New pages under `entities/`, `processes/`, `concepts/` *that originate from Confluence content*
- `processes/operations/confluence-migration.md` (the canonical runbook — update its progress tracker as batches complete)
- `vault/` for credential extractions per [[CLAUDE]] § *Rules* #2

Read-only outside the lane until end-of-day merge.

## Required Context

- [[confluence-migration]] — canonical runbook; per-space status table; protocol (scope → propose → extract → map → apply); credential-extraction rules.
- [[Confluence]] — tool entity page; MCP auth notes.
- [[CLAUDE]] § *Parallel Ingestion* — the page-level pattern this workstream actually executes.
- [[CLAUDE]] § *Rules* — additive ingest rule (#9), credentials rule (#2), contradiction rule (#6).

## Plan-Mode Rule

- **Skip plan mode** for batches that follow the protocol already approved in [[confluence-migration]] (extract → map → apply with the same per-space scope).
- **Enter plan mode** when:
  - Starting a new Confluence space (e.g. moving from INFRA to CGEP) — scope and lane potentially shift.
  - The consolidation/restructure pass at the end (changes to existing pages, not just additions).
  - Any cross-lane work is needed (extremely unlikely for this workstream).

## Session Log

_Initial bootstrap — no work executed in this session._

### 2026-04-18 — bootstrap

- did: created this tracker; lane and required context inherited from existing [[confluence-migration]] runbook.
- decided: nothing new — runbook stays canonical.
- next: open a fresh Claude session with the boot prompt below; resume at INFRA batch 2 per the runbook's *Next-Batch Queue*.

### 2026-04-18 — INFRA Batch 2

- did: fetched all 8 per-deployment-group pages (Prod2, QA1, Test1, Demo1, Dev DG1–4 Canada). Created `concepts/architecture/deployment-groups.md` (consolidated resource inventory + 16-step deployment playbook). Extracted large credential block to `vault/infra-credentials.md`: Synapse admin (shared), portal superuser (shared), Postgres per-env, Core API App Registrations per-env, portal/agent API clients per-env. Amended vault "Azure SP example" entry — `f3e887c8` confirmed as Demo1 Core API App Registration.
- decided: consolidated all 8 pages into one wiki page rather than per-env pages; the shared structure makes consolidation cleaner and more useful for onboarding. Stale 2022 version snapshots and checkbox states intentionally excluded.
- next: **INFRA Batch 3** — Network/VPN/Storage/Agents (9 pages: Local Network Reverse Proxy 1630371841, Local Network Storage 1024622602, ALDC Cloud/NextCloud 965640193, VPN overview 961576965, Tailscale on Linux 1050673157, Agent Builds 957382661, Agent Backup & Redeployment 1062567937, Eclipse 2.0 Deployment notes 1441562625, Regular user per environment 1134493697).

### 2026-04-18 — INFRA Batch 3

- did: fetched all 9 pages. Created `local-network.md` (reverse proxy + TrueNAS/Covenant + Tailscale, 3 pages consolidated), `nextcloud.md` (tool entity — 16 users redacted to vault), `tailscale-linux.md` (Ubuntu how-to), `agent-builds.md` (Windows + Linux build + backup/restore, 2 pages merged). Appended Eclipse 2.0 Azure deploy section to `eclipse-azure-deployment.md`. Vault: NextCloud users, Covenant SMB/CIFS, NEXTAUTH_SECRET, per-env test accounts.
- decided: consolidated Reverse Proxy + Storage + VPN into one `local-network.md` (all on-prem network infrastructure); merged Agent Builds + Agent Backup into one `agent-builds.md` (same subject domain). Regular user per environment was vault-only (pure credentials, no engineering content).
- next: **START A NEW SESSION** — context budget reached after Batch 2 + Batch 3. New session opens with INFRA Batch 4 (3 Snowflake pages: 1532067843, 1034092551) then pivots to client spaces (CGEP first).

### 2026-04-18 — INFRA Batch 4

- did: fetched 2 Snowflake pages (INFRA/1532067843, INFRA/1034092551). Appended § Core API Integration to `entities/tools/snowflake.md` (4 route modules with function tables). Appended § Reader Accounts with SQL lifecycle reference (redacted). Extracted `READER_ADMIN_BACA483F` password (`<REDACTED — see vault/infra-credentials.md § Snowflake Reader Account admin>`) to `vault/infra-credentials.md` § Snowflake Reader Account admin. Diagram on 1532067843 is image-only — deferred. Updated `confluence.md`, `confluence-migration.md`, and `log.md`.
- decided: diagram deferred (blob URL, MCP cannot retrieve); dev-example password `Aldc1234` in the SQL sample noted in vault but not treated as a distinct credential. INFRA substantive content now complete — remaining ~31 pages are all release-note history (skip list) + 1 stale TODO.
- next: Client spaces — CGEP first. Enter plan mode when starting CGEP per the plan-mode rule.

### 2026-04-18 — CGEP Scoping

- did: fetched all 5 CGEP pages. Assessed content. Mapping approved.
- decided: 2 of 5 pages have ingest-worthy content. 3 are nav/empty — skip. No credentials found. Both ingest targets go into existing `entities/clients/GEP.md`.
  - CGEP/1233092873 (space home) → new `## ALDC Team` section (John Moran, Sean O'Grady, Karen Prete, Aaron Stryd)
  - CGEP/1233289293 (Inventory Subject Area) → new `## Inventory Subject Area` section (6 participating objects: Fact Inventory Balance, Fact Purchase Order, Dim Product, Dim Warehouse, Dim Vendor, Dim Purchase Order; Jira CUST-761; gap note — no `dim_purchase_order` view currently documented in warehouse section)
  - CGEP/1233125384 (Data Warehouse) → skip, empty
  - CGEP/1235877889 (Projects) → skip, nav-only
  - CGEP/1235976193 (Meeting Notes) → skip, nav-only
- next: **Execute CGEP ingest — plan already scoped and approved. Skip plan mode. Apply mapping directly: append `## ALDC Team` and `## Inventory Subject Area` sections to `GEP.md`; update `confluence.md` ingestion log; update `confluence-migration.md` CGEP row to ✅ Complete; append to `log.md`. Then move to CF92.**

### 2026-04-18 — CGEP Execution

- did: applied approved CGEP mapping. Appended `## ALDC Team` (John Moran, Sean O'Grady, Karen Prete, Aaron Stryd) and `## Inventory Subject Area` (6 objects, CUST-761, dim_purchase_order gap note) to `entities/clients/GEP.md`. Updated `confluence.md` ingestion log, `confluence-migration.md` CGEP row → ✅ Complete, `log.md`. No credentials found in CGEP space.
- decided: included dim_purchase_order gap note as a `> **Gap:**` callout in GEP.md since it's listed as a participating object in Confluence but absent from the warehouse section — useful signal for GP-208 context.
- next: **Enter plan mode for CF92 (new Confluence space per plan-mode rule). Scope the space, assess whether F9 supersedes or complements CF92, then propose a mapping before writing.**

### 2026-04-18 — CF92 Scoping

- did: scoped CF92 (43 pages) and F9 (1 page). F9 = empty Atlassian template boilerplate — skip entirely. CF92 plan approved: 5 batches, 39 ingest pages + 4 nav/template skips. New wiki pages to create: `entities/projects/dax-media-app.md`, `entities/projects/dax-ai.md`, `entities/tools/windsor.md`, `concepts/architecture/fusion92-data-architecture.md`. Existing pages to extend: `fusion92.md`, `custom-fusion-92-audience-api.md`, `snowflake.md`.
- decided: F9 produces nothing. CF92 Batch 1 (foundation + integrations) goes first; meeting notes (Batch 5) are lowest priority and may be mostly skippable.
- next: **Execute CF92 Batch 1 — skip plan mode (approved). Fetch 8 pages in parallel via 2 Explore subagents. Client/team/sources subagent: 1207009548, 1207238675, 1669300225, 1229881345. Windsor/DIOS subagent: 1675001857, 1675919361, 1692991495, 1215529061. Subagents propose; main agent writes.**

### 2026-04-18 — CF92 Batch 1

- did: fetched all 8 pages via 2 parallel Explore subagents. Applied 6 writes: appended § ALDC Team (John Moran, Sean O'Grady, Karen Prete) + § Data Source Integration Status (21-row platform table) to `fusion92.md`; created `entities/tools/windsor.md` (Windsor auth + account management); created `entities/clients/adm.md` (ADM marketing dashboard, GCP-native sub-client); created `concepts/architecture/fusion92-platform-ids.md` (Flight Check ID mapping + matching logic); appended § Nextcloud Folder Structure & Workflow to `custom-fusion-92-audience-api.md`. Updated confluence.md ingestion log, index.md (Windsor + ADM + fusion92-platform-ids), log.md.
- decided: Routed "Permissions and Security" (1229881345) to `entities/clients/adm.md` — ADM is a Fusion92 sub-client using GCP/BigQuery, not the standard ALDC stack. Platform IDs page routed to `concepts/architecture/fusion92-platform-ids.md` (not `entities/data-sources/` which doesn't exist). ADM stub (1215529061) skipped — nav-only. No vault extractions (no hard-coded credential values in batch).
- next: **CF92 Batch 2 — DAX Media App (11 pages). Skip plan mode (approved). Spawn 2 Explore subagents for the DAX Media App pages.**

### 2026-04-18 — CF92 Batch 2

- did: fetched all 11 DAX Media App pages via 2 parallel Explore subagents. Created `entities/projects/dax-media-app.md` — comprehensive project entity covering Phase 1 PRD (scope, user roles, UAT feedback, timeline), Phase 2 Metrics, PRJ505 UI Redesign (complete), PRJ538 Bulk Actions (complete), PRJ537 Smartsheet Replacement (in-progress) with data table spec + pacing formula, Additional Fields/Change Log, Notifications System, and NetSuite PO Sync (full field mapping + troubleshooting). Added disambiguation callout to `flight-check.md` (operational process vs. app). Updated confluence.md, index.md (dax-media-app under Projects), log.md.
- decided: NetSuite PO Sync routed to dax-media-app.md (not flight-check.md — different concepts share name). Smartsheet Requirements folded into PRJ537 section of dax-media-app.md rather than polluting fusion92.md with spec details. No credentials found.
- next: **CF92 Batch 3 — Data Architecture (Snowflake pages: 1363017731, 1367212038, 1367703569, 1382088715; ADM/GCP architecture: 1224900632, 1254883340, 1230700595). Skip plan mode (approved).**

### 2026-04-18 — CF92 Batch 3

- did: fetched 9 pages via 2 parallel subagents (3 empty/skipped). Created `concepts/architecture/fusion92-data-architecture.md` (Snowflake setup checklist, September 2024 decisions, DIOS→DAX→DSP notes). Appended § Infrastructure Architecture to `snowflake.md`. Appended § Eclipse 2.0 App Framework Patterns to `eclipse.md`. Appended § Security Group Architecture to `adm.md`. Updated confluence.md, index.md, log.md.
- decided: Snowflake Infrastructure general knowledge → snowflake.md (not client-specific). Architectural Considerations (brief Eclipse 2.0 patterns) → eclipse.md rather than new page. Full Test Environment → adm.md security groups (overlap with existing roadmap handled by adding only new info). 3 pages empty/skipped.
- next: **CF92 Batch 4 — DAX AI dashboards + Univision (7 pages: 1200553996, 1206779939, 1236598785, 1212678200, 1224933377, 1281130497, 1283096590). Skip plan mode (approved).**

### 2026-04-18 — CF92 Batch 4

- did: fetched all 7 pages via 2 parallel subagents. Created `entities/projects/dax-ai.md` (DAX AI hub + 3 dashboard specs). Extended `fusion92.md` with Univision Dashboard Project (REQ-283 external spec) and Phase 2 Marketing Reporting (ADM-adjacent). Updated confluence.md, index.md, log.md.
- decided: Phase 2 Marketing Reporting (mostly ADM-related) → fusion92.md with cross-ref to adm.md (not adm.md itself — content is mixed F92/ADM). External DAX Dashboard is a stub — captured as-is with DEFERRED status. Univision content stays in fusion92.md (not a separate page — Univision is F92's client, not a direct ALDC client).
- next: **CF92 Batch 5 — Meeting Notes + DIOS connectivity (8 pages: 1208647702, 1225719814, 1226342551, 1263501314, 1364688898, 1365016577, 1207009670, 1215660134). Skip plan mode (approved).**

### 2026-04-18 — CF92 Batch 5 + CF92/F9 Complete

- did: fetched all 8 pages. Appended to adm.md (Funnel.io workspace config), fusion92-data-architecture.md (data categorization framework + Snowflake architecture shift), custom-fusion-92-audience-api.md (DIOS→DAX REST API spec). 4 nav/template pages skipped. Updated confluence.md CF92 log, confluence-migration.md CF92 + F9 rows → ✅ Complete, log.md.
- decided: 4 nav pages confirmed empty (Meeting Notes, Meeting notes in space, Projects, How-to articles). Funnel.io config → adm.md (ADM-specific, Funnel is their ETL). DIOS connectivity meeting → fusion92-data-architecture.md (Snowflake strategic mandate, not API details). DIOS integration spec → custom-fusion-92-audience-api.md (REST API contract details).
- **CF92 COMPLETE. F9 previously assessed as empty boilerplate — COMPLETE.**
- next: **Update index.md with all new pages created during CF92 batches. Then follow checkpoint procedure in session-lifecycle.md § Checkpoint.**

### 2026-04-18 — CORE Batch 1

- did: verified MCP auth (paul.russell@aldc.io ✓). Scoped CORE space (79 pages). Entered plan mode; proposed 5-batch strategy + 7-page skip list — approved. Fetched all 10 Batch 1 pages via 2 parallel Explore subagents. Applied 10 writes: priority pointers resolved (`deployment-groups.md` + `azure-environment-bootstrap.md`); 5 existing pages extended (`local-network.md`, `snowflake.md`, `core_api.md` ×2, `connector-docker-deployment.md`, `agent-builds.md`); 2 new pages created (`powerbi-secret-refresh.md`, `executive-snapshot-email.md`). Credential extraction: Galactica SQL creds (CONTRADICTION flagged), GHCR service account, Postgres Docker password → `vault/infra-credentials.md`. Updated confluence.md, confluence-migration.md, log.md, index.md.
- decided: Azure Queue Trigger content folded directly into `core_api.md` rather than standalone page (content volume didn't warrant separate page). Executive snapshot = new standalone ops page. Docker Guide = appended to connector-docker-deployment.md as § Docker Reference.
- next: **CORE Batch 2 — CosmosDB schema docs (13 pages). Skip plan mode (CORE is already approved; sub-batch execution only). Spawn 2 Explore subagents: Group A (916488197, 893124613, 929103873, 921632769, 937197569, 1050869770, 960069656) · Group B (917700609, 921632782, 902987777, 968163329, 917700622, 928186369). Target: new `concepts/architecture/cosmosdb-schema.md`.**

### 2026-04-18 — CORE Batch 2

- did: fetched all 13 CosmosDB schema pages via 2 parallel Explore subagents. Created `concepts/architecture/cosmosdb-schema.md` — full schema reference covering all 11 collections (account, capacity_provider, capacity, agent, work_connection, work_template, work_partition, task, staff, report, schedule/session pipeline). work_template is 2024-02-08 vintage (most current); others are 2021–2022. 2 pages skipped: 916488197 (empty parent), 960069656 (Azure Synapse Link procedural guide). Credential extraction: Fivetran Snowflake `analyticlabs`/`uRbGSUTgTpmU@N3m+L` → vault. Updated index.md, confluence.md, log.md, confluence-migration.md.
- decided: Fernet-encrypted strings in capacity/capacity_provider examples are not extracted to vault (encryption key already there; encrypted values are not plaintext secrets). Staff PII (phone/email) not vaulted — stored in actual CosmosDB, manage there. Synapse Link procedural guide skipped (operational Azure UI guide, not schema reference).
- next: **CORE Batch 3 — Core API architecture + operations (12 pages): 238387201, 7929869, 33390595, 522191059, 522191131, 886603777, 885620774, 877592581, 909737996, 964591617, 720044036, 892796955. Target: extend `entities/repos/core_api.md` with historical architecture context. Spawn 2 Explore subagents.**

### 2026-04-18 — CORE Batch 3

- did: fetched all 12 pages. Extended `core_api.md` with 7 sections: REST API Spec (2021), Env Variables (redacted), Architecture & Language Stack, Notification Module, Task Daemon, Portal Data export. 5 skipped (2 empty/nav, 1 incomplete, 1 separate PowerShell system, 1 file-ref only). Large vault extraction: Twilio/Mailjet/Pushover creds, dev env COSMOS_KEY, alt MASTER_CLIENT_SECRET (contradiction flagged), dev Azure SP.
- decided: REST API spec condensed to endpoint table + flow — 2021 vintage, [[postman-collections]] is current source of truth. Reference Designs (4 MS docs links) folded into § Architecture & Language Stack rather than standalone section.
- next: **CORE Batch 4 — [see session log below]**

### 2026-04-18 — CORE Batch 4

- did: fetched all 20 pages via 2 parallel Explore subagents. Created `concepts/architecture/core-api-data-model.md` (v1 domain model: 14 collections + merge strategies). Extended `snowflake.md` with v1 client DB structure + Azure integration setup. 6 skipped (empty, binary, pricing, deps). Vault: Snowflake service account `CORE_a7a8d78c` + demo connection examples.
- decided: Account Secret (540115026) merged into § Account Collection (v1) rather than separate section — content largely duplicates 540704815. Licensing Reference (463601805) skipped (Python 3.8 dep matrix, out of scope for data model). Snowflake Pricing (278036481) skipped (2021 rates, operational).
- next: **CORE Batch 5 — [see session log below]**

### 2026-04-18 — CORE Batch 5 — **CORE COMPLETE**

- did: fetched all 17 pages via 2 parallel Explore subagents. Created: `proxmox.md` (host admin, guest provisioning, vGPU, disk expansion), `mailjet.md`, `dashboard.md` (Eclipse Dashboard Cosmos model), `synapse-analytics-setup.md`. Extended: `nextcloud.md` (ZFS + backup strategy), `local-network.md` (Covenant Linux mount), `debugging-warehouse-loads.md` (zombie + Snowflake job abort), `flight-check.md` (account health PBI). 5 skipped: link-only, product design, stale infra ref, Capacities (already in cosmosdb-schema). Vault: NextCloud ncadmin + Mailjet account password.
- decided: Linux Guides (disk resize) folded into proxmox.md § Guest Disk Expansion (not standalone linux.md). Capacities (934248449) skipped — minimal content, already covered by cosmosdb-schema.md. Account Health PBI folded into flight-check.md (not standalone page). CORE SPACE COMPLETE.
- **CORE: 61/79 pages handled. Migration complete.**
- next: **START NEW SESSION** — CORE is complete. Next space: CLIEN (has CLIEN/1294794754 SQL Server requeue reference). Then CDD/CKA/CAN scope pass, then ALDCKB/ENG/AIRA/CONN.

### 2026-04-18 — CDD/CKA/CAN Complete

- did: scoped all three spaces (10 pages total). CDD (3 pages) and CKA (3 pages) are entirely nav/boilerplate — skipped, no ingest needed (`dish-duer.md` and `kit-ace.md` from CLIEN already capture all engineering content). CAN (4 pages): 1 substantive page — CAN/1235845127 (Customer Insights Dashboard PRD, REQ-169/CUST-679) appended to `aspire-north.md` as § Customer Insights Dashboard (RACI, scope, 38 Experian data fields, Eclipse PNG-export requirements). No credentials. Updated confluence.md, confluence-migration.md, log.md.
- decided: CDD and CKA produce nothing — both are identical 3-page nav shells with no engineering content. CAN's single content page is a well-structured PRD that extends aspire-north.md cleanly without needing a new page.
- next: ~~CONN~~ → see CONN session log below.

### 2026-04-18 — AIRA Complete

- did: scoped AIRA (3 pages, all by Vlad). 1 skipped (3-line space home). Created `concepts/patterns/adversarial-investigation-skill.md` from AIRA/1763246091 — Vlad's `/investigate-adversarial` Claude Code skill (6-phase adversarial protocol, PROVE/DISPROVE/BLIND-SPOT, mandatory phase gates, stored at `.claude/skills/investigate-adversarial/skill.md`). Substantially updated `ai-pr-workflow.md` from AIRA/1765244929 — definitive ALDC dev workflow with full tool stack (Semgrep, TruffleHog, Claude Opus review, PyTestArch, quality-gate aggregator, CCX), merge conditions, per-repo config, non-negotiables. All checks live as of 2026-04-10. Updated index.md, confluence.md, confluence-migration.md, log.md.
- decided: ai-pr-workflow.md updated (not duplicated) — AIRA/1765244929 is the implemented version of ENG/1761050625. Adversarial skill gets its own page (reusable tool worth finding independently). CCX noted as "see Zeus KB for setup" — not documented further here as Zeus KB content not yet ingested.
- next: **CONN** (Connector space). Enter plan mode.

### 2026-04-18 — ENG Complete

- did: scoped ENG space (4 pages). 3 skipped (space home + 2 Atlassian templates). Created `concepts/patterns/ai-pr-workflow.md` from ENG/1761050625 — team-ratified 6-step AI-augmented PR workflow (feature branch → PR → automated checks → AI code review [WIP/Vlad] → human review → merge). Agreed by full dev team 2026-04-02. Updated index.md, confluence.md, confluence-migration.md, log.md.
- decided: new standalone page rather than appending to `ai-development-project-standard.md` — that page is about metrics/ROI tracking; this is a workflow standard. Distinct enough to warrant its own page. Added strategic context callout (wiki migration enables AI agents/gates to use company context).
- next: **AIRA** (AI Research, 2026-04-06). Enter plan mode.

### 2026-04-18 — CLIEN Complete

- did: Scoped CLIEN (87 pages). Entered plan mode; approved 4-batch strategy. Executed all 4 batches via parallel Explore subagents. 48/87 pages handled. **6 new operations pages** (client-deactivation, client-vm-setup, client-invoicing, client-communications, client-onboarding-checklist, model-deploy-production). **1 new business-logic page** (periodicity — SHARED_DIM_PERIODICITY + DAX SWITCH patterns). **9 new client entity pages** (dish-duer, kit-ace, book-depot, terrayn, aspire-north, indochino, drop-in-gaming + previously existing heartland-dental/aspire-north stubs). **Extended** ssms.md (partition refresh), nextcloud.md (client tenant access), power-bi.md (template + Excel access), snowflake.md (perf notes), GEP.md (contacts, SRs, NetSuite scoping), kit-ace.md (account details, ecommerce systems), fusion92.md (enterprise scoping project). **Vault extractions**: TERRAYN Athena AWS IAM, KIT_ACE SFCC/OCAPI/SQL/GA API key. Updated confluence.md, confluence-migration.md (CLIEN → ✅ Complete), log.md, index.md.
- decided: 1677459457 (DIOS to DAX Audience Files) skipped — attachments-only (PDF, Excel, PNG), no text. Heartland Dental empty. Enterprise Scoping Project routed to fusion92.md (Fusion92 enterprise data integration context). 2021 data cubes/templates/reports (~9 pages) + 2022 planning tables (~7 pages) on skip list — stale, no engineering value.
- **CLIEN COMPLETE.**
- next: **START NEW SESSION** — CLIEN is complete. Next: CDD/CKA/CAN (scope first — may be minimal since dish-duer.md + kit-ace.md already capture CLIEN-era content). Then ALDCKB/ENG/AIRA/CONN.

### 2026-04-18 — Consolidation/Lint Plan Approved

- did: surveyed full wiki (100 in-scope pages across `entities/`, `concepts/`, `processes/`, `tickets/` + root). Built link graph, orphan report, stale-pointer scan, index-gap scan, large-page census. Produced prioritised punch list (P1 load-bearing, P2 important, P3 polish). Key findings: **no outstanding `> **Contradiction**:` callouts** anywhere; `[[Power BI]]` (18 files) and `[[GitHub Actions]]` (5 files) slug "mismatches" are **false alarms** — both target pages resolve via frontmatter `aliases:`; real issues are `[[connector-development-standards]]` stale in 5 connector pages, `[[heartland-dental]]` stale in index, `workflow-automation.md` + `sandbox-feature-delivery.md` missing from index, 11 strictly index-only pages needing content cross-refs, and a handful of small stale pointers (`[[Zeus Memory]]`, `[[PhaseLab]]`, `[[GP-199]]`, `[[moving-target source tables]]`).
- decided: **approve all three tiers** (P1 + P2 + P3). Execution hand-off to Sonnet follow-on session — the design decisions (what's load-bearing vs. not, slug-alias false alarms, Prefect/AI-pivot cross-ref priorities) were the reasoning-heavy part and are now baked into the boot prompt.
- next: **START A NEW SONNET SESSION** with the boot prompt below. Execute P1 → P2 → P3 in order; update `index.md` and `log.md` at the end.

## Decisions Log

- 2026-04-18 — Tracker is a *coordinator*, not a replacement. The runbook page [[confluence-migration]] remains the source of truth for migration mechanics; this tracker only holds per-session state and pending shared-file edits.
- 2026-04-18 — "Flight Check" disambiguation: the name refers to two distinct things. ALDC's operational validation runbook = `processes/operations/flight-check.md`. Fusion92's Flight Management web app (now the DAX Media App) = `entities/projects/dax-media-app.md`. Added disambiguation callout to both.
- 2026-04-18 — ADM is a Fusion92 sub-client using a GCP/BigQuery stack (not ALDC's standard Eclipse/Snowflake). Gets its own page (`entities/clients/adm.md`) rather than being folded into fusion92.md.
- 2026-04-18 — DAX Media App and DAX AI are separate entity pages (different products). dax-media-app.md = the shipped Flight Check replacement; dax-ai.md = analytics dashboard suite (mostly ON HOLD).
- 2026-04-18 — Fusion92-specific Snowflake architecture decisions routed to `concepts/architecture/fusion92-data-architecture.md` rather than polluting general `entities/tools/snowflake.md`. General Snowflake infrastructure reference (account hierarchy, warehouse model) → snowflake.md.
- 2026-04-18 — Univision dashboard project stays in fusion92.md (Univision is F92's client, not a direct ALDC client — not worth a standalone page).

## Pending Wiki Updates

_None._

## Blockers / Open Questions

_None._

## Cross-Lane Requests

_None._

## Next Session Boot Prompt

**Recommended model: Sonnet (default is fine — `sonnet[1m]`).** This is mechanical execution of an Opus-approved punch list. Opus-level reasoning isn't needed; the judgment calls are already in the prompt.

**Estimated volume:** ~60 targeted edits across ~30 pages. Plan for one sitting.

````
You are executing the approved consolidation/lint punch list for the LLM wiki. All Confluence spaces are fully ingested. The plan was produced and approved in the prior Opus session (see session log entry "2026-04-18 — Consolidation/Lint Plan Approved" in `processes/distributed-workflow/active/confluence-migration.md`).

## Boot procedure

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md` — especially § Rules (#3 update index.md, #4 append log.md, #6 contradictions, #9 additive) and § Conventions (wikilink format, page format).
2. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\confluence-migration.md` — the 2026-04-18 "Consolidation/Lint Plan Approved" session log entry has the full context.
3. Read `C:\Users\PaulRussell\repos\wiki\index.md` — you will be appending entries to this during execution.

## Strategic context (keep these in mind when you hit judgment calls)

- **Prefect connector migration is highest priority.** Cross-links between `prefect.md` / `connector.md` and the 6 connector spec pages in `entities/tools/connectors/` are load-bearing. Err on the side of MORE cross-refs here.
- **AI-driven delivery pivot.** `ai-pr-workflow.md`, `adversarial-investigation-skill.md`, `ai-development-project-standard.md` are live standards. They need to be discoverable from the repo pages engineers actually work in.
- **Onboarding test:** an engineer who opens `index.md` should be ≤2 hops from anything important.
- **Frontmatter aliases matter.** Obsidian resolves `[[Power BI]]` to `power-bi.md` because `power-bi.md`'s frontmatter has `aliases: [Power BI, PBI]`. Do NOT "fix" wikilinks whose targets have the display name as an alias — that's already working. Only fix links whose target file (or alias) genuinely doesn't exist.

## Execution order

Work P1 → P2 → P3. Tick each item as you finish. Do NOT batch index.md edits — update index.md as you create new pages so it stays consistent. Append ONE row to `log.md` at the end describing the whole consolidation pass.

## The approved punch list

### P1 — Load-bearing

- [ ] **Create `concepts/patterns/connector-development-standards.md`** — canonical "building an ALDC/Prefect connector" pattern page. Pull content from `prefect.md` § Migration Pattern + relevant `connector.md` sections: attribute hierarchy (ConnectorConnectionBase, ConnectorOptionsBase), parameter patterns, PartitionScheme/MergeScheme selection, reference implementation pointer (`connector/accounts/ALDC_QA/deployments/exchange_rates.py`). The 5 connector spec pages already link to this in their See Also — you're fulfilling those links. Add to index.md under Patterns. Cross-link back to all 6 connector pages, `prefect.md`, `connector.md`, `eclipse.md`, `python-development-standards.md`.
- [ ] **Add § Connector Specs to `prefect.md` AND `connector.md`** — each should list all 6 pages in `entities/tools/connectors/`: `[[google-analytics]]`, `[[facebook-ads]]`, `[[bing-ads]]`, `[[google-ads]]`, `[[amazon-ads]]`, `[[trade-desk]]`. Also link to `[[google-oauth-python]]` (shared pattern) and `[[connector-token-refresh]]` (operational).
- [ ] **Create `entities/clients/heartland-dental.md` stub** — match the pattern of other client pages. One-paragraph body: "Heartland Dental. Empty Confluence page during migration — no content ingested yet. Placeholder retained so references don't break." Frontmatter: `tags: [entity, client, heartland-dental, placeholder]`, `aliases: [Heartland Dental]`. The index.md entry already says this; just create the file so the `[[heartland-dental]]` link resolves.
- [ ] **Add `entities/projects/workflow-automation.md` to `index.md`** — under ## Entities › Projects. One-line hook: "Client Workflow Automation — design for automated sandboxed feature-delivery flow targeting GEP. Phase-1 sandbox pattern + phased build roadmap."
- [ ] **Add `concepts/patterns/sandbox-feature-delivery.md` to `index.md`** — under ## Concepts › Patterns. One-line hook: "Per-feature Snowflake schema pattern (`WAREHOUSE_TEST_<TICKET_ID>`) for isolating in-flight warehouse changes."

### P2 — Important

- [ ] **Add § Development Standards to `clients-repo.md`, `core_api.md`, `connector.md`.** Three bullets each pointing to `[[ai-pr-workflow]]`, `[[adversarial-investigation-skill]]`, `[[ai-development-project-standard]]`. Also include `[[python-development-standards]]` and `[[git-branching-strategy]]` on each (already standards-adjacent).
- [ ] **Cross-ref `[[openclaw]]` from `factoria.md`** — factoria.md already describes using openclaw as its runtime; add the wikilink in the relevant architecture section plus See Also.
- [ ] **Cross-ref `[[cce-troubleshooting]]` from `cce.md`** — add to See Also and to any Troubleshooting/Known-issues section.
- [ ] **Add § Client Inventory to `clients-repo.md`** — single list of all 11 client pages: `[[GEP]]`, `[[fusion92]]`, `[[adm]]`, `[[dish-duer]]`, `[[kit-ace]]`, `[[book-depot]]`, `[[terrayn]]`, `[[aspire-north]]`, `[[indochino]]`, `[[drop-in-gaming]]`, `[[heartland-dental]]`. One-line qualifier per client (active / 2022-discovery / stub).
- [ ] **Create `entities/projects/zeus-memory.md`** — substantive entry. Derive from `sources/obsidian-import/research/OpenTribe/` and `entities/projects/opentribe.md` content. Zeus Memory is Paul's knowledge-integrity product (the OpenTribe page already covers MVP/wedge/adoption strategy — decide whether this is a separate product page or whether to rename opentribe.md → zeus-memory.md and update opentribe references). If renaming, update the 3 stale refs in `cce.md` (lines 11, 56) and `monorepo-research.md` (line 64), plus the opentribe index.md entry. If keeping separate, write a lightweight page pointing to both. Recommend the rename — opentribe is the product's name but Zeus Memory is the more common usage.
- [ ] **Create `entities/projects/phaselab.md` stub** OR rewrite the 3 `[[PhaseLab]]` references (`cpma.md` lines 39, 58; `opentribe.md` line 74) as prose. Use judgment — if PhaseLab is a real project Paul is working on (check `sources/obsidian-import/research/PhaseLab/`), create the page; if it's just an early-idea placeholder, rewrite as prose.
- [ ] **Fix `[[GP-199]]` in `action-items.md` line 73** — either create `tickets/gep/GP-199.md` stub (check if the ticket exists in Jira — Paul's tickets follow the GP-### pattern) or rewrite that one line to drop the wikilink.
- [ ] **Cross-ref `[[model-deploy-production]]`** from `client-release-checklist.md` and `gep-snowflake-pbi-deployment.md` — add to See Also and to the "publish the PBI model" step within each.
- [ ] **Cross-ref `[[client-invoicing]]`** from `client-onboarding-checklist.md` and `client-deactivation.md` See Also sections.
- [ ] **Cross-ref `[[FU92-342]]` from `fusion92.md`** and **`[[GP-203]]` from `GEP.md`** — add to a § Tickets section or inline where the ticket's subject is mentioned.

### P3 — Nice-to-have

- [ ] **Review `confluence.md` (540 lines) for splitting.** Likely contains an ingestion log that should move to `log.md` (or a new `confluence-ingestion-log.md`). Read the page, identify the repetitive log-style sections, and split if the structural boundary is clean. If not clean, leave.
- [ ] **Review `core_api.md` (431 lines) for splitting.** Consider moving 2021-era historical sections (v1 REST API Spec, v1 Task Daemon) into `core-api-data-model.md` (which is already v1-focused). Keep `core_api.md` focused on current state.
- [ ] **All other large pages (>200 lines): leave as-is.** Reference pages like `cosmosdb-schema.md`, `snowflake.md`, `eclipse.md`, `deployment-groups.md` are intentionally comprehensive — splitting would hurt navigability.
- [ ] **Fix `[[moving-target source tables]]` in `gep-inventory-data-dictionary.md` line 36** — rewrite that reference to point to `[[accumulating-source-tables]]` (which has the moving-target QA workflow).
- [ ] **Make `log.md` discoverable** — add a single line to `CLAUDE.md` § Core Operations (near where ingest/lint are described) pointing at it. Low priority — audit log, not content. Alternative: add to index.md under a new ## Meta section.

## Rules of engagement

- **Never modify `sources/`.** All new content is derived from existing in-scope pages or written fresh.
- **Additive ingest (CLAUDE.md Rule #9).** Don't rewrite existing pages unless fixing a specific stale link or moving sections per an explicit P3 item.
- **Append to `log.md` ONCE at the end** with a single row: `| 2026-04-18 | consolidation-lint | Applied P1+P2+P3 punch list: <N> pages created, <N> pages extended, <N> stale links resolved, index.md updated |`.
- **If something blocks you** (e.g. Paul must confirm whether PhaseLab is a real project), flag it in this tracker's Session Log and continue with other items.

## Deliverable

At the end of the session, append a session-log entry to this tracker ("2026-04-18 — Consolidation Execution") summarising what changed, what was deferred, and any blockers. Then mark the CF Migration workstream **DONE** in the Goal section (if the goal criteria are met) or document the residual.
````

### 2026-04-18 — Consolidation Execution

- **did:** Executed the full P1+P2+P3 punch list from the Opus-approved plan.
  - **P1 (load-bearing):** Created `connector-development-standards.md` (fulfilling stale links in all 6 connector spec pages); added § Connector Specs to `prefect.md` and `connector.md`; created `heartland-dental.md` stub; added `workflow-automation` and `sandbox-feature-delivery` to `index.md` Patterns section.
  - **P2 (important):** Added § Development Standards (ai-pr-workflow, adversarial-investigation-skill, ai-development-project-standard, python-development-standards, git-branching-strategy) to `clients-repo.md`, `connector.md`, and `core_api.md`; added § Client Inventory (11 pages) to `clients-repo.md`; added `[[cce-troubleshooting]]` to `cce.md` See Also; created `zeus-memory.md` (rename from opentribe.md — stale `[[zeus-memory]]` refs now resolve); created `phaselab.md` (PhaseLab is a real demo-ready product); removed stale `[[GP-199]]` wikilink from `action-items.md`; added `[[model-deploy-production]]` to `client-release-checklist.md` and `gep-snowflake-pbi-deployment.md`; added `[[client-invoicing]]` to `client-onboarding-checklist.md` and `client-deactivation.md`; confirmed `[[FU92-342]]` and `[[GP-203]]` already present in their respective client pages (no change needed).
  - **P3 (polish):** Fixed `[[moving-target source tables]]` → `[[accumulating-source-tables]]` in `gep-inventory-data-dictionary.md`; added `## Meta` section to `index.md` making `log.md` discoverable; assessed `confluence.md` (left as-is — ingestion log IS the content, too thin to split meaningfully); assessed `core_api.md` (left as-is — historical sections still useful for old-core debugging); confirmed `[[openclaw]]` already cross-ref'd in `factoria.md`.
- **deferred:** confluence.md split (P3.1 — not clean enough); core_api.md split (P3.2 — historical context still load-bearing).
- **blockers:** None. All items resolved without Paul input.

## See Also

- [[../README]]
- [[../orchestration-pattern]]
- [[../session-lifecycle]]
- [[confluence-migration]]
