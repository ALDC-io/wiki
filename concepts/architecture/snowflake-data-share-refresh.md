---
tags: [architecture, snowflake, data-share, refresh, reliability, incident]
aliases: [share refresh behavior, CREATE OR REPLACE across shares, share atomicity, frozen share]
sources: [GP-208 Phase 1 deploy conversation 2026-04-16, GP-208 Sellercloud staleness incident 2026-04-16]
created: 2026-04-16
updated: 2026-04-16
---

# Snowflake Data Share Refresh Behavior

Cross-cutting operational concern for any [[GEP]] (or other ALDC-client) table that is read **through a Snowflake data share** while also being rebuilt via `CREATE OR REPLACE TABLE` on the producer side.

## The pattern

Producer-side warehouse tables use full-replace refresh:

```sql
CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT ... ;
```

This is **atomic within the producer database** — consumers inside the producer DB see either the old version or the new version, never a broken/missing state.

Across a **Snowflake data share**, the behavior depends on how the consumer references the object:

| Reference style | Behavior during refresh |
|---|---|
| **By name** (SQL: `SELECT ... FROM PROD_DG1_GEP.WAREHOUSE.X`) | Transparent handoff — new version becomes visible once the CREATE completes; no gap for readers |
| **By UUID / cached metadata** (some BI tools, introspection queries) | Object may appear to briefly disappear during the refresh window because the underlying object identity changes |

## Observed symptom

Tables in the `PROD_DG1_GEP` outbound share (example: `PURCHASING_FCT_BALANCE`) displayed in the Snowflake UI as "Created N minutes ago" with a fluctuating row count. The metadata-cache view may even show the table temporarily absent from the share, but `SELECT` queries against it continue to succeed as long as the consumer is referencing by name.

## Impact on [[GP-208]] Phase 1

Our inventory fact reads:

- **Raw sources** (`PROD_DG1_GEP.AMAZON.*`, `PROD_DG1_GEP.SELLERCLOUD_SQL.*`) — **via share**. Susceptible to this concern.
- **Derived warehouse** (`WAREHOUSE.PURCHASING_FCT_BALANCE`, `WAREHOUSE.SHARED_DIM_PRODUCT`) — **unprefixed**, resolves to current DB, **not** via share. Each env's scheduled task keeps its local copy fresh independently.

Net: share-refresh exposure is limited to raw sources. A scheduled fact refresh that happens to hit a mid-refresh source table could fail; next run should succeed.

## Mitigation options

| Tactic | When to use | Cost |
|---|---|---|
| **Snowflake task retry (`AFTER` + `ERROR_INTEGRATION`)** | Scheduled refreshes that might collide with producer refresh windows | Low — built-in feature |
| **Buffer view in consumer** (consumer's own view that wraps the shared object) | High-frequency refresh sources; downstream cannot tolerate transient failures | Medium — extra layer; only helps certain failure modes |
| **Eventual-consistency tolerance** | Facts where a single missed run is acceptable | Zero |
| **Coordinated refresh windows** | When producer and consumer cadences can be scheduled to not overlap | High — cross-team orchestration |

**Default recommendation for GEP**: rely on Snowflake task retry with alerting. Anything more elaborate is premature until a real incident proves it necessary.

## Failure mode 2 — Frozen share (no new data propagating)

Distinct from transient refresh collisions. Here the share itself stops propagating new writes indefinitely.

### Observed symptom (GP-208, 2026-04-16)

- `PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL` and `COMBINED_MAIN_INVENTORY_PANDL` stuck at `MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___) = 2026-03-05 07:01 PST` for 42 days
- Eclipse connector ("GEP Seller Cloud VPN" template, `schema: dbo`, `table: INVENTORY_PANDL`) running healthy — partitions completing multiple times daily
- Both CURRENT and COMBINED views equally stale (rules out view-layer filter bugs)

### Why this is hard to notice

- Eclipse shows partitions as Complete — no alerting signal there
- Consumer-side SELECTs continue to succeed (data is present, just old)
- The Snowflake UI `LAST_ALTERED` timestamp on shared views only reflects view-definition changes, not data updates
- Clients who aren't actively using the affected views won't see broken dashboards

### Detection queries

```sql
-- Quick freshness check for any shared raw source
SELECT
    MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___) AS LATEST_INGEST,
    DATEDIFF(DAY, MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___), CURRENT_TIMESTAMP()) AS DAYS_STALE,
    COUNT(*) AS ROW_COUNT
FROM PROD_DG1_GEP.<schema>.<shared_view>;

-- Cross-check with producer-side Eclipse template run history to triangulate:
-- if Eclipse says "Complete" but consumer view is stale, the freeze is producer-side.
```

### Root cause hypotheses (not yet confirmed)

- Producer-side scheduled task that refreshes the shared object stopped running
- Producer account's share permissions / grants silently lapsed
- Producer made a `CREATE OR REPLACE TABLE` change that broke the share link (requires regrant)
- "Warehouse reset" operation (Paul flagged as possible fix, exact meaning unknown) may be required producer-side to re-establish propagation

### Recommended investigation path

1. Confirm the Eclipse template is writing to the *same* Snowflake account and database that produces our share (don't assume — producer may have multiple landing zones)
2. On the producer account, check last-altered timestamp of the actual base table (not the shared view) — is it fresh there?
3. If producer has fresh data but share doesn't reflect it → share regrant / `ALTER SHARE` operation needed
4. If producer is also stale → follow the Eclipse → producer path; there's a downstream-of-Eclipse task that's broken

### Monitoring recommendation (post-mortem action)

Add a Snowflake scheduled task or external monitor that runs the freshness detection query above nightly against key shared sources, alerting when `DAYS_STALE > N`. Avoids future 40+ day undetected freezes.

## What to check if a fact refresh fails

1. `SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(...))` to see the error message
2. If error mentions "object not found" or "cannot resolve": the source probably dropped during the run
3. If error is the **first** of a sequence and the **next** scheduled run succeeded → confirmed transient share-refresh collision; no action needed
4. If errors repeat across runs → investigate producer's refresh schedule and consider retry config

## See Also

- [[GP-207]] — prod-to-test data share setup that established this pattern
- [[GP-208]] — first ticket where transient-collision concern was raised; also where frozen-share failure mode was discovered
- [[accumulating-source-tables]] — related but distinct concern (many rows per key, not atomicity)
- [[Snowflake]] — platform page
- [[gep-snowflake-pbi-deployment]] — deployment runbook (candidate spot to codify task retry config)
- [[data-share-pattern]] — outbound/inbound share setup mechanics
