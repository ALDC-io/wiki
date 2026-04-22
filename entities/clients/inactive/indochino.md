---
tags: [entity, client, indochino, retail, apparel, sql-server]
aliases: [INDOCHINO, Indochino Apparel Inc.]
sources: [Confluence CLIEN/875429895]
created: 2026-04-18
updated: 2026-04-18
---

# INDOCHINO (Indochino Apparel Inc.)

Custom apparel retailer. 2021 assessment engagement — ALDC conducted a detailed data warehouse architecture review and produced prioritized recommendations.

## Account Details

| Field | Value |
|---|---|
| Short Code | INDOCHINO |
| Industry | Retail Apparel (custom/made-to-measure) |
| Primary Timezone | America/Vancouver |
| Main Contact | Alex Buhler, CIO (`alex.buhler@indochino.com`) |
| Cloud Provider | Amazon Web Services |
| Region | Canada Central |

## System Architecture (2021 Assessment)

**Production SQL Host (TESTBI03)**

| Component | Value |
|---|---|
| IP | 52.9.71.99 |
| SQL Server version | 2016 SP2 CU6 (13.0.5292) |
| EC2 instance | r5.8xlarge |
| OS | Windows Server 2016 |
| Cores / RAM | 32 logical / 256 GB |
| Storage | ~4 TB |
| Monthly cost | ~$10,864/month + storage |
| Region | us-west-1b |

**Jumpbox:** `54.67.109.5` — Remote Desktop access. Username: `biservice` / password in Dashlane.

**Databases:**

| Database | Purpose | Recovery | Size |
|---|---|---|---|
| Control | Orchestration logging + metadata | Simple | 4 GB |
| Depot | Dimensional tables (data warehouse) | Simple | 195 GB |
| Landing | Temporary staging | Simple | 80 GB |
| MDS | Master Data Services | Full | 4 GB |
| Preload | Incremental dimension holding | Simple | 31 GB |
| Staging | ODS with history tracking | Simple | 240 GB |
| SSISDB | SSIS application store | Full | 75 GB |

**Integration Services Pipeline (4 phases):**
1. Pre-Extract: Source data → Landing DB
2. Extract: Landing → Staging DB (history-tracked)
3. Pre-Load: Staging → Preload DB (transformations)
4. Load: Preload → Depot DB (final warehouse)

**Reporting stack:** SQL Server Reporting Services (on-prem), SQL Server Analysis Services (Tabular, 2016), Power BI (workspace audit pending).

## Key Problems Identified

- Hourly orchestration frequently fails or doesn't complete on time
- Hard DML truncates in Load process render warehouse blank on reload
- SSAS on SQL Server 2016 — significantly behind current cloud capabilities
- No integration between Sage X3 (cloud accounting) and data warehouse
- Excel connectivity issues for 40–50 Finance/Marketing users
- R scripts executing against local DHL shipping data folders
- SSISDB log bloat (75 GB)

## Recommendations (Priority Ranked)

**High Impact:**
1. **Pre-Load/Load incremental logic** — adds incremental processing to replace full reloads; most important change
2. **Agent ad-hoc truncate fix** — remove hard DML truncates preventing blank-warehouse state
3. **Migrate SSAS → Power BI Premium Per User** — models are schema-compatible; faster refresh, lower cost

**Moderate Impact:**
4. Redevelop SSRS reports in Power BI; retire on-prem Reporting Services
5. Add covering indexes to Staging DB for Pre-Load join performance
6. Remove truncate from schedule (prevents blank reporting on batch failure)
7. Remove unnecessary columns from source extracts (reduces schema-binding errors)

**Long-Term:**
- Replace SQL Server with Snowflake (recommended over Redshift)
- Replace SSIS with Python/Airflow/DBT/Databricks
- Retire Master Data Services in favour of Excel/CSV
- Implement CI/CD
- Consolidate reporting on Power BI

## High-Priority SSIS Packages

| Phase | Package | Issue |
|---|---|---|
| Pre-Extract | account_measurement_tryon_detail | High runtime + failure rate |
| Pre-Extract | operation_shipment | High runtime |
| Pre-Extract | order_order_coupon | High failure rate |
| Pre-Load | Order Shipment, Order Detail, Order Header | Need incremental logic |
| Load | Order Shipment, Order Detail | High runtime |

## See Also

- [[star-schema-convention]] — ALDC warehouse conventions
- [[snowflake]] — recommended replacement for SQL Server DW
- `vault/infra-credentials.md` — Jumpbox credential noted (biservice / Dashlane)
