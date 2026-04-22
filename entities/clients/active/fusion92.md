---
tags: [entity, client, fusion92, media, advertising]
aliases: [Fusion92, Fusion 92]
sources: [clients repo FUSION_92/ directory]
created: 2026-04-16
updated: 2026-04-16
---

# Fusion92

Media activation and advertising analytics client. Aggregates campaign performance data across multiple ad platforms into a unified [[Snowflake]] reporting model.

## Data Sources (Eclipse Connections)

11 Eclipse connections in `FUSION_92/eclipse/connections/`:

| Connection | System | Notes |
|-----------|--------|-------|
| amazon_ads | Amazon Advertising API | Campaign reporting |
| meta | Meta (Facebook) Ads API | Multiple client accounts (BCBSM, Parkside, Community Choice, Ross) |
| microsoft_ads | Microsoft Advertising | Campaign reports |
| snowflake_advantage360 | Snowflake (Advantage360) | Ad log data |
| snowflake_fusion_viant | Snowflake (Viant data) | DSP performance |
| trade_desk_my_reports | The Trade Desk | Performance + unique impression reports |
| viant_dsp_reporting | Viant DSP | Campaign perf, detailed perf, ROAS, reach/frequency |
| windsor | Windsor.ai | Aggregated marketing data |
| smartsheet | Smartsheet | Budget data (yearly sheets per region/client) |
| firebase_flight_check | Firebase | Flight check system |
| galactica_aldc_library | Galactica SQL | Shared ALDC library data |

## Eclipse Templates

50+ templates organized by platform:

- **Meta** (12): Campaign + ad set level for BCBSM Brand DP+, BCBSM Business Units DP+, BCBSM Michigan, Parkside, Community Choice, Ross Brand Advertising
- **Smartsheet** (10+): Yearly budget sheets — 2023 (BCBSM, Chi, Det, FY23, FY24, Performance Marketing) and 2024 (ADM, BCBSM, Chi, Det)
- **Trade Desk** (2): Performance report, unique impression report
- **Viant DSP** (4): Campaign performance, detailed performance, ROAS, reach/frequency
- **Google** (5+): Google Ads, Campaign Manager, CM impression reach, DV360, DV360 reach, Search Ads
- **LinkedIn** (2): LinkedIn Ads, LinkedIn Ads video/social
- **Amazon DSP** (1): Campaign report
- **Advantage360** (1): Ad log
- **Flight Check** (2): Flights, jobs
- **Supplements** (5): Financial currency, geography, KPI periodicity, time calendar, time

## Snowflake Warehouse

10 SQL views in `FUSION_92/snowflake/warehouse/`:

### Dimensions
| View | Purpose |
|------|---------|
| shared_dim_account | Account/advertiser dimension |
| shared_dim_campaign | Campaign dimension |
| shared_dim_creative | Creative/ad dimension |
| shared_dim_currency | Currency dimension |
| shared_dim_date | Date dimension |
| shared_dim_flight | Flight (campaign run period) dimension |
| shared_dim_platform | Ad platform dimension |

### Facts
| View | Purpose |
|------|---------|
| fct_budget | Budget/planned spend |
| fct_flight | Flight-level metrics |
| fct_spend | Actual spend/performance |

## Key Concepts

- **Flight Check**: System for tracking campaign flights (scheduling windows) — uses Firebase + Smartsheet as sources
- **Advantage360**: Third-party ad log aggregation platform
- **Multi-account Meta**: Separate templates per client account (BCBSM, Parkside, etc.) rather than one consolidated pull

## Custom services

- [[custom-fusion-92-audience-api]] — DIOS-to-DAX API. Takes raw audience data from Fusion's internal DIOS web app, joins + formats per destination ad platform (Reddit, Meta, etc), outputs to Nextcloud. Runs on-prem due to 60 GB-memory / 2–5 minute request constraints.

## Active Tickets

- [[FU92-342]] — (see ticket page)

## ALDC Team

