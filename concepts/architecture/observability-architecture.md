---
tags: [concept, architecture, observability, monitoring, alerting, prometheus, grafana, uptime-kuma, fastapi, azure, slack, mailjet]
aliases: [Observability Architecture, observability stack, three-plane observability]
sources:
  - processes/distributed-workflow/active/observability-platform.md
  - C:/Users/PaulRussell/.claude/plans/fancy-inventing-aho.md
created: 2026-04-24
updated: 2026-04-24
---

# Observability Architecture (v1)

Component diagram, data flows, tool choices, rejected alternatives, and durable schemas for the [[observability-platform]] v1 implementation. Approved 2026-04-24.

The architecture has **three monitoring planes** plus a thin **read API** that doubles as the v2 agent-interface seam. The whole stack runs from one `docker-compose.yml` that's identical on a laptop and on the prod Azure VM.

## Component diagram

```
                                 ┌──────────────────────────────────────────────┐
                                 │             Slack alerts (#observability /   │
                                 │             #observability-dev)              │
                                 └──────────────────▲───────────────────────────┘
                                                    │
                                ┌───────────────────┴────────────────────┐
                                │  obs-alerter  (Python module)          │
                                │  P1/P2/P3 severity, corr-IDs, dry_run  │
                                └───────────▲─────────────▲──────────────┘
                                            │             │
                ┌───────────────────────────┘             └─────────────────────────┐
                │                                                                   │
   ┌────────────┴────────────────┐  ┌──────────────────┐  ┌─────────────────────────┴──────┐
   │  Plane 1                    │  │  Plane 2         │  │  Plane 3                       │
   │  Uptime Kuma                │  │  Prometheus      │  │  obs-jobs (Python image, cron) │
   │  HTTP/TCP/ping/keyword/DNS  │  │  +Pushgateway    │  │  check_eclipse_templates.py    │
   │  6 apps + LAN (TS)          │  │  +Grafana        │  │  check_snowflake_tasks.py      │
   └─────────────▲───────────────┘  └─────▲────▲───────┘  │  check_pbi_refresh.py          │
                 │                        │    │          │  check_data_share.py           │
                 │                        │    │          └────────▲───────────────────────┘
                 │  HTTP probes           │    │  scrape /metrics  │  Cosmos / Snowflake /
                 │                        │    │                   │  PBI REST queries
                 ▼                        │    ▼                   ▼
         eclipse / eclipse_exp /          │   eclipse_exp        Eclipse Cosmos · Snowflake
         core_api / flight-check /        │   /metrics           TASK_HISTORY · PBI REST ·
         workflows / dios + LAN           │   node-exporter      shared-object SELECT 1
                                          │
                                          │           ┌──────────────────────────────┐
                                          └──────────►│  obs-api (FastAPI, :8090)    │
                                                      │  /health/services            │
                                                      │  /jobs                       │
                                                      │  /alerts                     │◄── v2 MCP
                                                      │  /search?corr_id=…           │    wrapper
                                                      └──────────────┬───────────────┘    attaches
                                                                     │                    here
                                                                     ▼
                                                      ┌──────────────────────────────┐
                                                      │  Snowflake                   │
                                                      │  OBSERVABILITY.JOB_RUNS      │
                                                      │  (≥365d, monthly partition)  │
                                                      └──────────────────────────────┘

   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │  Support inbox (separate, Production 2 sub)                                        │
   │                                                                                    │
   │   support@aldc.io  →  Mailjet inbound parse  →  aldcprodfnapsupport1c01            │
   │                                                  ├─ classify(email) ──┐            │
   │                                                  └─ POST Jira REST    │  v2 swap   │
   │                                                                       ▼  point     │
   │                                                       (v1 keyword map; v2 agent)   │
   └────────────────────────────────────────────────────────────────────────────────────┘

   ┌────────────────────────────────────────────────────────────────────────────────────┐
   │  Dead-man switch (separate, non-Azure)                                             │
   │                                                                                    │
   │   UptimeRobot ──HTTPS──►  https://obs.aldc.io/heartbeat  (VM cron writes file)     │
   │        │                                                                           │
   │        └──Slack webhook (separate, on same Slack app)──► #observability(-dev)      │
   │                                                                                    │
   │   Independent: different cloud, different network path, different account.         │
   │   Stays green during a full Azure Canada Central outage AND during Tailscale       │
   │   outages (because /heartbeat is reachable on the Azure public IP, not via TS).    │
   └────────────────────────────────────────────────────────────────────────────────────┘
```

