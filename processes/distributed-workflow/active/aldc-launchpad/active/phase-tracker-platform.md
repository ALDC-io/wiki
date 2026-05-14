---
tags: [aldc-launchpad, tracker, platform, jira-replacement, deployment, rollback, power-bi, active]
created: 2026-05-14
updated: 2026-05-14
plan_approved: 2026-05-14
plan_file: C:\Users\PaulRussell\.claude\plans\indexed-puzzling-shannon.md
---

# Engineering Tracker + Development Platform

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-platform-dashboard.md` → `/launchpad-platform-dashboard`
**Status:** Plan approved — implementation not started
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
  (Jira MCP + Zeus + wiki + git)  B5 PR via gh pr create             Power BI ★ (eval-pending)
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
| 1 | Tracker data schema | `platform/master/data/tracker.json` | Planned |
| 2 | Status normalization map | `platform/master/data/tracker-status-map.json` | Planned |
| 3 | Sync skill | `.claude/commands/tracker-sync.md` | Planned |
| 4 | Tracker UI shell + List view | `platform/master/pages/tracker/index.html` | Planned |
| 5 | Kanban view | (same file) | Planned |
| 6 | Timeline / Gantt view | (same file) + inline SVG | Planned |
| 7 | Detail panel + actions | (same file) | Planned |
| 8 | Smart prioritization | `platform/master/pages/tracker/prioritize.js` | Planned |
| 9 | Route registration | `platform/master/index.html` | Planned |

### Part B — Development Platform pipeline (~6 days)

| Stage | Deliverable | File | Status |
|---|---|---|---|
| B1 | Requirements brief generator | `cli/platform/b1_requirements.py` + `/platform-plan` skill | Planned |
| B2 | Approach options generator | `cli/platform/b2_approach.py` + `/platform-approach` skill | Planned |
| B3 | Session implementation skill | `.claude/commands/platform-session.md` | Planned |
| B4 | Test plan generator | `cli/platform/b4_test.py` | Planned |
| B5 | PR creator | `cli/platform/b5_pr.py` | Planned |
| B6 | CR handler + impact diff | `cli/platform/b6_cr.py` + UI quick-entry | Planned |
| B7 | Deploy orchestrator | `cli/deploy.py` + `cli/deployers/*.py` | Planned |
| B7-R | Rollback executor | `cli/rollback.py` | Planned |

### B7-PBI evaluation + integration (~5 days, parallelizable)

| # | Deliverable | File | Status |
|---|---|---|---|
| P1 | Vendored TOM wrapper | `tools/pbi/pbi_model_apply.exe` + .NET source | Planned (copy from [[aldc-shipyard]] `scripts/pbi_model_apply/`) |
| P2 | Sandbox safety module | `cli/pbi_eval/_safety.py` | Planned (refuses non-Sandbox workspaces) |
| P3 | Approach 1 harness — XMLA via TOM | `cli/pbi_eval/eval_xmla.py` | Planned (10 tests: T1-T10) |
| P4 | Approach 2 harness — REST only | `cli/pbi_eval/eval_rest.py` | Planned (10 tests: R1-R10) |
| P5 | Approach 3 harness — Hybrid | `cli/pbi_eval/eval_hybrid.py` | Planned (6 tests: H1-H6) |
| P6 | Eval runner | `cli/pbi_eval/runner.py` | Planned (runs all 3, scores matrix) |
| P7 | Eval results | `data/tracker/PBI-EVAL/results.json` | Planned (TBD after harness runs) |
| P8 | Production deployer (winning approach) | `cli/deploy_pbi.py` | Planned (interface stable regardless of winner) |
| P9 | PBI rollback | `cli/rollback_pbi.py` | Planned (consumes BIM snapshot) |

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
