# GP-200: Order of Operations & Deployment Runbook

  

> **Purpose**: This document is both a record of the GP-200 deployment (Amazon UK

> orders added to the orderline pipeline) **and** a reusable runbook for future

> Snowflake → Power BI deployments in the GEP client. The phases, commands,

> queries, and pitfalls below generalise to any change that touches the

> warehouse views and downstream model.

  

## Branch & Environment Model

  

GEP uses a three-environment promotion flow with manual Snowflake deploys at each step:

  

| Branch | Snowflake Environment | Power BI |

|---|---|---|

| `feature/...` | (none — local validation only) | (none) |

| `GEP/development` | (none directly — feature branches are merged in) | (none) |

| `GEP/user-testing` | `TEST_DG1_GEP` (the "Snowflake Test" env) | `GEP Test Models` workspace |

| `main` | `PROD_DG1_GEP` | Production workspace |

  

**Important**: Code merging to a branch does NOT automatically deploy to Snowflake

or refresh Power BI. Both are manual steps, performed in the Snowflake UI and

Power BI Service respectively. The repo is the source of truth; Snowflake and

Power BI mirror it on demand.

  

---

  

## Pre-requisites

  

Anything needed before development can start. For GP-200:

  

- [x] Obtain UK Amazon Seller Central credentials from Dashlane (named with "UK")

- [x] Fill in `GEP/eclipse/connections/amazon_seller_central_uk.json` with real credentials

      (`partner_id`, `refresh_token`, `client_identifier`, `client_secret`)

- [x] Confirm with GEP what `min_date` to use in the template (when UK orders started)

- [x] Update `min_date` in `GEP/eclipse/templates/amazon/all_orders_report_UK.json`

  

For future deployments adding a new data source: identify credentials, decide

ingestion start date, confirm any GEP-side configuration needed.

  

## Phase 1: Register Connection & Template in CosmosDB

  

For new data sources only. Existing-source changes can skip this phase.

  

- [x] Register `amazon_seller_central_uk.json` as a new connection in CosmosDB

- [x] Register `all_orders_report_UK.json` as a new work template in CosmosDB

- [x] Verify the connector accepts your `filter_marketplace` value

  - For Amazon: confirmed `"gb"` follows the ISO country code pattern used by US (`"us"`) and CA templates

  

## Phase 2: Run Connector & Validate Ingestion

  

- [x] Trigger the template run via Eclipse to pull source data

- [x] Confirm data appears in Snowflake at the expected raw table:

      `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK`

- [ ] Verify schema matches the existing equivalent table:

  ```sql

  DESCRIBE TABLE PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS;

  DESCRIBE TABLE PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK;

  ```

- [x] Spot-check the data:

  ```sql

  SELECT COUNT(*), MIN(PURCHASE_DATE), MAX(PURCHASE_DATE), COUNT(DISTINCT CURRENCY)

  FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK;

  ```

  - **Finding**: Multiple currencies present (not just GBP) — Amazon UK marketplace

    can include cross-border/Pan-European orders with USD, EUR, etc.

  - **Resolution**: See Phase 2b below

  

### Phase 2b: UK Currency Fix (added during QA)

  

**Problem discovered**: The original design joined Amazon orders to

`SHARED_DIM_COMPANY_CURRENCY_MAP` on `CURRENCY_NAME` to determine `COMPANY_ID`.

UK orders with non-GBP or NULL currencies were misattributed to Amazon US

(company 163) instead of Amazon UK (company 178).

  

**Solution**: Filter the UK leg to `WHERE SALES_CHANNEL = 'Amazon.co.uk'` and

`COALESCE(CURRENCY, 'GBP')` for NULL currency rows. Excludes cross-border EUR/SEK

rows (genuinely from other European marketplaces) and ensures all UK rows resolve

to company 178 via the existing currency join.

  

**Why this works**: Amazon UK marketplace settles in GBP for true UK orders.

The non-GBP currency rows in `CURRENT_REPORT_ALL_ORDERS_UK` are actually

Pan-European orders (Italy, Spain, Germany, France, Ireland) that should not be

in the UK pipeline at all.

  

**Full rationale**: See `GEP/_testing/gp200_currency_fix_rationale.md`

  

**Files changed:**

