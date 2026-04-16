## Context

GEP has delivered a sample 100-row inventory export covering FBA availability buckets, GEP2 quantities, AWD measures, kit quantities, and a CaptureDate timestamp. 

The goal is to make this feed queryable inside the managed GEP Snowflake environment, building a new fact table and ingestion pathway from scratch.

  

**Key framing:** The existing inventory-related files (`inventory_fct_balance.sql`, `inventory_fct_historical_balance.sql`, `extract_inventory_current.sql`) were built previously but are **not in active use by GEP**. This is a greenfield inventory implementation. The new fact table becomes GEP's primary inventory model. Prior inventory files are referenced only for reusable SQL patterns.

  

---


## What the Previous Inventory Model Did (Research)


The existing `inventory_fct_balance.sql` pulled from **three sources:**

| Sample CSV Column                     | Likely Old Source Equivalent                 | Notes                                    |
| ------------------------------------- | -------------------------------------------- | ---------------------------------------- |
| GEP2 Available Qty                    | `INVENTORYAVAILABLEQTY` (Sellercloud GEP2)   | Same underlying data                     |
| On Order GEP2 Qty                     | Purchasing fact (not in old inventory model) | Net-new                                  |
| Total US FBA Available                | `AFN_FULFILLABLE_QUANTITY` (Amazon FBA)      | Same data, possibly pre-aggregated       |
| Total Non Sellable                    | `AFN_UNSELLABLE_QUANTITY` (Amazon FBA)       | Same data                                |
| US FBA Reserved (Orders/Prcss/Trnsfr) | `AFN_RESERVED_QUANTITY` (Amazon FBA)         | More granular breakdown than old model   |
| CA FBA Available                      | Not in old model                             | Net-new                                  |
| AWD InT / AWD Available               | Not in old model                             | Net-new (Amazon Warehouse Distribution?) |
| Kit Qty columns                       | Not in old model                             | Net-new                                  |
| Direct FBA / SCC FBA columns          | Not clearly in old model                     | May be new fulfillment channel breakdown |
  

**How the data arrived:**  

Both Sellercloud and Amazon sources are already live in `PROD_DG1_GEP.*` — they flow into Snowflake through ALDC's existing data pipelines (not a data share, not a file stage). The inventory model was a view on top of those already-present raw tables.

  

**Why the old model was shelved:**  

The client changed their mind and chose to manage their own inventory data rather than have ALDC implement it. Now they want us to implement it, meaning some of the prior SQL work may be reusable. Confirm with the team engineer who worked on the original implementation for full context.

  

**Important caveat — pipeline health:**  

We don't know whether the Sellercloud and Amazon feeds in `PROD_DG1_GEP.*` are still actively refreshing today or if they went stale when the original model was shelved. If they went stale, "rebuild from existing sources" (Path C) is not viable without first restoring those pipelines. This must be confirmed before any Path C work begins.

  

---

## How the New Navira/GEP Feed Compares

Looking at the sample CSV columns against the old sources:


| Sample CSV Column                     | Likely Old Source Equivalent                 | Notes                                    |
| ------------------------------------- | -------------------------------------------- | ---------------------------------------- |
| GEP2 Available Qty                    | `INVENTORYAVAILABLEQTY` (Sellercloud GEP2)   | Same underlying data                     |
| On Order GEP2 Qty                     | Purchasing fact (not in old inventory model) | Net-new                                  |
| Total US FBA Available                | `AFN_FULFILLABLE_QUANTITY` (Amazon FBA)      | Same data, possibly pre-aggregated       |
| Total Non Sellable                    | `AFN_UNSELLABLE_QUANTITY` (Amazon FBA)       | Same data                                |
| US FBA Reserved (Orders/Prcss/Trnsfr) | `AFN_RESERVED_QUANTITY` (Amazon FBA)         | More granular breakdown than old model   |
| CA FBA Available                      | Not in old model                             | Net-new                                  |
| AWD InT / AWD Available               | Not in old model                             | Net-new (Amazon Warehouse Distribution?) |
| Kit Qty columns                       | Not in old model                             | Net-new                                  |
| Direct FBA / SCC FBA columns          | Not clearly in old model                     | May be new fulfillment channel breakdown |

  

