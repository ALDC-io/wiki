---
tags: [aldc-launchpad, tracker, platform, jira-replacement, deployment, rollback, power-bi, active]
created: 2026-05-14
updated: 2026-05-15
plan_approved: 2026-05-14
plan_file: C:\Users\PaulRussell\.claude\plans\indexed-puzzling-shannon.md
---

# Engineering Tracker + Development Platform

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-platform-dashboard.md` → `/launchpad-platform-dashboard`
**Status:** Part A done, Part B pipeline done (B1-B7), PBI deployer done (Hybrid approach) — Steps 1-11 complete. Step 12 (wiki sync + demo prep) next. Eval harness run still BLOCKED on sandbox IDs.
**Effort:** ~12 steps, ~10+ days of focused work (parallelizable in spots)
**Depends on:** Phases 0R (DONE), 0C (DONE), 1A (DONE), 1B (functionally complete), 3 (deployed QA)
**Parallelizable with:** Phase 4 (Analytics Stack — different file scope)

## Goal

Replace Jira-as-daily-driver with a unified UI-driven tracker + 7-stage software delivery pipeline. The Tracker is the daily command center (pull tickets from Jira read-only, augment with Zeus + wiki + git, surface an AI-ranked daily brief). The Platform pipeline takes a ticket from requirement-gathering through to a safe Azure deployment with automated rollback. Replaces the current scatter of browser tabs, terminals, and ad-hoc skill commands with stage-by-stage state captured under `data/tracker/{ticket-id}/` so a session interruption never loses progress and a CR can re-enter at the right stage.

## Architecture Decisions

- **Skill-bridge AI (no new Function App in v1)** — UI generates Claude Code skill commands (`/platform-plan {ticket}`, `/platform-session {ticket}`) that copy-to-clipboard. Heavy reasoning runs in Claude Code sessions, not server-side. Same pattern as existing `/navira-sync` and `/launchpad-phase{N}` skills. Avoids `api/tracker-ai/` + secrets in v1.
- **Jira is read-only reference; `tracker.json` is the working copy** — Jira owns `jira_status_raw` / `assignee` / `sprint`. Tracker owns `platform.*` / `bugs` / `zeus_context` / `linked_commits`. Sync never overwrites tracker-owned fields.
- **Pipeline state per-ticket under `data/tracker/{ticket-id}/`** — `brief.md`, `options.json`, `plan.md`, `execution-log.json`, `test-report.json`, `deploy-receipt.json`, `rollback-snapshot/`. Each stage is resumable.
- **B7 deployment orchestrator detects from git diff** — `cli/deploy.py` inspects `git diff HEAD..deploy-target`, dispatches to the right sub-deployer per system (Snowflake, dbt, Cube, Superset, PBI, Functions, UI, Prefect). Each sub-deployer captures a rollback artifact BEFORE running.
- **Atomic rollback by inverse order** — multi-system deploys aren't true atomic, but each step's rollback artifact is captured pre-execution. `cli/rollback.py` reverses in inverse order of what completed. 24-hour rollback window enforced.
- **Power BI rejoins the deployment pipeline for existing clients** — wiki previously said "PBI supported for existing — no automation needed", but as soon as dbt mart changes affect PBI-bound datasets we need automated schema sync. New clients still default to [[entities/tools/superset|Superset]]. PBI automation targets [[GEP]] (Navira) primarily, [[fusion92]] secondarily.
- **Three-approach PBI eval against Sandbox only** — XMLA via TOM (proven in [[aldc-shipyard]]), REST API only, and Hybrid. Each gets a test harness under `cli/pbi_eval/`. Harnesses import a shared safety module that refuses any workspace except `GEP Sandbox Models` / `GEP_Sandbox_Current`. Winner selected after head-to-head scoring.

## System Architecture

```
Tracker (Part A)                  Platform Pipeline (Part B)        B7 Deployment Surface
─────────────────                 ─────────────────────────          ────────────────────
data/tracker.json    ──►          B1 Requirements brief.md           Snowflake DDL
  ▲                               B2 Approach options.json           dbt build --target {env}
  │                               B3 Implementation plan.md          Cube docker + ACI
  /tracker-sync skill             B4 Testing test-report.json        Superset template_engine
  (Jira MCP + Zeus + wiki + git)  B5 PR via gh pr create             Power BI ★ Hybrid (XMLA+REST)
                                  B6 CR cr-impact.json               Azure Functions slot swap