- `sales_dim_order_base.sql` — UK CTE leg: `WHERE SALES_CHANNEL = 'Amazon.co.uk'` + `COALESCE(CURRENCY, 'GBP')`

- `sales_fct_amazon_orderline.sql` — same CTE change

- `sales_fct_seller_cloud_orderline.sql` — same CTE change

  

## Phase 3: CSV Supplements

  

For changes that introduce a new marketplace, company, or other dimension that

needs human-readable names. Only required if `SHARED_DIM_MARKETPLACE` or

similar dim views need new entries.

  

- [x] Add "Amazon UK" row to Marketplace Name CSV

  - Location: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Name`

- [x] Add "Amazon UK" row to Marketplace Config CSV

  - Location: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Config`

- [ ] Trigger a CSV supplement refresh or wait for scheduled pull

      (CSVs flow into `PROD_DG1_GEP.SUPPLEMENT.CURRENT_*_CSV` tables)

  

## Phase 4: Local Validation Testing

  

Before opening a PR. Spin up a personal test schema, run the SQL changes against

it, validate behavior end-to-end.

  

- [x] Create a test schema (e.g., `WAREHOUSE_TEST_PAUL`) with copies of relevant

      tables / views

- [x] Run validation SQL — for GP-200 see `gp200_source_marketplace_validation.sql`

  - V1-V3: Map table has correct values

  - V4: All UK orders map to company 178

  - V5: Originally non-GBP UK orders correctly map to company 178

  - V6: Originally NULL currency UK orders resolve to GBP

  - V7: US multi-marketplace mapping preserved (CAD→166, MXN→168)

  - V8: US orders still map to company 163

  - V9: Seller Cloud mapping unaffected

  - V10: No duplicate order IDs

  

- [x] Get code review on the PR

  

- [x] Merge feature branch → `GEP/development`

  

---

  

## Phase 5: Deploy SQL Views to Snowflake Test

  

**Triggered by**: code merged to `GEP/development`.

  

Deployment is manual — run each SQL file directly against the **Snowflake Test**

environment via the Snowsight UI. There is no CI/CD pipeline; the repo is the

source of truth, Snowflake is updated by manually executing the files.

  

### 5a. Snapshot baseline counts BEFORE deploying

  

Save these results — you'll compare against them post-deploy:

  

```sql

SELECT TRANSACTION_CURRENCY_ID, COUNT(*) AS cnt

FROM WAREHOUSE.SALES_DIM_ORDER_BASE

WHERE ORDER_ID LIKE 'AMZ_%'

GROUP BY TRANSACTION_CURRENCY_ID;

```

  

Tailor the query to whatever your change touches. The point is to have a

"before" picture you can sanity-check against an "after".

  

> **⚠️ CAVEAT**: If this is the first time GP-207's `PROD_DG1_GEP` data-share

> switch is hitting Test (or any change that switches sources from local Test

> tables to a data share), expect dramatic volume changes after deploy.

> Pre-snapshot may not be apples-to-apples with post-snapshot. See "Pitfalls"

> section at the end.

  

### 5b. Run SQL files against Snowflake Test (order matters)

  

In Snowsight, with database context `TEST_DG1_GEP`, execute each file in order:

  

1. [`GEP/snowflake/warehouse/sales_dim_order_base.sql`](../snowflake/warehouse/sales_dim_order_base.sql)

   — updates `WAREHOUSE_SOURCE.SALES_DIM_ORDER_BASE` view

2. [`GEP/snowflake/warehouse/sales_fct_amazon_orderline.sql`](../snowflake/warehouse/sales_fct_amazon_orderline.sql)

   — updates `WAREHOUSE_SOURCE.SALES_FCT_AMAZON_ORDERLINE` view + creates `WAREHOUSE.SALES_FCT_AMAZON_ORDERLINE` table

3. [`GEP/snowflake/warehouse/sales_fct_seller_cloud_orderline.sql`](../snowflake/warehouse/sales_fct_seller_cloud_orderline.sql)

   — updates `WAREHOUSE_SOURCE.SALES_FCT_SELLER_CLOUD_ORDERLINE` view + creates `WAREHOUSE.SALES_FCT_SELLER_CLOUD_ORDERLINE` table

