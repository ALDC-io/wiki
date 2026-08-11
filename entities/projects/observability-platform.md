---
tags: [entity, project, observability, monitoring, alerting, platform, aldc, ofelia, cron]
aliases: [Observability Platform, ALDC Observability, observability-platform, observability project]
sources:
  - processes/distributed-workflow/active/observability-platform.md
  - C:/Users/PaulRussell/.claude/plans/fancy-inventing-aho.md
created: 2026-04-24
updated: 2026-08-10
---

# Observability Platform

ALDC's lightweight, company-wide observability and monitoring platform — a small self-hosted stack that answers, at a glance and with alerting, whether every ALDC application, data job, on-prem and Azure resource, and the support inbox is healthy. Production-only scope for v1; env-parametric by config so Test / QA / Dev plug in later without refactor. Ratified design lives at [[concepts/architecture/observability-architecture|observability-architecture]].

> **Status (2026-04-25): Week 1 complete.** Stack running locally. `check_eclipse_templates.py` live, firing real alerts to `#observability-dev`. Week 2 (Plane 2 + remaining Plane 3 + Snowflake + obs-api) is next session.

## Why this exists

Today the five health questions in the workstream tracker's *Goal* section are answered by manually poking [[Snowflake|Snowsight]], [[Power BI|Power BI Service]], [[Portainer]], the [[Azure|Azure Portal]], and Steven's ad-hoc `query-cosmos-schedules.py` script. There is no unified surface and no alerting. The most painful gaps surfaced as recent incidents:

- [[connector-timeout-outage]] — no queue-depth alerting; the issue was diagnosed only after customers complained.
- [[GP-PENDING-data-share-stability]] — `PROD_DG1_GEP` share occasionally drops tables silently; detected only when a deploy fails.
- [[snowflake-data-share-refresh]] § *Failure mode 2* — frozen-share, 42-day undetected staleness on a SellerCloud view.
- [[powerbi-secret-refresh]] — credential expiries are tracked in an Outlook calendar, not a system.

v1 lands the alerting and the dashboard for these and the rest of the §F2 inventory in the tracker.

## Scope

### In scope (v1)

| Plane | What | Reference |
|---|---|---|
| 1 — Synthetic / uptime | HTTP health probes for the 6 ALDC apps + on-prem LAN targets | [[observability-architecture]] § Plane 1 |
| 2 — Metrics | Prometheus + Pushgateway + Grafana; node-exporter on Docker VMs; Azure Monitor read | [[observability-architecture]] § Plane 2 |
| 3 — Job-health | Python CLIs for Eclipse templates, Snowflake tasks, PBI refresh, data shares | [[observability-architecture]] § Plane 3 |
| Read API | `obs-api` FastAPI — thin read-only surface for v2 agents | [[observability-architecture]] § obs-api |
| Alerter | P1/P2/P3 severity routing, correlation IDs, Slack | [[observability-architecture]] § Alert Topology |
| Support inbox | Mailjet inbound parse → Function App → Jira REST | [[observability-architecture]] § Support Inbox |

### Out of scope (v1, deferred to v2 or later)

- LLM-based email classification.
- Distributed tracing wire-up beyond what eclipse_exp already emits.
- Full log aggregation (Loki / Elastic).
- Client-visible SLA dashboards (GEP, Fusion92).
- Non-prod environment monitors (Test / QA / Dev) — `test.yaml` and `qa.yaml` ship stubbed.
- v2 MCP server / CLI / agent classifier — sketched in [[observability-architecture]] § v2 Seam.

## Recommended Alerts

High-priority alert rules that should be implemented in Plane 3 (job-health monitors). Listed here as backlog items pending the Week 2/3 implementation sessions.

### Snowflake Task Suspension (Priority: Critical)

**What:** Poll `SHOW TASKS IN DATABASE PROD_DG1_GEP` every 15 minutes and alert if any task has `state='suspended'` and `last_suspended_reason='SUSPENDED_DUE_TO_ERRORS'`.

**Why this matters:** [[GP-PENDING-sales-data-outage-2026-05-22]] was a 14-hour outage caused by an auto-suspended root task. The suspension happened at 19:52 PT and was not detected until a client report the following morning (09:14 PT). A 15-minute check would have caught this within one poll cycle.

**Implementation:**
- Run via the existing Snowflake connection (account `wj66376`, role `PROD_DG1_CORE_ADMIN` or `ACCOUNTADMIN`).
- Query: `SHOW TASKS IN DATABASE PROD_DG1_GEP` — parse output for `state = 'suspended'` AND `last_suspended_reason = 'SUSPENDED_DUE_TO_ERRORS'`.
- Alert to `#observability-dev` (dev) / `#observability` (prod) Slack channel.
- Severity: **P1 (Critical)** — stale data ships to client immediately.
- Recovery: auto-resolve when task returns to `state = 'scheduled'` or `state = 'started'`.

