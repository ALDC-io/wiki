---
tags: [ticket, gep, data-share, snowflake, operations, pending]
aliases: [GP-PENDING-data-share-stability, Data Share Stability, Share Gap Detection]
sources: []
created: 2026-04-21
updated: 2026-04-21
last_incident: 2026-04-22
---

# GP-PENDING — Prod-to-Test Data Share Stability

Research and implement a reliable mechanism to detect and prevent `PROD_DG1_GEP` share
gaps before they cause task chain failures at deploy time.

## Status

`pending` — not yet filed in Jira. Raised after the `CURRENT_REPORT_ALL_ORDERS_UK` gap
caused a sandbox task chain failure during GP-197 development (2026-04-21).

## Problem

The `PROD_DG1_GEP` outbound share occasionally loses tables — either because:

- A table is recreated via `CREATE OR REPLACE TABLE` during an Eclipse refresh cycle and
  the share grant is not re-applied (object-level grants do not survive object replacement)
- A new table is added to PROD by Eclipse (e.g. a new Amazon marketplace feed) but is never
  explicitly added to the outbound share

Gaps are **invisible until runtime**: the share object appears valid, the sandbox clone
succeeds, SQL files deploy cleanly — the failure only surfaces when the task chain tries to
expand a view that references the missing shared object.

### Known incidents

| Date | Missing object | Resolution |
|---|---|---|
| 2026-04-18 | `SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL` | Re-added manually during GP-208 Phase 1 session |
| 2026-04-20 | (GP-200 era) `CURRENT_MAIN_PURCHASEITEM`, `CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT` | Re-added manually (noted in [[GP-207]]) |
| 2026-04-21 | `AMAZON.CURRENT_REPORT_ALL_ORDERS_UK` | Flapping — dropped mid-day post-deploy; re-added manually. See timeline below. |
| 2026-04-22 | `AMAZON.CURRENT_REPORT_ALL_ORDERS_UK` | Dropped again (second recurrence in 2 days). Detected via `deploy.py --check-share` during [[GP-208]] sandbox pre-flight. Re-added manually by Paul. |
| 2026-04-22 | `SUPPLEMENT.CURRENT_FORECAST_CSV` | First observed failure for this object. Detected via `deploy.py --check-share` during [[GP-208]] sandbox pre-flight. Re-added manually by Paul. |

Pattern: every few tickets, a table drops out of the share and is only discovered when a
sandbox or TEST deploy fails. Manual fix takes 5–15 minutes but is a recurring interrupt.

### 2026-04-21 flap — `CURRENT_REPORT_ALL_ORDERS_UK`

This incident is material because the table **disappeared post-deploy**, not at deploy time:

| Time (PDT) | Event |
|---|---|
| 2026-04-21 06:00 | `TASK_WAREHOUSE_ORDERLINE_0` cron run **succeeded** → UK table was present in share |
| 2026-04-21 ~06:00 – ~13:26 | UK table dropped from share (no manual action by Paul) |
| 2026-04-21 13:26 | Next task run **failed**: `Object 'PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK' does not exist or not authorized` |
| 2026-04-21 14:24 | Paul re-added table to share; manual task re-run **succeeded** |

Rules out "forgot to add it" as a cause — the grant was present and then was revoked by
something. Most likely culprit: an Eclipse refresh cycle running `CREATE OR REPLACE TABLE`
between 06:00 and 13:26, which drops object-level share grants. This is strong evidence
that **Option D** (Eclipse post-load re-grant) or **Option A** (future grants that survive
object replacement) is the right fix — a detection-only option (B/C) would have caught this
later but not prevented the task-chain failure and the subsequent interrupt.

## Goal

Zero surprise share gaps at deploy time. The fix should be discovered proactively (before
triggering the task chain) and ideally prevented entirely.

## Options for Research

### Option A — Future grants on the share (preferred starting point)

Replace per-table share grants with schema-level grants including `FUTURE` coverage:

```sql
-- On PROD account as ACCOUNTADMIN
GRANT USAGE ON ALL TABLES IN SCHEMA PROD_DG1_GEP.AMAZON TO SHARE <share_name>;
GRANT USAGE ON FUTURE TABLES IN SCHEMA PROD_DG1_GEP.AMAZON TO SHARE <share_name>;
-- Repeat for AMAZON_ADS, SELLERCLOUD_SQL, SUPPLEMENT
```

**Pros:** One-time fix. Any new table added to a shared schema is automatically included.
`CREATE OR REPLACE TABLE` still drops the object-level grant but the schema future grant
re-covers it on next table creation.

