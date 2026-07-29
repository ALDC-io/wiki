---
tags: [concept, architecture, snowflake, cost, infrastructure, optimization]
aliases: [Snowflake Cost Analysis, Snowflake Cost Optimization, Snowflake Credit Analysis]
sources: [conversation 2026-07-16, code review of clients + aldc-launchpad + core_api + aldc-scripts, ALDC-651, live ACCOUNT_USAGE baseline both accounts 2026-07-28]
created: 2026-07-16
updated: 2026-07-28
---

# Snowflake Cost Analysis & Optimization

Cost model + optimization workstream for ALDC's [[Snowflake]] estate. Tracked as epic **ALDC-651** (Paul) with lane tickets in sprint S7. Started 2026-07-16 as a code-review-driven scoping pass; **the numeric baseline landed 2026-07-28 and overturned the original hypotheses** — see [[#The measured answer 2026-07-28]].

The sibling analysis for the other big infra spend is [[prefect-cost-analysis]].

## The measured answer 2026-07-28

**The one-line lesson: this estate's Snowflake bill was ~60–93% idle warehouse time, not query cost, not data volume, and not the clients anyone suspected.**

### 1. The spike was entirely non-prod; prod never moved

| Month | Prod credits/day | Non-prod credits/day |
|---|--:|--:|
| Apr 2026 | 23.0 | **3.7** |
| May 2026 | 23.0 | **15.3** |
| Jun 2026 | 23.6 | **24.1** |
| Jul 2026 | 23.7 | **23.9** |

The +84% invoice growth that triggered the whole exercise was **non-prod growing 6.5×**. Prod was flat to within 3% across 90 days. Reconciles with the invoice trend to a constant ~67-credit monthly offset.

**Cause pinned to the day — a single QA Cube.dev container, not the dev work happening alongside it.** An early hypothesis blamed the TEST Eclipse reactivation and [[GP-225]]/[[GP-226]]-era development; that was wrong. Non-prod daily credits against the container's poll count:

| Date | Credits/day | Cube polls |
|---|--:|--:|
| May 1–13 | **3.95** avg | **0** |
| **May 14** | **14.41** | **209** (deployed 13:37) |
| May 15–31 | **23.06** avg | **480/day** |

A 6× step on the deployment date, no ramp, then flat at 480 polls/day for 75 days (36,039 polls total). The Navira dev work *was* happening in that account — it simply wasn't what moved the bill. **Lesson: when a cost curve steps rather than ramps, look for a deployment on that date, not for a gradually-growing workload.**

### 2. Root cause: `AUTO_SUSPEND` vs. statement chatter

`COMPUTE_WH` is **X-Small** with **`AUTO_SUSPEND=300`** on both accounts (provisioned that way by `core_api/v1/route_capacity.py`). X-Small bills 1 credit/hour, so credits/day = hours/day billed.

| | Billed credits/day | Query work h/day | Idle share | Suspends/day |
|---|--:|--:|--:|--:|
| Non-prod | 24.1 | 1.6 | **~93%** | **0 on 11 of 13 days** |
| Prod | 23.8 | 9.5 | **~60%** | 26 |

Prod issues **52,412 `USE` statements per 24h** — one every 1.6 seconds — from the Eclipse service account, plus FUSION_92's 20 dynamic tables refreshing ~562×/day. Idle gaps essentially never reach 300 seconds, so the warehouse bills around the clock while doing a fraction of that in work.

**The exact-saving formula (reusable):** with `AUTO_SUSPEND=N`, billed idle per inter-query gap is `min(gap, N)`. So the saving from lowering 300→60 is precisely `SUM(min(gap,300) − min(gap,60))` over observed gaps in `QUERY_HISTORY`. That converts `AUTO_SUSPEND` tuning from guesswork into arithmetic — **19.2 credits/day / ~$1,240/mo across both accounts here.**

### 3. The pollers-are-expensive trap

A **Cube.dev** instance polling a `refresh_key` cache probe every 180 s on non-prod cost **7.14 credits/day (~$460/mo)** while performing **13 minutes of actual query work per fortnight**. Cause: Snowflake bills a **60-second minimum per warehouse resume**, and the poll forces ~405 resumes/day. Measured by counterfactual — billed idle recomputed with those sessions removed (133.7 h → 33.7 h over 14 days).

Its harm reconciles two independent ways: total harm at `AUTO_SUSPEND=300` ≈ 20.1 credits/day (from the May step change); the `AUTO_SUSPEND=60` change recovered 14.13 and the counterfactual measured the residual at 7.14 → **sum 21.3, agreement within 6%**. So most of the non-prod `AUTO_SUSPEND` win was this container's damage being mitigated rather than a general efficiency gain — worth remembering before crediting a config change with a saving that actually belongs to removing a specific workload.

