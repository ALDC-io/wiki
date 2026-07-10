---
tags: [concept, architecture, snowflake, naming, star-schema]
aliases: [star schema, naming convention, warehouse naming]
sources: [clients repo __TEMPLATE_ACCOUNT/snowflake/readme.txt, GEP/snowflake/warehouse/*.sql, Confluence TECH/1238499340 (Warehouse Standards)]
created: 2026-04-16
updated: 2026-07-08
---

# Star Schema Convention

ALDC's standard naming and structural patterns for [[Snowflake]] warehouse objects. All clients follow these conventions, defined in `__TEMPLATE_ACCOUNT/snowflake/readme.txt`.

## Object Naming

| Pattern | Example | Purpose |
|---------|---------|---------|
| `shared_dim_*` | shared_dim_date, shared_dim_product | Reusable dimensions shared across domains |
| `*_dim_*` | sales_dim_order, marketing_dim_campaign | Domain-specific dimensions |
| `*_fct_*` | sales_fct_orderline, inventory_fct_balance | Domain-specific fact tables |
| `shared_fct_*` | shared_fct_exchange_rate | Reusable facts shared across domains |
| `extract_*` | extract_product, extract_sales_detail | Flattened/denormalized exports for downstream |
| `*_base` | shared_dim_product_base | Base version of a dim (raw joins, no derived metrics) |

**Naming formula**: `{domain}_{type}_{name}`
- Domain: `shared`, `sales`, `marketing`, `purchasing`, `inventory`, `traffic`
- Type: `dim` (dimension), `fct` (fact)
- Name: descriptive (orderline, balance, activity, etc.)

## Key Hashing

All surrogate keys use SHA2:

```sql
SHA2(PRODUCT_ID) AS PRODUCT_KEY
SHA2(TO_DATE(DATE)) AS DATE_KEY
SHA2(BALANCE_DATE::VARCHAR) AS BALANCE_DATE_KEY
SHA2(CUSTOMER_ID) AS CUSTOMER_KEY
```

Convention: key column name is `{ENTITY}_KEY`, source column is `{ENTITY}_ID`.

## Common Dimensions

Present in most client implementations:

| Dimension | Key Column | Source | Notes |
|-----------|-----------|--------|-------|
| shared_dim_date | DATE_KEY | SUPPLEMENT.CURRENT_TIME_CALENDAR | 2015-01-01 to CURRENT_DATE + 2yr. Includes fiscal calendar (YEAR_SERIAL, QUARTER_SERIAL, MONTH_SERIAL, WEEK_SERIAL) |
| shared_dim_product | PRODUCT_KEY | Multiple (Sellercloud, Amazon, vendor) | Often has a `_base` variant. Includes MASTER_SKU, ASIN, pricing, brand, vendor |
| shared_dim_customer | CUSTOMER_KEY | Sellercloud orders/customers | May be deprecated for some clients (e.g., GEP as of 2024-10-25) |
| shared_dim_currency | CURRENCY_KEY | SUPPLEMENT.CURRENT_FINANCE_CURRENCY | ISO alpha/num codes, country, division significance |
| shared_dim_location | LOCATION_KEY | SUPPLEMENT.CURRENT_SELLERCLOUD_CHANNEL_MAP_CSV | Maps channel IDs to channel names |
| shared_dim_brand | BRAND_KEY | Sellercloud brands | Brand master data |
| shared_dim_vendor | VENDOR_KEY | Sellercloud vendors | Vendor master data |
| shared_dim_warehouse | WAREHOUSE_KEY | Sellercloud warehouses | Physical warehouse locations |
| shared_dim_marketplace | MARKETPLACE_KEY | SUPPLEMENT.CURRENT_MARKETPLACE_NAME | Marketplace mapping |
| shared_dim_periodicity | PERIODICITY_KEY | Supplement | Time granularity dimension |

## Currency Triple Pattern

All monetary measures in fact tables appear in three versions:

```sql
SALES_GROSS_TRANSACTION     -- In the transaction's original currency
SALES_GROSS_SUBSIDIARY      -- In subsidiary currency (often 0.0 for single-currency)
SALES_GROSS_CONSOLIDATED    -- Converted to reporting currency via CONSOLIDATED_RATE
```

Exchange rates come from `ALDC_LIBRARY.WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` (sourced from exchangeratesapi.io).

### ⚠ Transaction-currency handling in the data model (rule + open item)

**The rule:** every monetary value must be converted to a single reporting currency (USD `*_CONSOLIDATED`)
**before** it enters any cross-marketplace aggregation, margin, or ratio. **Never sum a raw
`*_TRANSACTION` / local-currency column across marketplaces** — Amazon US is USD, Amazon CA is CAD, UK is
GBP, etc., so a raw sum silently blends currencies.

- **Sales fact** — use `*_CONSOLIDATED` (USD). `*_TRANSACTION` is native only.
- **Marketing fact (`MARKETING_FCT_ACTIVITY`)** — its `COST`/`SALES_AMOUNT` are **local currency**
  (Amazon US=USD, CA=CAD; Google/Meta are USD-native). Do **not** sum `COST` for a USD total. The
  `MARKETING_EFFICIENCY` view is the USD-converted layer (`SPEND_USD*`): `AMZ_DAY` maps
  `MARKETPLACE_NAME`→currency then applies FX; Google/Meta pass through USD-native. Any new marketing
  measure/margin must consume the USD layer, and any **new ad source must land USD** (or be conditioned on
  its marketplace's currency) before it feeds margin. See [[cross-channel-marketing-attribution]].
- **Lectric agency fact** — `SALES_GROSS_TRANSACTION` is native (=USD today, US-only), **no
  `*_CONSOLIDATED` column**. Fine while US-only; **adding a non-USD Lectric marketplace requires the
  consolidated triple first**, or its sales will blend currencies into Navira totals.

**Exchange-rate caveats:** `SHARED_FCT_EXCHANGE_RATE` carry-forward fills **forward only** (interior gaps
must be healed — the Jan-2026 gap was patched manually), the ALDC Library feed **stopped 2026-03-03**
(carry-forward interim in place, see [[exchange-rate-pipeline]] / `project_exchange_rate_pipeline`), and the
table has **corrupt far-future dates** — always bound `EXCHANGE_DATE`.

> **OPEN ITEM (2026-07-08, to resolve):** standardize a single, model-wide currency-consolidation
> convention so *every* fact feeding the Navira data model (sales, marketing spend, agency tenants, and new
> ad sources) exposes a USD-consolidated column at ingestion — rather than each consumer view re-deriving FX.
> This removes the per-view `MARKETPLACE_NAME`→currency `CASE` maps and the risk that a new source is summed
> in local currency. Surfaced while building the cross-channel `Margin incl. Ad Spend` work (Google/Meta
> destination spend). Tracked in memory `feedback_transaction_currency_handling`.

## Common SQL Patterns

### Division safety
```sql
DIV0(numerator, denominator)  -- Returns 0 instead of NULL
```

### Window functions for ranking
```sql
DENSE_RANK() OVER(ORDER BY DATE) :: INT AS DATE_SEQUENCE
DENSE_RANK() OVER(PARTITION BY YEAR ORDER BY DATE) :: INT AS DATE_OF_YEAR
```

### Latest-row filtering
```sql
QUALIFY ROW_NUMBER() OVER(PARTITION BY key ORDER BY date DESC) = 1
```

### Null handling
```sql
COALESCE(field1, field2, field3) AS final_field
EQUAL_NULL(a, b)  -- Treats NULLs as equal in comparisons
```

### Secure views
```sql
CREATE OR REPLACE SECURE VIEW WAREHOUSE_SOURCE.view_name AS ...
```

## Base Table Pattern

When a dimension needs derived metrics that reference fact tables (creating potential circular dependencies), use a two-layer approach:

1. `shared_dim_product_base.sql` — raw source joins only (no fact table references)
2. `shared_dim_product.sql` — extends base with derived metrics (LAST_SALE_DATE, FIRST_SALE_DATE from SALES_FCT_ORDERLINE)

## Fact Table Patterns

### Union of sources
Large fact tables often union multiple sources:
```sql
-- sales_fct_orderline: union of 3 sources
SELECT ... FROM SALES_FCT_SELLER_CLOUD_ORDERLINE
UNION ALL
SELECT ... FROM unknown_cost_orders  -- ORDER_ID like 'UNK_%'
UNION ALL
SELECT ... FROM SALES_FCT_AMAZON_ORDERLINE  -- Not yet in Sellercloud
```

### Append-only with incremental load
```sql
INSERT INTO WAREHOUSE.table
SELECT * FROM WAREHOUSE_SOURCE.table
WHERE timestamp > (SELECT MAX(timestamp) FROM WAREHOUSE.table);
```

## GEP vs Fusion92 Differences

| Aspect | [[GEP]] | [[fusion92]] |
|--------|---------|-------------|
| View type | `CREATE OR REPLACE SECURE VIEW` | `CREATE OR REPLACE DYNAMIC TABLE` |
| Refresh | Scheduled tasks (manual management) | `TARGET_LAG = '1 hour'` (auto) |
| Domain focus | E-commerce (sales, inventory, purchasing) | Media (spend, flights, campaigns) |
| Fact complexity | High (margin calculations, fee allocation, return handling) | Moderate (spend aggregation, deduplication) |

## SQL style conventions

Sourced from Confluence TECH/1238499340 (Warehouse Standards, Brayden) — labelled "in progress, to be discussed" in the source; captured here as **proposed conventions**, not formally ratified. Ingested 2026-04-17.

### Order `*_KEY` after the value it hashes

When a view emits both a value and its `*_KEY`, put the **value first**, then the `*_KEY` as `SHA2(value)`. Lets the key reference the already-computed column instead of re-duplicating the calculation.

Instead of:

```sql
SHA2(
    DATEFROMPARTS(
        EXTRACT(YEAR FROM TO_DATE(SMARTSHEET.FLIGHT_START)),
        MONTHLY_SPEND.MONTH_NUMBER,
        1
    )
) AS SPEND_DATE_KEY,
DATEFROMPARTS(
    EXTRACT(YEAR FROM TO_DATE(SMARTSHEET.FLIGHT_START)),
    MONTHLY_SPEND.MONTH_NUMBER,
    1
) AS SPEND_DATE,
```

Do:

```sql
DATEFROMPARTS(
    EXTRACT(YEAR FROM TO_DATE(SMARTSHEET.FLIGHT_START)),
    MONTHLY_SPEND.MONTH_NUMBER,
    1
) AS SPEND_DATE,
SHA2(SPEND_DATE) AS SPEND_DATE_KEY,
```

### Re-use already-defined fields in `SELECT`

Downstream columns should reference earlier ones by alias rather than copy-pasting the expression. Saves edits and prevents drift between duplicated calculations.

Instead of:

```sql
TOTALSALES AS SALES_ACTUAL_GROSS,
TOTALSALES - TOTALDISCOUNT - TOTALREFUND AS SALES_ACTUAL_NET,
(TOTALSALES - TOTALDISCOUNT - TOTALREFUND) / QTY AS SALES_ACTUAL_NET_PER_ITEM,
```

Do:

```sql
TOTALSALES AS SALES_ACTUAL_GROSS,
SALES_ACTUAL_GROSS - TOTALDISCOUNT - TOTALREFUND AS SALES_ACTUAL_NET,
SALES_ACTUAL_NET / QTY AS SALES_ACTUAL_NET_PER_ITEM,
```

### Stick to `NUMBER` and `FLOAT`

Snowflake has only two real numeric type families — the `NUMBER` family (incl. `INT`, `DECIMAL`, `NUMERIC` etc.) and the `FLOAT` family (incl. `DOUBLE`, `REAL`). The rest are aliases. Proposal: standardize on `NUMBER` and `FLOAT` only, avoid the aliases, to reduce inconsistency across the warehouse.

## See Also

- [[Snowflake]] — the platform
- [[data-pipeline-flow]] — how data flows through these objects
- [[clients-repo]] — where the SQL files live
- [[client-repo-structure]] — folder layout convention
