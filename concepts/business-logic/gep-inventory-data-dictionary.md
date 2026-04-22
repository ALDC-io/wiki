---
tags: [business-logic, gep, inventory, snowflake, data-dictionary]
aliases: [GEP inventory columns, inventory data dictionary, INVENTORY_FCT_BALANCE columns]
sources: [GEP/snowflake/warehouse/inventory_fct_balance.sql, GEP/snowflake/warehouse/extract_inventory_current.sql, GEP/_testing/GP-208/uat_column_coverage.md]
created: 2026-04-16
updated: 2026-04-16
---

# GEP Inventory — Data Dictionary

Durable reference for the columns in [[GEP]]'s `INVENTORY_FCT_BALANCE` fact table and the `EXTRACT_INVENTORY_CURRENT` public view that feeds [[Power BI]]. Populated from [[GP-208]] Phase 1 ingestion design.

## Column status legend

- **Populated** — real data, refreshed each load
- **Derived** — computed from other populated columns
- **Placeholder** — intentionally `NULL` until upstream ingestion work lands. Do not read as "zero units"

## Product identity

Product metadata joined from `SHARED_DIM_PRODUCT` on `PRODUCT_KEY`. All populated.

| Column                                                                        | Source                           | Notes                                         |
| ----------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------- |
| `PRODUCT_ID`                                                                  | Sellercloud internal ID          | Primary join key to fact                      |
| `PRODUCT_KEY`                                                                 | `SHA2(PRODUCT_ID)`               | Surrogate (star schema convention)            |
| `MASTER_SKU`                                                                  | Sellercloud                      | Business-facing SKU (e.g., `MS_610585814451`) |
| `PRODUCT_NAME`, `ASIN`, `UPC`, `BRAND`, `DEFAULT_VENDOR`, `MANUFACTURER_NAME` | Sellercloud → SHARED_DIM_PRODUCT | Standard product metadata                     |

## Dates

| Column | Description | Populated when |
|---|---|---|
| `BALANCE_DATE` | Snapshot date | Always |
| `BALANCE_DATE_KEY` | `SHA2(BALANCE_DATE::VARCHAR)` surrogate | Always |
| `CAPTURE_TIMESTAMP` | Exact timestamp of Amazon FBA snapshot | Only when row has FBA data. Used to identify FBA-sourced rows and detect [[accumulating-source-tables\|moving-target source tables]] |

## Self-managed warehouse (GEP2)

Sourced from `PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL` filtered to Sellercloud `GEP2` warehouse. Non-sellable rows come from `GEP2-Returns_Unsellable`. All populated.

| Column | Description |
|---|---|
| `GEP2_AVAILABLE_QTY` | Units available for sale |
| `GEP2_RESERVED_QTY` | Units reserved against open orders (Sellercloud) |
| `GEP2_ON_HAND_QTY` | Physical on-hand count |
| `NON_SELLABLE_QTY` | Returned / damaged units in `GEP2-Returns_Unsellable` |

## Amazon FBA (US marketplace)

Sourced from `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_FBA_INVENTORY`, dedup'd to latest row per SKU via `ROW_NUMBER() OVER (PARTITION BY SKU ORDER BY ___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___ DESC)`. All populated.

| Column | Amazon source | Description |
|---|---|---|
| `US_FBA_AVAILABLE_QTY` | `AFN_FULFILLABLE_QUANTITY` | Available for Amazon orders |
| `US_FBA_INBOUND_WORKING_QTY` | `AFN_INBOUND_WORKING_QUANTITY` | Being prepared by seller (not yet shipped) |
| `US_FBA_INBOUND_SHIPPED_QTY` | `AFN_INBOUND_SHIPPED_QUANTITY` | In transit to Amazon FC |
| `US_FBA_INBOUND_RECEIVING_QTY` | `AFN_INBOUND_RECEIVING_QUANTITY` | Received at FC, not yet shelved |
| `US_FBA_RESEARCHING_QTY` | `AFN_RESEARCHING_QUANTITY` | Under investigation at FC (e.g., missing units) |
| `US_FBA_RESERVED_QTY` | `AFN_RESERVED_QUANTITY` | Reserved for open Amazon orders |
| `US_FBA_UNFULFILLABLE_QTY` | `AFN_UNSELLABLE_QUANTITY` | Damaged / defective at FC |
| `US_FBA_TOTAL_QTY` | `AFN_TOTAL_QUANTITY` | Amazon's total-at-Amazon tally |
| `US_FBA_WAREHOUSE_QTY` | `AFN_WAREHOUSE_QUANTITY` | Units physically at an FC |
| `US_FBA_FUTURE_SUPPLY_BUYABLE_QTY` | `AFN_FUTURE_SUPPLY_BUYABLE` | Expected future availability |
| `US_FBA_RESERVED_FUTURE_SUPPLY_QTY` | `AFN_RESERVED_FUTURE_SUPPLY` | Future supply already reserved |
| `MFN_FULFILLABLE_QTY` | `MFN_FULFILLABLE_QUANTITY` | Merchant-fulfilled network (self-shipped, not in Amazon FCs) |

### Validated FBA identities (2026-04-16 QA)

Confirmed empirically during Phase 1 QA against `TEST_DG1_GEP.WAREHOUSE_TEST_PAUL.INVENTORY_FCT_BALANCE` (6,226 FBA rows):