## Tool choices (v1) and why

| Component | Choice | Why this over alternatives |
|---|---|---|
| Synthetic probes | **Uptime Kuma** | Single container, free, built-in Slack webhook, supports HTTP/TCP/ping/keyword/DNS in one place. Declarative seed via `seed.json`. |
| Metrics scrape | **Prometheus** | De-facto standard, eclipse_exp already emits `/metrics` in this format, eclipse_exp ships an `ops/grafana-dashboard.json` we can import as-is. |
| Batch metrics | **Pushgateway** | Standard pattern for short-lived jobs. Lets Plane 3 jobs publish without exposing scrape endpoints. |
| Visualisation | **Grafana** | Imports eclipse_exp dashboard verbatim; Azure Monitor data source covers Application Insights + Cost Mgmt without an agent. |
| Job-health CLIs | **Python (per check)** | Steven's existing script is Python; PBI/Snowflake/Cosmos all have first-class Python SDKs. Containerised for host-portability per local-first contract. |
| Read API | **FastAPI** (`obs-api`) | Same stack as eclipse_exp (familiar). Stable JSON shapes for v2 MCP wrapper. |
| Persistence (probes) | **Prometheus TSDB**, 60-day local retention | Built-in to Prometheus, fits ≥30-day v2 constraint with margin. |
| Persistence (jobs) | **Snowflake `OBSERVABILITY.JOB_RUNS`** | Already inside ALDC's data plane; queryable by Grafana, by `obs-api`, by humans, and by v2 agents. Variant columns absorb per-check payload without schema churn. |
| Alert transport | **Slack webhooks** | Already the team's primary channel; single app `ALDC Observability` per Decisions Log. |
| Probe host (prod) | **Standard B2ms Linux VM** in Quality 1, East US 2 | Native `docker-compose.yml` fit. See § Rejected Alternatives for why not Container Apps / Container Instances. |
| Support-inbox transport | **Mailjet inbound parse** | Mailjet account already used by core_api. Push (not poll), real-time, retries on Mailjet's side. |
| Dead-man switch | **UptimeRobot free tier** | Independent cloud + account. Free for 50 monitors. Posts to Slack via separate webhook. |
| Tunnelling | **Tailscale daemon on the VM** | Already the team's VPN. ACL-controlled access to LAN targets via the existing `kookiet` subnet router. |

## Plane 1 — Uptime Kuma

Probes the 6 public app endpoints from the §F2 inventory, plus on-prem LAN targets when `enable_onprem_probes: true` (prod only):

- `https://eclipse.aldc.io/` (eclipse Web App)
- `https://eclipse-exp.aldc.io/health` (eclipse_exp)
- `https://api.eclipse.analyticlabs.io/v2/health` (Eclipse-2.1 prod core_api)
- `https://aldcprodfnapcore1c01.azurewebsites.net/api/health` (core_api)
- `https://dax.fusion92.eclipse.aldc.io/` (flight-check Next.js)
- `https://audience-fusion92-app.aldc-ca-w1.com/` (DIOS / custom-fusion-92-audience-api)
- LAN (post-cutover, via Tailscale): NPM `192.168.31.20:81`, TrueNAS Covenant, Proxmox iDRAC `192.168.30.{81,83,85,87}`, kookiet `100.70.65.48`.

Cadence: 60s. Failure → P1 alert via Uptime Kuma's built-in Slack webhook.

## Plane 2 — Prometheus + Pushgateway + Grafana

**Prometheus scrapes:**

- `eclipse_exp` `/metrics` (already emitted; uses `prometheus-fastapi-instrumentator`).
- Pushgateway (`:9091`) — receives Plane 3 job batch metrics.
- (Post-cutover) `node-exporter` on the 6 Docker VMs in the [[deployment-groups]] § *Docker Container Runtimes* table, via Tailscale.
- (Post-cutover) `cAdvisor` on the same VMs for container-level metrics.

**Grafana dashboards:**

1. eclipse_exp dashboard imported from `eclipse_exp/ops/grafana-dashboard.json` verbatim.
2. **ALDC Prod Overview** — single dashboard stitching Plane 1 (Uptime Kuma status), Plane 2 (Prom timeseries), Plane 3 (Snowflake `JOB_RUNS` query via Snowflake datasource), and Azure Monitor (Cost Mgmt + Application Insights) into one operator view.