| Name |
|------|
| John Moran |
| Sean O'Grady |
| Karen Prete |

*Source: CF92/1207009548*

## Data Source Integration Status

Status as of Confluence snapshot (2024–2025). Overall status: **DONE — Viant Reach is the final outstanding item.**

| Source | Jira refs | Client PoC | Connectivity | Data in Eclipse | Activation | Notes |
|--------|-----------|------------|:------------:|:---------------:|:----------:|-------|
| NetSuite | CUST-732 | Cory Hanna, Christina Taylor | DONE (2024-04-05) | ON HOLD | PENDING | Revisit once DAX Media App complete. Prioritize per Christina's platform list. |
| Advantage 360 | CUST-741, CRTL-1194 | Johanna Berger | DONE (2024-06-10) | DONE | DONE | In production (2025-05-01). Uses TargetSmart API. Campaigns: 4VOTER_StateofMichigan_EarlyVoter + Univision Dashboard. |
| Viant | CUST-560, CRTL-1198 | Johanna Berger | DONE | DONE | DONE | Standard Match first, then Placekey for unmatched addresses. Reach & frequency only where unique identifiers unavailable. |
| Trade Desk | CUST-738, CRTL-1202 | Johanna Berger | DONE | DONE | DONE | Conversion data reporting in progress. Platform IDs added to Smartsheets. |
| Amazon DSP | CUST-743, CRTL-1206 | Tom Hammond | DONE (2024-03-18) | DONE | DONE | Delve - Fusion active account. |
| Amazon Ads | CUST-745, CRTL-1210 | Tom Hammond | DONE (2024-03-28) | BLOCKED | BLOCKED | No live accounts active; nothing planned for 2024. Access to Delve - Fusion only. |
| Microsoft Ads / Bing | CUST-643 | Lindsey Watters | DONE (2024-03-28) | DONE | DONE | In production (2025-04-23). Requires Azure app registration on F92 side. |
| LinkedIn Ads | CUST-744, CRTL-1214 | Lindsey Watters | DONE (2024-04-11) | DONE | DONE | Lindsey authorized account. |
| Google CM 360 | CUST-644, CRTL-837 | Lindsey Watters | DONE (2024-03-07) | DONE | DONE | ADMIS account added. |
| Google DV360 | CUST-641, CRTL-819 | Lindsey Watters | DONE (2024-03-18) | DONE | DONE | Accounts: Buddig (1880478), CBOE (4679731), Dremel (1327691266). Flights using both CM + DV360 brought in via CM (1:1 flight-to-DSP). |
| Google Ads | CUST-627, CRTL-771 | Lindsey Watters | DONE (2024-03-07) | DONE | DONE | 23 accounts at initial prod deploy. |
| Google SA360 | CUST-642, CRTL-823 | Lindsey Watters | DONE | DONE | DONE | ADMIS account added. Platform account ID + campaign ID in Smartsheets (2024-07-18). Google Ads takes precedence over SA360 when both report same campaigns. |
| Meta Ads | CUST-593 | Johanna Berger | DONE | DONE | DONE | Active accounts: BCBSM Brand, DP+ BCBSM Michigan, Blue Cross Blue Shield, Community Choice, Credit Union Parkside, Credit Union Ross Brand Advertising. |
| Flight Check | — | Johanna Berger | DONE | DONE | DONE | — |
| Smartsheets | — | Johanna Berger | DONE | DONE | DONE | 2023 + 2024 Master Templates active (BCBSM, Chi, Det variants). |
| Experian | CUST-586, CRTL-1258 | Justina Silva | CANCELLED | — | — | Direct access not permitted. Eclipse imports flat files from Experian SFTP (Consumer View ×13/month; New Mover/Household/Parent ×1/week). |
| Axciom | — | — | CANCELLED | — | — | Cancelled 2024-03-08. |
| Snapchat Ads | — | — | DEFERRED | — | — | — |
| Beeswax | — | — | DEFERRED | — | — | — |
| TikTok Ads | — | — | DEFERRED | — | — | — |
| Pinterest Ads | — | — | DEFERRED | — | — | — |
| Alteryx | — | — | DEFERRED | — | — | — |

