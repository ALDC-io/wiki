---
tags: [concept, architecture, snowflake, cost, infrastructure, optimization]
aliases: [Snowflake Cost Analysis, Snowflake Cost Optimization, Snowflake Credit Analysis]
sources: [conversation 2026-07-16, code review of clients + aldc-launchpad + core_api + aldc-scripts, ALDC-651]
created: 2026-07-16
updated: 2026-07-16
---

# Snowflake Cost Analysis & Optimization

Cost model + optimization workstream for ALDC's [[Snowflake]] estate. Tracked as epic **ALDC-651** (assigned Vlad) with five lane tickets in sprint S7. Started 2026-07-16 as a code-review-driven scoping pass; the numeric baseline is **pending the first live `ACCOUNT_USAGE` run** (see Status).

The sibling analysis for the other big infra spend is [[prefect-cost-analysis]].

## Estate under analysis

Two primary accounts + one reader, all `AZURE_CANADACENTRAL`, Standard Edition (~$2.00–2.25 USD/credit). See [[GP-261]] / [[snowflake-environment-provisioning]] for account identity.

| Env | Locator | Org-qualified | Admin role | Notes |
|---|---|---|---|---|
| Non-prod (QA/Test/UAT, shared) | `OG35375` | `LSUBOGT.YX94045` | `TEST_DG1_CORE_ADMIN`; `PAULRUSSELLADMIN` | `TEST_DG1_*` databases |
| Prod | `WJ66376` | `LSUBOGT.MY89318` | `PROD_DG1_CORE_ADMIN` (ACCOUNTADMIN) | `PROD_DG1_*` databases |
| Reader | `AH87540` | — | `READER_ADMIN_BACA483F` | external data-share consumer, 2-credit/day monitor |

## Key findings (from code review — pre-metering)

