---
tags: [tool, platform, aldc-launchpad, automation, orchestration]
aliases: [Session Orchestrator, Claude Code Orchestrator, Pipeline Executor]
sources: []
created: 2026-05-15
updated: 2026-05-15
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

## Pipeline Types (Proposed — Not Yet Implemented)

15 reusable pipeline types identified as DAG templates. Each stage = one Claude Code session in a worktree:

1. **Connector credential retrieval** — OAuth token exchange, credential validation
2. **Prefect implementation** — flow + task design, testing, deployment
3. **Snowflake warehousing** — schema design, SQL development, testing
4. **Bug fix** — investigation, root cause, fix, testing, deployment
5. **New client onboarding** — discovery, setup, template config, go-live
6. **Existing client migration** — from legacy to new framework
7. **Azure provisioning** — infrastructure as code, deployment, validation
8. **Eclipse → Prefect migration** — connector port, testing, cutover
9. **dbt development** — schema design, model implementation, testing
10. **Cube semantic layer** — metric definition, dimension design, validation
11. **Data quality monitoring** — rules, testing, alerting
12. **CI/CD infrastructure** — GitHub Actions, deployment gates, testing
13. **Incident response** — triage, mitigation, root cause, prevention
14. **Credential rotation** — secret refresh, key management, deployment
15. **Documentation sync** — wiki updates, runbook generation, knowledge transfer

**Architecture:** Each pipeline type is a DAG of reusable stages. Each pipeline run creates a PR at completion.

**Next Step:** Opus plan-mode session to design the pipeline DAG system.

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
