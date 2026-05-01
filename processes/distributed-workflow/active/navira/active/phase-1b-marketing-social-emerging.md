---
tags: [workflow, navira, phase-1b, marketing, tiktok, email, target-plus, priority-1]
aliases: [Navira Phase 1B, Marketing Social Emerging]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-30
---

# Phase 1B — Marketing Data: Social & Emerging Channels

**Priority:** 1 · **Interfaces:** 3 · **Status:** Tickets created — S5. Needs refinement. · **Depends on:** Phase 1A ingestion pattern

> **2026-04-28 scope change:** Target+ moved to Phase 1A — confirmed as active spend by Heather Tabor. TikTok, Creator Connections, and Email were not listed as current spend channels. Phase 1B may be deprioritized pending further input from Navira.

## Objective

Extend the marketing data pipeline (built in Phase 1A) to cover social commerce, influencer marketing, marketplace advertising, and email campaigns — completing Navira's cross-channel marketing visibility.

## Interfaces — Build Order

| # | Interface | Notes |
|---|---|---|
| 7 | **TikTok Shops** | API access TBD. May be coupled with Creator Connections. Not listed as current spend (2026-04-28). |
| 8 | **Email Campaigns** | Platform unknown (Klaviyo/Mailchimp/HubSpot?). Metrics: sends, opens, clicks, revenue attributed. Not listed as current spend (2026-04-28). |
| 9 | **Creator Connections** | May be a TikTok Creator Marketplace feature or a separate influencer platform — clarification needed. Not listed as current spend (2026-04-28). |

## Prerequisites

- [ ] Phase 1A ingestion pattern proven and stable
- [ ] TikTok API access confirmed (Q5 from Phase 1A open questions)
- [ ] Email marketing platform identified (Q6)
- [ ] ~~Target+ integration method determined (Q7)~~ — moved to Phase 1A (2026-04-28)
- [ ] Credentials provisioned (see [[navira-credentials-access]])

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q5 | Are "Creator Connections" a TikTok feature or a separate influencer platform? Does TikTok Shops have API access or export-only? | One TikTok connector or two integrations |
| Q6 | Which email marketing platform? What metrics matter — sends, opens, clicks, revenue attributed? Does email revenue tie back to Shopify/Amazon orders? | API selection, schema scope |
| Q7 | Is Navira a Target+ marketplace seller? API or manual data feed (SFTP/portal export)? | Automation feasibility — file watcher vs API poll |

## Suggested Approach

Reuse Phase 1A pipeline; adapt transformations per channel. The unified marketing schema should accommodate these sources without schema changes — only new source adapters needed.

## Acceptance Criteria

Same as Phase 1A (daily ingestion, < 24h latency, 2% reconciliation tolerance, alerting, queryable in PBI/Eclipse).

## Jira Tickets

| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-228 | TikTok/Creator Connections | S5 | TikTok Shops + Creator Marketplace — needs platform confirmation |
| GP-229 | Email Campaigns | S5 | Platform TBD (Klaviyo/Mailchimp/HubSpot?) |

## See Also

- [[phase-1a-marketing-ad-platforms]] — prerequisite phase
- [[navira-dashboard-recommendations]] — D6 Paid Media Performance, D7 Email & Owned Channels
