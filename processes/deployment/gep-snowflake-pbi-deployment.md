---
tags: [process, deployment, gep, snowflake, power-bi, runbook]
aliases: [GEP Deployment Runbook, Snowflake Deployment, PBI Deployment, GEP Deploy]
sources: [sources/obsidian-import/deployments/Order of Operations.md, sources/obsidian-import/deployments/GP-200.md, sources/obsidian-import/deployments/Future Improvements - CREATE TICKET FOR THIS.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Deployment Steps-Guide - Paul.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Deployment Steps-Guide - Steven.md]
created: 2026-04-16
updated: 2026-05-22
---

# GEP Snowflake + Power BI Deployment Runbook

End-to-end deployment guide for shipping changes to the [[GEP]] client's data warehouse and reporting layer. Covers the full cycle from feature branch through [[Snowflake]] deploy and [[Power BI]] model refresh. This runbook was battle-tested during the GP-200 (Amazon UK orders) deployment and generalized for reuse.

> **When to use this vs [[client-release-checklist]]**: this page is the GEP-specific end-to-end walkthrough with per-phase pitfalls and exact error messages. For a **generic** client release checklist (any client, simpler form), see [[client-release-checklist]]. Both reference the same underlying [[git-branching-strategy]].

**Key principle**: Code merge does NOT auto-deploy. [[Snowflake]] and [[Power BI]] deploys are always manual steps.

> **XMLA automation for metadata-only PBI changes (added 2026-04-24).** For new tables, columns, relationships, measures, and format strings — i.e. anything that does NOT change visual layout — GEP now supports programmatic model updates via `pbi_model_apply.exe` (XMLA + TOM + Roslyn) instead of the PBI Desktop republish described in Phase 10 below. See [[pbi-xmla-automation]] for the pattern and [[pbi-model-apply-wrapper]] for the wrapper. Phases 9 and 10 of this runbook still apply when changes include visual edits (`changes.pbi_model.visual_required = true`) or when `.pbix` artefacts themselves need updating in `repos/power_bi`. First validated end-to-end on [[GP-208]] (2026-04-24).

## Prerequisites

- Access to [[Snowflake]] (Snowsight web UI) for both `TEST_DG1_GEP` and `PROD_DG1_GEP`
- Access to [[Power BI]] Service (`app.powerbi.com`) with permissions on `GEP Test Models` and Production workspaces
- Service account credentials for Power BI (stored in Dashlane as "PBI Snowflake Non-Prod" and equivalent prod entry)
- The [[clients-repo]] cloned locally with the feature branch ready
- If adding a new data source: credentials for that source (check Dashlane), connection/template JSON files prepared, and CosmosDB access for [[Eclipse]] registration

## Branch & Environment Model

| Branch | Snowflake Environment | Power BI |
|---|---|---|
| `feature/...` | (none -- local validation only) | (none) |
| `GEP/development` | (none directly -- features merge here first) | (none) |
| `GEP/user-testing` | `TEST_DG1_GEP` | `GEP Test Models` workspace |
| `main` | `PROD_DG1_GEP` | Production workspace |

See [[data-pipeline-flow]] for how data flows through the full stack.

## Steps

### Phase 1: New Data Source Registration (skip if not adding a source)

1. Create the [[Eclipse]] connection JSON under `GEP/eclipse/connections/`
2. Create the [[Eclipse]] template JSON under `GEP/eclipse/templates/`
3. Register the connection in CosmosDB
4. Register the work template in CosmosDB
5. Verify the connector accepts your configuration values (e.g., `filter_marketplace` for Amazon uses ISO country codes: `"us"`, `"ca"`, `"gb"`)
6. Trigger the template run via [[Eclipse]] and confirm data appears in the expected raw [[Snowflake]] table (e.g., `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK`)
7. Spot-check the data:
   ```sql
   SELECT COUNT(*), MIN(PURCHASE_DATE), MAX(PURCHASE_DATE)
   FROM PROD_DG1_GEP.<SCHEMA>.<RAW_TABLE>;
   ```

### Phase 2: CSV Supplements (skip if no new dimension entries)

Only required when adding a new marketplace, company, or other dimension value that needs human-readable names in `SHARED_DIM_MARKETPLACE` or similar.

1. Add rows to the relevant CSVs on Nextcloud:
   - Marketplace Name: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Name`
   - Marketplace Config: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Config`
