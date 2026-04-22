---
tags: [entity, client, kit-ace, retail, apparel, netsuite, google-analytics]
aliases: [KIT_ACE, Kit & Ace, Kit and Ace]
sources: [Confluence CLIEN/564658177, Confluence CLIEN/881426433, Confluence CLIEN/884539393]
created: 2026-04-18
updated: 2026-04-18
---

# KIT_ACE (Kit and Ace Technical Apparel Inc.)

> Note: KIT_ACE has a dedicated Confluence space (CKA) which has not yet been migrated. These pages are from the general CLIEN space and represent the 2021 discovery and build phase.

## Client Overview

Retail apparel client. Finance model + Google Analytics reporting. Primary contact: Kateryna Petrova (`Kateryna.Petrova@kitandace.com`).

Data warehouse follows the ALDC Standard Retail Dimensional Model — same shared dimensions as [[dish-duer]] and other retail clients.

## Finance Model

### Refresh Schedule

- Every 2 hours (critical for month-end operations)
- Production retention: 72 months; Test retention: 12 months
- High-frequency tables: GL, Inventory Balances, Transaction

### Object Level Security (OLS)

Two consumer roles: **Inventory** (limited) and **Finance** (full access).

| Object | Inventory | Finance |
|---|---|---|
| Account | ✗ | ✓ |
| Budget | ✗ | ✓ |
| Currency | ✗ | ✓ |
| Date | ✓ | ✓ |
| Department | ✗ | ✓ |
| Financial Statement | ✗ | ✓ |
| General Ledger | ✓ | ✓ |
| GL Derivatives | ✓ | ✓ |
| Inventory | ✓ | ✓ |
| Inventory Balances | ✓ | ✓ |
| Inventory Item | ✓ | ✓ |
| Item Cost | ✓ | ✓ |
| Location | ✓ | ✓ |
| Model Metadata | ✓ | ✓ |
| Periodicity | ✗ | ✓ |
| Subsidiary | ✓ | ✓ |
| Transaction | ✓ | ✓ |
| Vendor | ✓ | ✓ |
| Version | ✗ | ✓ |

### Key Data Tables

**Transaction** (primary fact)
- Source: NetSuite ER
- Grain: item, customer, vendor
- Amounts: `AMOUNT_TRANSACTION` (local/transaction currency), `AMOUNT_SUBSIDIARY`, `AMOUNT_CONSOLIDATED`
- `SALES_QUANTITY`: item count

**Budget**
- Source: NetSuite
- Grain: Location, account, subsidiary, date (month-level)
- Versioned: annual with Q2/Q3/Q4 planning cycle updates
- `Budget Shape` breaks monthly budget into daily granularity

**Income Collapse / Net Income / Retained Earnings**
- Compensate for NetSuite gap (no formal month-end closing)
- Net Income: derived from Income Collapse; resets at year-start
- Retained Earnings: fixed value at year-start

**Inventory Balances**
- Source: NetSuite
- New row written only on balance change
- Inventory status values: On Hand, On Order, In Transit, Committed (flagged for shipment; BOPIS, uninspected returns), Available
- Includes cost and price metrics

**General Ledger (GL):** Transaction header data.

**Financial Statement:** Selector object for different financial report roll-ups.

**Subsidiary:** Drives currency, financial settings; represents companies under the parent entity.

## Google Analytics Integration

### Dimensions

| Category | GA Field | Examples |
|---|---|---|
| Products | `ga:productName`, `ga:productSku` | Not compatible with all measures |
| Dates | `ga:date`, `ga:dateHourMinute` | Minute granularity from 2020-11-01 |
| Channel | `ga:channelGrouping` | Affiliates, Direct, Display, Email, Organic Search, Paid Search, Referral, Social |
| Source | `ga:source` | businesswire.com, ca.search.yahoo.com, cn.bing.com |
| Medium | `ga:medium` | affiliate, cpc, display, email, organic, Paid_Social, referral |
| Site Content | `ga:pagePath` | /ca/en/sale/women, /ca/en/limitless-dress/KWD10089.html |
| Geography | `ga:country`, `ga:region` | Canada; Alberta, BC, Manitoba, etc. |
| Search Term | `ga:keyword` | branded + category terms |
| Affinity Category | `ga:interestAffinityCategory` | Banking/Avid Investors, Beauty/Beauty Mavens, etc. |
| Device | `ga:deviceCategory` | desktop, mobile, tablet |
| Campaign | `ga:campaign` | #1025 - Women's Shorts, #1034 - Men's Cotton Terry Sweats, etc. |

