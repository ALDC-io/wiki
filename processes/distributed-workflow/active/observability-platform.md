---
tags: [distributed-workflow, active, observability-platform]
aliases: [Observability Platform Tracker, Company-Wide Observability Tracker]
sources: []
created: 2026-04-24
updated: 2026-04-24 (planning session complete: design approved by Paul; project page + architecture page written; entering execution phase)
---

# Observability Platform — Workstream Tracker

Design and build a **lightweight, company-wide observability & monitoring platform** covering ALDC application health, data-pipeline health, on-prem + Azure infrastructure health, and the support inbox. Production-only scope for v1; env-parameterised so Test / QA / Dev can be added later without refactor.

## Goal

End state is a platform that answers, at a glance and with alerting, five questions for **Production** without manual Snowsight / Power BI Service / Portainer / Azure Portal poking:

1. **Is every ALDC app up and healthy?** (eclipse, eclipse_exp, core_api, flight-check, workflows / DAX API, custom-fusion-92-audience-api / DIOS)
2. **Is every data job on schedule and succeeding?** (Eclipse templates, [[connector]] runs, Snowflake tasks, Power BI refresh, prod→test data shares)
3. **Is the infrastructure healthy?** (Proxmox hypervisors Nostromo / Sulaco / Patna / Auriga / Infinity, the six Docker VMs, TrueNAS/Covenant, Tailscale kookiet router, Nextcloud, Server4 cron host)
4. **Are Azure resources healthy and inside cost budget?** (Function Apps, Web Apps, Cosmos DB, Storage Accounts, Queue depth — especially the `/work/pick` queue surfaced in [[connector-timeout-outage]])
5. **What is in the support inbox right now, and is it routed?** (email → Jira, assigned to Paul or Lori)

"Done for v1" = a running deployment with `/health` synthetic probes on all apps, node-level metrics on all Proxmox hosts + Docker VMs, a Snowflake / PBI / template-failure job-health sweep running on a schedule, a support-inbox bridge creating Jira tickets, a single Slack channel receiving all alerts, and one Grafana dashboard that surfaces all of the above.

Out of scope for v1 (revisit in v2):