Azure Monitor data source uses a service principal in v1; should move to managed identity once the VM is provisioned (post-cutover).

## Plane 3 — Job-health CLIs

Each script is one entrypoint inside a single Python image, run by a `cron` sidecar on a per-check cadence.

| Script | Cadence (v1 default) | What it does | Source of truth |
|---|---|---|---|
| `check_eclipse_templates.py` | 15 min | Cosmos `work_template` + `schedule` queries; status-count state machine; alerts on `failed`/`zombie`/`no-completion-since-N` per `templates.yaml` config | Seeded verbatim from `C:/Users/PaulRussell/repos/projects/query_template_and_schedule_status/query-cosmos-schedules.py` |
| `check_snowflake_tasks.py` | 30 min | Queries `INFORMATION_SCHEMA.TASK_HISTORY`; alerts on `FAILED` or `SKIPPED` for any configured task chain | [[flight-check]] § 2 query as starting template |
| `check_pbi_refresh.py` | 30 min | PBI REST `/datasets/{id}/refreshes` per workspace; alerts on failure; surfaces credential-expiry countdown | [[powerbi-secret-refresh]] § *Current secret expiry dates* |
| `check_data_share.py` | 60 min | For each shared object in `prod.yaml`: `SELECT 1 FROM <obj> LIMIT 1` (gap detection) + `SELECT MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___)` (frozen-share detection) | [[GP-PENDING-data-share-stability]] + [[snowflake-data-share-refresh]] § *Failure mode 2* |

All four jobs use the same shared lib:

- `lib/alerter.py` — severity routing, dry_run, Slack POST.
- `lib/correlation.py` — UUID4 generation + propagation.
- `lib/labels.py` — emits `client`, `environment`, `service`, `component`, `resource_name` per [[aldc-naming-convention]].
- `lib/snowflake_writer.py` — appends one row per run to `OBSERVABILITY.JOB_RUNS`.
- `lib/push.py` — Pushgateway helper.

### `check_eclipse_templates.py` — what changes from Steven's script

**Preserved verbatim** (Decisions Log 2026-04-24):
- The two Cosmos queries (`get_templates` + `get_schedules`).
- The `process_template` state machine (`init`/`complete`/`failed`/`zombie`, `since_completion`, `last_complete`, `last_failed`).
- `America/Vancouver` display path for human-readable timestamps.

**Changed (the four §F1 gaps):**
1. **Account list sourced from Cosmos** at runtime; the hard-coded 5-account whitelist at the original script's lines 98–104 is dropped.
2. **`templates.yaml` config** distinguishes critical (alert on first failure) from ignorable/flaky (alert after N consecutive failures or M zombies). Resolves Steven's own TODO at lines 37–42.
3. **Prom push + Slack output** via the shared `obs-alerter`. stdout path retained for ad-hoc operator runs.
4. **Correlation ID + UTC** added to every payload. Local display still America/Vancouver.

## obs-api (FastAPI) — the v2 read surface

A read-only FastAPI service that wraps Prometheus and `OBSERVABILITY.JOB_RUNS`. Ships with v1 because moving the read surface in is far cheaper than retrofitting it in v2.

| Endpoint | Returns | Backed by |
|---|---|---|
| `GET /health/services?service=&env=&since=` | Per-service uptime + latest probe status | Prometheus query API + Uptime Kuma DB |
| `GET /jobs?check=&env=&since=` | Per-check run history | `OBSERVABILITY.JOB_RUNS` |
| `GET /alerts?severity=&since=` | Recent alerts (deduped by correlation ID) | `OBSERVABILITY.JOB_RUNS WHERE alert_sent` |
| `GET /search?corr_id=` | Cross-system event timeline for one correlation ID | Prom + JOB_RUNS + alert log |
| `GET /search?resource=` | All events touching a named resource | JOB_RUNS WHERE resource_name = ? |
| `GET /heartbeat` | 200 if VM cron has written within 90s, else 503 | Local file mtime check |

JSON shapes are stable; v2 MCP tools wrap these endpoints 1:1 (see § v2 Seam below).

## Alert topology

