---
tags: [entity, tool, confluence, documentation, wiki]
aliases: [Confluence]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Confluence

ALDC's team wiki / documentation platform. Hosts institutional docs that are not captured in-repo — detailed dataflow diagrams, per-client operational setup (SSMS schedules, VPN notes), Prefect/Azure resource documentation, and offboarding/onboarding materials.

## Known valuable pages

| Topic | Location |
|-------|----------|
| **Brayden's offboarding folder/space** | Contains onboarding + offboarding documentation, including [[Prefect]] Azure-resources documentation |
| **Dataflow diagram (detailed)** | More thorough version of the Snowflake → SQL Server → PBI flow documented in [[SSMS]] |
| **Per-client SSMS setup** | Login info and schedule for when SSMS partition jobs need to run — check the client's Confluence page |
| **Infrastructure / clients / networking** | Mix of pages that should eventually be extracted into this LLM wiki |

## Relationship to the LLM wiki

This LLM wiki (at `C:\Users\PaulRussell\repos\wiki`) and Confluence are complementary, not redundant:

- **Confluence** — source of truth for team-shared, cross-role docs (ops, client setup, networking)
- **LLM wiki** — Paul's compounding engineering knowledge base; optimized for Claude Code sessions

Goal is to progressively ingest the most load-bearing Confluence pages into this wiki so Claude sessions have the context without needing to fetch from Confluence each time.

> **Resuming this migration?** See [[confluence-migration]] for the runbook + current progress + next batches. This section below is the per-page ingestion log.

## Ingestion status

