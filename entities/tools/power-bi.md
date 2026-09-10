---
tags: [entity, tool, power-bi, reporting, visualization]
aliases: [Power BI, PBI]
sources: [clients repo report_common/ directories, Obsidian vault notes, GP-208 Data Source Settings check 2026-04-21, GP-200 UAT investigation 2026-05-20, Eclipse Test report fix 2026-05-21, Navira live-data-model + ME/Agency integration 2026-06-18, Agentic Power BI docs pointer 2026-08-23 (UNREAD)]
created: 2026-04-16
updated: 2026-08-29
---

# Power BI

ALDC's reporting and visualization layer. Power BI semantic models import data directly from [[Snowflake]] (via M queries against `WAREHOUSE.*` and `REPORT_COMMON.*` views) and store it in the model's internal VertiPaq column-store cache. That cache is what refreshes populate; "partitions" of that cache are what gets re-processed via [[SSMS]] or `pbi_model_apply.exe`.

## Data flow into Power BI

```
Snowflake (WAREHOUSE.*, REPORT_COMMON.*)
        │  (Snowflake.Databases connector, M query per table)
        ▼
Power BI semantic model — VertiPaq cache (tabular model partitions)
        │
        ▼
Power BI reports (visuals, DAX measures)
```

> **Correction (2026-04-24):** earlier versions of this page described an intermediate SQL Server DB between Snowflake and PBI. **That DB does not exist in the GEP data path.** PBI connects direct to Snowflake (+ core_api for glossary metadata). The confusion arose because SSMS is used to process partitions of the PBI tabular model via its XMLA endpoint — SSMS is acting as an XMLA client into the PBI Premium Analysis Services layer, not into a separate SQL Server database. Verified via Data Source Settings inspection on the live GEP PBIX (2026-04-21); confirmed architecturally in the 2026-04-24 GP-208 XMLA validation session. See [[SSMS]] for the reframe, and [[pbi-xmla-automation]] for the automation layer that replaces SSMS partition processing for metadata changes.

A more detailed (external) diagram lives in [[Confluence]] — treat its SQL-Server-intermediate framing with the same correction in mind.

## How Power BI Connects to Snowflake

Power BI models import data from Snowflake `REPORT_COMMON.*` views. These views are specifically designed as the PBI consumption layer — pre-aggregated, denormalized, and optimized for the model's grain.

### Report Common View Types

Defined in `__REPORT_COMMON_VIEWS` and per-client `snowflake/report_common/` directories:

| View Pattern | Purpose | Used By |
|-------------|---------|---------|
| `DEFAULT_DEFAULT` | Baseline reporting view | All clients |
| `RETAIL_DAILY_SALES_*` | Daily sales (CONFIG, DATE, FACT, GLOSSARY, LOCATION) | GEP, KIT_ACE, DISH_DUER, RAIN_CITY |
| `RETAIL_CUSTOMER_VALUE_*` | Customer analytics (ACQUISITION, CUSTOMER, DATE, FACT, ITEM, LOCATION, SUMMARY) | KIT_ACE, RAIN_CITY |
| `RETAIL_ITEM_ATTRIBUTE_*` | Product attributes (DATE, FACT, ITEM, LOCATION) | KIT_ACE, DISH_DUER |
| `RETAIL_KPI_MANAGER_*` | KPI dashboards (CONFIG, DATE, GLOSSARY, LOCATION, SALES_FACT, TRAFFIC) | KIT_ACE, DISH_DUER |
| `RETAIL_PRODUCT_MANAGER_*` | Product management (DATE, FACT, ITEM) | KIT_ACE |
| `RETAIL_INVENTORY_PLANNER_*` | Inventory planning (COMBINED, DATE, INVENTORY, ITEMS, LOCATION, SALES) | KIT_ACE |
| `RETAIL_PURCHASE_FREQUENCY_*` | Purchase frequency (CUSTOMER_SALES_LOCATION, SALES) | KIT_ACE |
| `RETAIL_ECOMMERCE_FLASH_*` | E-commerce flash reports (DATE, FACT) | KIT_ACE, RAIN_CITY |
| `RETAIL_BASKET_ANALYSIS` | Market basket analysis | KIT_ACE |

### GEP-Specific Report Common Views
- `DEFAULT_DEFAULT.sql`
- `RETAIL_DAILY_SALES_DATE.sql`
- `RETAIL_DAILY_SALES_FACT.sql` — unions budget and actual sales data
- `RETAIL_DAILY_SALES_LOCATION.sql`

### ⭐ Snowflake connector auth — corrected 2026-09-08

**Supported auth types** (MS Learn Power Query Snowflake connector, updated 2026-07-31):
*Snowflake (Username/Password), Microsoft account (Microsoft Entra ID), **Key Pair Auth (ADBC)**,
**Service Principal (SPN)***; Fabric adds **Workspace Identity**.

