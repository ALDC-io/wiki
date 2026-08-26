---
tags: [concept, architecture, snowflake, cost, infrastructure, optimization]
aliases: [Snowflake Cost Analysis, Snowflake Cost Optimization, Snowflake Credit Analysis]
sources: [conversation 2026-07-16, code review of clients + aldc-launchpad + core_api + aldc-scripts, ALDC-651, live ACCOUNT_USAGE baseline both accounts 2026-07-28, after-side pulse both accounts 2026-07-29]
created: 2026-07-16
updated: 2026-07-29
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

## Confirmed 2026-07-29 — the after-side measurement

**The fix worked.** Measured the day after, not inferred from the arithmetic.

### The discriminating read: a complete window inside a partial day

The trap on the morning after a change is that the day isn't over, so credits/day can't be compared. The way through: **the overnight 00:00–06:00 window is a complete elapsed period even on a partial day**, so it compares like for like a full 24 h before anything else can.

| Account | Before (13 straight nights) | 29 Jul | Change |
|---|--:|--:|--:|
| Non-prod `OG35375` | 6.05 – 6.09 | **0.70** | **−88%** |
| Prod `WJ66376` | 6.31 – 6.75 | **4.88** | **−25%** |

Corroborated hour-for-hour against the same weekday before the change (Wed 22 Jul), overlapping hours 00–14: non-prod **15.15 → 1.60 (−89%)**, prod **16.67 → 13.53 (−19%)**. Suspends/day went from **0 on 11 of 13 days** to 38 by mid-morning on non-prod; prod from 23–32/day to 104.

**The single most legible artefact — the 1.000 signature.** On 22 Jul non-prod billed **~1.000 credits in every single hour of the day**, all 24 of them. That flat line at exactly one credit/hour *is* an X-Small awake 24/7, and it is worth recognising on sight in any hour-of-day breakdown. Post-fix, most hours read 0.000, and `WAREHOUSE_EVENTS_HISTORY` shows `RESUME 13:00:33` → `SUSPEND 13:01:33` — exactly 60 s apart, i.e. `AUTO_SUSPEND=60` behaving precisely as specified.

### Verify the metering watermark before believing a low number

**A window that hasn't been published yet produces a low number indistinguishable from a win.** Before reading anything into the 0.70, check the publication high-water mark:

```sql
SELECT MAX(end_time) FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY;
```

`end_time` is the *end* of the metering hour bucket, so a healthy value reads slightly ahead of wall-clock. If it sits before 06:00 local, the overnight figure is incomplete and means nothing yet.

### Revised total — the headline came down ~8%

| | Predicted 2026-07-28 | Measured 2026-07-29 |
|---|--:|--:|
| Non-prod credits/day | 24.1 → ~2.8 | **~2.5** (better) |
| Prod credits/day | 23.8 → ~18.7 | **~19.5** (slightly worse) |
| Combined | ~$1,851/mo · $22.2K/yr · 55% | **~$1,690/mo · ~$20.3K/yr · ~54%** |

**Per-item attribution is not recoverable, and this is the methodological lesson.** `AUTO_SUSPEND` on both accounts *and* stopping the Cube poller all landed on 2026-07-28, and prod — originally designated the A/B control — was changed the same day. So the *total* is measured but the split is not: non-prod fell ~21.7 credits/day against 14.13 predicted for `AUTO_SUSPEND` alone, the excess belonging to the poller stop. **If you designate a control, do not change it the same day; the attribution is worth more than the extra day of saving.**

## Alert design lessons (2026-07-29)

Seven lessons from building the ALDC-656 guardrail. All of them are about an alert that is *technically correct* while being operationally useless or misleading.

