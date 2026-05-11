---
tags: [workflow, navira, gep, roadmap, client, e-commerce]
aliases: [Navira Roadmap, Navira Integration, GEP Roadmap]
sources: [eclipse_exp/frontend/public/navira/navira-roadmap.html, eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-05-03
---

# Navira Integration — Workflow Hub

Navira (formerly [[GEP]]) is an e-commerce analytics client. This folder tracks the active delivery of new data interfaces into the Navira DataWarehouse (Snowflake + Power BI + Eclipse/Zeus Chat).

**Source:** 5 interactive HTML documents in `eclipse_exp/frontend/public/navira/` (registered as the `navira-roadmap` app in Eclipse, migration 068). Last updated April 9, 2026.

## Architecture Overview

```
                     ┌─────────────────┐
                     │ Excel Pivot Table│
                     └────────┬────────┘
                              │
┌──────────────┐    ┌────────▼────────┐    ┌──────────────────┐
│  Data Sources │───►│ Navira DW       │───►│ Eclipse          │
│  (7 domains)  │    │ Snowflake + PBI │    │ Dashboards + Zeus│
└──────────────┘    └─────────────────┘    └──────────────────┘
```

## Roadmap — Priority Order

| Phase | Domain | Interfaces | Priority | Status |
|---|---|---|---|---|
| **0** | Prefect Foundation | Framework hardening (6 gaps) + migrate Sellercloud + resolve CC1–CC7 | P0 | **In Progress** — G1–G3/G5 done (GP-213–216, GP-220). Repo fork done (GP-247). Prefect Server validated (GP-243). Snowflake env isolation done (GP-248). Work Pools done (GP-218, E2E blocked on Snowflake staging DB). CI/CD gated pipeline done (GP-217). Next: GP-218 E2E (after Snowflake password reset), Sellercloud migration (GP-219). |
| **1A** | Marketing — Ad Platforms | Google Ads (Amazon + D2C), Facebook Ads, Amazon PPC UK/CA, Target+ | P1 | Tickets created (GP-221, GP-222, GP-223, GP-225, GP-226, GP-227). Sprint S3/S4. |
| **1B** | Marketing — Social & Emerging | TikTok Shops, Creator Connections, Email Campaigns | P1 | Tickets created (GP-228, GP-229). Sprint S5. Needs refinement. |
| **1C** | Sales — Agency Customers | Seller Central (Sales), Seller Central (Inventory) | P1 | Tickets created (GP-230, GP-231). Sprint S4/S5. |
| **2** | Inventory | Sellercloud (Inventory), Navira Purchasing System | P2 | Tickets created (GP-232, GP-233). Backlog. |
| **3** | Competitor | SmartScout | P3 | Tickets created (GP-234). Backlog. Needs refinement. |
| **4** | Unstructured | Email, Meeting Notes, Word Documents | P4 | Tickets created (GP-235). Backlog. Needs refinement. |

### Production (already live)

| Domain | Interfaces | Status |
|---|---|---|
| Sales Data Navira | Sellercloud, Amazon US, Shopify | Live |
| Sales Data Navira | Amazon UK | In Progress |
| Marketing Data Navira | Amazon US PPC (SP, SB, SD) | Live (708K rows, current 2026-04-28) |
| Marketing Data Navira | Amazon CA PPC (SP, SB, SD) | Live (68K rows, current 2026-04-28) |
| Corporate Data | Marketplaces, Products, Companies, Account Managers, SKU Kitting, Item Data, Item Cost | Live |

### Blockers

| Item | Blocker | Owner | Action |
|---|---|---|---|
| ~~Amazon UK PPC~~ | ~~No UK advertising profile authorized~~ **RESOLVED 2026-05-08:** UK Profile ID 1236242149887729 exchanged on live call. All 3 marketplaces (US/UK/CA) confirmed active. | ~~Navira~~ | ALDC to update pipeline config + validate GBP data flow. |

## Jira Ticket Map

All GP tickets created 2026-04-30. See individual phase pages for details.

### Phase 0 — Prefect Foundation
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-213 | E2E Proof (Sprint 0A) | S2 | Done |
| GP-214 | pytest Framework (Sprint 0B) | S2 | Done |
| GP-215 | Logging + CI Pipeline (Sprint 0C) | S2 | Done |
| GP-216 | Account Auto-Discovery (Sprint 0D) | S2 | Done |
| GP-220 | DateWindow Partition (G1) | S2 | Done |
| GP-247 | Fork connector repo → prefect-connectors | S2 | Done |
| GP-248 | Snowflake Environment Isolation (QA/UAT/Prod) | S2 | Done |
| GP-243 | Validate existing Prefect Server | S2 | Done |
| GP-217 | CI/CD Pipeline — Docker & GHCR | S3 | Done |
| GP-218 | QA/Prod Work Pools & Promotion Pipeline | S3 | Blocked (Snowflake password reset — staging DB) |
| GP-246 | Migration Testing Protocol | S3 | To Do |
| GP-219 | Sellercloud Migration (build S2, QA deploy S3) | S2/S3 | To Do |

### Phase 1A — Marketing Ad Platforms
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-221 | Amazon UK PPC OAuth | S3 | BLOCKED |
| GP-222 | Facebook Ads Connector | S4 | To Do |
| GP-223 | Target+ Connector | S4 | To Do |
| GP-237 | Access & Credentials Epic (GP-238–245) | S2+ | Ongoing |
| GP-225 | Unified Marketing Schema Design | S3 | To Do |
| GP-226 | Google Ads Connector | S4 | To Do |
| GP-227 | Historical Backfill | S5 | To Do |

### Phase 1B — Marketing Social & Emerging
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-228 | TikTok/Creator Connections | S5 | To Do |
| GP-229 | Email Campaigns | S5 | To Do |

### Phase 1C — Sales Agency Customers
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-230 | SP-API Registration | S4 | To Do |
| GP-231 | Seller Central Multi-Tenant | S5 | To Do |

### Phase 2 — Inventory
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-232 | Sellercloud Inventory | Backlog | To Do |
| GP-233 | Purchasing System & COGS | Backlog | To Do |

### Phase 3 — Competitor Data
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-234 | SmartScout | Backlog | To Do |

### Phase 4 — Unstructured Data
| Ticket | Summary | Sprint | Status |
|---|---|---|---|
| GP-235 | Discovery & Architecture Design | Backlog | To Do |

---

## Cross-Cutting Concerns (CC1–CC7)

Shared infrastructure decisions that affect ALL phases. Resolved empirically during [[phase-0-prefect-foundation]] by building and validating the actual infrastructure.

| ID | Topic | Question |
|---|---|---|
| CC1 | Ingestion Framework | Shared connector pattern (logging, error handling, retry, scheduling) vs. independent per-project? Recommendation: standardize early — 9 marketing connectors alone justify it. |
| CC2 | Scheduling & Orchestration | What orchestrates ingestion jobs? ([[Prefect]], Snowflake Tasks, cron?) What's already in place for production pipelines? |
| CC3 | Secrets Management | Where are API keys, OAuth tokens stored today? Centralized secrets manager? With 17+ new interfaces, credential management is a real operational concern. |
| CC4 | Monitoring & Alerting | What monitoring exists for production pipelines? Alert destination (Slack, PagerDuty, email)? |
| CC5 | Snowflake Architecture | Current DB/schema/warehouse structure? Naming conventions? Should new interfaces follow existing pattern or restructure? |
| CC6 | Data Quality & Reconciliation | What data quality framework exists? (dbt tests, Great Expectations, custom?) Standardize reconciliation pattern in Phase 1A for all subsequent interfaces. |
| CC7 | Change Management | Schema changes, connector updates, deployments — CI/CD or manual? What environments exist (dev/staging/prod)? |

## Next Steps

1. **Start Phase 0** — harden the Prefect framework (6 gaps) and migrate Sellercloud. This answers CC1–CC7 empirically.
2. **In parallel:** Provision API credentials for Phase 1A sources (lead time) — see [[navira-credentials-access]]
3. **In parallel:** Begin Amazon SP-API app registration for Phase 1C (2–4 week approval)
4. After Phase 0 gate passes: design unified marketing schema (Snowflake) for Phase 1A
5. Schedule discovery sessions for Priority 1 open questions
6. Initiate legal review for agency customer DPA and unstructured data governance

## Workflow Pages

### Active

- [[phase-0-prefect-foundation]] — Framework hardening, Sellercloud migration, CC1–CC7 resolution (prerequisite for all)
- [[phase-1a-marketing-ad-platforms]] — Google Ads, Facebook Ads, Amazon PPC UK/CA, Target+
- [[phase-1b-marketing-social-emerging]] — TikTok, Creator Connections, Email
- [[phase-1c-sales-agency-customers]] — Seller Central multi-tenant sales + inventory
- [[phase-2-inventory]] — Sellercloud inventory, Navira Purchasing System
- [[phase-3-competitor-data]] — SmartScout
- [[phase-4-unstructured-data]] — Email, Meeting Notes, Documents
- [[credential-validation-toolkit]] — API credential tester CLI (ongoing, parallel to all phases)

### Reference

- [[navira-credentials-access]] — Auth questionnaire status + credential tracking (cross-cutting prerequisite)
- [[navira-access-briefing]] — Client meeting briefing: access requirements by phase, what to ask vs what we have
- [[navira-dashboard-recommendations]] — 8 proposed dashboards + competitive landscape + architecture
- [[navira-data-dictionary-phase1a]] — API field reference for Google Ads, Meta, Amazon

### Completed

_(none yet — move workflows here when done)_

## See Also

- [[GEP]] — client entity page (Navira = GEP's new name)
- [[Prefect]] — likely orchestration platform (CC2)
- [[Snowflake]] — data warehouse
- [[Eclipse]] — dashboard/visualization layer
- [[connector-development-standards]] — ALDC Prefect connector pattern
- [[eclipse_exp]] — source of the 5 interactive HTML documents