⭐ **The belief that "Power BI's ODBC connector cannot do Snowflake key-pair" is FALSE and has been
since 2025** — connector implementation 2.0 (GA July 2025) swapped Simba ODBC for the Arrow **ADBC**
driver, and key-pair went GA Feb 2026. Verified against our own tenant, which is stronger than any
doc — `GET https://api.fabric.microsoft.com/v1/connections/supportedConnectionTypes` returns:

```
"type": "Snowflake",
"supportedCredentialTypes": ["Basic","OAuth2","KeyPair","ServicePrincipal","WorkspaceIdentity"],
"supportedConnectionEncryptionTypes": ["NotEncrypted"],
"supportsSkipTestConnection": false,
"creationMethods": [{"name": "Snowflake.Databases", ...}]
```

Of **325** connection types in the tenant, only **two** declare `KeyPair`: `SFTP` and `Snowflake`.

**Reading credential state.** The legacy PBI API renders these as `datasourceType: "Extension"`
with NULL `.server`/`.database` — connector identity is in `connectionDetails.kind`, target in
`.path`. ⚠ **An enumeration filtering on `datasourceType == "Snowflake"` or reading `.server`
returns 0 rows with 0 errors — a blind zero.** Always carry a positive control. The Fabric API
types the same objects as `"Snowflake"`; `"Extension"` is a legacy rendering artefact, and the
`datasourceId` and Fabric `connectionId` are the **same GUID**.

⚠ `GET /gateways` returns **0 with HTTP 200** for cloud connections — that is not "no gateways".
Virtual cloud gateway IDs come only from the dataset → datasources walk.

**Useful signals:**
- `lastCredentialUsedDateTime` on `/v1/connections` — "this credential last authenticated at T",
  in one GET, without triggering a refresh. Better health check than polling refresh history.
- `supportsSkipTestConnection: false` for Snowflake means **every credential write performs a real
  authentication attempt** — so a 200/201 *is* proof, not merely a stored setting. This makes
  `POST /v1/connections` (unbound `ShareableCloud`) a **zero-blast-radius** validation path.

⛔ **Key-pair forces ADBC** — *"the ADBC driver is always used regardless of this setting"* — which
**deletes** the documented self-mitigation (`remove Implementation="2.0"` to fall back to ODBC) and
inherits two open connector defects: *`count distinct` returns incorrect result* and a memory
regression. The first **Completes** rather than failing, so `MailOnFailure` cannot fire on it.
Always run an old-vs-new **numeric parity check** on cutover — a green refresh is not evidence of
correct numbers. See [[ALDC-1164]], and [[GP-318]] for the same failure shape.

### ⚠ Refresh alerting does not mean refresh detection

- Power BI **disables a schedule after 4 consecutive failures**, at which point failure emails stop
  — *the alarm goes quiet exactly when the outage becomes permanent*. Alarm on **staleness**
  (no new `Completed` within 2× the interval), not just on `status == Failed`.
- Measured on this estate: `ALDC_FINANCE / Profitability Model` failed 2026-05-29 with
  `notifyOption = MailOnFailure` **enabled** and ~3 months passed with no response;
  `FUSION_92 Test Models / Activation Model` reads `enabled: true` and has been silent since
  2026-08-23. **`enabled` is not a health signal.**
- `refreshSchedule.enabled = False` is **not a lock** — `ViaApi` and `OnDemand` refreshes were
  observed against a schedule-disabled prod model.
- ⚠ `targetStorageMode: "Abf"` does **not** mean Import — MS documents the field only as
  "The dataset storage mode", with no enum. Use `ContentProviderType` to settle Import vs Composite.

⚠ **`CORE_API_CLIENT_TOKEN` is stored as a plaintext M parameter** on every parameterised model,
readable via `GET /datasets/{id}/parameters` by any principal with ordinary dataset read access.

## Power BI Workspaces (Fusion92)

| Workspace | Model | Owner | Refresh Cadence | Notes |
|-----------|-------|-------|-----------------|-------|
| FUSION_92 Prod Models | Activation Model | `paul.russell@aldc.io` | Scheduled (verify post-takeover) | Taken over 2026-05-22 (FU92-417) |
| FUSION_92 Test Models | Activation Model | `paul.russell@aldc.io` | Scheduled (verify post-takeover) | Taken over 2026-05-22 (FU92-417) |

> **Incident 2026-05-22:** Both Fusion92 Activation Model datasets failed refresh — previous owner removed from Azure AD (`DMTS_UserNotFoundInADGraphError`). Paul took over both, re-entered Snowflake credentials, refreshed successfully. See FU92-417.

## Power BI Workspaces (GEP)