1. **Silence must be unambiguous.** An alert that only speaks on breach is indistinguishable from one that is broken, suspended, or emailing nobody. Fix: a **weekly heartbeat** on a fixed day, with the rule stated inside the message — *no email for 8+ days means the monitoring is broken, not that all is well.*
2. **Never let the alert compare across your own change.** A prior-7-day median still contains pre-change days, so a deliberate improvement fires a −90% step change *every morning for a week*. Six consecutive alarms for a success is how people learn to ignore alerting. Fix: a **`CHANGE_LOG` table**; baseline becomes `max(latest change + 1, eval_day − 7) .. eval_day − 1`, and the check is **skipped below 2 baseline days** — one day is an anecdote — saying so explicitly rather than omitting a signal silently.
3. **Put the reported date in the subject.** A backfilled or forced send about a historical day is otherwise indistinguishable from a live alarm. This actually happened: a test send reporting pre-fix 2026-07-27 (24.12 credits, 0 suspends) was read as *"the changes didn't apply, we're still wasting credits"*. Label manual sends `[TEST]` too. **A false alarm is a defect in the alert, not in the reader.**
4. **One source of truth for recipients.** A list duplicated between `ALLOWED_RECIPIENTS` and a literal in the procedure will drift and start emailing nobody. Keep it in a table the procedure reads at run time, change it through one validated command, and **fail loudly** — report unverified addresses rather than silently dropping them, and refuse to leave the list empty.
5. **Never address alerts to individuals.** The prod monitor was notifying **three people who had left the company**, so prod cost alerts reached nobody while looking correctly configured. Departures silently break individual-addressed alerting; a distribution list does not. Review `NOTIFY_USERS` whenever someone leaves.
6. **Test the scheduled path separately from the logic path.** Calling a procedure from an admin session proves nothing about a serverless task running `EXECUTE AS OWNER` with the managed-task privilege. Trigger the task and read `TASK_HISTORY`. Note its first row is the *next scheduled* run, not yours.
7. **⭐ An arriving alert proves only the account that sent it — put the account in the subject and check it.** "I'm getting the cost alert emails, so alerting is fine" is not evidence when two accounts are monitored separately. Verified 2026-07-29: **all 12 cost-alert emails received since 27 Jul carry `OG35375` (non-prod); zero carry `WJ66376` (prod).** Prod's guardrail was never deployed, so prod's silence and prod-being-quiet are indistinguishable — the exact failure mode lesson 1 exists to prevent, reappearing one level up because *another* account's alerts were filling the gap. Generalises beyond Snowflake: with per-account (or per-tenant, per-region) alerting, **a healthy signal from one scope is affirmative evidence about that scope only.** The account locator in the subject line is the discriminating field; without it the inbox cannot answer the question at all.

### Snowflake email verification is per-account

Extends the `090270` gotcha above: **the same address can be verified in one account and unverified in another.** `paul.russell@aldc.io` is verified on non-prod and unverified on prod, which is exactly why non-prod alerting works and prod's does not. Two distinct error codes surface it:

| Statement | Error | Meaning |
|---|---|---|
| `ALTER RESOURCE MONITOR … SET NOTIFY_USERS` | `090270` | user's email not verified |
| `ALTER NOTIFICATION INTEGRATION … SET ALLOWED_RECIPIENTS` | `394209` | address not a verified user in this account |

Verification is a Snowsight UI action per account (Profile → email → resend verification); there is no SQL for it. Probe additively — keep the existing recipients in the trial list — so a rejection leaves the monitor exactly as found.

**Confirmed from the inbox 2026-07-29 (still open):** every guardrail email received is `OG35375`, none are `WJ66376` — so non-prod alerting is live and prod alerting has no working path at all. Still outstanding: **three verifications** (Paul on prod; Vlad on non-prod *and* prod). Snowsight URLs — non-prod `app.snowflake.com/canada-central.azure/og35375`, prod `…/wj66376`. Until then the prod resource monitor's `NOTIFY_USERS` still lists three departed employees (see lesson 5), so prod cost alerts reach nobody.

**Also visible in that batch — the lesson-2 fix landing live.** Two sends seven minutes apart on 2026-07-29 show the baseline logic changing over: `22:02 UTC` reported `prior 7d median : 24.12 · step vs median : -36.7%` (a deliberate improvement firing as an alarm), while `22:09 UTC` reported `baseline median : 0 (0 day(s) since 2026-07-28) · step vs baseline : 0%` — the `CHANGE_LOG`-aware baseline correctly declining to compare across the change and saying so in-message rather than omitting the signal.

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

### Guardrail additions (2026-07-29)

