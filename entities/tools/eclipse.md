---
tags: [entity, tool, eclipse, connector, etl]
aliases: [Eclipse, Eclipse Connector, ALDC Connector]
sources: [clients repo eclipse/ directories, connector repo]
created: 2026-04-16
updated: 2026-04-16
---

# Eclipse

ALDC's proprietary connector platform for data ingestion. Eclipse pulls data from source systems (APIs, databases, files) and loads it into [[Snowflake]]. Configuration is JSON-based, living in the [[clients-repo]].

## Core Concepts

### Connections
JSON files in `CLIENT/eclipse/connections/` that hold authentication credentials for a data source.

```
connections/
├── amazon_seller_central.json   # OAuth tokens, client ID/secret
├── sellercloud_sql.json         # SQL Server uid/pwd
├── budget.json                  # CSV file config
└── ...
```

Each connection defines: server/host, auth type (API key, OAuth, SQL credentials), and any source-specific config.

### Templates
JSON files in `CLIENT/eclipse/templates/SOURCE_NAME/` that define what data to pull from a connected source.

```
templates/
├── amazon/
│   ├── all_orders_report.json
│   ├── inventory_report.json
│   └── sales_and_traffic_report.json
├── sellercloud_sql/
│   ├── order.json
│   ├── product.json
│   └── inventory_pandl.json
└── supplement/
    ├── budget.json
    ├── currency.json
    └── calendar.json
```

Templates specify: source table/endpoint, columns to extract, filters, scheduling params (like `min_date`), and how data maps to Snowflake tables.

**Supplement templates** are special — they pull from CSV files or reference data, not live APIs.

### Tasks
Scheduled execution of templates. Tasks define when and how often Eclipse pulls data. Tasks are managed in the Eclipse UI or via CosmosDB.

### Capacity / Dataset
`capacity.json` and related configs define the Eclipse account's capacity allocation and data model structure.

## Data Landing Pattern

Eclipse loads data into Snowflake source schemas using a `CURRENT_*` table naming pattern:

```
PROD_DG1_GEP.AMAZON.CURRENT_REPORT_FBA_INVENTORY
PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL
PROD_DG1_GEP.SUPPLEMENT.CURRENT_TIME_CALENDAR
```

The `CURRENT_` prefix indicates the latest snapshot. Some also maintain `HISTORY_` prefixed tables for full history. The `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___` column tracks when each snapshot was captured.

## Registration Workflow

When adding a new connection + template:

1. **Create connection JSON** in `CLIENT/eclipse/connections/`
2. **Create template JSON(s)** in `CLIENT/eclipse/templates/SOURCE_NAME/`
3. **Register in CosmosDB** — connection and template must be registered via the Eclipse admin interface or API
4. **Create/resume task** — schedule the template execution
5. **Verify data landing** — check that `CURRENT_*` tables appear in the correct Snowflake source schema

See [[gep-snowflake-pbi-deployment]] for the full deployment walkthrough including Eclipse registration.

## Connector Runtime

The Eclipse connector runs as a Docker container on VMs. The runtime:
- Reads connection + template configs from CosmosDB
- Executes data pulls on schedule
- Handles pagination, rate limiting, retries
- Loads data into Snowflake via stage + COPY INTO

The runtime code lives in the `connector` repo (`C:\Users\PaulRussell\repos\connector`).

## Eclipse Environments

| Environment | CosmosDB Instance | Notes |
|-------------|-------------------|-------|
| Production | `eclipse_prod1c01` | Production connectors |
| Test | `eclipse_test1c01` | Testing/development |

Connection configs for both are in `ALDC_ENG/eclipse/connections/`.

## Scale (in clients repo)

- 150+ connections across 19 clients
- 300+ templates defining data pulls
- Major connection types: Snowflake, SQL Server, REST APIs (Amazon, Meta, Google, etc.), CSV files, MongoDB, Firebase

## See Also

- [[clients-repo]] — where Eclipse configs live
- [[data-pipeline-flow]] — Eclipse's role in the full pipeline
- [[Snowflake]] — where Eclipse loads data
- [[connector]] — the Eclipse runtime codebase
