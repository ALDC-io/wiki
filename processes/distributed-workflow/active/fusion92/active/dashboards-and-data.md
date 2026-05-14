---
tags: [workflow, fusion92, flight-check, dax, dashboards, bugs]
aliases: [F92 Dashboards, Fusion92 Dashboard Work]
sources: [analyticlabsdc.atlassian.net/jira/software/projects/FU92]
created: 2026-05-12
updated: 2026-05-13
---

# Fusion 92 — Dashboards & Data

Flight Check app bugs, DAX features, and data sync work.

> **Note (2026-05-13):** Previous content here was Navira/GEP work (SKU Profitability, Marketing Dashboard, BSR, Google Ad Spend) filed under FU92 by mistake. Those tickets are being moved to the GP project. This page now reflects actual Fusion92 work.

## Flight Check — Bugs

| Ticket | Summary | Priority | Status |
|---|---|---|---|
| FU92-395 | DAX user role error on approved flight — persists after re-login | To Do | May relate to FU92-396 (JWT fix shipped) |
| FU92-387 | Manual Entry Blocked in Metrics Table indicator showing incorrectly | To Do | Flight Check UI bug |
| FU92-386 | Legacy Flight Check Templates Fail Often | To Do | Template reliability |
| FU92-381 | Locked Fields | To Do | Field editing bug |
| FU92-374 | No Scroll Bar on Job Details Page | To Do | UI bug |

## Flight Check — Features

| Ticket | Summary | Priority | Status |
|---|---|---|---|
| FU92-379 | Flight Check Data Sync Monitoring | To Do | Monitoring/observability |
| FU92-378 | App Improvements and Bugs (umbrella) | To Do | General improvements |
| FU92-373 | Pacing Notifications — Questions and Updates | Needs Priority | Notification system |
| FU92-372 | DAX Tech Fee Formula — "Planned Tech Fee" field | Needs Priority | DAX feature request |

## Completed

| Ticket | Summary | Resolution |
|---|---|---|
| FU92-396 | DAX JWT role refresh — stale role cached from login | Fixed: PR #35 merged. 5-min TTL role refresh via user/list endpoint. |
| FU92-394 | Viant DSP actuals missing after 4/2 | Fixed: connector polling timeout → schedules re-enabled |
| FU92-398 | Meta investigation — spend drop | Closed: no data loss, campaign volume change |

## See Also

- [[integrations-and-platform]] — NetSuite, Windsor
- [[../README]] — F92 workflow hub