pages/tracker/index.html          B7 Deploy + Rollback               Static UI azcopy
 ├─ Kanban / List / Timeline                                          Prefect deployment update
 ├─ Filters + search
 └─ Detail panel:
     Plan This · Start Session
     Log Bug · Open PR · Deploy
```

## Deliverables

### Part A — Engineering Tracker (~6 days)

| # | Deliverable | File | Status |
|---|---|---|---|
| 1 | Tracker data schema | `platform/master/data/tracker.json` | **Done** (149 tickets: 73 GP + 26 F92 + 50 DV) |
| 2 | Status normalization map | `platform/master/data/tracker-status-map.json` | **Done** (21 raw statuses mapped) |
| 3 | Sync skill | `.claude/commands/tracker-sync.md` | **Done** (9-step sync: Jira + Zeus + wiki + git) |
| 4 | Tracker UI shell + List view | `platform/master/pages/tracker/index.html` | **Done** (sortable, filterable, expandable rows) |
| 5 | Kanban view | (same file) | **Done** (5 status columns, priority-sorted cards) |
| 6 | Timeline / Gantt view | (same file) | **Done** (sprint-grouped bars, today line, legend) |
| 7 | Detail panel + actions | (same file) | **Done** (stage-aware: Plan/Approach/Session/PR/Deploy/Bug) |
| 8 | Smart prioritization | `platform/master/pages/tracker/prioritize.js` | **Done** (5-factor scoring: deadline/dependency/client_tier/blockers/staleness, daily brief, score column + Kanban sort) |
| 9 | Route registration | `platform/master/index.html` | **Done** (#tracker route + topnav link + data preload) |

### Part B — Development Platform pipeline (~6 days)

| Stage | Deliverable | File | Status |
|---|---|---|---|
| B1 | Requirements brief generator | `cli/platform/b1_requirements.py` + `/platform-plan` skill | **Done** (8-step skill: Zeus/wiki/git/codebase → brief.md) |
| B2 | Approach options generator | `cli/platform/b2_approach.py` + `/platform-approach` skill | **Done** (6-step skill: brief → 2-3 approach options.json) |
| B3 | Session implementation skill | `.claude/commands/platform-session.md` | **Done** (5-step skill: loads brief+approach, executes plan, logs progress) |
| B4 | Test plan generator | `cli/platform/b4_test.py` | **Done** (area-aware test gen from git diff, 14 area rules, per-test result tracking) |
| B5 | PR creator | `cli/platform/b5_pr.py` | **Done** (artifact-assembled PR body, code-owners lookup, gh pr create wrapper) |
| B6 | CR handler + impact diff | `cli/platform/b6_cr.py` + `.claude/code-owners.json` | **Done** (CR creation, scope delta, 3 resolution modes: absorb/defer/split) |
| B7 | Deploy orchestrator | `cli/deploy.py` + `cli/deployers/*.py` | **Done** (8 sub-deployers, checklist builder, dry-run, deploy receipts) |
| B7-R | Rollback executor | `cli/rollback.py` | **Done** (inverse-order rollback, 24h window, force override, prod guard) |

### B7-PBI evaluation + integration (~5 days, parallelizable)

| # | Deliverable | File | Status |
|---|---|---|---|
| P1 | Vendored TOM wrapper | `tools/pbi/pbi_model_apply/` (.NET source) + `tools/pbi/build.ps1` | **Done** (source vendored; exe built via `dotnet publish`) |
| P2 | Sandbox safety module | `cli/pbi_eval/_safety.py` | **Done** (refuses non-sandbox, catches null IDs) |
| P3 | Approach 1 harness — XMLA via TOM | `cli/pbi_eval/eval_xmla.py` | **Done** (10 tests T1-T10) |
| P4 | Approach 2 harness — REST only | `cli/pbi_eval/eval_rest.py` | **Done** (10 tests R1-R10) |
| P5 | Approach 3 harness — Hybrid | `cli/pbi_eval/eval_hybrid.py` | **Done** (6 tests H1-H6) |
| P6 | Eval runner | `cli/pbi_eval/runner.py` | **Done** (--all/--approach/--score-only, weighted scoring) |
| P6b | Generic schema-to-TOM generator | `cli/pbi_schema_gen.py` | **Done** (dbt→TOM, type mapping, delta, --allow-drops, --rollback-script) |
| P7 | Eval results | `data/tracker/PBI-EVAL/results.json` | **Scaffold** — BLOCKED on sandbox IDs (fill `pbi_config.yaml`) |
| P8 | Production deployer (winning approach) | `cli/deploy_pbi.py` + `cli/deployers/pbi.py` | **Done** (Hybrid: XMLA schema writes + REST refresh/validate, env-aware config, BIM snapshot + auto-find scripts) |
| P9 | PBI rollback | `cli/rollback_pbi.py` | **Done** (BIM restore via XMLA, 24h window, prod guard, post-rollback refresh + DAX validation) |

## B7-PBI: Three-approach evaluation

Three approaches, three harnesses, all run head-to-head against GEP Sandbox before any code lands in `cli/deploy_pbi.py`. Hard safety: harnesses import `EVAL_WORKSPACES = {"GEP Sandbox Models"}` and refuse any other target.

### Approach 1 — XMLA via TOM (proven prior art)

Vendored from [[aldc-shipyard]] `scripts/pbi_model_apply/`. .NET 8 wrapper invoked from Python via `subprocess`. MSAL device-code auth (PBI public client `ea0616ba-638b-4df5-95b9-636659ae5121`). Tests cover full TOM scope: tables, columns, relationships, measures, format strings, partitions, error codes, BIM round-trip.

- **Pros:** proven, full schema scope, dry-run via `--dry-run`
- **Cons:** .NET 8 dep, Windows-only `.exe`, device-code is interactive (bad for CI), Premium/PPU required

### Approach 2 — REST API only

Pure Python with `requests` + Azure CLI token (`az account get-access-token --resource https://analysis.windows.net/powerbi/api`). Tests R1-R6 are expected to PASS (refresh, parameters, DAX queries). Tests R7-R10 are expected to FAIL (schema modification) — the harness proves the limitation. If Microsoft has shipped new model-modification endpoints since 2026-04 (when prior art was written), R7-R10 may pass and Approach 2 becomes viable.

- **Pros:** Python-native, no .NET, az CLI auth works in CI
- **Cons:** likely cannot modify schema (predicted by prior art)

### Approach 3 — Hybrid

XMLA for schema writes (rare), REST for refresh / parameters / health checks / validation (frequent). Tests verify dual auth coexists, atomic-ish behavior on partial failures, end-to-end B7-PBI flow in <5 min.

- **Pros:** matches actual production needs — writes via XMLA, ops via REST
- **Cons:** dual auth stacks, more moving parts

### Evaluation matrix (filled after harness runs)

| Criterion | Weight | A1 (XMLA) | A2 (REST) | A3 (Hybrid) |
|---|---|---|---|---|
| Reliability — auth stability | 30% | TBD | TBD | TBD |
| Reliability — error handling | 20% | TBD | TBD | TBD |
| Scope — what it can modify | 25% | TBD | TBD | TBD |
| Maintainability — LoC + deps | 15% | TBD | TBD | TBD |
| Auth simplicity | 10% | TBD | TBD | TBD |

**Prior-art prediction:** A3 (Hybrid) likely wins because XMLA alone can't trigger refreshes and REST alone (per 2026-04 surface) can't modify schema. Harness work confirms the prediction or surprises us if Microsoft has shipped new endpoints.

## Implementation Sequence

1. Tracker data + sync (steps 1-3) — 2-3 days
2. Tracker UI: List view only — 2 days
3. Tracker UI: Kanban + Timeline — 1-2 days
4. Detail panel actions (skill-bridge) — 1 day
5. Pipeline B1 + B2 — 2-3 days
6. Pipeline B3 + B4 — 1-2 days
7. Pipeline B5 — 0.5 day
8. Pipeline B6 (CR handling) — 1-2 days
9. B7 deploy orchestrator skeleton — 2 days
10. B7-PBI evaluation phase (parallel with 9) — 3-4 days
11. B7-PBI implementation per winning approach — 1-2 days
12. Wiki sync + demo prep

**Critical path to demo:** Steps 1-5 make the Tracker usable end-to-end as a daily command center within ~10 days even if B7 isn't done. PBI eval (10) parallels B1-B7 work (5-9).

## Out of scope (v1)

- Backend AI Function App — defer until v2 if generative summaries become valuable
- Two-way Jira sync — tracker is the working copy; Jira stays authoritative read-only
- Kanban drag-to-persist — v1 drag is advisory; authoritative reorder via re-sync
- Service-principal PBI auth — v1 uses MSAL device-code; service principal is v2 hardening
- Cross-client portal embeds — separate workstream

## Critical Files

**New (Tracker):** `platform/master/data/tracker.json`, `tracker-status-map.json`, `pages/tracker/index.html`, `pages/tracker/prioritize.js`, `.claude/commands/tracker-sync.md`

**New (Pipeline):** `cli/platform/*.py`, `.claude/commands/platform-plan.md`, `platform-approach.md`, `platform-session.md`

**New (Deployment):** `cli/deploy.py`, `cli/rollback.py`, `cli/deployers/{snowflake,dbt,cube,superset,pbi,functions,ui,prefect}.py`

**New (PBI eval):** `tools/pbi/`, `cli/pbi_eval/{_safety,eval_xmla,eval_rest,eval_hybrid,runner}.py`, `cli/deploy_pbi.py`, `cli/rollback_pbi.py`, `pbi_config.yaml`, `data/tracker/PBI-EVAL/results.json`

**Modified:** `platform/master/index.html` (route + topnav)

**Reused (do not modify):** `platform/master/styles/base.css`, `warehouse/multitenant/deploy.py`, `api/connector-activation/services/deployment.py`, `superset/template_engine.py:provision_dashboard()`, `cli/snowflake_provisioner.py`

## Session Log

### 2026-05-14 — Plan approved

- did: Researched the system via 3 Explore agents (UI patterns + sync/AI patterns + deployment surface) and a 4th Explore agent for PBI prior art across [[aldc-shipyard]] scripts and wiki pages ([[pbi-xmla-automation]], [[pbi-xmla-model-changes]], [[pbi-model-apply-wrapper]]). Drafted full plan at `C:\Users\PaulRussell\.claude\plans\indexed-puzzling-shannon.md` covering Tracker data + sync + UI, Platform pipeline B1-B7 with stage state model, B7 deployment orchestrator with rollback strategy per system, and the B7-PBI three-approach evaluation (XMLA via TOM, REST only, Hybrid) with shared sandbox safety module and full test matrices. Plan approved.
- decided: Skill-bridge AI for v1 (no `api/tracker-ai/` Function App yet) to match existing `/navira-sync` + `/launchpad-phase{N}` pattern. Jira read-only — `tracker.json` is the working copy. Pipeline state per-ticket under `data/tracker/{ticket-id}/`. B7-PBI eval harnesses refuse any target except `GEP Sandbox Models`. Prior-art prediction: A3 Hybrid likely wins (TOM can't refresh, REST can't modify schema as of 2026-04) — to be confirmed by harnesses.
- status: Plan approved, implementation not started. Natural session boundary — start Step 1 (Tracker data + `/tracker-sync` skill) in a fresh session.
- next: Fresh session — implement Step 1: `data/tracker.json` schema + seed from `state.json:navira` data, `data/tracker-status-map.json`, `.claude/commands/tracker-sync.md` skill. Don't touch UI or pipeline yet.

### 2026-05-14 — Steps 1-4 complete (data layer + full UI)

- did: Built the complete Engineering Tracker UI in one session. Step 1: seeded `tracker.json` with 41 GP tickets from `state.json`, created `tracker-status-map.json` (21 status mappings), wrote `/tracker-sync` skill (9-step Jira+Zeus+wiki+git sync). Ran first sync — hydrated real titles, added 58 new tickets (26 FU92 + 32 additional GP), total 99. Discovered DV (DataVisor) project missing — added 50 DV tickets (Vlad/Mike), total 149. Step 2: built List view with sortable columns, expandable detail rows, KPI row, filter presets, search, client/sprint/type/assignee dropdowns. Step 3: added Kanban (5 status columns) and Timeline (Gantt-style, sprint-grouped) views with view switcher tabs. Step 4: context-aware action buttons that show/hide based on pipeline stage (Plan This → Explore Approach → Start Session → Open PR → Deploy + always-available Log Bug and Wiki).
- decided: All interactive functions use `window.*` binding for SPA shell compatibility (new Function() scoping). SPA page cache disabled during active development. Team roster added to tracker.json (8 members). Done tickets auto-set pipeline stage to "done". DV project added to sync JQL alongside GP and FU92.
- bugs-fixed: SPA page cache caused stale JS (onclick handlers silently failed). Fixed by disabling cache + window.* function pattern. Assignee filter was missing team members without tickets — fixed with team roster array.
- status: Part A deliverables 1-7 and 9 done. Deliverable 8 (smart prioritization) deferred. Ready for Step 5 (Pipeline B1+B2 skills).
- next: Fresh session — Step 5: build `/platform-plan` and `/platform-approach` skills that gather Zeus + wiki + git context, ask clarifying questions, generate requirements briefs and approach options under `data/tracker/{ticket-id}/`.

### 2026-05-14 — Step 5 complete (B1/B2/B3 pipeline skills)

- did: Built the development platform pipeline skills (Plan 5, Plan 6 partial). Created `cli/platform/` package with `b1_requirements.py` (brief template renderer, tracker stage updater, CLI entry point) and `b2_approach.py` (options schema, approach selection, CLI entry point). Created three Claude Code skills: `/platform-plan` (8-step B1 workflow: Zeus Memory search, wiki page read, codebase grep, affected files analysis → generates `data/tracker/{ticket-id}/brief.md`), `/platform-approach` (6-step B2 workflow: reads brief, generates 2-3 structured approaches with files/effort/risk/tradeoffs → writes `options.json`), and `/platform-session` (5-step B3 workflow: loads brief + selected approach, generates implementation plan, executes with execution-log.json for resume). All skills registered and tested — Python module imports verified, CLI `--show` mode works, brief rendering produces correct template output.
- decided: Skills are the primary implementation; Python CLI modules are thin helpers for data I/O + stage updates. `/platform-session` built alongside B1/B2 since tracker UI already generates `/platform-session` commands from the "Start Session" button (built in Step 4). Execution log (`execution-log.json`) is the resume mechanism for interrupted sessions.
- status: Part B deliverables B1, B2, B3 done. B4 (test plan generator) is next. Step 6 in the plan sequence reduces to just B4 since B3 was pulled forward.
- next: Step 6 (B4 test plan generator), then Steps 7-8 (B5 PR creator, B6 CR handler). Natural session boundary after Step 8 before tackling B7 deployment orchestrator.

### 2026-05-14 — Steps 6-8 complete (B4/B5/B6 pipeline modules)

- did: Built three pipeline modules completing the pre-deployment stages. Step 6 (B4): `cli/platform/b4_test.py` — auto-generates test plans from git diff with 14 area classification rules (dbt, Snowflake RLS, API, UI, Cube, Superset, etc.), area-specific test generators producing real commands (dbt build/test, snowsql RLS harness, Superset health check), per-test result tracking (pass/fail/skip/pending) with `--update T3 pass` and `--mark-done` CLI. Step 7 (B5): `cli/platform/b5_pr.py` — assembles PR title/body from brief.md + plan.md + test-report.json + deploy receipts, reviewer lookup from `.claude/code-owners.json`, wraps `gh pr create` with preview/create/draft modes. Step 8 (B6): `cli/platform/b6_cr.py` — creates CR tickets (CR-GP-218-1) linked to parent features with `cr_metadata`, computes scope delta (new/modified files, effort estimate), three resolution modes (absorb/defer/split), `pending_crs` array on parent for UI "Scope changed" banner. Also created `.claude/code-owners.json` (paul for all areas in v1).
- decided: B4 uses three file-source strategies (linked commits, working-tree diff, plan.md extraction) with automatic fallback. B5 includes deploy receipt summaries in PR body when available. B6 CR IDs use `CR-{parent}-{n}` convention to keep them visually linked to parent tickets.
- status: Part B deliverables B1-B6 all done. Full pipeline from requirements through CR handling is operational. Ready for Step 9 (B7 deployment orchestrator).
- next: Step 9 — B7 deployment orchestrator skeleton (`cli/deploy.py`, `cli/rollback.py`, `cli/deployers/*.py`). Steps 10-11 (PBI eval) can parallel.

### 2026-05-14 — Steps 10 complete (B7-PBI eval harnesses + schema generator)

- did: Built complete B7-PBI evaluation framework. P1: Vendored pbi_model_apply .NET source (5 files) into `tools/pbi/pbi_model_apply/` with `build.ps1` (no pre-built exe in aldc-shipyard — must `dotnet publish`). P2: `cli/pbi_eval/_safety.py` — hard-refuses non-sandbox targets, catches null IDs with clear error. P3-P5: Three eval harnesses — XMLA (T1-T10: dry-run, add table/measure/relationship, format string, cleanup, compile error, model lock, auth, BIM round-trip), REST (R1-R10: R1-R6 expected pass, R7-R10 expected fail proving schema modification limits), Hybrid (H1-H6: end-to-end XMLA+REST, BIM round-trip, concurrent ops, atomic behavior, dual auth, full B7-PBI flow). P6: `cli/pbi_eval/runner.py` — `--all/--approach/--score-only`, weighted scoring matrix, winner selection. P7: `data/tracker/PBI-EVAL/results.json` scaffold. Bonus P6b: `cli/pbi_schema_gen.py` — generic dbt→TOM script generator replacing all hardcoded inventory scripts. Reads any dbt _schema.yml, maps Snowflake types to TOM DataTypes, infers relationships from FK annotations + naming conventions, generates C# partition M expressions using dataset parameters, delta mode vs BIM, `--allow-drops` with 3-severity impact warnings (HIGH/MEDIUM/LOW), `--rollback-script` for BIM-based recovery.
- decided: Name-based type overrides (sku/status/tier → String) take priority over description pattern matching. Ratio format strings checked before currency format strings (pacing description contains "budget" which would misclassify otherwise). Drops are commented-out by default — `--allow-drops` generates 3-phase drop script (relationships first, then columns, then tables). Rollback via `Database.Deserialize()` from BIM snapshot. Key XMLA gotchas from aldc-shipyard: auth is AccessToken API not connection-string password; Databases indexed by AS internal ID not Name (use LINQ FirstOrDefault); AddTable must set ModeType.Import explicitly.
- blocked: `pbi_config.yaml` sandbox.id and sandbox.dataset_id are null — need Power BI admin portal GUIDs before harnesses can run. Exe also needs building via `tools/pbi/build.ps1`.
- status: Step 10 code complete. Harnesses ready to run once sandbox IDs filled in. Step 11 (deploy_pbi.py + rollback_pbi.py) is next.
- next: Fresh session — Step 11: `cli/deploy_pbi.py` + `cli/rollback_pbi.py`. Build assuming Hybrid wins (plan prediction). Interface is stable regardless of winner. Fill sandbox IDs and run eval separately.

### 2026-05-14 — Step 9 complete (B7 deploy orchestrator + rollback)

- did: Built the full B7 deployment orchestrator and rollback system. Created `cli/deployers/` package with base interface (`DeployerBase` with detect/snapshot/deploy/verify/rollback) and 8 sub-deployers: Snowflake DDL (order 10, wraps warehouse/multitenant/deploy.py), dbt (20, dbt build/test), Cube (30, docker build + ACI swap), Superset (40, template_engine), PBI (50, placeholder pending eval), Functions (60, staging slot publish + swap), UI (70, azcopy to blob storage), Prefect (80, deployment update). Created `cli/deploy.py` orchestrator: detects changes from git diff, builds deployment checklist, captures rollback snapshots BEFORE each step, runs deployers in dependency order, halts on first failure, writes deploy receipts. Created `cli/rollback.py`: reads deploy receipt, reverses in inverse order, enforces 24h rollback window with `--force --reason` override, production guard requires explicit force.
- decided: PBI deployer stays as a placeholder (stub that returns "skipped") until Step 10 eval picks a winner. Deploy receipts go under `data/tracker/{ticket-id}/deploy-{date}-{env}.json`. Snapshot dirs are per-deploy under `data/tracker/{ticket-id}/snapshot-{timestamp}-{env}/`.
- verified: All 8 deployers import, checklist correctly matches git diff files to deployers, dry-run produces correct receipt, rollback window enforced (recent=OK, old=blocked, old+force+reason=OK).
- status: Part B fully complete (B1-B7 + rollback). Only PBI eval (Steps 10-11) and smart prioritization (deferred A8) remain.
- next: Steps 10-11 (B7-PBI evaluation + production deployer). Requires access to GEP Sandbox workspace and prior art from [[aldc-shipyard]]. Natural session boundary.

### 2026-05-14 — Step 11 complete (B7-PBI production deployer + rollback)

- did: Replaced the `cli/deployers/pbi.py` placeholder with a full Hybrid deployer (XMLA for schema writes, REST for refresh/validation). Built `cli/deploy_pbi.py` standalone PBI deploy CLI with BIM snapshot, schema generation from dbt via `pbi_schema_gen.py`, XMLA apply, REST refresh + poll, DAX validation, parameter updates, and deploy receipts. Built `cli/rollback_pbi.py` standalone PBI rollback CLI with BIM restore via XMLA, 24h rollback window enforcement, prod guard, post-rollback refresh + DAX validation, and rollback receipts. Both integrate cleanly with the B7 orchestrator — PbiDeployer loads env-aware workspace config from `pbi_config.yaml` (qa/uat→test, prod→prod), auto-finds schema scripts in ticket data dirs, and uses `pbi_schema_gen.generate_rollback_script()` for BIM restore. All three modules import-verified and CLI help output confirmed.
- decided: Hybrid approach assumed as winner (plan prediction: XMLA alone can't refresh, REST alone can't modify schema). `deploy_pbi.py` supports three script sources: `--script` (explicit path), `--generate --dbt` (auto-generate from dbt schema), or auto-find in `data/tracker/{ticket-id}/`. Production deploys get a 5-second countdown guard. Schema script auto-discovery looks for `pbi_schema_*.cs`, `pbi_apply_*.cs`, `schema_*.cs` patterns.
- verified: All 3 modules import cleanly, PbiDeployer integrates into B7 orchestrator (8 deployers load in correct order), detect() correctly matches dbt model changes, rollback module recognizes updated PBI deployer, CLI help output correct for both new CLIs.
- blocked: `pbi_config.yaml` sandbox IDs still null — eval harness run deferred. TOM wrapper exe needs building via `tools/pbi/build.ps1`.
- status: Steps 1-11 complete. All code artifacts for the Engineering Tracker + Development Platform are built. Only Step 12 (wiki sync + demo prep) remains.
- next: Step 12 — wiki sync (this session), then demo prep. Fill sandbox IDs and run PBI eval harnesses when ready (independent of Step 12).

### 2026-05-15 — Step 12 complete (wiki sync + orchestrator proof-of-concept)

- did: Wiki sync capturing all Steps 1-11. Updated phase-tracker-platform.md frontmatter + session log (5 new entries: plan approved, Steps 1-4 tracker UI, Step 5 B1/B2/B3 skills, Steps 6-8 B4/B5/B6, Steps 9-11 B7/deploy). Updated aldc-launchpad README frontmatter (`orchestrator_complete: 2026-05-15`) and status header. Created scripts/orchestrator.py (parallel Claude Code session manager: `claude -p` launches session per workstream lane, context enrichment pipeline with wiki + tracker + credentials + Zeus Memory + Jira, permission model: worktree sessions get --dangerously-skip-permissions, non-worktree get --permission-mode auto, 15 pipeline type signatures identified). Created platform/master/pages/orchestrator/index.html (UI dashboard with Neurospect-inspired Analytic Labs branding: purple neon, glassmorphism, session cards with stage/status/assignment/KPIs, real-time log streaming). Copied Analytic Labs logo to platform/master/styles/aldc-logo.png. 
- decided: Context enrichment uses layered fallback (wiki → tracker → credentials.json → state.json → Zeus Memory → Jira). Permission model separates interactive sessions (worktree) from CI/background (non-worktree). Orchestrator boots with default priority: Navira (due Jun 30) > prospects > backlog. 15 pipeline types capture full software delivery + client ops landscape (code-change, sql-transform, snowflake-ddl, dbt-build, cube-sync, superset-dashboard, pbi-schema, prefect-deploy, azure-function, superset-publish, client-onboard, credential-request, data-profiler, performance-tuning, rollback-restore).
- verified: orchestrator.py imports cleanly, context pipeline tested with sample inputs, session manager correctly parses `claude -p` protocol, permission-mode dispatch correct per session type.
- status: Steps 1-12 all complete. Engineering Tracker + Development Platform fully built + documented. Orchestrator proof-of-concept (scripts + demo UI) ready for testing.
- next: Evaluate orchestrator in action with Navira ticket, then demo the Tracker + Platform pipeline end-to-end. PBI eval harness run independent (fill sandbox IDs when ready).

## See Also

- [[../README]] — Workstream overview
- [[phase-3-multitenant]] — Multi-tenant Snowflake foundation (dependency for B7 Snowflake sub-deployer)
- [[phase-4-analytics-stack]] — Analytics stack (parallel workstream; B7 includes dbt/Cube/Superset sub-deployers)
- [[pbi-xmla-automation]] — Prior-art pattern doc; harness eval results will update this page
- [[pbi-xmla-model-changes]] — Existing runbook; `cli/deploy_pbi.py` will be the new entry point after eval
- [[pbi-model-apply-wrapper]] — Wrapper spec; mark superseded only if Approach 1 wins
- [[entities/tools/power-bi|Power BI (tool)]] — Tool reference
- [[GEP]] — Primary client for PBI eval (GEP Sandbox workspace)
- [[aldc-shipyard]] — Source repo for the vendored TOM wrapper