| Severity | Definition | Routing | Throttle |
|---|---|---|---|
| **P1 — urgent** | Customer-impacting: app down, prod task chain failed root, share table missing, queue depth >10× baseline. Also: P2 auto-escalated after 24h unresolved. | Slack channel + `@here` | None |
| **P2 — action needed today** | Job failure on a non-critical template, PBI refresh failed, Snowflake task SKIPPED downstream, freshness > expected window | Slack channel only | One per `(check_name, resource_name)` per hour (configurable via `OBS_P2_THROTTLE_SECS`) |
| **P3 — weekly digest** | Soft signals: chronically flaky template, credential expiring in 30 days, unused share grant, cost trend | Single Mon 09:00 PT summary | Aggregated |
| **RESOLVED** | Template/check previously failing now completing again | Green ✅ notification | One on first recovery |

### Alert state management — `lib/state.py`

Every Plane 3 check uses `lib/state.py` for durable per-resource alert state. State persists in `./data/alert_state/alert_state.json` (bind-mounted volume). State writes are skipped in dry-run mode to avoid contaminating live state with test runs.

State structure:
- **`active`**: currently failing resources → `{first_seen, last_alerted, alert_count, failure_count, incident_count}`
- **`history`**: past incidents (survives recovery) → `{incident_count, last_resolved}` — enables recurrence tracking

Key behaviours:
- **Throttle**: P2 re-alerts at most once per `OBS_P2_THROTTLE_SECS` (default 3600s). P1 always fires.
- **Auto-escalation**: P2 → P1 after `OBS_P2_ESCALATE_HOURS` (default 24h) unresolved.
- **Trend tracking**: compares current failure count to previous run's count → "📈 Getting worse (+6)" or "📉 Improving".
- **Recurrence**: increments `incident_count` each time a resource enters a new failing period → "3rd time this month".
- **Recovery**: `mark_resolved()` archives to history and returns entry for the recovery notification.

### Alert message anatomy (Plane 3)

Every Plane 3 alert message contains (when applicable):

```
🟡 Action needed today

⏱ Still failing — first alerted 6h ago · #2 occurrence    ← ongoing banner
📈 Getting worse (+6 failures since last check)             ← trend

Client — Data description for affected dates                 ← impact statement
<View template in Eclipse>  [env]                           ← deep link

Runs: N/M failed (%)   Without completion: N                ← stats
⚠️ N templates failing on agent-name — connector issue      ← blast radius
Data: Most recent complete: Apr 24 (up to date)             ← staleness
Last failed: YYYY-MM-DD HH:MM PT
Agent: agent-id  hostname

Error: <cleaned error text>                                  ← error
Recovery: Auto-recovers at midnight UTC (~10h)               ← estimated recovery
Suggested fix: <action>                                      ← remediation

_UTC timestamp_  `corr-UUID`                                 ← footer
```

**Root-cause grouping**: multiple templates from the same account with the same error fingerprint are bundled into a single message with per-template bullets.

**Data staleness**: computed from completed schedule partition dates (not run timestamps). For partitioned templates (Amazon SC), shows the most recent date for which data IS available, independent of which dates are failing. Staleness ≥ 3 days triggers ⚠️.

**Blast radius**: if N > 2 templates are failing on the same connector agent, each alert notes this — points to a connector-level issue rather than individual template credentials.

**Estimated recovery**: pattern-matched against error text. QuotaExceeded → calculates hours to Amazon midnight UTC reset. Expired secrets / IP blocks → "Requires manual action."

### Channel routing (v1)

| Source | Local dev | Prod |
|---|---|---|
| Uptime Kuma | `#observability-dev` | `#observability` |
| Plane 3 jobs (P1/P2) | `#observability-dev` | `#observability` |
| Recovery notifications | `#observability-dev` | `#observability` |
| Weekly digest (P3) | suppressed by `OBS_DRY_RUN` | `#observability` |
| Dead-man switch (UptimeRobot) | n/a | `#observability` (separate webhook on same Slack app) |
| Mailjet→Jira router | `#observability-dev` | `#observability` |

A single Slack app **"ALDC Observability"** holds all webhooks. Webhook URL selection is the `SLACK_WEBHOOK_URL` env var.

### Correlation ID propagation

```
probe/job emits UUID4 → Prom label corr_id="…"
                     → Snowflake JOB_RUNS.correlation_id
                     → Slack message footer (last line, monospace)
                     → Jira ticket label corr-<UUID>
```