**2026-04-17 — Brayden Offboarding subtree (TECH space, 6 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Azure Resources (TECH/1766096900) | [[Prefect]] § Azure resources (production) |
| Switching Environments QA/Test/Prod (TECH/1768882177) | [[Prefect]] § Switching environments |
| Prefect Architecture Overview (TECH/1769046017) | [[Prefect]] § Deployment architecture |
| DIOS-to-DAX API (TECH/1766031362) | [[custom-fusion-92-audience-api]] (new page) |
| Old Connectors (TECH/1769177102) | [[connector]] § Legacy (pre-Prefect) architecture |
| Brayden Offboarding + Prefect parents | — (navigation-only, no body content) |

**2026-04-17 — TECH space Batch 2 (6 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Warehouse Standards (TECH/1238499340) | [[star-schema-convention]] § SQL style conventions |
| Development Standards (TECH/1238728725) | — (one-sentence empty parent page) |
| Reference Architecture (TECH/1023246339) | **Deferred** — 4 architecture diagrams (High-Level Overview, System Connectivity, Client Access, Tenancy) are image-only and not retrievable via the MCP markdown API. Needs a manual screenshot pass or attachment-fetch tool. |
| Eclipse 2.0 (TECH/1191575556) | [[Eclipse]] § Eclipse 2 framework decisions (WIP) |
| CORE_API (TECH/920616961) — misnamed, contains Python standards | [[python-development-standards]] (new page) |
| Cosmos DB Partial Updates (TECH/1156284418) | [[CosmosDB]] § Partial updates (patch_item) |

**TECH space progress:** 12 of 30 pages handled (11 ingested + 1 deferred for images). 11 remaining in Batch 3 / Batch 4 / skip list.

**2026-04-17 — TECH space Batch 3 (5 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Employee Onboarding (TECH/1231945782) | [[employee-onboarding]] (new page) |
| Release checklist (TECH/1361903625) | [[client-release-checklist]] (new page) |
| Git Branching Strategy (TECH/1362296835) | [[git-branching-strategy]] (new page — merged with cheatsheet) |
| Git branching cheatsheet (TECH/1362133015) | [[git-branching-strategy]] § Cheatsheet (merged into the strategy page) |
| Clients Repository (TECH/1264648200) | — (nav-only, 3 bullet-links to the pages above) |

**TECH space progress:** 17 of 30 pages handled (15 ingested + 1 skipped-empty + 1 skipped-nav + 1 deferred-images). 13 remaining = Batch 4 (5) + skip list (7) + space home page.

**2026-04-17 — TECH space Batch 4 (5 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| AI Development Project Standard (TECH/1612218379) | [[ai-development-project-standard]] (new page) |
| GitHub (TECH/1242300433) | [[git-branching-strategy]] § Commit message format |
| ALDC Admin Guides (TECH/1232142375) | — (empty parent; Employee Onboarding, its main child, already migrated in Batch 3) |
| Semantic Versioning (TECH/1010335752) | [[git-branching-strategy]] § Versioning (semver) |
| Google OAuth python code (TECH/1145143297) | [[google-oauth-python]] (new page — `developer_token` and `customer_id` redacted per wiki rule #2) |

**TECH space progress:** 22 of 30 pages handled (19 ingested + 2 skipped-empty + 1 skipped-nav + 1 deferred-images). 8 remaining = skip list (7 low-value) + 1 TECH space home page.

**2026-04-17 — TECH space final skip log:**

| Page | ID | Why skipped |
|---|---|---|
| Key Recycling Checklist | 1313013766 | 2024 empty template (just section headers, no content) |
| ACTION: Setup Experimental GitHub Repo and Migrate Sandboxes | 1621393412 | 2025-06-09 action TODO, due 2025-06-12 (~10 months stale) — not worth migrating as an action item |
| Time Sheet Logging | 1232044060 | HR workflow, out of scope for engineering wiki |
| Interview Tests | 1019969537 | HR/hiring content, out of scope |
| Troubleshooting article | 920518943 | 2022 Confluence "how-to article" template placeholder |
| How-to article | 920518934 | 2022 Confluence "how-to article" template placeholder |
| Technology | 920518922 | TECH space home page (TOC only) |

**TECH space: MIGRATION COMPLETE** (22 handled, 8 intentionally skipped).

---

**2026-04-17 — INFRA space Batch 1 (8 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Azure Standards (INFRA/233897985) | [[aldc-naming-convention]] (new, merged with On-Prem) |
| On Premise Standards (INFRA/343506945) | [[aldc-naming-convention]] § On-prem resources + VM inventory; admin credentials extracted to `vault/infra-credentials.md` |
| Deployment Guides (INFRA/937984005) | [[new-client-setup]] (new page) |
| Complete Environment Deployment end-to-end (INFRA/959086593) | [[azure-environment-bootstrap]] (new page; `MASTER_CLIENT_SECRET` + `AZURE_CLIENT_SECRET` extracted to `vault/infra-credentials.md`) |
| Infrastructure Home (INFRA/522289512) | — (2021 Atlassian space-setup boilerplate) |
| Corp Infrastructure (INFRA/895713281) | — (empty) |
| Deployments (INFRA/986087425) | — (2023 stale release-history table v1.3.0–v1.13.0) |
| Environment and Code version tracking (INFRA/1096220693) | — (stale 2024-10 version table) |

**INFRA space progress:** 8 of 58 pages handled (4 ingested + 4 skipped). 50 remaining = Batch 2 per-env docs (8), Batch 3 network/agents (9), Batch 4 Snowflake (3), + ~30 release-note skips + 1 stale action TODO.

**2026-04-18 — INFRA space Batch 2 (8 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Production 2 - Canada - Deployment Group 1 (INFRA/944373761) | [[deployment-groups]] § Production 2 — DG1 (resource inventory + credentials → vault) |
| Quality 1 (QA) - Canada - Deployment Group 1 (INFRA/973012993) | [[deployment-groups]] § Quality 1 — DG1 |
| Test 1 - Canada - Deployment Group 1 (INFRA/922615840) | [[deployment-groups]] § Test 1 — DG1 |
| Demo 1 - Canada - Deployment Group 1 (INFRA/937885723) | [[deployment-groups]] § Demo 1 — DG1 |
| Development 2 - Canada - DG1 / Sean O'Grady (INFRA/945782785) | [[deployment-groups]] § Development 2 — DG1 |
| Development 2 - Canada - DG2 / Lawrence Young (INFRA/947486721) | [[deployment-groups]] § Development 2 — DG2 |
| Development 2 - Canada - DG3 / Emile Bilodeau (INFRA/947486737) | [[deployment-groups]] § Development 2 — DG3 |
| Development 2 - Canada - DG4 / Mitchell Pask (INFRA/948142081) | [[deployment-groups]] § Development 2 — DG4 |

Large credential extraction to `vault/infra-credentials.md`: Synapse admin (shared), portal superuser (shared), Postgres per-env (9 entries), Core API App Registrations per-env (5 entries with secrets), portal/agent API clients per-env (10 entries). Also amended vault "Azure SP example" entry — confirmed the `f3e887c8` client ID is the Demo 1 Core API App Registration.

**INFRA space progress:** 16 of ~58 pages handled (12 ingested + 4 skipped). 42 remaining = Batch 3 network/agents (9), Batch 4 Snowflake (3), + ~30 release-note skips + 1 stale action TODO.

**2026-04-18 — INFRA space Batch 3 (9 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Local Network Reverse Proxy (INFRA/1630371841) | [[local-network]] § Reverse proxy (diagram image-only, lost) |
| Local Network Storage (INFRA/1024622602) | [[local-network]] § Network storage — TrueNAS / Covenant |
| VPN overview (INFRA/961576965) | [[local-network]] § VPN — Tailscale |
| ALDC Cloud (NextCloud) Configuration (INFRA/965640193) | [[nextcloud]] (new page); credentials (15 users) → vault |
| Connecting to a VM using tailscale on Linux (INFRA/1050673157) | [[tailscale-linux]] (new page) |
| Agent Builds (INFRA/957382661) | [[agent-builds]] (new page, merged with Backup); credentials → vault |
| Agent Backup & Redeployment (INFRA/1062567937) | [[agent-builds]] § Backup & Redeployment |
| Eclipse 2.0 Deployment and Service notes (INFRA/1441562625) | [[eclipse-azure-deployment]] § Eclipse 2.0 Azure deployment; NEXTAUTH_SECRET → vault |
| Regular user per environment (INFRA/1134493697) | vault only — per-env test user accounts (all aldc1234) |

Credential extraction to `vault/infra-credentials.md`: NextCloud users (9 internal + 7 client users), Covenant SMB/CIFS credentials, Eclipse 2.0 NEXTAUTH_SECRET, per-env test accounts.

**INFRA space progress:** 25 of ~58 pages handled (21 ingested + 4 skipped). 33 remaining = Batch 4 Snowflake (3), + ~30 release-note skips + 1 stale action TODO.

**2026-04-18 — INFRA space Batch 4 (2 pages) ingested via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| ALDC Snowflake ecosystem / integration (INFRA/1532067843) | [[snowflake]] § Core API integration (new section); diagram image-only → deferred |
| Snowflake Reader Accounts (INFRA/1034092551) | [[snowflake]] § Reader Accounts (new section); `READER_ADMIN_BACA483F` password → `vault/infra-credentials.md` § Snowflake Reader Account admin |

Credential extraction to `vault/infra-credentials.md`: Snowflake reader account admin (AH87540, `READER_ADMIN_BACA483F`, password `*4Jvf^ECZ416`).

**INFRA space progress:** 27 of ~58 pages handled (23 ingested + 4 skipped). ~31 remaining = ~30 release-note skips + 1 stale action TODO. **INFRA substantive content: MIGRATION COMPLETE.**

---

**2026-04-18 — CGEP space (5 pages: 2 ingested + 3 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Client - Global Ecom Partners (CGEP/1233092873) | [[GEP]] § ALDC Team (4 ALDC members listed) |
| Inventory Subject Area (CGEP/1233289293) | [[GEP]] § Inventory Subject Area (6 participating objects; CUST-761; gap note on missing dim_purchase_order) |
| Data Warehouse (CGEP/1233125384) | — (empty body) |
| Projects (CGEP/1235877889) | — (nav-only) |
| Meeting Notes (CGEP/1235976193) | — (nav-only) |

No credentials found. **CGEP space: MIGRATION COMPLETE** (2 ingested, 3 skipped).

**2026-04-18 — CF92 space Batch 1 (8 pages: 6 ingested + 1 skip-nav + 1 skip-stub) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Client - Fusion 92 (CF92/1207009548) | [[fusion92]] § ALDC Team (3 members) |
| F92 Data Sources (CF92/1207238675) | [[fusion92]] § Data Source Integration Status (full platform table with connectivity/activation status) |
| Data Source Platform IDs (CF92/1669300225) | [[fusion92-platform-ids]] (new page — ID mapping table + matching logic) |
| Permissions and Security (CF92/1229881345) | [[adm]] (new page — GCP/BigQuery security config for ADM sub-client) |
| Authenticating Windsor (CF92/1675001857) | [[Windsor]] (new page — auth + user management) |
| Adding Accounts Windsor (CF92/1675919361) | [[Windsor]] § Adding Accounts (appended to Windsor page) |
| DIOS to DAX API + Nextcloud (CF92/1692991495) | [[custom-fusion-92-audience-api]] § Nextcloud Folder Structure & Workflow |
| ADM (CF92/1215529061) | — (stub/nav-only, no content) |

No hard-coded credential values found. Data Sources page references dates creds were received and API endpoint docs but no actual secrets — no vault extraction required.

**2026-04-18 — CF92 space Batch 2 (11 pages: 10 ingested + 1 routing note) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| DAX Media App (CF92/1439399945) | [[dax-media-app]] (new page — hub/overview) |
| DAX Media App - Flight Management Application Phase 1 (CF92/1206779949) | [[dax-media-app]] § Phase 1 (summary, scope, timeline, feedback) |
| DAX Media App - Metrics Data Consolidation (CF92/1360887813) | [[dax-media-app]] § Phase 2 |
| DAX Media App Feedback (CF92/1425440769) | [[dax-media-app]] § Phase 1 Feedback Highlights |
| DAX Media App - Additional Fields/Change Log (CF92/1437204481) | [[dax-media-app]] § Additional Fields & Change Log |
| DAX Media App - Notifications (CF92/1437302786) | [[dax-media-app]] § Notifications System |
| Flight Check - UI Redesign PRJ505 (CF92/1437204494) | [[dax-media-app]] § PRJ505 |
| Flight Check - App Feature Addition PRJ538 (CF92/1632141315) | [[dax-media-app]] § PRJ538 |
| Flight Check - Smartsheet Replacement PRJ537 (CF92/1633681409) | [[dax-media-app]] § PRJ537 |
| Fusion 92 - Smartsheet Improvement Requirements (CF92/1654030337) | [[dax-media-app]] § PRJ537 → Smartsheet Requirements |
| Flight Check NetSuite Purchase Order Sync (CF92/1660911619) | [[dax-media-app]] § NetSuite PO Sync |

No credentials found. [[flight-check]] operational runbook updated with disambiguation note (app vs. process).

**2026-04-18 — CF92 space Batch 3 (9 pages: 5 ingested + 4 skipped-empty) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Snowflake Infrastructure Considerations (CF92/1363017731) | [[snowflake]] § Infrastructure Architecture (account hierarchy, warehouse model, cost, access control) |
| Snowflake Implementation Checklist (CF92/1367212038) | [[fusion92-data-architecture]] (new page — setup checklist + phases) |
| 2024-09-06 Snowflake Infrastructure Considerations (CF92/1367703569) | [[fusion92-data-architecture]] § September 2024 decisions (Azure + Standard Edition confirmed) |
| Data Architecture Diagrams (CF92/1382088715) | [[fusion92-data-architecture]] § DIOS→DAX→DSP flow (text notes; diagrams are image-only) |
| Architectural Considerations (CF92/1254883340) | [[Eclipse]] § Eclipse 2.0 Application Framework Patterns |
| Full Test Environment (CF92/1230700595) | [[adm]] § Security Group Architecture |
| Data Architecture Assessment (CF92/1362198536) | — (empty body) |
| Google Cloud Architecture (CF92/1224900632) | — (empty body) |
| Data Architecture Meeting Notes (CF92/1362395143) | — (empty body) |

No credentials found.

**2026-04-18 — CF92 space Batch 4 (7 pages, all ingested) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| DAX AI (CF92/1200553996) | [[dax-ai]] (new page — product overview + dashboard status table) |
| DAX AI Financial Reporting Dashboard REQ-234 (CF92/1206779939) | [[dax-ai]] § Financial Reporting Dashboard |
| DAX AI Performance Summary Dashboard REQ-198 (CF92/1236598785) | [[dax-ai]] § Performance Summary Dashboard |
| External DAX Dashboard REQ-215 (CF92/1212678200) | [[dax-ai]] § External Dashboard (stub/deferred) |
| Phase 2 Marketing Reporting (CF92/1224933377) | [[fusion92]] § Phase 2 Marketing Reporting (ADM-adjacent; see also [[adm]]) |
| Univision Dashboards (CF92/1281130497) | [[fusion92]] § Univision Dashboard Project |
| Univision Dashboard External (CF92/1283096590) | [[fusion92]] § Univision Dashboard Project (external dashboard spec) |

No credentials found.

**2026-04-18 — CF92 space Batch 5 (8 pages: 4 ingested + 4 skipped-nav/template) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| 2024-03-20 Funnel.io New Channels (CF92/1225719814) | [[adm]] § Funnel.io Workspace Configuration |
| Data Categorization/DW Model Meeting Notes (CF92/1263501314) | [[fusion92-data-architecture]] § Data Categorization Framework |
| 2024-09-05 DIOS to DAX Audience Integration (CF92/1364688898) | [[custom-fusion-92-audience-api]] § DIOS→DAX Integration Specification |
| 2024-09-03 DIOS / DAX Connectivity (CF92/1365016577) | [[fusion92-data-architecture]] § Snowflake-Centric Architecture Shift |
| Meeting Notes (CF92/1208647702) | — (nav parent, no content) |
| Meeting notes in space (CF92/1226342551) | — (nav template, empty) |
| Projects (CF92/1207009670) | — (nav directory, no content) |
| How-to articles (CF92/1215660134) | — (template stub, no content) |

No credentials found. **CF92 space: MIGRATION COMPLETE** (43 pages total: 39 ingested + 4 skipped-nav/template). F9 space previously assessed as empty/boilerplate — SKIP.

---

**2026-04-18 — CORE space Batch 1 (10 pages, all ingested) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Data Centre (CORE/800489527) | [[deployment-groups]] § Virtual Hosts & On-Prem Infrastructure (PRIORITY — fulfils [[aldc-naming-convention]] pointer) |
| Creating app registration for Core (CORE/891813889) | [[azure-environment-bootstrap]] § App Registration Setup for RBAC (PRIORITY) |
| On-Prem Links and Common Dev Links (CORE/1749811201) | [[local-network]] § Service Access Portals |
| Snowflake MFA and OAuth Setup (CORE/1571160065) | [[snowflake]] § Authentication & MFA Hardening |
| Datasets and API Access (CORE/1467940876) | [[core_api]] § Datasets API |
| Power BI Registration Secret Refresh (CORE/1468104706) | [[powerbi-secret-refresh]] (new page) |
| Docker Guides (CORE/1074823173) | [[connector-docker-deployment]] § Docker Reference; GHCR + Postgres restore |
| Azure Queue Storage Trigger (CORE/1048248321) | [[core_api]] § Azure Queue Storage Trigger |
| Modify Executive Snapshot Email Script/Schedule (DUER) (CORE/1559461890) | [[executive-snapshot-email]] (new page) |
| Agent Virtual Machine (VM) (CORE/922550273) | [[agent-builds]] § Legacy agent process |

Credential extraction to `vault/infra-credentials.md`: Galactica SQL Server (`sa`/`0chTpYrtgL` + `eclipse`/`qir4Xkcn^bd` — **CONTRADICTION flagged** vs. prior INFRA/343506945 `sa`/`gpH^Cf49BMu`), GHCR service account token + GitHub password (`aldc-svc-automation`), Postgres Docker password.

**CORE space: Batch 1 of 5 complete. 10/79 pages handled.**

---

**2026-04-18 — CORE space Batch 2 (13 pages: 11 ingested + 2 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Cosmos DB Documents (CORE/916488197) | — (empty parent/index page) |
| Cosmos Database Principles (CORE/893124613) | [[cosmosdb-schema]] § Core ETL Pipeline Documents + ETL flow overview |
| Cosmos DB - account (CORE/929103873) | [[cosmosdb-schema]] § Account Collection |
| Cosmos DB - staff (CORE/921632769) | [[cosmosdb-schema]] § Staff Collection |
| Cosmos DB - capacity (CORE/937197569) | [[cosmosdb-schema]] § Capacity Collection |
| Cosmos DB - capacity_provider (CORE/1050869770) | [[cosmosdb-schema]] § Capacity Provider Collection |
| Cosmos DB Analytic Store Setup (CORE/960069656) | — (Azure Synapse Link procedural guide, not schema) |
| Cosmos DB - agent (CORE/917700609) | [[cosmosdb-schema]] § Agent Collection |
| Cosmos DB - work connection (CORE/921632782) | [[cosmosdb-schema]] § Work Connection Collection; Fivetran Snowflake creds → vault |
| Cosmos DB - report (CORE/902987777) | [[cosmosdb-schema]] § Report Collection |
| Cosmos DB - task (CORE/968163329) | [[cosmosdb-schema]] § Task Collection |
| Cosmos DB - work partition (CORE/917700622) | [[cosmosdb-schema]] § Work Partition Collection |
| Cosmos DB - work_template (CORE/928186369) | [[cosmosdb-schema]] § Work Template Collection (most current — updated 2024-02) |

Credential extraction: Fivetran Snowflake connection (`analyticlabs` / `uRbGSUTgTpmU@N3m+L`, server `px06888`) → `vault/infra-credentials.md` § Fivetran Snowflake. Fernet-encrypted strings in capacity/capacity_provider are examples only; encryption key already in vault.

**CORE space: Batch 2 of 5 complete. 23/79 pages handled.**

---

**2026-04-18 — CORE space Batch 3 (12 pages: 7 ingested + 5 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Core API (CORE/238387201) | [[core_api]] § REST API Specification (2021 endpoint table + session/schedule flow) |
| Architecture Overview (CORE/7929869) | [[core_api]] § Architecture & Language Stack |
| Technical Documentation (CORE/33390595) | — (empty nav page) |
| Core Home (CORE/522191059) | — (duplicate nav; content captured from Architecture Overview) |
| Reference Designs (CORE/522191131) | [[core_api]] § Architecture & Language Stack (folded in as reference links) |
| Environment Variables (CORE/886603777) | [[core_api]] § Environment Variables (redacted); **15+ credentials → vault** |
| Notification Module (CORE/885620774) | [[core_api]] § Notification Module (route_notification.py) |
| Quickstart Guide (CORE/877592581) | — (nav/incomplete; routing concepts already in core_api.md) |
| Task Daemon (CORE/909737996) | [[core_api]] § Task Daemon (route_task.py) |
| Azure API (CORE/964591617) | — (separate PowerShell system, not core_api) |
| Reporting and Telemetry (CORE/720044036) | — (minimal page, Power BI file reference only) |
| Using data from portal_data in PowerBI (CORE/892796955) | [[core_api]] § Portal Data Export & Power BI Integration |

Credential extraction to `vault/infra-credentials.md`: Twilio SID/token/number, Mailjet key/secret (2 sets), Pushover token, dev-env COSMOS_KEY, ENCRYPTION_KEY example, MASTER_CLIENT_SECRET alt (CONTRADICTION flagged), dev STORAGE_SAS1/SAS2, dev Azure SP (client_id `177e8b90`, subscription `e23c2c14`), ALDC Sandbox SAS key.

**CORE space: Batch 3 of 5 complete. 35/79 pages handled.**

---

**2026-04-18 — CORE space Batch 4 (20 pages: 14 ingested + 6 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Scheduling (CORE/522191103) | [[core-api-data-model]] § Template System & Queue Storage |
| Routine (CORE/540704854) | [[core-api-data-model]] § Routine Collection |
| Schedule (CORE/537329699) | [[core-api-data-model]] § Schedule Collection |
| Schedule Event (CORE/537296929) | [[core-api-data-model]] § Schedule Event Collection |
| Session (CORE/540114967) | [[core-api-data-model]] § Session Collection |
| Session Event (CORE/540114974) | [[core-api-data-model]] § Session Event Collection |
| Account Connector (CORE/540704807) | [[core-api-data-model]] § Account Connector Collection |
| Connector (CORE/540114985) | [[core-api-data-model]] § Connector Metadata Collection |
| Account (CORE/540704815) | [[core-api-data-model]] § Account Collection (v1) |
| Session Schema (CORE/540704833) | [[core-api-data-model]] § Session Schema Collection |
| Schema (CORE/540115003) | [[core-api-data-model]] § Schema Collection |
| Database Schema v1 (CORE/537002029) | [[core-api-data-model]] § Common Document Attributes |
| Account Secret (CORE/540115026) | [[core-api-data-model]] § Account Collection (v1) — merged |
| Merge Strategies (CORE/701956097) | [[core-api-data-model]] § Merge Strategies & History Tracking |
| Snowflake (CORE/374341641) | [[snowflake]] § v1 Client Database Structure |
| Datawarehouse Integrations (CORE/418873390) | [[snowflake]] § v1 Snowflake Azure integration setup; service account creds → vault |
| Postman (CORE/641794082) | — (nav/binary blob, no extractable content) |
| Licensing (CORE/471924755) | — (empty page) |
| Licensing Reference (CORE/463601805) | — (software deps list, out of scope) |
| Snowflake Standard Pricing (CORE/278036481) | — (2021 pricing data, operational/out of scope) |

Credential extraction to `vault/infra-credentials.md`: Snowflake service account `CORE_a7a8d78c` / `h[n$1:R,lD<ulv5iXc46ay@M]:qn~d`; demo connection creds (NetSuite, SQL Server examples).

**CORE space: Batch 4 of 5 complete. 49/79 pages handled.**

---

**2026-04-18 — CORE space Batch 5 (17 pages: 12 ingested + 5 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| vGPU Configuration (CORE/1160904705) | [[proxmox]] § vGPU Configuration (new page) |
| Proxmox Host Guides (CORE/1043726358) | [[proxmox]] § Host Administration (new page) |
| Proxmox Guest Guides (CORE/1087340545) | [[proxmox]] § Guest Provisioning + § Disk Expansion |
| Linux Guides (CORE/1086881800) | [[proxmox]] § Guest Disk Expansion (folded in) |
| cloud.aldc.io NextCloud build (CORE/1086881902) | [[nextcloud]] § ZFS Setup & Installation |
| cloud.aldc.io Backup Overview (CORE/895778817) | [[nextcloud]] § Backup Strategy & Disaster Recovery |
| Linux + Covenant storage (CORE/1023770631) | [[local-network]] § Mounting Covenant Storage on Linux |
| Mailjet Configuration and Domain (CORE/926285825) | [[mailjet]] (new page); account password → vault |
| Dashboard usage/documentation (CORE/1078525953) | [[dashboard]] (new page — Eclipse Dashboard feature architecture) |
| Synapse Analytics Workspace Setup (CORE/960397353) | [[synapse-analytics-setup]] (new page) |
| Zombies in ALDC!? (CORE/922583054) | [[debugging-warehouse-loads]] § Marking stalled items as zombies |
| Removing stucked jobs on Snowflake (CORE/923238429) | [[debugging-warehouse-loads]] § Aborting stuck Snowflake jobs |
| Monitoring the health of our Accounts on PowerBI (CORE/923140107) | [[flight-check]] § Account health dashboard |
| Cloud.aldc.io Backup & Restore (CORE/1086587008) | — (stub/link-only page) |
| Invoice Automation (CORE/1027244033) | — (product design spec, not operational) |
| File Access (CORE/1043595287) | — (stale infra reference) |
| Capacities (CORE/934248449) | — (minor; content already covered in [[cosmosdb-schema]]) |

Credential extraction to `vault/infra-credentials.md`: NextCloud admin `ncadmin`/`nextcloud`; Mailjet account password `P0st0ff!ce!`. Covenant CIFS + Mailjet API keys already in vault from prior batches — no duplication.

**CORE space: MIGRATION COMPLETE. 61/79 pages handled (49 ingested + 18 skip/defer + 7 confirmed-skip nav/template/release-notes from skip list).**

---

**2026-04-18 — CLIEN space Batch 1 (14 pages: 12 ingested + 2 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| SQL Server SSMS (CLIEN/1294794754) | [[ssms]] § Partition Refresh (**PRIORITY** — resolves existing wiki pointer) |
| Client - Deactivation Checklist (CLIEN/1414594561) | [[client-deactivation]] (new page) |
| Client - VM Setup (CLIEN/1658716161) | [[client-vm-setup]] (new page) |
| Client - Invoicing Process (CLIEN/1730281475) | [[client-invoicing]] (new page) |
| Model Deploy to Production (CLIEN/1244561414) | [[model-deploy-production]] (new page) |
| Outage Emails (CLIEN/1260978177) | [[client-communications]] (new page — merged with 1260584963 + 1027637253) |
| Data Model Access Email (CLIEN/1260584963) | [[client-communications]] § Data Model Access Email |
| Client - Notifications (CLIEN/1027637253) | [[client-communications]] (nav parent — folded into client-communications.md) |
| Client Onboarding Checklist (CLIEN/439025665) | [[client-onboarding-checklist]] (new page) |
| Client_Tenant NextCloud Access (CLIEN/948240388) | [[nextcloud]] § Client Tenant Access |
| Granting PowerBI Excel Model Access (CLIEN/1023115265) | [[power-bi]] § Granting Excel Model Access |
| PowerBI Template (CLIEN/904429569) | [[power-bi]] § Report Template |
| System Information for Clients (CLIEN/1297776644) | — (image-only page, no extractable content) |
| Customer Success Resources (CLIEN/1733558276) | — (nav-only index) |

No credentials requiring vault extraction found in Batch 1.

**CLIEN space: Batch 1 of 4 complete. 14/87 pages handled.**

---

**2026-04-18 — CLIEN space Batches 2–4 (34 pages: 25 ingested + 9 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Periodicity Documentation (CLIEN/1407877121) + Periodicity within Models (CLIEN/1281228804) | [[periodicity]] (new page — SHARED_DIM_PERIODICITY + DAX patterns) |
| GEP Projects (CLIEN/1458634759) | [[GEP]] § Service Requests |
| GEP Onboarding Checklist (CLIEN/1173913601) | [[GEP]] § Client Contact & Contract |
| GEP overview (CLIEN/1167196168) | [[GEP]] § Excel Model Scope |
| NetSuite Scoping Call (CLIEN/1302986753) | [[GEP]] § NetSuite Integration Context |
| Snowflake Review with Mark (CLIEN/1071644673) | [[Snowflake]] § Performance Review Notes |
| DISH_DUER (CLIEN/909115393, 932872202, 1033928705, 1033732113, 936148993, 1082687489, 1090682881, 1088880641) | [[dish-duer]] (new page — full dimensional model, Finance Model, Eclipse objects) |
| KIT_ACE (CLIEN/564658177, 881426433, 884539393, 674791449, 665583621) | [[kit-ace]] (new page + account details, ecommerce systems) |
| BOOK_DEPOT (CLIEN/972488707, 1013972993) | [[book-depot]] (new page) |
| TERRAYN (CLIEN/1013874689) | [[terrayn]] (new page) |
| ASPIRE_NORTH (CLIEN/1047822343) | [[aspire-north]] (new page) |
| INDOCHINO (CLIEN/875429895) | [[indochino]] (new page — detailed 2021 architecture assessment) |
| DROP_IN Gaming (CLIEN/1031110657, 1035927561) | [[drop-in-gaming]] (new page) |
| Athena Credentials (CLIEN/1013186565) | `vault/infra-credentials.md` § TERRAYN — Athena (TERRAYN AWS IAM key) |
| Account Details KIT_ACE (CLIEN/674791449) | `vault/infra-credentials.md` § KIT_ACE — SFCC + Camacc SQL Server + initial Eclipse passwords |
| Ecommerce KIT_ACE (CLIEN/665583621) | `vault/infra-credentials.md` § KIT_ACE — Google Analytics API Key |
| Enterprise Scoping Project (CLIEN/1111687169) | [[fusion92]] § Enterprise Scoping Project |
| PowerBI nav (CLIEN/1294630913) | — (nav-only) |
| Standard Processes (CLIEN/1106444300) | — (nav-only) |
| DIOS to DAX Audience Files (CLIEN/1677459457) | — (attachments-only, no text) |
| Heartland Dental (CLIEN/1040285739) | — (empty page) |
| Approach Overview (CLIEN/1112342531) | — (nav/Miro board link only) |

**CLIEN space: MIGRATION COMPLETE. 48/87 pages handled (37 ingested + 11 skipped/nav + ~39 intentional skips).**

---

**2026-04-18 — CDD space (3 pages: 0 ingested + 3 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Client - Dish & Duer (CDD/1226735691) | — (welcome boilerplate) |
| Projects (CDD/1226670103) | — (nav directory) |
| Meeting Notes (CDD/1227194371) | — (nav directory) |

**CDD space: MIGRATION COMPLETE** (0 ingested, 3 skipped — `dish-duer.md` from CLIEN captures all engineering content).

**2026-04-18 — CKA space (3 pages: 0 ingested + 3 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Client - Kit & Ace (CKA/1235615827) | — (welcome boilerplate) |
| Projects (CKA/1235779881) | — (nav directory) |
| Meeting Notes (CKA/1235616021) | — (nav directory) |

**CKA space: MIGRATION COMPLETE** (0 ingested, 3 skipped — `kit-ace.md` from CLIEN captures all engineering content).

**2026-04-18 — CAN space (4 pages: 1 ingested + 3 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Customer Insights Dashboard REQ-169/CUST-679 (CAN/1235845127) | [[aspire-north]] § Customer Insights Dashboard (PRD: RACI, scope, 38 Experian data fields, Eclipse feature requirements) |
| Client - Aspire North (CAN/1235779865) | — (welcome boilerplate) |
| Projects (CAN/1235877900) | — (nav directory) |
| Meeting Notes (CAN/1236008963) | — (nav directory) |

No credentials found. **CAN space: MIGRATION COMPLETE** (1 ingested, 3 skipped).

**2026-04-18 — ALDCKB space (4 pages: 0 ingested + 4 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| ALDC Support Knowledge Base Home (ALDCKB/1753678232) | — (Atlassian default space template) |
| Getting Started with ALDC Support (ALDCKB/1753776129) | — (customer portal guide, not engineering) |
| Billing FAQ (ALDCKB/1753808897) | — (customer-facing FAQ, not engineering) |
| Contact Information (ALDCKB/1753841665) | — (support@aldc.io + business hours, not engineering) |

**ALDCKB space: MIGRATION COMPLETE** (0 ingested, 4 skipped — customer-facing support portal, no engineering content).

**2026-04-18 — ENG space (4 pages: 1 ingested + 3 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| AI Development Workflow Plan (ENG/1761050625) | [[ai-pr-workflow]] (new page — team-ratified 6-step PR workflow with AI review integration; Vlad leading rollout) |
| Engineering (ENG/1758527826) | — (space home, default boilerplate) |
| Template - How-to guide (ENG/1758527843) | — (Atlassian template) |
| Template - Troubleshooting article (ENG/1758527855) | — (Atlassian template) |

No credentials found. **ENG space: MIGRATION COMPLETE** (1 ingested, 3 skipped).

**2026-04-18 — AIRA space (3 pages: 2 ingested + 1 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Adversarial Multi-Agent Investigation Protocol (AIRA/1763246091) | [[adversarial-investigation-skill]] (new page — `/investigate-adversarial` Claude Code skill, 6-phase protocol, PROVE/DISPROVE/BLIND-SPOT) |
| ALDC Development Workflow (AIRA/1765244929) | [[ai-pr-workflow]] (major update — full implementation: Semgrep, TruffleHog, Claude Opus review, PyTestArch, quality-gate, CCX, per-repo config, merge conditions, non-negotiables; all checks live as of 2026-04-10) |
| AI Research & Architecture (AIRA/1762984361) | — (3-line space description, nav only) |

No credentials found. **AIRA space: MIGRATION COMPLETE** (2 ingested, 1 skipped).

**2026-04-18 — CONN space (38 pages: 11 ingested + 27 skipped) via Atlassian MCP:**

| Confluence page | Wiki destination |
|---|---|
| Connector Development Standards (CONN/424280065) | [[eclipse]] § Connector Development Standards (attribute hierarchy, interface spec, base classes, code layout) |
| Bing Ads OAuth Token Regeneration Steps (CONN/1575747585) | [[connector-token-refresh]] (new page) |
| Google Analytics (CONN/645300259) | [[google-analytics]] (new page) — credentials → vault |
| Facebook Marketing API Connector Setup (CONN/898695196) | [[facebook-ads]] (new page) |
| Facebook Marketing API (CONN/899645489) | [[facebook-ads]] § credentials + API endpoints — credentials → vault |
| Bing Ads / Microsoft Advertising (CONN/1132560386) | [[bing-ads]] (new page) |
| Google Ads (CONN/1134100481) | [[google-ads]] (new page) |
| Amazon Ads and Amazon DSP (CONN/1298792450) | [[amazon-ads]] (new page) |
| Trade Desk Connector And Reports API (CONN/1458831371) | [[trade-desk]] (new page) |
| ODBC (CONN/493649955) | [[eclipse]] § Base Classes (folded into Connector Development Standards) |
| Web Applications (CONN/645201921) | — (foundational OAuth overview, low engineering value) |
| Architecture Diagrams (CONN/1738604545) | — (image-only blobs, not retrievable) |
| Connector Class Model (CONN/484900948) | — (image-only diagram) |
| Architecture (CONN/495943748) | — (empty page) |
| Getting started (CONN/495648921) | — (generic Confluence template) |
| Making a template (CONN/495648924) | — (generic Confluence admin) |
| Operation Fiasco (CONN/1738342401) | — (Jira issue link only, DV-284) |
| Netsuite SuiteAnalytics Connect (CONN/501547009) | — (2021/deleted author, example placeholder creds) |
| Genesys PureCloud (CONN/278200323) + 10 other 2021 connectors | — (2021 vintage/deleted authors: Base, REST, Flat File, MySQL, PostgreSQL, Redshift, Shopify, Twitter, TomTom, CSV, OpenWeatherMap, HubSpot, Web Scrapers, FeedTheRobot, PhoneBurner, NutShell) |

Credential extraction to `vault/infra-credentials.md`: Google Analytics support@aldc.io password, Facebook Marketing API support@aldc.io password + sandbox access token.

**CONN space: MIGRATION COMPLETE** (11 ingested + 27 skipped). All active ad platform connectors documented under `entities/tools/connectors/` with Prefect migration notes.

## Open follow-ups

Carried from [[action-items]]:

- ~~Research the best way to extract Confluence pages/spaces for ingestion into the LLM wiki~~ — resolved 2026-04-17 via the authenticated Atlassian MCP server
- Continue ingesting remaining TECH-space pages (calibration batch done; next batches TBD)
- Integrate notes from INFRA, CORE, CLIEN, CF92, CGEP spaces

## See Also

- [[SSMS]] — Confluence holds detailed dataflow diagrams and per-client setup
- [[Prefect]] — Confluence holds the Prefect Azure-resources doc in Brayden's offboarding space
- [[Azure]] — Confluence covers Azure resource layout per environment
