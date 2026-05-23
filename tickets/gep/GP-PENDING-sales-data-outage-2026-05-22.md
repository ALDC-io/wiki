---
tags: [ticket, gep, incident, snowflake, outage, resolved, task-chain]
aliases: [GEP Sales Data Outage, Navira Missing Sales Data, PROD_DG1_ALDC_LIBRARY Access Failure]
created: 2026-05-22
updated: 2026-05-22
---

# GP-PENDING: GEP/Navira Missing Sales Data — Task Chain Suspended (2026-05-22)

Post-mortem for a ~14-hour Snowflake task chain suspension that left GEP/Navira sales and inventory data stale by ~10 hours. Root cause: the Snowflake task service role lacked (or lost) explicit `USAGE` on `PROD_DG1_ALDC_LIBRARY`, causing step 7 (`SALES_FCT_ORDERLINE`) to fail at view expansion time. Snowflake auto-suspended the root task after the error, halting all downstream warehouse refreshes.

---

## Timeline

| Timestamp (PT unless noted) | Event |
|---|---|
| 2026-05-21 09:18 | GP-199 ASIN views deployed to prod (`EXTRACT_AMAZON_ADS_SB_AD_ASIN_MAP`, `EXTRACT_AMAZON_ADS_SB_AD_DAILY_SPEND`, `MARKETING_FCT_ACTIVITY`) |
| 2026-05-21 ~19:50 | `TASK_WAREHOUSE_ORDERLINE_0` runs on its hourly schedule. Steps 0–6 complete. Step 7 (`SALES_FCT_ORDERLINE`) **FAILS** |
| 2026-05-21 19:52:24 | Snowflake auto-suspends `TASK_WAREHOUSE_ORDERLINE_0` — reason: `SUSPENDED_DUE_TO_ERRORS` |
| 2026-05-21 23:11–23:47 UTC | Amazon S&T CHILD ASIN template hits `QuotaExceeded` errors (transient, auto-recovered — unrelated to outage) |
| 2026-05-22 ~morning | Navira reports missing sales data |
| 2026-05-22 09:00 UTC | PBI Prod model scheduled refresh fails with `Section1/Vendor/Renamed Columns` error (transient — hourly refreshes 10:00–16:00 UTC all succeeded) |
| 2026-05-22 09:05 | Task chain resumed: `ALTER TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0 RESUME` + `EXECUTE TASK` |
| 2026-05-22 09:06–09:08 | Steps 0–6 complete successfully |
| 2026-05-22 09:08 | Step 7 fails **again** with same `PROD_DG1_ALDC_LIBRARY` error |
| 2026-05-22 09:12 | Grant fix applied (see Resolution below) |
| 2026-05-22 09:12 | Verified: `SALES_FCT_ORDERLINE` view resolves correctly under task role |
| 2026-05-22 09:12–09:14 | Steps 7–10 run manually as `ACCOUNTADMIN` — all succeed |
| 2026-05-22 16:15 UTC | PBI Prod model refresh triggered via API |
| 2026-05-22 16:18 UTC | Refresh completes successfully |

**Total outage duration: ~14 hours** (2026-05-21 19:52 PT to 2026-05-22 09:14 PT)

---

## Error Message

```
SQL compilation error: Failure during expansion of view 'SALES_FCT_ORDERLINE':
Failure during expansion of view 'SHARED_FCT_EXCHANGE_RATE':
Database 'PROD_DG1_ALDC_LIBRARY' does not exist or not authorized.
```

Observed at step 7 of `TASK_WAREHOUSE_ORDERLINE_0` running as `PROD_DG1_ROLE_CORE_SVC_DA8904DB`.

---

## Root Cause

The Snowflake task service role `PROD_DG1_ROLE_CORE_SVC_DA8904DB` lost (or never had explicit) `USAGE` on the `PROD_DG1_ALDC_LIBRARY` database.

The dependency chain is:
1. `WAREHOUSE.SALES_FCT_ORDERLINE` (step 7 of task chain) references
2. `WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` (secure view in `PROD_DG1_GEP`) which references
3. `PROD_DG1_ALDC_LIBRARY.WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` — **cross-database reference**

When the task chain reached step 7, Snowflake tried to expand both views at query-parse time. The task role could not resolve `PROD_DG1_ALDC_LIBRARY`, causing the `does not exist or not authorized` error.

Snowflake then auto-suspended the **root task** (`TASK_WAREHOUSE_ORDERLINE_0`) per its `SUSPEND_TASK_AFTER_NUM_FAILURES` policy. No further hourly runs occurred.

