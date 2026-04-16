---
tags: [entity, client, gep, navira, e-commerce]
aliases: [GEP, Navira, Global E-commerce Partners]
sources: [clients repo GEP/ directory]
created: 2026-04-16
updated: 2026-04-16
---

# GEP (Navira)

E-commerce analytics client. Primary focus: Amazon (US/UK/CA), SellerCloud, and Galactica data consolidated into a [[Snowflake]] star schema with [[Power BI]] reporting.

## Environments

| Branch | Snowflake | Power BI |
|--------|-----------|----------|
| `feature/*` | none | none |
| `GEP/development` | none | none |
| `GEP/user-testing` | `TEST_DG1_GEP` | GEP Test Models workspace |
| `main` | `PROD_DG1_GEP` | Production workspace |

Code merge does NOT auto-deploy. [[Snowflake]] and [[Power BI]] deploys are manual. See [[gep-snowflake-pbi-deployment]] for the full runbook.

## Data Sources (Eclipse Connections)

14 Eclipse connections in `GEP/eclipse/connections/`:

| Connection | System | Auth Type |
|-----------|--------|-----------|
| amazon_seller_central | Amazon Seller Central API | OAuth (refresh_token) |
| amazon_ads | Amazon Advertising API | OAuth (refresh_token) |
| sellercloud_rest | SellerCloud REST API | Username/password |
| sellercloud_sql | SellerCloud SQL Server | SQL auth (VPN-gated) |
| sql_server | Galactica SQL Server | SQL auth |
| budget | CSV file (budget data) | File-based |
| currency | CSV file (currency rates) | File-based |
| forecast_with_type | CSV file (forecasting) | File-based |
| csv_account_managers | CSV supplement | File-based |
| csv_sku_kits | CSV supplement (kit definitions) | File-based |
| sellercloud_channel_map_csv | CSV supplement | File-based |
| state_names | CSV reference data | File-based |
| supplement_company_name | CSV supplement | File-based |
| supplement_marketplace_name | CSV supplement | File-based |

## Eclipse Templates

62 templates organized by connection source:

- **Amazon Seller Central** (11): orders, inventory, FBA returns, inbound/outbound, sales & traffic (US + CA child ASIN variants), merchant/open listings, seller
- **Amazon Ads** (5+): brand, portfolio, sponsored brands/display/products campaigns + reports
- **SellerCloud REST** (10): brand, customer, inventory, orders, product, purchase_order, RMA, vendor, warehouse
- **SellerCloud SQL** (16): brand, inventory PANDL, manufacturer, order/orderitem/orderpayment, product (+ properties), purchase/purchaseitem/receive, vendor, warehouse
- **Supplements** (10): budget, company name, currency, financial currency, forecast, marketplace, channel map, SKU kits, account managers, state names
- **Calendar**: calendar.json

## Snowflake Warehouse (Star Schema)

37 SQL views in `GEP/snowflake/warehouse/`:

### Dimensions (shared_dim_*)
| View | Purpose |
|------|---------|
| shared_dim_date | Date dimension |
| shared_dim_product / _base | Product master (MASTER_SKU → PRODUCT_KEY via SHA2) |
| shared_dim_customer | Customer dimension |
| shared_dim_brand | Brand dimension |
| shared_dim_marketplace | Marketplace dimension |
| shared_dim_location | Location/geography |
| shared_dim_currency / _company_map | Currency + company mapping |
| shared_dim_vendor | Vendor dimension |
| shared_dim_warehouse | Warehouse dimension |
| shared_dim_periodicity | Time period granularity |

### Facts (*_fct_*)
| View | Purpose |
|------|---------|
| sales_fct_orderline | Core sales fact — all order lines |
| sales_fct_seller_cloud_orderline | SellerCloud-specific order lines |
| sales_fct_amazon_orderline | Amazon-specific order lines |
| sales_fct_budget | Budget fact |
| sales_fct_cost / _estimates / _history | Cost tracking |
| purchasing_fct_balance / _historical | Purchase order balance |
| inventory_fct_balance / _historical | Inventory balance (currently unused — [[GP-208]] rebuilds this) |
| marketing_fct_activity | Marketing/ads performance |
| traffic_fct_activity | Traffic/sessions data |
| shared_fct_exchange_rate | FX rates |

### Extracts (extract_*)
| View | Purpose |
|------|---------|
| extract_product | Product extract for reporting |
| extract_sales_by_day | Daily sales aggregate |
| extract_sales_detail | Detailed sales extract |
| extract_fba_manage_inventory | FBA inventory extract |
| extract_inventory_current | Current inventory snapshot |
| extract_warehouse_metadata | Warehouse metadata |

### Marketing Dimensions
- marketing_dim_platform, marketing_dim_campaign
- sales_dim_order / _base

### Report Common Views
- DEFAULT_DEFAULT.sql
- RETAIL_DAILY_SALES_DATE/FACT/LOCATION.sql

## Data Share

GEP has a Snowflake data share setup exposing warehouse views to external consumers. Pattern documented in `GEP/snowflake/data_share/warehouse.sql`.

## Active Tickets

- [[GP-208]] — Inventory feed ingestion & modelling (in progress)
- [[GP-207]] — Prod to test data share setup (completed)
- [[GP-204]] — Add marketplace CSV columns for Amazon and DTC fee (completed)
- [[GP-203]] — Add traffic for Canada (completed)
- [[GP-200]] — Amazon UK addition to orders (completed)
- [[GP-197]] — (historical)
- [[GP-169]] — (historical)

## See Also

- [[clients-repo]] — repo structure and conventions
- [[star-schema-convention]] — ALDC warehouse naming
- [[data-pipeline-flow]] — Eclipse → Snowflake → PBI pipeline
- [[Eclipse]] — connector platform
- [[Snowflake]] — data warehouse
- [[Power BI]] — reporting layer
