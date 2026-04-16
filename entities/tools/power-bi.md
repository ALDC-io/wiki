---
tags: [entity, tool, power-bi, reporting, visualization]
aliases: [Power BI, PBI]
sources: [clients repo report_common/ directories, Obsidian vault notes]
created: 2026-04-16
updated: 2026-04-16
---

# Power BI

ALDC's reporting and visualization layer. Power BI models consume `REPORT_COMMON` views from [[Snowflake]], which are pre-aggregated for optimal performance.

## How Power BI Connects to Snowflake

Power BI models import data from Snowflake `REPORT_COMMON.*` views. These views are specifically designed as the PBI consumption layer — pre-aggregated, denormalized, and optimized for the model's grain.

### Report Common View Types

Defined in `__REPORT_COMMON_VIEWS` and per-client `snowflake/report_common/` directories:

| View Pattern | Purpose | Used By |
|-------------|---------|---------|
| `DEFAULT_DEFAULT` | Baseline reporting view | All clients |
| `RETAIL_DAILY_SALES_*` | Daily sales (CONFIG, DATE, FACT, GLOSSARY, LOCATION) | GEP, KIT_ACE, DISH_DUER, RAIN_CITY |
| `RETAIL_CUSTOMER_VALUE_*` | Customer analytics (ACQUISITION, CUSTOMER, DATE, FACT, ITEM, LOCATION, SUMMARY) | KIT_ACE, RAIN_CITY |
| `RETAIL_ITEM_ATTRIBUTE_*` | Product attributes (DATE, FACT, ITEM, LOCATION) | KIT_ACE, DISH_DUER |
| `RETAIL_KPI_MANAGER_*` | KPI dashboards (CONFIG, DATE, GLOSSARY, LOCATION, SALES_FACT, TRAFFIC) | KIT_ACE, DISH_DUER |
| `RETAIL_PRODUCT_MANAGER_*` | Product management (DATE, FACT, ITEM) | KIT_ACE |
| `RETAIL_INVENTORY_PLANNER_*` | Inventory planning (COMBINED, DATE, INVENTORY, ITEMS, LOCATION, SALES) | KIT_ACE |
| `RETAIL_PURCHASE_FREQUENCY_*` | Purchase frequency (CUSTOMER_SALES_LOCATION, SALES) | KIT_ACE |
| `RETAIL_ECOMMERCE_FLASH_*` | E-commerce flash reports (DATE, FACT) | KIT_ACE, RAIN_CITY |
| `RETAIL_BASKET_ANALYSIS` | Market basket analysis | KIT_ACE |

### GEP-Specific Report Common Views
- `DEFAULT_DEFAULT.sql`
- `RETAIL_DAILY_SALES_DATE.sql`
- `RETAIL_DAILY_SALES_FACT.sql` — unions budget and actual sales data
- `RETAIL_DAILY_SALES_LOCATION.sql`

## Power BI Workspaces (GEP)

| Workspace | Snowflake Environment | Branch |
|-----------|----------------------|--------|
| GEP Test Models | `TEST_DG1_GEP` | `GEP/user-testing` |
| Production | `PROD_DG1_GEP` | `main` |

## Model Refresh

Power BI model refreshes are **manual** — they do not auto-trigger on Snowflake data changes.

Refresh process:
1. Navigate to the workspace in Power BI Service
2. Find the dataset/semantic model
3. Click refresh (or schedule a refresh)
4. Monitor refresh status for completion/errors

After any Snowflake warehouse change, the PBI model must be manually refreshed to pick up new data or schema changes.

## Common Issues

- **Stale data**: PBI model not refreshed after Snowflake deploy — always refresh after deploying warehouse changes
- **Schema mismatch**: If Snowflake view columns change, PBI model may error on refresh — update the PBI model to match
- **Date columns**: Some date columns may not import correctly into PBI models — may need research per ticket (noted in [[GP-208]] to-do)

## Deployment Workflow

See [[gep-snowflake-pbi-deployment]] for the full end-to-end deployment including PBI refresh steps.

## See Also

- [[Snowflake]] — data source
- [[star-schema-convention]] — warehouse naming that feeds report_common views
- [[data-pipeline-flow]] — PBI's position in the full pipeline
- [[GEP]] — primary client using PBI