**Diagnostic runbook:** See [[Snowflake]] § Task Suspension Diagnosis for the SQL to diagnose and resume.

## Owners

| Role | Person |
|---|---|
| Workstream lead | Paul Russell (`paul.russell@aldc.io`) |
| Support-inbox co-owner | Lori Beck (`lori.beck@aldc.io`) |
| Reference implementation source | Steven (failing-templates script) |

Slack:
- `#observability-dev` (private) — created 2026-04-24, channel ID `C0AV0PRJ4JF`. Webhook vaulted in `vault/credentials.md` § Observability.
- `#observability` (public, prod) — **deferred** until v1 prod cutover.

## Repo

`github.com/ALDC-io/observability` — to be created at the start of Week 1 implementation. Local clone path will be `C:/Users/PaulRussell/repos/observability/`. Layout is documented in [[observability-architecture]] § Repo Layout.

## ⚠ Adding a Plane 3 job — four ways it silently never runs

Learned the hard way deploying `check_account_freshness.py` ([[FU92-421]], 2026-08-10). The script
was committed, correct, and validated read-only against prod — and would still have done **nothing**,
every night, forever. Four independent faults, none of which surfaces an error anyone would see.
Walk this list for every new job.

1. **`jobs/Dockerfile` COPYs scripts by name.** There is no `COPY *.py`. A new script that isn't
   added is simply absent from the image; ofelia execs it and gets *"can't open file"*. Add the
   `COPY` line.
2. **`lib/push.py`'s signature is `push(job_name, registry)` — job name FIRST.** Calling
   `push.push(registry, job=NAME)` raises `TypeError`, which the conventional surrounding
   `try/except` swallows to stderr. Result: the job looks fine and **zero metrics ever reach
   Prometheus**. Copy the call from `check_gp199_attribution.py`, don't write it from memory.
3. **⭐ Ofelia reads job labels ONLY at daemon start. It does not re-scan a running container.**
   Recreating `obs-jobs` is *not* enough — the job ends up registered **nowhere**: it looks deployed,
   never fires, and stays silent. After any label change:
   ```bash
   docker compose up -d obs-jobs && docker compose restart cron
   docker logs cron --tail 100 | grep "New job registered"   # confirm yours is listed
   ```
4. **Ofelia cron is 6-field with a LEADING SECONDS field** (robfig/cron `WithSeconds`). A 5-field
   expression is parsed seconds-first: `"*/15 * * * *"` fires every 15 **seconds**. Always write
   `"sec min hour dom mon dow"`.

**Prove it fires through its scheduled path — don't infer it from a manual `docker exec`.** Install a
temporary schedule a few minutes out, recreate + restart cron, and watch the job actually start in
`docker logs cron`; confirm the Pushgateway `push_time_seconds{job="…"}` advances to that run's
timestamp. Then restore the real schedule. A monitor that has never been observed firing is not
deployed, it is hopeful.

**Reading the logs:**
- `docker logs cron --since <dur>` is **unreliable** here — Docker's log timestamps and the ones
  ofelia prints into the message body disagree, so `--since 24h` can return 0 lines while entries
  from minutes ago exist. Use `--tail N` instead.
- Ofelia marks any run with a non-zero exit as `failed: true`. These jobs exit 1 when they find
  problems, so **"failed" in the cron log does not mean the job crashed.** The discriminator is the
  Prometheus `*_up` gauge (0 = ran, found problems) vs. an absent/stale metric (= genuinely crashed).
- Pushgateway retains metrics **indefinitely**. A `job="…"` entry proves the job ran *at some point*,
  not that it ran today — always read `push_time_seconds` before concluding a job is alive.

**Credentials:** `SF_ACCT/SF_USER/SF_PWD/SF_ROLE` are already wired into `obs-jobs` for the GP-199
monitor — a service account with **plain password auth and no MFA**. A new Snowflake job needs no new
credentials, and can be run ad-hoc in-container without triggering an MFA push to a phone. Set
`SF_AUTHENTICATOR=username_password_mfa` only when running locally as a human.

**Config placement:** put job config in `config/` (mounted read-only at `/app/config`), not in
`jobs/`. Anything under `jobs/` is baked into the image, so editing an ignore list or enabling a feed
would need a rebuild. Guard against an empty config being read as healthy — a monitor scanning zero
feeds reports green forever, which is the exact failure these jobs exist to catch.

## Phasing

Three weeks, dependency-ordered:

