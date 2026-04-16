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

## Active Tickets

- [[FU92-342]] — (see ticket page)

## See Also

- [[clients-repo]] — repo structure and conventions
- [[Eclipse]] — connector platform
- [[Snowflake]] — data warehouse