### Measures

**Transaction & Revenue:** Transaction Revenue (`ga:transactionRevenue` — not compatible with Product dims), Product Revenue (`ga:itemRevenue`), Average Price (`ga:revenuePerItem`)

**User & Session:** Users, New Users, Sessions, Ecommerce Conversion Rate (`ga:transactionsPerSession`)

**Engagement:** Bounce Rate, Pages/Sessions, Avg Session Duration, Pageviews, Unique Pageviews, Avg Time on Page

**Search:** Total Unique Searches, Results Pageviews/Search

**Cart Behavior:** Cart-to-Detail Rate, Buy-to-Detail Rate

### K&A Performance Forecast (Custom)

Maintained in Google Spreadsheet (Brayden), supplemented by GA data.

**Cost dimensions tracked:** Google, Bing, Affiliate, Criteo, Facebook Dynamic Retargeting, Paid Social (Conversion/Dynamic Prospecting/Traffic), Display (UF/LF), Discovery, Email, Email Acquisition.

**Aggregated cost:** Performance Total (excluding/including Email Acquisition).

**Derived metrics:** ROAS (Revenue / Total Spend), AOV, Conversion Rate, Cost per Order, Cost per Session.

### GA Reports

- GA - Product Performance
- GA - Sales Performance
- GA - Pageviews
- GA - Channel
- GA - Search Terms
- GA - Location
- GA - Affinity Categories
- K&A Performance Forecast

## Account Details (2021)

Source: Confluence CLIEN/674791449.

| Field | Value |
|---|---|
| Account ID | `8425e311` |
| Storage Account | `aldcdevstac` |

**Staff users and Excel Model access (as of 2021):**

| Name | Email | Models |
|---|---|---|
| Kateryna Petrova | `kateryna.petrova@kitandace.com` | Inventory, Finance |
| Melissa Kinnoch | `melissa.kinnoch@kitandace.com` | Inventory, Finance |
| Nick Kim | `chunghyun.kim@kitandace.com` | Finance |
| Kent Whalley | `kent.whalley@kitandace.com` | Inventory, Finance |
| Michael Cruickshank | `michael.cruickshank@kitandace.com` | Inventory, Finance |
| Jacqueline Williams | `jacqueline.williams@kitandace.com` | Inventory |
| Noah Yuswack | `noah.yuswack@kitandace.com` | Inventory |
| Gina Gotch | `gina.gotch@kitandace.com` | Inventory |

Excel Model logins follow the pattern `firstname.lastname@kitandace.aldc.io`.

## Ecommerce Systems (2021)

Source: Confluence CLIEN/665583621.

**Salesforce Commerce Cloud (SFCC):** Managed by PDX (PM: Katie Porter, Dev: Julie Osborne). Major topics: Orders, Customers, Campaigns, Catalog, Gift Certificates. Integration via "Okapi" API calls. Credentials (staging) in `vault/infra-credentials.md` § KIT_ACE — SFCC.

**Google Tag Manager:** Managed by PDX (K&A handles small changes).

**Google Analytics:** Managed by K&A. Test API key in `vault/infra-credentials.md` § KIT_ACE — Google Analytics API Key.

**Camacc SQL Server (Time of Flight cameras):** Connection credentials in `vault/infra-credentials.md` § KIT_ACE — Camacc SQL Server.

## See Also

- [[dish-duer]] — similar retail client (also DISH_DUER, standard retail dimensional model)
- [[star-schema-convention]] — ALDC dimensional model conventions
- [[periodicity]] — SHARED_DIM_PERIODICITY used in Finance Model
- [[nextcloud]] — client tenant access (Kat Kateryna.Petrova@kitandace.com)
- [[power-bi]] — report_common views include KIT_ACE-specific views