**Likely trigger:** Grant history showed no prior explicit grant of `PROD_DG1_ALDC_LIBRARY` to the task role. The role was probably relying on implicit or inherited access that was disrupted — most likely by the GP-199 view deployment session on 2026-05-21 09:18 (which ran as a higher-privileged role and may have altered role hierarchy or session context) or an undetected role hierarchy change.

---

## Impact

| Dimension | Detail |
|---|---|
| Duration | ~14 hours |
| Affected client | GEP / Navira |
| Stale tables | `SALES_FCT_ORDERLINE`, `INVENTORY_FCT_BALANCE`, `SHARED_DIM_PRODUCT`, `TRAFFIC_FCT_ACTIVITY` |
| PBI Prod model | Serving data through May 21 morning run — missing ~10 hours of order processing |
| Data gap (orders) | 1,387 orders not visible until fix applied |
| Data gap (order lines) | 5,114 order lines not visible until fix applied |
| PBI 09:00 UTC refresh | Transient `Section1/Vendor/Renamed Columns` failure — self-recovered by 10:00 UTC |

---

## Resolution

### Steps taken (2026-05-22 09:05–09:14 PT)

1. Resumed root task:
   ```sql
   ALTER TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0 RESUME;
   EXECUTE TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0;
   ```

2. Observed step 7 fail again with same error. Ran steps 7–10 manually as `ACCOUNTADMIN` — all succeeded.

3. Applied grant fix as `ACCOUNTADMIN`:
   ```sql
   GRANT USAGE ON DATABASE PROD_DG1_ALDC_LIBRARY
     TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;

   GRANT USAGE ON SCHEMA PROD_DG1_ALDC_LIBRARY.WAREHOUSE
     TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;

   GRANT SELECT ON ALL VIEWS IN SCHEMA PROD_DG1_ALDC_LIBRARY.WAREHOUSE
     TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB;
   ```

4. Verified `SALES_FCT_ORDERLINE` resolves correctly under the task role.

5. Triggered PBI Prod model refresh via API at 16:15 UTC → confirmed at 16:18 UTC.

### Evidence of fix

| Metric | Before fix | After fix | Delta |
|---|---|---|---|
| PBI latest data | May 21 | May 22 | +1 day |
| Orders | 2,645,180 | 2,646,567 | +1,387 |
| Order Lines | 3,175,580 | 3,180,694 | +5,114 |
| Task state | suspended | started | — |
| Next run | — | 09:50 PT hourly | — |

---

## Prevention

1. **Add monitoring for Snowflake task suspension events.** Alert when any task enters `SUSPENDED_DUE_TO_ERRORS` state. Add to ALDC observability platform (see [[observability-architecture]]). This would have cut detection time from ~10 hours to minutes.

2. **Audit all cross-database view references and ensure task roles have explicit grants.** Implicit or inherited access is fragile — any role hierarchy change or session-context shift can silently revoke it. Target: all `PROD_DG1_ROLE_*` task roles against all cross-database views they transitively depend on.

3. **Consider `GRANT FUTURE PRIVILEGES ON VIEWS IN SCHEMA PROD_DG1_ALDC_LIBRARY.WAREHOUSE TO ROLE PROD_DG1_ROLE_CORE_SVC_DA8904DB`** to prevent future access loss when new views are added to the library schema.

4. **After every prod deployment session** (especially those running as `ACCOUNTADMIN`/`SYSADMIN`), verify task chain next-run status has not been interrupted. A 5-minute post-deploy checklist step would catch this class of failure.

---

## Open Questions

- What specifically disrupted the grant between a working state and the 19:50 failure? Grant history inspection was inconclusive. Was it the GP-199 deployment session? A Snowflake role cache flush? A role hierarchy change? — **Not yet determined.**
- Is `PROD_DG1_ALDC_LIBRARY` used by any other task roles that may also be missing the explicit grant? — **Needs audit.**

---

## See Also

- [[GP-199]] — ASIN Brand Campaign Attribution; deployed same day as outage trigger
- [[GP-PENDING-data-share-stability]] — Recurring data share grant issues; closely related class of problem
- [[GP-PENDING-infra-connector-failures]] — Broader infra failures discovered 2026-05-22 during the same investigation window
- [[snowflake-data-share-refresh]] — Data share refresh patterns and known grant/access issues
- [[observability-architecture]] — ALDC observability platform; task suspension monitoring should be added here
- [[flight-check]] — Operational validation process; should include task-state check as a step
