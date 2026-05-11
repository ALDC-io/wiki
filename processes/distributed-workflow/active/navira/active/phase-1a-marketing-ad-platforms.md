---
tags: [workflow, navira, phase-1a, marketing, google-ads, facebook-ads, amazon-ppc, priority-1]
aliases: [Navira Phase 1A, Marketing Ad Platforms]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html, eclipse_exp/frontend/public/navira/navira-phase1a-data-dictionary.html]
created: 2026-04-27
updated: 2026-04-30
---

# Phase 1A — Marketing Data: Ad Platforms

**Priority:** 1 (Immediate) · **Interfaces:** 6 (in build order) · **Status:** Tickets created — S3/S4

## Objective

Centralize all marketing spend and performance data into Snowflake so the business can measure true ROAS across channels, correlate ad spend with sales by SKU/marketplace, and surface marketing insights through Power BI / Eclipse dashboards.

## Interfaces — Build Order

| #   | Interface               | Rationale                                                                                                                                                                  |
| --- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Google Ads → Amazon** | Likely highest spend. Establishes the ad-platform ingestion pattern (OAuth, daily pulls, spend/impression/click/conversion schema) that every subsequent connector reuses. |
| 2   | **Google Ads → D2C**    | Same API, different campaign segmentation. Validates pattern handles multiple attribution paths.                                                                           |
| 3   | **Amazon PPC UK**       | Same Amazon Advertising API as US PPC. Regional variant tests multi-marketplace handling.                                                                                  |
| 4   | **Amazon PPC CA**       | Same API, third marketplace. **Already live** — 68K rows in production (confirmed 2026-05-08).                                                                             |
| 5   | **Facebook Ads**        | Different API (Meta Marketing API) but same output schema. Proves ingestion pattern is source-agnostic.                                                                    |
| 6   | **Target+**             | Moved from Phase 1B — confirmed as active spend channel by Heather (2026-04-28). May be API or SFTP/portal export.                                                         |

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

## Jira Tickets

### Active this sprint (S2)
| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-199 | ASIN Brand Campaign Attribution — Initial Design | S2 | **Priority** — Lori's top ask. Scope/design ticket. |
| GP-183 | Connection: Google Ads — Windsor vs API Research | S2 | Research ticket — informs GP-226 + GP-238 |
| GP-238 | ACCESS: Google Ads Credentials & MCC Access | S2 | Child of Epic GP-237. Depends on GP-183 decision. |
| GP-241 | ACCESS: Amazon UK PPC OAuth Follow-up | S2 | Child of Epic GP-237. BLOCKED on Navira. |
| GP-239 | ACCESS: Facebook/Meta Business Manager + API | S2 | Child of Epic GP-237. |
| GP-240 | ACCESS: Target+ Discovery + Credentials | S2 | Child of Epic GP-237. |

### Future sprints
| Ticket | Summary | Sprint | Notes |
|---|---|---|---|
| GP-225 | Unified Marketing Schema Design | S3 | Snowflake schema — prerequisite for all 1A connectors |
| GP-221 | Amazon UK PPC OAuth — Build | S3 | Technical implementation once GP-241 unblocks access |
| GP-226 | Google Ads Connector | S4 | Depends on GP-183 decision + GP-238 credentials |
| GP-222 | Facebook Ads Connector | S4 | Depends on GP-239 credentials |
| GP-223 | Target+ Connector | S4 | Depends on GP-240 credentials |
| GP-227 | Historical Backfill | S5 | All platforms — Google 3yr, Meta 2yr, Amazon 60–90d |

### Cross-cutting
| Ticket | Summary | Notes |
|---|---|---|
| GP-237 | Access & Credentials Epic (GP-238–245) | Parent epic for all access tickets |

## Boot Prompts

### GP-238 — Google Ads Access: Windsor vs Direct API Research

````
You are working on **GP-238** (ACCESS: Google Ads — Credentials & MCC Access from Navira).

**Goal:** Determine the recommended approach (Windsor.ai vs direct Google Ads API), draft a client communication explaining the recommendation with trade-offs, and document next steps.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\windsor.md` — ALDC's existing Windsor account (used by Fusion92)
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\navira-credentials-access.md` — current credential status. Key facts:
   - Navira MCC ID already provided: `728-582-8945` (Justin Shuster, 2026-04-15)
   - ALDC MCC linking still pending
   - Open question: are Amazon + D2C campaigns in same MCC or separate?
4. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\connectors\google-ads.md` — existing ALDC Google Ads connector docs (4-credential model)
5. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\phase-1a-marketing-ad-platforms.md` — Phase 1A context
6. Check windsor ai docs online for Google Ads connector if required.

**Key context:**
- ALDC already has a Windsor account (Fusion92 client). Check if GEP/Navira has their own Windsor account or can be added to the existing one.
- Windsor was recommended by Marshall (GP-183 comment, 2026-04-27) as "quicker and more affordable" but "Google Ads connection would be more robust and longer term."
- GP-183 (Jira) has the full comment history including Marshall's and Lori's input.

**Deliverables:**
1. Research document comparing Windsor vs direct Google Ads API:
   - Setup time and complexity for each
   - Data granularity / report types available
   - Cost (Windsor subscription vs free API)
   - Maintenance burden (token refresh, API version upgrades)
   - Recommendation with clear reasoning
2. Draft client communication to Navira explaining:
   - Recommended approach + why
   - What Navira needs to do (Windsor: grant account access; Direct API: nothing beyond MCC linking already provided)
   - Timeline expectation for each path
   - If Navira prefers direct API, explain the delay (1-2 week developer token approval)
3. Update GP-238 and GP-183 with findings

**Scope:** Research + client communication draft only. Do NOT build the connector or modify code.
````

### GP-199 — ASIN Brand Campaign Attribution: Initial Design

````
You are working on **GP-199** (Utilize ASIN Data on Amazon Ad Spend Interface for Campaign — new call and data set).

**Goal:** Produce an initial design for ASIN-level brand campaign attribution, including proposed Snowflake schema changes, PBI model impact, and clarifying questions for Navira.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read GP-199 on Jira (https://analyticlabsdc.atlassian.net/browse/GP-199) — full comment history. Key points:
   - Lori: "this is the top priority" (2026-04-28)
   - Steven: need to know what Amazon Ads endpoint/report contains ASIN-level brand campaign data
   - Lori: "The new Amazon API returns the ASIN per campaign"
   - Marshall: "check in with Paul on this one directly"
   - Original estimate: 17.5–25 hrs (Claude + review)
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\phase-1a-marketing-ad-platforms.md` — Phase 1A context
4. Read `C:\Users\PaulRussell\repos\wiki\concepts\business-logic\gep-inventory-data-dictionary.md` — reference for existing schema patterns
5. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\connectors\amazon-ads.md` — Amazon Ads connector docs
6. In the clients repo (`C:\Users\PaulRussell\repos\clients`), read `GEP/snowflake/warehouse/marketing_fct_activity.sql` — the current marketing fact table where brand campaign spend is split across all ASINs in a brand via portfolio

**Key context:**
- Currently, brand campaign spend is attributed to ALL ASINs under a brand (even distribution via portfolio lookup). No ASIN-level targeting data exists.
- The Amazon Advertising API has a Sponsored Brands campaign report that includes `campaignId` → targetable ASINs. The specific endpoint/report needs to be identified.
- This could be done via the existing Eclipse connector (add a new template) OR as a Prefect connector (Phase 1A pattern). The `gep-feature` skill may apply if this is a warehouse SQL + PBI change.
- GP-199 is a Scope ticket — it needs a design, not an implementation.

**Deliverables:**
1. Identify the Amazon Advertising API endpoint/report that provides campaign-to-ASIN mapping for Sponsored Brands
2. Propose Snowflake schema changes:
   - New staging table (e.g., `EXTRACT_AMAZON_ADS_CAMPAIGN_ASIN_MAP`)
   - Changes to `marketing_fct_activity.sql` to use ASIN-level attribution instead of portfolio-based even split
3. Assess PBI model impact — what changes in the Power BI semantic model?
4. List clarifying questions for Navira/Lori
5. Rough effort estimate for implementation

**Scope:** Design document + questions only. Do NOT implement SQL changes or modify code.
````

## See Also

- [[navira/README|Navira Roadmap]] — master hub
- [[navira-credentials-access]] — credential status
- [[phase-1b-marketing-social-emerging]] — next phase (social + emerging channels)
- [[navira-dashboard-recommendations]] — D1 Marketing Command Center, D3 Amazon Performance Hub, D6 Paid Media Performance
- [[google-ads]], [[facebook-ads]], [[amazon-ads]] — existing ALDC connector specs
- [[connector-development-standards]] — canonical ALDC/Prefect connector pattern