`obs-api` `/search?corr_id=…` walks the timeline. Direct precursor to v2's `observability.trace(correlation_id)` MCP tool.

### `OBS_DRY_RUN` semantics

`OBS_DRY_RUN=true` short-circuits Slack POST: logs `[DRY RUN] severity=P2 …` to stderr. Snowflake writes still happen (Week 2). Pushgateway still receives metrics. State is NOT updated in dry-run mode — dry runs are pure previews with no side effects. Default `true` in `.env`, `false` for live runs.

### Key env vars (alert system)

| Var | Default | Purpose |
|---|---|---|
| `OBS_DRY_RUN` | `true` | Suppress Slack POST; no state writes |
| `OBS_P2_THROTTLE_SECS` | `3600` | Seconds between repeat P2 alerts per resource |
| `OBS_P2_ESCALATE_HOURS` | `24` | Hours before unresolved P2 auto-escalates to P1 |
| `ECLIPSE_PORTAL_URL` | `https://eclipse.aldc.io` | Base URL for template deep links |

## Support-inbox bridge

`support@aldc.io` → MX → Mailjet inbound parse route → POST `aldcprodfnapsupport1c01/api/inbound`.

The Function App (Python, consumption plan) hands the parsed email to `router.route_email()` which calls `classify(email) -> Classification` — the v2 swap point. v1 classifier is a keyword map:

| Bucket | Keywords (case-insensitive substring match in subject + body) |
|---|---|
| Paul | `deploy`, `snowflake`, `pbi`/`power bi`, `warehouse`, `eclipse`, `connector`, `prefect`, `share`, `refresh`, `etl`, `task chain` |
| Lori | `invoice`, `billing`, `credentials`, `access`, `onboard`/`onboarding`, `account`, `user`, `license`, `permission`, `vendor` |
| Default | Paul (round-robin in v2) |

Then `POST /rest/api/3/issue` with assignee accountId resolved via cached lookup. After ticket creation, a single P2 Slack heads-up message lands in the alert channel.

### v2 swap

`classify()` returns a `Classification(assignee, summary, priority, jira_fields)` dataclass. v2 replaces the function body with an MCP call returning the same shape. The agent classifier is free to call `obs-api` first to pre-triage. Nothing else in the pipeline changes.

## Repo Layout

```
observability/
├── docker-compose.yml             # identical local + prod
├── .env.example                   # documents every var
├── .env                           # gitignored; per-host
├── config/
│   ├── local.yaml                 # ships in repo; LAN probes off
│   ├── prod.yaml                  # ships in repo; LAN probes on; full target set
│   ├── test.yaml                  # stubbed for v1
│   └── qa.yaml                    # stubbed for v1
├── stack/
│   ├── prometheus.yml
│   ├── grafana/{datasources,dashboards}/
│   └── uptime-kuma/seed.json
├── jobs/
│   ├── check_eclipse_templates.py
│   ├── check_snowflake_tasks.py
│   ├── check_pbi_refresh.py
│   ├── check_data_share.py
│   ├── lib/{alerter,correlation,labels,snowflake_writer,push}.py
│   └── Dockerfile
├── obs-api/{app.py, Dockerfile}
├── support-inbox/
│   ├── function_app.py
│   ├── router.py
│   └── host.json
├── infra/
│   ├── ansible/                   # VM bootstrap (Docker, Tailscale, cron, journald)
│   └── uptimerobot/               # README + import-able monitor config
└── ops/
    ├── runbook.md                 # mirror of processes/operations/observability-runbook.md
    └── alert-rules.yml
```

## Schemas

### `OBSERVABILITY.JOB_RUNS` (Snowflake)

The load-bearing v2 commitment — stable for v1's lifetime. Adding columns is fine; renaming is breaking.