4. [`GEP/snowflake/warehouse/extract_warehouse_metadata.sql`](../snowflake/warehouse/extract_warehouse_metadata.sql)

   — updates `WAREHOUSE_SOURCE.EXTRACT_WAREHOUSE_METADATA` view

5. [`GEP/snowflake/warehouse/shared_dim_marketplace.sql`](../snowflake/warehouse/shared_dim_marketplace.sql)

   — updates `WAREHOUSE_SOURCE` + `WAREHOUSE` views (view-only, no scheduled task)

  

> **⚠️ KNOWN ISSUE**: `extract_warehouse_metadata.sql` line 109 uses

> `CREATE OR REPLACE SECURE VIEW WAREHOUSE.EXTRACT_WAREHOUSE_METADATA` but the

> hourly task `task_warehouse_extract_metadata` materializes the same name as a

> physical TABLE. Snowflake's `CREATE OR REPLACE VIEW` cannot replace a TABLE,

> so this statement **will fail** with:

> `Object 'EXTRACT_WAREHOUSE_METADATA' already exists as TABLE`.

> The view-source statement (lines 1-107) succeeds normally, and the next task

> run will re-materialize the table from the updated source view. **Ignore the

> line 109 error and move on.** Tracked as a follow-up to change line 109 to

> `CREATE OR REPLACE TABLE` to match the pattern in other warehouse files.

  

> **⚠️ POTENTIAL ISSUE — data-share gaps**: SQL files may reference objects in

> `PROD_DG1_GEP.*` schemas that were not added to the prod→test data share

> (the share is configured manually in the Snowflake prod UI by Paul, not

> defined in the repo). If a view fails with

> `Object 'PROD_DG1_GEP.SCHEMA.TABLE' does not exist or not authorized`, that

> object needs adding to the share. See "Pitfalls" section for the gaps

> discovered during GP-200 deploy.

  

## Phase 6: Materialize Physical Tables (Snowflake Test)

  

The views deployed in Phase 5 update `WAREHOUSE_SOURCE.*` (logical view layer).

Physical tables in `WAREHOUSE.*` are materialized by scheduled Snowflake tasks

(`CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT * FROM WAREHOUSE_SOURCE.X`).

  

### Option A — Wait for cron (slow)

  

- `task_warehouse_orderline_0` (root) runs at :50 past each hour (America/Vancouver)

- `task_warehouse_extract_metadata` runs at :00 each hour

- After the next cycle, physical tables reflect the new views

  

### Option B — Trigger manually (fast, recommended)

  

1. Snowsight → **Monitoring → Task History**

2. Search for `TASK_WAREHOUSE_ORDERLINE_0`

3. Click into the task → **Graph** tab

4. Click **Run** on the root node — this fires the full 10-step DAG:

   - 0. `SALES_DIM_ORDER_BASE`

   - 1. `SHARED_DIM_PRODUCT_BASE`

   - 2. `SALES_FCT_SELLER_CLOUD_ORDERLINE`

   - 3. `SALES_FCT_AMAZON_ORDERLINE`

   - 4. `SALES_FCT_COST` — depends on `AMAZON_ADS` schema

   - 5-9. (downstream tables)

5. Watch Task History — all 10 should turn green (`SUCCEEDED`)

  

`shared_dim_marketplace` is view-only and live immediately after Phase 5 — not

in the task graph.

  

### Verify task chain success

  

```sql

SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME, ERROR_MESSAGE

FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(

    SCHEDULED_TIME_RANGE_START => DATEADD(HOUR, -2, CURRENT_TIMESTAMP())

))

WHERE NAME LIKE 'TASK_WAREHOUSE_ORDERLINE%'

ORDER BY SCHEDULED_TIME DESC;

```

  

All 10 entries should be `SUCCEEDED`. If any are `FAILED`, read the

`ERROR_MESSAGE` and triage:

  

- **"Object does not exist or not authorized"** → data-share gap. Add the

  missing object to the prod→test share in Snowflake prod UI, then re-run.

- **"Failure during expansion of view ... Error in secure object"** → same

  root cause (downstream view depends on a missing share object). Fix the

  share, re-run.

- **Other errors** → read carefully, the message usually points at the line.

  

After fixing any share gaps, re-trigger from `TASK_WAREHOUSE_ORDERLINE_0`