**Resolved 2026-07-28: container stopped** (polling confirmed ceased — zero polls in the 10 minutes after shutdown against a 180 s cadence). Non-prod returned toward its pre-container baseline of ~3.95 credits/day.

Generalises to: **attaching any poller to a shared warehouse silently converts it into a 24/7 charge**, and lowering `AUTO_SUSPEND` does not fix a poller whose interval is shorter than the work is worth. Identify pollers via `SESSIONS.client_environment` (not `client_application_id`, which reported only `JavaScript 2.4.0`).

### 4. What was *not* the cause

- **Inactive clients (DISH_DUER / KIT_ACE / ASPIRE_NORTH) — zero compute.** Zero task runs in 90 days; 64 KIT_ACE dynamic tables defined but **0 ACTIVE**; ASPIRE_NORTH has no database on either account. Their pipelines were already suspended. Residual footprint ~0.087 TB ≈ **$2/mo**.
- **Storage — ~2% of spend** (1.59 TB, ~$37/mo vs ~$3,090/mo compute). The `TRANSIENT`-facts lever is real but worth ~$9/mo (`PROD_DG1_GEP` carries 0.412 TB Fail-safe against 0.114 TB active).
- **The full-rebuild DAGs.** GEP's hourly 11-step orderline chain runs ~1.5 h/day against 23.8 credits/day billed — converting it to incremental is worth **~$8/mo** against the highest consumer-regression risk in the estate (PBI reads `WAREHOUSE.SALES_FCT_ORDERLINE`). Deferred.

### 5. Method lessons

**Suspend count per day is a better leading indicator than credits.** Non-prod sat at zero suspends for eleven consecutive days while billing 24 h/day, and nobody saw it — a monthly credit total takes a month to look wrong, a suspend count of zero is wrong the same day.

**When a cost curve steps rather than ramps, look for a deployment on that date** — not for a gradually-growing workload. The first (wrong) hypothesis blamed concurrent development work because it was happening in the same account at the same time; the step change pointed at a single deployment instead.

**`query_text ILIKE '%pattern%'` matches your own probe.** This produced two wrong conclusions during the investigation — a "last poll 0 seconds ago" reading and a bogus latency comparison — because the probe's own SQL contained the search string. Always add `AND session_id <> CURRENT_SESSION()`, or match the target query's actual shape.

**Identify client applications via `SESSIONS.client_environment`, not `client_application_id`.** The latter reported only the driver (`JavaScript 2.4.0`); the application name was inside the environment JSON.

**Resource-monitor notifications fail silently for unverified emails** (`090270` on `SET NOTIFY_USERS`). A guardrail can look correctly configured while emailing nobody — verify delivery, never assume it.

### 6. Constraint on where cost monitoring can run (2026-07-28)

The [[observability-platform]] Ofelia scheduler and `obs-jobs` container run in **local Docker on a workstation** — every README endpoint is `localhost`, and the Azure VM cutover (`aldcqalnxnobs1u01`, Quality 1, East US 2) is unstarted Week 3 work. **A cost monitor scheduled there only runs when that machine is on, and would have missed this entire incident during any week it was off.**

Consequence for design: put the highest-value alert **inside Snowflake** as a serverless task with `SYSTEM$SEND_EMAIL` — no external host, no credentials, no availability gap — and treat the richer report as a separate, host-dependent concern. Get the alarm working before the dashboard.

Note also that the obs stack already wires `SF_ACCT`/`SF_USER`/`SF_PWD`/`SF_ROLE`, i.e. **password** auth. Since `ACCOUNT_USAGE` needs elevated privileges, reusing that pattern would place an admin password in a `.env` — the same anti-pattern that made this incident's spend unattributable. Use a `TYPE = SERVICE` user (Snowflake forbids passwords on them) with key-pair auth instead.

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

## Toolkit additions (2026-07-28)

| File | Purpose |
|---|---|
| `cost_pulse.py` | Daily A/B companion to `cost_baseline.py` — credits/day, **overnight 00:00–06:00 credits**, suspend/resume counts, busy-vs-billed hours, and the idle-gap distribution that yields the exact `AUTO_SUSPEND` saving. Renders a before/after table pivoted on a `--marker` date, excluding partial and change-day rows. |
| `reports/render_pdf.py` | Markdown → styled PDF (python-markdown + headless Chrome) so report deliverables stay reproducible from source. |