- LLM-based email classification for support inbox (keyword router is enough for v1).
- Distributed tracing across services (eclipse_exp already emits OTel; wire it up only if it's effectively free).
- Full log aggregation (Loki / Elastic). Query Application Insights directly for now.
- Ingest of client-visible SLA metrics (GEP / Fusion92 uptime reports). Internal view only.
- Non-prod environments. Platform must be **env-parametric by config**, but only Prod monitors run in v1.
- **Agent-facing query interface** (MCP server / CLI / read API that a Claude Code session can call to triage an inbound support email). Deferred to v2. Full design intent captured in *Future Scope — v2 Agent Interface* below so v1 can be shaped to not preclude it.

## Lane

Wiki: **ALDC**

Owned paths (this workstream may write here):

- `processes/distributed-workflow/active/observability-platform.md` (this tracker)
- `entities/projects/observability-platform.md` (new — the design doc)
- `concepts/architecture/observability-architecture.md` (new — component diagram, data flows, tool choices, rejected alternatives)
- `processes/operations/observability-runbook.md` (new — once the platform is live: how to respond to alerts, rotate creds, extend monitors)
- `entities/tools/uptime-kuma.md`, `entities/tools/prometheus.md`, `entities/tools/grafana.md` (new — only if those tools are chosen during plan-mode approval)
- A new repo outside the wiki at `C:/Users/PaulRussell/repos/observability/` once Paul greenlights a dedicated repo (see Decisions Log).

**Read-only outside the lane.** In particular, do not edit existing runbooks ([[flight-check]], [[gep-snowflake-pbi-deployment]], [[powerbi-secret-refresh]], [[executive-snapshot-email]], [[connector-docker-deployment]], [[agent-builds]]) or tool pages ([[Snowflake]], [[Power BI]], [[Eclipse]], [[Azure]], [[proxmox]]) in this session. If the design implies changes to those pages, write a *Cross-Lane Request* and surface to Paul.

## Required Context

Read in parallel at boot. This is a large reading list because the platform touches every ALDC system — skim for the observability-relevant sections, not cover-to-cover.

**Applications to monitor:**
- [[core_api]] — Function App `aldcprodfnapcore1c01`; no `/health` today; `/work/pick` historical timeout.
- [[eclipse_exp]] — Reference implementation. Already has `/ping`, `/health`, `/metrics` (Prometheus), structlog + correlation IDs, `ops/grafana-dashboard.json`, Slack alerts on job failures. **Use its patterns verbatim for the other services.**
- [[entities/repos/eclipse|eclipse (repo)]] — Legacy portal UI, no health today.
- [[entities/repos/flight-check|flight-check (repo)]] — Next.js iframe; has 4 backend deps.
- [[workflows]] — F92 Azure Functions, includes DAX API routes + Bing Ads token refresh cron.
- [[custom-fusion-92-audience-api]] — DIOS API, on-prem, 60 GB memory, Gunicorn 2 workers.

**Data pipeline to monitor:**
- [[connector]] — Docker data plane across 6 VMs; Prefect migration in progress.
- [[Prefect]] — QA-sub hosted; will replace connector.
- [[flight-check]] — The operational validation runbook; today's manual version of what v1 automates.
- [[Snowflake]] — Task history, data freshness patterns.
- [[snowflake-data-share-refresh]] + [[GP-PENDING-data-share-stability]] — Silent share-object drops are a known, unsolved hazard; v1 must detect them.
- [[Power BI]] — Refresh cadence + credential expiry.
- [[powerbi-secret-refresh]] — Known upcoming credential expiries → calendar-style alerting candidate.
- [[data-pipeline-flow]] — End-to-end flow the job-health sweep traces.
- [[connector-timeout-outage]] — Queue-depth + latency alerting motivation.

**Infrastructure to monitor:**
- [[deployment-groups]] — Per-env Azure + on-prem VM inventory. The source of truth for what to probe.
- [[azure-environments]] — Subscription map.
- [[aldc-naming-convention]] — Resource naming pattern (`aldc<env><type><func><group><region><seq>`) — lets config files loop over envs predictably.
- [[local-network]] — Nginx / TrueNAS / Tailscale / Covenant. The monitor must survive a Tailscale outage, so the probe host must NOT depend on Tailscale for its outbound path.
- [[agent-builds]] — Proxmox Agent VM provisioning.
- [[proxmox]] — Host inventory + iDRAC creds.
- [[entities/tools/nextcloud|nextcloud]] — Asset sync, CIFS reconnect hazard.
- [[executive-snapshot-email]] — Existing cron pattern on Auriga VM 11099; reference for "scheduled job that posts to Slack."

**Support inbox context:**
- [[mailjet]] — Inbound-email candidate. Sender domain `@aldc.io`.
- [[aldc-scripts]] — `send_slack.sh` is the reusable Slack webhook wrapper; `cost-monitoring/` is the closest prior art for "scheduled report → Slack", author Lori Beck. Treat it as reference implementation, **not** as working production until someone confirms the cron still runs on Server4 and `#the-olds` still exists. Paul cannot see `#the-olds` — signal it is dead.

**Pattern + protocol:**
- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\README.md`
- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\orchestration-pattern.md`
- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md`
- `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`

## Plan-Mode Rule

**Every session in this workstream is plan-mode-first** until an approved design lives in `entities/projects/observability-platform.md` AND an approved architecture in `concepts/architecture/observability-architecture.md`. Scope is genuinely fuzzy — there are at least four viable stacks (self-hosted Prometheus+Grafana+Uptime Kuma; Grafana Cloud free tier; Datadog SaaS; absorb into [[eclipse_exp]] ops surface) and the support-inbox arm could land as an Azure Function, a Prefect flow, or a Logic App. Don't start writing the design page until the structure is approved.

After the design exists, future sessions that **implement** individual components (e.g. "stand up Uptime Kuma on Nostromo", "write the Snowflake task-history monitor") should plan-mode-first per the workstream defaults in [[session-lifecycle]] — each new component is its own scoped decision.

The **end-of-day merge session** that applies Pending Wiki Updates is mechanical and does NOT enter plan mode.

## Session Log

Append-only. Newest at the bottom.

### 2026-04-24 — Bootstrap: tracker created, research pass complete (Opus, research-only)

- **did:**
  - Read distributed-workflow README / orchestration-pattern / session-lifecycle / tracker-template.
  - Spawned two research subagents in parallel: (a) locate Steven's failing-templates script in the "workflow library"; (b) full inventory of everything needing observability across apps / pipeline / infra / Azure / support inbox.
  - Consolidated findings into this tracker's *Required Context* and into the *Research Findings* section below.
  - No code or design writing this session — per Plan-Mode Rule above, design session is next.
- **decided:**
  - This is a distributed-workflow workstream, not a single-session job — too many decisions (repo vs absorb, tool choice, env parameterisation strategy, support-inbox router depth, alert-channel topology) to settle in one go.
  - Plan-mode-first for every session until the design doc lands.
  - v1 is Production-only but env-parametric-by-config. No non-prod monitors in v1.
- **next:** Open a fresh Claude Code session using the *Planning Boot Prompt* below. That session enters plan mode, produces a proposed architecture + tool selection + phasing, folds in Steven's failing-templates script (arriving from Paul), and waits for Paul's approval before any writing outside this tracker.

### 2026-04-24 — Blockers resolved + v2 agent interface scoped (Opus, research-only continuation)

- **did:**
  - Paul returned answers to the five blockers. Moved four to Decisions Log (dedicated repo ✅, self-host ✅, Lori confirmed ✅, new Slack channel for v1 ✅) and reframed Steven's script as an arriving hand-off rather than missing work.
  - Added *Future Scope — v2 Agent Interface* section capturing Paul's intent to make observability agent-queryable (support-email → agent → observability query → Jira ticket with pre-triage). Five concrete "shape-of-v1 constraints" recorded so v1 choices do not foreclose v2: durable persistence, ALDC-naming-convention labels, thin stable read surface, correlation IDs, ≥30-day retention.
  - Trimmed Planning Boot Prompt so the next session does NOT re-ask resolved questions.
- **decided:** dedicated repo; self-host; Lori; provision new Slack channel; v2 agent interface is a stated constraint on v1.
- **next:** Planning Boot Prompt below. Same trigger as before — now with fewer open questions and a v2 agent-interface guardrail.

### 2026-04-24 — Steven's script located and absorbed (Opus, research continuation)

- **did:**
  - Paul provided location: `github.com/ALDC-io/projects/query_template_and_schedule_status/`. Repo already cloned at `C:/Users/PaulRussell/repos/projects/`.
  - Read `query-cosmos-schedules.py` (~375 lines), `.env.template`, `requirements.txt`.
  - Rewrote §F1 from "NOT located" to full analysis: CLI surface, exit codes, Cosmos query shape, env vars, and four v1 gaps — hard-coded 5-account whitelist, missing critical/ignorable template config, stdout-only output, no correlation IDs. Identified Steven's own TODOs in-source (lines 37-42) as v1-scope items.
  - Added Decisions Log entry committing to preserve the two Cosmos queries + status-count state machine verbatim; re-home the wrapper into the new `observability` repo.
  - Cleared the "script handoff" open blocker.
- **decided:** `observability/jobs/check_eclipse_templates.py` seeds from `query-cosmos-schedules.py`; keep the correctness core, extend with the four gaps, keep original in-place as reference until v1 ships.
- **next:** Open Planning Boot Prompt session. Two open blockers left (probe host VM, Slack channel name).

### 2026-04-24 — Probe host clarified + Slack channel decided (Opus, research continuation)

- **did:**
  - Explained probe host function to Paul (Docker Compose host for Uptime Kuma + Prometheus + Grafana + job-health CLIs; "who watches the watchers" failure-isolation concerns around Tailscale dependence and Azure fate-sharing).
  - Paul chose `#observability` as the v1 Slack channel — single firehose, categorisation by service + client deferred to v2 via the existing naming-convention labels.
  - Added Decisions Log entries: `#observability` channel; probe host v1 recommendation is `aldcsuptdock1c01` (existing support Docker VM on Nostromo, zero provisioning, correct failure isolation); rejected Azure Container App (fate-shared with monitored apps); fresh VM on Nostromo deferred to v2.
  - Cleared both open blockers from the blockers section; moved to Resolved.
- **decided:** v1 channel = `#observability`; v1 probe host candidate = `aldcsuptdock1c01` pending planning-session confirmation; v2 channel topology uses `(service_type, client)` label → webhook routing table.
- **next:** Paul creates `#observability` Slack channel + webhook; then open Planning Boot Prompt session. All blockers are cleared — the planning session is now a pure design exercise.

### 2026-04-24 — Local-first dev workflow added (Opus, research continuation)

- **did:**
  - Paul asked whether the probe host can run locally during development and migrate to prod once stable. Confirmed yes; documented the constraints, the cutover procedure, and the "what changes / what doesn't" matrix in a new *Development Workflow — local-first, host-portable* section.
  - Six durable rules: single `docker-compose.yml`, all env-specific values in `.env` + `config/<env>.yaml`, `enable_onprem_probes` flag for LAN targets, `#observability-dev` channel for dev / `#observability` for prod, fresh-start TSDB at cutover, secrets via local `.env` → Azure Key Vault/Dashlane in prod.
  - Cutover = `git pull` + swap `.env` + flip flag + `docker compose up -d` on `aldcsuptdock1c01`. ~30-minute mechanical step.
  - Added Decisions Log entry locking in local-first development as a v1 constraint.
- **decided:** v1 must be host-portable. Plane 3 jobs are containerised (not laptop-Python-version-sensitive). `local.yaml` and `prod.yaml` both ship in the repo from day one. Local dev does NOT page real people — separate Slack channel or `dry_run` flag.
- **next:** Paul creates `#observability` (and optionally `#observability-dev`) + webhooks. Then open Planning Boot Prompt session. All blockers are cleared.

### 2026-04-24 — Pre-planning checklist resolved; probe host pivoted to Azure (Opus, research continuation)

- **did:**
  - Paul returned answers to the five pre-planning checklist items. `#observability-dev` created (private); `#observability` deferred until v1 prod cutover. Slack app "ALDC Observability" registered; dev webhook captured to `vault/credentials.md` under a new *Observability* section (channel ID `C0AV0PRJ4JF`; prod webhook TBD via *Add New Webhook to Workspace* on the same app).
  - Paul clarified that the archive link he copied (`slack.com/archives/C0AV0PRJ4JF`) is NOT a webhook — that's the channel URL. Documented the distinction in the vault so future-Paul doesn't repeat the mistake.
  - **Probe host pivoted.** Paul explicitly overrode the earlier recommendation of `aldcsuptdock1c01` (Nostromo on-prem): v1 probe host is **local dev → Azure for production**. Rationale: Paul wants to move ALDC off on-prem dependence going forward, full stop. Accepted the fate-sharing risk the earlier decision flagged.
  - Added a new Decisions Log entry superseding the on-prem recommendation, and recorded the required mitigations so the planning session addresses them rather than re-opening the decision.
- **decided:** `#observability-dev` (private) is the v1 dev alert channel with webhook in vault; `#observability` creation deferred to prod cutover; Slack app reused for both webhooks; probe host is Azure long-term, not on-prem, with explicit non-Azure dead-man switch as the mitigation.
- **next:** Paul opens a fresh session with the updated Planning Boot Prompt. All checklist items are resolved; planning session is fully unblocked.

### 2026-04-24 — Planning session: design approved (Opus, plan-mode)

- **did:**
  - Read tracker §F1–F3 in full plus all Required Context pages (eclipse_exp, aldc-naming-convention, deployment-groups, azure-environments, local-network, aldc-scripts, flight-check, connector-timeout-outage, powerbi-secret-refresh, mailjet, executive-snapshot-email, snowflake-data-share-refresh, connector, GP-PENDING-data-share-stability) and Steven's `query-cosmos-schedules.py` source.
  - Drafted full v1 design plan at `C:/Users/PaulRussell/.claude/plans/fancy-inventing-aho.md` covering all seven Boot Prompt questions: tool stack, Azure compute choice, env-parameterisation, alert topology, support-inbox router, three-week phasing, v2 agent-interface seam.
  - Paul approved the plan in full (auto-mode).
  - Wrote `entities/projects/observability-platform.md` and `concepts/architecture/observability-architecture.md` per lane.
- **decided:** see new Decisions Log entries below — every choice listed under *Approval scope* in the plan file is now ratified.
- **next:** Execution Phase Week 1. First implementation ticket is in the refreshed Execution Boot Prompt below: bootstrap `github.com/ALDC-io/observability` repo, ship `docker-compose.yml` + Plane 1 Uptime Kuma + first Plane 3 job (`check_eclipse_templates.py` re-homed from Steven's script). Exit criterion: first real alert lands in `#observability-dev` from a real production failure.

### 2026-04-24 — Week 1 bootstrap: repo skeleton + Plane 1 + first Plane 3 job (Sonnet, execution)

- **did:**
  - Plan-mode first: drafted `C:/Users/PaulRussell/.claude/plans/luminous-zooming-map.md` covering 21 files, 7-service docker-compose, cron sidecar decision (ofelia vs supercronic), Cosmos account discovery, obs-api stub scope, Uptime Kuma seed approach. Paul approved.
  - Built the full repo skeleton at `C:/Users/PaulRussell/repos/observability/`:
    - `docker-compose.yml` — 7 services: uptime-kuma, prometheus, pushgateway, grafana, obs-api, obs-jobs, cron (ofelia sidecar).
    - `config/` — `local.yaml` (6 public URLs, dry_run:true, onprem:false), `prod.yaml`, `test.yaml`, `qa.yaml`, `templates.yaml` (empty; Paul populates with known-critical/flaky templates).
    - `stack/` — `prometheus.yml` (pushgateway-only scrape for Week 1), `uptime-kuma/seed.json` (6 monitors + Slack notification; manual import), `grafana/datasources/prometheus.yml` (provisioning).
    - `jobs/lib/` — `alerter.py` (P1/P2/P3 severity, Slack Block Kit, OBS_DRY_RUN), `correlation.py` (UUID4 + footer), `labels.py` (ALDC naming-convention dict builder), `push.py` (Pushgateway helper).
    - `jobs/check_eclipse_templates.py` — re-homed from Steven's script. Preserved verbatim: `get_templates()`, `get_schedules()`, `process_template()`, `get_completed_time_string()`, stdout print block. Extended with four §F1 gaps: (a) `get_accounts()` queries Cosmos `account` container at runtime with graceful schema degradation, (b) `templates.yaml` critical/ignorable config loaded at startup, (c) Prom metrics pushed to Pushgateway + Slack via alerter, (d) correlation ID + UTC timestamps on every payload.
    - `jobs/Dockerfile` + `jobs/requirements.txt` (azure-cosmos, pytz, python-dotenv, prometheus-client, requests, pyyaml).
    - `obs-api/app.py` (FastAPI stub: `GET /` and `GET /heartbeat`) + `obs-api/Dockerfile`.
    - `.github/workflows/lint.yml` (ruff + mypy).
    - `.gitignore`, `.env.example`, `README.md` (quick-start + smoke-test procedure).
  - **Repo is NOT yet on GitHub** — Paul must `git init`, push to `github.com/ALDC-io/observability`, and run `docker compose up -d` to start the stack.
- **decided:**
  - **Cron sidecar = ofelia** (`mcuadros/ofelia:latest`). Mounts Docker socket (read-only). `obs-jobs` runs `tail -f /dev/null` to stay alive; ofelia execs into it on schedule. Ad-hoc: `docker exec obs-jobs python /app/check_eclipse_templates.py`.
  - **Uptime Kuma seeding = manual import**. `stack/uptime-kuma/seed.json` ships in repo; substitute webhook URL via `sed` before importing via Settings → Backup.
  - **obs-api stub only in Week 1** — `GET /` and `GET /heartbeat`. Full Prometheus + Snowflake wiring in Week 2.
  - **Cosmos account discovery** — `SELECT c.id, c.name FROM c WHERE c.status = 'active'`; falls back to no-filter query if zero results. No confirmed schema, graceful degradation.
- **next:** Week 2 — wire Prometheus scrape of `eclipse_exp /metrics`, import eclipse_exp Grafana dashboard, add `check_snowflake_tasks.py` + `check_pbi_refresh.py` + `check_data_share.py`, add `lib/snowflake_writer.py` → `OBSERVABILITY.JOB_RUNS`, wire obs-api routes to Prometheus + Snowflake.

**Prerequisite for smoke-test (Paul):**
1. `git init && git remote add origin git@github.com:ALDC-io/observability.git && git push -u origin main` (or Paul creates via GitHub UI first).
2. `cp .env.example .env` → fill in Cosmos + Slack vars from vault.
3. `docker compose up -d`
4. Import `stack/uptime-kuma/seed.json` into Uptime Kuma UI after substituting the webhook URL.
5. `docker exec obs-jobs python /app/check_eclipse_templates.py --debug --full` → verify stdout + Pushgateway metrics.
6. Set `OBS_DRY_RUN=false` → rerun → confirm real alert in `#observability-dev`.

### 2026-04-25 — Week 1 alert system: iterative refinement session (Sonnet, execution)

**Exit criterion met:** ✅ Real alerts landing in `#observability-dev` with full context. Stack running locally at `C:/Users/PaulRussell/repos/observability/`.

- **did:**
  - Smoke-tested the stack end-to-end against real production Cosmos data. Discovered 5 real failing templates (Microsoft Ads, Viant Snowflake, Meta Facebook Ads Windsor, 2× Amazon ASIN GEP). All fired correctly with `OBS_DRY_RUN=false`.
  - Discovered Cosmos `account` container schema: no `status` field; documents use `full_name` + `short_code` (not `name`). Fixed `get_accounts()` to use `full_name`/`short_code` — account names now display as "Global Ecom Partners", "Fusion92", etc.
  - Confirmed Eclipse template URL format: `https://eclipse.aldc.io/account/template/{template_id}/edit/`.
  - Discovered Eclipse error format: stored in schedule `comment` field (e.g. `"Extraction/Connector error: [{'code': 'QuotaExceeded', ...}];"`). Wrote `_clean_error()` parser.
  - Discovered partition dates stored in `option.filter` array on schedule documents (two formats: `filter_date` for Amazon SC, `date` for Amazon Ads).
  - Iteratively redesigned the alert message format through 4+ rounds of feedback from Paul:
    - Round 1: plain-English severity ("Action needed today"), account names, Eclipse link.
    - Round 2: client impact statement ("GEP — Amazon Sales & Traffic data for Apr 18–24 is not updating"), partition dates, error text, suggested fix.
    - Round 3: data freshness / staleness report ("Most recent complete: Mar 1 · 54 days stale ⚠️"), agent/hostname.
    - Round 4: alert throttling (`lib/state.py`), recovery notifications, root-cause grouping, `enabled: false` in templates.yaml.
    - Round 5 (final): auto-escalation P2→P1 after 24h, recurrence counter, trend indicator, blast radius detection, estimated recovery time.
  - Wrote `lib/state.py` — alert state persistence with `active`/`history` structure, P2 throttle (default 1h), P2→P1 auto-escalation (default 24h), trend tracking, incident count, recovery detection.
  - Updated `lib/alerter.py` — plain-English severity labels, cleaner message structure, `send_recovery()` function.
  - Extended `jobs/check_eclipse_templates.py` significantly beyond original §F1 scope:
    - `_clean_error()`, `_extract_partition_date()`, `extract_failure_context()` — rich schedule analysis.
    - `_compute_staleness()` — data freshness from completed partition dates.
    - `_error_fingerprint()`, `_group_alert_candidates()`, `_build_grouped_message()` — root-cause grouping.
    - `_estimated_recovery()` — per-error-type recovery time estimates.
    - `_blast_radius_note()` — multi-template same-agent failure detection.
    - `build_alert_message()` — full structured message with all fields.
    - Two-phase alert loop: Phase 1 collects candidates with state check, Phase 2 groups and sends.
  - Confirmed stack operational: `docker compose ps` showing all 7 containers healthy, metrics flowing to Pushgateway, alerts posting to Slack correctly.
- **decided:**
  - **Cosmos account schema confirmed**: use `full_name`/`short_code` fields. No `status` or `name` fields.
  - **Eclipse URL format confirmed**: `/account/template/{template_id}/edit/` (not `/accounts/{id}/templates/{id}`).
  - **Eclipse error field confirmed**: `comment` field on schedule document.
  - **Partition date field confirmed**: `option.filter` array with `filter_date` (Amazon SC) or `date` (Amazon Ads) fields.
  - **`lib/state.py`** is the durable alert state mechanism for all Plane 3 checks going forward. Week 2 checks reuse it.
  - **Inactive templates handled via `enabled: false`** in `config/templates.yaml`. Paul to add Fusion92 Microsoft Ads + Viant as first entries.
  - **Real failures observed in prod**: Microsoft Ads expired Azure AD secret (AADSTS7000222), Viant Snowflake IP block, Meta Facebook Ads 54 days stale (400 error), Amazon ASIN quota exceeded (auto-recovers ~midnight UTC).
- **next:** Week 2 (new session). See refreshed Execution Boot Prompt below.

**Still pending — Paul action required:**
1. `git init` + push to `github.com/ALDC-io/observability`.
2. Import Uptime Kuma seed.json via UI (Settings → Backup → Import; substitute webhook URL first with `sed`).
3. Add inactive Fusion92 templates to `config/templates.yaml` with `enabled: false` (Microsoft Ads Campaign, Viant).

## Decisions Log

Durable choices that affect future sessions. One bullet per decision; date it.

- **2026-04-24** — Workstream is distributed-workflow-managed (this tracker). Reason: touches too many owned paths and too many open architectural questions to complete in a single session. Plan-mode-first until a design exists.
- **2026-04-24** — v1 scope is Production only. Config files must be env-parametric so Test / QA can plug in later, but no non-prod monitors land in v1. Reason: avoids design-by-committee on subscription inventory during bootstrap.
- **2026-04-24** — Reference implementation for app-level health is [[eclipse_exp]] (`/ping`, `/health`, `/metrics`, structlog, `ops/grafana-dashboard.json`, Slack alerts). Other services are brought up to that bar rather than inventing a new pattern.
- **2026-04-24** — **Dedicated `observability` repo** under `github.com/ALDC-io` (Paul confirmed). Do NOT absorb into [[aldc-scripts]]. Rationale: clean ownership, CI/CD, room to grow, and avoids mixing new critical infra with an unverified legacy grab-bag.
- **2026-04-24** — **Self-host** the Uptime Kuma + Prometheus + Grafana stack for now (Paul confirmed). Grafana Cloud stays filed as fallback if self-host maintenance becomes painful; not a v1 concern.
- **2026-04-24** — **Support inbox co-owner is Lori** (Lori Beck, `lori.beck@aldc.io`). "Laura" in the brainstorm was a typo; no Laura at ALDC. Router map: request → Paul OR Lori.
- **2026-04-24** — **Support Slack channel: provision a new one for v1.** A channel may already exist (brainstorm said ask Marshall), but Paul has greenlit creating one for now rather than blocking on that answer. Channel name TBD in planning session; route `send_slack.sh` webhook there.
- **2026-04-24** — **Steven's failing-templates script will be delivered by Paul** (he has a call with Steven imminently). Not missing, just not in-hand yet. Planning session should treat its arrival as a hand-off artifact to review, not a blocker.
- **2026-04-24** — **v2 scope acknowledged: agent-facing query interface.** v1 must not architect itself in a way that precludes v2 adding a read API / MCP server / CLI that Claude Code agents can call during support triage. Concrete design deferred; shape-of-v1 constraints captured in *Future Scope — v2 Agent Interface* below.
- **2026-04-24** — **`check_eclipse_templates.py` seeds from** `ALDC-io/projects/query_template_and_schedule_status/query-cosmos-schedules.py`. The two Cosmos queries (`get_templates`, `get_schedules`) and the status-count state machine (`process_template`) are preserved verbatim; the wrapper is re-homed into the new `observability` repo. Four v1 gaps (hard-coded account whitelist, missing critical/ignorable config, stdout-only output, no correlation IDs) are in-scope for v1. UTC+local display preserved.
- **2026-04-24** — **v1 Slack channel: `#observability`** (Paul to create). Single firehose for v1. v2 will categorise via additional channels (`#obs-snowflake`, `#obs-eclipse`, `#obs-gep`, `#obs-fusion92`, etc.) driven by [[aldc-naming-convention]] labels on each metric — the routing table maps `(service_type, client)` tuples to webhooks. Free once the labels are already enforced per the v2 agent-interface shape constraint.
- **2026-04-24** — ~~**Probe host (v1 recommendation): `aldcsuptdock1c01`**~~ **SUPERSEDED 2026-04-24 — see next entry.** Original rationale retained for context: existing support Docker VM on Nostromo, zero provisioning, correct failure isolation (independent of Azure + prod VMs Sulaco/Infinity), direct WAN via NPM so Tailscale outages don't blind the monitor. Azure Container App was rejected because fate-shared with the apps being monitored.
- **2026-04-24** — **Probe host (REVISED): local dev → Azure for production.** Paul override (explicit): ALDC is moving away from on-prem dependence going forward; the new observability platform must not reinforce it. Supersedes the `aldcsuptdock1c01` recommendation. The earlier fate-sharing concern (monitor sitting inside the Azure sub it watches) is *acknowledged and accepted* on the condition that v1 ships three mitigations the planning session must design in: (1) **external non-Azure dead-man switch** (e.g. UptimeRobot free tier or a `cron` heartbeat on Server4) that pages if the Azure-hosted monitor stops checking in; (2) **Azure region / subscription separation** where feasible — the monitor should not live in the exact same resource group / region as the biggest thing it watches; (3) **on-prem LAN probes** (Proxmox hosts, Docker VMs, TrueNAS, NPM) reach their targets via Tailscale from the Azure host, which means the monitor cannot page on Tailscale outages alone — the dead-man switch above covers that too. Specific Azure compute choice (Container App vs Container Instance vs Function App + VM) is a planning-session decision; this entry locks the host *location*, not the *service*.
- **2026-04-24** — **Development is local-first, host-portable.** Single `docker-compose.yml` runs identically on Paul's laptop and on the prod probe host. All environment-specific values in `.env` + `config/<env>.yaml`. Local dev uses `#observability-dev` Slack channel (or a `dry_run` config flag); prod alerts go to `#observability`. `enable_onprem_probes: false` locally to skip LAN-only targets without depending on Tailscale. Cutover is `git pull` + swap `.env` + flip flag + `docker compose up -d` — ~30 minutes mechanical. Prometheus TSDB fresh-starts at cutover (no volume migration). Full procedure in *Development Workflow — local-first, host-portable* section.
- **2026-04-24** — **Slack channels created / deferred + webhook vaulted.** `#observability-dev` is **private, created**, and its webhook is stored in `vault/credentials.md` under the new *Observability* section. `#observability` (prod firehose) is **deferred** until v1 prod cutover — Paul will create it as public at that point. Both webhooks are produced by the same Slack app "ALDC Observability" (https://api.slack.com/apps) — add a second webhook to the same app at cutover rather than registering a new app. Channel ID for `#observability-dev` is `C0AV0PRJ4JF`. If `#observability-dev` stays private past v1 ship, Paul explicitly invites Lori / Steven / Marshall when they need visibility.
- **2026-04-24 (planning approval, ratified)** — **Tool stack v1 = three-plane self-host + read API.** Plane 1: Uptime Kuma (`louislam/uptime-kuma:1`). Plane 2: Prometheus (`prom/prometheus:v2`) + Pushgateway (`prom/pushgateway:v1`) + Grafana (`grafana/grafana:11`). Plane 3: single `obs-jobs` Python image with multiple entrypoints (`check_eclipse_templates.py`, `check_snowflake_tasks.py`, `check_pbi_refresh.py`, `check_data_share.py`) driven by a `cron` sidecar. **Plus `obs-api`** (FastAPI, `:8090`) — thin read-only HTTP wrapper over Prometheus + the new Snowflake `OBSERVABILITY.JOB_RUNS` table. obs-api is the v2 agent-interface seam, landed in v1 because retrofitting it later is materially more expensive than building it now.
- **2026-04-24 (planning approval, ratified)** — **Azure compute = Standard B2ms Linux VM running `docker-compose.yml` + dedicated Function App for the support-inbox webhook.** Container App rejected (single-container preferred; breaks "single docker-compose, host-portable" contract; same control plane as eclipse_exp). Container Instance rejected (file-share-only persistent volumes; same fate-sharing). VM in **Quality 1 sub, East US 2** — distinct subscription AND distinct region from `aldcprodrsgp1c` Canada Central. Function App `aldcprodfnapsupport1c01` lives in Production 2 (intentional — webhook traffic is bursty, serverless is the right fit, and the Function is independent of the probe host). Estimated cost ≈ $45–55/mo all-in.
- **2026-04-24 (planning approval, ratified)** — **Three fate-sharing mitigations, concretised:** (1) UptimeRobot free-tier dead-man switch probes `https://obs.aldc.io/heartbeat` at 60s; VM cron writes a heartbeat file every 30s; endpoint returns 503 if older than 90s; UptimeRobot pages a *separate* webhook on the same Slack app. Independent: different cloud, account, and network path. (2) VM region+subscription separation as above. (3) Tailscale daemon on the VM joins the existing tailnet for LAN probes. **Asymmetry:** the dead-man switch does NOT depend on Tailscale, so a Tailscale outage is independently detectable and pages as P1.
- **2026-04-24 (planning approval, ratified)** — **Env-parameterisation = single `docker-compose.yml` + `config/<env>.yaml` + `.env` for secrets.** `OBS_ENV={local|prod}` selects which YAML the containers load. Secrets in prod come from Azure Key Vault via VM-managed-identity into a tmpfs `.env`; locally they sit in plain `.env` (gitignored). `local.yaml` and `prod.yaml` ship complete in v1; `test.yaml` and `qa.yaml` ship stubbed (`enable: false`).
- **2026-04-24 (planning approval, ratified)** — **Alert topology = P1 / P2 / P3 severities + correlation IDs end-to-end + `OBS_DRY_RUN` flag.** P1 page-now (Slack + `@here`); P2 within-day (Slack only, throttled to 1 per `(check_name, resource_name)` per hour); P3 weekly digest (Mon 09:00 PT aggregate). Single Slack app **"ALDC Observability"** holds all webhooks; no second app. `OBS_DRY_RUN=true` short-circuits Slack POST but keeps Snowflake writes + Pushgateway pushes happening (full local rehearsal of every alert path).
- **2026-04-24 (planning approval, ratified)** — **Correlation ID propagation:** every probe + job run + alert generates one UUID4. Carried as `corr_id` Prom label, `correlation_id` Snowflake column, monospace footer line in Slack messages, `corr-<UUID>` Jira label. `obs-api` `/search?corr_id=…` walks the cross-system timeline and is the v1 precursor to v2's `observability.trace(correlation_id)` MCP tool.
- **2026-04-24 (planning approval, ratified)** — **Support-inbox router = Mailjet inbound parse → `aldcprodfnapsupport1c01` Azure Function → Jira REST.** IMAP poll rejected (need M365 service account; stuck sessions hang silently; cost overhead). Function `router.classify(email) -> Classification` is the v2 swap point — v1 keyword map (Paul: deploy/snowflake/pbi/warehouse/eclipse/connector/prefect/share/refresh/etl/task chain; Lori: invoice/billing/credentials/access/onboard/account/user/license/permission/vendor; default Paul). v2 swaps the function body for an MCP-backed agent classifier returning the same `Classification` shape. After Jira ticket creation, one P2 Slack heads-up line lands in the alert channel.
- **2026-04-24 (planning approval, ratified)** — **Phasing: three weeks, dependency-ordered.** Week 1: local stack + Plane 1 Uptime Kuma + first Plane 3 job (`check_eclipse_templates.py`). Week 2: Plane 2 Prom/Grafana + remaining Plane 3 jobs + `obs-api` + `OBSERVABILITY.JOB_RUNS` table. Week 3: Azure VM cutover + UptimeRobot dead-man switch + Mailjet→Jira Function + `#observability` channel creation. Out of v1: LLM email classification, Loki, distributed tracing wire-up, non-prod monitors, MCP server.
- **2026-04-24 (planning approval, ratified)** — **`OBSERVABILITY.JOB_RUNS` schema is committed for v1's lifetime.** Adding columns is fine; renaming is breaking. Schema captured in `concepts/architecture/observability-architecture.md` § Schemas. ≥365-day retention via Time Travel + monthly partition. Hosted in a Snowflake DB to be created Week 2 (Test or QA env until a dedicated obs DB is provisioned).
- **2026-04-24 (planning approval, ratified)** — **Plane 3 `check_eclipse_templates.py` re-home pattern.** Preserve verbatim: the two Cosmos queries (`get_templates`, `get_schedules`) and the `process_template` status-count state machine. Extend with the four §F1 gaps: drop hard-coded 5-account whitelist (source from Cosmos `account` container at runtime), add `templates.yaml` critical/ignorable config (resolves Steven's lines 37–42 TODO), add Prom push + Slack output via `obs-alerter`, add correlation IDs + UTC. Original script stays in-place at `C:/Users/PaulRussell/repos/projects/query_template_and_schedule_status/` as reference until v1 ships.
- **2026-04-25 (execution, confirmed)** — **Week 1 exit criterion met.** 5 real Slack alerts landed in `#observability-dev` from real production Eclipse template failures (see smoke-test details below). `OBS_DRY_RUN=true` suppressed correctly; `OBS_DRY_RUN=false` posted live. Cosmos `account` container does NOT have a `status` field — the no-filter fallback query returned 12 accounts (vs. Steven's hard-coded 5). Stack stays running locally with `OBS_DRY_RUN=true` until Week 2.
- **2026-04-25 (execution, confirmed)** — **Cosmos `account` container schema:** no `status` field; `SELECT c.id, c.name FROM c` returns 12 accounts including `8425e311` (Kit and Ace), `5d556742` (Dish Duer), `0fc00e34` (Fusion92), `da8904db` (GEP), `8b28d977` (ALDC Library), and 7 others. Accounts `221eb67e` and `17fc16d7` appear to be library/dev accounts with templates that have no recent schedules — they show up as "no completions / unknown" noise. Consider adding those to `templates.yaml` as ignorable with a high threshold, or filtering to known-active accounts only.
- **2026-04-25 (execution, observed)** — **Real failing templates as of 2026-04-25:** `Microsoft Ads - Campaign` (Fusion92, 32/32 failures), `Viant - Reach and Frequency - Fusion Snowflake` (Fusion92, 63/63 failures), `Meta Facebook Ads -- Windsor` (Fusion92, 2/3 failures), `Amazon Ads - Sponsored Brands - Campaign Report` (GEP, 2/56), `Amazon Seller Central ASIN CHILD` (GEP, 20/130 + 14/94 on CA variant). These are ongoing production issues the alerts now surface automatically.

## Research Findings (bootstrap session, 2026-04-24)

Captured here so subsequent plan-mode sessions inherit the context without re-running the research.

### F1. Steven's "failing templates" script — LOCATED

**Repo:** `github.com/ALDC-io/projects` (already cloned at `C:/Users/PaulRussell/repos/projects/`)
**Path:** `projects/query_template_and_schedule_status/`
**Files:**
- `query-cosmos-schedules.py` (~375 lines, Python 3)
- `.env.template` — `DATABASE_ID`, `PROD_COSMOS_HOST/KEY`, `TEST_COSMOS_HOST/KEY`
- `requirements.txt` — `azure-cosmos`, `pytz`, `python-dotenv`

**What it does:** queries Eclipse core CosmosDB `work_template` + `schedule` containers, cross-references schedules to templates over a configurable window (default 1 day), and reports per-template status. Standard operator invocation is `python query-cosmos-schedules.py --full --failed`, which lists every template whose latest schedule is `failed` or has never completed. Two Cosmos queries per run — cheap.

**CLI surface:**
- `--env test|prod` (default prod)
- `--account <id>` (filters to one client; hard-coded id whitelist — see gaps)
- `--template <id>`
- `--days <float>` (default 1)
- `--full`, `--failed`, `--debug`

**Output per template:** latest status, count since completion, last completion time (America/Vancouver), per-status counts (`init` / `complete` / `failed` / `zombie`). Prints to stdout grouped by account.

**Exit codes:** `0` all good · `1` failures found · `400` Cosmos error · `500` other exception. Script-friendly — can pipe to Slack/Prometheus without parsing stdout.

**Gaps the v1 generalisation (`check_eclipse_templates.py`) must fix:**
1. **Hard-coded 5-account whitelist** at `query-cosmos-schedules.py:98-104` (Kit and Ace `8425e311`, Dish Duer `5d556742`, Fusion92 `0fc00e34`, GEP `da8904db`, ALDC Library `8b28d977`). Every other active client is silently dropped. v1 must source the account list from Cosmos (`account` container) at runtime, not hard-code.
2. **No critical-vs-ignorable template config** — Steven's own TODO at lines 37-42. A chronically-flaky template drowns the signal. v1 needs a YAML config listing critical templates (alert immediately on single failure) and ignorable/flaky ones (alert only after N consecutive failures).
3. **stdout-only output** — suitable for operator-run ad-hoc checks; v1 needs the same logic to also emit Prometheus metrics (via `prometheus_client` pushgateway) and Slack messages (via `send_slack.sh`) so it can run unattended.
4. **No correlation ID** — per the v2 agent-interface shape constraint (§ Future Scope), every alert needs one.
5. **Script is America/Vancouver-local for timestamp display** — fine for humans, but v1's durable store should keep UTC and let the viewer render local. Preserve Steven's display path, add UTC to the metric/alert payload.

**What to preserve verbatim:** the Cosmos query logic (the two queries at `get_templates` / `get_schedules`) and the status-counts state machine in `process_template`. Those are the load-bearing correctness work; the wrapper around them is what v1 re-homes.

**Status:** Absorbed into plan. The planning session uses this as the seed for `observability/jobs/check_eclipse_templates.py`, extends it with the four gaps above, and keeps the original script in-place as a reference implementation until v1's version ships.

### F2. Full inventory of things needing observability (what v1 must probe)

**Applications (HTTP health probes + error rate):**

| Resource | Home | Today's monitoring | v1 probe |
|---|---|---|---|
| eclipse | Azure Web App `aldcprodwbapportal1c01`, `https://eclipse.aldc.io` | None | Add `/health`; probe 60s |
| eclipse_exp | Container App `eclipse-exp-api`, `https://eclipse-exp.aldc.io` | `/ping`, `/health`, `/metrics` (Prom), Grafana dashboard, Slack alerts | Import Prom scrape + dashboard |
| core_api | Function App `aldcprodfnapcore1c01` | None documented | Add `/health`; probe 60s |
| flight-check (repo) | Azure Web App `https://dax.fusion92.eclipse.aldc.io` | None | Probe iframe root + 4 backend deps |
| workflows / DAX API | Function App `F92_workflow_app` | None | Probe `/api/dax/*` heartbeat |
| custom-fusion-92-audience-api (DIOS) | On-prem `https://audience-fusion92-app.aldc-ca-w1.com` (Gunicorn, 2 workers, 60 GB RAM) | None | Probe `/` + memory gauge |

**Data pipeline (job health + data freshness):**

| Resource | Failure mode | v1 check |
|---|---|---|
| Eclipse templates (via connector) | Template runs fail silently; downstream tables go stale | Reimplement Steven's script if it turns up; otherwise query Eclipse/Cosmos for failed template tasks over N hours |
| connector (6 Docker VMs) | Agent container down, Portainer unreachable | Prom node-exporter + Docker daemon health on each VM |
| Prefect (QA sub) | Flow failures, scheduler down | Prefect's own API → Slack webhook |
| Snowflake tasks | Task chain root fails, downstream SKIPPED | Query `INFORMATION_SCHEMA.TASK_HISTORY` on schedule; pattern already in [[flight-check]] |
| Power BI refresh | Semantic model refresh fails (common: credential expiry per [[powerbi-secret-refresh]]) | PBI REST `/datasets/{id}/refreshes` per workspace |
| Prod→test data share (GP-207) | Objects silently drop from share ([[GP-PENDING-data-share-stability]]) | Periodic `SELECT COUNT(*)` from every shared object ref |
| connector `/work/pick` queue | Queue depth spikes under timeout ([[connector-timeout-outage]]) | Azure Queue depth alert |

**Infrastructure (Proxmox + Docker VMs + on-prem):**

| Resource | IP / host | v1 check |
|---|---|---|
| Nostromo (Proxmox R730) | 192.168.30.80:8006 / iDRAC 192.168.30.81 | ICMP + iDRAC scrape + ZFS pool state |
| Sulaco (Proxmox R730) | 192.168.30.82:8006 / iDRAC 192.168.30.83 | Same |
| Patna (Proxmox R430) | 192.168.30.84:8006 / iDRAC 192.168.30.85 | Same |
| Auriga (Proxmox R730xd + TrueNAS) | 192.168.30.86:8006 / iDRAC 192.168.30.87 | Same + NFS/CIFS export health |
| Infinity (Proxmox R730, Coquitlam) | 192.168.30.80:8006 / iDRAC 192.168.22.157 | Same |
| `aldcproddock1c01` (Sulaco VM, 52c/224GB) | 192.168.35.70 | node-exporter + cAdvisor |
| `aldcproddock1c03` (Marathon VM, 32c/128GB) | 192.168.22.70 | Same |
| `aldctestdock1c01` (Auriga VM, 16c/96GB) | 192.168.36.70 | Same |
| `aldcqadock1c01` (Auriga VM, 16c/64GB) | 192.168.36.71 | Same |
| `aldcsuptdock1c01` (Nostromo VM, 16c/128GB) | 192.168.31.20 | Same |
| `aldcproddock1c05` (Infinity VM, 52c/224GB) | — | Same |
| TrueNAS / Covenant (RAIDZ2×6, 30 TiB) | `covenant.prod.site3.aldc`, 66.183.0.251:32322 | Disk health, CIFS reconnect detection |
| Nginx Proxy Manager | 192.168.31.20:81 | Proxy-level `/health` scrape |
| Tailscale kookiet router | 100.70.65.48 | External reachability probe from a non-Tailscale path |
| Nextcloud (VM 13006 Scarif) | — | Sync health + disk |
| Server4 cron host | — | node-exporter + cron-heartbeat (dead-man switch) |
| Auriga VM 11099 (exec snapshot cron) | — | Heartbeat from [[executive-snapshot-email]] |

**Azure resources (per subscription, Prod first):**

- Production 2 (`aldcprodrsgp1c`, sub `6389f755-…`): core_api Function App, eclipse_exp Web App, legacy Eclipse Web App, Cosmos `aldcprodcsdb1c01`, Storage `aldcprodstaccore1c01` + `aldcprodstacqueue1c01`, F92 Function App `aldcprodfnapf921c01`.
- Quality 1 (`aldcqarsgp1c`, sub `efe036d8-…`): Prefect workloads.
- Test 1 (`aldctestrsgp1c`, sub `6969113c-…`): mirror of Prod for testing.
- Dev DG1–4.

v1 focus: Prod subscription cost alerts (Azure Cost Management budgets, native), Application Insights pulled into Grafana via the Azure Monitor data source (read-only, no agent), queue depth on `aldcprodstacqueue1c01`.

**Support inbox:**

- Email: `support@aldc.io` (confirmed convention; exact routing unconfirmed).
- Slack channel: candidate name `#aldc-support`. **Unknown if a channel already exists** — the brainstorm explicitly says "check with Marshall." Surface this as a blocker for the planning session.
- Jira routing target: Paul or Lori, decided by keyword heuristic in v1.

**Existing monitoring (what we already have, must not duplicate):**

- eclipse_exp: full Prom + Grafana + Slack alerting — reference impl.
- Application Insights: linked to all Azure Function Apps; mostly unused for alerting.
- aldc-scripts `cost-monitoring/`: weekly Slack cost report, Server4, **status likely dead** per [[aldc-scripts]]. Paul cannot see `#the-olds`.
- PostHog in flight-check (client-side, product analytics — not operational).

### F3. Preliminary recommendation — **lightweight, three-plane stack**

To be re-examined and either ratified or replaced during the planning session.

**Plane 1 — Synthetic + uptime (apps + web endpoints):**
- **Uptime Kuma** self-hosted on an on-prem Docker VM. Single container, free, Slack webhook built-in, covers HTTP / TCP / ping / keyword / DNS. Runs where it does NOT depend on Tailscale so it can still page when Tailscale is down. Probes the 6 apps above at 60s cadence.

**Plane 2 — Infra + app metrics:**
- **Prometheus** (single container, co-located with Uptime Kuma) scrapes:
  - `node-exporter` on every Proxmox host + every Docker VM (CPU / mem / disk / net).
  - `cAdvisor` on every Docker VM (container-level).
  - `/metrics` on every ALDC app that exposes it (eclipse_exp already does; others get it incrementally as follow-up tickets).
  - Azure Monitor via the Prometheus Azure data source OR pulled through Grafana's Azure Monitor plugin.
- **Grafana** (single container, same host) imports eclipse_exp's `ops/grafana-dashboard.json` as one dashboard and adds a second "ALDC Prod Overview" dashboard stitching all planes together.

**Plane 3 — Job / data-pipeline health:**
- Start with generalising Steven's failing-templates script **once located** (or writing a replacement if not). Single Python CLI `observability/jobs/check_*.py`, one check per job family:
  - `check_snowflake_tasks.py` — queries `INFORMATION_SCHEMA.TASK_HISTORY`, alerts on FAILED/SKIPPED.
  - `check_pbi_refresh.py` — PBI REST, alerts on failed refresh + surfaces credential-expiry countdown from [[powerbi-secret-refresh]].
  - `check_eclipse_templates.py` — Eclipse API or Cosmos schema container, alerts on template-level failures.
  - `check_data_share.py` — `SELECT COUNT(*)` against every shared object, alerts on drops ([[GP-PENDING-data-share-stability]]).
  - Emits to Prometheus via `prometheus_client` push gateway AND to Slack via `send_slack.sh` pattern.
- Scheduled via **Prefect** (since we're migrating to it anyway) OR a simple systemd timer on the same host as Prometheus (v1 may use the simpler option and move to Prefect in v2).

**Support inbox:**
- Mailjet inbound parse route → tiny Azure Function `aldcprodfnapsupport1c01` → Jira REST (`POST /rest/api/3/issue`). Assignee picked by a keyword map (`deploy|snowflake|pbi|warehouse` → Paul, `invoice|credentials|access|onboard` → Lori). Round-robin / LLM classifier deferred to v2.
- Slack channel: **confirm with Marshall first** (per brainstorm). If none exists, create `#aldc-support` and point the Slack webhook there; otherwise reuse.

**Repo shape:**
- New dedicated repo `observability` under `github.com/ALDC-io`. Preferred over absorbing into `aldc-scripts` because:
  - `aldc-scripts` is "likely legacy" per its own wiki page; mixing new critical infra with an unverified legacy grab-bag is risky.
  - Clear ownership + CI/CD + room to grow + a natural home for dashboards JSON and monitor configs.
- Layout sketch (plan-mode refines):
  ```
  observability/
  ├── README.md
  ├── config/
  │   ├── prod.yaml          # hosts, urls, Azure subs, Snowflake creds-pointer
  │   ├── test.yaml          # stub, not active in v1
  │   └── qa.yaml            # stub, not active in v1
  ├── stack/
  │   ├── docker-compose.yml # Uptime Kuma + Prometheus + Grafana
  │   ├── prometheus.yml     # scrape config
  │   └── grafana/
  │       ├── dashboards/
  │       └── datasources/
  ├── jobs/                  # Plane 3 Python CLIs
  │   ├── check_snowflake_tasks.py
  │   ├── check_pbi_refresh.py
  │   ├── check_eclipse_templates.py
  │   └── check_data_share.py
  ├── support-inbox/         # Azure Function source (Python)
  │   ├── function_app.py
  │   └── router.py          # keyword → assignee map
  └── infra/
      └── ansible/           # or bash: provisioning node-exporter on VMs
  ```

**Rejected alternatives (to validate in planning):**

- **Datadog / New Relic SaaS**: cost is disproportionate at ALDC scale; ingesting internal data paths into a third-party also creates an ingress story we don't want to own for clients.
- **Grafana Cloud free tier**: viable, but ties ingest limits to a third party's pricing evolution. Keep as fallback if self-hosting is rejected.
- **Custom Next.js dashboard in eclipse_exp**: only worthwhile once eclipse_exp is the canonical control plane. Today it's still being stood up — leaning on it now couples v1 to another project's timeline.
- **Azure Monitor / Alerts alone**: Azure-centric; wouldn't cover on-prem, Snowflake, PBI, Mailjet. Role is "one of the planes," not the whole platform.

## Development Workflow — local-first, host-portable

**Constraint** (2026-04-24, Paul): the entire stack must be runnable from Paul's dev laptop while the platform is being built, and migratable to the chosen **Azure** prod host (specific Azure compute service TBD in planning — Container App / Container Instance / Function App + VM) without rewrites. Note: earlier drafts of this tracker targeted `aldcsuptdock1c01` on Nostromo; that target was superseded on 2026-04-24 in favour of Azure — see Decisions Log.

**How v1 honours this:**

1. **Single `docker-compose.yml`** at the repo root brings up Uptime Kuma + Prometheus + Grafana + the Plane 3 job containers + a `cron` sidecar for scheduled jobs. The same file works on a laptop and on a Linux probe host. If a design step relies on a path that only works on the prod host, that is a smell.
2. **All environment-specific values in `.env`** alongside `docker-compose.yml`. Ship `.env.example`, `.env.local.example`, `.env.prod.example`. Swap the file, not the code.
3. **`enable_onprem_probes` flag in config** — `false` locally (skips Proxmox iDRAC `192.168.30.x`, Docker-VM `node-exporter` scrapes, NPM, TrueNAS Covenant), `true` on the prod probe host. Local dev exercises everything that works against public endpoints + cloud APIs (apps, Snowflake, PBI, Azure Monitor) without depending on Tailscale.
4. **Separate dev Slack channel** — `#observability-dev` for development; `#observability` only ever receives prod alerts. Webhook URL is the only thing that differs. Alternative is a `dry_run: true` config flag that logs "would alert" instead of posting; either is acceptable.
5. **Fresh-start TSDB + Grafana state at cutover** — do NOT migrate local Prometheus history to prod. v1 retention is short (≥30 days target per agent-interface constraint), a clean baseline post-move is easier to reason about than rsync'ing volumes.
6. **Secrets**: local `.env` on disk → Azure Key Vault or Dashlane in prod. Same env-var schema, different source.

**Cutover procedure (planning session refines, but the shape is fixed):**

1. Deploy the stack to the chosen Azure compute service (planning session picks Container App vs Container Instance vs VM + Function App). The `docker-compose.yml` contract does not change; the host does.
2. `git clone github.com/ALDC-io/observability` (or push image to the chosen Azure Container Registry).
3. Pull `.env.prod` from Azure Key Vault, inject into the container runtime.
4. Flip `enable_onprem_probes: true`, populate the LAN target lists (reachable from the Azure host via Tailscale — planning session confirms the Tailscale-in-Azure pattern).
5. `docker compose up -d` (or the Azure equivalent).
6. Verify probe heartbeat lands in `#observability` **AND** the non-Azure dead-man switch (UptimeRobot / Server4 cron) sees the host — both must be green before the local dev stack is torn down.
7. Disable the local dev stack (`docker compose down` on the laptop) so you're not double-paging.

Cutover should be a ~30-minute mechanical step. If the planning session designs something where cutover is harder than that, push back.

**What this implies for the planning session:**

- The repo layout sketch in §F3 stays — `stack/docker-compose.yml`, `config/{prod,test,qa}.yaml` — but make Plane 3 jobs containerised images so they're not laptop-Python-version-sensitive.
- All probe URLs, target hostnames, account IDs, retention windows, alert thresholds belong in `config/<env>.yaml`. None hard-coded.
- `prod.yaml` and `local.yaml` should both exist in the repo from day one — `local.yaml` is `prod.yaml` minus the LAN-only targets and minus the on-prem heartbeats.

## Future Scope — v2 Agent Interface

**Intent** (2026-04-24, from Paul): make the observability platform first-class for autonomous agents, not only for humans. Example use case:

> A support email arrives from a GEP stakeholder: "our Amazon UK data hasn't updated since Monday." A Claude Code agent (running under the support-inbox bridge, or in Paul's session) queries the observability platform to pull: current state of every Amazon UK-related connector run + Snowflake task + data-share object + PBI refresh for the last 7 days. The agent produces a **pre-triage report** — "Connector `AMZN_UK_ORDERS` has been failing since Monday 06:00 UTC with `401 Unauthorized`; credential `amazon-uk-refresh-token` expired per [[powerbi-secret-refresh]] pattern" — and either drafts a Jira ticket with that triage pre-filled or posts the summary to Slack for human review.

**This is explicitly NOT a v1 deliverable.** It is captured here so v1 architectural choices do not foreclose it. v1 should be shaped such that adding the agent interface in v2 is additive, not a rewrite.

**Shape-of-v1 constraints to preserve the v2 option:**

1. **Persist, don't just alert.** Every probe result and job-health check result writes to a durable store (Prometheus's TSDB + the Python jobs' Snowflake/Postgres result table). Slack notifications are a view onto that store, not the source of truth. Without this, an agent has nothing to query; it would have to re-run the checks live.
2. **Label everything with the ALDC naming convention.** Metrics carry `client`, `environment`, `service`, `component`, `resource_name` labels so queries like "everything Amazon UK-related in Prod for GEP over the last 7 days" decompose to a clean PromQL/SQL filter. Use [[aldc-naming-convention]] tokens verbatim as label values.
3. **Keep a thin, stable read surface.** Either Grafana's HTTP API or a purpose-built read-only FastAPI endpoint in front of Prometheus + the Snowflake/Postgres jobs table. No internal Prometheus-only conventions leak to callers. The schema this surface exposes is what v2's MCP server / CLI wraps.
4. **Every alert has a correlation ID.** Matches eclipse_exp's existing `asgi-correlation-id` pattern. Lets an agent walk backwards from a Jira ticket ID or a Slack message link to the underlying probe/job event that triggered it.
5. **Retention ≥ 30 days** for probe + job-health history. Anything shorter and the agent can't answer the "has this been failing intermittently for a week?" question.

**Explicit v2 deliverables (for future planning, NOT v1):**

- **MCP server** exposing tools like `observability.query_service_health(service, env, since)`, `observability.query_job_runs(job_name, env, since)`, `observability.list_recent_alerts(severity, since)`, `observability.search_by_resource(resource_name)`. Shape inspired by how the Atlassian MCP wraps Jira/Confluence.
- **Read-only CLI** (`obs query …`) for interactive use and non-Claude agents.
- **Support-inbox agent loop**: inbound email → classifier → `observability.*` queries → Jira ticket with triage pre-filled OR Slack summary. Replaces the v1 keyword router once the agent consistently outperforms it.
- **Agent-optimised summary endpoints** (e.g. `GET /summary/service/{name}?format=agent`) returning structured JSON ready to paste into an LLM context window — saves the agent from reconstructing the same shape every call.

If the v1 planning session surfaces a tool choice that would make v2 harder (e.g. "alerts only, no durable history"), that choice should be flagged against this section before committing.

## Pending Wiki Updates

Proposed edits to shared files (`index.md`, `log.md`). Applied during end-of-day merge session.

- `index.md` → under *Processes → Distributed Workflow*, add:
  `- [[processes/distributed-workflow/active/observability-platform]] — Active workstream tracker (design phase: company-wide lightweight observability & monitoring platform — app health, data jobs, on-prem + Azure infra, support inbox).`
- `index.md` → under *Entities → Projects*, add:
  `- [[observability-platform]] — Lightweight, company-wide observability & monitoring platform (3-plane self-host: Uptime Kuma + Prom/Grafana + Python job-health + obs-api + Mailjet→Jira). v1 design approved 2026-04-24.`
- `index.md` → under *Concepts → Architecture*, add:
  `- [[observability-architecture]] — v1 design: component diagram, data flows, alert topology, OBSERVABILITY.JOB_RUNS schema, fate-sharing mitigations, rejected alternatives. Approved 2026-04-24.`
- `index.md` → update `updated:` date to today.
- `log.md` → append:
  `| 2026-04-24 | distributed-workflow | Created active/observability-platform tracker. Research-only session: inventoried every app/pipeline/infra/Azure/inbox resource needing monitors (see tracker §F2); outlined 3-plane lightweight stack (Uptime Kuma + Prom/Grafana + Python job-health sweep + Mailjet→Jira for inbox) as a straw-man for the planning session (see tracker §F3). Steven's "workflow library" failing-templates script NOT located in repos — flagged as blocker. |`
- `log.md` → append (later same day, all checklist items resolved):
  `| 2026-04-24 | distributed-workflow | observability-platform: pre-planning checklist resolved. #observability-dev created (private) with webhook vaulted; #observability deferred to prod cutover. Probe host decision pivoted on-prem→Azure per Paul (moving off on-prem); original aldcsuptdock1c01 recommendation superseded with three fate-sharing mitigations baked into the planning session's scope (external dead-man switch, region/sub separation, Tailscale-in-Azure). Planning boot prompt updated. |`
- `log.md` → append (planning session complete):
  `| 2026-04-24 | distributed-workflow | observability-platform: planning session complete. v1 design approved by Paul (plan at C:/Users/PaulRussell/.claude/plans/fancy-inventing-aho.md). Wrote entities/projects/observability-platform.md and concepts/architecture/observability-architecture.md. Decisions Log appended with 11 ratified choices: tool stack (Uptime Kuma + Prom/Pushgateway/Grafana + obs-jobs + obs-api + Snowflake JOB_RUNS); Azure compute (B2ms VM in Quality 1/East US 2 + Function App in Production 2 for Mailjet→Jira); three fate-sharing mitigations concretised; env scheme; alert topology + correlation IDs; support-inbox router with v2 swap seam; three-week phasing; OBSERVABILITY.JOB_RUNS schema committed; check_eclipse_templates.py re-home pattern. Execution boot prompt refreshed with Week 1 ticket. |`
- `vault/credentials.md` already updated out-of-band with the new *Observability* section (no `index.md` entry — vault is gitignored).
- `log.md` → append (Week 1 execution complete):
  `| 2026-04-25 | distributed-workflow | observability-platform: Week 1 complete. Stack running locally. check_eclipse_templates.py live with full alert system: throttling, recovery notifications, root-cause grouping, blast radius, trend, recurrence, auto-escalation, data staleness, estimated recovery, Eclipse deep links. Real alerts confirmed in #observability-dev. Cosmos schema confirmed (full_name, schedule.comment, option.filter). Eclipse URL format confirmed (/account/template/{id}/edit/). lib/state.py written. Architecture doc updated to reflect actual alert system built. Week 2 Boot Prompt refreshed. |`
- `entities/projects/observability-platform.md` → status updated to Week 1 complete (done in this session).
- `concepts/architecture/observability-architecture.md` → § Alert topology section rewritten to reflect the actual alert system built (done in this session).
- `log.md` → append (session close — Uptime Kuma + final items):
  `| 2026-04-25 | distributed-workflow | observability-platform: session close. Uptime Kuma seeded via SQLite (6 monitors: 2 HTTP for eclipse+eclipse_exp, 4 TCP/443 for services without health endpoints). Slack notification fixed (field name slackwebhookURL). Status page created at /status/aldc with two groups: ALDC Core Platform + Client Applications. GitHub repo created at github.com/ALDC-io/observability (private). Cross-lane requests filed for /health endpoints on core_api, flight-check, workflows, dios. Week 2 Boot Prompt includes Azure queue depth check + Azure Monitor Grafana datasource. |`

## Blockers / Open Questions

For Paul. Each gets a date.

### Resolved

- ✅ **2026-04-24** — ~~Dedicated `observability` repo vs absorb~~ → **dedicated repo**. See Decisions Log.
- ✅ **2026-04-24** — ~~Self-hosted vs Grafana Cloud~~ → **self-host**. See Decisions Log.
- ✅ **2026-04-24** — ~~Lori vs Laura~~ → **Lori Beck**, Laura does not exist at ALDC. See Decisions Log.
- ✅ **2026-04-24** — ~~Does a support Slack channel exist?~~ → **create a new one for v1**, name TBD in planning. Marshall may have an existing one; if so, migrate later. Not blocking.
- ✅ **2026-04-24** — ~~Where is Steven's script?~~ → **Located at** `github.com/ALDC-io/projects/query_template_and_schedule_status/` (already cloned at `C:/Users/PaulRussell/repos/projects/`). Full analysis + v1 gap list in §F1. Env vars in `.env.template`; secrets live in Azure or Dashlane.

### Open

_None — all blockers are resolved as of 2026-04-24. Planning session is fully unblocked._

### Resolved (continued)

- ✅ **2026-04-24** — ~~Probe host function unclear~~ → Probe host = the Docker Compose host running Uptime Kuma + Prometheus + Grafana + the Python job-health CLIs. Its location matters because (a) if it's down everything looks silent; (b) it shouldn't depend on Tailscale for outbound probes; (c) it shouldn't live inside the Azure sub it monitors. Explained in Decisions Log + below.
- ✅ **2026-04-24** — ~~v1 Slack channel name~~ → **`#observability`** for prod (deferred until cutover), **`#observability-dev`** (private, created) for dev. Webhook for dev channel vaulted. v2 will categorise by service + client.
- ✅ **2026-04-24** — ~~Probe host recommendation `aldcsuptdock1c01`~~ → **Overridden** to Azure (local dev → Azure prod). See Decisions Log for the three fate-sharing mitigations the planning session must design in.

## Cross-Lane Requests

### 2026-04-25 — Add `/health` endpoints to ALDC apps

**Context:** Uptime Kuma Plane 1 monitors are currently using TCP port 443 for four services because they have no HTTP health endpoint. This tells us the server is reachable but not that the app is actually healthy. For a meaningful health signal these apps need a dedicated `/health` route.

**Requested changes** (one per repo — do NOT edit these repos in this workstream session):

| App | Repo | Request |
|---|---|---|
| core_api | `core_api` | Add `GET /api/health` Azure Function trigger returning `{"status":"ok","service":"core_api"}` with HTTP 200 |
| flight-check | flight-check repo | Add `GET /health` Next.js API route (no auth) returning `{"status":"ok"}` — or confirm a public URL that always returns 2xx |
| workflows / DAX API | workflows repo | Add `GET /api/health` Function trigger returning `{"status":"ok","service":"workflows"}` |
| dios (custom-fusion-92-audience-api) | DIOS repo | Add `GET /health` Gunicorn route returning `{"status":"ok","service":"dios"}` with HTTP 200 |

Once any of these is deployed, update the corresponding Uptime Kuma monitor from `port:443` back to `http` on the `/health` URL via the UK UI or `stack/uptime-kuma/seed.py`.

Note: `eclipse.aldc.io` returns HTTP 200 on the root so it already works as an HTTP monitor. `eclipse-exp.aldc.io/health` is correctly implemented and is the reference pattern for all the above.

## Pre-Planning Checklist (Paul, before pasting the boot prompt)

**Status: all resolved 2026-04-24.** Retained for audit trail. The Planning Boot Prompt below reflects the resolved state.

- [x] ~~Create Slack channel `#observability`.~~ → **Deferred** until v1 prod cutover. Public channel at that point. (Paul, 2026-04-24)
- [x] **Create Slack channel `#observability-dev`.** → Created **private** on 2026-04-24. Channel ID `C0AV0PRJ4JF`. Paul invites Lori / Steven / Marshall explicitly if/when they need visibility; no plan to make it public.
- [x] **Add an Incoming Webhook.** → Slack app *ALDC Observability* registered; webhook for `#observability-dev` captured. Prod webhook created at cutover via *Add New Webhook to Workspace* on the same app (do NOT create a second app).
- [x] **Capture webhook URL(s) in `vault/credentials.md` → *Observability* section.** Dev webhook stored 2026-04-24. Prod webhook row reserved as TBD. Format: env vars `SLACK_WEBHOOK_URL_DEV` (populated) and `SLACK_WEBHOOK_URL_PROD` (populated at cutover).
- [x] ~~Confirm probe host candidate `aldcsuptdock1c01`~~. → **Overridden.** Probe host is local dev → Azure for production. Paul is moving off on-prem dependence. See Decisions Log for the fate-sharing mitigations the planning session must design in (external dead-man switch, region/sub separation, Tailscale-in-Azure pattern).

Optional:

- [ ] Skim `C:/Users/PaulRussell/repos/projects/query_template_and_schedule_status/query-cosmos-schedules.py` before planning so the Plane 3 template-failure discussion has shared context.

## Next Session Boot Prompts

Two boot prompts are provided because the workstream has two clearly separated phases. Use the **Planning** prompt for the next session; **Execution** is for post-approval implementation sessions.

### A) Planning Boot Prompt (use this next)

````
You are resuming the observability-platform workstream in plan mode.

Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\observability-platform.md` — in full, including §F1–F3 Research Findings.
3. Read the distributed-workflow pattern:
   - `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\README.md`
   - `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\orchestration-pattern.md`
   - `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md`
4. Parallel-read every page in the tracker's *Required Context* section.
5. Verify today's daily note exists (`daily/YYYY-MM-DD.md`); if not, create it from `daily/_template.md`.

Plan-mode rule for this workstream: **every session is plan-mode-first** until both
`entities/projects/observability-platform.md` and
`concepts/architecture/observability-architecture.md` exist and are approved by Paul.

Before planning, internalise the already-ratified decisions in the tracker's
Decisions Log (2026-04-24 entries). Do NOT re-litigate these:

- Dedicated `observability` repo under `github.com/ALDC-io`.
- Self-host the stack (not Grafana Cloud).
- Support co-owner is Lori Beck (not "Laura").
- **Slack: `#observability-dev` (private) is CREATED with webhook vaulted; `#observability` (prod) is DEFERRED until v1 prod cutover.** Both webhooks live under one Slack app "ALDC Observability" — do not register a second app. v2 will add per-service / per-client channels driven by the naming-convention labels.
- **Probe host: local dev → Azure for production. On-prem `aldcsuptdock1c01` was overridden** (Paul is moving ALDC off on-prem). Planning session picks the *Azure compute service* (Container App vs Container Instance vs VM + Function App) and must design in the three fate-sharing mitigations: (1) external non-Azure dead-man switch; (2) region / subscription separation from the biggest things it watches; (3) Tailscale-in-Azure for on-prem LAN probes. See the 2026-04-24 "Probe host (REVISED)" entry in the Decisions Log.
- Steven's failing-templates script is LOCATED at
  `C:/Users/PaulRussell/repos/projects/query_template_and_schedule_status/query-cosmos-schedules.py`.
  Read it before planning. Tracker §F1 has the analysis and the four v1 gaps.
  Decisions Log commits to preserving the two Cosmos queries + status-count state
  machine verbatim; design `check_eclipse_templates.py` around that core.
- v2 agent-queryable interface is acknowledged scope; v1 must not foreclose it.
  Honour the five shape-of-v1 constraints in *Future Scope — v2 Agent Interface*
  (durable persistence, ALDC-naming-convention labels, thin stable read surface,
  correlation IDs, ≥30-day retention).

Your job this session, in plan mode:

1. No blockers to confirm — all five pre-planning items are resolved. Read Steven's
   script before designing Plane 3:
   `C:/Users/PaulRussell/repos/projects/query_template_and_schedule_status/`.
2. Produce a proposed design covering:
   a. Tool stack (validate or replace the 3-plane Uptime Kuma + Prom/Grafana +
      Python jobs straw-man in §F3). Must satisfy the five v2 shape constraints.
      Plane 3 `check_eclipse_templates.py` seeds from Steven's script per §F1 —
      preserve its Cosmos queries + state machine, extend the four gaps.
   b. **Azure compute choice for the prod probe host.** Container App (managed,
      Azure-native, fate-sharing risk) vs Container Instance (simpler, same
      fate-sharing) vs a dedicated Linux VM + Azure Function App split (more
      moving parts, cleaner isolation). Trade-off decision — name the winner
      and show the fate-sharing mitigation story (dead-man switch + region/sub
      separation + Tailscale-in-Azure) concretely, not as a handwave.
   c. Env-parameterisation scheme (config files, how per-env values are injected;
      prod-only in v1, test/qa configs stubbed).
   d. Alert topology (severity levels; correlation ID propagation; dev webhook
      routes to `#observability-dev`, prod webhook routes to `#observability`
      once created; `dry_run` flag behaviour for local dev).
   e. Support-inbox router (Mailjet vs IMAP poll; keyword map v1; Paul vs Lori
      assignment rules; how to leave a seam for v2 agent replacement).
   f. Phasing: what ships in v1 week-1, week-2, week-3. Must be aggressive enough
      that something useful lands quickly, and honest about dependencies.
   g. How v2's agent interface (MCP server / CLI / read API) attaches to the v1
      stack without refactor — sketch the seam, don't implement it.
3. Produce the plan via Claude Code's plan-mode — do NOT write any wiki page or
   any file outside this tracker until Paul approves. The plan IS the artifact.

When the plan is approved:

- Write `entities/projects/observability-platform.md` (project page, inside this workstream's lane).
- Write `concepts/architecture/observability-architecture.md` (component diagram + data flows + tool choices + rejected alternatives, inside this workstream's lane).
- Update `Decisions Log` in this tracker with every durable choice Paul ratified.
- Append a new `Session Log` entry with `did:` / `decided:` / `next:`.
- Queue `index.md` and `log.md` updates into *Pending Wiki Updates* for the end-of-day merge session.
- Refresh the *Execution Boot Prompt* below with the exact first implementation ticket.

Lane reminder: you may write ONLY the paths listed under *Lane* in the tracker.
Everything else is read-only. If the design needs changes to existing runbooks
or tool pages, write a *Cross-Lane Request* in this tracker instead.

Checkpoint procedure at end of session:
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § *Checkpoint*.
````

### B) Execution Boot Prompt — **Week 2 ticket: Plane 2 + remaining Plane 3 jobs + obs-api wiring**

````
You are resuming the observability-platform workstream in execution mode.
Week 1 is COMPLETE. This is the Week 2 ticket.

Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker in full (Session Log + Decisions Log).
3. Read the design pages:
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\observability-platform.md`
   - `C:\Users\PaulRussell\repos\wiki\concepts\architecture\observability-architecture.md`
4. Read the current repo state (skim key files):
   - `C:/Users/PaulRussell/repos/observability/jobs/check_eclipse_templates.py`
   - `C:/Users/PaulRussell/repos/observability/jobs/lib/state.py`
   - `C:/Users/PaulRussell/repos/observability/docker-compose.yml`
5. Read the eclipse_exp Grafana dashboard to import:
   `C:/Users/PaulRussell/repos/eclipse_exp/ops/grafana-dashboard.json` (skim structure)

## Week 1 state (already done — do NOT redo)

Stack is running locally at `C:/Users/PaulRussell/repos/observability/`. `.env` is populated.
`check_eclipse_templates.py` is live, firing real alerts every 15 min via ofelia cron.
`lib/state.py` handles throttle / trend / recurrence / auto-escalation / recovery.
Cosmos schema confirmed: `account.full_name`, `account.short_code`, `schedule.comment` for errors,
`schedule.option.filter` for partition dates. Eclipse URL: `/account/template/{id}/edit/`.

Repo pushed to `github.com/ALDC-io/observability` ✅
Uptime Kuma seeded (6 monitors, Slack notification, status page at /status/aldc) ✅
Still pending — Paul to do: add inactive Fusion92 templates to `config/templates.yaml` with `enabled: false` when IDs are known.

## Current ticket — Week 2

**Goal:** Plane 2 metrics live in Grafana; all four Plane 3 job-health checks running;
`OBSERVABILITY.JOB_RUNS` table created; `obs-api` routes wired to real data.

**Exit criterion:** Grafana dashboard shows eclipse_exp metrics; a Snowflake query on
`OBSERVABILITY.JOB_RUNS` returns real rows from `check_eclipse_templates.py` runs;
`obs-api` `/jobs` endpoint returns live data.

**Steps (no plan-mode required — Week 2 scope is well-defined):**

1. **Prometheus scrape of eclipse_exp `/metrics`:** uncomment the `eclipse_exp` scrape
   target in `stack/prometheus.yml`. Verify metrics appear at `http://localhost:9090`.

2. **Import eclipse_exp Grafana dashboard:** copy
   `C:/Users/PaulRussell/repos/eclipse_exp/ops/grafana-dashboard.json` into
   `stack/grafana/dashboards/`. Add a dashboard provisioning YAML to
   `stack/grafana/dashboards/dashboard.yml`. Restart Grafana and verify the dashboard loads.

3. **Create Snowflake `OBSERVABILITY.JOB_RUNS` table:** use the schema in
   `concepts/architecture/observability-architecture.md` § Schemas. Database: create a new
   `OBSERVABILITY` database in the test or prod Snowflake environment (confirm with Paul
   which env to use). Add a Snowflake connection to the vault pointing at it.

4. **Write `lib/snowflake_writer.py`:** appends one row per check run to `JOB_RUNS`.
   Called at the end of every Plane 3 job. Graceful degradation — if Snowflake write
   fails, log and continue (never block the alert path).

5. **Wire `check_eclipse_templates.py` → Snowflake:** call `snowflake_writer.write()`
   after the push/alert loop. Pass the corr_id, check_name, status summary, per-template
   details as the `details` VARIANT column.

6. **Write `check_snowflake_tasks.py`:** query `INFORMATION_SCHEMA.TASK_HISTORY` for
   FAILED or SKIPPED tasks in the last N hours. Reuse `lib/state.py`, `lib/alerter.py`,
   `lib/push.py`, `lib/snowflake_writer.py`. Pattern from [[flight-check]] § 2 query.

7. **Write `check_pbi_refresh.py`:** PBI REST `/datasets/{id}/refreshes` per workspace.
   Alert on failed refresh. Surface credential-expiry countdown from
   [[powerbi-secret-refresh]] § *Current secret expiry dates*. Reuse shared lib.

8. **Write `check_data_share.py`:** `SELECT 1 FROM <shared_obj> LIMIT 1` for each
   object in `prod.yaml` shared_objects list. `SELECT MAX(___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___)` for frozen-share detection. Reuse shared lib.

9. **Wire obs-api `/jobs` endpoint** to query `OBSERVABILITY.JOB_RUNS`. `/alerts` endpoint
   to query `JOB_RUNS WHERE alert_sent = TRUE`. `/search?corr_id=` to join both.

10. **Write `check_azure_queue.py`:** poll Azure Storage Queue depth for
    `aldcprodstacqueue1c01` (the `/work/pick` queue that caused [[connector-timeout-outage]]).
    Uses the Azure Storage REST API with a SAS token or service principal from vault.
    Alerts P1 when depth > configurable threshold (default 100, representing backlog beyond
    normal burst). Alert message shows current depth, growth trend, and links to Azure portal
    queue page. Cadence: 5 min. Reuse `lib/state.py`, `lib/alerter.py`, `lib/push.py`.
    Add `AZURE_STORAGE_ACCOUNT`, `AZURE_QUEUE_SAS_TOKEN` env vars to `.env.example`.

11. **Update ofelia labels** to schedule all new checks (30 min Snowflake tasks + PBI,
    60 min data share, 5 min Azure queue).

12. **Add Grafana ALDC Prod Overview dashboard** — the primary operational view.
    Single screen answering all 5 platform health questions:
    - Row 1 — App health: embed UK status page iframe OR replicate the 6 monitor statuses
      via UK's JSON API (`/api/status-page/aldc`) as a table panel.
    - Row 2 — Metrics: eclipse_exp request rate, error rate, p99 latency (from Prometheus).
    - Row 3 — Job health: `OBSERVABILITY.JOB_RUNS` last-run status per check (Snowflake datasource).
    - Row 4 — Azure queue depth: `aldcprodstacqueue1c01` depth timeseries (from `check_azure_queue.py` Pushgateway metrics).
    Design goal: one screen, no clicking, answers "is everything ok right now?"

13. **Add Grafana Azure Monitor datasource** (service principal from vault) to surface
    Application Insights request rates + exception counts for core_api and eclipse_exp.
    Add to the ALDC Prod Overview dashboard as a separate row.

**Deliverables:**
- Eclipse_exp metrics visible in Grafana.
- `OBSERVABILITY.JOB_RUNS` table with real rows.
- All Plane 3 checks running on schedule (Eclipse templates, Snowflake tasks, PBI refresh, data share, Azure queue depth).
- `obs-api /jobs` returning live data.
- Azure queue depth alert wired — motivated by [[connector-timeout-outage]].
- Tracker Session Log entry for Week 2.

Plan-mode rule: no plan-mode required for Week 2 — scope is fully specified.
Exception: if a design decision arises (e.g. which Snowflake environment to use,
PBI REST auth approach), pause and ask Paul rather than assuming.

Lane reminder: code writes to `observability/` repo only. Wiki writes limited to:
this tracker (Session Log + Pending Wiki Updates), and tool pages
`entities/tools/uptime-kuma.md`, `entities/tools/prometheus.md`,
`entities/tools/grafana.md` if not yet written. Do NOT write the runbook
(`processes/operations/observability-runbook.md`) until Week 3.

Checkpoint procedure:
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § *Checkpoint*.
````

## See Also

- [[processes/distributed-workflow/README|distributed-workflow]]
- [[orchestration-pattern]]
- [[session-lifecycle]]
- [[tracker-template]]
- [[flight-check]] — today's manual observability runbook; the thing v1 automates.
- [[eclipse_exp]] — reference implementation for app-level health.
- [[aldc-scripts]] — prior-art weekly-report-to-Slack; treat as reference only, status unconfirmed.
- [[connector-timeout-outage]], [[powerbi-secret-refresh]], [[GP-PENDING-data-share-stability]] — past incidents that motivate specific v1 monitors.
