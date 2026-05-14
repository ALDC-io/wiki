---
tags: [workflow, fusion92, flight-check, dax, netsuite, client, agency]
aliases: [Fusion92 Workflow, F92 Roadmap]
sources: [analyticlabsdc.atlassian.net/jira/software/projects/FU92]
created: 2026-05-12
updated: 2026-05-13
---

# Fusion 92 — Workflow Hub

Fusion 92 is a digital agency / marketing analytics client. DAX Media App (Flight Check), NetSuite integration, Windsor ad platform connections.

**Contact:** Juliann Otto (j.otto@fusion92.com)
**Jira project:** FU92 · **Board:** 38 (ALDC Scrum)
**Repos:** [[flight-check]], [[workflows]], [[custom-fusion-92-audience-api]]

## Data Correction (2026-05-13)

FU92-400 through FU92-414 (15 tickets created 2026-05-12) were Navira/GEP business meeting items filed under FU92 by mistake. They are being moved to the GP project in Jira. The previous wiki pages here incorrectly listed those as F92 work. Corrected below.

The completed pre-ticket items (Periodicity, Dashboard Rollout, SP Dashboard fixes, SKU Profitability duplication) were also Navira work — moved to Navira context.

## Active Work

### Paul's Current Tickets

| Ticket | Summary | Status | Wiki |
|---|---|---|---|
| FU92-397 | NetSuite PO Employee field shows wrong person | In Progress | [[../../tickets/fusion92/FU92-397]] |
| FU92-396 | DAX JWT role refresh — stale role after login | Done (PR #35 merged) | [[../../tickets/fusion92/FU92-396]] |

### To Do — Bugs & Support

| Ticket | Summary | Priority | Area |
|---|---|---|---|
| FU92-395 | DAX user role error on approved flight — persists after re-login | To Do | Flight Check |
| FU92-393 | Fusion NetSuite in QA — sandbox connection trouble | To Do | NetSuite |
| FU92-387 | Manual Entry Blocked in Metrics Table indicator showing when it shouldn't | To Do | Flight Check |
| FU92-386 | Legacy Flight Check Templates Fail Often | To Do | Flight Check |
| FU92-381 | Locked Fields | To Do | Flight Check |
| FU92-374 | No Scroll Bar on Job Details Page | To Do | Flight Check |

### To Do — Features & Improvements

| Ticket | Summary | Priority | Area |
|---|---|---|---|
| FU92-379 | Flight Check Data Sync Monitoring | To Do | Flight Check |
| FU92-378 | App Improvements and Bugs for Flight Check | To Do | Flight Check |
| FU92-373 | Pacing Notifications — Questions and Updates | Needs Priority | Flight Check |
| FU92-372 | DAX Tech Fee Formula — "Planned Tech Fee" field request | Needs Priority | DAX |

## Workflow Pages

### Active

- [[dashboards-and-data]] — Flight Check app bugs, DAX features, data sync
- [[integrations-and-platform]] — NetSuite integration, Windsor connections

### Backlog

_(Backlog pages removed — uk-ads, forecast-sp-report, subscribe-save-kpis, name-change were all Navira items misfiled under F92)_

### Completed

- [[completed-pre-ticket]] — FU92-396 JWT fix (PR #35), FU92-394 Viant DSP fix, FU92-398 Meta investigation

## See Also

- [[fusion92]] — client entity page
- [[fusion92-data-architecture]] — data architecture overview
- [[fusion92-platform-ids]] — platform IDs reference
- [[navira/README]] — Navira (separate client, misfiled tickets being corrected)