| File | Purpose |
|---|---|
| `guardrails/cost_alert_task.sql` | The whole guardrail as idempotent DDL — notification integration, `ALDC_OPS.COST` schema, `ALERT_RECIPIENTS` + `CHANGE_LOG` tables, `SP_COST_GUARDRAIL(BOOLEAN)`, the serverless task. Statements separated by a `--;;` sentinel because a naive split on `;` breaks the `$$`-quoted procedure body. |
| `guardrails/apply_guardrails.py` | `--apply` / `--validate` / `--rollback` / `--set-recipients a@x,b@y`. Asserts the account locator before executing anything; rollback is 6 idempotent drops. |
| `guardrails/COST_CONVENTIONS.md` | 19 provisioning / monitoring / notification / measurement rules distilled from this incident. |

All on branch `feature/aldc-651-cost-reduction` in `ALDC-io/observability`.

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
  - ~~**Still open:** post-change metering confirmation (due 2026-07-29…)~~ → **confirmed 2026-07-29, see [[#Confirmed 2026-07-29 — the after-side measurement]]**. Remaining: Cube `refreshKey` interval (~$355/mo, needs owner sign-off, **do not impact that instance**); FUSION_92 dynamic-table lag (consumer-gated); warehouse isolation for the chatty ingest.
- **2026-07-29 — after-side measurement confirms the change; guardrail live on non-prod.**
  - **Metering confirmed** — non-prod overnight 6.05→0.70 (−88%), prod 6.31–6.75→4.88 (−25%), suspends 0→38 and 23–32→104. Revised total **~$1,690/mo (~$20.3K/yr, ~54%)**, about 8% under the 2026-07-28 headline. Full-day (rather than overnight-window) confirmation due 2026-07-30. Does **not** change the contract recommendation — still do not sign $40K.
  - **T4 (ALDC-656) guardrail LIVE on non-prod**: serverless task `ALDC_OPS.COST.T_COST_GUARDRAIL` + `SP_COST_GUARDRAIL(BOOLEAN)` + `ALDC_COST_ALERT_EMAIL` integration, daily 14:00 UTC. Covers all five ALDC-752 §1 same-day signals — zero-suspends, step change, overnight burn, idle %, new principal — plus a Monday heartbeat and a self-check on its own failed runs. Proven firing **autonomously** (07:00 local, `SUCCEEDED`), with email receipt confirmed in the inbox rather than trusted from a `SENT` return code.
  - **Deliberate deviation from the ALDC-656 scope:** the ticket specifies the pulse on the Ofelia cron; built Snowflake-native instead, for the availability reason in [[#6. Constraint on where cost monitoring can run (2026-07-28)]].
  - **Key-pair service account deprioritised** — it existed to let an *external* scheduled job run unattended; going Snowflake-native removed that need. Still wanted for `QUERY_TAG` attribution, no longer on the critical path.
  - **PROD guardrail + monitor blocked** on email verification: `PAULRUSSELLADMIN`, `PAULRUSSELL` and `VLADRYZHKOV` all unverified on prod, and Vlad also unverified on non-prod → three verifications needed. Decision: alerts go to **Paul + Vlad**, not Paul alone.
  - **Access-review item (not cost):** `BRAYDENMARSHALLADMIN`, `SEANOGRADY`, `STEVENDEUTEKOM`, `BRAYDENMARSHALL`, `STEVENDEUTEKOMADMIN` all still **enabled** on prod despite having left.
  - **Security item (not cost):** a *prod* Snowflake admin credential (`snowflake-prod-admin`) is stored in the *QA* Key Vault `aldc-vault-qa`, crossing an environment boundary.
  - **Azure held deletions triaged** (ALDC-745): all four sit in `Quality 1 / rg-aldc-launchpad` as one stopped QA Superset/Cube stack. Front Door `aldc-portal-afd` is the only clearly safe deletion and carries nearly all the money (~$35/mo base, no custom domains, route points at a stopped ACI). ACR `aldcqaazcr1c01` is **not** safe alone — both ACIs pull from it and the 2026-05-14 images may be the only copy. **Both Key Vaults should be kept**: Standard Key Vault has no monthly base charge, so deleting saves ≈$0 while risking the Lectric SP-API set and 15 `gep-prefect` secrets.
  - **`pg-aldc-superset-qa` auto-restarts ~2026-08-04** (Azure restarts stopped flexible servers after 7 days), which silently reverses ~$19/mo *and* re-exposes a `0.0.0.0`–`255.255.255.255` firewall rule with public access enabled. Any "stop it to save money" action needs a deletion follow-up or a recurring check.
  - **ALDC-744's description is stale** — it still says prod was "deliberately left unchanged so it acts as a clean A/B control". Prod was changed 2026-07-28; this page is correct and the ticket is not.

## ⭐ Measurement corrections (ALDC-1026, 2026-08-26) — read before quoting any figure above

A Navira-share consumption sweep re-measured the instruments this page rests on and found four
defects. **Figures on this page that predate 2026-08-26 inherit them.**

1. **The credit price was never measured.** `ORGANIZATION_USAGE.RATE_SHEET_DAILY` on both accounts
   gives **$2.25/credit and $25.00/TB-month**. **`$2.15` appears nowhere on either account** — it is
   the hardcoded `--price` default in `observability/jobs/snowflake-cost/cost_baseline.py:163`.
   Every dollar figure derived from that default is **~4.7% low**.
2. **`WAREHOUSE_METERING_HISTORY` is not the whole bill.** It carries **93.1% non-prod / 96.9% prod**
   of account credits (365d) — and it returns *exactly two warehouse names per account* while
   **five distinct service-pool warehouses execute queries and appear in none of them**. On non-prod
   those pools burn **130,781 query-seconds against `COMPUTE_WH`'s 99,725 — 131%**. `TRUST_CENTER`
   alone is **513.6 credits/yr ≈ $1,155** across both accounts. **Use `METERING_DAILY_HISTORY` as the
   denominator.**
3. **`TABLE_STORAGE_METRICS` undercounts storage ~4.8×** because it excludes the 7-day fail-safe tail
   of *dropped* tables — and on a `CREATE OR REPLACE` estate that tail *is* the storage story.
   GEP measured **141.80 GB** on that basis and **685.79 GB** at billing grain
   (`DATABASE_STORAGE_USAGE_HISTORY`). ⚠ **The wrong basis was used twice, by two different people,
   after the defect had already been flagged in the same analysis.** Flagging a defect does not
   remove it from circulation.
4. **`ACCESS_HISTORY` is NOT-RECORDED on Standard edition** — SELECTable, fully defined (14 columns),
   **0 rows on both accounts across 13 months**. Any estate analysis that read "never accessed" from
   it produced a **false zero** and must be re-opened.

### The thesis holds, and harder than stated

`COMPUTE_WH` measured: **non-prod 3,353.55 credits / 6,942 billed hours / 152.71 execution hours =
2.20% busy over 365 days.** Prod, 30 days: **562.73 credits / 720 billed hours** — that is
**24 hours a day; the prod warehouse never suspends** — at 23.34% busy.
⇒ **~98% of a year's non-prod compute spend bought idle time.** A per-job cost on a shared warehouse
is arithmetic on an assumption: killing a job that runs concurrently with others saves nothing.
`QUERY_ATTRIBUTION_HISTORY` **is live on both accounts** and gives per-query credits — but it
accounts for only **59.5% prod / 11.8% non-prod** of metered compute, so per-object cost is a
**floor**, and grossing it up is INFERRED with the model stated.

### Storage: where GEP's money actually is

**685.79 GB ≈ $17.15/month** across both accounts, **70% of it `PROD_DG1_GEP` fail-safe (478.19 GB)**,
concentrated **99.4% in three schemas** — `SELLERCLOUD_SQL` 17.21 GB, `AMAZON` 12.68 GB,
`AMAZON_ADS` 8.61 GB on 0.487 GB active (**17.7×**). GEP is **47.2% of prod account storage**.
Every orphan and rollback/shadow table combined is **2.4 GB (0.35%)** — the orphan sweep is not
where the money is. **This is the live T3 lead.**

## See Also

- [[Snowflake]] — platform reference (env naming, tasks, dynamic tables, reader accounts)
- [[prefect-cost-analysis]] — sibling Azure/Prefect cost model
- [[star-schema-convention]] — warehouse table conventions
- [[snowflake-environment-provisioning]] — account locators + provisioning
- [[observability-platform]] — host repo for the toolkit + recurring cost job (T4)
