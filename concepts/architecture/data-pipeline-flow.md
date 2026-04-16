---
tags: [concept, architecture, pipeline, data-flow]
aliases: [data pipeline, pipeline flow, ETL flow]
sources: [clients repo GEP/ and FUSION_92/ directories, __TEMPLATE_ACCOUNT/snowflake/readme.txt]
created: 2026-04-16
updated: 2026-04-16
---

# Data Pipeline Flow

The end-to-end data pipeline at ALDC: [[Eclipse]] pulls from source systems, loads into [[Snowflake]], transforms through a layered star schema, and surfaces in [[Power BI]].

## Pipeline Diagram

```
┌──────────────────────┐
│   SOURCE SYSTEMS     │
│                      │
│  Amazon Seller API   │
│  SellerCloud REST    │
│  SellerCloud SQL     │
│  Meta/Google/etc.    │
│  CSV files           │
│  Snowflake (3rd pty) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   ECLIPSE            │  Connector runtime (Docker on VMs)
│   connections/*.json │  Auth credentials
│   templates/*.json   │  Data pull definitions
│   tasks              │  Scheduled execution
└──────────┬───────────┘
           │  COPY INTO / INSERT
           ▼
┌──────────────────────────────────────────────────────┐
│   SNOWFLAKE                                          │
│                                                      │
│   Source Schemas ──► WAREHOUSE_SOURCE ──► WAREHOUSE   │
│   (AMAZON.*,         (intermediate       (physical    │
│    SELLERCLOUD.*,     views: join,        tables via  │
│    SUPPLEMENT.*)      clean, hash keys)   sched task) │
│                                              │        │
│                                              ▼        │
│                                      REPORT_COMMON    │
│                                      (pre-aggregated  │
│                                       BI-ready views) │
│                                              │        │
│                              ┌────────────────┤       │
│                              ▼                ▼       │
│                         DATA_SHARE      Power BI      │
│                         (secure views   consumption   │
│                          for external                 │
│                          consumers)                   │
└──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│   POWER BI           │
│   Imports from       │
│   REPORT_COMMON.*    │
│   Manual refresh     │
└──────────────────────┘
```

## Layer Details

### Layer 0: Source Systems
External systems that own the data. ALDC does not control these.

Examples for [[GEP]]:
- Amazon Seller Central (orders, inventory, FBA, traffic)
- Amazon Advertising (sponsored products/brands/display campaigns)
- SellerCloud (orders, products, inventory, purchasing, RMAs)
- Galactica SQL Server (additional order/payment data)
- CSV supplements (budgets, currency rates, forecasts, reference data)

### Layer 1: Eclipse Ingestion
[[Eclipse]] connectors pull data on schedule and load into Snowflake source schemas.

Data lands as `CURRENT_*` tables:
```
PROD_DG1_GEP.AMAZON.CURRENT_REPORT_FBA_INVENTORY
PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL
PROD_DG1_GEP.SUPPLEMENT.CURRENT_TIME_CALENDAR
```

The `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___` column tracks snapshot capture time.

### Layer 2: WAREHOUSE_SOURCE (Intermediate Views)
SQL views that join, clean, and standardize source data:
- Apply SHA2 hashing for surrogate keys
- Cast data types, handle nulls with COALESCE
- Join across source schemas (e.g., product + vendor + brand)
- Apply business logic (e.g., COGS calculations, fee allocations)

These are **views, not materialized** — they compute on read.

### Layer 3: WAREHOUSE (Physical Tables)
Snowflake scheduled tasks materialize WAREHOUSE_SOURCE views into physical tables:
```sql
-- Full refresh
CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT * FROM WAREHOUSE_SOURCE.X;

-- Incremental append (e.g., for inventory)
INSERT INTO WAREHOUSE.X
SELECT * FROM WAREHOUSE_SOURCE.X
WHERE timestamp > (SELECT MAX(timestamp) FROM WAREHOUSE.X);
```

This is the star schema consumed by everything downstream:
- `shared_dim_*` — reusable dimensions (date, product, customer, etc.)
- `*_fct_*` — domain facts (sales orderline, inventory balance, marketing activity)
- `extract_*` — flattened/denormalized exports

### Layer 4: REPORT_COMMON (BI-Ready Views)
Pre-aggregated views designed for [[Power BI]] consumption:
- GROUP BY at the right grain for each report
- SUM/COUNT aggregations pre-computed
- Union of budget + actual data where needed
- Named by report type: `RETAIL_DAILY_SALES_FACT`, `RETAIL_KPI_MANAGER_SALES_FACT`, etc.

### Layer 5: DATA_SHARE (Optional)
Secure views for Snowflake-to-Snowflake sharing with external consumers:
- Always use explicit column lists (never `SELECT *`)
- Exposed via Snowflake's native data sharing mechanism
- See [[data-share-pattern]] for setup

## Key Properties

- **No CI/CD**: All deployments are manual. Code in repo is source of truth; Snowflake mirrors it on demand.
- **No streaming**: All batch-oriented. Eclipse runs on schedules (hourly, daily).
- **Currency normalization**: All monetary facts have TRANSACTION, SUBSIDIARY, and CONSOLIDATED versions.
- **Idempotent views**: WAREHOUSE_SOURCE views can be re-executed safely. Physical tables are recreated from scratch or appended incrementally.

## See Also

- [[Eclipse]] — connector platform (Layer 1)
- [[Snowflake]] — data warehouse (Layers 2-5)
- [[Power BI]] — reporting (consumer)
- [[star-schema-convention]] — naming patterns for Layers 2-3
- [[client-repo-structure]] — where the SQL/config files live