**Cons:** Requires ACCOUNTADMIN on the PROD account. Need to verify Snowflake edition
supports `FUTURE` share grants (available on Business Critical and above; confirm GEP's
edition). Schema-level grants expose ALL tables — verify no tables in those schemas should
be withheld from the share.

**Research needed:** Confirm Snowflake edition. List all tables in each schema to verify
none should be excluded. Check whether `CREATE OR REPLACE TABLE` resets the future grant
coverage or requires the grant to be re-issued.

---

### Option B — Share audit script run pre-deploy

A script (`GEP/scripts/audit_share.py` or integrated into `deploy.py`) that enumerates
all `PROD_DG1_GEP.*` references across warehouse SQL files and confirms each is accessible
before any deploy proceeds.

```python
# Pseudocode
refs = find_prod_refs(all_warehouse_sql_files)   # regex scan
for ref in refs:
    execute(f"SELECT 1 FROM {ref} LIMIT 1")       # fails fast if missing from share
```

**Pros:** Catches gaps against the full task chain dependency tree, not just the files
being deployed. Can be run as a standalone health check independent of deploys.

**Cons:** Only catches gaps at the point of running — does not prevent them. Adds latency
to the pre-deploy step (one query per shared object; could be ~50 queries). Does not help
if a gap opens between audit and task chain execution.

**Relationship to existing pre-flight:** `deploy.py` already has a pre-flight check
(`preflight_check`) but it only queries objects referenced in the files being deployed.
This option extends coverage to the full warehouse SQL set. See [[gep-snowflake-pbi-deployment]].

---

### Option C — Snowflake monitoring task on non-prod

A scheduled Snowflake task in `TEST_DG1_GEP` that runs daily and probes each known
`PROD_DG1_GEP.*` object:

```sql
CREATE OR REPLACE TASK TEST_DG1_GEP.OPERATIONS.TASK_SHARE_HEALTH_CHECK
  WAREHOUSE = COMPUTE_WH
  SCHEDULE  = 'USING CRON 0 7 * * * UTC'
AS
  SELECT
    'PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK' AS object_name,
    (SELECT COUNT(*) FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK LIMIT 1) AS accessible;
  -- repeat for each critical object
```

Alert on failure via Snowflake email notification or a dedicated monitoring ticket.

**Pros:** Catches gaps proactively, days before a deploy hits them. Runs independently of
the deploy workflow. Could feed into existing [[flight-check]] process.

**Cons:** Task must be maintained as new shared objects are added. Snowflake email
notifications require configuration. Does not prevent gaps — only detects them faster.
A table that drops out on Monday is caught by Tuesday's check, not immediately.

---

### Option D — Eclipse post-load hook to re-grant share

If Eclipse's `CREATE OR REPLACE TABLE` is the root cause of grant drops, add a post-load
SQL step in the Eclipse task configuration that re-issues share grants after each load:

```sql
-- Post-load step in Eclipse connector task
GRANT SELECT ON TABLE PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK TO SHARE <share_name>;
```

**Pros:** Fixes the root cause directly — grant is restored immediately after each
overwrite. No ACCOUNTADMIN required if SYSADMIN has GRANT privilege on the share.

**Cons:** Requires editing Eclipse task configurations for every ingestion task that
touches a shared table. Eclipse connector task structure may not support post-load SQL
steps easily (research needed). Brittle — if a new table is added without this step,
the gap problem recurs.

**Research needed:** Confirm whether Eclipse connector supports post-load SQL hooks.
Confirm whether `CREATE OR REPLACE TABLE` actually drops the grant (test in sandbox).

---

## Recommended Approach

Start with **Option A** (future grants). It is the only option that prevents gaps rather
than detecting them. If Snowflake edition or ACCOUNTADMIN access is a blocker, fall back
to **Option B** (share audit script) as a lower-cost detection layer that can be shipped
quickly. Option C (monitoring task) is a good complement to either — catches gaps that
open between deploys.

## Next Steps

- [ ] Verify Snowflake edition for PROD account (Business Critical required for future share grants)
- [ ] List all tables in AMAZON, AMAZON_ADS, SELLERCLOUD_SQL, SUPPLEMENT on PROD — confirm
      all are safe to expose via schema-level grant
- [ ] Test Option A in sandbox: create a test share, issue future grant, do `CREATE OR REPLACE TABLE`, confirm grant survives
- [ ] File as a Jira ticket once approach is chosen

## See Also

- [[GP-207]] — original prod-to-test data share setup; lessons learned section noted this risk
- [[data-share-pattern]] — Snowflake data sharing conventions
- [[snowflake-data-share-refresh]] — `CREATE OR REPLACE TABLE` semantics across a share
- [[flight-check]] — existing operational validation; Option C would feed into this
- [[GEP]] — client entity