**Key insight:** The feed may be pulling from the **same underlying systems** (Sellercloud + Amazon) but delivered as a pre-aggregated snapshot rather than raw source data. 

This matters because:

1. We can use the old `inventory_fct_balance` SQL to **cross-validate** the new feed during QA

2. **If it IS the same data, the question becomes whether we really need a data share — or whether ALDC can reconstruct this from what's already in `PROD_DG1_GEP.*`**

3. Net-new columns (AWD, kits, CA FBA, On Order GEP2) would be the true incremental value

  

---

  

## Previous vs. This Iteration — Decision Checklist for Client

  

The following questions are framed as comparisons between the previous implementation and the current ask. Each one should be answered before implementation begins.

  

---


**1. Data Source**

*Previously:* GEP2 inventory came from Sellercloud SQL (`PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL`). FBA inventory came from Amazon Seller Central reports (`PROD_DG1_GEP.AMAZON.CURRENT_REPORT_FBA_INVENTORY`). Both were already live in ALDC's managed Snowflake environment — no data share or file transfer was needed.

  

*This time:* The sample CSV appears to contain similar data (GEP2 quantities, FBA quantities). It could be sourced from the same systems.

  

> **Question:** Is the inventory feed pulling from the same Sellercloud and Amazon sources as before — i.e., data already flowing through ALDC's pipelines? If yes, we can build this without a new ingestion pathway and extend the model with the net-new columns. If no, where is the data coming from and how should it be delivered?

  

---


**2. Ingestion Pathway**

*Previously:* No data share or file stage — source data arrived via ALDC's existing Sellercloud and Amazon connectors directly into `PROD_DG1_GEP.*`.

*This time:* If the data source is the same, no new ingestion is needed. If it's a new source, a Snowflake data share or interim file stage is required.


> **Question:** Do we want to use the same ingestion pathway as before (existing pipelines in PROD_DG1_GEP.*), or is this a new external feed that requires a data share or file delivery?

  

---

  

**3. Grain / Primary Key**


*Previously:* Grain was `PRODUCT_ID` (Sellercloud internal ID) × current snapshot — one row per product, always reflecting the latest available data. MASTER_SKU was resolved via a join to `SHARED_DIM_PRODUCT`, not used as the primary key.


*This time:* The sample CSV uses `MASTER_SKU` as the lead key and includes `CaptureDate` and `Iteration`, suggesting a time-series / snapshot approach rather than a single current row.


> **Question:** Do we want the same grain as before (one current row per product, keyed by PRODUCT_ID), or do we want a time-series grain (one row per MASTER_SKU × CaptureDate or × Iteration)? The time-series approach is recommended as it enables trend analysis and DOH calculations.

  

---


**4. Snapshot Type (Historical vs. Current-Only)**


*Previously:* Current-only. The model was built to reflect the latest inventory snapshot — `QUALIFY RANK() = 1` on the most recent date. A historical version (`inventory_fct_historical_balance.sql`) was attempted but abandoned and is not in use.


*This time:* The presence of `CaptureDate` and `Iteration` in the feed suggests the data is designed to be captured over time. Append-only is recommended.

  

> **Question:** Do we want to store only the latest snapshot (same as before), or do we want to retain full history (append-only, one row per snapshot)? Recommendation: append-only with a separate "current" extract view — more useful and avoids having to re-introduce a historical model later.

  

---


**5. Cost & Retail Price Extensions**


*Previously:* Yes — the fact table included `qty × LAST_COST` and `qty × LAST_RETAIL_PRICE` extended cost and retail columns for every inventory bucket. Costs came from Sellercloud (`INVENTORY.COST`, `INVENTORY.SITEPRICE`).

  

*This time:* The sample CSV contains no cost or price data — only quantities.

  