```sql
CREATE TABLE OBSERVABILITY.JOB_RUNS (
    correlation_id     STRING       NOT NULL,
    check_name         STRING       NOT NULL,           -- 'check_eclipse_templates' | …
    client             STRING,                          -- 'GEP' | 'FUSION92' | 'ALDC'
    environment        STRING       NOT NULL,           -- 'prod' | 'test' | 'qa' | 'local'
    service            STRING,                          -- 'eclipse' | 'snowflake' | 'pbi' | …
    component          STRING,                          -- finer-grained
    resource_name      STRING,                          -- 'TASK_WAREHOUSE_ORDERLINE_0', 'CURRENT_REPORT_ALL_ORDERS_UK'
    status             STRING       NOT NULL,           -- 'ok' | 'warn' | 'fail'
    severity           STRING,                          -- 'P1' | 'P2' | 'P3'
    started_at_utc     TIMESTAMP_NTZ NOT NULL,
    ended_at_utc       TIMESTAMP_NTZ NOT NULL,
    duration_ms        NUMBER,
    details            VARIANT,                         -- per-check structured payload
    metric_summary     VARIANT,                         -- {failed:3, since_completion:7, …}
    alert_sent         BOOLEAN      DEFAULT FALSE,
    slack_message_ts   STRING,
    jira_ticket_key    STRING
)
CLUSTER BY (environment, started_at_utc);
```

Retention ≥365 days via Time Travel + monthly partition.

> **Agent telemetry does NOT land here.** Per-decision telemetry from the v2 agent ([[triage-agent]]) is
> high-volume request telemetry, not scheduled-job health — it gets its own sibling tables
> **`AGENT_DECISIONS` / `AGENT_EVALS` / `AGENT_DRIFT_WINDOWS`** (R18), keeping `JOB_RUNS` clean for
> scheduled/bounded jobs (eval batches / drift jobs / prompt-regression runs stay here *as jobs*). The
> table DDL/ownership + write path are an **open contract** between this platform and the agent — see
> [[agent-observability-telemetry]] (built locally in SQLite first, behind an export seam).

### Label vocabulary

Pulled from [[aldc-naming-convention]]:

| Label | Values |
|---|---|
| `client` | `GEP` (incl. Navira), `FUSION92`, `ALDC`, plus tenant aliases |
| `environment` | `prod`, `test`, `qa`, `dev`, `demo`, `supt`, `stg`, `local` |
| `service` | `eclipse`, `eclipse_exp`, `core_api`, `flight-check`, `workflows`, `dios`, `connector`, `prefect`, `snowflake`, `power-bi`, `cosmos`, `azure-queue` |
| `component` | depends on service (e.g. `connector_agent`, `task_chain`, `dataset_refresh`, `share_object`) |
| `resource_name` | the actual ALDC-named resource: `aldcprodfnapcore1c01`, `TASK_WAREHOUSE_ORDERLINE_0`, `CURRENT_REPORT_ALL_ORDERS_UK`, etc. |

## Probe-host placement (prod) — fate-sharing mitigations

The probe host is a Standard B2ms Linux VM `aldcqalnxnobs1u01` in **Quality 1 sub, East US 2** — distinct subscription AND distinct region from the biggest things it watches (`aldcprodrsgp1c` Canada Central). Three concrete mitigations honour the Decisions Log "Probe host (REVISED)" entry:

1. **External non-Azure dead-man switch** — UptimeRobot free tier probes `https://obs.aldc.io/heartbeat` at 60s. The VM's `cron` writes a heartbeat file every 30s; the endpoint returns 503 if older than 90s. UptimeRobot pages a *separate* Slack webhook (on the same `ALDC Observability` app) when it sees ≥2 consecutive failures. Independent cloud, account, and network path from Azure.
2. **Region + subscription separation** — Azure Canada Central regional outage cannot silence the monitor; an incident scoped to the Production 2 subscription cannot silence the monitor. Quality 1 also already hosts Prefect, so observing it is co-located.
3. **Tailscale-in-Azure for LAN probes** — Tailscale daemon on the VM joins the existing tailnet. LAN-only targets reach via Tailscale through the `kookiet` subnet router. The dead-man switch in (1) does **not** depend on Tailscale, so a Tailscale outage is detectable independently — on-prem probes go red but the monitor itself stays alive and pages the Tailscale outage as a P1.

## v2 Seam

```
                 ┌──────────────────────────────┐
                 │  v1 obs-api (FastAPI)        │  ← unchanged in v2
                 │  /health/services            │
                 │  /jobs                       │
                 │  /alerts                     │
                 │  /search?corr_id=…           │
                 └──────────────┬───────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────────────┐
    │  v2 MCP server   │ │  v2 CLI      │ │  v2 support-inbox    │
    │  observability.* │ │  obs query…  │ │  agent classifier    │
    │  tools           │ │              │ │  (replaces classify) │
    └──────────────────┘ └──────────────┘ └──────────────────────┘
```

