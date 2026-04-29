---
tags: [entity, tool, power-bi, reporting, visualization]
aliases: [Power BI, PBI]
sources: [clients repo report_common/ directories, Obsidian vault notes, daily/2026-04-17.md, GP-208 Data Source Settings check 2026-04-21]
created: 2026-04-16
updated: 2026-04-24
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

## Power BI Workspaces (GEP)

| Workspace | Snowflake Environment | Branch | Refresh Cadence |
|-----------|----------------------|--------|-----------------|
| GEP Test Models | `TEST_DG1_GEP` | `GEP/user-testing` | **Scheduled — once daily at 07:00 Pacific** (next scheduled fire 2026-04-22 07:00; last fire 2026-04-21 07:07:10 — PBI drift of a few minutes is normal). Ad-hoc refresh also available on demand. |
| Production | `PROD_DG1_GEP` | `main` | See semantic model refresh settings in the Production workspace (confirm before quoting). |

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

## See Also

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