2. Trigger a CSV supplement refresh or wait for the scheduled pull (CSVs flow into `PROD_DG1_GEP.SUPPLEMENT.CURRENT_*_CSV` tables)

### Phase 3: Local Validation Testing

Before opening a PR.

1. Create a personal test schema in [[Snowflake]]:
   ```sql
   CREATE SCHEMA WAREHOUSE_TEST_PAUL;
   ```
2. Copy relevant tables/views into your test schema
3. Run your changed SQL files against the test schema
4. Write and run validation queries specific to your change (e.g., currency mapping checks, dedup verification, row counts per company)
5. Confirm all validation passes, then open a PR targeting `GEP/development`
6. Get code review, then merge feature branch into `GEP/development`

### Phase 4: Snapshot Baseline Counts

**Before deploying any SQL**, capture baseline counts you can compare post-deploy:

```sql
-- Tailor this to whatever your change touches
SELECT TRANSACTION_CURRENCY_ID, COUNT(*) AS cnt
FROM WAREHOUSE.SALES_DIM_ORDER_BASE
WHERE ORDER_ID LIKE 'AMZ_%'
GROUP BY TRANSACTION_CURRENCY_ID;
```

Save the results. You will compare against them after materialization.

### Phase 5: Deploy SQL Views to Snowflake Test

Deployment is manual -- copy each SQL file from the repo and execute it in the Snowsight UI.

1. In Snowsight, set your database context to `TEST_DG1_GEP`
2. Execute each changed SQL file **in dependency order**. Typical order for orderline changes:
   1. `GEP/snowflake/warehouse/sales_dim_order_base.sql` -- updates `WAREHOUSE_SOURCE.SALES_DIM_ORDER_BASE` view
   2. `GEP/snowflake/warehouse/sales_fct_amazon_orderline.sql` -- updates view + creates table
   3. `GEP/snowflake/warehouse/sales_fct_seller_cloud_orderline.sql` -- updates view + creates table
   4. `GEP/snowflake/warehouse/extract_warehouse_metadata.sql` -- updates metadata view
   5. `GEP/snowflake/warehouse/shared_dim_marketplace.sql` -- updates marketplace view (live immediately, no task needed)
3. Watch for errors. Expected/ignorable errors are documented in Pitfalls below. Unexpected errors usually mean a data-share gap.

### Phase 6: Materialize Physical Tables

Views deployed in Phase 5 update `WAREHOUSE_SOURCE.*` (the logical view layer). Physical tables in `WAREHOUSE.*` are populated by scheduled [[Snowflake]] tasks.

**Option A -- Wait for cron (slow):**
- `TASK_WAREHOUSE_ORDERLINE_0` runs **once daily at 06:00 America/Vancouver** (`USING CRON 0 6 * * * America/Vancouver`). Verified 2026-04-21 via `SHOW TASKS LIKE 'TASK_WAREHOUSE_ORDERLINE%' IN DATABASE TEST_DG1_GEP`.
- `task_warehouse_extract_metadata` runs at :00 each hour (verify separately; not re-confirmed in 2026-04-21 check)
- Means: new rows deployed during the day won't materialize in `WAREHOUSE.*` until the next 06:00 PDT window unless you manually trigger.

**Option B -- Trigger manually (fast, recommended):**
1. Snowsight -> **Monitoring -> Task History**
2. Search for `TASK_WAREHOUSE_ORDERLINE_0`
3. Click into the task -> **Graph** tab
4. Click **Run** on the root node -- this fires the full 10-step DAG:
   - 0: `SALES_DIM_ORDER_BASE`
   - 1: `SHARED_DIM_PRODUCT_BASE`
   - 2: `SALES_FCT_SELLER_CLOUD_ORDERLINE`
   - 3: `SALES_FCT_AMAZON_ORDERLINE`
   - 4: `SALES_FCT_COST` (depends on `AMAZON_ADS` schema)
   - 5-9: downstream tables
5. Watch Task History -- all 10 steps should turn green (`SUCCEEDED`)

**Verify task chain success:**
```sql
SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD(HOUR, -2, CURRENT_TIMESTAMP())
))
WHERE NAME LIKE 'TASK_WAREHOUSE_ORDERLINE%'
ORDER BY SCHEDULED_TIME DESC;
```

If any step is `FAILED`, see the triage guide in Pitfalls below.

