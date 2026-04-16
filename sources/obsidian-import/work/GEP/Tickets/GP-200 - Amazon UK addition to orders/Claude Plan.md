# GP-200: Add Amazon UK to Order Line

  

## Context

GEP wants Amazon UK orders to appear in the order line warehouse data, particularly in the window before orders appear in Seller Cloud (pulled directly from Amazon's API). Company ID 178 ("Amazon UK", GBP) already exists in the currency map. GEP has provided separate UK credentials (in Dashlane). This is orders-only scope — ad spend and traffic are out of scope.

  

## Implementation Plan

  

### 1. New Connection — `amazon_seller_central_uk.json` (CREATE)

- **File**: `GEP/eclipse/connections/amazon_seller_central_uk.json`

- Clone `amazon_seller_central.json`, replace credentials with the UK ones from Dashlane

- Name: `"Amazon Seller Central - UK"`

- New UUID for `id`

- Same `account_id: "da8904db"`

- Check if any Eclipse manifest or registration file references connection IDs — if so, register the new connection there

- Verify UK credentials have the same report throttling limits; if not, adjust `retry_default`/`retry_min`/`retry_max` or schedule priority accordingly

  

### 2. New Template — All Orders Report UK (CREATE)

- **File**: `GEP/eclipse/templates/amazon/all_orders_report_UK.json`

- Clone `all_orders_report.json`

- Point `connection_id` to the new UK connection

- Change `filter_marketplace` value to `"gb"` (follows ISO country code pattern: us, ca, gb)

  - **Must validate against connector docs first** — if the connector doesn't recognize `"gb"` for the orders category, may need to leave filter blank and filter downstream on marketplace_id instead

- Add `"table_name": "ALL_ORDERS_UK"` to options so data lands in `CURRENT_REPORT_ALL_ORDERS_UK`

- New UUID for `id`

- Update `name` to `"Amazon Seller Central - All Orders Report - UK"`

- Set `min_date` to when UK data actually starts (ask GEP) — avoids empty-data retries

- Check if any Eclipse manifest references template IDs — if so, register

  

### 3. SQL Changes — Union UK orders into existing views

  

`CURRENT_REPORT_ALL_ORDERS` is referenced in **4 files**. For each:

- Use a **CTE** (`AMAZON_ALL_ORDERS`) to define the UNION once per file — easier to extend when other EU markets come online

- Use **explicit named columns** (not `SELECT *`) to guard against schema drift between the two tables

- Verify QUALIFY/window/dedup logic still works when both markets flow in simultaneously

  

#### 3a. `sales_dim_order_base.sql` (EDIT)

Add `AMAZON_ALL_ORDERS` CTE to existing WITH block and replace FROM reference:

```sql

AMAZON_ALL_ORDERS AS (

    SELECT

        AMAZON_ORDER_ID, ASIN, CURRENCY, FULFILLMENT_CHANNEL, ITEM_PRICE,

        ITEM_STATUS, ITEM_TAX, PROMOTION_IDS, PURCHASE_DATE, QUANTITY,

        SHIP_CITY, SHIP_COUNTRY, SHIP_POSTAL_CODE, SHIP_STATE, SKU, ORDER_STATUS

    FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS

    UNION ALL

    SELECT

        AMAZON_ORDER_ID, ASIN, CURRENCY, FULFILLMENT_CHANNEL, ITEM_PRICE,

        ITEM_STATUS, ITEM_TAX, PROMOTION_IDS, PURCHASE_DATE, QUANTITY,

        SHIP_CITY, SHIP_COUNTRY, SHIP_POSTAL_CODE, SHIP_STATE, SKU, ORDER_STATUS

    FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK

)

-- Then: FROM AMAZON_ALL_ORDERS AS AMAZON_ORDERS

```

- Company mapping already works — `SHARED_DIM_COMPANY_CURRENCY_MAP` has `(178, 1, 'GBP')` which maps GBP → company 178 ("Amazon UK")

- Dedup logic (`ORDER_LIMIT.ORDERSOURCEORDERID IS NULL`) must still correctly exclude UK orders once they appear in Seller Cloud — verify that Seller Cloud UK orders have `ORDERSOURCE IN (20, 4)` like US orders

  

#### 3b. `sales_fct_amazon_orderline.sql` (EDIT)

Same CTE pattern (new WITH block added), replacing the FROM reference.

  

#### 3c. `sales_fct_seller_cloud_orderline.sql` (EDIT)

Same CTE pattern prepended to existing WITH block, replacing the LEFT JOIN source. Alias and ON clause preserved.

  

#### 3d. `extract_warehouse_metadata.sql` (EDIT)

Add a new metadata UNION ALL block for the UK table:

```sql

UNION ALL

SELECT

'AMAZON' AS TOPIC,

'REPORT' AS CATEGORY,

'ALL_ORDERS_UK' AS TABLE_NAME,

MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___) AS LATEST_RECORD_UTC

FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK

```

- After deploying, run the metadata view manually — it tends to cache until the task chain completes

  

### 4. `shared_dim_marketplace.sql` (EDIT)

Add UK to the hard-coded unknown-order marketplace fallback VALUES list:

```sql

(163, 'Global Ecom Partners', 'Amazon US'),

(166, 'Amazon Canada', 'Amazon CA'),

(168, 'Amazon Mexico', 'Amazon Mexico'),

(178, 'Amazon UK', 'Amazon UK')        -- NEW

```

- Confirm company_id 178 matches what the Seller Cloud join uses, so the "unknown" block resolves correctly

  

### 5. CSV Supplements (MANUAL / out-of-repo)

- **Marketplace Name CSV**: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Name`

  - Needs a row mapping the UK channel/company to marketplace name "Amazon UK"

- **Marketplace Config CSV**: `/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Config`

  - Needs a row for "Amazon UK" with `APPLY_DISCOUNT_TO_NET` and `DTC_FEE_RATE` values

- **Action**: Call out these exact paths in the ticket so QA knows where to look. Require screenshot/snippet evidence once updated.

  

## Files Summary

  

| File | Action |

|------|--------|

| `GEP/eclipse/connections/amazon_seller_central_uk.json` | CREATE |

| `GEP/eclipse/templates/amazon/all_orders_report_UK.json` | CREATE |

| `GEP/snowflake/warehouse/sales_dim_order_base.sql` | EDIT (add CTE to WITH block) |

| `GEP/snowflake/warehouse/sales_fct_amazon_orderline.sql` | EDIT (add new WITH + CTE) |

| `GEP/snowflake/warehouse/sales_fct_seller_cloud_orderline.sql` | EDIT (prepend CTE to WITH) |

| `GEP/snowflake/warehouse/extract_warehouse_metadata.sql` | EDIT (add UK metadata block) |

| `GEP/snowflake/warehouse/shared_dim_marketplace.sql` | EDIT (add UK to VALUES) |

  

## Verification / QA Plan

  

1. **Data ingestion**: Deploy connection + template, confirm data appears in `CURRENT_REPORT_ALL_ORDERS_UK`

2. **Warehouse pipeline**: Run task chain (`task_warehouse_orderline`) and verify:

   - UK orders in `SALES_DIM_ORDER_BASE` with company_id 178

   - UK order lines in `SALES_FCT_AMAZON_ORDERLINE`

   - UK orders in unified `SALES_FCT_ORDERLINE`

   - "Amazon UK" in `SHARED_DIM_MARKETPLACE`

3. **Cross-reference**: Pick one known Seller Cloud UK order ID and trace it end-to-end through `SALES_FCT_ORDERLINE`

4. **Row-count delta**: Compare US/CA row counts before and after to prove existing data didn't shift

5. **Dedup validation**: Confirm that UK orders are correctly zeroed out / excluded from Amazon-direct once Seller Cloud ingests them (UK pipeline may lag differently than US)

6. **Metadata**: Run `extract_warehouse_metadata` view manually and verify UK entry shows

  

## Risks

- **Connector marketplace support**: `"gb"` may not be recognized for orders category — validate against connector docs first; fallback is blank filter + downstream filtering

- **Schema drift**: UK table must have identical columns to US table — use explicit column names in UNION

- **UK pipeline lag**: Dedup timing may differ from US — monitor for duplicates in early days

- **CSV supplements**: Must be updated separately on Nextcloud before marketplace names resolve

- **Throttling**: UK credentials may have different rate limits than NA



# To do 
- manually add on CosmosDB work connection, work template