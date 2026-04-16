---
tags: [entity, tool, snowflake, data-warehouse]
aliases: [Snowflake, SF]
sources: [clients repo snowflake/ directories, __TEMPLATE_ACCOUNT/snowflake/readme.txt]
created: 2026-04-16
updated: 2026-04-16
---

# Snowflake

ALDC's data warehouse platform. Each client has a dedicated Snowflake environment with a star schema of dimensions, facts, extracts, and report-common views. [[Power BI]] consumes the report_common views.

## Environment Naming

Pattern: `{ENV}_DG1_{CLIENT}`

| Environment | Example | Purpose |
|-------------|---------|---------|
| PROD | `PROD_DG1_GEP` | Production |
| TEST | `TEST_DG1_GEP` | User testing / staging |

## Schema Architecture

Each client environment contains these schemas (see [[star-schema-convention]] for details):

| Schema | Purpose | Materialization |
|--------|---------|----------------|
| Source schemas (e.g., `AMAZON`, `SELLERCLOUD_SQL`, `SUPPLEMENT`) | Raw data from [[Eclipse]] connectors | Tables populated by Eclipse |
| `WAREHOUSE_SOURCE` | Intermediate views — clean, join, standardize source data | Views (not materialized) |
| `WAREHOUSE` | Final star schema — dimensions and facts | Physical tables via scheduled tasks |
| `REPORT_COMMON` | Pre-aggregated BI-optimized views | Views consumed by [[Power BI]] |
| `DATA_SHARE` | Secure views for Snowflake-to-Snowflake sharing | Secure views |

### Data flow through schemas

```
Source systems → Eclipse → Source schemas (AMAZON.*, SELLERCLOUD_SQL.*, SUPPLEMENT.*)
    ↓
WAREHOUSE_SOURCE.* (intermediate views — joins, SHA2 keys, type casting)
    ↓
WAREHOUSE.* (physical tables — scheduled task: CREATE TABLE AS SELECT)
    ↓
REPORT_COMMON.* (pre-aggregated views for Power BI)
    ↓
DATA_SHARE.* (secure views for external consumers, optional)
```

## Key SQL Patterns

### SHA2 Key Hashing
All surrogate keys use SHA2:
```sql
SHA2(PRODUCT_ID) AS PRODUCT_KEY
SHA2(TO_DATE(DATE)) AS DATE_KEY
SHA2(BALANCE_DATE::VARCHAR) AS BALANCE_DATE_KEY
```

### Currency Handling (Triple Measure Pattern)
All monetary measures appear in three versions:
```sql
AMOUNT_TRANSACTION    -- In transaction currency
AMOUNT_SUBSIDIARY     -- In subsidiary currency (often 0.0 for single-currency clients)
AMOUNT_CONSOLIDATED   -- Converted to reporting currency via CONSOLIDATED_RATE
```
Exchange rates from [[star-schema-convention|SHARED_FCT_EXCHANGE_RATE]] in `ALDC_LIBRARY`.

### Division Safety
```sql
DIV0(numerator, denominator)  -- Returns 0 on division by zero (not NULL)
```

### Window Functions
```sql
DENSE_RANK() OVER(ORDER BY DATE) :: INT AS DATE_SEQUENCE
QUALIFY ROW_NUMBER() OVER(PARTITION BY key ORDER BY date DESC) = 1  -- Latest row
```

### Null Coalescing
```sql
COALESCE(field1, field2, field3) AS final_field
EQUAL_NULL(a, b)  -- Treats NULLs as equal in comparisons
```

## Scheduled Tasks

WAREHOUSE tables are materialized from WAREHOUSE_SOURCE views using Snowflake scheduled tasks:
- Tasks run on a schedule (hourly for inventory, varies by client)
- Pattern: `CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT * FROM WAREHOUSE_SOURCE.X`
- Incremental pattern: `INSERT INTO ... WHERE timestamp > MAX(existing)`

## Dynamic Tables (Newer Pattern)

[[fusion92]] uses Snowflake dynamic tables instead of scheduled tasks:
```sql
CREATE OR REPLACE DYNAMIC TABLE ... TARGET_LAG = '1 hour'
```
Auto-refreshes without explicit task management. [[GEP]] still uses the older secure view + task pattern.

## Data Shares

Secure views in `DATA_SHARE` schema expose data to external Snowflake accounts:
- Always use explicit column lists (never `SELECT *`) — prevents breakage when source columns change
- Pattern: `CREATE OR REPLACE SECURE VIEW DATA_SHARE.X AS SELECT col1, col2, ... FROM WAREHOUSE.X`
- See [[data-share-pattern]] for full setup guide

## Deployment

Deploys are **manual** — code merging to a branch does NOT auto-deploy to Snowflake. See deployment processes for each client (e.g., [[gep-snowflake-pbi-deployment]]).

Steps:
1. Copy SQL from the repo file
2. Paste and execute in Snowflake UI (worksheet)
3. Verify view/table was created correctly
4. Pause → recreate → resume any scheduled tasks that reference the changed objects

## See Also

- [[star-schema-convention]] — naming patterns
- [[data-pipeline-flow]] — full pipeline flow
- [[Power BI]] — downstream consumer
- [[Eclipse]] — upstream data source
- [[clients-repo]] — where SQL files live