| Workspace | Workspace ID | Dataset | Dataset ID | Snowflake Env | Refresh Cadence |
|-----------|-------------|---------|-----------|--------------|-----------------|
| GEP Test Models | `a29d4c01-4a8f-4a1e-8784-4d7dedcde940` | Data Model | `66151728-f00f-4a08-af91-6687de5f13dc` | `TEST_DG1_GEP` | **Daily 07:00 Pacific** — confirmed running. Owner: `paul.russell@aldc.io` |
| GEP Test Reports (LEGACY) | `7f47a5e0-b619-4aea-b69a-259d4d4315fa` | Daily Sales | `8c935a8f-50c0-4404-8756-28853c9a8623` | `TEST_DG1_GEP` | No schedule. Last refresh Oct 2024 — **stale, archive candidate** |
| GEP Prod Models | `de58032f-c282-46fb-8b8f-88900df997d1` | Data Model | `74a529b3-5112-4f1e-9ee6-9ab642b288c4` | `PROD_DG1_GEP` | **Hourly, 02:00–16:00 Pacific**. Owner: `paul.russell@aldc.io` |
| GEP Prod Reports | `11b7df98-b2bd-4cea-a01c-42d8a63a7134` | Daily Sales | `c35abad7-c685-4ddb-a352-2b761f98618e` | `PROD_DG1_GEP` | No schedule. |
| GEP Sandbox Models | `8545f3cb-4e2d-4985-bf31-79066248c9be` | GEP_Sandbox_Current | `fb41970d-2beb-4ed9-9f82-35c6439b35ea` | Per-ticket sandbox DB | Manual only. |

> ⚠️ **Do not use GEP Test Reports for UAT.** The "Daily Sales" dataset there has no scheduled refresh and is stale (last refresh Oct 2024). Always use **GEP Test Models → Data Model** for UAT validation. **Action item:** Rename "GEP Test Reports" workspace to "GEP Test Reports (LEGACY - DO NOT USE)" and archive. Owner: `karen.prete@aldc.io` — nothing depends on it as of 2026-05-21 (Eclipse Test was the last dependency, now resolved).

> **Eclipse Test report fix (2026-05-21):** GEP/Navira users accessing reports via `eclipse-test.aldc.io/account/reports/` were seeing stale data because the Eclipse Django app's report record (pk=51, Postgres) pointed to Power BI Report ID `a86256ca-7fa8-439e-9b28-605107640086` in the legacy workspace. Fixed by updating the `power_bi_report` field to `15128c39-dcbf-4ed5-a52b-02080f0ed315` (the "Data Model" report in GEP Test Models workspace). Report renamed from "Daily Sales" to "Test Data Model". The PBI Report ID is stored in Eclipse's Django Postgres database (`aldctestpgdbportal1c01.postgres.database.azure.com`, database `eclipse`), NOT in [[core_api]] CosmosDB. Update scripts in `aldc-launchpad/scripts/pbi/`.
>
> **Prod risk:** GEP Prod Reports workspace (`11b7df98`) also has no refresh schedule and its "Daily Sales" report (`7564da58-7788-4b73-9e7a-fb3d1ffd590b`) may have the same issue if prod Eclipse embeds it. Verify whether prod users access reports through Eclipse prod — if so, apply the same fix pointing to GEP Prod Models report (`1d096c9d-4839-49e5-992c-b755de578098`).

> Note: an earlier wiki entry (daily/2026-04-17.md) recorded wrong workspace/dataset IDs (`85c00659` / `1ac238e9`). Those point to "Account Summary Test Canada DG1" (a different client). The correct IDs are in the table above — verified 2026-05-20 via Power BI REST API.

## Model Refresh

Refresh cadence is configured **per semantic model** in Power BI Service — each model's refresh schedule lives under **... → Settings → Scheduled refresh** in the workspace. Refresh is **not** tied to Snowflake data changes; Snowflake updates the warehouse, Power BI pulls on its own schedule.

### GEP Test Model (`GEP Test Models` workspace)

The GEP Test semantic model is configured for a scheduled refresh **once daily at 07:00 Pacific**. This sits intentionally after the warehouse task chain, which fires at 06:00 Pacific and typically completes by ~06:15 — giving the PBI refresh ~45 min of buffer before it pulls. Users of the test PBI model see the prior day's warehouse state each morning (see [[gep-snowflake-pbi-deployment]] for the warehouse side).

Actual refresh timestamps drift a few minutes from the schedule — this is normal Power BI behavior. Verified 2026-04-21:
- Configured fire time: 07:00 PDT
- Actual fire time: 07:07:10 PDT (7 min drift)
- Next scheduled fire: 2026-04-22 07:00 PDT