again. Steps 0-3 will re-run (idempotent — same output) and the failed step

should now succeed.

  

## Phase 7: End-to-End Validation (Snowflake Test)

  

Run after the task chain shows all 10 steps green.

  

### 7a. Functional checks (change-specific)

  

For GP-200:

  

- [ ] UK orders appear in dim:

  ```sql

  SELECT COUNT(*), MIN(CREATE_DATE), MAX(CREATE_DATE)

  FROM WAREHOUSE.SALES_DIM_ORDER_BASE

  WHERE COMPANY_ID = 178;

  ```

  Expect ~901 (900 GBP + 1 ZZZ — see Pitfalls).

  

- [ ] UK order lines exist:

  ```sql

  SELECT COUNT(*)

  FROM WAREHOUSE.SALES_FCT_AMAZON_ORDERLINE OL

  INNER JOIN WAREHOUSE.SALES_DIM_ORDER_BASE OB ON OB.ORDER_KEY = OL.ORDER_KEY

  WHERE OB.COMPANY_ID = 178;

  ```

  

- [ ] UK appears in unified orderline:

  ```sql

  SELECT COUNT(*)

  FROM WAREHOUSE.SALES_FCT_ORDERLINE OL

  INNER JOIN WAREHOUSE.SHARED_DIM_MARKETPLACE MK ON MK.MARKETPLACE_KEY = OL.MARKETPLACE_KEY

  WHERE MK.MARKETPLACE_NAME = 'Amazon UK';

  ```

  

- [ ] Marketplace dim has Amazon UK:

  ```sql

  SELECT DISTINCT MARKETPLACE_NAME

  FROM WAREHOUSE.SHARED_DIM_MARKETPLACE

  WHERE MARKETPLACE_NAME LIKE '%UK%';

  ```

  

- [ ] Metadata entry present:

  ```sql

  SELECT * FROM WAREHOUSE.EXTRACT_WAREHOUSE_METADATA

  WHERE TABLE_NAME = 'ALL_ORDERS_UK';

  ```

  

- [ ] Cross-reference: a known UK order from Seller Cloud should be deduped

      from the Amazon base (see dedup logic at `sales_dim_order_base.sql:254-265`):

  ```sql

  SELECT TOP 5 ORDERSOURCEORDERID

  FROM PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_ORDER

  WHERE COMPANYID = 178 AND ORDERSOURCE IN (20, 4);

  

  -- Pick one of those order IDs and verify it's NOT also in the Amazon base

  SELECT * FROM WAREHOUSE.SALES_DIM_ORDER_BASE

  WHERE ORDER_SOURCE_ID = '<order_id_from_above>'

    AND ORDER_ID LIKE 'AMZ_%';

  -- Expected: 0 rows (deduped)

  ```

  

### 7b. Volume sanity check

  

Compare against the Phase 5a snapshot:

  

```sql

SELECT TRANSACTION_CURRENCY_ID, COUNT(*) AS cnt

FROM WAREHOUSE.SALES_DIM_ORDER_BASE

WHERE ORDER_ID LIKE 'AMZ_%'

GROUP BY TRANSACTION_CURRENCY_ID;

```

  

Per-company breakdown is more informative when source data has changed:

  

```sql

SELECT

    COMPANY_ID,

    COMPANY_NAME,

    CASE

        WHEN ORDER_ID LIKE 'AMZ_%' THEN 'Amazon feed'

        WHEN ORDER_ID LIKE 'SC_%' THEN 'Seller Cloud'

        ELSE 'Other'

    END AS source,

    COUNT(*) AS cnt

FROM WAREHOUSE.SALES_DIM_ORDER_BASE

WHERE COMPANY_ID IN (163, 166, 168, 174, 178)

GROUP BY 1, 2, 3

ORDER BY 1, 3;

```

  

> **⚠️ CAVEAT — Amazon vs Seller Cloud dedup**: Amazon orders that also exist

> in Seller Cloud are filtered out of the Amazon leg (Seller Cloud is the

> system of record). See `sales_dim_order_base.sql:254-265`. As Seller Cloud

> data grows, more Amazon orders get deduped, so the `AMZ_*` count naturally

> shrinks. This is **not** a bug — total per-company volume (AMZ + SC combined)

> is what matters for stakeholder reporting.

  

