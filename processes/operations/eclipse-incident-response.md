---
tags: [process, operations, eclipse, incident, outage, on-prem, runbook]
aliases: [Eclipse Incident Response, Outage Recovery, Connector Outage Runbook]
sources: [ALDC-244 (Kamloops power outage 2026-06-01), observability/ops/incident_triage.py, conversation 2026-06-01]
created: 2026-06-01
updated: 2026-06-11
automated_by: [[triage-agent]]
---

# Eclipse Incident Response (Outage Recovery)

Runbook for recovering [[Eclipse]] connector extractions after an infrastructure outage
(power loss, network blip, agent/container restart, source-system downtime). Companion to
[[flight-check]] (proactive validation) and [[debugging-warehouse-loads]] (single-template
failures). Proven end-to-end on the **2026-06-01 Kamloops power outage** (ALDC-244).

The on-prem connector hosts (Kamloops, Coquitlam) run the Docker agents (`dios` =
`gep-sellercloudvpn`, `dcgeneral-coquitlam`, etc.) and an on-prem SQL Server source. A power
or network event there fails any template mid-run and stalls anything scheduled during the gap.
See [[local-network]] and [[agent-builds]] for the host topology.

## Principle: monitor and triage read-only first

Do **not** start re-triggering blindly. First establish: is the infra back, what actually
failed because of the outage (vs. pre-existing noise), and did the core pipeline self-recover.
All triage here is **read-only** — no writes, no alerts.

## Step 1 — Confirm services are back

- Watch the **#observability-dev** Slack channel ([[observability-platform]] / Uptime Kuma).
  The `[dios]` monitor flipping to **Up** marks power/network return.
- Auto-resolved alerts (e.g. *"… is now updating again"*) confirm the scheduler is processing.

## Step 2 — Triage what failed (read-only)

Run the incident-triage tool (lives in the observability repo `ops/`; read-only Cosmos query,
same shapes as `jobs/check_eclipse_templates.py` with all side effects stripped):

```bash
cd ~/repos/observability
python ops/incident_triage.py --window-start "<outage UTC>" --window-end "<recovery UTC>" --links
```

It reports **(A)** templates that ran during the window and didn't complete (casualties),
**(B)** templates whose current latest run is failed/zombie, and (`--links`) Eclipse
re-trigger URLs. See `observability/ops/README.md` for the tool reference.

**Classify the output — not everything is yours to fix:**

| Pattern | Action |
|---|---|
| `init` runs right after recovery | In-flight — the scheduler auto-kicked queued runs. Let them finish; don't re-trigger. |
| SQL `[HYT00] Login timeout` | Outage casualty — source was unreachable. Re-trigger after confirming source back (Step 3). |
| `zombie` | Run died mid-execution (power kill). Re-trigger; data is safe (see gotcha below). |
| Amazon `QuotaExceeded` | **Noise** — API quota, auto-recovers ~midnight UTC. Not outage-related. |
| Known IP-block / app-bug failures (e.g. Viant Snowflake whitelist, Firebase double-init) | **Noise** — pre-existing, out of scope. |

## Step 3 — Canary before mass re-trigger

For SQL-source templates, **re-trigger ONE as a canary** (a low-risk, fast one like Calendar):

- ✅ Completes → the on-prem SQL Server is genuinely back → re-trigger the rest from the
  `--links` URLs.
- ❌ Fails again with `[HYT00] Login timeout` → the **source host itself didn't come back**
  with the power → escalate to infra (Portainer / SQL Server host on the affected box).
  Do **not** keep blind-retrying.

## Step 4 — Verify the downstream warehouse consumes it

Re-extraction only fixes the landing layer. Confirm the Snowflake chain rebuilds:

```bash
cd ~/repos/aldc-launchpad
python scripts/gep_warehouse_health.py --tasks --freshness   # read-only
# --resume available to force the root task, but NOT needed if the :50 hourly cron is healthy
```

Root task `TASK_WAREHOUSE_ORDERLINE_0` runs on a `:50` hourly cron; the next run sweeps up any
late-landing reference data. Confirm `state=started` (not `suspended`) and consumer tables
(`SALES_FCT_ORDERLINE`, `SHARED_DIM_PRODUCT`, …) show a fresh `LAST_ALTERED`.

## Gotcha: zombied single-`full`-partition templates

When a `partition_scheme.method: full` template (e.g. SellerCloud **Product Properties Amazon**)
is power-killed mid-run, the schedule goes `zombie` and its single partition (`work_partition`)
is left with un-acked `queue_messages` and `in_queue: true`.

