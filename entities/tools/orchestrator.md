---
tags: [tool, platform, aldc-launchpad, prefect-connectors, automation, orchestration, parity]
aliases: [Session Orchestrator, Claude Code Orchestrator, Pipeline Executor, parity harness]
sources: [prefect-connectors/orchestrator/stage_scripts/snowflake_ops.py, prefect-connectors/orchestrator/server.py, prefect-connectors/orchestrator/pipelines.py, prefect-connectors/orchestrator/static/index.html, prefect-connectors docs/KNOWN_ISSUES.md issues 23+25 (branch development @ 62556f1)]
created: 2026-05-15
updated: 2026-08-14
---

# Session Orchestrator

> ✅ **UNSHELVED — 2026-08-13/14.** The connector-promotion pipeline is **live again** and is the
> tooling for the Prefect migration hackathon. It ran end to end (17/17 stages, parity PASS) on
> `exchangeratesapi` on 2026-08-14. See [[#Parity harness — how to read a PASS (2026-08-14)]] and
> [[#Gotchas]] below, which are the current operating notes.
>
> **It also moved repos.** The orchestrator now lives in **[[prefect-connectors]]** under
> `orchestrator/` and is started with `python -m orchestrator` from that repo — not
> `aldc-launchpad/scripts/orchestrator.py`. Paths in the sections below predate the move (the Phase 0
> migration decided 2026-05-22, see [[orchestrator-production-readiness]]) and should be read as
> historical.
>
> <details><summary>Superseded 2026-05-28 banner</summary>
>
> ⚠️ **Connector-promotion use case SHELVED — 2026-05-28.** The orchestrator's headline pipeline (Prefect connector promotion QA→UAT→Prod) is parked along with the [[prefect|Prefect]] migration and the credential portal. The generic session-runner may be reused later, but do not treat the connector-promotion / credential pipelines below as the live process. Live work + full context: [[processes/distributed-workflow/active/navira/README|Navira workstream]].
>
> </details>

Autonomous multi-stage pipeline execution system for ALDC Launchpad. Spawns isolated Claude Code sessions in git worktrees, manages concurrency, monitors execution, and surfaces results via web UI.

## Core Infrastructure

**Location:** `aldc-launchpad/scripts/orchestrator.py` + `platform/master/pages/orchestrator/index.html`

**Stack:**
- Python HTTP server on port 8765 serving master dashboard + REST API
- Launches `claude -p` subprocesses with `--output-format stream-json` for autonomous sessions
- Thread pool (max 4 parallel sessions) with per-session watchdog timers
- Git worktree isolation: each session gets a branch `session/{ticket}-{hash}`
- Persistent state in `platform/master/data/sessions.json` (SQLite migration possible later)

**Key Components:**

1. **Session Launcher** — spawns `claude -p` with:
   - Pre-loaded context (wiki page for ticket, related pages, client registry, credentials, tracker data, prior session learnings)
   - Self-enrichment instructions (search Zeus Memory, fetch live Jira, synthesize context)
   - Session type selected from 15 pipeline types (see below)
   - Worktree isolation flag + permission mode (skip-permissions for worktrees, auto for analysis)

2. **Stream JSON Parser** — decodes real-time `stream-json` event stream:
   - Extracts assistant text (thought/output) into formatted prose
   - Builds tool call chips (fn name + args) with visual grouping
   - Extracts usage/cost from three nested paths: `event.message.usage`, `event.usage`, `event.modelUsage`
   - Handles timeout interruption gracefully

3. **Watchdog Timer** — per-session process management:
   - Timeout handler kills hung processes and force-sets status
   - Race condition fixed: if result event arrived before timeout, force status to "succeeded" regardless of prior state
   - Logs exit code + stderr for debugging

4. **Output Renderer** — web UI displays session output as:
   - Stream-json events → formatted prose (markdown-to-HTML via mdToHtml)
   - Tool calls as chips + metadata
   - Completion banners with total tokens/cost
   - Live scroll updates during stream; archive at completion

## Bugs Fixed (Session 2026-05-15)

1. **Windows Pipe Buffering** — `text=True` on Popen caused Python's TextIOWrapper to buffer stdout, blocking readline() until process death. Fixed by switching to binary I/O (`bufsize=0`, no `text=True`), decoding manually.

2. **Timeout Race Condition** — timeout handler set status to "timeout" while `_run_session` was stuck on readline(). After kill, the result event was read but status was already "timeout". Fixed by: if `got_result` event, force status to "succeeded" regardless.

3. **Usage/Cost Extraction** — stream-json nests usage in three places depending on event type. Added `_extract_usage()` helper covering all three paths (`event.message.usage` for assistants, `event.usage` for results, `event.modelUsage` for per-model breakdown).

4. **UI Button Logic** — `cancelSession` used PATCH instead of POST; `launchSession` fired toast+close twice. Fixed.

## Permission Model

- **Worktree sessions** (implement, fix_bug, plan, migrate_connector): `--dangerously-skip-permissions` — the worktree IS the sandbox
- **Non-worktree sessions** (analyze, code_review, investigate): `--permission-mode auto`
- **Non-read-only templates** force `use_worktree=true`

## Context Enrichment Pipeline

Pre-loads local context into prompt before spawning sessions:

1. **Wiki page** for the ticket (if exists)
2. **Related wiki pages** (follows `[[wikilinks]]`)
3. **Client registry entry** from `shared/client-registry.json`
4. **Credential status** for the client from `platform/master/data/credentials.json`
5. **Full ticket data** from `platform/master/data/tracker.json`
6. **Prior session learnings** from completed sessions (self-enrichment log)

Self-enrichment instructions tell the spawned session to:
- Search Zeus Memory for ticket/client context
- Fetch live Jira issue status via Atlassian MCP
- Synthesize pre-loaded + live context before starting work

## Pipeline Types (Production — 6 Active, 1 Deferred)

Migrated from proposed list to production DAG-based execution. Each stage is either a `claude-p` session, a `script` (Python callable), or a `gate` (manual approval or condition poll).

| Type | Stages | Purpose |
|---|---|---|
| `connector-migration` | ~~15~~ **18** | Eclipse → Prefect v3 migration (analyze → create-flow → test → PR → deploy → verify → parity) |
| `credential-provision` | 6 | Credential collection → Key Vault → Prefect Block |
| `data-parity-test` | 5 | Post-migration data validation (legacy vs Prefect output) |
| `connector-promotion` | 14 | QA → UAT → Prod with gates and parity checks |
| `client-onboarding` | — | Provision new client end-to-end (Snowflake, RBAC, blocks) |
| `connector-activation` | — | Deploy migrated connector for a specific client |
| `prefect-infra` | deferred | One-time setup (already complete) |

⚠ **Stage counts here are unreliable — count the definition.** `connector-migration` was measured at
**18 stages** on 2026-08-14; this table said 15 and [[prefect-connectors]] said 16. The section
comment above `PIPELINE_DEFS` in the code says **"10"** and is itself stale. The comment is not the
count.

## Pipeline Engine (2026-05-26)

**Location:** Migrated to `prefect-connectors/orchestrator/` (was `aldc-launchpad/scripts/`)

**DAG Execution:**
- Stages define `depends_on: [...]` for dependency ordering
- `_find_ready_stages()` computes which stages can run in parallel
- DAG view in UI shows parallel execution capability
- Auto-advance on success unless `auto_advance: false` (manual gate)

**Stage Types:**
- `claude-p` — launches `claude -p` subprocess in git worktree
- `script` — calls Python callable directly (jira_ops, prefect_ops, snowflake_ops, git_ops, gate_checks)
- `gate` — manual approval or condition-based polling (Docker image ready, CI checks pass)

**Gate Auto-Policy:** Configurable conditions per gate (e.g., `tests_pass: true`, `parity_score_min: 99.5`). Auto-approves if conditions met.

## Engine Modules (14 total)

| Module | Purpose |
|---|---|
| `circuit_breaker.py` | Closed/open/half_open state machine for Prefect/Snowflake/GHCR/Jira calls. Prevents cascading failures. |
| `pipeline_agent.py` | Monitors stage failures, classifies errors, auto-retries (max 2), failure pattern learning via memory store, global pause on recurring failures, stale-dispatch watchdog. |
| `analytics.py` | Per-connector cost tracking, budget forecasting, stage metrics (avg/p95 duration, cost, success rate). |
| `audit.py` | Append-only pipeline event log per pipeline (stage started/completed/failed, gate approvals, rollbacks). |
| `memory.py` | Per-scope persistent memory (decisions, learnings, incidents). Keyword search. Used by pipeline agent for failure correlation. |
| `notifications.py` | Webhook dispatch (Slack/Teams/generic), exponential backoff retry, delivery logging. |
| `quality_observatory.py` | Parity score aggregation, per-table metrics (row counts, schema match, freshness). |
| `health_monitor.py` | Polls Prefect/Snowflake for runtime metrics. Alert rules engine (gt/lt/eq operators). |
| `wave_scheduler.py` | Batch connector migrations in ordered waves with parallelism control. |
| `rollback.py` | Backward walk from failed stage with undo callable registry. |
| `validation.py` | Auto-checks session output (command, file_exists, grep). Quality gate mapping. |
| `events.py` | In-memory event bus, SSE pub/sub, ring buffer. |
| `work_guard.py` | Git repo safety checks, session lock files. |
| `canary.py` | Canary/shadow deployment validation against production Snowflake. |

## Hardening (2026-05-26 — all 9 phases complete)

### Phases 1-4 (morning session)

1. **Circuit breaker** — Prevents cascading Prefect/Snowflake/GHCR API failures.
2. **Stage metrics** — Cost/tokens/duration flow from sessions to stage objects.
3. **Failure pattern learning** — Memory store tracks incidents; global pause if 3+ pipelines fail at same stage within 30min.
4. **Agent retry fix** — `restart_from_stage()` replaces broken `advance_pipeline()` for retries. Stale dispatch recovery on startup + watchdog.
5. **Test coverage** — 74 → 122 tests.

### Phases 5-9 (afternoon session)

5. **Hard budget enforcement** — Pipeline-level budget cap (auto-calculated at 120% of stage budgets). Pauses pipeline if cumulative cost exceeds cap. `POST /api/pipelines/{id}/resume` to unblock with optional new budget.
6. **SLA auto-escalation** — Critical health alerts auto-create Jira tickets with 60-minute dedup cooldown per connector+metric. `POST /api/health/escalate`.
7. **Performance dashboard** — Analytics tab shows stage metrics table (runs, success rate, avg/p95 duration, cost) and prompt effectiveness table. Configuration panel for max_parallel.
8. **Configurable parallelism** — `ORCHESTRATOR_MAX_PARALLEL` env var + `PATCH /api/config` runtime update. Recreates thread pool.
9. **Prompt effectiveness tracking** — Records pass/fail per template:stage in `on_session_complete`. `GET /api/analytics/prompt-effectiveness`.

### Pipeline infrastructure (first end-to-end run)

- **verify-blocks stage** — New stage before `deploy-prefect` that checks required Prefect blocks exist. Auto-creates from Key Vault (primary + cred vault) if missing. Also verifies Snowflake infrastructure block.
- **Entrypoint resolution** — Fuzzy catalog matching with stripped-underscore comparison. Also scans deployments directory as fallback. Fixed `exchangeratesapi` → `exchange_rates.py` mismatch.
- **verify-data** — Resolves target database from account short_code (`QA_DG1_GEP_PREFECT`) and schema from connector catalog.
- **Parity check** — Cross-account: compares Prefect QA output (`og35375`) vs production Snowflake (`wj66376`) using separate prod credentials. Row counts, schema comparison, aggregates.
- **CI auto-trigger** — `image-gate` now auto-triggers `gh workflow run CI --ref development` if no recent build exists. `workflow_dispatch` added to ci.yml.
- **Credential loader** — BOM fix for Snowflake JSON, prod admin secret, cred vault URL. Defensive `or {}` guards.

**Test count:** 144 tests (22 new for phases 5-9).

## UI Design

**Location:** `platform/master/pages/orchestrator/index.html`

Rebuilt with Neurospect-inspired design system:
- Analytic Labs branding with pulsing purple neon logo glow
- Glassmorphism cards, Orbitron/Inter/JetBrains Mono typography
- Output tab renders stream-json as formatted prose instead of raw JSONL
- Launch modal with pipeline-type selector, ticket lookup, context preview
- Session list with status badges, cost display, cancel button

## Session State

**Location:** `platform/master/data/sessions.json`

Per-session structure:
```json
{
  "session_id": "uuid",
  "ticket_id": "GP-208",
  "pipeline_type": "snowflake-warehousing",
  "status": "running|succeeded|timeout|failed",
  "started_at": "ISO8601",
  "completed_at": "ISO8601",
  "tokens_in": 10000,
  "tokens_out": 5000,
  "cost_usd": 0.50,
  "branch": "session/GP-208-abc123",
  "output_log": "sessions/session-uuid.jsonl"
}
```

Output logs stored in `platform/master/data/sessions/{session_id}.jsonl` for replay/inspection.

## Parity harness — how to read a PASS (2026-08-14)

The `snowflake_ops.py` parity stage compares a QA landing schema against the production table. Four
rules were learned the hard way; all four are properties of *measurement*, not of this codebase.

**1. Coverage is a question about the business key, not the whole row.**
Deduplicating on all columns counts an intraday *restatement* as extra coverage. Production keeps
~3.3 rate restatements per key per day; QA pulls each date once. Deduped on all columns those look
like wildly different coverage (14,517 vs 4,381); deduped on the **primary key** they are identical
(4,381 vs 4,381) — which is the true statement. Dedupe on the grain you actually claim to cover.

**2. A duplication budget must be *relative* when production cannot reproduce its own history.**
Production `EXCHANGE_RATES` is itself **4.86× duplicated** (repeated `MergeStrategy.Insert`, every
row `HISTORY_CURRENT=1`, no close-out). An absolute "zero duplicates" gate can never pass against
that baseline, so the raw-row check is **demoted to non-gating** and the budget becomes "QA must not
be materially worse than prod".

> ⚠ **Read the resulting PASS accurately.** A green verdict under a relative budget means *QA is no
> worse than prod*. It does **not** mean *QA is clean*. The reference run passed while still
> carrying **1.51× in-window duplication**. Anyone quoting the PASS as a cleanliness claim is
> over-reading it.

**3. Compare both sides over the same window, and seed that window from the *intended* range.**
An early version applied QA's own range to production. Fixed to a true date intersection — but the
window is still seeded from **QA's own MIN/MAX**, so if QA *under-covers* dates the window narrows
to exactly what QA has, both sides then match, and it passes. The `clipped` annotation only fires
when **prod** narrows QA — the harmless direction. **Open defect as of 2026-08-14.** The fix is to
carry the run's intended window (the partition scheme / `started_at`, already known to
`prefect_ops`) into parity and compare it against `qa_min..qa_max`.

**4. Re-pulling the same date under `MergeStrategy.Insert` duplicates rows.**
`backfill_runs: 1` passes; `backfill_runs: 8` fails at 10.57× against prod's 4.86×. Nothing
dedupes, because the primary key is enforced per table and the re-pulled rows are identical apart
from metadata columns. Two non-equivalent remedies: switch to `MergeStrategy.Version` (idempotent on
the key, as [[amazon-ads]] and `amazon_sellercentral` use — but it changes write semantics and needs
its own evidence), or keep `Insert` and make partitions non-overlapping. See
[[connector-development-standards]] for the scheme-selection rules.

**5. The coverage check is inert by default — and still reports PASS.**
Nothing in the shipped pipeline supplies an **intended window** to the coverage comparison. Without
one it returns `NOT_COMPARABLE`; that verdict is filed under **`advisories`** rather than
`inconclusive`; and the run **still reports PASS**. A check that cannot produce a failing answer
reports success forever — see [[vacuous-verification]]. Distinct from rule 3: rule 3 is a window that
narrows until both sides trivially match, this is a comparison that never happens at all.
*(`prefect-connectors` `docs/KNOWN_ISSUES.md` issue 25, 2026-08-14.)*

Note the interaction with [[schema-dialect-drift]]: consolidating 48 fragments into 1 did not
*create* the duplication, it made it **visible** — the same rows were previously spread across many
tables. Visible is an improvement, not a fix.

⚠ And note the interaction with the **connector-side** write defects found 2026-08-14
([[prefect-connectors]] issues 22, 24, 26): `MergeStrategy.Version` triple-inserts, every partition
hashes to `md5("")`, and `self.responses` accumulates across partitions. **Any duplication factor the
harness reports is the product of at least two independent causes** — which is why the measured
**10.57×** never traced to a single mechanism, and why fixing one of them will not take the number
to 1.

## Stall recovery — a `pending` stage is unreachable (2026-08-14)

**If a stage completes without queueing its successor, the pipeline cannot be rescued from the UI.**
Three independent mechanisms each miss it:

| Mechanism | Why it misses a `pending` stage |
|---|---|
| UI approve control | Rendered only for `status === 'dispatched'` (`orchestrator/static/index.html:1085-1086`). A `pending` stage gets **no control of any kind** |
| `parity_score_min` auto-policy | Lives inside `_dispatch_gate_stage` (`server.py:858-871`) — unreachable until a gate has been **dispatched** |
| `recover_stale_pipelines` | Resets only `dispatched` stages |

> **Correction to previously-recorded state.** `recover_stale_pipelines` is **not** gated on the
> pipeline agent toggle, and it runs **unconditionally at server startup** (`server.py:2403`). It
> still cannot recover a stalled pipeline — but the reason is the `dispatched`-only reset above, not
> that it never runs.

**Half fixed.** `parity-check`'s `auto_advance` was flipped to `True` in commit `bf67f66`. But
**fifteen** stage definitions still carry `auto_advance: False`, and **thirteen of those are not
gates** — `uat-parity`, `prod-robustness`, `canary-monitor`, `enable-schedule` and others across
`connector-promotion`, `connector-canary` and `connector-activation`. Each is a latent stall.

⚠ **`auto_advance` is copied onto the pipeline record at `create_pipeline` time**
(`orchestrator/pipelines.py:1288`). A pipeline created before the fix keeps the **old** value, and an
orchestrator **restart does not retrofit it** — the usual "restart picks up orchestrator-side fixes"
rule does **not** apply to this field. Recreate the pipeline.

## Gotchas

- **`versions` is a dict**, `{table_name: rows}` — not a list. `versions[0]` raises `KeyError`, not
  an `IndexError`, which reads like a missing table. Use `sorted(...)[0]`.
- **A deployment's landing schema is fixed when the deployment is created.** Restarting a pipeline
  from `trigger-run` under a *new* user suffix writes to the **OLD** schema while parity reads the
  new one — so parity reports an empty QA side and you debug the wrong thing. Now a hard refusal
  (PR #34).
- **`trigger_and_wait` wraps its body in `try/except`**, so a sentinel exception raised inside a test
  is swallowed into a `ScriptResult`. "Did my call get through?" assertions written that way test
  **nothing** and pass unconditionally. Assert on the **absence of the specific refusal** instead.
- **The suffix and the data dir normally move together.** `ORCHESTRATOR_USER_SUFFIX=pr` resolves the
  data dir to `data-pr` on its own. Pinning `ORCHESTRATOR_DATA_DIR` back while changing the suffix
  produces a banner that disagrees with the directory — occasionally a deliberate hack (to get a
  virgin landing schema while keeping pipeline history), never a pattern. **Check the startup banner
  reads the instance you expect**; `default` means the env did not take and you are about to write
  into the shared landing schema.
- **Orchestrator-side fixes need a process restart; connector-side fixes need a new image.** Getting
  this backwards costs an 18-minute pipeline run for nothing. Parity logic, gates, worktree paths,
  the watchdog and the suffix guard are all orchestrator-side. Anything in `base_connector` ships in
  the ACI image: merge → CI rebuild → new run. ⚠ **One exception: `auto_advance` is snapshotted onto
  the pipeline at creation, so a restart does not pick it up** — see the stall-recovery section.

## See Also

- [[aldc-launchpad]] — ALDC Launchpad monorepo (original home repo)
- [[prefect-connectors]] — where the orchestrator now lives and runs (`python -m orchestrator`)
- [[schema-dialect-drift]] — the fragmentation root cause the parity harness was built to detect
- [[vacuous-verification]] — why the inert coverage check and the swallowed sentinel exception are the same bug
- [[github-actions]] — the silent publish-skip that keeps connector-side fixes from ever running
- [[orchestrator-production-readiness]] — the 5-phase hardening plan (Phases A–E)
- [[processes/distributed-workflow/active/aldc-launchpad/README]] — Active workstream tracker
- [[claude-code-enhanced]] (legacy cce project, for comparison)