### 7c. Currency mapping check

  

```sql

SELECT

    COMPANY_ID,

    COMPANY_NAME,

    TRANSACTION_CURRENCY_ID,

    COUNT(*) AS cnt

FROM WAREHOUSE.SALES_DIM_ORDER_BASE

WHERE COMPANY_ID IN (163, 166, 168, 174, 178)

GROUP BY 1, 2, 3

ORDER BY 1, 4 DESC;

```

  

Expected: each Amazon company maps to its expected currency (USD/CAD/MXN/BRL/GBP).

Small `ZZZ` rows indicate unmapped SellerCloud currency codes — investigate but

don't necessarily block.

  

---

  

## Phase 8: Promote to User Testing (PR-based)

  

Once Phase 7 validation passes:

  

- [ ] Open PR: `GEP/development` → `GEP/user-testing`

- [ ] Tag a reviewer (typically the same person who reviewed your feature PR)

- [ ] Once approved, merge the PR

  

After merge, **the user-testing Snowflake environment does NOT auto-deploy**.

Repeat Phases 5-7 against `TEST_DG1_GEP` (Snowflake Test) — wait, actually

in this client setup, `GEP/user-testing` and "Snowflake Test" point at the

same Snowflake environment. You're done with Snowflake at this point.

  

> **NOTE**: Confirm with Steven whether your specific change requires any

> separate user-testing Snowflake deploy. For GP-200, no — the Test environment

> is shared.

  

## Phase 9: Refresh & Validate Power BI Test Model

  

Snowflake changes are only half the story — the client primarily interacts with

the Power BI model, so changes must be verified there before handoff.

  

### 9a. Trigger refresh

  

1. Go to `app.powerbi.com`

2. Workspace: **GEP Test Models**

3. Find the **Semantic model** row (NOT the Report row)

4. Click **⋯** (More options) → **Refresh now**

5. Watch **⋯ → Refresh history** for completion

   - Expect anywhere from a few minutes to 30+ minutes depending on data volume

   - First refresh after a data-share switch (e.g., GP-207) will be slower

  

> **CAVEAT**: If credentials have expired, refresh will fail. Fix via

> **⋯ → Settings → Data source credentials → Edit credentials**.

  

### 9b. Smoke-test in Explore (web)

  

You don't need Power BI Desktop for validation — use the **Explore Data Model**

feature directly in Service.

  

1. On the Semantic model page, click **Explore** in the top toolbar

2. Build a Marketplace × Sales matrix:

   - From **Marketplace** table, drag **Marketplace Name** to the visual

   - From **Marketplace Measures** (or wherever your sales measure lives),

     drag a measure like **Actual - Sales - Gross**

   - Important: use a **measure**, not a raw column. Raw `Order ID`

     count from the Order table will give the same number for every

     marketplace because Order is not directly related to Marketplace

     (the relationship goes Marketplace → Order Line → Order).

3. Add **Transaction Currency** as a column to verify currency attribution

  

### 9c. Validation checklist

  

For GP-200 (adapt for your change):

  

- [ ] **Amazon UK appears** in marketplace slicer

- [ ] **Amazon UK sales are in GBP only** (no leakage into other currency columns)

- [ ] **GBP column total = Amazon UK row total** (only UK contributes to GBP)

- [ ] **UK orders span multiple weeks** (add Week Name from Date hierarchy as

      a row, filter to Amazon UK — should see distribution, not a single dump)

- [ ] **Other Amazon marketplaces (US/CA/MX/BR) are present and grew or stayed

      stable** — do NOT expect identical numbers if a data-share switch

      landed alongside this deploy (they will be larger)

- [ ] **No new blank/Unknown marketplace rows** unexpectedly

  

> **⚠️ POWER BI MATRIX READING**: It's easy to misread cell→column alignment in

> sparse matrices. If totals look weird, **trust the column totals** in the

> Total row before trusting individual cells. When in doubt, cross-check

> against the Snowflake `SALES_DIM_ORDER_BASE` query in Phase 7c.

  

### 9d. Notify stakeholders

  

- [ ] Notify GEP that the change is available in the test model for UAT

- [ ] Include any relevant caveats from the Pitfalls section that GEP should

      be aware of (e.g., if a data-share switch landed alongside your change,

      mention that volumes have stepped up)

  

