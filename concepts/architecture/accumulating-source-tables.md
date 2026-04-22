---
tags: [architecture, snowflake, eclipse, ingestion, qa, data-modeling]
aliases: [moving target source tables, CURRENT_REPORT accumulation, history timestamp dedup]
sources: [GP-208 Phase 1 QA session 2026-04-16, inventory_fct_balance.sql]
created: 2026-04-16
updated: 2026-04-16
---

# Accumulating Source Tables (`CURRENT_REPORT_*`, `CURRENT_MAIN_*`)

[[Eclipse]] ingestion writes to tables prefixed `CURRENT_REPORT_*` and `CURRENT_MAIN_*`. Despite the `CURRENT_` naming, these tables **retain multiple historical ingestion batches** per natural key. Each batch is stamped with `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___`.

## Why this matters

- A naive `SELECT * FROM CURRENT_REPORT_FBA_INVENTORY` returns **all historical rows**, not just the latest snapshot — one row per SKU per ingestion batch
- To get "latest per natural key", consumers must explicitly deduplicate:

```sql
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY <natural_key>
    ORDER BY ___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___ DESC
) = 1
```

## Testing implications — "moving target" property

Any fact table built from a `CURRENT_REPORT_*` source has the property that **latest-per-key at time T can differ from latest-per-key at time T+N** if new batches arrive between the two reads. This breaks naive reconciliation between a materialized fact and a direct-to-source query unless both observe the same snapshot.

Measured during [[GP-208]] Phase 1 QA against `CURRENT_REPORT_FBA_INVENTORY` (6,226 SKUs):

| Drift between CTAS and verification | Reconciliation delta | What it looked like |
|---|---|---|
| **~8 hours** (CTAS in morning, QA in afternoon) | 0.8% unit delta across measures | Directional signs matched real inventory flow: working↓, shipped↑, available↑, reserved↑ |
| **~0 seconds** (rebuild and query in same session) | 0.18% residual | Same-timestamp tie-breaking inside one batch produced ~1 row and ~585 units of drift across 316K |

## QA workflow for any fact using these sources

1. **Drift diagnostic**: compare `MAX(fact.CAPTURE_TIMESTAMP)` against `MAX(source.___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___)`. If >60s, source has been refreshed since the fact was built
2. **Rebuild in session**: rerun the CTAS and the reconciliation query back-to-back in the same Snowflake worksheet to minimise drift
3. **Acceptable tolerance**: ≤1% unit delta and ≤5 row delta is passing for Phase 1 current-snapshot facts. Tighter is unrealistic given upstream refresh cadence

## Phase 2 benefit — free history

The accumulated batches *are* the history. An append-only fact can ingest incrementally:

```sql
INSERT INTO WAREHOUSE.<fact>
SELECT ... FROM WAREHOUSE_SOURCE.<fact>
WHERE CAPTURE_TIMESTAMP > (SELECT MAX(CAPTURE_TIMESTAMP) FROM WAREHOUSE.<fact>);
```

No separate historical-ingestion pipeline needed; the source tables are already storing what we need.

## Applicability

Any GEP fact that reads from:

- `AMAZON.CURRENT_REPORT_*` (FBA inventory, orders, returns, sales-and-traffic, etc.)
- `SELLERCLOUD_SQL.CURRENT_MAIN_*` (orders, order items, products, purchases, etc.)
- Similar `CURRENT_*` patterns in other client environments

Check by running `SELECT COUNT(*) FROM <table> GROUP BY <natural_key> HAVING COUNT(*) > 1 LIMIT 5;` — if any keys return, the table is accumulating.

## See Also

- [[GP-208]] — first documented occurrence and empirical drift measurement
- [[gep-inventory-data-dictionary]] — production example of the dedup pattern
- [[snowflake-data-share-refresh]] — related but distinct concern (atomicity, not accumulation)
- [[Eclipse]] — ingestion platform that writes these tables
- [[Snowflake]] — warehouse platform