> **Question:** Do we want cost and retail price extensions in the new model (same as before), or quantities only for now? If costs are desired, what is the source — Sellercloud (same as before), or a different system?

  

---


**6. Velocity (Days on Hand)**


*Previously:* Yes — the fact included 7-day and 30-day rolling average velocity calculations derived from `SALES_FCT_ORDERLINE`. These supported DOH calculations in downstream reporting
  

*This time:* Not included in the sample feed. `SALES_FCT_ORDERLINE` is still active and could be used.


> **Question:** Do we want velocity (7-day and 30-day rolling average from sales) included in the new inventory model (same as before), or should this be deferred to a consumer/reporting layer?

  

---

  
**7. Warehouse Scope**


*Previously:* Only two warehouses: GEP2 (self-managed) and GEP2-Returns_Unsellable. No Canada, AWD, or kit tracking.


*This time:* The sample CSV includes CA FBA, AWD columns, and kit quantities — expanding beyond the old model's scope.


> **Question:** The new feed includes net-new warehouse/program scopes (Canada FBA, AWD, kits). Are all of these active and expected to have meaningful data in production, or are some placeholder columns for future use?

  

---


**8. Extract / Consumer View**


*Previously:* `extract_inventory_current.sql` joined the inventory fact to `SHARED_DIM_PRODUCT` (for product metadata) and `PURCHASING_FCT_BALANCE` (for on-order quantity). This was the public-facing view.
 

*This time:* Same pattern is appropriate. `PURCHASING_FCT_BALANCE` is still active and on-order qty is included in the sample CSV (`On Order GEP2 Qty`) — we should confirm whether we pull it from the fact or recalculate it from the purchasing fact.


> **Question:** The sample includes `On Order GEP2 Qty` directly in the feed. Previously, on-order quantity was pulled from `PURCHASING_FCT_BALANCE` and joined at the extract layer. Do we want to use the value from the feed directly, or continue joining purchasing data at the extract layer for consistency?

  

---


## Go/No-Go Milestone: Grain Decision
 

**Do not build Layer 2 or Layer 3 until the grain is confirmed.**

| Option | Grain                    | Implication                                                        |
| ------ | ------------------------ | ------------------------------------------------------------------ |
| A      | MASTER_SKU × CaptureDate | One snapshot per SKU per day; Iteration is metadata only           |
| B      | MASTER_SKU × Iteration   | One snapshot per SKU per batch run; multiple rows per day possible |

**Recommendation:** Hybrid design regardless of answer.

- Append-only physical table (retains all history)

- `extract_inventory_current.sql` view filters to `MAX(CAPTURE_TIMESTAMP)` for latest snapshot
  

This avoids a retool if GEP later wants trend/DOH analysis.

  
---


## Open Questions for Client

  
### Same Source or New Source? (Core Question)

1. **Is the inventory feed pulling from the same systems the old model used?**

   - Old model pulled GEP2 quantities from Sellercloud (`CURRENT_MAIN_INVENTORY_PANDL`) and FBA quantities from Amazon reports (`CURRENT_REPORT_FBA_INVENTORY`) — both already live in ALDC's Snowflake environment

   - **If yes (same source):** We may not need a data share for the base inventory columns — but we must also confirm: (a) the Sellercloud and Amazon pipelines in `PROD_DG1_GEP.*` are still actively refreshing (not stale), and (b) we have upstream sources for the net-new columns (AWD, CA FBA, kits, On Order GEP2) that are not in the legacy model. Even if the base data exists, the new feed may still be required to fill those gaps.

   - **If no (new source/system):** Data share or file stage is the right path. We need account details, role, refresh cadence.

  

### Delivery Mechanism & Data Contract (if new source)

2. Data share confirmed or TBD? If yes:

   - GEP Snowflake account identifier + role (ALDC will assign USAGE on database + SELECT on share)

   - Table/view name being shared

   - Refresh cadence

   - **Timezone of CaptureDate** — UTC, warehouse-local, or other?

   - Historical backfill scope + who is responsible for it

