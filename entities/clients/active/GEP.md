---
tags: [entity, client, gep, navira, e-commerce]
aliases: [GEP, Navira, Global E-commerce Partners]
sources: [clients repo GEP/ directory, CGEP/1233092873, CGEP/1233289293]
created: 2026-04-16
updated: 2026-04-27
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

## ALDC Team

ALDC team members on the GEP engagement (source: CGEP/1233092873, 2024-03-27):

- John Moran
- Sean O'Grady
- Karen Prete
- Aaron Stryd

> GEP-side team members were not documented in the Confluence space at time of ingestion.

## Inventory Subject Area

Subject area scope page for GEP inventory data (source: CGEP/1233289293). Related Jira: CUST-761.

### Participating Objects

| Object | Type |
|--------|------|
| Fact Inventory Balance | Fact |
| Fact Purchase Order | Fact |
| Dimension Product | Dimension |
| Dimension Warehouse | Dimension |
| Dimension Vendor | Dimension |
| Dimension Purchase Order | Dimension |

> **Gap:** `Dimension Purchase Order` is listed as a participating object in the Confluence subject-area page but is not documented in the [[GEP]] § Snowflake Warehouse section above. The view may not yet exist or may be tracked under a different name. See also [[GP-208]] (inventory rebuild in progress).

## Client Contact & Contract

Source: Confluence CLIEN/1173913601 (GEP Onboarding Checklist, 2024-01-12).

| Field | Value |
|---|---|
| Full Name | Global Ecom Partners |
| Primary Contact | Heather Tabor (Chief Operating Officer) |
| Email | htabor@globalecompartners.com |
| Phone | 770-639-8331 |
| Address | 7167 Cross County Rd, Suite A, North Charleston, SC 29418 |
| Time Zone | EST |
| Industry | Retail |
| Contract Start | January 1, 2024 |
| Minimum Fee | $3,500/month |
| Short Code | GEP |
| Tenant Location | Canada |
| Tier | XS |
| Invoice Day | 1 |
| Jira Startup | CUST-701 |

## Excel Model Scope

Source: Confluence CLIEN/1167196168 (GEP overview page, 2023-12-22).

Proposed Excel model feature set combining all dimensions and facts:

- KPI Report
- Order Summary
- Promo Recaps
- Long-term storage fees
- Excess Inventory
- No Sales
- Lost Buy Box
- Open to Buy

## Service Requests (as of 2024-12)

Source: Confluence CLIEN/1458634759.

| SR | Title | Key Outcomes | Status |
|---|---|---|---|
| REQ-397 | Tool Additions Rd 2 | Amazon Order # field; custom margin calc; Product Condition via SQL Server | NOT STARTED |
| REQ-402 | Tool Additions Rd 3 | Remove Order Problem; Other Marketplace Ad Spend; Inventory Bins; Amazon MX/CA | IN PROGRESS (4h approved) |
| REQ-415 | Tool Additions Rd 4 | 120-day no-margin logic; SKU Dept/Category classification; Subscribe & Save; Search Query Performance | IN PROGRESS (4h approved) |
| REQ-430 | Tool Additions Rd 5 | Order Exception | NOT STARTED |
| REQ-451 | Tool Additions Rd 6 | FBA product age indicator | NOT STARTED |
| REQ-441 | Credits | Brand credit flag (Y/N, date, RTO indicator) | NOT STARTED |
| REQ-422 | Periodicity | Show YTD instead of full-year for previous year | NOT STARTED (may already exist) |
| REQ-453 | FBA Inventory (Daytona) | Update FBA inventory logic | NOT STARTED |
| REQ-404 | QBO Connection | QuickBooks Online connection | NOT STARTED (scope unknown) |
| REQ-438 | Daily Sales Dashboard | Add Marketplace Name filter (post REQ-402 Marketplace Name) | NOT STARTED |

## NetSuite Integration Context

Source: Confluence CLIEN/1302986753 (NetSuite Scoping Call, 2024-06-17).

Attendees: Johanna, Lindsey, Shannon, Christina Taylor, Cory Hanna, Sean, Karen.

**Problem:** NetSuite and Flight Check are not connected — Fusion92 team manually enters data in both systems.

**Goal:** Invoice details (Date/Number/Amount) entered in Flight Check push to NetSuite to auto-generate an invoice — single-entry workflow.

**Key constraints:**
- Client invoices are billed per campaign code, up-front — disconnect from vendor invoices (billed after ads run)
- Vendor invoices (e.g. Google) cover multiple clients and campaign lines
- Next steps: Christina + Sean to align on platform-level detail; Flight Check ID + NetSuite media project as line-level inputs

## Navira Integration Roadmap

A comprehensive integration roadmap covering 17 new data interfaces across 6 phases is tracked at [[processes/distributed-workflow/active/navira/README|Navira Workflow Hub]]. Source: 5 interactive HTML documents in `eclipse_exp/frontend/public/navira/`. Includes credentials tracker, 8 dashboard recommendations, and Phase 1A data dictionary.

Current production interfaces: Sellercloud, Amazon US, Shopify, Corporate Data (7 tables). Amazon UK in progress. New interfaces span Marketing (Google Ads, Facebook, TikTok, Email, Amazon PPC UK/CA), Agency Sales (multi-tenant Seller Central), Inventory, Competitor (SmartScout), and Unstructured Data.

## See Also

- [[processes/distributed-workflow/active/navira/README|Navira Workflow Hub]] — active integration roadmap + phase workflows
- [[clients-repo]] — repo structure and conventions
- [[star-schema-convention]] — ALDC warehouse naming
- [[data-pipeline-flow]] — Eclipse → Snowflake → PBI pipeline
- [[Eclipse]] — connector platform
- [[Snowflake]] — data warehouse
- [[Power BI]] — reporting layer
- [[periodicity]] — periodicity dimension and DAX patterns used in GEP model
- [[dax-media-app]] — Flight Check app (referenced in NetSuite scoping context)
