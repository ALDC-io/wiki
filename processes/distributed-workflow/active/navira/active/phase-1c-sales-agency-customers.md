---
tags: [workflow, navira, phase-1c, sales, agency, amazon-sp-api, multi-tenant, priority-1]
aliases: [Navira Phase 1C, Sales Agency Customers]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-28
---

# Phase 1C — Sales Data: Agency Customers

**Priority:** 1 · **Interfaces:** 2 · **Status:** Not Started

## Objective

Extend the data warehouse to ingest sales and inventory data from agency customers' Amazon Seller Central accounts. Enables Navira to provide data-driven reporting and advisory services to clients while maintaining strict data isolation between tenants.

## Interfaces — Build Order

| # | Interface | Notes |
|---|---|---|
| 1 | **Seller Central (Sales)** | Orders, order items, returns, settlements — align to existing Navira Sales Data schema |
| 2 | **Seller Central (Inventory)** | FBA inventory levels, inbound shipments, stranded inventory, restock recommendations |

## Suggested Approach

Extend existing Amazon US pattern with multi-account support.

## Prerequisites

- [ ] **Resolve I-1:** Determine whether existing private SP-API app (partner `A3VJEVLAWT2I1E`) can be upgraded to public, or whether a new app registration is required — see [[navira-credentials-access]] § "ALDC to Investigate First"
- [ ] Amazon SP-API **public app** registered and approved (2–4 week lead time — start after I-1 resolved)
- [ ] Tenant isolation strategy decided (CC5 / Q3 below)
- [ ] Legal / Data Processing Agreement template for agency customers
- [ ] Understanding of current Sellercloud/Amazon US integration (Production)

## High-Level Requirements

- **Multi-tenant architecture:** Each customer's data isolated — no cross-tenant leakage in queries, dashboards, or exports
- **SP-API integration:** Amazon Selling Partner API for both sales orders and FBA inventory
- **Onboarding workflow:** Standardized process to connect a new customer (OAuth grant, marketplace selection, initial backfill)
- **Sales scope:** Orders, order items, returns, settlements
- **Inventory scope:** FBA levels, inbound shipments, stranded inventory, restock recommendations
- **Per-customer refresh cadence:** Configurable (some need hourly inventory, others daily)
- **Offboarding:** Data removal policy when an agency customer leaves

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q1 | How many agency customers at launch vs 12 months out? | Self-serve onboarding vs manual provisioning |
| Q2 | Will Navira register an SP-API app that customers OAuth into, or will each provide their own tokens? Existing registration? | Auth flow design, Amazon app store listing, security review |
| Q3 | Tenant isolation in Snowflake — separate schemas per customer, shared schema with tenant_id, or separate databases? | Query performance, RLS complexity, cost, cross-customer aggregates |
| Q4 | Existing Sales Data Navira ingests Amazon US via Sellercloud. For agency customers who also sell on Amazon US — same schema or parallel? | Extension vs separate system |
| Q5 | Will agency customers get dashboard access (PBI/Eclipse) or periodic reports only? | BI licensing, dashboard templating, security model |

## Dependencies

| Dependency | Detail |
|---|---|
| **Amazon SP-API App Registration** | Must be approved before customer onboarding. 2–4 week review. |
| **Existing Amazon US Pipeline (Production)** | Understanding informs extend vs parallel-build decision. |
| **Legal / DPA** | Agency customer contracts must authorize data ingestion and storage. Template needed before first onboarding. |

## Acceptance Criteria

- [ ] New agency customer connected and producing data within **1 business day**
- [ ] **Zero cross-tenant data leakage** (verified by isolation test suite)
- [ ] Sales data matches Seller Central reports within **1% variance**
- [ ] Inventory snapshots current within configured refresh cadence
- [ ] Customer offboarding completely removes all stored data
- [ ] Monitoring dashboard shows per-customer ingestion health

## See Also

- [[navira/README|Navira Roadmap]]
- [[navira-credentials-access]] — SP-API credential tracking
- [[navira-dashboard-recommendations]] — D8 Marketplace Expansion