| v2 MCP tool (sketch) | Maps to obs-api endpoint |
|---|---|
| `observability.query_service_health(service, env, since)` | `GET /health/services` |
| `observability.query_job_runs(job_name, env, since)` | `GET /jobs` |
| `observability.list_recent_alerts(severity, since)` | `GET /alerts` |
| `observability.search_by_resource(resource_name)` | `GET /search?resource=` |
| `observability.trace(correlation_id)` | `GET /search?corr_id=` |
| `observability.classify_support_email(email)` | new v2-only tool; replaces `router.classify()` body |

What v1 commits to so v2 is cheap:
- `OBSERVABILITY.JOB_RUNS` schema is stable.
- `obs-api` JSON shapes are stable.
- Labels normalised to [[aldc-naming-convention]].
- Correlation IDs are end-to-end on every event.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| **Datadog / New Relic SaaS** | Cost disproportionate at ALDC scale. Ingesting internal data paths into a third-party also creates an ingress story we don't want to own for clients. |
| **Grafana Cloud free tier** | Viable, but ties ingest limits to a third-party's pricing evolution. Kept as a fallback if self-hosting becomes painful. Not v1. |
| **Custom Next.js dashboard inside [[eclipse_exp]]** | Only worthwhile once eclipse_exp is the canonical control plane. Today it's still being stood up — leaning on it now couples v1 to another project's timeline. |
| **Azure Monitor / Alerts alone** | Azure-centric; doesn't cover on-prem, Snowflake, PBI, Mailjet. Role is "one of the planes" via Grafana data source, not the whole platform. |
| **Azure Container App as probe host** | Single-container preferred; multi-container is a sidecar workaround that breaks the "single docker-compose, host-portable" contract. File-share-only persistent volumes are awkward for the Prom TSDB. Same control plane as eclipse_exp, so high fate-sharing. |
| **Azure Container Instance group as probe host** | Better than Container App on multi-container support, but still file-share-only volumes and same fate-sharing as Container App. |
| **Probe host on `aldcsuptdock1c01` (Nostromo)** | Originally the recommendation — overridden 2026-04-24 because Paul is moving ALDC off on-prem dependence. Old rationale retained in tracker for context. |
| **IMAP poll** for support inbox | Stuck IMAP sessions hang silently; need M365 service account. Mailjet inbound parse is push, retried on Mailjet's side, and uses an account we already have. |
| **Single Slack app "ALDC Observability" + a second app for prod** | Decisions Log explicitly forbids registering a second app. Add a second incoming webhook to the same app instead. |
| **Absorb scripts into [[aldc-scripts]]** | Status of that repo is "likely legacy" per its own wiki page; mixing new critical infra with an unverified grab-bag is risky. Dedicated repo wins. |
| **Push job-health straight to Slack with no durable store** | Forecloses the v2 agent-queryable interface (the agent would have to re-run probes). The Snowflake `JOB_RUNS` table is the load-bearing v2 commit. |
| **Skip correlation IDs in v1** | Forecloses `observability.trace(correlation_id)` in v2 — would require a backfill or a forensic gap. Cheap to add up-front; expensive to add later. |

## See Also

- [[observability-platform]] — project page (scope, owners, phasing).
- [[agent-observability-telemetry]] — the v2 agent's per-decision telemetry (`AGENT_*` sibling tables, online-eval pyramid, shadow mode) that lands beside this platform's `JOB_RUNS`.
- `processes/distributed-workflow/active/observability-platform.md` — workstream tracker.
- [[eclipse_exp]] — reference implementation for app-level health (dashboard JSON imported here).
- [[flight-check]] — manual operational runbook automated by Plane 3.
- [[aldc-naming-convention]] — label vocabulary.
- [[deployment-groups]] — per-env Azure resource inventory.
- [[azure-environments]] — subscription model.
- [[local-network]] — Tailscale + Covenant + NPM.
- [[mailjet]] — inbound parse mechanism.
- [[connector-timeout-outage]], [[powerbi-secret-refresh]], [[GP-PENDING-data-share-stability]], [[snowflake-data-share-refresh]] — incidents motivating specific monitors.
- [[aldc-scripts]] — `send_slack.sh` pattern reference (re-implemented in Python here; do NOT depend on the bash script).