1. **No cost visibility today.** `ACCOUNT_USAGE` is queried exactly once in the whole estate (`aldc-launchpad/warehouse_ops/_query_history.py`, for a failed-proc debug), never for cost. No queries against `WAREHOUSE_METERING_HISTORY` / `STORAGE_USAGE` / `METERING_DAILY_HISTORY` anywhere. The weekly Slack cost dashboard ([[aldc-scripts]] `cost-monitoring/corporate-costs-report.sh`) covers Azure/GitHub/Anthropic but **not Snowflake**.
2. **One shared `COMPUTE_WH` per account.** Every task and dynamic table in `clients/` + `aldc-launchpad/warehouse_ops/` runs on a single warehouse named `COMPUTE_WH`. No per-client/per-workload isolation → credit attribution needs query/task history, not the SQL. No `CREATE WAREHOUSE` sizing or multi-cluster config in code; warehouses are provisioned XS / `AUTO_SUSPEND=300` / `AUTO_RESUME=TRUE` at account setup (`core_api/v1/route_capacity.py:667`, `route_setup.py:205,370`).
3. **Zero incremental patterns.** Every fact is a full `CREATE OR REPLACE TABLE ... AS SELECT`. No `INSERT ... WHERE > MAX(...)` anywhere. Prime compute suspects:
   - **GEP** hourly 10-table orderline DAG — `clients/GEP/eclipse/scripts/task_warehouse_orderline.json` (root `TASK_WAREHOUSE_ORDERLINE_0`, cron `50 * * * *`, 24×/day) + hourly `task_warehouse_purchasing.json`.
   - **DISH_DUER** hourly fact chain — `clients/DISH_DUER/snowflake/warehouse/sales_dim_order.sql` DAG (root cron `0 * * * *`).
   - **ASPIRE_NORTH** — 5 dashboard cache procs, twice-hourly 06–18 (~130 proc runs/day).
   - **KIT_ACE** — 16+ dynamic tables at `TARGET_LAG='1 HOUR'`, two of them **also** re-materialized daily into `_CACHE` tables (`eclipse/scripts/task_warehouse_inventory.json`) — double cost.
   - **FUSION_92** mostly uses the cheaper `TARGET_LAG=DOWNSTREAM`; deprecated `*_meta_*` tables at `'1 hour'` may still be deployed (a file under `deprecated/` doesn't drop the object).
4. **Hidden storage cost.** Hourly `CREATE OR REPLACE` on large facts spins up ~24×/day of Time Travel + 7-day Fail-safe copies. Plus sprawl in `aldc-launchpad/warehouse_ops/` (42 rollback / 14 shadow / clone scripts): orphaned dev schemas `WAREHOUSE_TEST_GP226` / `WAREHOUSE_TEST_NAVIRA_ROADMAP` / `WAREHOUSE_TEST_GP226_TEAM`, per-run timestamped Lectric clones (`_lectric_refresh.py`), a whole-DB clone (`_deploy_lectric_clone.py`), and `_RB`/`_SHADOW`/`_BEFORE` copies from GP-199/200/225/226/259/277/281. **Gate:** `WAREHOUSE_TEST_GP226` / `_NAVIRA_ROADMAP` leaked into **live prod dependencies** (`clients/GEP/snowflake/warehouse/marketing_fct_activity_consolidated.sql`) — reclassify, do not blind-drop (the daily Data Model reads these; see [[GP-225]]).
5. **No resource monitors as code** beyond the 2-credit/day reader cap. No credit guardrail on either `COMPUTE_WH`.

## Access & method

Reuse the existing connection pattern — `snowflake-connector-python` (already a dep), password auth (+MFA option on prod), role `ACCOUNTADMIN` (required to read `SNOWFLAKE.ACCOUNT_USAGE`), following `warehouse_ops/_query_history.py` + `_navira_share_mount.py`. All Phase-0 queries are read-only — safe in prod. The alternative programmatic path is `core_api` `route_warehouse.warehouse_query()` (Cosmos-sourced creds, all accounts).

## Toolkit (T0 / ALDC-652)

Read-only cost toolkit at **`observability/jobs/snowflake-cost/`** (repo `ALDC-io/observability`; the originally-planned `aldc-scripts` no longer exists on GitHub):

| File | Purpose |
|---|---|
| `queries.py` | 19-query `ACCOUNT_USAGE` battery (single source of truth) |
| `cost_baseline.py` | Runner → per-query CSVs + ranked `SUMMARY.md` per account |
| `_conn.py` | Both-account connection helper |
| `README.md` | Run instructions; outputs git-ignored under `baseline/<env>/` |

Battery covers: credits by service type + month; warehouse credits + hour-of-day; query attribution + cost proxy; spill/contention; task runs; serverless-task / dynamic-table / auto-clustering / MV refresh; storage by DB; top-table overhead (time-travel + fail-safe + clone); sandbox/clone sprawl; warehouse events; login cadence; live `SHOW WAREHOUSES` / `RESOURCE MONITORS`. `--dump-sql` emits a UI-pasteable `queries.sql`. Built + **live-validated against non-prod (OG35375): 19/19 queries return data**; ruff + mypy clean. 2026-07-16.

## Phased plan (all executed; strict per-change evidence gate)

- **Phase 0 (T0):** baseline both accounts → ranked cost-hotspot report (gates the rest).
- **Phase 1 — quick wins:** TRANSIENT rebuild targets (kill Fail-safe on high-churn facts); AUTO_SUSPEND tuning (evidence-led); storage sweep of dead clones/rollbacks; resource monitors (NOTIFY-first).
- **Phase 2 — compute redesign:** GEP orderline → incremental (T1/ALDC-653); DISH_DUER / KIT_ACE / ASPIRE_NORTH / FUSION_92 (T2/ALDC-654); query tagging / warehouse isolation.
- **Phase 3 — guardrails:** recurring Snowflake cost report as an `observability` job (Ofelia schedule + alerting/Grafana; the old `aldc-scripts` weekly Slack dashboard repo is gone); key-pair read-only cost service account; cost conventions doc.

Lane tickets: **T0** ALDC-652 · **T1** ALDC-653 · **T2** ALDC-654 · **T3** ALDC-655 · **T4** ALDC-656 (all in S7; unassigned for self-select). Every mutation follows the evidence gate: prove the target the consumer actually reads → validate at the consumer layer → prove no regression → non-destructive first + rollback → gate the deploy.

## Status

- **2026-07-16:** Plan approved; epic + 5 lane tickets created (ALDC-651…656, S7). T0 toolkit **built, live-validated on non-prod (19/19 queries), and pushed to `ALDC-io/observability` `jobs/snowflake-cost/`** (PR #2, CI green, ready to merge). First non-prod canary (7-day): ~188 `WAREHOUSE_METERING` credits (`COMPUTE_WH` dominant), **0 resource monitors** (confirms no guardrail), and a leftover **`SANDBOX_DG1_GEP_GP197`** schema still running hourly orderline tasks (T2/T3 candidate). **Full baseline still pending: 90-day window on both accounts incl. prod (WJ66376)** — reconcile against Snowflake Admin → Cost Management. Sent to Vlad for ticket review.

## See Also

- [[Snowflake]] — platform reference (env naming, tasks, dynamic tables, reader accounts)
- [[prefect-cost-analysis]] — sibling Azure/Prefect cost model
- [[star-schema-convention]] — warehouse table conventions
- [[snowflake-environment-provisioning]] — account locators + provisioning
- [[observability-platform]] — host repo for the toolkit + recurring cost job (T4)
