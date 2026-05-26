---
tags: [tool, platform, aldc-launchpad, automation, orchestration]
aliases: [Session Orchestrator, Claude Code Orchestrator, Pipeline Executor]
sources: []
created: 2026-05-15
updated: 2026-05-26
---

# Session Orchestrator

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
| `connector-migration` | 15 | Eclipse → Prefect v3 migration (analyze → create-flow → test → PR → deploy → verify → parity) |
| `credential-provision` | 6 | Credential collection → Key Vault → Prefect Block |
| `data-parity-test` | 5 | Post-migration data validation (legacy vs Prefect output) |
| `connector-promotion` | 14 | QA → UAT → Prod with gates and parity checks |
| `client-onboarding` | — | Provision new client end-to-end (Snowflake, RBAC, blocks) |
| `connector-activation` | — | Deploy migrated connector for a specific client |
| `prefect-infra` | deferred | One-time setup (already complete) |

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

## Hardening (2026-05-26 session)

Key fixes and features added during pipeline hardening sprint:

1. **Agent retry was broken** — `advance_pipeline()` only matches dispatched/pending stages, so retrying a failed stage silently did nothing. Fixed: agent uses `restart_from_stage()` which resets to pending and re-dispatches.
2. **Stale dispatch recovery** — `recover_stale_pipelines()` scans on startup + periodic watchdog for stages stuck in dispatched >30min.
3. **`create_pr` commits before pushing** — Claude sessions don't always commit their work. Script now calls `commit_changes()` first and verifies commits exist ahead of main.
4. **Prefect deployment name** — Was generating `name/name` with a slash causing API 500s. Fixed to just `name`.
5. **Circuit breaker** — Prevents cascading Prefect API failures across all pipelines.
6. **Stage metrics** — Cost/tokens/duration now flow from sessions to pipeline stage objects for analytics.
7. **Failure pattern learning** — Memory store tracks incidents; global pause if 3+ pipelines fail at same stage within 30min.
8. **Test coverage** — 74 → 122 tests.

**Remaining (phases 5-9):** Hard budget enforcement, SLA auto-escalation, performance dashboard UI, configurable parallelism, prompt effectiveness tracking.

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

## See Also

- [[aldc-launchpad]] — ALDC Launchpad monorepo (home repo)
- [[processes/distributed-workflow/active/aldc-launchpad/README]] — Active workstream tracker
- [[claude-code-enhanced]] (legacy cce project, for comparison)
