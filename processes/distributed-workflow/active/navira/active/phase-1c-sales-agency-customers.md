---
tags: [workflow, navira, phase-1c, sales, agency, amazon-sp-api, multi-tenant, priority-1]
aliases: [Navira Phase 1C, Sales Agency Customers]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-30
---

# Phase 1C — Sales Data: Agency Customers

**Priority:** 1 · **Interfaces:** 2 · **Status:** Tickets created — S4/S5

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

- [x] **~~Resolve I-1~~:** **RESOLVED 2026-05-08.** Amazon does not support converting private → public. New public app registration required via Solution Provider Portal (SPP). Identity verification ~20 min, approval ~1–2 weeks.
- [ ] Amazon SP-API **public app** registered on SPP and approved (~1–2 week lead time — register now)
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
| **Amazon SP-API App Registration** | Must be approved before customer onboarding. ~1–2 week review via SPP. I-1 resolved — new app required (private cannot convert to public). |
| **Existing Amazon US Pipeline (Production)** | Understanding informs extend vs parallel-build decision. |
| **Legal / DPA** | Agency customer contracts must authorize data ingestion and storage. Template needed before first onboarding. |

## Acceptance Criteria

- [ ] New agency customer connected and producing data within **1 business day**
- [ ] **Zero cross-tenant data leakage** (verified by isolation test suite)
- [ ] Sales data matches Seller Central reports within **1% variance**
- [ ] Inventory snapshots current within configured refresh cadence
- [ ] Customer offboarding completely removes all stored data
- [ ] Monitoring dashboard shows per-customer ingestion health

## Jira Tickets

| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-230 | SP-API Registration (new public app via SPP) | S4 | I-1 resolved — ~1–2 week approval. Register now. |
| GP-231 | Seller Central Multi-Tenant | S5 | Multi-tenant sales + inventory ingestion |

## Boot Prompts

### GP-230 — SP-API App Registration & Multi-Tenant Design

````
You are working on **GP-230** (Amazon SP-API App Registration & Multi-Tenant Design).

**Goal:** Investigate whether the existing SP-API app can serve agency customers, submit registration if needed, and design the multi-tenant Snowflake isolation strategy.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` — § "ALDC to Investigate First" for the I-1 investigation (existing private SP-API app, partner `A3VJEVLAWT2I1E`)
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\phase-1c-sales-agency-customers.md` — full Phase 1C context
4. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\connectors\amazon-ads.md` — existing Amazon OAuth patterns
5. Read `C:\Users\PaulRussell\repos\wiki\concepts\patterns\sandbox-feature-delivery.md` — Snowflake isolation patterns (inform multi-tenant design)

**I-1 RESOLVED (2026-05-08):**
The existing SP-API app (partner `A3VJEVLAWT2I1E`) is private and **cannot** be converted to public. Amazon does not offer an upgrade path. A new public app must be registered via the Solution Provider Portal (SPP) at developer.amazonservices.com/solution-provider-portal. Identity verification ~20 min, approval ~1–2 weeks. SPP replaced Seller Central for developer management as of Aug 31, 2025.

**Multi-tenant design decision:**
- Option A: Separate schemas per customer (`AGENCY_<CUSTOMER>`) — safest, auditable
- Option B: Shared schema with `tenant_id` + Snowflake RLS — cheapest, scales better
- Option C: Separate databases per customer — most isolated, most expensive
Recommend based on expected customer count (ask Navira via Lori — Q1).

**Deliverables:**
1. ~~I-1 investigation result~~ — DONE: new app required
2. SP-API public application submitted on SPP
3. Multi-tenant isolation design document
4. Legal/DPA template status check

**Scope:** Investigation + design + registration submission. Do NOT build connectors — that's GP-231.
````

## See Also

- [[navira/README|Navira Roadmap]]
- [[navira-credentials-access]] — SP-API credential tracking
- [[navira-dashboard-recommendations]] — D8 Marketplace Expansion