---

  

## Phase 10: Cleanup

  

- [ ] Drop personal test schema:

      `DROP SCHEMA IF EXISTS WAREHOUSE_TEST_PAUL CASCADE;`

- [ ] Archive any one-off testing/scratch SQL files in `GEP/_testing/`

      (this `gp200_order_of_operations.md` doc is intentionally **kept** for

      future reference — do NOT delete)

- [ ] Ensure `GP-200-plan.md` (or any task-tracking scratch file) is not

      committed (already gitignored / unstaged)

- [ ] File any follow-up tickets identified during deploy (see Pitfalls section)

  

---

  

## Pitfalls Encountered During GP-200 Deploy

  

This section is the most important part for future reference. Each entry below

cost real time during GP-200 and is likely to recur on future deploys.

  

### Pitfall 1: Data-share gaps in Snowflake Test

  

**What happened**: SQL files reference `PROD_DG1_GEP.*` schemas via an external

data share configured manually in the Snowflake **prod** UI (not defined in

the repo). Multiple objects were missing from the share and only surfaced as

errors when the views/tasks tried to compile against them.

  

**Symptoms**:

- `SQL compilation error: Object 'PROD_DG1_GEP.X.Y' does not exist or not authorized`

- Task chain failure: `Failure during expansion of view 'X': Error in secure object`

  

**Objects discovered missing** (added to the share during GP-200 deploy):

- `PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_PURCHASEITEM` — needed by

  `extract_warehouse_metadata.sql`

- `PROD_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`

  — needed by `sales_fct_cost.sql` (caused task step 4 to fail)

  

**For future deploys**: Before triggering the task chain, consider running a

dry-run against the share by SELECT'ing from each `PROD_DG1_GEP.*` object the

view chain references. Or, audit the share against every `PROD_DG1_GEP.*`

reference in `GEP/snowflake/warehouse/**/*.sql` once and for all.

  

**Fix**: Add the missing object to the share in the Snowflake **prod** UI,

then re-trigger the task / re-run the SQL.

  

### Pitfall 2: `extract_warehouse_metadata.sql` line 109 view-vs-table conflict

  

**What happened**: The file's last statement (line 109) is

`CREATE OR REPLACE SECURE VIEW WAREHOUSE.EXTRACT_WAREHOUSE_METADATA AS ...`.

But the hourly `task_warehouse_extract_metadata` materializes the same name as

a physical TABLE. Snowflake cannot use `CREATE OR REPLACE VIEW` to replace a

TABLE.

  

**Symptom**: `SQL compilation error: Object 'EXTRACT_WAREHOUSE_METADATA' already exists as TABLE`

  

**This is harmless** — the source view (lines 1-107) succeeds and the next

task run rebuilds the table from the new source. Ignore line 109's error.

  

**Fix (long-term)**: Change line 109 to `CREATE OR REPLACE TABLE` to match

the pattern in other warehouse SQL files. Tracked as a follow-up ticket.

  

### Pitfall 3: Data-share switch causes step-change in volume

  

**What happened**: GP-207 (separate ticket) switched all `PROD_DG1_GEP.*`

references from previously-local Test source schemas to a prod data share.

GP-200 was the first deploy after GP-207 landed in Test, so when its task

chain ran, the Snowflake tables were re-materialized against the prod share's

much larger dataset. Pre-deploy snapshot showed 622K Amazon orders; post-deploy

showed 25K `AMZ_*` orders + 2.52M `SC_*` orders (≈ 4x total growth).

  

**Why the `AMZ_*` count specifically dropped**: The dedup logic at

`sales_dim_order_base.sql:254-265` filters out Amazon orders that also exist

in Seller Cloud (SC is the system of record when both exist). With the prod

share's full SC dataset, far more Amazon orders matched and were correctly

attributed to SC instead of Amazon. **No data was lost** — it was reattributed.

  

**For future deploys**: When pre/post snapshot volumes look very different,

diagnose by:

1. Check if the materialization completed (`INFORMATION_SCHEMA.TASK_HISTORY`)

2. Compare the live view against the materialized table (rules out task issue)

3. Check raw source row counts (`SELECT COUNT(*) FROM PROD_DG1_GEP.X.Y`)