**Daily cadence summary (GEP Test):**
- 06:00 PDT — Snowflake `TASK_WAREHOUSE_ORDERLINE_0` cron fires → 10-step DAG materializes the warehouse
- ~06:15 PDT — warehouse task chain completes (typical)
- 07:00 PDT — Power BI Test semantic model scheduled refresh fires (allow a few min drift)
- ~07:15–07:30 PDT — Power BI refresh completes, test model reflects prior day's closed orders

If fresher data is needed intra-day (e.g. post-deploy verification), trigger an ad-hoc refresh:

1. Navigate to the **GEP Test Models** workspace in Power BI Service
2. Find the **Semantic model** row (NOT the Report row)
3. Click **...** → **Refresh now**
4. Watch **... → Refresh history** for completion (a few minutes to 30+ minutes)

> If credentials have expired, refresh will fail. Fix via **... → Settings → Data source credentials → Edit credentials**. See [[powerbi-secret-refresh]] for the secret lifecycle.

### After a warehouse deploy

After a Snowflake warehouse change, the scheduled refresh will eventually pick it up — but during UAT or customer validation, trigger an ad-hoc refresh with the steps above so the test model reflects the change immediately.

## Common Issues

- **Stale data**: PBI model not refreshed after Snowflake deploy — always refresh after deploying warehouse changes
- **Schema mismatch**: If Snowflake view columns change, PBI model may error on refresh — update the PBI model to match
- **Date columns**: Some date columns may not import correctly into PBI models — may need research per ticket (noted in [[GP-208]] to-do)
- **Marketplace table is a bridge table, not a dimension**: The GEP Marketplace table has 19,934 rows — one per unique product-marketplace combination (MARKETPLACE_KEY is a hash). It is NOT a simple dimension with one row per marketplace name. Using Marketplace Name as a row field in a table visual resolves to the bridge-table grain (e.g., 174 rows for Amazon UK instead of the expected 435 order lines). Fix: use Marketplace Name as a **slicer or filter**, then use **Count Distinct of Order Line ID** as the measure. Never put Marketplace Name and Order Line ID in the same table visual as row fields. See [[GP-200]] Pitfall 4.
- **Client workspace access not provisioned for UAT**: GEP Test Models workspace only has internal ALDC accounts by default. External client users (e.g., `jshuster@navira.io`) need a provisioned `@gep.aldc.io` account + PBI PPU license + workspace Viewer access before they can test. Karen Prete or Lori Beck have M365 admin rights. See [[GP-200]] UAT findings 2026-05-21.
- **Dataset owner removed from Azure AD**: If the dataset owner's account is deleted or deprovisioned, scheduled refresh is automatically disabled and all stored credentials are wiped. Error code: `DMTS_UserNotFoundInADGraphError`. Fix: take over the dataset (Settings → Take over), re-enter all data source credentials from Dashlane, re-enable scheduled refresh. Incidents: GEP Prod Models 2026-05-20; Fusion92 Prod + Test Models 2026-05-22 (FU92-417, both taken over by `paul.russell@aldc.io`, refreshes confirmed green). **Long-term**: use a dedicated service account as dataset owner so individual offboarding doesn't break refreshes.

## PBI Diagnostic Tool

`scripts/pbi/` in `aldc-launchpad` (committed `bff0663`, 2026-05-20). Multi-client CLI for PBI health checks, refresh history, and DAX verification. Replaces ad-hoc diagnostic scripts.

```bash
# Health check for all GEP workspaces
python -m scripts.pbi health GEP

# Verify Amazon UK data is in the model
python -m scripts.pbi verify "GEP Test Models" "Data Model" --check entity --entity "Amazon UK"

# Marketplace breakdown with order line counts
python -m scripts.pbi verify "GEP Test Models" "Data Model" --check marketplace

# Refresh history for a dataset
python -m scripts.pbi refresh-history "GEP Test Models"
```

**Auth**: Three-tier — Azure CLI token first (zero-prompt if `az login` active), then MSAL file cache (`scripts/pbi/.token_cache.bin`, gitignored), then device-code. After the first device-code login, subsequent runs are silent.

**Known PBI API constraints (GEP Import-mode datasets):**
- `GET /datasets/{id}/tables` → HTTP 404 — only works for Push datasets, not Import
- `EVALUATE INFO.TABLES()` → DAX error — not supported at GEP model compatibility level
- Table discovery: use `EVALUATE ROW("cnt", COUNTROWS('TableName'))` probing per table name
- Correct client ID for device-code: `7f67af8a-fedc-4b08-8b4e-37c4d127b6cf` (Power BI Desktop). The `ea0616ba` client ID in old wiki notes is rejected (AADSTS65002)
- All ALDC service principal secrets in `vault/infra-credentials.md` are expired as of 2026-05-20 — SP auth requires secret rotation in Azure Portal
- **Eclipse Test 403 for GEP/Navira users (2026-05-27):** Root cause was zero Navira/GEP user documents in the Test CosmosDB (`aldctestcsdb1c01`), not a PBI SP or workspace issue. Fixed by copying 51 user documents from prod CosmosDB. The PBI embed SPs (`Power BI REST API GEP` and `GEP Admin`) have valid secrets through 2026-12 and Contributor access on GEP Test Models workspace.

