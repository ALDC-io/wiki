---
tags: [entity, client, adm, fusion92, gcp, bigquery, looker-studio]
aliases: [ADM]
sources: [CF92/1229881345]
created: 2026-04-18
updated: 2026-04-18
---

# ADM

ADM ("ADM marketing dashboard") is a project that lives in the CF92 Confluence space, suggesting it is a [[fusion92]] sub-client or campaign account. Unlike the standard ALDC stack (Eclipse → Snowflake → Power BI), ADM uses a GCP-native stack: BigQuery, Google Cloud Storage, Looker Studio, Funnel.io, and Google Analytics.

> **Relationship to Fusion92:** ADM appears in Fusion92's Smartsheet template list (2024 ADM budget template). The Confluence permissions page is under CF92. The exact client relationship is not fully documented — treat as a Fusion92 sub-client until clarified.

## Stack

| Layer | Tool |
|-------|------|
| Data warehouse | BigQuery (project: `adm-data-374418`) |
| File storage | Google Cloud Storage |
| ETL / data aggregation | Funnel.io |
| Reporting | Looker Studio (Google Data Studio) |
| Analytics | Google Analytics / Firebase |

## GCP Security & Permissions

### User Groups (recommended structure)

| Group | Members | Access |
|-------|---------|--------|
| Martech Integration | Funnel service account, ETL/Funnel devs | BigQuery + GCS write |
| Martech Reporting | Looker service account, read-only data scientists, dashboard editors | BigQuery dataViewer |
| Martech Direct Pub | — | Read/write Google Sheets |
| Martech Developer | — | Full BigQuery + GCS + Looker + Funnel |

### Service Accounts

| Account | Purpose |
|---------|---------|
| `martech-svc-looker@adm.com` | Funnel.io → BigQuery connection |
| `martech-nonprod-copy@adm-data-374418.iam.gserviceaccount.com` | Non-production data copy script |
| `firebase-measurement@system.gserviceaccount.com` | GA sync (system — do not alter) |
| `firebase-adminsdk-50ctn@adm-data-374418.iam.gserviceaccount.com` | Firebase SDK (system — do not alter) |
| `firebase-service-account@firebase-sa-management.iam.gserviceaccount.com` | Firebase service management (system — do not alter) |

> **Note:** Firebase/GA system service accounts must not be modified — GA ↔ BigQuery sync depends on them.

### Key Permission Notes

- **Looker Studio minimum**: `bigquery.jobs.create` + `bigquery.dataViewer` at the dataset/table level. Project-level BigQuery access does NOT cascade to datasets/tables.
- **Funnel.io** requires BigQuery + GCS permissions (see [Funnel docs](https://help.funnel.io/en/articles/1494331-google-bigquery-dataset-configuration)). Prefer service account auth over personal OAuth.
- **BigQuery BI Engine**: 1 GB free capacity allocated; as of 2024-03 investigation, BI Engine appeared not enabled for Looker Studio connections.

### Recommended: Migrate Looker to Service Account

Personal accounts currently authorize the Looker Studio → BigQuery connection. Recommendation: migrate to a dedicated service account (`martech-svc-looker@adm.com`) for tighter permission control.

## Implementation Roadmap (2024)

### Phase 1: Test Environment (target 2024-03-25 – 2024-04-03)
- ✅ BigQuery instance + all datasets
- ✅ Separate Funnel workspace
- ☐ Security groups
- ☐ Service accounts + group connections
- ☐ Separate Looker workspace
- ☐ Separate Funnel data flows (test all workflows)
- ☐ Looker dashboard copy to test workspace
- ☐ GA ↔ BigQuery dual-environment solution
- ☐ Source control tool opportunities

### Phase 2: Production Deployment (target 2024-04-08 – 2024-04-19)
- ☐ Full business team testing
- ☐ Agreed outage window
- ☐ Deploy via source control tools (if possible)

*Roadmap dates are from 2024 Confluence snapshot — status unknown.*

## Security Group Architecture

*Source: CF92/1230700595 — full test environment setup*

Recommended security group structure (replaces the prod→nonprod copy script workflow):

| Group | Members | Permissions |
|-------|---------|-------------|
| Martech Integration | Funnel service account, ETL/Funnel devs | BigQuery + GCS integration access; Funnel workflow management |
| Martech Reporting | Looker service account, read-only report writers, data scientists | Read-only dashboard access; edit Looker dashboard definitions |
| Martech Direct Pub | — | Read/write Google Sheets |
| Martech Developer | — | Elevated BigQuery access; full Sheets + Looker + Funnel |

**Service account deprecation:** The `martech-nonprod-copy@adm-data-374418.iam.gserviceaccount.com` prod→nonprod copy script service account should be discontinued and removed once the separate test environment is in place.

*Note: Phase 1 / Phase 2 implementation timeline is documented in § Implementation Roadmap above.*

## Funnel.io Workspace Configuration

*Source: CF92/1225719814 (meeting 2024-03-20, attendees: Sean O'Grady, Alyssa Kortemeier, Funnel.io team)*

- Create a second Funnel.io workspace for nonproduction testing (use the built-in Workspace feature; copy data warehouse config from the prod workspace).
- **No infrastructure-as-code support in Funnel.io** — nonprod management is manual.
- Adding Pardot, SEM Rush, LinkedIn Organic channels is unlikely to trigger additional Flex Point charges.
- Follow-ups: Paul Buccheri to research prod/nonprod approaches from other Funnel accounts; Sean to train Brayden on Funnel.

## See Also

- [[fusion92]] — parent client (ADM appears as a Fusion92 sub-client)
