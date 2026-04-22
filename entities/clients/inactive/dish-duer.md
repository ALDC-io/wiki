---
tags: [entity, client, dish-duer, retail, apparel, sap, shopify]
aliases: [DISH_DUER, Dish & Duer, Dish and Duer]
sources: [Confluence CLIEN/909115393, Confluence CLIEN/932872202, Confluence CLIEN/1033928705, Confluence CLIEN/1033732113, Confluence CLIEN/936148993, Confluence CLIEN/1082687489, Confluence CLIEN/1090682881, Confluence CLIEN/1088880641]
created: 2026-04-18
updated: 2026-04-18
---

# DISH_DUER (Dish & Duer Apparel Inc.)

> Note: DISH_DUER has a dedicated Confluence space (CDD) which has not yet been migrated. These pages are from the general CLIEN space and represent the 2022–2023 discovery and build phase.

## Client Overview

| Field | Value |
|---|---|
| Full Name | Dish & Duer Apparel Inc. |
| Short Code | DISH_DUER |
| Account ID | `5d556742` |
| Primary Contact | Calvin Roex (`calvin@shopduer.com`) |
| Technical Contact | Quinton Wong (`quinton@shopduer.com`) |
| Address | 1757 W 4th Ave Vancouver, BC V6J 1M2 |
| Industry | Retail Apparel |
| Costing Method | FIFO |
| Tier | XS |
| Tenant Location | Canada |
| Reporting Providers | Eclipse Dashboards, Eclipse Aperture, Power BI Embedded |
| Discovery Period | 2022-05-11 to 2022-06-30 |
| Subscription Period | 2022-07-01 to 2023-06-30 (1 year) |
| Total Credits | 15 |

## Discovery Phase — Required Reports

**Phase 1:**

| Report | Credits | Notes |
|---|---|---|
| Sales Excel Model | 3–6 | Custom; credits depend on user count + complexity. Includes booked vs shipped, budget/forecast/reforecast. |
| Daily Sales | 1 | Standard |
| Product Analysis | 1 | Standard; development underway |
| KPI Manager | 1 | Trialing door trackers/TOF in Calgary (DOR) |
| Customer Value | 1 | Standard |

**Phase 2+:**
- Daily Shop Planner (1 credit) — Calvin to discuss with retail manager
- Inventory — no Phase 1 requirement

## Finance Model

### Data Sources (SAP + Shopify)

DISH_DUER uses SAP as the primary ERP. Shopify handles ecommerce; a middleware integration syncs Shopify → SAP for shipments.

**P&L and finance reports sourced from:**
- `SAP_CA.*` and `SAP_USA.*` — GL tables, cost centre, COGS, trial balance
- Shopify — Order, Order Lines, Refunds, Returns
- Budget CSVs — one file per location per fiscal year

**Key finance reports in current use:**
- Departmental P&L (from SAP cost centre; tabs per department + consolidated)
- Consolidated P&L (trial balance; combined manually with GL + departmental listings)
- Combined Financial Statements (P&L + balance sheet)
- Cost Centre Report (GL + sales channel from SAP, back-end by Quinton)
- Gross Margin (GM) Report (discount group from Shopify + SAP department GL budgets)
- COGS Report (~80% complete in SAP; realigns COGS to possession date)

**Supply chain flow (COGS context):**
Pakistan factory → Saltbox (3PL/crossdocking) → Wholesale OR Vancouver (Retail/Ecomm). Wholesale doesn't hit inventory; DTC hits inventory at Vancouver. Transfer Out from Pakistan records COGS, but ownership doesn't transfer to Duer until US crossdock.

### Eclipse Connections & Templates (Finance Model Production Deployment)

**Connections:**
- `csv_shape.json`, `csv_financial_budget.json`, `csv_account.json`

**Templates:** finance_ca/usa_ojdt, financial_currency, financial_version, geography_country, kpi_periodicity, account_csv, finance_ca/usa_oprc, finance_ca/usa_oact, finance_ca/usa_jdt1

**Snowflake objects deployed:**
- Dimensions: `finance_dim_account`, `finance_dim_account_flat`, `finance_dim_subsidiary`, `finance_dim_subsidiary_flat`, `finance_dim_cost_centr`, `finance_dim_department`, `shared_dim_date2`, `finance_dim_version`, `shared_dim_currency`, `shared_dim_periodicity`, `finance_dim_transaction`
- Facts: `shared_fct_exchange_rate`, `finance_fct_shape`, `finance_fct_budget`, `finance_fct_transaction_line`
- Bridge: `shared_bridge_calendar`

**PBI Deployment:** `finance_model_202301.json` deployed to Prod. Eclipse group with Finance Model access includes: Kanise, Kelly, Quinton, Phoebe, Sean, Karen, John, Mustafa.

## Dimensional Model (Retail)

### Shared Dimensions

