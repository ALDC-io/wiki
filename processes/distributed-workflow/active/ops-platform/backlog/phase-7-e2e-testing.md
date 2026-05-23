---
tags: [ops-platform, launchpad, phase7, testing, e2e, validation]
created: 2026-05-09
updated: 2026-05-15
---

# Phase 7: E2E Testing

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase7.md` → `/launchpad-phase7`
**Status:** Phase 7a complete (2026-05-15) — smoke test + CLI last-mile gaps closed

> **Active work is in the `aldc-launchpad` monorepo.** See the 2026-05-15 session log in [[../../aldc-launchpad/README]] for details.

## Goal

Validate the complete Launchpad platform end-to-end with a synthetic test client.

## Phase 7a: E2E Smoke Test (2026-05-15) — DONE

Pragmatic-testable scope — validate what exists today, create TestCorp, surface gaps.

### Completed
1. TestCorp synthetic client created in `client-registry.json` + `state.json` (e-commerce, individual tier, 3 connectors)
2. SPA golden path: 21/21 routes resolve, 12/21 hydrate from JSON data layer
3. Wizard smoke test: 6-step flow fully parameterized, generates correct output for TestCorp
4. Warehouse multi-tenant SQL: fully parameterized, RLS isolation solid, TestCorp provisionable
5. Credential exchange API: 6 endpoints implemented, HMAC tokens + Key Vault + Prefect blocks
6. CLI last-mile gaps closed: wizard format adapter, `--dry-run`, credential link generation
7. `CLIENT_BLOCK_SUFFIXES` hardcoding fixed (dynamic fallback)
8. `build_block_data` Snowflake stub fixed (structured account/user/role/password)
9. Wizard: GA4 connector added, PBI→Superset deliverables
10. Dry-run verified: `python -m cli.aldc_onboard --env qa provision TESTCORP.json --dry-run` passes

### Remaining for full Phase 7
- Credential portal UI (connect.analyticlabs.io) — API backend built, needs HTML/JS form
- Live provisioning against QA Snowflake (dry-run verified, live run not yet executed)
- Superset dashboard provisioning E2E
- Onboarding time measurement (target < 30 min)
- Regression test: existing clients GEP/F92 unaffected
- Security review (`/security-review`)

## Phase 7b: Session Orchestrator + Pipeline Engine (2026-05-15) — DONE

Built end-to-end orchestrator for parallel ticket execution with AI agents.

### What was built

**Pipeline Engine** (`scripts/pipelines.py`, `scripts/orchestrator.py`):
- 4 pipeline types: connector-migration (14 stages), prefect-infra, credential-provision, data-parity-test
- 3 stage types: `claude-p` (AI code gen, ~$0.50-1.50), `script` (zero-cost Python callables), `gate` (manual/condition)
- DAG-based execution with `depends_on`, `auto_advance`, prior_results chaining
- Worktree chaining: all stages share one git worktree/branch per pipeline
- Submodule init on worktree creation (connectors/ available to all stages)
- Azure Key Vault credential loading at startup (`scripts/stage_env.json`)
- Jira transitions at pipeline start (→Development), QA deploy (→QA), completion (→Done)

**Script Stages** (`scripts/stage_scripts/`):
- `prefect_ops.py` — deploy connector to Prefect QA work pool, trigger flow run + poll to completion
- `snowflake_ops.py` — verify data landing (row counts), run parity check (pytest or API)
- `gate_checks.py` — Docker image condition polling via GHCR API
- `jira_ops.py` — Jira transitions + comments (non-blocking if no token)
- `credentials.py` — Azure Key Vault → env vars at startup

**Orchestrator UI** (`platform/master/pages/orchestrator/index.html`):
- Three-column layout: Inbox | Main board | Zeus Chat + Activity
- Pipeline Cards view with SVG DAG visualization, progress bars, stage type icons (🧠/⚙/🔒)
- Deploy Board view: QA → UAT → Prod promotion status per connector
- Session Kanban: traditional lane-based view with review/diff/approve buttons
- Zeus Chat: natural language queries via `claude -p`, pipeline state context
- Azure Neural Voice TTS (`en-US-DavisNeural`): spoken alerts for stage completions, failures, gates
- 5 specialized agents: Zeus Review, Code Review, User Testing, Deploy, Refactor
- Gate action panels: "Approve & Continue" buttons across all 3 views
- Diff viewer modal: syntax-highlighted diffs including connectors submodule
- Review & Direct bar: per-pipeline agent buttons + direction input
- Ticket detail expansion: click-to-expand with metadata, Jira status, priority

### Commits

| SHA | Message | Branch |
|-----|---------|--------|
| `7ba2f99` | feat(orchestrator): pipeline engine with DAG execution, script/gate stages, Key Vault credentials | `paulrussell/feature/e2e-onboarding` |
| `01e48e2` | feat(orchestrator-ui): Neurospect-style dashboard with Zeus Chat, voice alerts, deploy board | `paulrussell/feature/e2e-onboarding` |

### Pipeline runs (Phase 0 tickets)

Seeded and executed 4 Phase 0 pipelines in parallel:
- **GP-218** (prefect-infra): 4/4 stages completed — work pool YAMLs, promotion script, CI/CD workflows, QA checklist. Real commits in connectors submodule.
- **GP-219** (connector-migration): 3/10 stages completed (analyze, create-flow, local-test) → paused at merge-gate. Worktree chaining fix needed (stage 2 couldn't see stage 1 output) — fixed mid-session.
- **GP-242** (credential-provision): completed code stages — HMAC link gen, credential tracking, block provisioning scripts.
- **GP-246** (data-parity-test): completed code stages — 596-line parity test suite with Snowflake queries, dry-run report.

Total spend across all pipeline runs: ~$15 (multiple runs including debug iterations).

### Infrastructure created

- Azure Speech Services resource: `aldc-launchpad-speech` (rg-aldc-launchpad, Quality 1, F0 free tier, Canada Central)
- `scripts/stage_env.json` (gitignored): Key Vault URL, Prefect URL, Snowflake QA config, Azure Speech key

### Bugs fixed during session

1. **Worktree path mismatch**: `_create_worktree()` used `session["id"]` but pipeline sessions set `worktree_path` to shared pipeline name → stages couldn't find each other's work
2. **Submodule missing in worktrees**: `git submodule update --init` not called → connectors/ empty → GP-219 produced nothing
3. **Stage schema KeyError**: gate/script stages missing `template` field → pipeline creation crashed
4. **importlib dataclass bug**: modules loaded via `importlib.util` need `sys.modules` registration before `exec_module` or `@dataclass` fails
5. **Zeus Chat auth**: Anthropic SDK had no API key → switched to `claude -p` which inherits Claude Code auth

### Also shipped: DV-465 (Eclipse Chat context overflow)

Separate from orchestrator work — fixed a production bug in `core_api`:
- **Root cause**: `get_dataset_description` returned entire PBI schema (~200K tokens) in one tool response
- **Fix**: Split into `get_dataset_description` (overview, <5K tokens) + `get_table_columns` (per-table, lazy)
- **Also fixed**: `validate_dataset_request` accessing removed `.fields`, Dockerfile `FROM ubuntu` → `FROM ubuntu:22.04` (dotnet-sdk-8.0 apt install broken on Noble)
- **PR**: ALDC-io/core_api#236 — all CI checks green, awaiting team approval for merge
- **Deploy**: auto-deploys to staging on merge to `eclipse-2.1`, then manual slot swap to production

## Phase 7c: Next Session Scope (planned)

**Orchestrator hardening:**
- Worktree cleanup on pipeline delete
- Session count sprawl from Zeus chat (switch to persistent session)
- Stale pipeline detection + auto-cleanup
- Error recovery (restart from failed stage, not from scratch)

**Client onboarding pipeline type:**
- Wizard input → Snowflake provisioning → connector registration → credential collection → first data landing
- Link to client portal for credential submission
- Dependency tracking table (what unblocks what)

**Deploy board — live promotion:**
- Real QA → UAT → Prod slot swaps via Azure API
- Per-environment validation gates
- Rollback support

**Snowflake integration:**
- Visualization/validation of landing tables
- Row count dashboards per connector
- Schema drift detection

**Bulk migration:**
- Bulk connector migration: select N connectors from inbox → auto-create connector-migration pipelines for all → execute in parallel (max_parallel=8)
- Bulk credential provisioning: scan client-registry.json for all unpprovisioned credentials → batch-create credential-provision pipelines
- CSV/JSON import: upload a manifest of connectors+creds → orchestrator creates pipelines for each row
- Migration dashboard: track progress across all connectors for a client (e.g. Navira: 6/31 migrated, 25 remaining)

**UI improvements:**
- Cleaner design pass
- Client portal integration for credential pull
- Pipeline session linking (click session → see full pipeline context)
- Dependency graph visualization (which tickets block which)

## See Also

- [[phase-6-zeus]] — All features complete (prerequisite)
- [[phase-0-design-system]] — Where it started
- Plan file: `~/.claude/plans/kind-kindling-cascade.md` — end-to-end pipeline architecture
- Wiki deployment runbook: [[../../processes/deployment/eclipse-azure-deployment]] — core_api deploy steps
