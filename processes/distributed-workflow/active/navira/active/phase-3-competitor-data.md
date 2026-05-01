---
tags: [workflow, navira, phase-3, competitor, smartscout, priority-3]
aliases: [Navira Phase 3, Competitor Data]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-30
---

# Phase 3 — Competitor Data

**Priority:** 3 · **Interfaces:** 1 · **Status:** Tickets created — Backlog. Needs refinement.

## Objective

Ingest competitive intelligence from SmartScout for market share analysis, competitor pricing monitoring, category trend identification, and new product opportunity assessment — correlated with Navira's own sales and marketing data.

## Interfaces

| # | Interface | Notes |
|---|---|---|
| 1 | **SmartScout** | API or export depending on subscription tier. New standalone connector. |

## Suggested Approach

New standalone connector; define competitive analysis schema.

## High-Level Requirements

- **Competitor product tracking:** Pricing, BSR, estimated revenue, review counts for key competitor ASINs
- **Category/subcategory trends:** Market size estimates, growth rates, seller concentration
- **Brand monitoring:** New entrants, brand share shifts, listing changes
- **Own-product benchmarking:** Compare Navira's products against category averages and direct competitors
- **Refresh frequency:** Weekly or bi-weekly (daily if SmartScout supports it)
- **Historical trending:** Track competitor metrics over time, not just snapshots

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q1 | SmartScout subscription tier includes API access, or CSV/Excel export only? | Automation level — API = scheduled pulls; export = manual upload |
| Q2 | How many competitor ASINs/brands to track? (Top 10 per category? All ASINs in target subcategories?) | Data volume, refresh strategy, potential plan upgrade |
| Q3 | Competitive data in same Snowflake DB as internal data, or separated? Who has access? | Schema placement, access controls |
| Q4 | Is SmartScout confirmed, or also evaluate Jungle Scout, Helium 10, Keepa? | Schema generalization for multi-provider |

## Dependencies

| Dependency | Detail |
|---|---|
| **Corporate Data — Products (Production)** | Benchmarking requires joining competitor data with Navira's product catalog (ASINs). |
| **Sales Data (Production)** | Market share estimates compare Navira sales volumes against SmartScout category estimates. |

## Acceptance Criteria

- [ ] Competitor ASIN metrics populate in Snowflake on defined schedule
- [ ] Category trend data available for Navira's active subcategories
- [ ] Navira products benchmarkable against category averages
- [ ] Historical competitor data retained for trend analysis (min **6 months**)
- [ ] Access restricted to authorized internal users (no agency customer access)

## Jira Tickets

| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-234 | SmartScout | Backlog | Needs refinement — API access tier and ASIN scope TBD |

## See Also

- [[navira/README|Navira Roadmap]]
- [[navira-dashboard-recommendations]] — D3 Amazon Performance Hub (Share of Voice, BSR)
