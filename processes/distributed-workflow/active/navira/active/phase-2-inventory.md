---
tags: [workflow, navira, phase-2, inventory, sellercloud, purchasing, priority-2]
aliases: [Navira Phase 2, Inventory Data]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-30
---

# Phase 2 — Inventory Data

**Priority:** 2 · **Interfaces:** 2 · **Status:** Tickets created — Backlog

## Objective

Bring purchasing and inventory data into the warehouse to enable demand forecasting, inventory health analysis, stockout risk alerting, and margin analysis combining COGS (purchasing) + revenue (sales) + ad spend (marketing).

## Interfaces — Build Order

| # | Interface | Rationale |
|---|---|---|
| 1 | **Sellercloud (Inventory)** | Connector already exists for Sales Data. Extending for inventory endpoints is incremental and delivers immediate value (stock levels, warehouse locations). |
| 2 | **Navira Purchasing System** | Net-new connector to internal system. Requires discovery of API/DB access. Delivers COGS for full margin analysis. |

## Suggested Approach

Leverage existing Sellercloud connector; new connector for purchasing.

## High-Level Requirements

- **Inventory snapshots:** Point-in-time levels by SKU, warehouse, channel (FBA, FBM, 3PL)
- **Purchase orders:** PO number, supplier, SKU, qty ordered, qty received, unit cost, dates, status
- **Receiving data:** Link POs to actual receipts for lead time analysis
- **COGS calculation support:** Landed cost including freight, duties, warehousing fees
- **Stockout risk:** Days-of-supply using current velocity from Sales Data
- **Refresh:** Inventory snapshots minimum daily; purchasing data daily

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q1 | What is the Navira Purchasing System? (Custom app, ERP module, spreadsheet?) API, DB access, or file exports? | Entire integration approach |
| Q2 | Which Sellercloud inventory endpoints needed? (Summary, Warehouse, FBA?) Different rate limits from sales endpoints? | Throttling strategy, separate API user/key |
| Q3 | Which cost components tracked? (Unit cost, freight, customs/duties, insurance, warehousing fees?) Where does each live? | Single-source COGS field or calculated aggregate |
| Q4 | How many warehouses/fulfillment centers? Location-level tracking in Sellercloud? | Schema granularity |

## Dependencies

| Dependency | Detail |
|---|---|
| **Sales Data (Production)** | Stockout risk / days-of-supply needs sales velocity data. |
| **Corporate Data — Item Cost (Production)** | Already live. Clarify overlap with purchasing COGS. |

## Acceptance Criteria

- [ ] Inventory snapshot data matches Sellercloud UI within **1 business day**
- [ ] Purchase orders complete with line-item detail and cost
- [ ] Days-of-supply calculable by joining inventory + sales velocity
- [ ] Margin analysis possible: revenue (sales) − COGS (purchasing) − ad spend (marketing)
- [ ] Historical PO data backfilled to at least **12 months**

## Jira Tickets

| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-232 | Sellercloud Inventory | Backlog | GP-208 closed — artifacts carried forward here |
| GP-233 | Purchasing System & COGS | Backlog | Net-new connector to internal purchasing system |

> **Note:** GP-208 (Inventory feed ingestion & modelling) was closed with its artifacts (data dictionary, Phase 1 schema work) carried forward to GP-232.

## See Also

- [[navira/README|Navira Roadmap]]
- [[navira-dashboard-recommendations]] — D5 Profitability Waterfall
- [[gep-inventory-data-dictionary]] — existing GEP inventory data dictionary (may inform schema)