Both on branch `feature/aldc-651-cost-reduction` in `ALDC-io/observability`.

## Status

- **2026-07-16:** Plan approved; epic + 5 lane tickets created (ALDC-651…656, S7). T0 toolkit built, live-validated on non-prod (19/19 queries), merged to `ALDC-io/observability` `jobs/snowflake-cost/` (PR #2, squash `3e0e666`). Non-prod 7-day canary flagged **0 resource monitors** and a leftover `SANDBOX_DG1_GEP_GP197` schema running an orderline DAG consumed by nothing — dropped the same day.
- **2026-07-28 — baseline captured on BOTH accounts and the diagnosis inverted.** See [[#The measured answer 2026-07-28]]. Prompted by JK's 2026-07-27 scope update (which hypothesised inactive clients were the cause) and a Snowflake **$40K/1-year capacity commitment with a July 31 deadline**.
  - **T0 (ALDC-652) DONE** — 90-day baseline both accounts + live `SHOW TASKS`/`SHOW DYNAMIC TABLES` inventory.
  - **Applied non-prod:** `AUTO_SUSPEND` 300→60 (**measured 14.13 credits/day ≈ $911/mo**) + first-ever resource monitor `ALDC_NONPROD_MONTHLY` (NOTIFY-only, 400/mo, `suspend_at=None`). Warehouse confirmed cycling off within minutes.
  - **Applied prod:** `AUTO_SUSPEND` 300→60 (**measured 5.06 credits/day ≈ $326/mo**) + `ALDC_PROD_MONTHLY` (NOTIFY-only, 800/mo). Prod does **not** visibly cycle on a short sample — expected, since its sub-60s connector chatter keeps it awake through the working day; its saving comes from ~230 scattered longer gaps/day.
  - **Stopped the orphaned QA stack** from the deprioritised portal initiative: Cube container instance (**7.14 credits/day ≈ $460/mo** Snowflake + ~$43/mo Azure), Superset container instance (~$86/mo), Superset Postgres flexible server (~$19/mo). All **stopped, not deleted** — reversible in seconds, data intact; deletion held pending dependency checks on two Key Vaults, the container registry (holds the image) and a Front Door endpoint.
  - **TOTAL RECOVERED: ~$1,851/month ≈ $22.2K/year** — Snowflake run rate 47.9 → ~21.5 credits/day, **$37.1K → ~$16.6K/yr (55% cut)**. Non-prod 24.1 → ~2.8 credits/day (effectively solved); prod 23.8 → ~18.7 (all remaining headroom is here).
  - **Gotcha:** `ALTER RESOURCE MONITOR … SET NOTIFY_USERS` fails for any user whose Snowflake email is unverified (`090270`). On prod only `BRAYDENMARSHALLADMIN`, `SEANOGRADY`, `STEVENDEUTEKOM` were accepted — service accounts and several admins (incl. Paul's and Vlad's prod users) are unverified, so **verify the email first or the guardrail is console-only.**
  - **Ticket restructure:** new **T6 (ALDC-744)** warehouse-idle lane = the real #1; new **T5 (ALDC-745)** inactive-client archive rescoped to storage/compliance (~$2/mo); **T2 (ALDC-654) closed as superseded**; T1 (ALDC-653) deferred (~$8/mo, worst value/risk); T3 (ALDC-655) rescoped down; T4 (ALDC-656) promoted.
  - **Contract recommendation: do not sign $40K.** It matches the pre-optimisation run rate ($37.1K/yr) almost exactly, on a baseline that is majority idle. Path to **$9–15K/yr**; re-size after 30 days of measured consumption. Ask Snowflake for the credit rate, term, overage rate and rollover-vs-forfeiture terms before considering any commit.
  - **Still open:** post-change metering confirmation (due 2026-07-29 — if credits/day do not fall, revert to 300 and record the estimate as wrong); Cube `refreshKey` interval (~$355/mo, needs owner sign-off, **do not impact that instance**); FUSION_92 dynamic-table lag (consumer-gated); warehouse isolation for the chatty ingest; `cost_pulse.py` onto the Ofelia daily schedule.

## See Also

- [[Snowflake]] — platform reference (env naming, tasks, dynamic tables, reader accounts)
- [[prefect-cost-analysis]] — sibling Azure/Prefect cost model
- [[star-schema-convention]] — warehouse table conventions
- [[snowflake-environment-provisioning]] — account locators + provisioning
- [[observability-platform]] — host repo for the toolkit + recurring cost job (T4)