1. **Week 1** — Local stack (no Azure spend). Plane 1 + first Plane 3 job. Exit criterion: real alert in `#observability-dev` from a real production failure.
2. **Week 2** — Plane 2 + remaining Plane 3 jobs + `obs-api` + Snowflake `OBSERVABILITY.JOB_RUNS` + Grafana dashboard. Still local. Exit criterion: 30-day history queryable by correlation ID.
3. **Week 3** — Azure cutover (B2ms VM in Quality 1 / East US 2), UptimeRobot dead-man switch, Mailjet inbound → Jira. Exit criterion: prod alerts flow to `#observability`, support email creates a Jira ticket.

Full step-by-step procedure for each week is in the workstream tracker's Execution Boot Prompt.

## Decisions

The full Decisions Log is in `processes/distributed-workflow/active/observability-platform.md`. Summary of durable choices ratified for v1:

- Dedicated `observability` repo under `github.com/ALDC-io`; do NOT absorb into [[aldc-scripts]].
- Self-hosted (Uptime Kuma + Prometheus + Pushgateway + Grafana + Python jobs + `obs-api`).
- Probe host: local dev → **Linux VM in Quality 1 sub, East US 2** for prod. Three fate-sharing mitigations baked in (UptimeRobot dead-man switch, region+sub separation, Tailscale-in-Azure with dead-man-switch independence).
- Single `docker-compose.yml` runs identically on laptop and prod VM.
- Slack: `#observability-dev` for dev, `#observability` for prod (created at cutover). Single Slack app **"ALDC Observability"** holds both webhooks.
- Alert severities: **P1** page-now, **P2** within-day, **P3** weekly digest. Correlation IDs end-to-end.
- Plane 3 `check_eclipse_templates.py` seeds from Steven's `query-cosmos-schedules.py` — preserve the two Cosmos queries + status-count state machine verbatim, extend the four §F1 gaps.
- Support-inbox v1: Mailjet inbound parse → `aldcprodfnapsupport1c01` Azure Function → Jira REST. Keyword router with stable `classify(email) -> Classification` seam for v2 agent swap.
- v2 agent-queryable interface acknowledged: `obs-api` is the v2 read surface; `OBSERVABILITY.JOB_RUNS` schema is the load-bearing v2 commit; `classify()` is the v2 swap point.

## Querying this project

When working on observability:
- Read [[observability-architecture]] for the design itself (component diagram, data flows, alert topology, schemas, rejected alternatives).
- Read the workstream tracker (`processes/distributed-workflow/active/observability-platform.md`) for current phase, blockers, and the Execution Boot Prompt for the next implementation session.
- Tool pages for [[uptime-kuma]] / [[prometheus]] / [[grafana]] are written when those components are first stood up (Week 1–2).
- Runbook (`processes/operations/observability-runbook.md`) is written when the platform is live (post-Week 3).

## Cross-cutting impact

This platform changes how a number of existing processes are run. None of those pages are edited by this workstream — instead, write a *Cross-Lane Request* in the tracker if behaviour needs to change:

- [[flight-check]] — today's manual operational validation; v1 automates pieces of it. Future cross-lane work folds the Plane 3 checks into the runbook as the canonical pre-deploy step.
- [[powerbi-secret-refresh]] — the 30-day expiry countdown becomes a P3 weekly-digest entry rather than an Outlook calendar reminder.
- [[GP-PENDING-data-share-stability]] — `check_data_share.py` provides Option C (proactive monitoring) of that ticket's recommended approaches; covers detection while Option A (future grants) is the longer-term prevention.
- [[connector-timeout-outage]] — queue-depth alerting on `aldcprodstacqueue1c01` is in v1 scope.
- [[executive-snapshot-email]] — sibling weekly-Slack pattern, different VM. Reference only; not consumed.

## See Also

- [[observability-architecture]] — component diagram, data flows, schemas, rejected alternatives.
- `processes/distributed-workflow/active/observability-platform.md` — workstream tracker, Decisions Log, Session Log, Boot Prompts.
- [[eclipse_exp]] — reference implementation for app-level health (`/ping`, `/health`, `/metrics`, structlog, `ops/grafana-dashboard.json`).
- [[flight-check]] — today's manual observability runbook.
- [[aldc-naming-convention]] — label vocabulary for metrics + Snowflake rows.
- [[deployment-groups]] — per-env Azure resource inventory; source of truth for what to probe.
- [[azure-environments]] — subscription model.
- [[local-network]] — Tailscale + Covenant + NPM context for on-prem probes.
- [[mailjet]] — inbound-email mechanism for support inbox.
- [[aldc-scripts]] — sibling weekly-Slack prior art (`send_slack.sh`); status unverified, do not depend on.
- [[connector-timeout-outage]], [[powerbi-secret-refresh]], [[GP-PENDING-data-share-stability]], [[snowflake-data-share-refresh]] — incidents motivating specific v1 monitors.