### Phase 7: End-to-End Validation (Snowflake Test)

Run after all task steps show `SUCCEEDED`.

**7a. Functional checks** (adapt to your change):
```sql
-- Example: verify new marketplace orders appear
SELECT COUNT(*), MIN(CREATE_DATE), MAX(CREATE_DATE)
FROM WAREHOUSE.SALES_DIM_ORDER_BASE
WHERE COMPANY_ID = <expected_company_id>;

-- Verify order lines exist
SELECT COUNT(*)
FROM WAREHOUSE.SALES_FCT_AMAZON_ORDERLINE OL
INNER JOIN WAREHOUSE.SALES_DIM_ORDER_BASE OB ON OB.ORDER_KEY = OL.ORDER_KEY
WHERE OB.COMPANY_ID = <expected_company_id>;

-- Verify marketplace dimension entry
SELECT DISTINCT MARKETPLACE_NAME
FROM WAREHOUSE.SHARED_DIM_MARKETPLACE
WHERE MARKETPLACE_NAME LIKE '%<new_marketplace>%';
```

**7b. Volume sanity check** -- compare against Phase 4 baseline:
```sql
SELECT
    COMPANY_ID, COMPANY_NAME,
    CASE WHEN ORDER_ID LIKE 'AMZ_%' THEN 'Amazon feed'
         WHEN ORDER_ID LIKE 'SC_%' THEN 'Seller Cloud'
         ELSE 'Other' END AS source,
    COUNT(*) AS cnt
FROM WAREHOUSE.SALES_DIM_ORDER_BASE
WHERE COMPANY_ID IN (163, 166, 168, 174, 178)
GROUP BY 1, 2, 3
ORDER BY 1, 3;
```

> When comparing pre/post volumes: Amazon orders that also exist in SellerCloud are deduped out of the Amazon leg (SC is system of record). If SC data grew (e.g., via a data-share switch), `AMZ_*` counts will shrink while `SC_*` counts grow. Total per-company volume (AMZ + SC combined) is the meaningful metric.

**7c. Currency mapping check:**
```sql
SELECT COMPANY_ID, COMPANY_NAME, TRANSACTION_CURRENCY_ID, COUNT(*) AS cnt
FROM WAREHOUSE.SALES_DIM_ORDER_BASE
WHERE COMPANY_ID IN (163, 166, 168, 174, 178)
GROUP BY 1, 2, 3
ORDER BY 1, 4 DESC;
```

Each company should map to its expected currency. Small `ZZZ` rows indicate unmapped SellerCloud currency codes -- investigate but don't necessarily block.

### Phase 8: Promote to User Testing

1. Open PR: `GEP/development` -> `GEP/user-testing`
2. Tag a reviewer (typically the same person who reviewed your feature PR)
3. Once approved, merge

> In the current GEP setup, `GEP/user-testing` and Snowflake Test point at the same environment (`TEST_DG1_GEP`). No separate Snowflake deploy is needed after this merge.

### Phase 9: Refresh & Validate Power BI Test Model

> **Refresh cadence:** the GEP Test semantic model runs a **scheduled refresh once daily**. During a deploy you almost always want to trigger an ad-hoc refresh immediately rather than waiting for the next scheduled fire — otherwise the test model won't reflect your change until the schedule next runs.

**9a. Trigger an ad-hoc refresh:**
1. Go to `app.powerbi.com`
2. Workspace: **GEP Test Models**
3. Find the **Semantic model** row (NOT the Report row)
4. Click **...** (More options) -> **Refresh now**
5. Watch **... -> Refresh history** for completion (can take a few minutes to 30+ minutes)

> If credentials have expired, refresh will fail. Fix via **... -> Settings -> Data source credentials -> Edit credentials**. See [[powerbi-secret-refresh]] for the secret lifecycle.

**9b. Smoke-test in Explore (web):**
1. On the Semantic model page, click **Explore** in the top toolbar
2. Build a Marketplace x Sales matrix:
   - From **Marketplace** table, drag **Marketplace Name**
   - From **Marketplace Measures**, drag a measure like **Actual - Sales - Gross**
   - **Important**: use a **measure**, not a raw column. Raw `Order ID` count from the Order table gives the same total for every marketplace because Order is not directly related to Marketplace (see Pitfall 4 below).
3. Add **Transaction Currency** as a column to verify currency attribution