*Source: CF92/1207238675*

## Univision Dashboard Project

*Source: CF92/1281130497, CF92/1283096590*

Reporting dashboard for Fusion92's Univision client account. Data sources: Trade Desk, Advantage360, Viant. Replaces legacy Treehouse dashboard.

| Deliverable | REQ | Status |
|-------------|-----|--------|
| External customer-facing dashboard | REQ-283 | ON HOLD (budget approval pending) |
| Internal Fusion dashboard | — | Deferred |

**External dashboard scope (REQ-283):**
- ~30 external users; CSV export alongside dashboard
- Metrics: Impressions, Clicks, CTR, 100% Completions, Completion Rate (campaign/flight/creative); Reach + Frequency (campaign/flight only); Impressions by Device; Top 15 Sites
- Filters: Advertiser, Campaign Name, Order Number, Flight Name, Flight ID, Line ID, Custom Date Range
- Data SLA: Prior-day data before 10am Eastern
- Advantage360 + Viant data confirmed; Trade Desk pending confirmation

## Phase 2 Marketing Reporting

*Source: CF92/1224933377 — ADM-focused initiatives; see also [[adm]]*

Planning-phase notes (March 2024–March 2025) for the next phase of Fusion92/ADM marketing reporting:

- **Telemetry:** Automated failure email reporting for Fusion92 monitoring
- **Data Sources:** Pardot (ADM account), SEM Rush (possibly ADM), Facebook Campaigns (from April 1), LinkedIn/Facebook/Sprout Social organic
- **Architecture:** BigQuery refactoring/reorganization; new dual dashboard (marketer-focused + ADM stakeholder-focused)
- **Access:** Yury using ADM contractor account for Looker; Joe to provision empty report with editor role

## Enterprise Scoping Project (2023)

Source: Confluence CLIEN/1111687169 (Enterprise Scoping Project, 2023-06-06).

Fusion92 enterprise data integration scoping. Key data sources assessed:

| Source | Status | Notes |
|---|---|---|
| Experian Consumer View / New Mover / New Homeowner / New Parent / EDR | Moved out of scope (2023-06-26) | Source: Ryan Abney (r.abney@fusion92.com); stored in Azure |
| Viant Adelphic (DSP1) | Phase 1 | Data samples to NextCloud; need connectivity contact |
| TradeDesk (DSP2) | Phase 1 | Data samples to NextCloud; need connectivity contact |
| Google DV360 | Phase 1 | Data samples to NextCloud |
| Salesforce (F92 internal deals) | Phase 1 | Enterprise-wide rollout for internal campaign tracking |
| Salesforce (client systems) | Phase 2 | Contact: Lindsey Waters |
| NetSuite (F92) | Phase 2 | |
| Flight Check | Closed/out-of-scope | Contact: Lindsey Waters (l.waters@fusion92.com) |

**Key problems to solve:**
- Replace Smartsheets (Johanna Berger)
- Reduce Flight Check manual entry burden
- Snowflake Clean Rooms for F92 + clients (e.g. Experian) — Dave Nugent
- DSP return data capture and reporting
- Experian data movement audit + month-end reporting (12 files, pricing fields, client export tracking)
- CCPA compliance (California Consumer Protection Act)

## See Also

- [[clients-repo]] — repo structure and conventions
- [[Eclipse]] — connector platform
- [[Snowflake]] — data warehouse
- [[Windsor]] — marketing data aggregation (F92 `windsor` Eclipse connection)
- [[fusion92-platform-ids]] — platform account/campaign/order ID mapping for Flight Check
- [[dax-media-app]] — Flight Management App (Flight Check replacement)
- [[dax-ai]] — DAX AI dashboard product family (Performance, Financial, External dashboards)
- [[adm]] — ADM marketing dashboard sub-client (GCP/BigQuery stack)