- **It does not auto-recover on schedule** — re-trigger manually.
- **Re-triggers may take several minutes to land** — the agent has to drain the stale queue
  messages first. This is latency, **not** a wedge. Confirm the agent is healthy before assuming
  it's stuck: query `schedule` for that `agent_id` over the last 90 min — a healthy agent shows
  many `complete` runs. If so, just wait; no DB surgery needed.
- **Data is never corrupted by the zombie.** These loads write a new *versioned* table
  (`MAIN_…_N` → `_N+1`) and repoint the `CURRENT_MAIN_…` view atomically; a killed run wrote
  nothing and the live table retains the last-good snapshot. See [[accumulating-source-tables]].
- `in_queue: true` alone is **not** a blocker — partitioned templates (one partition/day) carry
  many `in_queue: true` partitions while running normally. Don't treat it as the smoking gun.

> If a re-run genuinely never lands and the agent is healthy, the last resort is a targeted
> `work_partition` reset (`in_queue: false`, `queue_messages: []`) — a **prod Cosmos write**.
> Capture the original doc as rollback and get a second pair of eyes (connector owner) before
> mutating; in the 2026-06-01 incident this was prepared but **not needed** (queue drained on
> its own).

## What needs a human vs. what self-heals

- **Self-heals:** anything `init` post-recovery; the Snowflake task chain (hourly cron);
  Amazon quota failures.
- **Needs manual re-trigger:** templates that `failed`/`zombie`d during the outage and whose
  schedule has already passed (especially low-cadence reference data: Calendar, Currency,
  Product Properties).
- **Needs infra escalation:** canary still failing → source host down.

## Worked example — 2026-06-01 Kamloops power outage (ALDC-244)

Outage ~20:15–20:44 UTC. Core sales pipeline (Order Item/Order/Payments/Orderline) self-healed
when the scheduler re-kicked queued runs post-recovery; the Snowflake chain rebuilt on the 13:50
cron. Three low-cadence reference templates (Calendar, FINANCIAL CURRENCY, Product Properties
Amazon) failed/zombied and needed manual re-trigger. Calendar canary confirmed the SQL Server was
back; Product Properties took a few minutes of queue-drain (not wedged — agent had 205 completions
in 90 min). No client impact (reference dims ≤4h stale, core pipeline current throughout).

## Automated by

- [[triage-agent]] — encodes this runbook as its proposal playbook (`triage/propose.py`): Step 2
  classification maps to fingerprint → action (Amazon `QuotaExceeded`/IP-block/Firebase → mark-noise;
  `HYT00`/source-host-down/power-outage → escalate-canary; `zombie` → re-trigger; queue-drain latency →
  wait; downstream warehouse → verify), each tagged with its **runbook step** and (for the canary path)
  the **Step 3 canary suggestion** (Calendar / FINANCIAL CURRENCY). A confidence gate means an ambiguous
  message cue surfaces a *suspected* fingerprint for a human rather than auto-asserting the action — every
  output is a recommendation routed to a human, never a service mutation. Read-only.
  - **Step 2 comment→fingerprint now automated (session 12, `triage/connector_error.py`).** The parser
    reads the Eclipse schedule `comment` field directly — both the structured
    `Extraction\Connector error: [{'code','message'}]` form (via `ast.literal_eval`, mirroring
    `check_eclipse_templates.py::_clean_error`/`_group_key`) and plain text — and emits the fingerprint
    as the **authoritative `INCIDENT` source** for the proposal (stronger than inferring from a human's
    email phrasing). This is the agent doing the Step-2 "classify the output" pattern-table lookup itself.
  - **Phase-4 isolated reproduction design resolved (session 12, decisions R27-R30).** The hard endgame —
    actually reproducing a failing connector run in Docker — uses **record/replay**: capture a frozen,
    immutable bundle in prod (resolved work descriptor + inputs + the parsed failure) and replay it through
    a thin `WorkProvider` seam in an isolated, network-less, credential-less container, with
    machine-checkable isolation evidence. The comment + alert_state are enough for *triage* (this runbook)
    but not for deterministic *replay*. Still gated; real capture hook is future.

## See Also

- [[flight-check]] — proactive operational validation (the non-incident counterpart)
- [[debugging-warehouse-loads]] — single-template "data not landing" runbook
- [[Eclipse]] — connector platform; § zombie/queue recovery gotcha
- [[accumulating-source-tables]] — versioned `CURRENT_*`/`MAIN_*` landing semantics
- [[observability-platform]] / [[observability-architecture]] — the monitoring + triage tooling
- [[GP-PENDING-infra-connector-failures]] — longer-running on-prem infra failure post-mortem
- [[GP-PENDING-sales-data-outage-2026-05-22]] — Snowflake task-chain suspension incident
- [[local-network]] / [[agent-builds]] — on-prem host + agent topology
