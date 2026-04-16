---
tags: [concept, pattern, repo, structure, convention]
aliases: [client folder layout, repo structure pattern]
sources: [clients repo __TEMPLATE_ACCOUNT/, root directory structure]
created: 2026-04-16
updated: 2026-04-16
---

# Client Repo Structure

The standard folder layout for each client in the [[clients-repo]]. Defined by `__TEMPLATE_ACCOUNT` and followed by all 19 active clients.

## Standard Layout

```
CLIENT_NAME/
├── eclipse/
│   ├── account.json              # Account-level Eclipse configuration
│   ├── capacity.json             # Capacity/dataset allocation
│   ├── connections/              # One JSON per data source (auth + endpoint)
│   │   ├── source_a.json
│   │   ├── source_b.json
│   │   └── ...
│   └── templates/                # One JSON per data pull definition
│       ├── source_a/             # Grouped by connection/source
│       │   ├── table_1.json
│       │   └── table_2.json
│       ├── source_b/
│       │   └── ...
│       └── supplement/           # Reference data (CSV files, lookups)
│           ├── calendar.json
│           ├── currency.json
│           └── ...
│
├── snowflake/
│   ├── warehouse/                # Star schema SQL definitions
│   │   ├── shared_dim_*.sql      # Shared dimensions
│   │   ├── *_dim_*.sql           # Domain dimensions
│   │   ├── *_fct_*.sql           # Fact tables
│   │   ├── extract_*.sql         # Flattened exports
│   │   └── shared_fct_*.sql      # Shared facts
│   ├── report_common/            # BI-ready pre-aggregated views
│   │   ├── DEFAULT_DEFAULT.sql   # Always present
│   │   └── RETAIL_*.sql          # Retail report views (varies by client)
│   └── data_share/               # Snowflake-to-Snowflake sharing (optional)
│       └── warehouse.sql
│
├── scripts/                      # Utility scripts (optional)
│   └── *.py
│
├── notes/                        # Project notes, planning docs (optional)
│   └── *.md
│
└── _testing/                     # Test files (gitignored in some branches)
    └── *.md
```

## Connection JSON Pattern

```json
{
  "connection_name": "source_name",
  "connection_type": "rest_api | sql_server | snowflake | csv | ...",
  "server": "hostname_or_url",
  "user": "username",
  "password": "password_or_token",
  // ... source-specific fields (refresh_token, client_id, api_key, etc.)
}
```

## Template JSON Pattern

Templates define data pulls. Key fields:
- Source table/endpoint/report name
- Column list or field mapping
- Filters (date ranges, `min_date`)
- Scheduling parameters
- Destination mapping (which Snowflake table to populate)

Templates reference their connection by name and are grouped in subdirectories matching the connection source.

## Supplement Convention

The `supplement/` template directory holds reference data that doesn't come from live APIs:
- Calendars, currencies, exchange rates
- Budget files, forecast files
- Channel maps, marketplace names, company names
- State/country reference data

These are typically CSV-based connections.

## Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Client directory | UPPER_SNAKE_CASE | `GEP`, `FUSION_92`, `KIT_ACE` |
| Connection file | lowercase_underscored.json | `amazon_seller_central.json` |
| Template directory | lowercase_underscored | `sellercloud_sql/` |
| Template file | lowercase_underscored.json | `all_orders_report.json` |
| Warehouse SQL | lowercase_underscored.sql | `sales_fct_orderline.sql` |
| Report common SQL | UPPER_SNAKE_CASE.sql | `RETAIL_DAILY_SALES_FACT.sql` |

## Client Sizes (by complexity)

| Tier | Clients | Connections | Templates | Warehouse SQL |
|------|---------|-------------|-----------|---------------|
| Large | [[GEP]], KIT_ACE | 14-16 | 50-62 | 25-37 |
| Medium | [[fusion92]], DISH_DUER, TERRAYN | 10-13 | 30-60 | 10-23 |
| Small | BOOK_DEPOT, RAIN_CITY, ASPIRE_NORTH | 4-8 | 10-40 | 5-10 |
| Minimal | DROP_IN, HEARTLAND_DENTAL | 1-2 | 1-2 | 0-1 |
| Internal | ALDC_ENG, ALDC_FINANCE, ALDC_LIBRARY | 5-12 | 15-30 | 4-16 |

## Special Directories

- `__TEMPLATE_ACCOUNT` — the gold standard reference. Check here when unsure about structure.
- `__REPORT_COMMON_VIEWS` — shared retail view templates used across clients
- `CORE_DEV` — account-level secrets and configuration templates
- `PUBLIC_LIBRARY` — public API connections (weather, stocks, exchange rates)

## See Also

- [[clients-repo]] — the repo overview
- [[Eclipse]] — how connections and templates work
- [[star-schema-convention]] — warehouse SQL naming patterns
