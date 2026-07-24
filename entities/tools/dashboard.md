---
tags: [entity, tool, dashboard, eclipse, cosmosdb, core-api]
aliases: [Eclipse Dashboard, Dashboard Feature, ALDC Dashboard]
sources: [Confluence CORE/1078525953]
created: 2026-04-18
updated: 2026-07-24
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

## eclipse-2.1 "explorer" dashboards (current)

The section above is the **legacy** dashboard model. The current eclipse-2.1 client
dashboards (rendered at `eclipse.analyticlabs.io`; admin at `eclipse.aldc.io`) use a
different set of [[CosmosDB]] containers in db `core`:

| Container | Role |
|---|---|
| `explorer_dashboard` | dashboard doc — `layout[].components[]` each reference a `visual_id` |
| `explorer_visual` | one doc per visual — holds `options` (visual_type, fields, measures, table flags) |
| `explorer_dataset` | dataset/model backing the visuals |

Partition key is `/account_id`. The Global Ecom Partners account (`da8904db`) hosts the
NAVIRA brand-dashboard family — ~59 dashboards (Brinno, Slobproof, Bigso, …).

### Table trend-comparison columns (`comparison_measures`)

Table visuals can show Prev % / YoY % columns. Governed by two `options` fields
(schema `core_api/api/visuals/schema.py`, logic `deps.py`):

- `show_previous_period: bool` — master switch; must be `true` for *any* comparison column.
- `comparison_measures: list[str] | null` — **which** measures get Prev%/YoY%.
  `null` (unset) = **all** measures; a list = only those measures. Strings must match
  the visual's `options.measures` **display names exactly** — a non-matching name silently
  renders **no** column (no error). Covered by `test_comparison_measures_subset` +
  `test_nonexistent_comparison_measures_no_crash`.

To limit comparison to one measure: set `comparison_measures=["<exact measure name>"]`
(and `show_previous_period=true` if it wasn't already on).

### Gotchas (learned the hard way — GP-298, 2026-07-24)

1. **Visuals are SHARED across dashboards.** One `explorer_visual` doc is referenced by
   many `explorer_dashboard` layouts, so editing its `options` changes **every** dashboard
   that renders it — there is no per-dashboard override without cloning the visual. Before
   any edit, map the blast radius: query all dashboards on the account and count references
   to the target `visual_id`. GP-298's "Brinno-only" edit actually hit 30–31 brand dashboards.
2. **Verify the visual by ID from the rendered dashboard's layout — never trust the ticket's
   name/ID.** GP-298 named `34fc12de` "Units by SKU" for Brinno's Units table, but Brinno
   actually renders `c00bc2d2` "Units by SKU *with RR%*" (a different visual with an extra
   measure). Two similarly-named visuals existed; only reading the dashboard's `layout`
   components revealed the true target. Cross-check rendered measure columns vs the doc's
   `options.measures` — a count mismatch means you're looking at the wrong visual.
3. **The browser caches the column layout.** After a Cosmos write the change is live
   immediately, but the client dashboard keeps serving the old columns until a **hard reload
   (Ctrl+Shift+R)**. A plain reload is not enough. If a client says "I don't see the change,"
   this is almost always why.

### Editing safely

Data-only edits go straight to prod Cosmos (`aldcprodcsdb1c01`, RG `aldcprodrsgp1c`,
sub "Production 2"; key via `az cosmosdb keys list ... --query primaryMasterKey`). Pattern
(see `aldc-launchpad/eclipse_ops/_gp298_*.py`): read-only inspect → capture rollback JSON of
each visual's `options` → dry-run with a drift guard (abort if live `measures` ≠ scoping
snapshot) + subset guard → `--apply` → **validate at the rendered layer** (hard-reload the
actual dashboard, confirm columns) with before/after screenshots.

## Synapse Analytics Integration

Dashboard data can be exposed to Synapse SQL views for analytics. See [[synapse-analytics-setup]] for how to create `OPENROWSET` views against CosmosDB collections.

## See Also

- [[cosmosdb-schema]] — full CosmosDB collection reference
- [[core_api]] — API that manages dashboard/dataset documents
- [[synapse-analytics-setup]] — querying CosmosDB from Synapse serverless SQL
- [[Eclipse]] — the portal that renders dashboards