**GEP model table names** (confirmed via DAX probing, 2026-05-20):
`Marketplace`, `Order`, `Order Line`, `Product`, `Vendor`, `Location`

## XMLA Automation (GEP)

For metadata-only model changes (new tables, columns, relationships, measures, format strings), GEP uses a programmatic XMLA path instead of opening the `.pbix` in PBI Desktop. See [[pbi-xmla-automation]] for the canonical pattern and [[pbi-model-apply-wrapper]] for the .NET wrapper (`pbi_model_apply.exe`) that runs TE3-compatible C# scripts via TOM + Roslyn. Validated end-to-end against [[GP-208]] on 2026-04-24.

Visual/report-layout edits (pages, visuals, bookmarks, colours) remain manual in PBI Desktop — no public API exists to automate them. The artifact's `changes.pbi_model.visual_required` flag keeps visual-bearing tickets on the manual republish path.

## Deployment Workflow

See [[gep-snowflake-pbi-deployment]] for the full end-to-end deployment including PBI refresh steps. For metadata-only model changes on GEP, the XMLA automation path above is the primary path; the manual `.pbix` republish is reserved for visual changes.

## Report Template

Source: Confluence CLIEN/904429569.

Template `.pbix` file lives in `Nextcloud\Customers\Style Guides`. A new file is created for each template version.

**Connection parameters (environment-specific):**
- Snowflake: `SNOWFLAKE_HOST`, `SNOWFLAKE_COMPUTE`
- Core API: `CORE_API_URL`, `CORE_API_CLIENT_TOKEN`, `CORE_API_ACCOUNT_ID`, `CORE_API_REPORT_ID`

Report documents (which carry the `CORE_API_REPORT_ID`) are configured in CosmosDB. `CORE_API_ACCOUNT_ID` and `CORE_API_REPORT_ID` differ per environment. See [[core_api]] for the report document schema.

Key template conventions:
- Do not edit the initial template page — always copy it first, keep the original hidden.
- New pages require updating bookmarks: Glossary Show, Metadata Show, Filters Show, Panels Hide.
- Glossary entries are populated from the Core API (keyed entries in the report CosmosDB document).

## Granting Excel Model Access

Source: Confluence CLIEN/1023115265.

