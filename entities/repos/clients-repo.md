---
tags: [entity, repo, clients, aldc]
aliases: [clients repo, clients repository, ALDC clients]
sources: [clients repo root directory structure]
created: 2026-04-16
updated: 2026-04-16
---

# clients repo

The primary ALDC repository (`C:\Users\PaulRussell\repos\clients`). Contains per-client [[Eclipse]] configs and [[Snowflake]] warehouse SQL. This is where all client data pipeline definitions and warehouse models live.

## Structure

Each client folder follows a standard pattern (defined in `__TEMPLATE_ACCOUNT`):

```
CLIENT_NAME/
├── eclipse/
│   ├── account.json          # Account-level config
│   ├── capacity.json         # Capacity/dataset config
│   ├── connections/          # Auth credentials for each data source
│   │   └── *.json
│   └── templates/            # Data pull definitions per source
│       ├── source_name/
│       │   └── *.json
│       └── supplement/
│           └── *.json
└── snowflake/
    ├── warehouse/            # Star schema SQL (dims, facts, extracts)
    │   └── *.sql
    ├── report_common/        # Pre-aggregated BI-ready views
    │   └── *.sql
    └── data_share/           # Snowflake-to-Snowflake share views (optional)
        └── *.sql
```

## Active Clients (19)

| Client | Domain | Key Data Sources |
|--------|--------|-----------------|
| [[GEP]] | E-commerce | Amazon, SellerCloud, Galactica |
| [[fusion92]] | Media/advertising | Meta, Google, Viant, Trade Desk |
| KIT_ACE | Retail | Shopify, Netsuite, Google Analytics, foot traffic |
| ASPIRE_NORTH | Healthcare/analytics | Salesforce, AWS S3, Fivetran |
| BOOK_DEPOT | E-commerce/retail | Google Analytics, MongoDB, SQL Server |
| DISH_DUER | Retail/operations | Snowflake Fivetran, CSV data |
| RAIN_CITY | E-commerce | Snowflake, Adventure Works DW |
| TERRAYN | Cannabis retail | Dutchie, Cova, Jane, Leafly, Greenbits (60+ templates) |
| ALDC_ENG | Internal engineering | Azure metrics, Eclipse instances, Galactica |
| ALDC_FINANCE | Internal finance | TSheets, web scrapers, CSV budgets |
| ALDC_LIBRARY | Shared data | Alpha Vantage, exchange rates, weather, scraping |
| ALDC_T_RETAIL | Internal demo | Wide World Importers DW |
| ALDC_QA | QA testing | NY Taxi data |
| ALDC_SALES | Internal sales | ComexStat, IMF, WTO |
| ALDC_SANDBOX | Sandbox | Minimal |
| ANALYTIC_LABS | Company CRM | NutShell, PhoneBurner, FeedTheRobot |
| NINTH_CO | Marketing | Facebook Marketing, Google Analytics |
| DROP_IN | Gaming | MySQL |
| HEARTLAND_DENTAL | Dental | Minimal (account.json only) |

## Utility Directories

| Directory | Purpose |
|-----------|---------|
| `__TEMPLATE_ACCOUNT` | Reference template for new client setup. Contains account.json, capacity.json, and readme files documenting the schema conventions |
| `__REPORT_COMMON_VIEWS` | Shared retail reporting view templates (DEFAULT_DEFAULT, RETAIL_ITEM_ATTRIBUTE_*) reused across clients |
| `CORE_DEV` | Account-level configuration and secrets. Contains `account_secret.json`, `account_template.json`, `account.json`, `work_connection.json` |
| `PUBLIC_LIBRARY` | Public API connections (weather, stocks, exchange rates, Twitter, TomTom) |

## Snowflake Schema Convention

Documented in `__TEMPLATE_ACCOUNT/snowflake/readme.txt`:

| Schema | Purpose |
|--------|---------|
| `warehouse_comm_src` | Common industry model views (base star schema) |
| `warehouse_cust_src` | Custom client-specific extensions to common views |
| `warehouse_comm` | Physical tables from comm_src (scheduled task materialization) |
| `warehouse_cust` | Physical tables from cust_src (scheduled task materialization) |
| `report_common` | Pre-aggregated BI-optimized views |

See [[star-schema-convention]] for naming details.

## Scale

- 150+ Eclipse connections across all clients
- 300+ Eclipse templates
- 200+ Snowflake warehouse SQL views

## See Also

- [[GEP]] — largest active client
- [[fusion92]] — media/advertising client
- [[Eclipse]] — connector platform (templates + connections)
- [[Snowflake]] — data warehouse
- [[star-schema-convention]] — naming patterns
- [[client-repo-structure]] — detailed folder layout pattern
