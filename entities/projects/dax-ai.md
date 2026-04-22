---
tags: [entity, project, fusion92, dax, dashboard, analytics]
aliases: [DAX AI, DAX Dashboards, DAX Analytics]
sources: [CF92/1200553996, CF92/1206779939, CF92/1236598785, CF92/1212678200]
created: 2026-04-18
updated: 2026-04-18
---

# DAX AI

DAX AI is [[fusion92]]'s integrated analytics dashboard product family, built by ALDC. "DAX" = Fusion92's product family name for ALDC-built tools. Includes the [[dax-media-app]] (Flight Management / Flight Check replacement) plus multiple reporting dashboards.

## Product Overview

| Component | REQ | Status | Description |
|-----------|-----|--------|-------------|
| DAX Media App (Flight Check) | REQ-196 | **COMPLETE** | See [[dax-media-app]] |
| Activation Model | REQ-267 | CLIENT TESTING | Audience activation + pacing |
| Performance Summary Dashboard | REQ-198 (CUST-720) | **ON HOLD** | Internal real-time pacing dashboard |
| Financial Reporting Dashboard | REQ-234 (CUST-770) | **ON HOLD** | Internal financial reconciliation |
| External Dashboard (Datorama Replacement) | REQ-215 (CUST-750) | **DEFERRED** | External client-facing reporting |
| Media Planning | REQ-200 | **DEFERRED** | — |

*Source: CF92/1200553996*

---

## Performance Summary Dashboard (REQ-198 / CUST-720)

*Status: ON HOLD. Source: CF92/1236598785*

Internal real-time pacing dashboard for Media Planners and the Activation Team.

**RACI:** Responsible — Mitchell Pask. Accountable — Johanna Berger, Aaron Stryd, Karen Prete. Informed — John Moran, Sean O'Grady, Dave Nugent.

### Users & Purpose

| User | Goal |
|------|------|
| F92 Media Planners | Track campaign pacing in real time; adjust if off-track |
| Activation Team | Monitor planned budget vs. actuals |

**Background:** Currently managed via Excel and SmartSheets.

### Metrics Required

**For Media Planners:** Cost, Impressions, Clicks, Frequency, Viewability Rate, Conversion Activity (Forms/Calls), Time Viewed, Campaign Code, CPM, CPC, CPA *(CPA definition varies by campaign — clarification needed)*

**For Activation Team:** Planned budget, Actuals (gross / net / platform), roll-up to campaign code

### Workflow

1. Media Planner sends audience discovery request → D&A team recommends audience size + CPM
2. Media Planner builds frequency-based plan, estimates impressions + costs
3. Plan booked into Flight Check ([[dax-media-app]])
4. Activation Team buys media
5. Actuals entered into SmartSheets
6. Planner reviews Performance Summary Dashboard; adjusts plan as needed

---

## Financial Reporting Dashboard (REQ-234 / CUST-770)

*Status: ON HOLD. Source: CF92/1206779939*

Internal financial reconciliation dashboard for D&A, Media Finance, AP, and Media Planners.

**RACI:** Responsible — Mitchell Pask. Accountable — Johanna Berger, Aaron Stryd, Karen Prete. Informed — John Moran, Sean O'Grady, Dave Nugent.

### Users & Purpose

| User | Goal |
|------|------|
| D&A Team | Report actual vs. planned impressions |
| Media Finance Team | Approve invoices, code media/D&A costs, reconcile |
| AP Team | Approve + pay vendor invoices; track vs. insertion order |
| Media Planners | Review performance; improve future estimates |

**Background:** Currently managed via Excel and SmartSheets.

### Metrics Required

**D&A + Media Finance:** Planned impressions, Actual impressions, Gross CPM, Cost from impressions to CPM

**Media Finance + AP + Media Planners:** Planned impressions, Actual impressions, Impressions Variance (% + value), Budget, Actual spend, Financial Variance (% + value), Platform, Publisher, [[Snowflake]] media project codes, NetSuite project code per campaign code

**Dimensions & Filters:** Channel, Customer, Campaign Code, Flight ID, Date, Platform. Roll-up to campaign code.

### Workflow (same as Performance Dashboard)

Media Planner → D&A recommendation → plan → Flight Check ([[dax-media-app]]) → Activation buys → AP enters invoices into SmartSheets → Actuals entered → Financial dashboard reviewed.

---

## External Dashboard — Datorama Replacement (REQ-215 / CUST-750)

*Status: DEFERRED. Source: CF92/1212678200*

External client-facing dashboard to replace Datorama. Largely a stub — requirements not yet defined.

- Report available to multiple external customers
- Internal Fusion team should be able to switch between customers
- Customer access mechanism TBD
- RACI not yet assigned

---

## See Also

- [[dax-media-app]] — DAX Media App (Flight Check replacement) — the active/shipped DAX product
- [[fusion92]] — client; all DAX products built for Fusion92
- [[Snowflake]] — data platform underlying the dashboards
- [[fusion92-data-architecture]] — Fusion92 Snowflake + data stack decisions