3. **Late/out-of-order arrivals** — If Iteration 42 arrives after Iteration 43, do we re-process? SLA for corrections?

4. **File stage fallback** — If data share not ready: who uploads CSV, how often, row-count + checksum validation on delivery?

  

### Data Semantics

5. **Grain** — Is `MASTER_SKU + CaptureDate` correct, or does Iteration need to be part of the key?

6. **Iteration field** — Retry counter, forecast version, or business-facing concept? How does it increment?

7. **Data dictionary** — Definitions for:

   - AWD columns — what program/warehouse?

   - Kit columns — what lifecycle stages?

   - FBA rollup vs. detail (Total US FBA Available vs. US FBA Available; Total Non Sellable vs. Non Sellable Qty)

   - Direct FBA vs. SCC FBA vs. US FBA breakdown

5. **EndAggregatedColumns** — New aggregated columns may be added. Will they be before or after this marker? Columns after it?
	1. This doesn't matter - this was just included in the sample csv so the reader can identify the columns to be aggregated.

7. **Negative values** — Reserved columns show negatives. Valid adjustments or data quality issue? Acceptable range?

8. **Sparse columns** — CA FBA, AWD, kits all zero in sample. Will populate or placeholders?

  

### Reporting & Consumer Use Cases

11. **Initial consumer scenarios** — First 1-2 reports or decisions this data drives (DOH, coverage, AWD replenishment?). Determines measure priority and whether Layer 2 needs derived fields.

  

---

  
## Assumptions (Pending Validation)

  
| Assumption                                                              | Risk                                | Validation                                          |
| ----------------------------------------------------------------------- | ----------------------------------- | --------------------------------------------------- |
| MASTER_SKU joins cleanly to `SHARED_DIM_PRODUCT.MASTER_SKU`             | High                                | Stage 100-row sample + run join; log unmatched SKUs |
| CaptureDate is UTC                                                      | Medium                              | Confirm with GEP                                    |
| EndAggregatedColumns is a system marker (exclude)                       | Low — confirmed by email            | Confirm no data columns exist after it              |
| Grain is MASTER_SKU × CaptureDate                                       | High                                | Go/no-go milestone                                  |
| Negative reserved values are valid corrections                          | Medium                              | Confirm acceptable range with GEP                   |
| Feed is a new data source (not reconstructible from existing pipelines) | High — drives ingestion path choice | Resolved by Question 1 above                        |
  

---

  

## Recommended Architecture


### Landing Zone Naming

Mirrors existing pattern (`PROD_DG1_GEP.AMAZON.*`, `PROD_DG1_GEP.SELLERCLOUD_SQL.*`):

- Data share path: `PROD_DG1_GEP.GEP_INVENTORY.*` (confirm name)

- File stage fallback: `PROD_DG1_GEP.GEP_INVENTORY.INVENTORY_RAW`

  

### Layer 1: Raw Ingestion

  
**Path A — Snowflake Data Share (if new source):**

- GEP shares table into `PROD_DG1_GEP.GEP_INVENTORY.*`

- Grants: `USAGE ON DATABASE`, `SELECT ON SHARE`

- Owner: GEP provisions; ALDC accepts and maps into account

  

**Path B — File Stage (interim fallback):**

- Transport: GEP delivers CSV (confirm: SFTP, manual drop, scheduled export?)

- Validation on receipt: row count + SHA256 checksum against manifest

- Load: `COPY INTO` using named file format (`TYPE = CSV, SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"'` — MASTER_SKU has spaces/special chars)

- Migration: swap source to data share with no Layer 2/3 changes

  

**Path C — Reconstruct from existing pipelines (if same source as old model):**

- Prerequisite: confirm `PROD_DG1_GEP.SELLERCLOUD_SQL.*` and `PROD_DG1_GEP.AMAZON.*` feeds are still actively refreshing (not stale from when the old model was shelved)