**`SHARED_DIM_DATE`**
- Source: `ANALYTICS.ANALYTICS.DIM_CALENDAR`
- Grain: `CALENDARDATE`
- Fiscal calendar (Year/Quarter/Month/Week/Date). Finance moving from standard to retail 4/5/4 calendar; week 53 handling TBD. Budget weeks run Sunday–Saturday.

**`SHARED_DIM_ITEM`**
- Source: `SAP_CA.OITM`, Shopify PRODUCT/PRODUCT_VARIANT, SAP ARGNS_* attribute tables
- Grain: `OITM.ITEMCODE`
- Hierarchies: Gender > Division (Womens/Mens) > Model (Jogger/Pant/etc) > Style > Color
- Key fields: ITEM_KEY, ITEM_CODE, GENDER, DIVISION, FABRIC, FIT, MODEL_CODE/NAME, COLOR, SIZE, SIZE_VARIANT, STYLE_CODE, SHOPIFY IDs, SEASON, PRODUCT_LIFECYCLE, REPLENISHMENT_TYPE, CHANNEL_ASSORTMENT
- Note: Not all PRODUCT_VARIANT entries have SKU values; use Canada OITM table for now.

**`SHARED_DIM_LOCATION`**
- Source: `SAP_*.OCRD`, `SAP_*.OSLP`, `SHOPIFY_*.LOCATION`, `SUPPLEMENT.SHOPIFY_LOCATION_MAP`
- Grain: LOCATION_ID
- Channel mapping: `SCAE%`/`SUSE%` = Ecommerce; `SCAR%`/`SUSR%` = Retail; `C%` = Wholesale
- Hierarchy: DTC (Retail + Ecommerce) / Wholesale (by Territory/Country)
- Retail square footage: Denver 900, Calgary 2000, Vancouver 2000, Toronto 2200, LA 2000
- Account type tiers: Key Account, VIP, Gold, eCommerce, Silver, Bronze, New, Point of Sale

**`SHARED_DIM_WAREHOUSE`**
- Source: `SAP_*.OWHS`
- Grain: `WHSCODE`
- Key fields: INSTANCE_PREFIX, WAREHOUSE_ID, NAME, PARENT_ID, TYPE, ADDRESS fields

### Finance Dimensions

| Dimension | Description |
|---|---|
| Account | Names + parent-child hierarchy; requires manual mapping CSV for GL → Financial Statement Rollup |
| Organizational Entities | Hierarchy: Legal Entity > Department > Cost Centre; supports CA/US subsidiaries |
| Version | Budget version tracking (annual with Q2/Q3/Q4 updates) |

### Facts

**`SALES_FCT_SALE` / `SALES_FCT_ORDERLINE`**
- Sources: SAP ORDR/RDR1, ODLN/DLN1, OINV/INV1, ORDN/RDN1; Shopify Orders/Refunds
- Key dates: Delivery.Docdate (picked), custom shipped date, Invoice.Docdate
- Currency handling: Transaction / Subsidiary / Consolidated (CAD)
- Amounts: Gross (`pricebefdi`), Markdowns, Discounts (`totalsumsy`), Net (`linetotal`), Returns
- Retail note: No delivery document — straight to invoice; returns recorded differently than wholesale.

**`FINANCE_FCT_BUDGET`**
- Sources: Budget CSVs (one file per location per fiscal year)
- Grain: Date, Location; wholesale accounts budgeted to individual leaf level

**`SHARED_FCT_EXCHANGE_RATE`**, **`FINANCE_FCT_TRANSACTION_LINE`**, **`FINANCE_FCT_SHAPE`** — supporting finance facts.

## Finance Model — Visible Fields (PBI)

Key visible measures (end-user facing):
- Actual - Ledger - Amount / Balance
- Budget - Ledger - Amount / Balance
- Filter Assistance (Finance)

Key visible dimension fields: Account Category/Description/Hierarchy/ID/Name/Number/Reporting Group; Cost Center ID/Name/Type; Subsidiary Hierarchy/ID/Name/Type; Transaction ID/Type/dates; Periodicity Name/Type.

Report Metadata fields (visible in all models): Deploy Date, Environment, Last Refresh Time, Report Name/Version/Status, Owner contacts.

## Phase 1 Testing

- Test users: Calvin, Quinton, Michael, Kanise, Ariana
- USA data needed in test environment
- Account name in Eclipse: "Duer"
- Related entity: Pimloco Performance Apparel Ltd.

**Phase 1 KPIs:** AOV, UPT, AUR, Sales per sqft, % to plan/budget.

## See Also

- [[kit-ace]] — similar retail client (also KIT_ACE Confluence space CKA)
- [[star-schema-convention]] — ALDC dimensional model conventions
- [[periodicity]] — SHARED_DIM_PERIODICITY used in Finance Model
- [[nextcloud]] — client tenant access (Calvin, Kanise, Quinton, Phoebe, Kelly)
- [[power-bi]] — PBI model setup and Excel model access
