---
tags: [concept, architecture, snowflake, naming, star-schema]
aliases: [star schema, naming convention, warehouse naming]
sources: [clients repo __TEMPLATE_ACCOUNT/snowflake/readme.txt, GEP/snowflake/warehouse/*.sql]
created: 2026-04-16
updated: 2026-04-16
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

## See Also

- [[Snowflake]] — the platform
- [[data-pipeline-flow]] — how data flows through these objects
- [[clients-repo]] — where the SQL files live
- [[client-repo-structure]] — folder layout convention