- If pipelines are healthy: build `INVENTORY_FCT_BALANCE` as a new view on those existing tables — covers the legacy columns (GEP2 qty, FBA qty, unsellable)

- **Coverage gap:** AWD, CA FBA, kit quantities, and On Order GEP2 are net-new and have no identified upstream table in the existing pipelines. Even if Path C is viable for the base columns, a partial data share or additional source may still be needed for these columns. Identify upstream tables for each before committing to Path C.

- Validate reconstructed columns against GEP's sample CSV during QA

  

### Layer 2: Source View (Transform)


**File:** `GEP/snowflake/warehouse/inventory_fct_balance.sql` (greenfield — replaces unused file; see archival note)


`CREATE OR REPLACE SECURE VIEW WAREHOUSE_SOURCE.INVENTORY_FCT_BALANCE`


**Transforms:**

- `PRODUCT_KEY = SHA2(PRODUCT_ID)` via join to `SHARED_DIM_PRODUCT` on `MASTER_SKU`

- `BALANCE_DATE = CAST(CaptureDate AS DATE)`, `CAPTURE_TIMESTAMP = CaptureDate::TIMESTAMP`

- `BALANCE_DATE_KEY = SHA2(BALANCE_DATE::VARCHAR)` (follow sales_fct_orderline pattern)

- `ITERATION` as INT metadata

- Exclude `EndAggregatedColumns`

- All QTY columns: `COALESCE(col, 0)::INT`

- Rename to snake_case `*_QTY` convention (see mapping)

- Header comment: document column set + source Iteration number + date (version marker for future schema changes)

  

**Mandatory fields:** MASTER_SKU, BALANCE_DATE, ITERATION (must not be null; alert on null rows)


**Derived fields (Layer 2):**

- `TOTAL_ON_HAND_QTY = GEP2_AVAILABLE_QTY + US_FBA_AVAILABLE_QTY + CA_FBA_AVAILABLE_QTY + AWD_AVAILABLE_QTY`

- DOH deferred to consumer model (needs velocity source)

- Cost extensions deferred until cost data is available

  

### Layer 3: Materialized Fact (Append-Only)

  

```sql

-- Backfill / initial load

CREATE OR REPLACE TABLE WAREHOUSE.INVENTORY_FCT_BALANCE

AS SELECT * FROM WAREHOUSE_SOURCE.INVENTORY_FCT_BALANCE;

  

-- Incremental scheduled task

INSERT INTO WAREHOUSE.INVENTORY_FCT_BALANCE

SELECT * FROM WAREHOUSE_SOURCE.INVENTORY_FCT_BALANCE

WHERE CAPTURE_TIMESTAMP > (SELECT MAX(CAPTURE_TIMESTAMP) FROM WAREHOUSE.INVENTORY_FCT_BALANCE);

```

  

**Load audit table:** `WAREHOUSE.INVENTORY_LOAD_AUDIT`

Columns: `LOAD_TIMESTAMP`, `SOURCE_ITERATION`, `SOURCE_CAPTURE_TIMESTAMP`, `ROWS_LOADED`, `ROWS_REJECTED`, `IS_OUT_OF_ORDER`


Late/out-of-order rows: inserted as valid history, flagged `IS_OUT_OF_ORDER = TRUE` in audit log.

  
### Layer 4: Public Extract View


**File:** `GEP/snowflake/warehouse/extract_inventory_current.sql`


Latest snapshot + product dim join, filtered to `MAX(CAPTURE_TIMESTAMP)`.

  

---

  
## Column Mapping