4. Use the per-company × source breakdown from Phase 7b — if AMZ + SC totals

   per company grew or stayed stable, the change is fine

  

**Stakeholder communication**: Always flag step-changes to GEP. They will

otherwise wonder why "Amazon US sales went 4x overnight" or "Amazon feed

shrank 95%."

  

### Pitfall 4: Power BI relationship structure (Order is not directly related to Marketplace)

  

**What happened**: When validating in Power BI Explore, dragging

`Order ID (Count)` against `Marketplace Name` returned the **same total** for

every marketplace. Looked like a major bug — was actually correct schema.

  

**Why**: `SALES_DIM_ORDER_BASE` does not have `MARKETPLACE_KEY`. Marketplace is

joined to the orderline tables (`SALES_FCT_*_ORDERLINE`), not the order dim

directly. So Power BI cannot filter Orders by Marketplace — no relationship

to follow.

  

**Fix**: Use a measure from **Marketplace Measures** (or any measure that

internally aggregates over Order Line). For raw counts, use a column from the

Order Line table instead of Order.

  

### Pitfall 5: Missing EUR mapping in `SHARED_DIM_COMPANY_CURRENCY_MAP`

  

**What happened**: 1 UK order out of 901 surfaced as `TRANSACTION_CURRENCY_ID = 'ZZZ'`

(unmapped). Investigation revealed it had `ORDERCURRENCYCODE = 3` in SellerCloud,

which is missing from the company-currency map. Further investigation revealed

SellerCloud currency code 3 = EUR, and **all** orders from European Amazon

companies (181 France, 182 Germany, 184 Italy, 187 Spain) — 23 orders total —

were also showing as `ZZZ`.

  

**Not GP-200's fault** — pre-existing data quality gap exposed by the

GP-207 data-share switch bringing in fuller European data. Tracked as a

separate ticket to add EUR mappings.

  

**For future deploys**: When a new currency or company is involved, check the

`SHARED_DIM_COMPANY_CURRENCY_MAP` in `GEP/snowflake/warehouse/shared_dim_currency_company_map.sql`

covers it. Currently mapped:

  

| Company | SC Code | Currency |

|---|---|---|

| 163 (Amazon US) | 0 | USD |

| 166 (Amazon Canada) | 4 | CAD |

| 168 (Amazon Mexico) | 6 | MXN |

| 174 (Amazon Brazil) | 31 | BRL |

| 178 (Amazon UK) | 1 | GBP |

  

Diagnostic for unmapped currencies:

```sql

-- Which companies have orders with currency codes not in the map?

SELECT

    O.COMPANYID,

    O.ORDERCURRENCYCODE,

    COUNT(*) AS cnt

FROM PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_ORDER O

LEFT JOIN WAREHOUSE.SHARED_DIM_COMPANY_CURRENCY_MAP M

    ON M.SELLERCLOUD_CURRENCY_ID = O.ORDERCURRENCYCODE

WHERE M.CURRENCY_NAME IS NULL

GROUP BY 1, 2

ORDER BY cnt DESC;

```

  

### Pitfall 6: Power BI matrix cells are easy to misread

  

**What happened**: When inspecting a sparse matrix (Marketplace × Currency)

with most cells empty, it's easy to misalign rows/columns visually. I

mistakenly flagged the matrix as showing currency mismatches that didn't

exist — the data was correct, my reading was off.

  

**Fix**: Always trust the **column totals** in the Total row over individual

cell positions. When in doubt, switch to a sorted table view instead of a

matrix, or cross-check against Snowflake using a per-company × per-currency

query.

  

---

  

## Follow-up Tickets Filed from This Deploy

  

- **Currency mapping gap (EUR / SellerCloud code 3)** — add EUR mapping for

  companies 181 (France), 182 (Germany), 184 (Italy), 187 (Spain) and

  investigate the 1 anomalous UK order with EUR currency. Filed: [ticket].

- **`extract_warehouse_metadata.sql:109` view→table fix** — change to

  `CREATE OR REPLACE TABLE` to match other warehouse files. (To be filed.)

- **GP-207 data-share completeness audit** — `PURCHASEITEM` and `AMAZON_ADS`

  were missing from the prod→test share; audit for any remaining gaps before

  the next deploy. (To be filed.)