**9c. Validation checklist** (adapt to your change):
- [ ] New marketplace/entity appears in the slicer
- [ ] Sales are in the correct currency only (no leakage)
- [ ] Currency column total matches the marketplace row total
- [ ] Orders span multiple time periods (not a single dump)
- [ ] Other existing marketplaces are present and stable/grew
- [ ] No new blank/Unknown marketplace rows unexpectedly

**9d. Notify stakeholders:**
- [ ] Notify GEP that the change is available in the test model for UAT
- [ ] Include caveats (e.g., volume step-changes from data-share switches)

### Phase 10: Deploy to Production

For production deployment of the [[Power BI]] model (from Steven's deployment guide):

1. Download the model `.pbix` file from GitHub (usually in a dated folder)
2. Open with [[Power BI]] Desktop
3. Set environment parameters for production:
   - Go to `Transform Data > Edit Parameters`
   - Set `CORE_API_URL` to `https://aldcprodfnapcore1c01.azurewebsites.net`
   - Set `SNOWFLAKE_HOST` to `wj66376.canada-central.azure.snowflakecomputing.com`
4. Refresh the data in Desktop
5. Save the model to a **temporary location** (NOT back to the repo -- repo models always point to test)
6. Publish to [[Power BI]] Service:
   - Ensure the file name matches the existing model
   - Select the correct workspace
   - Confirm the overwrite warning
7. In Power BI web, verify the refresh started (or trigger it manually)
8. Validate using Analyze in Excel or Explore

**Test environment parameters** (for reference -- these are the defaults in the repo):
- `CORE_API_URL`: `https://aldctestfnapcore1c01.azurewebsites.net`
- `SNOWFLAKE_HOST`: `og35375.canada-central.azure.snowflakecomputing.com`

### Phase 11: Cleanup

1. Drop personal test schema:
   ```sql
   DROP SCHEMA IF EXISTS WAREHOUSE_TEST_PAUL CASCADE;
   ```
2. Archive any one-off testing/scratch SQL files in `GEP/_testing/`
3. Ensure task-tracking scratch files are not committed (gitignored/unstaged)
4. File any follow-up tickets identified during deploy

## Excluding an order from all numbers (pattern — GP-283)

To drop a specific order from every report/PBI number (sales, COGS, returns, margin, order counts), use the dedicated exclusion view — **do not** hand-edit literals into the big order-base view.

1. Add a row to `WAREHOUSE_SOURCE.SALES_DIM_ORDER_EXCLUSIONS` (`clients/GEP/snowflake/warehouse/sales_dim_order_exclusions.sql`): warehouse-form `ORDER_ID` (`SC_<sellercloud_id>` or `AMZ_<amazon_id>`) + reason + requester + date.
2. `sales_dim_order_base.sql` already references it via a NULL-safe `NOT EXISTS` (use `NOT EXISTS`, never `NOT IN` — a NULL in the list would silently drop *all* orders). Because `SALES_FCT_ORDERLINE` INNER JOINs `SALES_DIM_ORDER` (← `SALES_DIM_ORDER_BASE`), removing an order at the base view drops all its lines everywhere downstream — retroactive and forward.
3. **Confirm the identifier first** (don't infer): query the raw source + built `SALES_DIM_ORDER` to prove which exact object the number maps to and that it resolves to one order. See [[confirm-consumer-source]].
4. Deploy the exclusion view + rebuild order_base → dim_order → fct_orderline (Phase 6), refresh PBI (Phase 9), validate (below).
5. Future self-service version (client maintains a CSV) is [[GP-284]].

### Drift-immune validation (use this, not grand-total before/after)
The warehouse reads a live, moving source ([[accumulating-source-tables]]), so a plain before/after grand-total comparison **conflates your change with source drift** and will look wrong. Instead: stand up a **shadow** of the *original* (pre-change) view from the captured rollback DDL and diff the order-ID sets against the deployed view in a **single statement** (consistent snapshot). The symmetric difference must be exactly your intended order(s). This caught a real scope problem on GP-283 (below).

### Gotcha: `GEP/development` is an integration branch — do NOT promote it wholesale
`development` accumulates in-flight work (e.g. GP-225 marketing schema). A `development → user-testing → main` PR carries **all** of it (GP-283 saw 124 files / ~8K lines). For a narrow fix, **cherry-pick the single commit** onto `user-testing` and `main` instead. Likewise, the repo `sales_dim_order_base.sql` can be **ahead of prod** (prod ran an older UK branch — see [[GP-282]]); deploying the repo file wholesale to prod silently promotes that delta. Scope prod deploys to *prod's own baseline + your change* and prove it with the drift-immune diff.

## Post-Deploy Verification Checklist

Run these after any warehouse view deployment on `wj66376` (production). Added 2026-05-22 following GP-PENDING-sales-data-outage-2026-05-22 (task chain suspended 14 hours due to cross-database grant loss).

### PD-1: Verify task chain health

After deploying views, confirm the root task is still in `started` state and not silently suspended:

```sql
-- Run after any warehouse view deployment on wj66376
SHOW TASKS IN DATABASE PROD_DG1_GEP;
-- Verify TASK_WAREHOUSE_ORDERLINE_0 state = 'started' (not 'suspended')
-- If suspended: check last_suspended_reason, fix the issue, then:
ALTER TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0 RESUME;
EXECUTE TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0;
```

> Snowflake auto-suspends the root task after repeated failures. A suspended task produces **no error in the deploy output** — it silently stops materializing data. This was the root cause of the 2026-05-22 outage.

- [ ] `TASK_WAREHOUSE_ORDERLINE_0` state = `started`
- [ ] If suspended: identify `last_suspended_reason`, resolve root cause, RESUME + EXECUTE

### PD-2: Verify cross-database grants

`SHARED_FCT_EXCHANGE_RATE` depends on `PROD_DG1_ALDC_LIBRARY` (cross-database). Verify the task service role can still reach it — this grant can be silently lost after certain DDL operations:

```sql
-- SHARED_FCT_EXCHANGE_RATE depends on PROD_DG1_ALDC_LIBRARY (cross-database)
-- Verify the task role has access:
USE ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;
SELECT COUNT(*) FROM PROD_DG1_ALDC_LIBRARY.WAREHOUSE.SHARED_FCT_EXCHANGE_RATE;
-- If this fails, re-grant as ACCOUNTADMIN:
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE PROD_DG1_ALDC_LIBRARY TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;
GRANT USAGE ON SCHEMA PROD_DG1_ALDC_LIBRARY.WAREHOUSE TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;
GRANT SELECT ON ALL VIEWS IN SCHEMA PROD_DG1_ALDC_LIBRARY.WAREHOUSE TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;
```

- [ ] `SELECT COUNT(*) FROM PROD_DG1_ALDC_LIBRARY.WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` returns a row count (not an auth error)
- [ ] If it fails: re-grant as ACCOUNTADMIN and re-run the manual task trigger (Phase 6)

See [[GP-PENDING-sales-data-outage-2026-05-22]] for full incident context.

### PD-3: Verify READER roles too — `SELECT ON ALL` dies with the object it was granted on

*Added 2026-09-03 from [[GP-318]]. PD-2 covers the **task service** role. The same failure hits
**reader/reporting** roles, and it is quieter because nothing gets suspended — a dashboard just 500s.*

**Measured in TEST (`og35375`, `TEST_DG1_GEP`), 2026-09-02/03.** A read-only role created 2026-09-01
with `GRANT SELECT ON ALL TABLES/VIEWS IN DATABASE` **plus** `ON FUTURE` could not resolve
`WAREHOUSE.SALES_FCT_ORDERLINE`:

```
SQL compilation error:
Object 'TEST_DG1_GEP.WAREHOUSE.SALES_FCT_ORDERLINE' does not exist or not authorized.
```

⭐ **The discriminating measurement.** Of the **34** objects that role could see in `WAREHOUSE`,
**zero were created after its grant date** — the 27 views top out at 2026-08-12, the 7 base tables at
2026-07-08. The role sees exactly the objects that have **not** been refreshed since it was granted.

`WAREHOUSE_SOURCE` copies into `WAREHOUSE` via a task chain, and a task doing `CREATE OR REPLACE`
**drops the object and takes its grants with it**. `SELECT ON ALL` is point-in-time, so it covers
nothing created afterwards:

> **Every refresh blinds every reader role granted with `ON ALL`.** The service role has PD-2 to
> catch it. Reader roles had nothing.

⚠ **`ON FUTURE` at database level did not save it** — worth knowing before relying on it. A
schema-level future grant takes precedence over a database-level one, so a database-level `ON FUTURE`
can be silently inert for a given schema. **Not confirmed** as the mechanism here (confirming needs
`ACCOUNT_USAGE`, which a reader role cannot read); recorded as the leading candidate.

**The verdict trap that makes this expensive.** Snowflake returns `does not exist or not authorized`
for both worlds deliberately, so it cannot leak hidden objects. Good security, terrible diagnosis:
**an under-granted role is indistinguishable from deleted data at the point of failure**, and the two
have entirely different owners. This produced one wrong published conclusion before it was caught.

*Separate them like this — a dependent secure view executes with its OWNER's rights, so it reads what
the caller cannot:*

```sql
-- 1. can the READER see it?  (role-visible only)
SHOW VIEWS LIKE 'SALES_FCT_ORDERLINE' IN SCHEMA TEST_DG1_GEP.WAREHOUSE;
-- 2. does a dependent view still return rows?   -> if yes, the object EXISTS
SELECT COUNT(*) FROM TEST_DG1_GEP.REPORT_COMMON.MARKETING_EFFICIENCY;
-- 3. decisive, needs privileges above the reader:
SELECT REFERENCED_SCHEMA, REFERENCED_OBJECT_NAME
FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
WHERE REFERENCING_OBJECT_NAME = 'MARKETING_EFFICIENCY';
```

Reading 2 returned **12,378** rows while reading 1 returned **nothing** — only possible if the object
exists and the reader is under-granted.

- [ ] After any task-chain refresh, confirm each reader/reporting role can still `SELECT` the
      refreshed objects — not only the service role
- [ ] Prefer a **schema-level future grant**, or a **grant step inside the task chain**, over
      re-granting after each incident. `ON ALL` alone guarantees this recurs

⛔ **Do not diagnose this from the error text.** Run readings 1 and 2 before concluding anything about
whether data is missing.

## Pitfalls / Gotchas

These were all encountered during real deployments and cost significant debugging time. Read them before deploying.

### 1. Data-share gaps in Snowflake Test

SQL files reference `PROD_DG1_GEP.*` schemas via an external data share configured manually in the Snowflake **prod** UI (not defined in the repo). Objects can be missing from the share.

**Symptoms:**
- `SQL compilation error: Object 'PROD_DG1_GEP.X.Y' does not exist or not authorized`
- Task chain: `Failure during expansion of view 'X': Error in secure object`

**Known gaps discovered during GP-200:** `SELLERCLOUD_SQL.CURRENT_MAIN_PURCHASEITEM`, `AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`

**Fix:** Add the missing object to the share in the Snowflake **prod** UI, then re-run. Consider auditing the share against all `PROD_DG1_GEP.*` references in `GEP/snowflake/warehouse/**/*.sql` before your first deploy.

**This can recur post-deploy.** On 2026-04-21, `CURRENT_REPORT_ALL_ORDERS_UK` was present in the share at 06:00 PDT (task chain succeeded), then dropped out mid-day (likely via an Eclipse `CREATE OR REPLACE TABLE` refresh revoking the object-level grant), then failed at 13:26 PDT. If a stakeholder reports fresh data missing from test days/weeks after a deploy, check the share before assuming a code issue. Permanent fix options tracked in [[GP-PENDING-data-share-stability]].

### 2. extract_warehouse_metadata.sql view-vs-table conflict

Line 109 uses `CREATE OR REPLACE SECURE VIEW WAREHOUSE.EXTRACT_WAREHOUSE_METADATA` but the hourly task materializes the same name as a physical TABLE. Snowflake cannot use `CREATE VIEW` to replace a TABLE.

**Symptom:** `Object 'EXTRACT_WAREHOUSE_METADATA' already exists as TABLE`

**This is harmless.** The source view (lines 1-107) succeeds, and the next task run rebuilds the table. Ignore the error.

### 3. Data-share switch causes step-change in volume

When a data-share switch (like GP-207) lands in Test for the first time, pre-deploy and post-deploy volumes will look very different. The dedup logic at `sales_dim_order_base.sql:254-265` means `AMZ_*` counts drop while `SC_*` counts rise -- total per-company volume should grow or stay stable.

**Diagnosis steps:**
1. Check `INFORMATION_SCHEMA.TASK_HISTORY` for completion
2. Compare live view vs materialized table
3. Check raw source row counts
4. Use per-company x source breakdown -- if AMZ + SC totals per company grew, the change is fine

**Always flag step-changes to GEP stakeholders.** They will wonder about dramatic volume shifts.

### 4. Power BI relationship structure -- Order not directly related to Marketplace

`SALES_DIM_ORDER_BASE` does not have `MARKETPLACE_KEY`. Marketplace joins to the orderline fact tables, not the order dimension. Dragging `Order ID (Count)` against `Marketplace Name` returns the same total for every marketplace -- this is correct schema behavior, not a bug.

**Fix:** Use a measure from **Marketplace Measures** (aggregates over Order Line internally), or use columns from the Order Line table.

### 5. Missing currency mappings in SHARED_DIM_COMPANY_CURRENCY_MAP

When adding a new currency or company, verify `shared_dim_currency_company_map.sql` covers it. Currently mapped: USD (163), CAD (166), MXN (168), BRL (174), GBP (178). EUR mappings for European companies (181, 182, 184, 187) were missing as of GP-200.

**Diagnostic:**
```sql
SELECT O.COMPANYID, O.ORDERCURRENCYCODE, COUNT(*) AS cnt
FROM PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_ORDER O
LEFT JOIN WAREHOUSE.SHARED_DIM_COMPANY_CURRENCY_MAP M
    ON M.SELLERCLOUD_CURRENCY_ID = O.ORDERCURRENCYCODE
WHERE M.CURRENCY_NAME IS NULL
GROUP BY 1, 2 ORDER BY cnt DESC;
```

### 6. Power BI matrix cells are easy to misread

Sparse matrices with many empty cells make it easy to misalign rows and columns visually. Trust the **column totals** in the Total row before trusting individual cells. When in doubt, switch to a sorted table view or cross-check against Snowflake.

### 7. Expired Power BI credentials

If a semantic model refresh fails, check for expired credentials first: **... -> Settings -> Data source credentials -> Edit credentials**. Use anonymous browser mode when logging in to Power BI web with service account credentials.

### 8. Dataset owner removed from Azure AD (incident 2026-05-20)

**Symptom:** Refresh fails with `DMTS_UserNotFoundInADGraphError`. Email notification says the dataset owner's account no longer exists in Azure AD. Scheduled refresh is auto-disabled and all stored credentials are wiped.

**Fix (step-by-step):**
1. Go to the workspace (e.g., **GEP Prod Models**) → three dots on the **Semantic model** row → **Settings**
2. Click **Take over** in the banner at the top of the settings page
3. Expand **Data source credentials** → click **Edit credentials** for each source:
   - Snowflake (x2): Basic auth, credentials from Dashlane **"Snowflake PBI Prod"** entry, Privacy = Organizational
   - Web (x1): Anonymous, Privacy = Organizational
4. Scroll to **Refresh** section → toggle **On** → set schedule → **Apply**
5. Trigger **Refresh now** to verify before waiting for the scheduled run

**Prevention:** The dataset owner should be a shared service account, not a personal account. When a person's Azure AD account is deprovisioned, their PBI dataset ownership breaks immediately.

## Future Improvements

Identified improvements to the deployment process (from source notes):
- `marketing_fct_activity.sql`: Investigate "Unknown" marketplace naming convention in `shared_dim_marketplace.sql`
- `sales_fct_cost.sql`: Check Amazon marketplace name `ILIKE` filters for correctness across all marketplaces
- `traffic_fct_activity.sql`: Review exchange rate join logic
- `shared_dim_marketplace.sql`: Investigate unknown marketplace entries
- `extract_warehouse_metadata.sql:109`: Change `CREATE OR REPLACE SECURE VIEW` to `CREATE OR REPLACE TABLE` to match other warehouse files

## See Also

- [[model-deploy-production]] — generic production model deployment checklist (PBI publish step + client user access)
- [[GEP]] -- client entity page
- [[Snowflake]] -- data warehouse tool page
- [[Power BI]] -- reporting tool page
- [[Eclipse]] -- connector platform
- [[data-pipeline-flow]] -- end-to-end data architecture
- [[star-schema-convention]] -- naming and schema conventions
- [[clients-repo]] -- primary repository structure
- [[data-share-pattern]] -- Snowflake data sharing setup
- [[environment-setup]] -- developer machine setup
- [[flight-check]] -- operational validation process
- [[ticket-breakdown-to-ship]] -- full ticket lifecycle
