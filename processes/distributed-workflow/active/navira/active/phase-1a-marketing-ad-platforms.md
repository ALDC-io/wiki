---
tags: [workflow, navira, phase-1a, marketing, google-ads, facebook-ads, amazon-ppc, priority-1]
aliases: [Navira Phase 1A, Marketing Ad Platforms]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html, eclipse_exp/frontend/public/navira/navira-phase1a-data-dictionary.html]
created: 2026-04-27
updated: 2026-04-28
---

# Phase 1A — Marketing Data: Ad Platforms

**Priority:** 1 (Immediate) · **Interfaces:** 6 (in build order) · **Status:** Not Started

## Objective

Centralize all marketing spend and performance data into Snowflake so the business can measure true ROAS across channels, correlate ad spend with sales by SKU/marketplace, and surface marketing insights through Power BI / Eclipse dashboards.

## Interfaces — Build Order

| # | Interface | Rationale |
|---|---|---|
| 1 | **Google Ads → Amazon** | Likely highest spend. Establishes the ad-platform ingestion pattern (OAuth, daily pulls, spend/impression/click/conversion schema) that every subsequent connector reuses. |
| 2 | **Google Ads → D2C** | Same API, different campaign segmentation. Validates pattern handles multiple attribution paths. |
| 3 | **Amazon PPC UK** | Same Amazon Advertising API as US PPC. Regional variant tests multi-marketplace handling. |
| 4 | **Amazon PPC CA** | Same API, third marketplace. |
| 5 | **Facebook Ads** | Different API (Meta Marketing API) but same output schema. Proves ingestion pattern is source-agnostic. |
| 6 | **Target+** | Moved from Phase 1B — confirmed as active spend channel by Heather (2026-04-28). May be API or SFTP/portal export. |

> **Note:** Interfaces 7–9 (TikTok, Email, Creator Connections) remain in [[phase-1b-marketing-social-emerging]] — not confirmed as current spend by Navira (2026-04-28).

## Prerequisites

- [ ] Cross-cutting decisions CC1–CC7 resolved (see [[navira/README]])
- [ ] API credentials provisioned and tested (see [[navira-credentials-access]])
- [ ] Snowflake marketing schema designed and approved
- [ ] Corporate Data product tables verified current (ASIN, GTIN, Shopify variant ID for SKU-level joins)

## High-Level Requirements

- **Unified marketing schema** in Snowflake: date, channel, campaign, ad_group, ad, marketplace, spend, impressions, clicks, conversions, revenue, ACOS/ROAS calculated fields
- **Daily automated ingestion** with configurable lookback window (ad platforms retroactively adjust numbers for 7–30 days)
- **Attribution alignment:** consistent attribution window definitions across platforms for apples-to-apples cross-channel ROAS
- **Currency normalization:** USD base with conversion for UK (GBP) and CA (CAD)
- **SKU-level mapping:** link ad campaigns to internal product SKUs for profitability analysis
- **Error handling & alerting:** retry logic for API rate limits, alerts on ingestion failures or data gaps
- **Historical backfill:** initial load (Google 3yr, Meta 2yr, Amazon 60–90 days)

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q1 | Which Google Ads MCC account(s) cover Amazon and D2C campaigns? Same MCC or separate? Developer tokens + OAuth configured? | Auth design, one connector or two configs |
| Q2 | ~~Is Navira already using Amazon Advertising API for US PPC? UK/CA same profile or separate? Current auth (LWA)?~~ **RESOLVED 2026-04-28:** US PPC (708K rows) and CA PPC (68K rows) already flowing via existing `amazon_ads` connector. Raw Snowflake tables confirmed only USD + CAD profiles — no UK (GBP) data. UK advertising profile not authorized; Navira must grant OAuth access for UK. Connector is multi-marketplace and needs no code changes. | Config change only — add UK profile ID to `MARKETPLACE_PROFILE_MAP` in `marketing_fct_activity.sql` once authorized. |
| Q3 | Attribution window and model for ROAS reporting today? (last-click 7-day, first-click 30-day?) Store raw platform attribution or apply custom model? | Schema design, transformation layer |
| Q4 | Which Business Manager ID owns the Meta ad accounts? System user token or user-level token with manual refresh? | Reliability of automated daily pulls |
| Q8 | How are campaigns linked to SKUs today? ASIN in Amazon, UTM in Google, product catalog in Meta? Master mapping table or needs building? | Mapping/resolution service vs existing Corporate Data join |

## Dependencies

| Dependency | Detail |
|---|---|
| **Snowflake Marketing Schema** | Must be designed and approved before first connector build. Recommend `MARKETING_RAW` (source-specific) + `MARKETING_ANALYTICS` (unified/transformed). |
| **Corporate Data (Live)** | SKU-level joins depend on live Product / Item Data / SKU Kitting tables. Verify marketplace-specific identifiers present. |
| **API Credentials** | All platform credentials provisioned and tested before dev begins. Shared secrets management approach required (CC3). |

## Acceptance Criteria

- [ ] Data lands in Snowflake daily with < 24h latency from source
- [ ] Historical backfill loaded to maximum available depth
- [ ] Row counts and spend totals reconcile to source platform within **2% tolerance**
- [ ] Failed ingestion triggers alert (email/Slack) with error context
- [ ] Data is queryable in Power BI and/or Eclipse dashboard
- [ ] Currency normalized to USD with original currency preserved
- [ ] Documentation: data dictionary, refresh schedule, known limitations

## Data Dictionary Reference

See [[navira-data-dictionary-phase1a]] for field-level API specs covering Google Ads (GAQL v18/v19), Meta Marketing API (v21/v22), Amazon Advertising API v3 (SP/SB/SD).

## See Also

- [[navira/README|Navira Roadmap]] — master hub
- [[navira-credentials-access]] — credential status
- [[phase-1b-marketing-social-emerging]] — next phase (social + emerging channels)
- [[navira-dashboard-recommendations]] — D1 Marketing Command Center, D3 Amazon Performance Hub, D6 Paid Media Performance
- [[google-ads]], [[facebook-ads]], [[amazon-ads]] — existing ALDC connector specs
- [[connector-development-standards]] — canonical ALDC/Prefect connector pattern