| Source Column          | Target Column                  | Type      | Nullable | Notes                                                 |
| ---------------------- | ------------------------------ | --------- | -------- | ----------------------------------------------------- |
| MASTER_SKU             | MASTER_SKU                     | VARCHAR   | No       | Join key                                              |
| (derived)              | PRODUCT_KEY                    | VARCHAR   | No       | SHA2(PRODUCT_ID)                                      |
| CaptureDate (date)     | BALANCE_DATE                   | DATE      | No       |                                                       |
| CaptureDate (full)     | CAPTURE_TIMESTAMP              | TIMESTAMP | No       |                                                       |
| Iteration              | ITERATION                      | INT       | No       | Must be > 0                                           |
| Total US FBA Available | TOTAL_US_FBA_AVAILABLE_QTY     | INT       | No       | Rollup — confirm = sum of detail cols                 |
| Total US FBA Working   | TOTAL_US_FBA_WORKING_QTY       | INT       | No       | Rollup                                                |
| Total US FBA InTransit | TOTAL_US_FBA_INTRANSIT_QTY     | INT       | No       | Rollup                                                |
| Total Non Sellable     | TOTAL_NON_SELLABLE_QTY         | INT       | No       | Rollup — confirm vs. NON_SELLABLE_QTY                 |
| Non Sellable Qty       | NON_SELLABLE_QTY               | INT       | No       | Detail subset                                         |
| On Order GEP2 Qty      | ON_ORDER_GEP2_QTY              | INT       | No       | Net-new (not in old model)                            |
| GEP2 Available Qty     | GEP2_AVAILABLE_QTY             | INT       | No       | Was `INVENTORYAVAILABLEQTY` in old Sellercloud source |
| US FBA Available       | US_FBA_AVAILABLE_QTY           | INT       | No       | Was `AFN_FULFILLABLE_QUANTITY`                        |
| US FBA InT Working     | US_FBA_INTRANSIT_WORKING_QTY   | INT       | No       |                                                       |
| Direct FBA Working     | DIRECT_FBA_WORKING_QTY         | INT       | No       |                                                       |
| SCC FBA Working        | SCC_FBA_WORKING_QTY            | INT       | No       | SCC = Seller Cloud Commerce (assumed)                 |
| US FBA InT Shipped     | US_FBA_INTRANSIT_SHIPPED_QTY   | INT       | No       |                                                       |
| Direct FBA Shipped     | DIRECT_FBA_SHIPPED_QTY         | INT       | No       |                                                       |
| SCC FBA Shipped        | SCC_FBA_SHIPPED_QTY            | INT       | No       |                                                       |
| US FBA Rsrvd Orders    | US_FBA_RESERVED_ORDERS_QTY     | INT       | No       | **Negatives observed — flag until policy confirmed**  |
| US FBA Rsrvd Prcss     | US_FBA_RESERVED_PROCESSING_QTY | INT       | No       | **Negatives observed — flag**                         |
| US FBA Rsrvd Trnsfr    | US_FBA_RESERVED_TRANSFER_QTY   | INT       | No       |                                                       |
| CA FBA Available       | CA_FBA_AVAILABLE_QTY           | INT       | No       | Net-new; sparse in sample                             |
| AWD InT                | AWD_INTRANSIT_QTY              | INT       | No       | Net-new; definition TBD                               |
| AWD Available          | AWD_AVAILABLE_QTY              | INT       | No       | Net-new; definition TBD                               |
| Pending Kit Qty        | PENDING_KIT_QTY                | INT       | No       | Net-new; all zero in sample                           |
| Working Kit Qty        | WORKING_KIT_QTY                | INT       | No       | Net-new; all zero in sample                           |
| FBM Offered Kit Qty    | FBM_OFFERED_KIT_QTY            | INT       | No       | Net-new; all zero in sample                           |


  

---


## ### Files to Create
| File                                                    | Purpose                                                    |
| ------------------------------------------------------- | ---------------------------------------------------------- |
| `GEP/snowflake/warehouse/inventory_fct_balance.sql`     | Source view + scheduled task (greenfield)                  |
| `GEP/snowflake/warehouse/extract_inventory_current.sql` | Latest-snapshot public extract                             |
| `notes/projects/GP-208/design.md`                       | Column dictionary + grain/design decisions (client-facing) |
| Optional: stage DDL + file format DDL                   | If file stage path is needed                               |

