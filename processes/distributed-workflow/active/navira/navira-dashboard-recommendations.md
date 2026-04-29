---
tags: [workflow, navira, dashboards, power-bi, eclipse, marketing, analytics]
aliases: [Navira Dashboards, Navira Dashboard Recommendations]
sources: [eclipse_exp/frontend/public/navira/navira-dashboard-recommendations.html]
created: 2026-04-27
updated: 2026-04-27
---

# Navira — Dashboard Recommendations

Straw-man dashboard set for Navira collaboration. Based on research across 20+ e-commerce analytics platforms. April 9, 2026.

## 1. Competitive Landscape

### Tier 1 (Best-in-Class)

| Tool | Strength | Relevance |
|---|---|---|
| **Triple Whale** | Blended attribution, Contribution Margin focus, Shopify-native | Closest to Navira's multi-channel model |
| **Northbeam** | Multi-touch attribution, creative-level ROAS, ML-based | Strong attribution methodology |
| **Measured** | Media mix modelling, incrementality testing | Enterprise-grade; may be overkill for initial build |

### Tier 2 (Relevant Capabilities)

| Tool | Strength | Notes |
|---|---|---|
| **Daasity** | Snowflake-native, e-commerce ETL + dashboards | Good reference for schema design |
| **Saras Analytics (Daton + Pulse)** | 100+ connectors, pre-built Snowflake models | Daton = ETL, Pulse = BI layer |
| **Glew.io** | Multi-channel attribution, inventory analytics | Mid-market focus |

> **Key Insight:** "Contribution Margin is the new North Star" — the industry hierarchy is **CM > MER > ROAS**. Dashboard design should reflect this: CM is the hero metric, MER (Marketing Efficiency Ratio) the operating metric, ROAS the channel-level metric.

## 2. Aggregation Layer Recommendation

**Recommended: Funnel.io**
- Native Snowflake connector (direct write, no intermediate staging)
- 600+ pre-built source connectors
- Campaign name parsing and normalization rules
- Handles cross-platform field mapping

**Alternative evaluated: Source Medium** — BigQuery-native, not a fit for Snowflake-centric stack.

## 3. Amazon-Specific KPIs

| KPI | Description | Dashboard |
|---|---|---|
| **TACoS** (hero metric) | Total Advertising Cost of Sales = Ad Spend / Total Revenue (including organic) | D3 |
| **ACoS** | Advertising Cost of Sales = Ad Spend / Ad-Attributed Revenue (by campaign type: SP/SB/SD) | D3 |
| **Share of Voice** | % of impressions on target keywords | D3 |
| **New-to-Brand %** | % of purchases from first-time brand customers | D3 |
| **Buy Box %** | % of time product wins the Buy Box (US/UK/CA) | D3 |
| **BSR** | Best Sellers Rank — category position over time | D3 |
| **Organic Rank** | Non-paid keyword ranking | D3 |

Tools with these capabilities: Pacvue, Intentwise, Perpetua.

## 4. Recommended Dashboards (D1–D8)

### D1: Marketing Command Center
**Audience:** CMO / CEO · **Cadence:** Weekly
**KPIs:** MER (Marketing Efficiency Ratio), Blended ROAS, CM%, Revenue by Channel
**Layout:** Executive scorecard — 4 hero tiles top, trend charts below, channel comparison table

### D2: Channel Mix & Allocation
**Audience:** VP Marketing · **Cadence:** Weekly
**KPIs:** ROAS/CAC by channel, ncROAS (new customer ROAS), spend share vs revenue share
**Layout:** Treemap for spend allocation, scatter plot (ROAS vs volume), recommendation cards

### D3: Amazon Performance Hub
**Audience:** Amazon Channel Manager · **Cadence:** Daily
**KPIs:** TACoS (hero), ACoS by campaign type (SP/SB/SD), SOV, BSR, Buy Box % (US/UK/CA), NTB%
**Layout:** TACoS trend as hero chart, campaign type breakdown, marketplace comparison columns
**Sources:** Amazon Ads API, SP-API

### D4: Customer LTV & Cohorts
**Audience:** CMO / CRM · **Cadence:** Monthly
**KPIs:** LTV:CAC ratio (target 3:1), cohort retention heatmap, repeat purchase rate, first-to-second purchase time
**Sources:** Shopify, Amazon orders, email platform

### D5: Profitability Waterfall
**Audience:** CFO / CMO · **Cadence:** Monthly
**KPIs:** Waterfall chart: Gross Revenue → minus COGS → minus Shipping → minus Fees → minus Ad Spend = **Contribution Margin**
**Sources:** Sales Data, Inventory/Purchasing (Phase 2), Marketing (Phase 1A)

### D6: Paid Media Performance
**Audience:** Media Buyers · **Cadence:** Daily
**KPIs:** Creative thumbnails, budget pacing, CTR, CPC, CPM by creative/audience
**Note:** 79% of TikTok conversions are missed by last-click attribution — consider view-through or data-driven attribution for TikTok.
**Sources:** All ad platforms (Phase 1A + 1B)

### D7: Email & Owned Channels
**Audience:** Email Manager · **Cadence:** Weekly
**KPIs:** Revenue Per Recipient (RPR), Flow Revenue (benchmark: ~41% of email revenue from 5.3% of sends), open rate, click rate, unsubscribe rate, list growth
**Sources:** Email platform (Phase 1B)

### D8: Marketplace Expansion
**Audience:** VP E-Commerce · **Cadence:** Monthly
**KPIs:** Revenue, units, margin, growth rate — compared across columns: Amazon US / Amazon UK / Amazon CA / Shopify / Target+
**Sources:** Sales Data (Production + Phase 1B for Target+)

## 5. Proposed Data Architecture

```
Ad Platforms ──→ Funnel.io ──→ Snowflake
Amazon ────────→ Daton ──────→ Snowflake
                                 │
                     ┌───────────┼───────────┐
                     ▼           ▼           ▼
              Power BI      Power BI     Eclipse
             DirectQuery     Import      Dashboards
             (operational)  (executive)
```

### Snowflake Data Model (proposed)

| Table | Domain |
|---|---|
| `fact_marketing_spend` | Ad spend, impressions, clicks, conversions by channel/campaign/day |
| `fact_orders` | Sales transactions across all marketplaces |
| `fact_inventory` | Inventory snapshots by SKU/warehouse/channel |
| `dim_customer` | Customer attributes, cohort assignment |
| `dim_product` | Product catalog with ASINs, GTINs, Shopify variant IDs |
| `dim_channel` | Channel/marketplace reference data |

### Power BI Strategy

- **DirectQuery** for operational dashboards (D3, D6) — real-time, higher query cost
- **Import** for executive dashboards (D1, D4, D5) — scheduled refresh, faster queries

## See Also

- [[navira/README|Navira Roadmap]]
- [[phase-1a-marketing-ad-platforms]] — data sources for D1, D3, D6
- [[phase-1b-marketing-social-emerging]] — data sources for D6, D7
- [[phase-2-inventory]] — data source for D5 (COGS)
- [[Power BI]] — reporting tool
- [[Snowflake]] — data warehouse
