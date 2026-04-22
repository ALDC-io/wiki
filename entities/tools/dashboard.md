---
tags: [entity, tool, dashboard, eclipse, cosmosdb, core-api]
aliases: [Eclipse Dashboard, Dashboard Feature, ALDC Dashboard]
sources: [Confluence CORE/1078525953]
created: 2026-04-18
updated: 2026-04-18
---

# Eclipse Dashboard Feature

> *Sourced from CORE Confluence (2024-07) — verify current state.*

Custom dashboard charts rendered in the Eclipse portal. Backed by two [[CosmosDB]] documents plus one Postgres `report` row.

## Data Model

One dashboard requires three documents:

| Store | Document type | Foreign key |
|---|---|---|
| Postgres | `report` | → `dashboard_id` |
| CosmosDB | `dashboard` | → `dataset_id` |
| CosmosDB | `dataset` | (none — root) |

### Dashboard document (CosmosDB)

```json
{
  "account_id": "f49f9aa3",
  "description": "My Dashboard",
  "dashboard_detail": [
    {
      "row": 0,
      "col": 0,
      "width": 5,
      "height": 3,
      "chart_type": "card",
      "title": "Trip Distance",
      "subtitle": "..."
    }
  ]
}
```

`dashboard_detail` is an array of chart configs — each has position (`row`, `col`), size (`width`, `height`), `chart_type`, and display strings.

### Dataset document (CosmosDB)

Contains dimension and metric definitions used by charts in the dashboard. Referenced from the `dashboard` document via `dataset_id`.

### Report row (Postgres)

The `report` table entry in the portal Postgres DB links the Postgres report record to the CosmosDB `dashboard` document via `dashboard_id`.

## Synapse Analytics Integration

Dashboard data can be exposed to Synapse SQL views for analytics. See [[synapse-analytics-setup]] for how to create `OPENROWSET` views against CosmosDB collections.

## See Also

- [[cosmosdb-schema]] — full CosmosDB collection reference
- [[core_api]] — API that manages dashboard/dataset documents
- [[synapse-analytics-setup]] — querying CosmosDB from Synapse serverless SQL
- [[Eclipse]] — the portal that renders dashboards