### Files to Reference (Do Not Modify)
| File                                                          | Why                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `GEP/snowflake/warehouse/inventory_fct_balance.sql` (current) | Prior unused work—use for QA cross-checks and SQL patterns (COALESCE, joins) |
| `GEP/snowflake/warehouse/shared_dim_product_base.sql`         | MASTER_SKU → PRODUCT_KEY join (active)                                       |
| `GEP/snowflake/warehouse/sales_fct_orderline.sql`             | Convention reference (secure view, COALESCE, DIV0, scheduled task)           |
| `GEP/snowflake/data_share/warehouse.sql`                      | Data share exposure pattern                                                  |

**Archival decision:** Overwrite the unused `inventory_fct_balance.sql` with the new implementation and note that in the commit message; Git history retains the prior version.

  

---

  

## QA Checklist (with Thresholds)


| Check                          | Method                                                         | Threshold / Alert                                                                   |
| ------------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Row count vs. source           | COUNT(*) source vs. fact                                       | Must match exactly; reject load if delta > 0                                        |
| MASTER_SKU join rate           | COUNT unmatched / total                                        | Alert if < 95%; log unmatched SKUs to audit table                                   |
| Null rate — mandatory fields   | COUNT(NULL) per col                                            | 0 for MASTER_SKU, BALANCE_DATE, ITERATION                                           |
| Null rate — quantity columns   | COUNT(NULL) per col                                            | 0 post-COALESCE; alert if any nulls pass through                                    |
| Negative value audit           | COUNT(col < 0) per reserved col                                | Log; do not reject — flag until GEP confirms policy                                 |
| Duplicate detection            | COUNT(*) vs. COUNT(DISTINCT MASTER_SKU \|\| CAPTURE_TIMESTAMP) | Zero dupes; reject load if dupes found                                              |
| Day-over-day delta             | ABS(today - yesterday) / yesterday per SKU                     | Alert if > 50% swing (or z-score > 3 as alternative)                                |
| Cross-validation vs. old model | Compare GEP2_AVAILABLE_QTY + FBA quantities                    | New feed should align closely with old `inventory_fct_balance` for overlapping cols |
| Out-of-order load              | SOURCE_CAPTURE_TIMESTAMP < MAX(existing)                       | Log with IS_OUT_OF_ORDER = TRUE; do not reject                                      |
| Load audit completeness        | Check audit entry exists after each load                       | Alert if missing                                                                    |

  

---

## Implementation Sequence
 

1. **Finalize + send client clarification email** — open questions above; gate all build steps on responses

2. **Resolve source question (Q1)** — same source as old model or new? This determines Path A/B/C

3. **Grain go/no-go** — confirm grain before any Layer 2/3 work

4. **Stand up ingestion** — provision Snowflake role + grants; confirm landing zone name

5. **Profile sample against `shared_dim_product`** — run join, measure MASTER_SKU match rate + null distribution; cross-check qty columns against old `inventory_fct_balance` output

6. **Create load audit table** — `WAREHOUSE.INVENTORY_LOAD_AUDIT`

7. **Draft `inventory_fct_balance.sql`** — greenfield source view; header comment documents column set + source Iteration

8. **Add scheduled task** — incremental append-only INSERT

9. **Draft `extract_inventory_current.sql`** — latest snapshot + product dim join

10. **Run full QA checklist** — resolve negative-value policy before sign-off

11. **Draft `notes/projects/GP-208/design.md`** — column dictionary, grain, open-item resolutions, data quality flags

12. **Data share exposure** (if GEP needs external access)

13. **Handoff summary** to stakeholders

  

---

  

## Estimated Effort

| Task | Estimate |
|--------------------------------------------------------|----------|
| Profile sample + summarize column behavior | ~2 hrs |
| Draft target schema/mapping + open-question log | ~3 hrs |
| Ingestion approach + QA outline | ~2 hrs |
| Build ingestion/staging objects (once details confirmed) | ~4 hrs |
| Wrap-up comms / reporting handoff | ~1 hr |
| **Total** | **~12 hrs** |