PBI Excel models require a separate ALDC-tenant login per user (not the user's own O365 account). Each client gets a `<tenant>.aldc.io` subdomain.

**Prerequisites:** User Administrator + Billing Administrator roles in Microsoft 365 Admin Center.

**Process (high-level):**
1. Check available Power BI Premium Per User licenses in Microsoft 365 Admin → Licenses; purchase more if at 0.
2. Create Active User: `firstname.lastname@<tenant>.aldc.io` — assign **Power BI Premium Per User** license only.
3. Add user to the client's Security Group in Microsoft 365 Admin Center (the security group is already a member of the PBI workspace).
4. If user still can't access despite being in the group: grant individual Contributor access in the PBI Workspace → Access panel. Use `firstname.lastname@<tenant>.aldc.io` format.
5. Pre-login to powerbi.com with the new credentials to avoid a Forbidden error on first login.
6. Send onboarding email — see [[client-communications]] § Data Model Access Email.

**Licensing notes (as of 2022):**
- Fusion92: not paying per-user (< 10 users)
- GEP: paying per user — update the Service Item when users change

## Live Data Model — "Analyze in Excel" live pivots (client validation)

*Source: Navira live-data-model investigation 2026-06-18.*

**What clients (Navira/GEP) call "the data model" download.** The file downloaded from the legacy [[Eclipse]] reports page is a tiny (~31–37 KB) Excel workbook with **no data** — just an OLAP `MSOLAP.8` **live connection** to the published PBI semantic model (PBI's "Analyze in Excel" artifact). Opened in Excel **desktop** (not web), every PivotTable field drag is a live query against the model over the **XMLA endpoint**.

The only environment-specific value is the dataset GUID in `xl/connections.xml`:
```
name="pbiazure://api.powerbi.com <DATASET_GUID> Model"
Provider=MSOLAP.8; Integrated Security=ClaimsToken;
Initial Catalog=sobe_wowvirtualserver-<DATASET_GUID>; Data Source=pbiazure://api.powerbi.com; ...
```
PROD GUID = `74a529b3-…` (GEP Prod Models); TEST = `66151728-…` (GEP Test Models). **To make a TEST live workbook from the PROD one: swap the GUID in `connections.xml` (two occurrences) — that's the entire change.** Pivot caches reference the connection by id with `refreshOnLoad=1`, so they repopulate from the target model; if the field list still looks like prod after the swap, **Data → Refresh All**.

### Prerequisites for the live connection (why TEST historically "didn't work")
The live MSOLAP connection authenticates the **end user** against the dataset. It needs ALL of:
1. Dataset on a Premium/PPU capacity with **XMLA endpoint = Read** (or R/W). GEP Test Models already satisfies this (models are deployed there via XMLA).
2. An **ALDC-tenant account** (`firstname.lastname@gep.aldc.io`) with a **PBI Premium Per User** license.
3. **Build** permission on the dataset — workspace **Contributor** grants it; **Viewer is NOT enough** for Analyze-in-Excel.

Historical TEST gap (2026-06): **GEP Test Models had zero client users** while GEP Prod Models had `@gep.aldc.io` Contributors → the prod download worked but the test one auth-failed. Fixed 2026-06-18 by mirroring prod — added `asad.amin`/`shah.muttal`/`sarwar.osama` (@gep.aldc.io) + `lori.beck`/`mike.stuart` as **Contributor** on GEP Test Models (PBI REST `groups/{id}/users`).

### Serving it from legacy Eclipse
The download is an `app_report` row (`type=REPORT_TYPE_FILE`) in the Eclipse portal Postgres (`aldctestpgdbportal1c01`, db `eclipse`) pointing at a blob in `aldcteststac1cda8904db/files/`, plus an `app_group_reports` row for visibility (group 15 "All Reports", GEP `account_id=19`). Consumer download route = **`/file/<pk>/`** (e.g. `eclipse-test.aldc.io/file/56/`); consumer landing `/` redirects to the first report; `/account/reports/` is the **staff** management view and `/aldc_admin/` is Django admin (staff accounts get bounced there). The `file` view pulls the blob with the **active account's** storage creds, so the user must be in the **GEP** account context. **Gotcha:** the static `Data Model.xlsx` (`app_report` id 50) is regenerated daily by the `func-aldc-cred` timer — the live workbook must use a **distinct name** ("Data Model (Live)", id 56) or the timer overwrites it.

Tooling: `aldc-launchpad/scripts/_upload_reports_to_portal.py`, `_add_portal_report_row.py`; model structural diff `aldc-launchpad/pbi_ops/_compare_models.py`.

**Static duplicate removed from client view (2026-06-26).** Group 15 "All Reports" exposed BOTH the static `Data Model` (id 50, 41 MB daily dump) and `Data Model (Live)` (id 56), confusing the client. Removed the static one by **unlinking it from group 15** (`DELETE FROM app_group_reports WHERE id=62` — report 50 ↔ group 15) on the TEST portal DB (`aldctestpgdbportal1c01`, db `eclipse`, login `eclipse`/`aldc1234`). Report 50's row + blob left intact (timer keeps refreshing an unlinked, invisible blob — harmless); rollback = `INSERT INTO app_group_reports (group_id, report_id) VALUES (15, 50);`. Evidence the unlink is durable: `app_group_reports` id 62 is a stable low id (one-time manual grant, not churned by the timer) and report 50's `created_datetime` is unchanged while only `updated_datetime` moves (timer does in-place blob refresh, doesn't manage group links). **Do NOT rename report 56 to plain "Data Model"** — the timer matches the static report by name/`Data Model.xlsx`; the `(Live)` name + distinct `Data Model (Live).xlsx` file is the protection against the timer overwriting it. Full delivery verification (both auth layers + DAX==SQL) in [[navira-roadmap-status]] § Delivery verified end-to-end (2026-06-26).

**GP-226 render-check (2026-07-22 — DAX done, rendered pending).** `Data Model (Live)` (id 56, bound to Daily model `66151728`) now surfaces the GP-226 cross-channel ad spend + Amazon ad-type split (`Spend - Amazon Sponsored Products/Brands/Display` + the 3 SP/SB/SD columns, `Marketing Efficiency` (+Product)). Both PBI models read canonical `REPORT_COMMON.MARKETING_EFFICIENCY(_MARGIN)` (the orphaned `_FIXED` pair was dropped 2026-07-22). Per the global consumer-layer rule, the **rendered** surfaces still need confirming (not just DAX): (1) download `/file/56/`, open in **desktop Excel**, refresh the live connection, confirm the new fields are in the field list + numbers populate (browser automation can't paint this Analyze-in-Excel pivot); (2) open the reports in the **"GEP Test Models"** PBI workspace and confirm every visual paints (no "Error loading data"), toggling each slicer. Target numbers + full runbook: `aldc-launchpad/boot-prompts/navira-gp226-rendered-validation.md` (Navira CM $37,894,667; UK ad spend $6,602; Amazon $2,499,932 = SP+SB+SD; Daily Gross $128,491,426). NB the Daily model intentionally HIDES the 29 analytics measures (only Spend + Contribution Margin visible) — that is GP-226 design, not a defect.

### PROD vs TEST model parity (verified 2026-06-18; closed 2026-06-19)
Structural diff (TOM dump of both models): **TEST is a clean structural superset of PROD** — all 30 prod tables exist in test; **all 245 prod measures and all prod relationships now present** (`_compare_models.py` reports PROD-only measures: 0, PROD-only relationships: 0). TEST adds 5 tables (`Agency`, `Marketing Efficiency`, `Marketing Efficiency Product`, `Google Brand/Product Grounding`) + ~49 measures (the in-flight roadmap features incl. Flag A/B guards, prod-promotion pending). Every difference maps to a roadmap ticket, and **GP-199 + GP-200 are present in both**. The two items where TEST trailed PROD were both closed 2026-06-19: **GP-256 `Actual - Sales - Return Rate %`** (added to TEST, validates 4.20%) and **`Traffic Activity[MARKETPLACE_KEY]`** + its Marketplace relationship — the latter was *not* warehouse-side: `WAREHOUSE.TRAFFIC_FCT_ACTIVITY` already exposed the column and the TEST/PROD refresh-policy M were byte-identical, so the fix was a pure model add (TOM column + relationship, then a single-table `type=full` enhanced-refresh to populate it + `type=calculate` recalc; validated measures byte-identical, 1 distinct MK / 0 blank, full source-row parity). Conclusion: anything Navira validates against prod today behaves identically in test. See [[navira-roadmap-status]] § TEST↔PROD parity for the full diff + the 2026-06-19 relationship-health/island fixes (Google Grounding→Agency, Marketing Activity→Campaign) and the redundant-dataset cleanup.

### Agency-aware sales model (GP-254 Option C, TEST 2026-06-19)
The `Order Line` sales fact is now multi-entity: it carries `ENTITY_CODE` (NAVIRA/LECTRIC) with an active
many:1 relationship to the `Agency` dim, so **every Sales Measure responds to the Agency slicer** (before,
only Marketing Efficiency did). The `Agency` dim gained `ENTITY_ROLE` (HOUSE=Navira / AGENCY=Lectric+future).
Rollup measures in `Sales Measures` → "Agency Rollups": `[base] (All Agencies)` =
`CALCULATE([base], REMOVEFILTERS('Agency'), 'Agency'[ENTITY_ROLE]="AGENCY")` (agencies only, excl Navira);
`[base] (Company Total)` = `CALCULATE([base], REMOVEFILTERS('Agency'))`. **Default unfiltered sales now =
Company Total (incl Lectric).** Pattern is the warehouse conformed-component work (see [[navira-roadmap-status]]
§ GP-254). Same incremental-column recipe below was used to populate `Order Line[ENTITY_CODE]`.

**Gotcha — adding a column to an incremental-refresh table:** new column metadata alone won't populate; a `type=calculate` recalc only builds calc/relationship indexes. You must run a **`type=full` enhanced-refresh scoped to that table** (`objects:[{table}]`, `applyRefreshPolicy:false`) to reprocess existing partitions and pull the new column from the source view, *then* `type=calculate`. If the table's refresh-policy `SourceExpression` selects all columns (no explicit column list), no M edit is needed — the new view column flows in automatically on reprocess.

## Agentic Power BI (Microsoft, first-party)

- Source: https://github.com/MicrosoftDocs/powerbi-docs/blob/main/powerbi-docs/developer/agentic/power-bi-agentic-overview.md
- Raw: https://raw.githubusercontent.com/MicrosoftDocs/powerbi-docs/main/powerbi-docs/developer/agentic/power-bi-agentic-overview.md
- Captured: 2026-08-23 — flagged as relevant to the **Power BI Data Model Designer** agent team
  in [[agent-factory]], which is currently blocked on the fact that no contract exists for what
  its output must satisfy.
- Status: **UNREAD** — saved as a pointer only. Nobody has read this doc yet, so nothing in it
  is a design premise. Tier it before citing: Microsoft product docs are `MARKETED` until a
  capability has been exercised against a real tenant.

**Why it matters:** if Microsoft ships a first-party agentic surface over Power BI models, that is
either the contract we would otherwise have to author, or the incumbent we would be duplicating.
Both readings change the Power BI team's design, so this is a build-vs-defer input.

**It sharpens an open question rather than answering one.** The agent-factory boot prompt records the
Power BI team as blocked on a non-existent contract. If Microsoft's agentic layer *defines* that
contract, the team's unlock condition changes materially — which is worth a real read rather than a
skim. `prospect` is the right instrument: it tiers vendor claims and refuses `MARKETED` ones as
design premises.

⚠ **This repo is Microsoft's documentation, not a library we can depend on.** Its value is
intelligence about what the platform will do for us, so treat the save as research input, not a
technical dependency.

### The blocking contract now exists (2026-08-23)

The "blocked on a non-existent contract" premise above is superseded. `factory/pbi_contract.py` in
[[agent-factory]] ships the **Power BI GreenContract**, M1 through M12, mirroring the
connector-migration GreenContract one layer up — built deliberately *before* any Power BI agent
exists. Same rendered-surface lesson this page already carries from GP-293/GP-318 (stale
`dataset_name` passing DAX parity while every visual errors; false zeros where the source reports
nothing), now stated as an executable contract rather than a postmortem: two of the twelve
assertions — every visual paints, every slicer responds — are declared even though no XMLA/DAX
instrument can observe either, and default to `Unmeasurable` rather than being silently dropped, so
an estate with no renderer wired reports "did not look" instead of a false PASS. See
[[agent-factory]] §"The Power BI GreenContract" for the full assertion list.

### Comparing a model against its source — three traps that all fail toward a false alarm (2026-09-10)

From ALDC-1302, where a parity gate reported "escalate the driver cutover" and every part of that
verdict turned out to be wrong. All three traps share a shape: **they manufacture a divergence, and
a manufactured divergence reads as a defect.**

**1. ⛔ NULL semantics differ between DAX and SQL. Mirror them or the comparison means nothing.**

| | DAX | SQL |
|---|---|---|
| `col < cutoff` where col is blank/NULL | **TRUE** — row INCLUDED | UNKNOWN — row EXCLUDED |
| `DISTINCTCOUNT(col)` / `COUNT(DISTINCT col)` | counts BLANK as **one value** | **discards** NULL entirely |

So the SQL side must read `(col < cutoff OR col IS NULL)`, and a distinct count needs
`COUNT(DISTINCT k) + (CASE WHEN COUNT(*) > COUNT(k) THEN 1 ELSE 0 END)`. Unmirrored, one run
compared `pbi=39,929` against `snowflake=10,272` and read as a **4× divergence** — the entire gap
was the 29,657 rows with a blank date. A key column holding any NULL diverges by exactly 1, every
time, which reads as a subtle corruption rather than an artefact.

**2. An incremental table's history is an ARCHIVE, and a green refresh never touches it.**
Measured on GEP Prod `Order Line`: **97 partitions, 91 of them last refreshed 2026-07-07**, with only
a rolling ~3-month window updating. Every refresh since has reported success. So the model held
**8,968 order lines the warehouse no longer has**, and no normal refresh will ever correct them —
that needs `RefreshType.Full` on the archived partitions. ⚠ Corollary: *"the refresh completed"*
says nothing about 94% of the table.

**3. A gate's verdict is not a diagnosis — localise before escalating.** The gate printed
`H1 — the model disagrees with its source, escalate the ADBC cutover`. Breaking the same comparison
down by period killed it in one table: **8,968 of 8,975 rows of divergence sat in the blank-date
bucket while 2.87M dated rows agreed to within 7**. A transport or driver defect cannot confine
itself to one date bucket. The cheap discriminator — *group the divergence by an axis and see
whether it concentrates* — should run **before** anyone is told to roll back a platform change.

⚠ Two more things that read like permissions failures and are not: `RowCount` is **not** a
`$SYSTEM.TMSCHEMA_PARTITIONS` column (asking for it fails the whole query with *"the specified column
was not found"*), and `GET_DDL` on a `WAREHOUSE.*` wrapper view returns only
`SELECT * FROM WAREHOUSE_SOURCE.*` — read the `WAREHOUSE_SOURCE` object for the real definition.

## See Also

- [[three-layer-presence-census]] — answering "is this data in prod?" without a false negative
- [[Snowflake]] — direct data source (via Snowflake.Databases M connector)
- [[SSMS]] — XMLA client into the PBI tabular model (for partition re-processing of historical data)
- [[pbi-xmla-automation]] — canonical pattern for programmatic model metadata changes
- [[pbi-model-apply-wrapper]] — .NET 8 wrapper that replaces TE3 CLI for scripted XMLA applies
- [[pbi-xmla-model-changes]] — TOM gotchas (schema discovery, Mode=Import, drop-if-exists)
- [[Confluence]] — detailed dataflow diagram (treat SQL-Server-intermediate framing with correction above)
- [[star-schema-convention]] — warehouse naming that feeds report_common views
- [[data-pipeline-flow]] — PBI's position in the full pipeline
- [[GEP]] — primary client using PBI
- [[client-communications]] — email templates for model access notifications