- **`AFN_TOTAL_QUANTITY`** = `AFN_FULFILLABLE + AFN_RESERVED + AFN_INBOUND_WORKING + AFN_INBOUND_SHIPPED + AFN_INBOUND_RECEIVING + AFN_RESEARCHING + AFN_UNSELLABLE` — **0 mismatches** across all rows
- **`AFN_WAREHOUSE_QUANTITY`** = `AFN_FULFILLABLE + AFN_RESERVED + AFN_UNSELLABLE + AFN_RESEARCHING` — confirmed via exhaustive check: 352 rows deviated from a simpler three-component formula; all 352 were explained by the `AFN_RESEARCHING` addition

Researching-state units are physically at the FC (hence included in warehouse), but `INBOUND_RECEIVING` (at the dock, not yet shelved) is **not** included.

### Negative values

A small number of rows may show negative values in reserved or adjustment columns — these reflect upstream corrections (Amazon adjustments or Sellercloud reclassifications), not data errors. Passthrough unchanged; flag via observability column only if the rate exceeds ~1% of rows.

## Purchasing

| Column | Description | Source |
|---|---|---|
| `ON_ORDER_GEP2_QTY` | Sum of open purchase-order quantities, aggregated per product (excludes cancelled POs upstream) | `WAREHOUSE.PURCHASING_FCT_BALANCE` |

## Pricing reference (from product master)

| Column | Description |
|---|---|
| `AVERAGE_COST` | Rolling average unit cost (Sellercloud) |
| `SITE_COST` | Listed site cost |
| `BUSINESS_PRICE` | Amazon business price |
| `LIVE_PRICE` | Current listed price on Amazon |

## Inventory value

| Column | Formula | Notes |
|---|---|---|
| `GEP2_LAST_COST` | Raw — Sellercloud | May be NULL for products without cost; NULL-preserving by design |
| `GEP2_LAST_SITE_PRICE` | Raw — Sellercloud | May be NULL |
| `GEP2_AVAILABLE_COST` | `GEP2_AVAILABLE_QTY × GEP2_LAST_COST` | |
| `GEP2_ON_HAND_COST` | `GEP2_ON_HAND_QTY × GEP2_LAST_COST` | |
| `GEP2_AVAILABLE_RETAIL` | `GEP2_AVAILABLE_QTY × GEP2_LAST_SITE_PRICE` | |
| `GEP2_ON_HAND_RETAIL` | `GEP2_ON_HAND_QTY × GEP2_LAST_SITE_PRICE` | |
| `NON_SELLABLE_COST`, `NON_SELLABLE_RETAIL` | Non-sellable qty × unsellable unit cost / price | |

## Rollup aggregates

Modelled after the `Total_*` aggregates in the reference feed.

| Column | Formula |
|---|---|
| `US_FBA_INBOUND_TOTAL_QTY` | `INBOUND_WORKING + INBOUND_SHIPPED + INBOUND_RECEIVING` |
| `TOTAL_AVAILABLE_QTY` | `GEP2_AVAILABLE_QTY + US_FBA_AVAILABLE_QTY` |
| `TOTAL_NON_SELLABLE_QTY` | `NON_SELLABLE_QTY + US_FBA_RESERVED_QTY + US_FBA_UNFULFILLABLE_QTY` |

## Placeholder columns (pending upstream ingestion)

Always `NULL` in the current build. The schema position matches the reference feed's shape so Power BI visuals don't need to restructure when real data lands.

| Column | What it represents | What's required to populate |
|---|---|---|
| `CA_FBA_AVAILABLE_QTY` | Canada-marketplace FBA available units | Add a second FBA report call with the CA marketplace ID |
| `AWD_AVAILABLE_QTY` | Amazon Warehousing & Distribution — units at AWD FCs | Integrate Amazon SP-API AWD inventory endpoint |
| `AWD_INTRANSIT_QTY` | AWD in-transit | Same as above |
| `PENDING_KIT_QTY` | Kit assemblies awaiting start | Requires Sellercloud kit-quantity exposure (current kit tables are cost-only) |
| `WORKING_KIT_QTY` | Kit assemblies in progress | Same as above |
| `FBM_OFFERED_KIT_QTY` | Kit listings offered via FBM | Same as above |

## Explicitly out of scope

- **Historical snapshots** — Phase 1 surfaces only the latest snapshot per product (full-replace refresh). History is Phase 2 via append-only incremental load.
- **Reserved sub-breakdown** (Orders / Processing / Transfer) — Amazon's base FBA report gives a single `RESERVED` lump; the 3-way split requires the separate SP-API Reserved Inventory Report.
- **Direct FBA / SCC FBA programs** — zero across the entire 100-row reference sample; likely unused at GEP.
- **Velocity / Days-on-Hand** — calculated measures; belong in a separate fact / view if prioritized.
- **`Iteration` field from reference feed** — feed-specific counter with no analog in our ingestion.

## Refresh model

- **Phase 1**: `CREATE OR REPLACE TABLE WAREHOUSE.INVENTORY_FCT_BALANCE AS SELECT * FROM WAREHOUSE_SOURCE.INVENTORY_FCT_BALANCE;` on a scheduled task — full replace, no history retained
- **Phase 2**: switch to `INSERT ... WHERE CAPTURE_TIMESTAMP > MAX(existing)` — appends new snapshots forward. Table grows over time; `EXTRACT_INVENTORY_CURRENT` continues to filter to `MAX(BALANCE_DATE)` so the change is transparent to consumers

## See Also

- [[GEP]] — client entity page
- [[GP-208]] — ticket that designed this fact table
- [[Snowflake]] — warehouse platform
- [[star-schema-convention]] — ALDC naming and key hashing conventions
- [[data-pipeline-flow]] — Eclipse → Snowflake → Power BI
