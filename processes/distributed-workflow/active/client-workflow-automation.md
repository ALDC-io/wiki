---
tags: [distributed-workflow, active, client-workflow-automation]
aliases: [Client Workflow Automation Tracker, Sandbox Feature Delivery Tracker]
sources: []
created: 2026-04-18
updated: 2026-04-29 (repo renamed aldc-automation → aldc-shipyard)
---

# Client Workflow Automation — Workstream Tracker

Design (not yet build) an automated, sandboxed feature-delivery flow for client work — primarily targeting GEP, where the painful step is **manual deploy of warehouse SQL + manual QA via validation queries and eyeballing**. End goal is requirements → scoped → designed → implemented → reviewed → tested → production-ready, with as much of the loop autonomous, secure, and well-tested as is realistic given the Snowflake + Power BI constraints.

## Goal

Today's session(s) produce a **written design** (no code yet) covering:

1. A clear map of the current GEP feature lifecycle (requirements → branch → SQL → manual deploy → eyeball QA → PBI refresh → handoff), with the highest-friction steps explicitly named.
2. The 2–3 highest-leverage automation candidates, ranked by impact × feasibility.
3. For the top candidate: a sketch of how a sandbox could host the design → implement → review → test → ship loop, given that production reads through Power BI's data model on a manually-deployed warehouse. Includes a candid section on why a true ephemeral sandbox might not be possible and what the practical fallback is.
4. A short list of automation primitives we already have (Snowflake test schemas, GP-207 prod→test data share, flight-check, branch model) so the design composes from existing pieces rather than greenfield.

"Done for today" = `entities/projects/workflow-automation.md` exists with the design above, and `concepts/patterns/sandbox-feature-delivery.md` captures the reusable pattern (or explicitly defers it as future work).

## Lane

Wiki: ALDC

Owned paths:
- `entities/projects/workflow-automation.md` (new)
- `concepts/patterns/sandbox-feature-delivery.md` (new)

**Read-only outside the lane** — do NOT edit existing GEP runbooks, deployment processes, or branching docs in this session. If the design implies changes to those, write a *Cross-Lane Request* and surface to Paul.

## Required Context

Read in parallel at boot:

- [[GEP]] — client overview, environment model, manual-deploy reality.
- [[gep-snowflake-pbi-deployment]] — the 11-phase end-to-end runbook + 7 documented pitfalls. This is the friction surface we're trying to reduce.
- [[flight-check]] — current operational validation; the "eyeball QA" we want to replace.
- [[git-branching-strategy]] — happy-path, user-test-fixes, hotfixes-to-prod; commit/release conventions.
- [[ticket-breakdown-to-ship]] — the generic ticket lifecycle the new design has to compose with.
- [[client-release-checklist]] — generic per-release gating.
- [[data-share-pattern]] and [[snowflake-data-share-refresh]] — the test environment relies on the prod→test share (GP-207), so any sandbox design has to respect share semantics.

Optional but useful when designing the sandbox section:

- [[GP-207]] — the prod→test data share work; explains what "test environment" means today.
- [[GP-208]] — recent ticket that surfaced manual-QA pain (eyeball validation, frozen-share incident).
- [[accumulating-source-tables]] — moving-target QA workflow Paul already developed; relevant prior art.

## Plan-Mode Rule

**Every session in this workstream is plan-mode-first** until a written design exists in `entities/projects/workflow-automation.md`. The scope is genuinely fuzzy and there are multiple viable approaches (true ephemeral sandbox, branch-isolated test schemas, snapshot-based testing, AI-driven validation against expected datasets, etc.). Don't start writing the design page until Paul has approved the structure.

After the design exists, future sessions that *implement* parts of it should plan-mode each new component (per the workstream Plan-Mode Rule defaults).

## Session Log

_Initial bootstrap — no work executed in this session._

### 2026-04-26 — Phase 7 architecture design: `aldc-automation` spec locked (Opus + `/effort high`)

- **Goal:** Produce a written spec for the `aldc-automation` repo so the next session can implement without re-deciding architecture. No code changes this session.
- **Decisions locked (D1–D7):**
  - **D1.** Repo name `aldc-automation`, location `~/repos/aldc-automation/`. Private, ALDC-owned.
  - **D2.** Per-client config files (`config/gep.yaml`, future `config/fusion92.yaml`), two-file pattern (`*.example.yaml` committed, `*.yaml` gitignored). Three-layer config: `.env` (Snowflake creds, singleton at automation repo root), `config/<client>.yaml` (structural + machine-local repo paths), `clients/<client>/pbi_config.yaml` (PBI GUIDs, gitignored). Full schema in [[aldc-shipyard]] §"Configuration model". Scripts accept `--client gep` flag; auto-resolve `<automation_repo>/config/gep.yaml`.
  - **D3.** Manifests move to `aldc-automation/clients/GEP/{deploy_manifest,validate_manifest}/`. They are tooling artifacts that evolve with `deploy.py`/`validate.py`, not feature artifacts. Cross-repo SQL refs by filename only (resolved via `clients_layout.warehouse_sql_dir`).
  - **D4.** Skill resolves automation home via env-var-with-convention: `AUTOMATION_HOME="${ALDC_AUTOMATION_HOME:-$HOME/repos/aldc-automation}"`. Rejected user-level YAML config (gratuitous when only field would be `automation_home:`). Rejected PATH-based dispatch (Windows + `.venv` fragility). Rejected hardcoded path (no escape hatch).
  - **D5.** `pbi_config.yaml` moves to `aldc-automation/clients/GEP/pbi_config.yaml`, gitignored. Skill reads it via `$AUTOMATION_HOME/clients/GEP/pbi_config.yaml`.
  - **D6.** Connector integration: flat `scripts/` dir with conventional naming (`connector_deploy.py` etc.); per-client manifests at `clients/<client>/connector_manifest/`; `config/<client>.yaml` grows a `connector:` section when used; likely a separate `connector-feature.md` skill (not growing `gep-feature`). Sketch only — not built this session.
  - **D7.** Migration plan: scaffold repo → copy scripts (no history) → refactor scripts to `--client`-driven config → create `config/gep.yaml` → move `pbi_config.yaml` → move skill to `~/.claude/commands/` → delete `clients/GEP/scripts/` → rebase GP-208 → archive `workflow-automation` feature branch → smoke test → resume dogfood. Full step list in [[aldc-shipyard]] §"Migration plan".
- **Tranche G gaps closed by this design:** G.1a (branch switch disaster — eliminated by separating repos), G.1b (deploy.py git ref — closed by reading ref from `repos.clients` working tree), G.1e (stale script on automation branch — eliminated, no automation branch in clients).
- **Tranche G gaps NOT addressed (filed elsewhere):** G.1c (share health check transitive blocking — skill logic fix, orthogonal), G.1d (script hash mismatch — working as intended).
- **Discovery:** the boot prompt asserted the skill already lived at `~/.claude/commands/gep-feature.md`, but it actually lives at `clients/.claude/commands/gep-feature.md`. The user-level move is part of this migration (step 6 of the plan), not pre-existing state.
- **Artifacts produced:**
  - [[aldc-shipyard]] — full repo spec (~280 lines): rationale, layout, config model, path resolution, script refactor checklist, connector pattern, migration plan, Tranche G gap closure mapping.
  - `index.md` — added [[aldc-shipyard]] entry under Repos.
  - This tracker — Phase 7 session log entry (this block), Near-term Architecture Goal section pointer-updated, Phase 7B implementation boot prompt written below.
- **Out of scope (deferred to Phase 7B implementation session):** repo creation, file moves, script refactor, skill rewrite, GP-208 rebase, dogfood re-run.
- **Next session:** Phase 7B execution (Sonnet). Boot prompt in "🔴 CURRENT" below.

### 2026-04-26 — Tranche G execution: GP-208 dogfood sandbox-complete (Sonnet)

- **Goal:** First full end-to-end dogfood of `/gep-feature GP-208`: scoping → sandbox Snowflake → sandbox PBI → (stop before TEST). Stopped at Sub-step 2 by design — tomorrow GP-208 will run clean from the beginning with all changes on the right branch.
- **What worked:**
  - Fast-path scoping confirmed in one "yes" — all requirements from wiki, no re-asking.
  - Snowflake sandbox deploy: 9/9 ✅, 18,992 rows (Sellercloud fresher after share re-add).
  - PBI sandbox: `Inventory Current` (Title Case, EXTRACT excluded) applied, all 31 tables refreshed ✅. Row count confirmed via Explore Data.
  - Legacy cleanup guards in `pbi_model_script.cs` cleanly dropped old Snowflake-named tables then added correct display-named table.
  - Artifact rebuilt from scratch using wiki as source — fast-path works as intended.
- **Gaps captured (in order surfaced):**
  - **G.1a (branch switch disaster):** Running `git checkout GP-208` in Claude Code's bash affected the *shared* working tree — removed `deploy.py` and other workflow-automation files from disk. Paul's terminal lost access to the scripts. Recovery: stash GP-208 changes, switch back to workflow-automation, restore SQL from stash. **Root cause:** Claude Code bash and user terminal share the same working tree. Never switch branches mid-session unless you're certain the user's terminal is not dependent on the current branch's files.
  - **G.1b (git ref shows wrong branch):** `deploy.py` outputs the git SHA/message from its current branch HEAD (workflow-automation `64a7...`), not the GP-208 branch. Cosmetic but confusing in the deploy log. Fix: either consolidate branches or add `--git-ref` param to deploy.py.
  - **G.1c (share health check: "continue" was wrong):** Share health check flagged `CURRENT_REPORT_ALL_ORDERS_UK` + `CURRENT_FORECAST_CSV` as unreachable. Paul chose `continue` since neither is a GP-208 source — but the sandbox DAG task `TASK_WAREHOUSE_ORDERLINE_0` depends on `CURRENT_REPORT_ALL_ORDERS_UK` transitively through `SALES_DIM_ORDER_BASE`. Deploy failed. **Fix needed in skill:** health check block must distinguish "is this object a GP-208 source?" vs "is this object in the shared sandbox DAG?" — the latter blocks regardless of which ticket is deploying.
  - **G.1d (script hash mismatch — correct behavior):** Script hash check fired as designed. Prior artifact had Tranche F hash; current script excluded EXTRACT. Surfaced, Paul confirmed yes, proceeded. Rule 9 working.
  - **G.1e (wrong script on workflow-automation branch):** `pbi_model_script.cs` on `workflow-automation` was the old pre-rename version (Snowflake names + EXTRACT included). Applied wrong script to sandbox first. Fixed by restoring correct script from stash and adding legacy cleanup guards (section 0 in script). **Root cause:** script changes were made on GP-208 branch but not ported to workflow-automation.
  - **Working directory drift:** Bash `cd GEP/scripts/pbi_model_apply` during dotnet build persisted between tool calls, causing subsequent git and file commands to run from the wrong directory. Fixed by explicitly `cd /c/Users/PaulRussell/repos/clients` before continuing.
- **Near-term goals (Paul, 2026-04-26):**
  1. **Tomorrow — GP-208 clean run to TEST:** Commit all staged changes on GP-208 branch (inventory_fct_balance.sql, extract_inventory_current.sql, pbi_model_script.cs, pbi_model_columns.cs, artifact.yaml, notes.md). Start `/gep-feature GP-208` fresh, run sandbox + PBI sandbox + TEST deploy + PBI model apply to GEP Test Models in one clean session.
  2. **Workflow portability (near-term architecture):** Move the entire workflow automation (skill, deploy.py, validate.py, manifests) to a permanent location that is branch-agnostic. The workflow should be able to "point at" any feature branch without switching to it. Today's dual-branch problem (automation on `workflow-automation`, SQL on `GP-208`) is unsustainable. See "Near-term Architecture Goal" section below.

### 2026-04-26 — Phase 7B implementation: `aldc-automation` repo built (Sonnet)

- **Goal:** Execute the migration plan from [[aldc-shipyard]] spec. Scaffold the new repo, copy and refactor all scripts, move the skill to user level, update clients repo.
- **What was done:**
  - **Repo scaffolded** at `C:/Users/PaulRussell/repos/aldc-automation/`. All directories + files written; Paul runs `git init` and makes initial commit.
  - **Scripts copied and refactored** (no git history): `deploy.py`, `validate.py`, `pbi_generate_columns.py`, `pbi_scan.py`, `pbi_seed_sandbox.py`, `data-share-capacity-query.py`.
  - **Script refactor:** added `--client <name>` arg to all scripts; replaced `_REPO_ROOT = _HERE.parent.parent` with `_AUTOMATION_HOME = _HERE.parent`; added `_load_client_config()` function; all path constants (`SQL_DIR`, `MANIFEST_DIR`, `TICKETS_DIR`, `CLIENTS_ROOT`, `ROOT_TASK`, `SANDBOX_SOURCE`) are now late-initialized globals set from config in `main()`.
  - **G.1b fix landed:** `deploy.py` and `validate.py` now use `git -C <CLIENTS_ROOT> log -1` to read the clients-repo HEAD, not the automation repo cwd.
  - **`.env` loading:** primary candidate is `_AUTOMATION_HOME / ".env"`; `_HERE / ".env"` kept as fallback.
  - **pbi_model_apply .NET source** copied verbatim (4 CS files + csproj). No changes.
  - **Manifests copied:** `clients/GEP/deploy_manifest/{GP-208,GP-BENCH-01}.yaml`, `clients/GEP/validate_manifest/GP-208.yaml`.
  - **`pbi_config.example.yaml`** copied to `clients/GEP/`.
  - **`config/gep.example.yaml`** created (committed schema doc with placeholder paths).
  - **`config/gep.yaml`** created with Paul's actual machine paths (gitignored).
  - **Skill moved to user level:** `~/.claude/commands/gep-feature.md` written with all `GEP/scripts/` references replaced by `$AUTOMATION_HOME`-based paths, `--client gep` added to all Python invocations, `AUTOMATION_HOME` prelude added.
  - **`clients/.gitignore`** updated: removed `GEP/scripts/pbi_config.yaml` and `GEP/scripts/_pbi_seed/` entries.
- **Still needed (Paul's git operations):**
  1. `cd C:/Users/PaulRussell/repos/aldc-automation && git init && git add . && git commit -m "chore: scaffold aldc-automation repo"`
  2. Copy `clients/GEP/scripts/pbi_config.yaml` → `aldc-automation/clients/GEP/pbi_config.yaml` (manual file copy, both gitignored).
  3. Copy `clients/GEP/scripts/.env` → `aldc-automation/.env` (manual file copy, both gitignored).
  4. Commit `clients/.gitignore` change on current branch in clients repo.
  5. Delete `clients/GEP/scripts/` (entire directory) from clients repo; commit the deletion.
  6. Rebase `feature/paulrussell/gp-208/inventory-feed` onto current clients HEAD; verify GP-208 SQL files still present.
  7. Archive `feature/paulrussell/workflow-automation/gep-scripted-deploy` branch.
  8. Smoke test: `python "$AUTOMATION_HOME/scripts/deploy.py" --client gep --env sandbox --ticket GP-208 --check-share`
- **Deviations from spec:**
  - `pbi_model_apply_path` was previously read from `pbi_config.yaml` (a manually-set field). After migration, §G in the skill computes it directly as `$AUTOMATION_HOME/scripts/pbi_model_apply/bin/Release/net8.0-windows/x64/pbi_model_apply.exe` — no pbi_config.yaml field needed.
  - `SANDBOX_SOURCE` and `TASK_OWNER_ROLE` kept as GEP-specific hardcodes in deploy.py (not in scope per refactor spec). `ROOT_TASK` reads from `cfg["snowflake"]["task_chain"]`.
  - `clients/.claude/commands/gep-feature.md` NOT deleted yet — Paul confirms removal when doing step 5 above (deleting scripts dir). The `.claude/commands/` exception in `.gitignore` is still valid for any future project-level skills.
- **Tranche G gaps closed by this implementation:** G.1a, G.1b, G.1e — all eliminated as designed.
- **Next session:** Tranche H dogfood — resume GP-208 clean run from scratch using scripts in `aldc-automation`. Boot prompt below.

### 2026-04-26 — Tranche H dogfood: GP-208 full workflow + rollback (Sonnet)

- **Goal:** First clean end-to-end `/gep-feature GP-208` run using the migrated `aldc-automation` repo. Ran through `implementing` Sub-step 2 → `test-deployed` → intentional rollback. Also used as a workflow improvement session.
- **What worked:**
  - TEST deploy: 9/9 ✅, 16,780 rows. deploy.py + validate.py running cleanly from aldc-automation.
  - PBI model applied to GEP Test Models via pbi_model_apply.exe. DAX validation (§J) confirmed 16,780 rows, 0 null PRODUCT_ID, 0 unjoined. New automated DAX check replaces manual eyeballing.
  - PRs raised, Jira design summary + QA evidence comments posted end-to-end.
  - Rollback executed (PR closed, PBI model reverted, Snowflake views restored).
  - `setup.py` one-time bootstrap script created and run successfully.
- **Workflow improvements shipped in this session:**
  - **Multi-root VS Code workspace** (`aldc-automation.code-workspace`) — both repos visible in one window.
  - **SQL file review with VS Code diff** — `git show main:<file> > /tmp/... && code --diff` opens per-file diff sequentially with per-file confirmation.
  - **Task chain monitoring in rollback** — deploy.py `--rollback` now tier-aware with optional `--run-task` between tiers.
  - **Automated DAX validation (§J)** — runs after every PBI refresh. Row count, null key check, relationship check. Replaces visual-only smoke-test.
  - **`setup.py` bootstrap** — one-time machine setup (Snowflake creds, repo paths, PBI workspace GUIDs, dotnet build). Idempotent. Prompted inline when config is missing mid-feature.
  - **PR flow corrected** — SQL PR now targets `GEP/development` (was `GEP/user-testing`). PBI model PR is a separate step.
  - **Rollback parser bug fixed** — the `not s.strip().startswith("--")` filter was silently dropping all views. Fixed: parse on `-- snapshot:` boundary, hard exit if 0 statements, post-restore INFORMATION_SCHEMA verification.
  - **Polling robustness** — `poll_task_chain` now anchors on ROOT_TASK via `TASK_NAME` parameter. Eliminates count fluctuation from staggered child-task scheduling.
  - **deploy.py --rollback --run-task** — tier-aware restore: tier-1 views → task chain → tier-2 views. `snapshot_views` writes `-- restore_tiers:` header to drive this.
- **Gaps and issues surfaced:**
  - `pbi_config.yaml` had not been migrated to aldc-automation — surfaced mid-session. Fixed by setup.py.
  - `pbi_model_apply.exe` build path was wrong (`x64` subdirectory doesn't exist for plain `dotnet build`). Fixed in setup.py and skill.
  - `dataset_name` in pbi_config.yaml was the workspace name ("GEP Test Models"), not the semantic model name ("Data Model"). Fixed by correcting pbi_config.yaml.
  - `pbi_model_rollback.cs` needed to remove relationships before deleting the table — `Table.Delete()` fails if relationships exist. Fixed with a relationship sweep first.
  - Rollback snapshot restore failed because old EXTRACT_INVENTORY_CURRENT referenced `FCT.CAPTURE_TIMESTAMP` which no longer exists in the rebuilt WAREHOUSE.INVENTORY_FCT_BALANCE. Pre-existing TEST inconsistency, not caused by GP-208.
  - Jira MCP deprecation notice: HTTP+SSE endpoint at `mcp.atlassian.com/v1/sse` deprecated after 2026-06-30 → update to `mcp.atlassian.com/v1/mcp`.
- **Next session:** Real GP-208 ship — run `/gep-feature GP-208`, resume at `implementing` Sub-step 2 (TEST deploy), proceed through to UAT. Boot prompt below.

---

### Near-term Architecture Goal — Dedicated `aldc-shipyard` Repo

> **2026-04-26 update:** design locked in Phase 7 session — full spec at [[aldc-shipyard]]. The summary below is preserved as decision context; consult the wiki page for the authoritative schema, path-resolution pattern, and migration plan.

**Decision (2026-04-26, confirmed by Paul):** create a separate `aldc-shipyard` repo (formerly `aldc-automation`) for all workflow automation infrastructure. Scripts stay off the `clients` and `connector` CI/CD branch chains entirely.

**Why not merge into `GEP/development`:**
The `clients` branch chain (`GEP/development` → `GEP/user-testing` → `main`) is the production deployment path. The automation is still actively being designed — merging there would pollute CI/CD environment branches with half-built tooling. A separate repo decouples the automation lifecycle completely.

**Why a separate repo is correct:**
- **Decoupled lifecycle** — automation iterates fast; `clients` and `connector` CI/CD chains stay clean
- **Neutral ground for multi-repo orchestration** — scripts coordinate both `clients` AND `connector`; they don't belong to either
- **Scalable to other clients** — Fusion92 or future clients get config entries, not forks of `clients`
- **No CI/CD risk** — break, redesign, and experiment freely without touching production branch chains

**Proposed repo structure:**

```
aldc-shipyard/
  scripts/
    deploy.py
    validate.py
    pbi_generate_columns.py
    pbi_scan.py
    pbi_seed_sandbox.py
    pbi_model_apply/       ← .NET source; bin/ gitignored
  clients/
    GEP/
      deploy_manifest/     ← GP-208.yaml etc.
      validate_manifest/
      pbi_config.yaml      ← gitignored (local workspace/dataset IDs)
  config/
    gep.yaml               ← paths to clients/connector repos, env settings
  .claude/
    commands/              ← skill source reference (live copy stays at ~/.claude/commands/)
```

**What stays in `clients` repo:** SQL files + ticket artifacts (`GEP/tickets/<ticket>/artifact.yaml`, `pbi_model_script.cs`, `pbi_model_columns.cs`, `notes.md`) — these belong WITH the SQL as part of the feature branch PR and PR review.

**What stays at user level:** `~/.claude/commands/gep-feature.md` — already there, already correct.

**Split summary:**

| Layer | Location | Why |
|---|---|---|
| Skill (orchestrator) | `~/.claude/commands/` | User-level, already repo-agnostic |
| Scripts (deploy, validate, pbi_*) | `aldc-shipyard` repo | Multi-repo neutral ground, off CI/CD chain |
| Manifests (deploy/validate YAML) | `aldc-shipyard/clients/GEP/` | Travel with the scripts that consume them |
| SQL files | `clients` repo (feature branch) | Part of the feature PR |
| Ticket artifacts (artifact.yaml etc.) | `clients` repo (feature branch) | Belong with the SQL they describe |
| Cross-repo config (repo paths) | `aldc-shipyard/config/gep.yaml` | Points scripts at correct local repo locations |
| Local secrets (workspace IDs etc.) | `aldc-shipyard/clients/GEP/pbi_config.yaml` | gitignored, machine-local |

**Next steps before next GP-208 dogfood:**
1. **Opus planning session** — nail the `config/gep.yaml` schema, how the skill resolves paths to both repos at runtime, and connector integration pattern.
2. Create `aldc-shipyard` repo, move scripts + manifests there.
3. Update skill to read automation repo path from config.
4. Run clean dogfood from the correct structure.

Do not run another GP-208 dogfood until steps 1–3 are done — the dual-branch problem will recur otherwise. This is the "Phase 7 architecture" referenced in prior tranche notes.

---

### 2026-04-25 — Tranche G planning + pbi_config test config (Sonnet, end of Tranche F session)

- **Goal:** Plan the next session (Tranche G) and unblock it by filling `pbi_config.yaml`
  test workspace entries and clearing the GP-208 artifact for a clean re-scope.
- **Decisions made:**
  - INVENTORY_FCT_BALANCE PBI display name: **"Inventory Current"** (Paul's call 2026-04-25).
    EXTRACT_INVENTORY_CURRENT display name: TBD — ask at scoping in Tranche G.
  - `pbi_model_script.cs` must be updated to use display names before TEST apply — the
    drop-if-exists guards and AddTable calls currently reference Snowflake names which
    don't exist in TEST under those names. See G.1 in boot prompt.
  - Tranche D (`prod-deployed` auto-apply) deferred until Sub-step 2 proves clean in Tranche G.
  - Phase 7 (multi-repo architecture) is a separate Opus planning session. Current
    architecture is safe to extend for one more dogfood without an overhaul.
- **Actions taken:**
  - `pbi_config.yaml` test entries filled: id=a29d4c01, dataset_id=66151728,
    dataset_name="Data Model" (resolved via REST API).
  - GP-208 artifact.yaml + notes.md deleted for clean re-scope.
  - Tranche G boot prompt written into tracker (see "🔴 CURRENT" section above).
- **Architecture discussion (summary):** Paul raised the question of whether workflow
  automation code belongs in `clients` repo when it will eventually touch `connector`
  and `power_bi` repos too. Recommendation: move the skill to `~/.claude/commands/`
  (user-level, repo-agnostic) and make scripts path-independent. Full design deferred
  to Phase 7 Opus session. Current architecture is not blocking Tranche G.

### 2026-04-25 — Phase 6 Tranche F kickoff: sandbox hardening plan 🟡 (Opus, planning)

- **Goal:** make `/gep-feature GP-208 force` drive Sub-step 1b end-to-end against
  the sandbox with zero manual rescue and emit a clickable validation link. Sandbox
  only — TEST tail and Tranche D explicitly deferred until the sandbox flow is stable.
- **Why a new tranche:** the 2026-04-24 acceptance test validated the *primitives*
  (wrapper apply, REST refresh, DAX row-count match) but did so by invoking each
  step manually outside the skill. Since then the skill itself has been heavily
  revised — §G rewritten to call `pbi_model_apply.exe` (MSAL-internal, no `--token`),
  MODEL SCAN block added, GENERATE COLUMN DEFINITIONS step added, `warn_only`
  support landed in `validate.py`. None of those skill paths have been exercised on
  GP-208. Tranche F dogfoods the actual user-facing flow.
- **Decision:** focus is sandbox only. We don't fill `workspaces.test.*` or
  `workspaces.prod.*` in `pbi_config.yaml` this session. The TEST tail dogfood and
  Tranche D both wait on a stable sandbox flow.
- **Plan (authoritative spec — see [[phase6-pbi-automation-plan]] §6.8):**
  - F.1 — add sandbox-only validation link emission to §G success + §H poll_refresh
    Completed + the existing MANUAL VISUAL CHECK block.
  - F.2 — default to skipping MODEL SCAN; file the TE3 hang fix as a follow-up.
  - F.3 — reset GP-208 sandbox state (drop the two tables) before the cold run.
  - F.4 — run Sub-step 1b end-to-end through the skill; confirm every block fires.
  - F.5 — capture every gap as it surfaces; fix in-session; re-run until clean.
  - F.6 — wiki consolidation (sandbox-only updates to plan + pattern + tracker).
- **Done criteria:** cold `/gep-feature GP-208 force` produces a populated model and
  prints a working validation link with no manual rescue; GP-208 artifact has fresh
  sandbox_applied_at + sandbox_refresh_id from the skill-driven run.
- **Out of scope this session:** Sub-step 2 TEST promotion, Tranche D prod
  auto-apply, `pbi_config.yaml` test/prod entries, `pbi_scan.py` TE3 hang fix,
  GP-208 naming-convention reconciliation.
- **Boot prompt for execution session:** see "🔴 CURRENT — Phase 6 Tranche F" in
  the Next Session Boot Prompt section below.
- **Execution log:**
  - **F.1 ✅ (2026-04-25)** — Sandbox validation link emission added to `gep-feature.md`:
    - §G exit-code-0 branch: prints `Workspace` + `Dataset` URLs from `pbi_config.workspaces.sandbox.*` (with null-guard).
    - §H `poll_refresh` Completed branch: same URLs + per-table `objects[]` status table.
    - MANUAL VISUAL CHECK: replaced bare "Open GEP Sandbox Models workspace" text with live URL template + note that links were already printed.
    - §I header: fixed stale "(shared by §G and §H)" → "(§H REST calls only — NOT for §G)" to match §5a revision from 2026-04-23.
    - All 4 touchpoints are sandbox-only; TEST/PROD emission explicitly deferred.
  - **F.2 ✅ (2026-04-25, decision)** — MODEL SCAN will be skipped for the GP-208 dogfood run. `pbi_scan.py` TE3 path remains `if False`-gated (subprocess hang). No skill code change needed — the existing graceful-skip flow fires automatically when Paul chooses `skip` at the `Run PBI model scan? (yes / skip)` prompt. TE3 hang fix filed as follow-up in `potential-tickets`.
  - **F.3 — GP-208 sandbox state reset (pending Paul action):** Drop the two GP-208 tables before running the skill. Easiest: re-run the existing `pbi_model_script.cs` (drop-if-exists guards make it idempotent). Paul can use the wrapper directly: `GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe --script GEP/tickets/GP-208/pbi_model_script.cs --workspace "GEP Sandbox Models" --dataset "GEP_Sandbox_Current"`. This will drop + re-add the tables and leave the sandbox in a known-clean state before the skill run.
  - **Pre-F.4 fix — GENERATE COLUMN DEFINITIONS "already wired" skip (2026-04-25):** Added skip condition: if `pbi_model_columns.cs` exists AND `pbi_model_script.cs` starts with `#load "pbi_model_columns.cs"` AND contains `AddColumns_*` calls, print "ℹ️  Column definitions already wired" and skip `pbi_generate_columns.py`. This is the expected F.4 step 3 behavior (spec says "recognises columns are wired and skips"). Proactively added to avoid a gap discovery during the run.
  - **F.3 ✅ COMPLETE (2026-04-25)** — Sandbox state reset. Tables dropped + recreated, relationship dropped + recreated, `SaveChanges() complete`. MSAL token still cached (no device-code prompt). Exit 0.
  - **F.3 GAP (2026-04-25) — TOM does not cascade-delete relationships on table remove.** Running `pbi_model_script.cs` with drop-if-exists failed on the second run with `OperationException: Relationship points to deleted table INVENTORY_FCT_BALANCE`. Root cause: `Model.Tables.Remove()` removes the table from TOM's in-memory collection but does NOT remove `SingleColumnRelationship` objects in `Model.Relationships` that reference it. `SaveChanges()` serializes the state and the server rejects the dangling relationship. **Fix applied:** added a pre-drop relationship-cleanup loop to both drop blocks in `pbi_model_script.cs` — collect relationships referencing the target table first, remove them, then remove the table. This pattern must be applied to every drop-if-exists block in any per-ticket script that may leave relationships behind.
  - **F.4 ✅ COMPLETE (2026-04-25)** — `/gep-feature GP-208 force` ran Sub-step 1b end-to-end through the skill with zero manual rescue:
    - MODEL SCAN → ran (Paul chose `yes`), REST fallback, both tables confirmed present at 0 rows (expected pre-refresh). scan_option_chosen = "B" recorded.
    - PRE-FLIGHT → found `pbi_model_script.cs` ✅
    - GENERATE COLUMN DEFINITIONS → "already wired" skip condition fired ✅
    - REBIND → `update_parameters` HTTP 200, `SANDBOX_DG1_GEP_GP208` + `SYSADMIN` ✅
    - §G apply → `pbi_model_apply.exe` exit 0; relationship-cleanup fix worked (relationship dropped before table, re-created after) ✅
    - F.1 validation links printed at §G exit-0 ✅
    - §H refresh_dataset → 202 Accepted, request ID `4de76ce2-44ef-4e4e-9a8d-b30087bc0d17` ✅
    - §H poll_refresh → Completed in ~4 min (10 polls × 20s); INVENTORY_FCT_BALANCE + EXTRACT_INVENTORY_CURRENT both Completed ✅
    - F.1 links + per-table status table printed at Completed ✅
    - MANUAL VISUAL CHECK → Paul clicked links, confirmed data visible ✅
    - RECORD OUTCOME → artifact updated: `sandbox_applied_at: 2026-04-25T20:57:52Z`, `sandbox_refresh_id: 4de76ce2-...`, `script_hash: bb597cf3...` ✅
  - **F.5 gaps surfaced (2026-04-25):**
    - **GAP 1 (fixed in-session):** TOM does not cascade-delete relationships on `Model.Tables.Remove()`. Second run of `pbi_model_script.cs` failed with `OperationException: Relationship points to deleted table INVENTORY_FCT_BALANCE`. Fixed: pre-drop relationship-cleanup loop added to both drop blocks in the script.
    - **GAP 2 (filed as follow-up):** `pbi_scan.py` ran (Paul chose `yes` not `skip`) and provided useful pre-run state confirmation. TE3 hang remains; REST fallback is sufficient for row-count confirmation.
    - **GAP 3 (filed as follow-up):** No optional table/column renaming step in skill. GEP convention is Title Case display names; script currently uses Snowflake names. Need a rename block in Sub-step 1b after model apply.
    - **GAP 4 (filed as follow-up):** No sandbox-vs-TEST model comparison step. Proposed validation: scan both environments before TEST apply, diff tables/relationships, flag unintended changes. Requires TE3/TOM scanner for useful metadata.
    - **GAP 5 (filed as follow-up):** No dry-run compile check before §G apply. Wrapper supports `--dry-run`; would catch Roslyn errors before XMLA connection.
    - **GAP 6 (filed as follow-up):** poll_refresh timeout currently aborts; should offer "keep polling? (yes / abort)" branch.
    - **GAP 7 (filed as follow-up):** script hash mismatch check (Rule 9) not wired into Sub-step 1b flow — should compare artifact hash vs. current file hash before re-apply and warn Paul if they differ.
    - **Additional hardening (applied in-session, 2026-04-25):** Items 1–4 shipped to `gep-feature.md`: (1) dry-run `--dry-run` compile check before §G apply (exit 4 = abort); (2) script hash mismatch warning before apply (Rule 9 wired in); (3) poll_refresh timeout → `(keep-polling-10min / abort)` branch instead of hard abort; (4) sandbox null-guard at Sub-step 1b entry before MODEL SCAN.
    - **Paul's Gap 1 (table/column renaming) — filed as follow-up.** Need an optional RENAME block after APPLY MODEL SCRIPT. GEP convention = Title Case display names; scripts currently use Snowflake names. Decision: separate tranche (requires naming locked at scoping time).
    - **Paul's Gap 2 (sandbox vs TEST model comparison) — filed as follow-up.** Useful but requires TOM-based scanner (TE3 path disabled). Row-count-only REST comparison is too narrow. Revisit after pbi_scan TE3-hang fix lands.
  - **F.6 ✅ COMPLETE (2026-04-25)** — Wiki consolidated (sandbox-only scope):
    - `phase6-pbi-automation-plan.md` §6.8 → flipped to ✅ COMPLETE with summary.
    - `pbi-xmla-model-changes.md` → appended relationship-cascade-delete gotcha with full code pattern and two-list workaround.
    - `pbi-xmla-automation.md` → updated Required Pieces §4 step 6 with validation link emission detail; step 2 annotated with "catches errors before XMLA connection".
    - Tracker (this file) → execution log complete with all F.1–F.6 entries and gaps.

### 2026-04-24 — Phase 6 Sub-step 1b end-to-end validation 🟡 (Opus, in progress)

- **Goal:** prove `pbi_model_apply.exe` works end-to-end against the GP-208 sandbox dataset, closing the "no columns" blocker from the 2026-04-22/23 dry-run and promoting GP-208 artifact to `sandbox_validated: true`. This is the acceptance test for the whole Phase 6 automation claim.
- **Context:** Tranches A–C shipped. `gep-feature.md` §G already calls `pbi_model_apply.exe` (wrapper committed today). The outstanding question is whether wrapper-driven apply + REST refresh actually produces populated tables in the sandbox.
- **Commits today (2026-04-24):**
  - `feat(pbi): pbi_model_apply .NET 8 wrapper — XMLA apply via TOM + Roslyn + MSAL`
  - `feat(pbi): pbi_scan.py + pbi_model_scan.cs — read-only PBI model scan`
  - Deleted `GEP/scripts/_rebind_sandbox_gp208.py` — hardcoded GP-208 one-off superseded by skill §H `update_parameters`.
- **Plan (agreed with Paul, this session):**
  1. Scan sandbox — `pbi_scan.py --env sandbox --tables INVENTORY_FCT_BALANCE,EXTRACT_INVENTORY_CURRENT`
  2. Verify sandbox parameter binding — GET `/datasets/{id}/parameters` confirms `SNOWFLAKE_DATABASE = SANDBOX_DG1_GEP_GP208`
  3. Harden `pbi_model_script.cs` — drop-if-exists guards so re-runs are idempotent regardless of starting state (Option 2 from the session)
  4. Wrapper dry-run — Roslyn compile check
  5. Wrapper apply — first run triggers MSAL device-code (browser); ~1h cached thereafter
  6. Trigger refresh via REST — POST `/refreshes`
  7. Poll refresh — 20s interval, 20-min cap
  8. Verify row counts — re-run scan; expect both tables with columns and non-zero rows
  9. Update GP-208 artifact — `sandbox_validated: true`, `sandbox_applied_at`, `sandbox_refresh_id`, new `script_hash`
  10. Update tracker + close out `pbi-xmla-model-changes.md` "Current Status" + "GP-208 Sub-step 1b Status" sections.
- **Execution log:** _appended below step-by-step as we go; deviations from the plan documented here_
  - **Step 1 (scan sandbox) ⚠️ false-negative, tables WERE present.** Scanner's `EVALUATE TOPN(1, 'X')` returns non-200 when tables have 0 columns — the scanner reports the same "not in model" for absent tables AND broken 0-column tables. Misled us initially; the 2026-04-22 broken tables were actually still there.
  - **Step 2 (verify parameter binding) ✅** — `SNOWFLAKE_DATABASE=SANDBOX_DG1_GEP_GP208`, `SNOWFLAKE_ROLE=SYSADMIN` confirmed via GET `/parameters`. Note: `CORE_API_CLIENT_TOKEN` value visible in the response — pre-existing security finding per 2026-04-21 discovery, already in [[potential-tickets]].
  - **Step 4 (dry-run) ✅** — script compiles via Roslyn.
  - **Step 5 (wrapper apply) ⚠️ required two plan deviations:**
    - **Deviation 1 — first run skipped the add:** tables existed from 2026-04-22 GUI attempt with broken partitions, but the script's `if (!Model.Tables.Contains(...))` guards only-add-if-absent → nothing was replaced. Escalated Step 3 (drop-if-exists hardening) from "deferred" to "on the critical path" and modified `pbi_model_script.cs` in-session.
    - **Deviation 2 — `Table.Delete()` does not exist in TOM** (only in TE3 GUI scripting sugar). Hit as Roslyn compile error. Fixed to `Model.Tables.Remove(Model.Tables[name])`. Dry-run green, apply succeeded, both tables dropped and readded.
  - **Step 6 (trigger refresh) ✅** — first refresh request ID `0381d73c-2ed0-465a-a3b1-6bf1d4ca6a02`.
  - **Step 7 (poll refresh) ✅** — Completed in ~4m 22s. REST response shows `objects[].status: "Completed"` for both new tables. One pre-existing warning (`_BASE_ACT_SALE_RET` → `SALES_RETURNS_CONSOLIDATED`) — 2026-04-21 tech debt, unrelated.
  - **Step 8 (verify rows) ❌ — acceptance test FAILED despite refresh success.** Direct DAX `COUNTROWS` returned `AnalysisServicesErrorCode 3241804132: "Table 'X' cannot be used in computations because it does not have any columns"` for both tables. Refresh "Completed" at partition level but tables were empty.
  - **Diagnosis #1 — Mode=Default → Mode=Import (WRAPPER BUG FIXED).** `_diag_partitions.cs` showed the new partitions had `Mode=ModeType.Default`; working `Inventory Balance` and `Product` partitions use `Mode=ModeType.Import` explicitly. The wrapper's `TabularExtensions.AddTable()` was creating partitions with the default mode. Patched `TabularExtensions.cs` to set `Mode = ModeType.Import` explicitly, rebuilt (`dotnet build -c Release`), re-applied, re-refreshed. Second refresh (request `4a225a83-...`) completed in ~5 min — but tables STILL had 0 user columns and DAX still failed.
  - **Diagnosis #2 — TOM does NOT auto-discover M-query schema (ROOT CAUSE, architectural).** `_diag_columns.cs` comparison showed working `Inventory Balance` has 28 explicitly-defined `DataColumn` objects with `SourceColumn` mappings; our new tables had only the auto-generated `RowNumberColumn`. **TOM requires columns to exist in metadata BEFORE refresh can load data.** Only Power BI Desktop's Power Query editor does M-query schema inference — TOM/XMLA/REST all assume predefined columns. Tested workaround `partition.RequestRefresh(RefreshType.Full) + Model.SaveChanges()`: did not populate columns. Full write-up and rationale in [[pbi-xmla-model-changes]] § TOM Schema-Discovery Constraint.
  - **Pivot — Option B chosen (with Paul, 2026-04-24):** build `GEP/scripts/pbi_generate_columns.py` — a small Python utility that queries Snowflake `INFORMATION_SCHEMA.COLUMNS` for target tables and emits a C# code fragment (`DataColumn { Name, SourceColumn, DataType }` entries). Fragment is pasted into `pbi_model_script.cs` (or future per-ticket scripts) before the `Model.AddTable()` calls. Reusable across every PBI-touching ticket. GP-208 validation is the acceptance test.
  - **Rejected alternatives:**
    - Option A — hand-code 28+ columns per new table. Unblocks today but puts manual schema authoring on every future PBI-touching ticket. Against the "high standard" goal.
    - Option C — extend the wrapper with Snowflake connectivity + `--infer-columns` flag. Best end state; defers for now because of scope (adds Snowflake.Data .NET dependency, ODBC creds management, connection-string handling inside the wrapper).
  - **Commits from this session (Paul-owned, not yet landed):**
    1. `pbi_model_apply/TabularExtensions.cs` — `Mode = ModeType.Import` fix.
    2. Rebuilt `pbi_model_apply.exe` binary.
    3. `GEP/tickets/GP-208/pbi_model_script.cs` — drop-if-exists hardening (`Model.Tables.Remove(...)`) replacing the original `if-not-exists` guards.
    4. Diagnostic scripts (`_diag_partitions.cs`, `_diag_columns.cs`, `_diag_requestrefresh.cs`) — can be deleted or parked under `GEP/tickets/GP-208/` as documented-working-examples for future diagnosis (recommend delete post-validation).
  - **Next steps this session:** (a) wiki updates in progress — tracker + `pbi-xmla-model-changes.md` + `phase6-pbi-automation-plan.md`. (b) Build `pbi_generate_columns.py`. (c) Apply generated columns to `pbi_model_script.cs`. (d) Re-run wrapper → refresh → verify rows > 0 → set `sandbox_validated: true`.
  - **Option B build — `pbi_generate_columns.py` ✅** — 200-line Python utility, mirrors `deploy.py` `.env` + Snowflake connect conventions. Takes `--env`, `--ticket` (for sandbox), `--tables`, `--schema` (default WAREHOUSE). Queries `INFORMATION_SCHEMA.COLUMNS`, maps Snowflake types → TOM `DataType` via the table documented in [[pbi-xmla-model-changes]]. Emits one `void AddColumns_<TABLE>(Table t)` function per table into a fragment file. First-try bug: `FROM IDENTIFIER(%s).INFORMATION_SCHEMA.COLUMNS` is a Snowflake syntax error; fixed to `FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_CATALOG = ...` using the current-DB context. Re-run clean: 27 cols for INVENTORY_FCT_BALANCE, 32 for EXTRACT_INVENTORY_CURRENT.
  - **Wrapper enhancement — `#load` support** — `Program.cs BuildScriptOptions` now calls `WithSourceResolver(new SourceFileResolver(searchPaths: [scriptDir], baseDirectory: scriptDir))`. Lets per-ticket scripts do `#load "pbi_model_columns.cs"` to include generator output without inlining. Generator-emitted files stay separate from hand-written logic. Rebuild confirmed.
  - **Script wiring — `pbi_model_script.cs`** — `#load "pbi_model_columns.cs"` at top; `AddColumns_INVENTORY_FCT_BALANCE(t)` / `AddColumns_EXTRACT_INVENTORY_CURRENT(t)` inserted between `Model.AddTable(...)` and `SetExpression(...)` for each table. New script hash: `6e16abc044d474...`.
  - **Final apply run ✅** — 27 + 32 columns defined; PRODUCT_KEY → Product relationship auto-created on the same pass because the column now exists at relationship-check time (previously skipped with "columns not yet present" warning).
  - **Refresh `ad9f66d5-91ab-41c4-a550-19e1ef4feb8c` ✅** — Completed in ~4m 10s; both tables marked Completed at the partition level.
  - **🎯 Acceptance test PASSED** — DAX `COUNTROWS`:
    - `INVENTORY_FCT_BALANCE`: **16,736 rows** (exact match with Snowflake sandbox validate 2026-04-22)
    - `EXTRACT_INVENTORY_CURRENT`: **16,560 rows** (slightly fewer — extract inner-joins against SHARED_DIM_PRODUCT)
  - **Artifact updated** — `sandbox_validated: true`, `sandbox_applied_at: 2026-04-24T18:32:00Z`, `sandbox_refresh_id: ad9f66d5-...`, `sandbox_row_counts: {...}`, new `script_hash`.
  - **Cleanup** — `_diag_partitions.cs`, `_diag_columns.cs`, `_diag_requestrefresh.cs`, `_diag_check_expressions.cs` removed from `GEP/tickets/GP-208/`. Diagnostic technique documented in [[pbi-xmla-model-changes]] for future use.

### 2026-04-24 — Phase 6 Sub-step 1b end-to-end validation ✅ COMPLETE + Tranche E wiki ✅ COMPLETE (Opus)

**🛑 SESSION END / RESUMPTION NOTES (2026-04-24):**

Paul closed the session here. Pick up next session as follows:

**1. Commit pending work (Paul-owned):**

`repos/clients` — 4 commits, in order:
1. `fix(pbi): wrapper — Mode=Import + #load support (closes TOM schema-discovery gap)`
   → `GEP/scripts/pbi_model_apply/TabularExtensions.cs`, `GEP/scripts/pbi_model_apply/Program.cs`
2. `feat(pbi): pbi_generate_columns.py — emit TOM DataColumn defs from Snowflake`
   → `GEP/scripts/pbi_generate_columns.py` (new)
3. `feat(GP-208): PBI sandbox validated end-to-end — 16,736 + 16,560 rows`
   → `GEP/tickets/GP-208/pbi_model_script.cs`, `GEP/tickets/GP-208/pbi_model_columns.cs`, `GEP/tickets/GP-208/artifact.yaml`
4. `feat(skill): Sub-step 1b — column generation pre-step for new tables`
   → `.claude/commands/gep-feature.md`

`repos/wiki` — 1 commit covering Tranche E + today's session log:
- `concepts/patterns/pbi-xmla-automation.md` (new), `entities/tools/power-bi.md`, `entities/tools/SSMS.md`,
  `entities/projects/workflow-automation.md`, `processes/deployment/gep-snowflake-pbi-deployment.md`,
  `processes/deployment/pbi-xmla-model-changes.md`, `processes/distributed-workflow/active/phase6-pbi-automation-plan.md`,
  `processes/distributed-workflow/active/client-workflow-automation.md`, `index.md`, `log.md`

**2. What's done:**
- Phase 6 Tranches A, B, C all shipped previously
- Phase 6 wrapper + generator + script wiring + GP-208 acceptance test ✅ today
- Tranche E wiki corrections ✅ today (canonical pattern page; SQL-Server-intermediate myth corrected; XMLA Automation cross-refs everywhere)
- "Multi-feature conflict in TEST/PBI" blocker ✅ closed today

**3. Remaining workstream backlog (NOT blocked, can pick up any time):**
- **Tranche D — `prod-deployed` conditional auto-apply** (plan §3.7). Implement only AFTER Tranche C is dogfooded on at least one *additional* real ticket beyond GP-208. Adds `if visual_required == false` branch at the prod publish gate that auto-applies `pbi_model_apply.exe` against the production dataset + REST refresh.
- **Replace `pbi_partition_expressions.md`** — vestigial from the TE3 GUI workaround era (per-ticket M-expression copy-paste reference). Now superseded by the model script's `InventoryFctM(...)` helper. Delete or repurpose as an M-expression conventions reference for any future ticket that needs to hand-author M outside the script.
- **Re-enable `pbi_scan.py` TE3 path or replace with TOM-based scanner.** Currently `if False`-gated; only REST DAX fallback runs. The wrapper proves a TOM-based scan is viable — could write a `pbi_model_scan` C# script that uses TOM (no TE3 dependency), then call it from `pbi_scan.py` via `pbi_model_apply.exe` + `--script`. Filed in [[potential-tickets]].
- **Naming-convention reconciliation** — GP-208 added new tables with Snowflake names (`INVENTORY_FCT_BALANCE`); GEP convention is Title Case (`Inventory Balance`). Reconcile when scoping the next inventory ticket. Decision recorded in GP-208 artifact 2026-04-23.

**4. Ticket state:**
- GP-208 artifact: stage = `implementing`, `sandbox_validated: true`. Next stage transition is to TEST (Sub-step 2 — promote model + Snowflake to TEST_DG1_GEP). Ready to advance once Paul wants to resume the GP-208 ticket itself (separate from the workstream backlog above).

**5. Stale boot prompts in this tracker:**
- The "🔴 CURRENT — Phase 6: Make Sub-step 1b work via automation" boot prompt below is now stale (the work it described is complete). Leave it for historical context, but a future resumption should NOT use it as the entry point — start from this 2026-04-24 entry instead.

---

**Outcome:** The full Phase 6 PBI model automation loop is proven end-to-end against GP-208 sandbox. Loop: wrapper apply (via TOM + Roslyn + MSAL) → REST parameter rebind → REST refresh + poll → DAX row-count verification. Acceptance test passes with exact row-count match to upstream Snowflake sandbox.

**Shipped today (uncommitted, Paul-owned):**
- `GEP/scripts/pbi_model_apply/TabularExtensions.cs` — `Mode = ModeType.Import` explicit (was inheriting `Default`)
- `GEP/scripts/pbi_model_apply/Program.cs` — `#load` directive support via `SourceFileResolver`
- `GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe` — rebuilt binary (gitignored via nested `.gitignore`)
- `GEP/scripts/pbi_generate_columns.py` — new helper (Option B)
- `GEP/tickets/GP-208/pbi_model_columns.cs` — generator output for GP-208
- `GEP/tickets/GP-208/pbi_model_script.cs` — drop-if-exists + `#load` + `AddColumns_*(t)` wiring
- `GEP/tickets/GP-208/artifact.yaml` — `sandbox_validated: true` + timestamps + row counts
- Wiki: [[pbi-xmla-model-changes]] § TOM Schema-Discovery Constraint + Mode gotcha + drop-if-exists pattern; [[phase6-pbi-automation-plan]] §6.6 + §6.7

**Remaining in the workstream (not blocked on this session):**
- Tranche D — `prod-deployed` conditional auto-apply (plan §3.7). Dogfood Tranche C on 1+ real tickets first.
- Tranche E — wiki docs: new `concepts/patterns/pbi-xmla-automation.md`, corrections to `entities/tools/power-bi.md` (remove SQL-Server-intermediate claims), `entities/tools/SSMS.md` (reframe as XMLA client into PBI tabular model), `gep-snowflake-pbi-deployment.md` (XMLA automation callout), `workflow-automation.md` §7 (PBI out-of-scope note), close "Multi-feature conflict in TEST / PBI" blocker.
- Update `gep-feature.md` §G / Sub-step 1b to mention the `pbi_generate_columns.py` pre-step when new tables are introduced.

### 2026-04-23 — Phase 6 Option A planning session complete ✅ (Opus, xhigh effort)

- produced: [[pbi-model-apply-wrapper]] — authoritative implementation plan for a thin
  .NET 8 console wrapper (`GEP/scripts/pbi_model_apply/`) that applies PBI model scripts
  via TOM directly, replacing the hung TE3 CLI path diagnosed in [[pbi-xmla-model-changes]].
- decisions:
  - **Technology:** .NET 8 console app; `Microsoft.AnalysisServices.NetCore.retail.amd64`
    (TOM) + `Microsoft.CodeAnalysis.CSharp.Scripting` (Roslyn). No MSOLAP, no WebView2,
    no GUI dependency — the thing that makes TE3 hang. Wrapper talks HTTPS to the PBI
    XMLA endpoint directly via TOM's managed transport with a bearer token in the
    connection string's `Password` field (`User ID=AzureAD;Password=<bearer>`).
  - **Script API:** TE3 emulation layer (~80 LOC) exposing `AddTable`,
    `AddRelationship`, `SetExpression` extension methods via Roslyn's `WithImports`
    mechanism. One documented syntax delta from TE3 GUI scripts: partition expression
    assignment becomes `.SetExpression(...)` because C# lacks extension properties.
    Two line edits in the existing `GP-208/pbi_model_script.cs` (§4.1 of plan); one
    additional edit for the `SingleColumnRelationship` cast in the relationship-exists
    probe (raw TOM exposes `FromTable`/`ToTable` on the typed subclass, not the base).
    Future scripts use the new form from the start.
  - **Build/deploy:** source project checked in at `GEP/scripts/pbi_model_apply/`;
    `bin/`/`obj/` gitignored; Paul runs `dotnet build -c Release` once (~90s first time
    with NuGet restore). Skill invokes `bin/Release/net8.0-windows/pbi_model_apply.exe`.
  - **CLI:** `--script / --workspace / --dataset / --token [--dry-run --timeout --verbose]`.
    Discrete args not one connection string — keeps wrapper in charge of formatting,
    makes the token easy to redact at the caller, matches how §G already resolves these
    from config.
  - **Exit codes:** 0 success, 1 script runtime, 2 auth/401, 3 connection, 4 Roslyn
    compile, 5 model locked, 6 invalid args, 99 unexpected — so §G can react distinctly
    (retry auth after re-acquiring token; don't retry compile errors; tell Paul to
    close TE3 GUI on lock errors).
  - **§G rewrite:** command-line replacement only — token acquisition (§I), config
    reads, token redaction on display, retry-on-401 all stay identical. Heading renames
    from "Tabular Editor CLI helper" to "PBI Model Apply helper".
  - **Config:** new `pbi_model_apply_path` top-level key in `pbi_config.yaml`;
    existing `tabular_editor_path` stays (still referenced by `pbi_scan.py`).
- highest-risk unknowns surfaced to Paul (see plan §11):
  1. 🔴 `Microsoft.AnalysisServices.NetCore.retail.amd64` + bearer token + GEP's
     PPU XMLA endpoint end-to-end — confirmed at API surface, unconfirmed on this
     specific capacity/tenant. Plan §11.4 has a 30-line standalone repro Paul can run
     in ~5 minutes to de-risk before the implementation session.
  2. 🟡 .NET 8 *SDK* (not just runtime) on Paul's machine — `dotnet --list-sdks`
     check, 30 seconds.
  3. 🟡 Roslyn `CSharpScript.RunAsync` with `WithImports("PbiModelApply")` resolving
     extension methods without a `using` in the script body. Documented working in
     Roslyn 4.11; fallback is to prepend one line to the script at load time.
- no code or skill changes in this session (planning only per boot prompt).
- wiki touches (plan doc + index + log; NO changes to `gep-feature.md` or any
  `GEP/scripts/` file; no edits to [[pbi-xmla-model-changes]] yet — that update happens
  in the implementation session).
- next: Sonnet implementation session booted from [[pbi-model-apply-wrapper]]. If Paul
  runs the §11.4 repro before it starts and it prints "Connected. Model has N tables.",
  the session should go straight through §3/§4/§6 with zero clarifying questions.
  Acceptance test is GP-208 sandbox apply → refresh → rows>0 (§7 of the plan).

### 2026-04-23 — Phase 6 MSAL pre-flight repro: Path-1 auth confirmed ✅ (Sonnet)

- goal: narrow the §11.1 risk from [[pbi-model-apply-wrapper]] — does TOM on .NET 8 accept
  a bearer token on GEP's PPU XMLA endpoint, and from which token source?
- outcome: **Path-1 confirmed.** MSAL device-code with PBI public client ID
  `ea0616ba-638b-4df5-95b9-636659ae5121` works end-to-end:
  - `appid=ea0616ba-...`, `aud=https://analysis.windows.net/powerbi/api` accepted.
  - `GEP_Sandbox_Current` found; model has **32 tables** (confirmed live).
  - Workspace: `GEP Sandbox Models`, dataset ID: `fb41970d-2beb-4ed9-9f82-35c6439b35ea`.
- confirmed broken: `az account get-access-token` bearer token — XMLA rejects it.
  Token's `appid=04b07795-...` (Azure CLI) is not an approved XMLA client.
  REST calls (§H) still work with `az` tokens. This is purely an XMLA restriction.
- three TOM implementation gotchas discovered and documented in [[pbi-model-apply-wrapper]] §11.1:
  1. `using Microsoft.AnalysisServices` + `using Microsoft.AnalysisServices.Tabular` →
     ambiguous `Server` → use `Microsoft.AnalysisServices.Tabular.Server` fully-qualified.
  2. `server.Databases["name"]` indexes by internal AS **ID** (GUID), not display `Name` →
     use `server.Databases.Cast<Database>().FirstOrDefault(d => d.Name == name)`.
  3. `AccessToken` ctor: use `DateTimeOffset`, not `DateTime`.
- plan delta proposed (awaiting Paul approval before applying):
  - Remove `--token` CLI arg from wrapper. Wrapper owns MSAL auth internally.
  - Add §I-XMLA (MSAL device-code, `ea0616ba-...` client, disk cache via
    `Microsoft.Identity.Client.Extensions.Msal`). Silent re-use within ~1h.
  - §I stays for REST (§H) unchanged. §G calls wrapper without passing token.
  - Add `--clear-token-cache` optional flag. Remove redaction step from §G display.
- wiki updates: [[pbi-model-apply-wrapper]] Q1b/Q3d/§3.1/§3.2/§3.2b/§3.4/§3.7/§3.8/
  §5.1/§6.1/§7.2/§11.1 all revised; [[phase6-pbi-automation-plan]] §I + §5a corrected.
- repro artefact: `C:\Users\PaulRussell\tom-repro\` (not in clients repo — standalone repro only).
- next: approve plan delta → Sonnet implementation session for `pbi_model_apply` wrapper.

### 2026-04-22/23 — Phase 6 GP-208 dry-run: Sub-step 1b in progress 🟡 (Sonnet)

- did: first real-ticket dry-run of Phase 6 (Sub-step 1b PBI sandbox validation) using GP-208. Completed: artifact created, Sellercloud blocker confirmed resolved, sandbox SQL deployed + validated (9/9 ✅, 16,736 rows), sandbox dataset rebound to `SANDBOX_DG1_GEP_GP208`, MODEL SCAN implemented via `pbi_scan.py` (REST fallback, TE3 path disabled — see blockers). Both `INVENTORY_FCT_BALANCE` and `EXTRACT_INVENTORY_CURRENT` tables added to sandbox dataset via TE3 GUI. Refresh triggered multiple times.
- **Blocked:** Tables refresh with "no columns" despite `Inventory Balance` (same connection) working. Most likely cause: partition type is DAX instead of M Query. Fix: open TE3 → verify partition type → change to M Query → paste correct expression → save → refresh.
- key discoveries — **all documented in [[pbi-xmla-model-changes]]**:
  1. **TE3 CLI (`/s /x`) does not work from any subprocess context** — TE3 is a Windows GUI app (PE subsystem 2) with a WebView2 browser component. When launched as a subprocess (Python, PowerShell, bash), the message loop is never pumped. Hang confirmed across 10+ approaches including: Python subprocess, PowerShell `Start-Process`, bash `timeout`, clearing WebView2 cache, disabling startup network calls, forced invalid preferences, direct positional args, porter token injection via ADOMD.NET. Workaround: Paul runs TE3 GUI manually and applies C# scripts from the scripting panel.
  2. **GEP M expression uses `PARAM_SHORT_CODE`** (not `SNOWFLAKE_DATABASE`) for the database parameter. Discovered by reading `Inventory Balance` partition expression. `PARAM_SHORT_CODE` is an M computed expression that resolves to the active Snowflake DB. `SNOWFLAKE_DATABASE` is a dataset parameter used only by the REST API rebind (`UpdateParameters`). All future TE scripts must use `PARAM_SHORT_CODE`.
  3. **C# script API differences TE2 vs TE3** — `Model.AddRelationship()` and `Model.SaveChanges()` don't exist in TE3; `Model.Database.Update()` is the save equivalent; `AddRelationship` takes 2 column arguments not 4.
  4. **Partition type gotcha** — `Model.AddTable()` in TE3 C# scripting may create a DAX partition by default. M expressions pasted into a DAX partition silently fail during refresh (table exists but "has no columns"). Must verify partition type in TE3 GUI before pasting M expression.
  5. **GEP PBI naming convention** — model uses Title Case display names (`Inventory Balance`, `Order Line`) not Snowflake identifiers (`INVENTORY_FCT_BALANCE`). Existing hidden `Inventory Balance` and `Inventory Measures` tables were discovered. New tables added with Snowflake names for now; renaming deferred. Filed to [[potential-tickets]].
  6. **pbi_scan.py TE3 path disabled** — `if False` guard added to prevent TE3 subprocess launch from spawning hung windows. REST scan path works for existence check + row count of queryable tables. TE3 path will be re-enabled when CLI automation is fixed.
- new wiki pages: [[pbi-xmla-model-changes]] (TE3 CLI findings, GEP M expression conventions, Sub-step 1b status, future fix directions)
- new potential tickets: pbi_scan.py requires TE3, GEP PBI naming convention not followed, share stability 2 new incidents (CURRENT_FORECAST_CSV + CURRENT_REPORT_ALL_ORDERS_UK recurrence)
- artifact: `GEP/tickets/GP-208/artifact.yaml` — stage: `implementing`, decisions logged, sandbox validate_pass: "9/9"
- next: **boot prompt below — "Phase 6 Sub-step 1b fix" — fix partition type in TE3 GUI**

### 2026-04-22 — Phase 6 Tranche C implementation complete ✅ (Sonnet)

- did: implemented Tranche C (§C.1–§C.4) in `.claude/commands/gep-feature.md`.
- changes:
  - **C.1** — `scoped` step 2b extended: after PBI yes/no, asks whether changes are
    `visual-included` or `metadata-only`; records `changes.pbi_model.visual_required`.
  - **C.2** — `Sub-step 1b — PBI sandbox model validation` inserted in `implementing`
    between sandbox teardown and Sub-step 2. Full gate/pre-flight/rebind/TE CLI apply/
    refresh poll/visual check/record outcome flow per plan §3.3.
  - **C.3** — `PBI model promotion to GEP Test Models` block inserted at the end of
    Sub-step 2: gates on `sandbox_validated`, uses §G + §H to apply script and refresh
    TEST dataset, records `test_applied_at` / `test_refresh_id`.
  - **C.4** — `test-deployed` step 3 refined: checks `test_applied_at`; skips manual
    refresh prompt if auto-apply already ran; still requires manual visual pass/fail.
- file size: 1,131 → 1,284 lines (+153 lines).
- context: Paul wants to use GP-208 (Inventory Feed Intake & Modelling, Phase 1) as
  the first real-ticket dry-run of Tranche C. Old GP-208 SQL from a prior abandoned
  attempt (2025, tried to combine current + historical inventory) is stale and ignored.
  GP-208 will start from scratch at the scoping stage.
- ready to commit (Paul owns): `.claude/commands/gep-feature.md`
  Suggested commit: `feat(skill): Phase 6 Tranche C — Sub-step 1b PBI sandbox validation + TEST promotion tail`
- next: fill `pbi_config.yaml` test.* and prod.* workspace IDs, then run
  `/gep-feature GP-208` to start the ticket from scoping.

### 2026-04-21 — Phase 6 Tranche A + B execution complete ✅ (Opus main + Sonnet subagent, live UI work with Paul)

- did: executed plan Tranches A (external setup + seed script) + B (skill primitives) end-to-end. Sandbox PBI workspace created, seed dataset uploaded, XMLA write confirmed.
- key artefacts:
  - Azure CLI 2.85.0 installed via `winget install Microsoft.AzureCLI`
  - Tabular Editor 2.28.0 installed via MSI from github.com/TabularEditor/TabularEditor/releases/2.28.0 (winget only ships TE 3 commercial)
  - Power BI workspace **GEP Sandbox Models** created (PPU, Large semantic model format) — id `8545f3cb-4e2d-4985-bf31-79066248c9be`
  - Seed PBIX `GEP/scripts/_pbi_seed/GEP_Sandbox_Template.pbix` (330 MB, gitignored) — copied from `repos/power_bi/custom/GEP/2026_03 Data Model/Data Model.pbix`
  - Seed dataset **GEP_Sandbox_Current** uploaded to sandbox workspace — id `fb41970d-2beb-4ed9-9f82-35c6439b35ea`
  - `GEP/scripts/pbi_seed_sandbox.py` (371 lines) written by Sonnet subagent, 2 Windows Python bugfixes added during live run (see below)
  - `GEP/scripts/pbi_config.yaml` populated with tenant + sandbox IDs; `pbi_config.example.yaml` committed as schema reference
  - `.claude/commands/gep-feature.md` extended with §G Tabular Editor CLI helper / §H PBI REST helper / §I Azure CLI bearer token helper + Phase 6 artefact schema fields + rules 9–11
- execution flow highlights:
  - Tranche B (skill primitives + seed script code) was handed off to a Sonnet subagent with the plan file as authoritative spec — subagent produced all three deliverables in one pass per plan §3.8 / §3.10 / §3.11 / §6.1. Zero ambiguity surfaced.
  - Azure CLI install ran in parallel with the subagent; both completed cleanly.
  - First seed-script run failed with `FileNotFoundError` on `subprocess.run(["az", ...])` — classic Windows Python subprocess gotcha: Windows `CreateProcess` doesn't resolve `.cmd` via PATHEXT. Added two fixes: `shutil.which("az")` + fallback to `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd` (handles stale PATH in terminals that predate the install).
  - Second run succeeded end-to-end — 97.5s upload of 330 MB PBIX, 11s import, parameter verification passed, config updated. Dataset ID auto-populated to `pbi_config.yaml`.
  - XMLA smoke test: opened GEP_Sandbox_Current in Tabular Editor 2 via `powerbi://api.powerbi.com/v1.0/myorg/GEP Sandbox Models`, edited a description, Ctrl+S saved quietly with no error → **XMLA Read/Write confirmed active on GEP's PPU capacity.**
- discoveries surfaced during A.0.6 (PBIX parameterisation):
  - **`PARAM_SHORT_CODE` design pattern.** The live GEP PBIX resolves the Snowflake DB name dynamically via a query called `PARAM_SHORT_CODE` that calls core_api `/v1/report/describe` to fetch the tenant's short code. This was NOT a plain text parameter (as the plan had assumed). A.0.6 simplified from "rewrite every table query" to "rewrite PARAM_SHORT_CODE to return SNOWFLAKE_DATABASE + rewrite 2 hardcoded queries (Campaign, Platform)" — total 3 M edits instead of 17. `SNOWFLAKE_ROLE` added as a parameter but currently unreferenced in M; kept for forward compat (role is set at credential level today).
  - **`_BASE_ACT_SALE_RET` DAX error.** Pre-existing tech debt in the live TEST PBIX — a base/hidden measure references a column that doesn't exist in its expected table. Not caused by our edits (we only changed Source + Tenant_Database steps). Filed to [[potential-tickets]].
  - **Committed credential in PBIX: `CORE_API_CLIENT_TOKEN`.** Value `RkZGRkZGRkYwMDAwOmFsRGM5ODc2IQ==` (base64 of `FFFFFFFF0000:alDc9876!`) is baked into every dated GEP PBIX in `repos/power_bi/custom/GEP/`. Wiki rule #2 violation — should be vaulted and rotated. Filed to [[potential-tickets]].
  - **core_api transient error** during test refresh: `field 'capacity' of the record wasn't found` from `/v1/report/describe` — flaky response from core_api TEST instance. Unrelated to sandbox work; the 4 core_api-backed queries (API Metadata, Report Metadata, Report Glossary, Report Configuration) can be excluded from refresh if they become blocking.
- what's live vs what's still planned:
  - ✅ Tranche A (external setup + seed script + smoke test) — **done**
  - ✅ Tranche B (skill helpers + artefact fields + rules) — **done, no behaviour change yet**
  - 🟡 Tranche C (Sub-step 1b insertion in `implementing`, Sub-step 2 TEST apply tail, `test-deployed` step 3 refinement) — **next session, requires Sonnet execution against plan §3.3/§3.5/§3.6**
  - 🟡 Tranche D (`prod-deployed` conditional auto-apply) — **after C is dogfooded on a real ticket**
  - 🟡 Tranche E (wiki docs: new `pbi-xmla-automation.md` pattern page, SSMS.md + power-bi.md data-flow correction, runbook updates)
- ready to commit (Paul owns): `.claude/commands/gep-feature.md`, `.gitignore`, `GEP/scripts/pbi_config.example.yaml`, `GEP/scripts/pbi_seed_sandbox.py`. Suggested commits in 3 groups (see chat recap).
- next: Tranche C execution when Paul has a PBI-touching ticket to validate on. Fill `pbi_config.yaml` `test.*` and `prod.*` workspace IDs before then.

### 2026-04-21 — Phase 6 planning session complete ✅ (Opus, xhigh effort)

- did: read wiki CLAUDE.md, tracker, workflow-automation.md §3.2/§3.6, current `gep-feature.md`, and the open "Multi-feature conflict in TEST / PBI" blocker. Produced a detailed Phase 6 plan covering PBI model automation via XMLA write.
- plan location: `wiki/processes/distributed-workflow/active/phase6-pbi-automation-plan.md` (sibling of this tracker).
- decisions:
  - **Sandbox isolation model** = Option B — one persistent `GEP Sandbox Models` workspace with one persistent `GEP_Sandbox_Current` dataset, rebound at runtime to the per-ticket Snowflake sandbox DB via `Update Parameters`. Rejected per-ticket workspace clones (Option A — capacity cost + provisioning overhead) and file-only (Option C — doesn't catch refresh/data errors). TMDL version-control (Option D) deferred to v2.
  - **Automation depth** = Level 2 for v1 — skill runs Tabular Editor CLI directly to apply model changes to the sandbox dataset, triggers REST refresh, polls until complete, Paul reviews visuals then promotes. Level 3 (Deployment Pipelines) deferred because pipeline existence on GEP's workspace is unconfirmed and visual regression isn't API-addressable anyway.
  - **Workflow insertion** = new Sub-step 1b in `implementing`, gated on `changes.pbi_model.required == true`. Fires only when needed; silent no-op otherwise. Sub-step 2 gets a TE CLI apply + refresh tail to promote the same validated script to the TEST dataset. `prod-deployed` PBI publish gate becomes auto-apply for metadata-only changes (if new `visual_required == false`) and stays manual for visual-included changes.
  - **Artefact schema additions** — extend `changes.pbi_model` with `visual_required`, `script_path`, `script_hash`, `sandbox_validated`, `sandbox_applied_at`, `sandbox_refresh_id`, `test_applied_at`, `test_refresh_id`, `prod_applied_at`, `prod_refresh_id`, `findings`. New `pbi_config` top-level config block for workspace/dataset IDs and TE path.
  - **Two new MCP-setup subsections** — §G (Tabular Editor CLI helper) and §H (PBI REST helper — token acquisition, `Update Parameters`, `Refreshes`, poll). §H failures BLOCK the stage (critical path), distinguishing it from §B (Jira MCP, non-blocking).
  - **Rules 9–11** — script hash drift detection, sandbox-is-shared-mutable discipline, PBI REST failures block the stage.
- open questions for Paul (blockers 1–4, shaping 5–9):
  1. Premium/PPU/Fabric capacity SKU?
  2. Tabular Editor install path (TE 2 free or TE 3)?
  3. SPN available for the workflow, or fall back to user OAuth?
  4. Current GEP PBIX connects directly to Snowflake, or via SQL Server?
  5. Sandbox workspace seed — Paul does manually or scripted as part of v1?
  6. Deployment Pipelines already configured on GEP's workspace?
  7. TMDL vs BIM preference (v2 only)?
  8. Where does `pbi_config` live — `.gep-feature-config.yaml`, env vars, or `GEP/scripts/.env`?
  9. `visual_required` flag — edge cases to document?
- resolves the "Multi-feature conflict in TEST / PBI" blocker on the PBI half. Snowflake TEST serialisation stays operational (already mitigated by Phase 4 checklist + rollback).
- implementation order: Tranche A (external setup, Paul-owned) → Tranche B (skill primitives, no behaviour change) → Tranche C (Sub-step 1b + Sub-step 2 tail, the main behaviour change) → Tranche D (`prod-deployed` conditional auto-apply) → Tranche E (wiki / runbook docs).
- Q&A round with Paul, same session (2026-04-21):
  - Q1 (capacity SKU): "think yes" — accept as Premium/PPU/Fabric implied by XMLA-write confirmation; verify in admin portal during Tranche A.0.1.
  - Q2 (Tabular Editor): not installed → **Tranche A.0.3 is explicit TE 2 install step**.
  - Q3 (SPN vs user OAuth): Paul has Azure AD license for PBI → **auth changed to user OAuth via Azure CLI bearer token (§I helper)**. Removes SPN registration, tenant-admin work, and any secret storage. ~1h token lifetime; re-acquire on 401.
  - Q5 (sandbox seed): scripted → **new deliverable `GEP/scripts/pbi_seed_sandbox.py`** handles `.pbix` upload + dataset ID discovery + `pbi_config.yaml` population. Idempotent so it doubles as sandbox reset.
  - Q4 (PBIX connection shape): **resolved 2026-04-21** — direct Snowflake, no SQL Server intermediate. Paul checked Data Source Settings: two sources, core_api URL (`aldctestfnapcore1c01...`) for glossary/metadata + `og35375.canada-central.azure.snowflakecomputing.com;COMPUTE_WH` direct Snowflake. The SSMS + power-bi wiki pages describe an "intermediate SQL Server DB" that does NOT exist in the GEP path — those pages are wrong and are tracked for correction in Tranche E.3.
  - Q4a (PBIX parameterisation): **resolved 2026-04-21**. Paul listed parameters: `CORE_API_REPORT_ID`, `CORE_API_ACCOUNT_ID`, `CORE_API_URL`, `CORE_API_CLIENT_TOKEN`, `SNOWFLAKE_HOST`, `SNOWFLAKE_COMPUTE`. **Gap:** no `SNOWFLAKE_DATABASE` or `SNOWFLAKE_ROLE` — the DB name is hardcoded in individual M queries. This blocks per-ticket sandbox DB rebinding unless we add the parameters. Resolution = Tranche A.0.6 (one-time seed PBIX parameterisation, ~15 min). See Q4b below — this also simplified A.0.6 scope.
  - Q4b (TEST vs Production PBIX): **resolved 2026-04-21**. Paul confirmed: "we need to point it to the prod host for the Production Model, this is the TEST PBI Data Model." **Two separate PBIX files exist, one per environment**, each pinning its own `SNOWFLAKE_HOST`. This means A.0.6 only needs to parameterise the **sandbox seed** (derived from TEST PBIX), NOT the live TEST or Production PBIX files. TEST dataset always points at TEST_DG1_GEP (hardcoded in its source PBIX); Production dataset always points at PROD_DG1_GEP (hardcoded in its source PBIX); neither needs rebinding — Sub-step 2 and Tranche D just apply the model script, datasource config untouched. **Zero risk to actively-deployed models from A.0.6.**
  - Q8 (config location): implicit — Paul opened `GEP/scripts/.env` in IDE while answering; plan now uses `GEP/scripts/pbi_config.yaml` (gitignored, structured) + optional `PBI_CONFIG_PATH` override in `.env`. No secrets in either file (tokens come from `az` at runtime).
- plan revisions (all in phase6-pbi-automation-plan.md):
  - §5 rewritten as answered/open status table
  - §5a new — "Revised auth plan" with user OAuth via `az account get-access-token`
  - §6.1 Tranche A rewritten — A.0 prerequisites (Paul, ~10 min) + A.1 scripted seed (`pbi_seed_sandbox.py`) + A.2 config file + A.3 smoke test
  - §3.10 §G/§H updated to pull bearer token from §I instead of SPN client-credentials flow
  - §I added — Azure CLI bearer token helper, session-cached, never-log discipline
  - §3.8 `pbi_config` block revised — no SPN client ID, no secrets
- next: all blocking questions resolved. Tranche A.0 prerequisites (Paul: capacity check, Azure CLI install, TE 2 install, sandbox workspace create, seed PBIX parameterisation per A.0.6) can start now. Tranches A.1–A.2 (scripted seed + config file) + Tranche B (skill primitives) follow in a Sonnet implementation session using the boot prompt below.

### 2026-04-21 — Phase 5 Tier 3 implementation complete ✅ (Sonnet, high effort)

- did: implemented all 7 items (8 logical commits) on `feature/paulrussell/workflow-automation/gep-scripted-deploy`. Files changed: `.gitignore`, `.claude/commands/gep-feature.md`.
- items completed (in spec order):
  - **Pre-item-7**: Added `GEP/tickets/*/_pr_body.md` to `.gitignore`
  - **Preamble §A–§D**: `## MCP setup` section added with cloudId resolution (§A), offline fallback (§B), confirm-and-post helper (§C). Artifact schema extended with `pr_url`, `pr_created_at`, `pr_jira_integration`, `changes.eclipse`, `changes.pbi_model`, `jira_sync`, `comments_posted`, `deploy_history.prod.data_dictionary_*`
  - **Item 8**: §E Jira status sync helper (8-step procedure: fetch status, no-op if already target, get transitions, confirm, call `transitionJiraIssue`, §B on failure). Wired at scoped→implementing ("In Progress"), test-deployed→uat ("In Review"), prod-deployed→complete ("Done"). `force` flag skips sync.
  - **Item 9**: Eclipse/PBI change tracking. `scoped` steps 2a/2b ask whether connector or model changes required. `implementing` Sub-step 1 gates on Eclipse precondition (yes/not-yet/skip-gate). `prod-deployed` PBI publish gate blocks `→complete` if PBIX unpublished. Old artifacts (no `changes` block) treated as `required: null` → all gates silently skipped.
  - **Item 7**: Full PR creation step at `test-deployed` step 4 — draft title+body, write `_pr_body.md`, show `gh pr create --body-file`, yes/edit-title/edit-body/skip options. Captures PR URL from stdout. Handles "already exists" stderr. Deletes temp file on success.
  - **Item 13**: GitHub-integration detection baked into step 4 tail — 60s poll of `getJiraIssueRemoteIssueLinks`, sets `pr_jira_integration = "native" | "via_comment" | null`. Rule 8 added (no `createIssueLink`).
  - **Item 11**: Design summary comment at `test-deployed` step 5 — full Markdown template (branch, PR URL, all requirements, decisions with alternatives, answered questions). §C confirm-and-post. Revision detection. §B queued fallback.
  - **Item 12**: §F QA evidence helper added to `## MCP setup`. JSON schema verified against validate.py source — flat `git` string, top-level `passed`/`total`, `checks[].passed`/`.display`. PASSING template (check table with pipe-escaping, 20-row truncation) and FINDINGS template. Invoked at test-deployed step 6 (env=test) and prod-deployed step 3b (env=prod).
  - **Item 10**: Data dictionary prompt at `prod-deployed` step 5 — case-insensitive `_FCT_`/`_DIM_` match on `requirements.delivery`, reads manifest for grain/pk/date/freshness, shows wiki path + cross-links. Multi-table loop. `later` defers with reminder printed at `complete`.
- schema verified (before coding): `validate_manifest/GP-208.yaml` field names (`primary_key`, `key_columns`, `date_column`, `freshness_days`, `product_key_column`) confirmed; `validate.py --save-results` JSON schema confirmed (differs from plan's expectation — `git` flat string not `{sha, msg}`, `passed`/`total` top-level not under `summary`; item 12 adjusted accordingly)
- suggested commits (8, one per item group):
  1. `chore: gitignore PR body temp files`
  2. `refactor(skill): add MCP setup section — cloudId resolution, offline fallback, comment helper, consolidated artifact schema`
  3. `feat(skill): Jira status transitions at stage boundaries with offline fallback (item 8)`
  4. `feat(skill): Eclipse/PBI change tracking at scoped + sandbox/prod gates (item 9)`
  5. `feat(skill): gh pr create step at test-deployed with artifact capture (item 7)`
  6. `feat(skill): Jira GitHub-integration detection after PR creation (item 13)`
  7. `feat(skill): design summary comment at test-deployed (item 11)`
  8. `feat(skill): QA evidence comment at test-deployed and prod-deployed (item 12); data dictionary prompt at prod-deployed (item 10)`

### 2026-04-21 — Phase 5 Tier 3 planning session complete ✅ (Opus, xhigh effort)

- did: read wiki CLAUDE.md, tracker, and current `.claude/commands/gep-feature.md` in full; loaded schemas for Atlassian MCP tools (`addCommentToJiraIssue`, `transitionJiraIssue`, `getTransitionsForJiraIssue`, `createIssueLink`, `getJiraIssueRemoteIssueLinks`, `getJiraIssue`); produced a detailed implementation plan for items 7–13 covering skill-file edits, artifact schema additions, MCP call signatures, interaction/sequencing, and edge cases per item.
- decisions:
  - **Cross-cutting preamble first.** Added §A (cloudId resolution), §B (offline fallback), §C (confirm-and-post helper), §D (consolidated artifact schema additions). All items reuse these rather than re-implement.
  - **Item 8 creates §E (Jira status sync) — a reusable procedure invoked at 3 transitions.** Handles already-in-target, missing transition, and MCP-offline gracefully (never blocks stage).
  - **Item 13 cannot use `createIssueLink`** (Jira-to-Jira only, not remote URLs). No `createRemoteIssueLink` tool is exposed in the available MCP suite. Resolution: rely on Jira's native GitHub integration (branch naming already satisfies) + always embed the PR URL in item 11's design summary comment. Item 13 is effectively a documentation rule + a one-time integration-detection probe after PR creation.
  - **Implementation order**: Preamble → Item 8 → Item 9 → Item 7 → Item 13 → Item 11 → Item 12 → Item 10. Rationale in plan.
  - **Sonnet session must verify two external schemas before implementing**: validate.py `--save-results` JSON structure (item 12), and validate manifest tables.* fields (item 10). Plan flags both.
- plan location: `wiki/processes/distributed-workflow/active/phase5-tier3-plan.md` (sibling of this tracker). Boot prompt below references it directly. 8 commits planned, one per preamble/item.
- next: fresh Sonnet session with Phase 5 Tier 3 — Implementation boot prompt. Read the plan file first.

### 2026-04-18 — bootstrap

- did: created this tracker; lane is intentionally narrow (two new pages, no edits to existing runbooks).
- decided: today is design only. No code, no edits to existing GEP processes.
- next: open a fresh Claude session with the boot prompt below; enter plan mode immediately and produce a structure for `entities/projects/workflow-automation.md` for Paul to approve before drafting.

### 2026-04-18 — design session complete

- did: read all 10 required + optional context pages; entered plan mode; proposed 7-section design doc structure; surfaced sandbox-scope question; received Paul's decisions; wrote `entities/projects/workflow-automation.md` and `concepts/patterns/sandbox-feature-delivery.md`.
- decided: sandbox = Option B (TEST_DG1_GEP + per-feature schemas); v1 priorities = scripted SQL deploy + validation suite + AI-assisted requirements Q&A; share freshness monitoring deferred to v2 ops ticket.
- next: implementation workstream — start with Phase 1 (`deploy.py`). Natural first use case is GP-208 PROD deploy once Sellercloud share is restored. Launch with Sonnet (execution session, plan already exists).

### 2026-04-21 — Phase 5 Tier 1+2 complete ✅ + feature-update dry-run complete ✅

- did: feature-update dry-run on GP-197 (Ireland exclusion CR). Surfaced 5 new gaps during the run; all fixed and committed. Also implemented Phase 5 Tier 1+2 items (6 commits).
- gaps surfaced and fixed during dry-run:
  1. Missing deploy + validate manifests for GP-197 → created both; confirmed skill creates them at `scoped` stage for future tickets
  2. SQL not confirmed before deploy → added confirmation prompt to Sub-step 1 (Phase 4 fix, committed earlier)
  3. Dynamic country subquery used `SALES_DIM_ORDER` (all channels) → corrected to `SALES_FCT_AMAZON_ORDERLINE` with NULL guard
  4. `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK` missing from share → added `--check-share` flag to deploy.py; added to [[potential-tickets]]
  5. Git state invisible at validate time → added same SHA + commit message header to validate.py
- phase 5 commits: git header in validate.py, sandbox teardown prompt, SQL confirmation before TEST deploy, `--check-share` flag, `--save-results` flag + artifact schema formalised with sandbox field
- GP-197 sandbox validate: 15/15 ✅ (IE excluded, GB present, US/CA/MX regression pass)
- decisions:
  - Negative commission/shipping fees are legitimate Amazon refund rows — manifest asserts changed to threshold monitors (< 10k), not zero
  - `SALES_FCT_AMAZON_ORDERLINE` confirmed as correct country source via INFORMATION_SCHEMA query (ADDRESS_SHIP_COUNTRY col 19 of 46)
- new wiki pages: [[GP-PENDING-data-share-stability]], entry in [[potential-tickets]]
- next: Phase 5 Tier 3 (PR creation, Jira transitions, Eclipse/PBI tracking) in a fresh session. Boot from Phase 5 boot prompt above.

### 2026-04-20 — Phase 4 hardening complete ✅

- did: implemented all 5 hardening items on `feature/paulrussell/workflow-automation/gep-scripted-deploy`.
  1. `validate.py` — `check_tables_exist()` pre-check added; skips universal checks with WARN for tables not yet in INFORMATION_SCHEMA (new-table tickets).
  2. `deploy.py` — `snapshot_views()` exception handler now distinguishes "object does not exist" errors (002003) from other failures; prints "new view — no rollback point exists" instead of generic WARN.
  3. Skill (`gep-feature.md`) — backward stage transition guard added to OPEN mode; shows current stage + blocks backward moves; `force` flag bypasses; `feature-update` exempt.
  4. Skill — Jira MCP graceful fallback added to LIST mode and scoping Step 1; offline mode with `[manual entry required]` placeholders.
  5. `GEP/tickets/README.md` created (TEST serialisation checklist); skill Sub-step 2 now runs `grep -l "stage: uat"` and warns before TEST deploy if another ticket is in UAT.
- files changed: `GEP/scripts/validate.py`, `GEP/scripts/deploy.py`, `.claude/commands/gep-feature.md`, `GEP/tickets/README.md` (new)
- next: commit each item separately (suggested messages below); then the workflow is ready for the next ticket.

**Suggested commits (stage each file separately):**
1. `fix(validate): skip universal checks with clear warning if target table does not exist`
2. `fix(deploy): clarify new-view message in snapshot_views instead of generic WARN`
3. `fix(skill): add backward stage transition guard with force bypass`
4. `fix(skill): add Jira MCP graceful fallback for offline/unreachable Jira`
5. `feat(process): TEST serialisation checklist in GEP/tickets/README.md + skill warning at TEST deploy`

### 2026-04-20 — Phase 3 end-to-end test complete ✅ (GP-197)

- did: tested full `/gep-feature` workflow end-to-end using GP-197 as the live ticket. Completed: Jira fetch, scoping Q&A, artifact, branch creation, deploy/validate manifests, sandbox deploy (9/9 validate), TEST deploy (10/10 task steps), PBI refresh confirmed. Surfaced and fixed 7 gaps during the run:
  1. Deploy + validate manifests not auto-created at scoped stage → fixed in skill
  2. Skill had no sandbox-vs-TEST distinction → fixed (sandbox = dev validation, TEST = client-visible)
  3. Validate manifest had no universal checks and weak ticket checks → fixed (5-category standard)
  4. TEST deployed to `WAREHOUSE_TEST_<ticket>` (invisible to PBI + task chain) → fixed (deploys to WAREHOUSE_SOURCE directly; rollback is safety net)
  5. No rollback mechanism → implemented in deploy.py (auto-snapshot + `--rollback` flag)
  6. No PBI smoke-test prompt → added to test-deployed stage in skill
  7. Infrastructure changes mixed with ticket changes on GP-197 branch → separated via cherry-pick; automation branch now clean and self-contained
- decided: TEST deploy goes directly to WAREHOUSE_SOURCE (not per-ticket schema). Rollback replaces schema isolation as the safety mechanism.
- GP-197 status: in UAT. PBI confirmed 2026-04-20. validate.py on TEST still pending (run before PROD deploy).
- next: hardening pass on automation branch before using with next ticket. See boot prompt below.

### 2026-04-18 — Phase 3 design approved ✅

- did: expanded Phase 3 design from "question generator script" to stateful feature workflow system. Updated design doc §2.4 and added §3.7 (full design sketch including artifact schema, stage model, Jira MCP integration, re-entry mechanism, wiki/Obsidian integration). Updated §5 and §6.
- decided: Claude Code skill (`/gep-feature`); artifact in `GEP/tickets/<ticket>/`; Jira filtered to `paul.russell@aldc.io`; Jira comments require Paul's approval before posting; multi-round `feature-update` supported.
- next: implement the `/gep-feature` skill. Start with the artifact schema and scoping stage; Jira MCP and wiki integration follow.

### 2026-04-18 — Phase 2 implementation complete ✅

- did: implemented `GEP/scripts/validate.py` and `GEP/scripts/validate_manifest/GP-208.yaml` on same branch. First live run against `TEST_DG1_GEP.WAREHOUSE.INVENTORY_FCT_BALANCE` returned 7/9 checks passing.
- discovered (column names in design doc §3.5 were wrong — corrected in YAML):
  - `GEP2_ON_HAND_QTY` → `GEP2_ON_HAND_QUANTITY`
  - `US_FBA_AVAILABLE_QTY` → `FBA_AVAILABLE_QUANTITY`
  - No `SOURCE` column exists — FBA vs Sellercloud split is implicit. Replaced `WHERE SOURCE = 'AMAZON_FBA'` check with FBA presence check (`FBA_AVAILABLE_QUANTITY IS NOT NULL`).
- real data findings surfaced by harness (not script bugs — current branch has no GP-208 changes):
  - **762 null `BALANCE_DATE` rows**: products appearing only via `DAILY_PRODUCT_SALES` CTE with no matching inventory row; `ARRAY_MIN` of all-null dates returns null.
  - **3 rows with negative `GEP2_ON_HAND_QUANTITY`**: Sellercloud reporting negative on-hand for 3 products; likely returns/adjustment edge case.
- files: `GEP/scripts/validate.py`, `GEP/scripts/validate_manifest/GP-208.yaml`
- next: Phase 3 (scoper.py) or GP-208 PROD deploy — Paul to decide priority.

### 2026-04-18 — Phase 1 implementation complete ✅

- did: implemented `GEP/scripts/deploy.py` and `GEP/scripts/deploy_manifest/` on branch `feature/paulrussell/workflow-automation/gep-scripted-deploy`. Full end-to-end test run against GP-208 in sandbox succeeded — all 10 task chain steps SUCCEEDED.
- decided (implementation discoveries, overriding original design):
  - **Sandbox is per-feature DATABASE clone** (not per-feature schema within TEST). `SANDBOX_DG1_GEP_<ticket>` cloned from `TEST_DG1_GEP` via zero-copy clone. Full task chain isolation confirmed (all task definitions reference sandbox DB after clone).
  - **Two Snowflake accounts**: `og35375` (non-prod: TEST, sandbox) and `wj66376` (prod). `.env` uses `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_ACCOUNT_PROD` separately.
  - **Per-file schema routing** in manifest (`schema: WAREHOUSE_SOURCE`). Files deploy to the schema the task chain reads from, not a generic sandbox schema.
  - **Task chain is opt-in** (`--run-task` flag). Default is SQL-only deploy.
  - **Sellercloud share was restored** during this session — `CURRENT_MAIN_INVENTORY_PANDL` back in PROD share with 6.5M rows.
  - **MFA auth**: `SNOWFLAKE_AUTHENTICATOR=username_password_mfa`, username `paulrussell`.
  - **TASK_OWNER_ROLE**: `TEST_DG1_ROLE_CORE_SVC_DA8904DB` — hardcoded constant in deploy.py; sandbox clone grants FUTURE privileges to this role.
- committed: `GEP/scripts/deploy.py`, `GEP/scripts/.env.example`, `GEP/scripts/deploy_manifest/GP-208.yaml`, `GEP/scripts/deploy_manifest/GP-BENCH-01.yaml`, `GEP/snowflake/warehouse/workflow_bench_smoke.sql`
- next: Phase 2 — validation suite (`validate.py`). Boot prompt below.

### 2026-05-02 — Option A monitoring layer: monitor.py, flight_check.py, deploy extensions, /session-open + /session-close skills

- did: Built Option A Phase A1+A2 of the workflow automation roadmap. Created `monitor.py` (freshness, task health, share integrity), `flight_check.py` (full operational health check replacing manual flight-check), `monitor_config.yaml` (GEP thresholds). Extended `deploy.py` with `MONITORING.DEPLOY_LOG` recording + prod promotion gate (`--force`). Extended `validate.py` with `--compare` for cross-env row count comparison. Created `workflow-analysis-current-vs-future.md` with 8 Mermaid diagrams, 27 gap items, 3 implementation options. Wired `§K Flight Check helper` into `/gep-feature` at test-deployed and prod-deployed stages. Built `/session-open` and `/session-close` skills. Scheduled weekly "GEP Prod Weekly Flight Check" remote agent (Mondays 08:00 UTC).
- decided: Option A (incremental automation) over Option B (data quality platform) or Option C (full CI/CD). Flight check failures are safety nets not gates — they never hard-block a stage. Remote flight check agent posts Jira checklists since it can't access Snowflake directly.
- next: Dogfood `/session-open` and `/session-close` next session. Remaining Option A gaps: schema diff (`deploy.py --diff`), connector validation suite, token expiry tracker. Tracker template v2 (phase-aligned layout matching Jira states) deferred to next session.

## Decisions Log

- 2026-04-18 — Output of this workstream is design artifacts only on first pass. Implementation is a separate follow-on workstream gated on Paul's design approval.
- 2026-04-18 — Lane intentionally excludes existing GEP runbooks. Any required changes there go through *Cross-Lane Request* + Paul, not silent edits — the runbooks are load-bearing for active deploys.
- 2026-04-18 — **Sandbox scope confirmed**: Option B — TEST_DG1_GEP + per-feature schemas (`WAREHOUSE_TEST_<ticket>`). PBI validation remains manual; Snowflake half fully automated. True ephemeral not practical due to PBI API limitations.
- 2026-04-18 — **v1 priorities confirmed**: (1) Scripted SQL deploy + task-chain trigger, (2) Structured validation suite, (3) AI-assisted requirements Q&A.
- 2026-04-18 — **Share freshness monitoring deferred**: technically the quickest win (single Snowflake task), but deliberately excluded from v1 scope. Pick up as a standalone ops ticket after v1 ships.
- 2026-04-18 — **Design approved**: `entities/projects/workflow-automation.md` written and approved. Plan-mode-first rule lifted for future implementation sessions (per Plan-Mode Rule: plan-mode only until design exists).
- 2026-04-18 — **Sandbox redesigned to per-feature DB clone**: original design used per-feature schema within TEST_DG1_GEP; upgraded to full database clone (`SANDBOX_DG1_GEP_<ticket>`) for complete task chain isolation. Zero-copy clone is fast and cheap; teardown drops the entire DB.
- 2026-04-18 — **Phase 1 shipped**: `deploy.py` committed to `feature/paulrussell/workflow-automation/gep-scripted-deploy`. GP-208 full end-to-end validated in sandbox — 10/10 task steps SUCCEEDED.
- 2026-04-18 — **Phase 2 shipped**: `validate.py` + `validate_manifest/GP-208.yaml` committed. 9 checks (6 universal + 3 ticket-specific). Design doc column names were wrong — corrected against real schema. Two known data findings in current TEST state (762 null BALANCE_DATE, 3 negative GEP2_ON_HAND_QUANTITY).
- 2026-04-18 — **Phase 3 design expanded**: original "scoper.py CLI" replaced with a stateful feature workflow system. Key additions: full stage model, per-ticket artifact (`GEP/tickets/<ticket>/artifact.yaml`), Jira MCP (filtered to paul.russell@aldc.io), re-entry via `feature-update` stage, wiki/Obsidian integration after each stage transition. Design approved and documented in §2.4 + §3.7 of `entities/projects/workflow-automation.md`.

## Pending Wiki Updates

_These touch shared files (index.md, log.md) and should be applied in the next end-of-day merge session._

- **index.md** — add under `## Entities > Projects`:
  `- [[workflow-automation]] — Client workflow automation design. Scripted deploy, validation harness, AI-assisted scoping. GEP v1 target.`
- **index.md** — add under `## Concepts > Patterns`:
  `- [[sandbox-feature-delivery]] — Per-feature Snowflake schema pattern for isolating in-flight deploys within a shared test environment.`
- **log.md** — append:
  `| 2026-04-18 | design | Wrote entities/projects/workflow-automation.md and concepts/patterns/sandbox-feature-delivery.md. Design session for client workflow automation workstream. |`
  `| 2026-04-18 | implement | Phase 2: validate.py + validate_manifest/GP-208.yaml. 9 checks (6 universal + 3 ticket-specific). First live run 7/9 passing; 2 known data findings in current TEST state. |`

## Blockers / Open Questions

_Sandbox-scope question resolved 2026-04-18._

### ✅ Resolved 2026-04-24 — Multi-feature conflict in TEST / PBI

**Status:** PBI half resolved end-to-end. Snowflake half remains operational coordination.

**PBI half (resolved):** Phase 6 shipped. New tickets with PBI model changes now validate against an isolated sandbox dataset (`GEP_Sandbox_Current` in the `GEP Sandbox Models` workspace) via `pbi_model_apply.exe` + REST refresh BEFORE anything touches the client-facing `GEP Test Models` workspace. GP-208 was the acceptance test — 16,736 + 16,560 rows loaded into the sandbox dataset on 2026-04-24. See [[pbi-xmla-automation]] for the pattern and the 2026-04-24 session log in this tracker for execution detail.

**Snowflake half (unchanged — accepted v1):** TEST_DG1_GEP is still a shared environment across tickets. Mitigated operationally by the TEST serialisation checklist added in Phase 4 and the rollback in `deploy.py`. Per-ticket Snowflake TEST isolation is not pursued — sandbox Snowflake DBs (`SANDBOX_DG1_GEP_<ticket>`) already provide per-ticket isolation before the TEST promotion gate, so tickets only collide in TEST when multiple are simultaneously promoted to UAT. That's rare in practice and easier to coordinate than to automate.

---

**Problem**: TEST_DG1_GEP is a shared environment. When multiple features are deployed
to TEST simultaneously, they can conflict in the WAREHOUSE schema. Worse, the PBI Test
Model (shared with clients for UAT) connects to TEST — so a broken or partially-deployed
TEST directly impacts a client in the middle of user-testing another feature.

**Root cause**: there is no per-feature isolation at the PBI layer. Sandbox gives full
Snowflake isolation (per-feature DB clone) but PBI cannot be isolated programmatically
(no public API for workspace provisioning or `.pbix` deploy). See design doc §3.2 and §3.6.

**What Paul wants**: PBI Data Model changes visible and isolated in sandbox, so each
feature can be fully validated in isolation before touching the shared TEST/PBI layer.
Clients always validate through the PBI Test Model — Snowflake-only validation is
insufficient for client sign-off.

**Why it's hard**: Microsoft's Power BI REST API does not support programmatic workspace
creation, `.pbix` deployment, or data source rebinding at the workspace level. All of
this is manual browser UI. This is the same constraint that prevented "true ephemeral"
sandbox in the original design.

**Partial mitigations available today**:
- Serialise TEST deploys — only one feature in TEST at a time (operational, not technical)
- Coordinate with client on UAT timing before deploying a second feature to TEST
- TEST rollback (now implemented in deploy.py) — quick restore if a second feature
  deploy breaks something a client is actively testing

**What a real fix looks like** (future work):
- Power BI Embedded / Fabric API — if Microsoft exposes workspace-level deploy API,
  per-feature PBI workspaces become feasible. Track the Fabric public roadmap.
- Per-feature PBI workspaces created manually by Paul per UAT cycle — labour intensive
  but technically possible today. Not automated.
- Decouple Snowflake UAT from PBI UAT — client validates data via direct Snowflake
  query share first, then PBI sign-off in a second pass. Changes the UAT process.

**Next action**: design a serialisation process + rollback runbook so that at minimum
the blast radius of multi-feature conflicts is contained. Track as a v2 ops ticket.

- **Sellercloud share restored** (2026-04-18): `CURRENT_MAIN_INVENTORY_PANDL` re-added to PROD outbound share. GP-208 PROD deploy is now unblocked.
- **GP-208 PROD deploy**: ready to run `python deploy.py --env prod --ticket GP-208 --run-task` once branch is merged to GEP/development and TEST validation is signed off.
- **Phase 3**: `/gep-feature` skill implementation — see boot prompt below.

## Cross-Lane Requests

_None._

## Next Session Boot Prompt

### ~~🔴 CURRENT~~ (complete 2026-04-26) — Tranche H: GP-208 dogfood + workflow improvements (Sonnet)

**Result:** Full workflow ran end-to-end. TEST deploy ✅, PBI model applied ✅, PRs raised, Jira comments posted. Intentionally rolled back (test run). Major workflow improvements shipped (see session log above). Next: real ship.

### 🔴 CURRENT — GP-208 real ship: TEST → UAT → prod (Sonnet)

**Primary goal:** Ship GP-208 for real. Workflow and tooling are fully proven from Tranche H. Resume at `implementing` Sub-step 2 (TEST deploy), proceed through TEST-deployed → UAT → prod.

**Why Sonnet:** Execution work following a thoroughly dogfooded workflow. All design decisions locked.

**Why Sonnet:** Execution work following an approved and dogfooded plan. Reasoning is not the bottleneck.

**Context:**
- Phase 7B migration is complete. Scripts live in `~/repos/aldc-shipyard/`. Skill is at `~/.claude/commands/gep-feature.md`.
- `clients` repo is on branch `feature/paulrussell/GP-208/inventory-feed-ingestion-and-modeling`. GP-208 SQL + artifacts committed at `6eef9f90`.
- `aldc-shipyard/.env` is in place. `config/gep.yaml` is in place.
- `clients/GEP/pbi_config.yaml` does NOT exist yet — needs to be created from `aldc-shipyard/clients/GEP/pbi_config.example.yaml` before PBI sandbox steps.
- Share health check already run: all 42 PROD_DG1_GEP objects accessible. Skip it at the Sub-step 1 prompt.
- G.1b confirmed fixed: `git ref` line in deploy output now shows the GP-208 branch HEAD.

````
You are shipping GP-208 for real — inventory feed ingestion & modelling for GEP.
The workflow was fully dogfooded in Tranche H (2026-04-26). Resume cleanly.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read `C:\Users\PaulRussell\repos\wiki\tickets\gep\GP-208.md` — status + next session boot context.
3. Read `C:\Users\PaulRussell\repos\clients\GEP\tickets\GP-208\artifact.yaml` — current stage.

Key facts:
- SHIPYARD_HOME = C:/Users/PaulRussell/repos/aldc-shipyard
- clients repo branch: feature/paulrussell/GP-208/inventory-feed-ingestion-and-modeling
- aldc-shipyard: fully set up (setup.py run, pbi_config.yaml populated for TEST,
  pbi_model_apply.exe built, config/gep.yaml in place)
- Workspace: open aldc-shipyard.code-workspace in VS Code before starting
- SQL files confirmed correct from Tranche H dogfood — no changes needed
- Stage: implementing → resume at Sub-step 2 (TEST deploy)

Invoke `/gep-feature GP-208` to begin.
````

---

### ~~🔴 CURRENT~~ (complete 2026-04-26) — Phase 7B: `aldc-automation` repo implementation (Sonnet + `/effort medium`)

**Result:** Migration complete. All scripts in `aldc-automation`, skill at user level, GP-208 branch clean, smoke test 42/42 ✅. See Phase 7B session log for deviations and details.

**Primary goal (original):** Build the `aldc-automation` repo per the spec at [[aldc-shipyard]]. Execute the migration plan end-to-end so the next GP-208 dogfood runs from the new structure. This is execution work, not design — the architecture is already locked.

**Why Sonnet:** Pure execution against an approved spec. File moves, script refactors, skill rewrite, smoke test. Reasoning is not the bottleneck.

**Why this must happen before the next dogfood:** The dual-branch problem (G.1a, G.1b, G.1e) recurs every session until the migration ships. The Phase 7 design (2026-04-26) locked the structure; running another dogfood from `clients/GEP/scripts/` will waste the session on branch management.

````
You are running Phase 7B of the client-workflow-automation workstream — the implementation
session for the aldc-automation repo. The architecture spec is already locked.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read `C:\Users\PaulRussell\repos\wiki\entities\repos\aldc-automation.md` — this is the
   authoritative spec. Every structural decision (repo layout, config schema, path resolution,
   connector pattern) is captured there. Do not redesign; execute.
3. Read this tracker:
   - 2026-04-26 Phase 7 session log — D1–D7 decisions and rationale
   - "Near-term Architecture Goal" section — original decision context
   - 2026-04-26 Tranche G execution log — gaps the migration must close (G.1a, G.1b, G.1e)
4. Skim the current scripts you will be moving and refactoring:
   - `clients/GEP/scripts/{deploy,validate}.py` — note the `_REPO_ROOT = _HERE.parent.parent`
     pattern; this is what becomes config-driven.
   - `clients/GEP/scripts/pbi_*.py` — pbi_generate_columns, pbi_scan, pbi_seed_sandbox.
   - `clients/GEP/scripts/pbi_model_apply/` — .NET source (Program.cs, ScriptGlobals.cs,
     ExitCodes.cs, TabularExtensions.cs, csproj). Do not copy bin/ or obj/.
   - `clients/GEP/scripts/{deploy_manifest,validate_manifest}/` — manifest YAMLs.
   - `clients/GEP/scripts/pbi_config.example.yaml` — schema doc.
   - `clients/.claude/commands/gep-feature.md` — orchestrator skill, currently at clients
     repo level, must move to user level (~/.claude/commands/) per migration step 6.

Migration plan (execute in order — Paul owns all git operations):

1. **Scaffold** `aldc-automation` at `~/repos/aldc-automation/`. Ask Paul to `git init` and
   create the initial commit; you write the README, .gitignore, and empty directory structure.
   .gitignore must cover: `.env`, `config/*.yaml` (except `*.example.yaml`),
   `clients/*/pbi_config.yaml`, `__pycache__/`, `.venv/`, `pbi_model_apply/bin/`,
   `pbi_model_apply/obj/`, `*.pyc`.

2. **Copy scripts** (no git history — fresh files):
   - `scripts/deploy.py`, `validate.py`, `pbi_generate_columns.py`, `pbi_scan.py`,
     `pbi_seed_sandbox.py`, `data-share-capacity-query.py`
   - `scripts/pbi_model_apply/{Program,ScriptGlobals,ExitCodes,TabularExtensions}.cs`
   - `scripts/pbi_model_apply/pbi_model_apply.csproj`
   - `clients/GEP/deploy_manifest/*.yaml`, `clients/GEP/validate_manifest/*.yaml`
   - `clients/GEP/pbi_config.example.yaml`

3. **Refactor scripts** per [[aldc-shipyard]] §"Script refactor required":
   - Add `--client <name>` arg to deploy.py and validate.py.
   - Replace `_REPO_ROOT = _HERE.parent.parent` (which used to mean clients-repo root)
     with `_AUTOMATION_HOME = _HERE.parent` and load `config/<client>.yaml` from there.
   - Replace hardcoded paths with config-driven ones:
     • SQL_DIR ← repos.clients / clients_layout.warehouse_sql_dir
     • MANIFEST_DIR ← _AUTOMATION_HOME / automation_layout.deploy_manifest_dir
     • Validate output dir ← repos.clients / clients_layout.tickets_dir / <ticket>
     • Rollback dir ← repos.clients / clients_layout.tickets_dir / <ticket> / rollback
     • PBI config ← _AUTOMATION_HOME / automation_layout.pbi_config_path
   - .env loader looks at _AUTOMATION_HOME / .env first, then falls back to legacy paths.
   - **G.1b fix:** deploy.py git ref must come from `git -C <repos.clients> log -1
     --format='%h %s' <ticket-branch>`, not `git log -1` from cwd. Wire this into the
     deploy header that prints "git ref".
   - PBI scripts get the same --client treatment for path resolution.

4. **Create `config/gep.yaml`** (gitignored, real values) and `config/gep.example.yaml`
   (committed schema doc) per the schema in [[aldc-shipyard]] §"`config/<client>.yaml`".
   The example file uses placeholder paths and explanatory comments; the real one has
   Paul's actual machine paths.

5. **Move `pbi_config.yaml`** values: copy current `clients/GEP/scripts/pbi_config.yaml`
   contents to `aldc-automation/clients/GEP/pbi_config.yaml`. Both are gitignored — this
   is a manual file copy, not a git move.

6. **Move skill to user level** (this is also a fix, since the skill was incorrectly
   reported as already user-level):
   - Move `clients/.claude/commands/gep-feature.md` → `~/.claude/commands/gep-feature.md`
     (Paul's call on whether to keep a copy at clients level for portability; recommend
     removing).
   - Add path-resolution prelude near the top:
     `AUTOMATION_HOME="${ALDC_AUTOMATION_HOME:-$HOME/repos/aldc-automation}"`
   - Replace every `python GEP/scripts/<x>.py` with
     `python "$AUTOMATION_HOME/scripts/<x>.py" --client gep` (the `--client` flag is
     part of the new contract — confirm against the deploy.py/validate.py refactor).
   - Replace every `GEP/scripts/pbi_config.yaml` reference with
     `"$AUTOMATION_HOME/clients/GEP/pbi_config.yaml"`.
   - Replace every `GEP/scripts/{deploy,validate}_manifest/` reference with
     `"$AUTOMATION_HOME/clients/GEP/{deploy,validate}_manifest/"`.

7. **Delete from clients repo** (Paul commits the deletion):
   - `GEP/scripts/` (entire directory — includes .venv, .env, scripts, manifests).
   - Update `clients/.gitignore` to drop now-obsolete entries
     (`GEP/scripts/.env`, `GEP/scripts/pbi_config.yaml`, `GEP/scripts/.venv/`, etc.).
   - If `clients/.claude/commands/gep-feature.md` is removed in step 6, remove the
     `.claude/commands/` directory if empty.

8. **Rebase GP-208** onto current clients HEAD. SQL files in `GEP/snowflake/warehouse/`
   and ticket artifacts in `GEP/tickets/GP-208/` (artifact.yaml, notes.md,
   pbi_model_script.cs, pbi_model_columns.cs) stay; nothing in `GEP/scripts/` survives.
   Verify GP-208's manifests in `aldc-automation/clients/GEP/deploy_manifest/GP-208.yaml`
   still reference SQL filenames that exist in clients on the GP-208 branch.

9. **Archive** `feature/paulrussell/workflow-automation/gep-scripted-deploy` — Paul
   closes any open PR or deletes the branch.

10. **Smoke test** from a fresh shell (new working directory, no env vars beyond the
    install). Cold run:
        python "$AUTOMATION_HOME/scripts/deploy.py" --client gep --env sandbox \
          --ticket GP-208 --check-share
    Confirm: config resolves, .env loads, manifest reads from automation repo, SQL files
    discovered in clients repo via config path, share check executes (does not need to
    succeed — just needs to reach Snowflake).

11. **Hand off to dogfood:** announce migration complete, point Paul at the next
    `/gep-feature GP-208` run boot prompt (will be a Tranche H section added after this
    session completes).

Done criteria:
- `~/repos/aldc-automation/` exists with the layout from [[aldc-shipyard]] §"Repo layout".
- `config/gep.yaml` exists (gitignored), `config/gep.example.yaml` is committed.
- All scripts run with `--client gep` and resolve paths from config — no hardcoded
  clients-repo paths remain.
- Skill at `~/.claude/commands/gep-feature.md` calls scripts via `$AUTOMATION_HOME`.
- `clients/GEP/scripts/` deleted on a commit Paul approves.
- Smoke test passes from a fresh shell.
- This tracker's session log gets a "2026-04-XX — Phase 7B execution" entry with: what
  was migrated, any deviations from the spec, gaps surfaced, and the boot prompt for the
  Tranche H dogfood (Sonnet) following the same pattern Tranche G used.

Out of scope this session — do NOT do:
- GP-208 dogfood re-run (next session, Tranche H).
- Tranche D prod auto-apply.
- pbi_scan.py TE3 hang fix.
- Any *new* feature work in deploy.py/validate.py beyond what the migration requires.
- Connector scripts (sketched only in spec; not built).
- Multi-client expansion (Fusion92 config) — wait for actual Fusion92 work to drive it.

Notes for execution:
- Paul owns git operations: `git init`, all commits, all deletes from clients repo,
  branch deletes. Surface clear "please run X" prompts; do not execute git mutations.
- The skill currently has many `cd GEP/scripts/pbi_model_apply && dotnet build` style
  invocations. After migration these become `cd "$AUTOMATION_HOME/scripts/pbi_model_apply"
  && dotnet build`. Be exhaustive — grep the skill for `GEP/scripts` and update every hit.
- pbi_seed_sandbox.py writes back to pbi_config.yaml — confirm the new path is writeable
  and the script uses the same config-resolution helper as the readers.
- If you discover the spec is wrong somewhere, surface the contradiction to Paul before
  deviating. Do not silently re-architect mid-execution.
````

---

### ~~🔴 CURRENT~~ (complete 2026-04-26) — Phase 7: `aldc-automation` repo architecture design (Opus + `/effort high`)

**Result:** spec locked in [[aldc-shipyard]]. D1–D7 decisions captured in 2026-04-26 Phase 7 session log. Implementation handed off to Phase 7B (above).

````
You are running the Phase 7 architecture planning session for the client-workflow-automation workstream.
Goal: design the `aldc-automation` repo and produce a written spec ready for implementation.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker — focus on:
   - "Near-term Architecture Goal" section (the confirmed decision and proposed structure)
   - Tranche G session log (gaps G.1a–G.1e — the pain points this design must solve)
3. Read `C:\Users\PaulRussell\repos\wiki\entities\projects\workflow-automation.md`
   — §6 Q1 (now resolved), §7 Out of Scope connector note, §4 existing primitives table.
4. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md`
   — §6.9 Tranche G (what's been validated so far, what gaps remain).
5. Scan the current scripts to understand what needs to move:
   - `GEP/scripts/deploy.py` — reads manifests, .env, runs Snowflake
   - `GEP/scripts/validate.py` — reads validate_manifest, .env
   - `GEP/scripts/pbi_config.yaml` — workspace/dataset IDs (gitignored)
   - `GEP/scripts/deploy_manifest/` — per-ticket YAML files
   - `GEP/scripts/validate_manifest/` — per-ticket YAML files
   - `GEP/scripts/pbi_model_apply/` — .NET source for the XMLA wrapper
   - `GEP/scripts/pbi_generate_columns.py`, `pbi_scan.py`, `pbi_seed_sandbox.py`
   - `.claude/commands/gep-feature.md` — the skill (stays at user level)

Context you must carry into the design:
- The `clients` repo has a CI/CD branch chain: GEP/development → GEP/user-testing → main.
  Automation scripts must NOT live on this chain — they are still actively evolving.
- The `connector` repo (Eclipse connector runtime) will eventually need its own
  deploy/validate scripts. The automation repo must accommodate this.
- The skill (`gep-feature.md`) already lives at `~/.claude/commands/` (user-level).
  It is the orchestrator. It calls scripts; it does not own them.
- Ticket artifacts (`artifact.yaml`, `pbi_model_script.cs`, `notes.md`) MUST stay in
  the `clients` repo alongside the SQL — they are part of the feature branch PR.
- `pbi_config.yaml` contains local workspace/dataset IDs — it is gitignored and
  machine-specific. It should move to the automation repo's gitignore.

Design decisions to make (work through these with Paul, in order):

**D1 — Repo name and location**
Proposed: `aldc-automation` at `C:\Users\PaulRussell\repos\aldc-automation\`.
Confirm or rename. This is a new ALDC repo — private, separate from clients/connector.

**D2 — Config schema: `config/gep.yaml`**
This file tells scripts where the `clients` and `connector` repos live on disk,
plus any per-client settings that aren't secrets.
Draft a schema. Key fields to resolve:
- How does the skill pass the config path to scripts at runtime? (env var? flag? convention?)
- Does each client (GEP, Fusion92) get its own config file, or sections in one file?
- What belongs in config vs. in `.env` (secrets) vs. in `pbi_config.yaml` (PBI IDs)?

**D3 — Manifest location**
Currently: `GEP/scripts/deploy_manifest/<ticket>.yaml` and `validate_manifest/<ticket>.yaml` in clients repo.
Should these move to `aldc-automation/clients/GEP/deploy_manifest/` (with scripts)?
Or stay in clients (closer to the SQL they describe)?
Tradeoff: manifests reference SQL filenames in clients — if they move, cross-repo path refs arise.
If they stay in clients, they need to live on a branch that doesn't pollute CI/CD.
Decide and lock.

**D4 — How the skill resolves script paths at runtime**
The skill currently calls `python GEP/scripts/deploy.py` assuming it is in the
clients repo working directory. After migration, the script lives in `aldc-automation`.
Options:
  A. Skill reads `automation_repo_path` from a user-level config (`~/.claude/gep-workflow.yaml`)
     and constructs the full path at runtime.
  B. `aldc-automation` is always at a fixed known path (e.g. `~/repos/aldc-automation/`)
     and the skill hardcodes the convention.
  C. Scripts are added to PATH — skill calls `deploy.py` without a path.
Recommend A (most flexible across machines). Design the config file format.

**D5 — pbi_config.yaml new home**
Currently gitignored in `GEP/scripts/pbi_config.yaml` (clients repo).
Should move to `aldc-automation/clients/GEP/pbi_config.yaml` (gitignored there).
The skill currently reads it via relative path from clients repo root.
After move: skill reads it from the automation repo path.
Confirm this is the right move. Update the skill spec accordingly.

**D6 — Connector integration pattern (design only, not build)**
When connector deploy steps are added to the workflow:
- Where do connector scripts live? (`aldc-automation/scripts/connector/`?)
- How does `config/gep.yaml` express the connector repo path?
- Does the gep-feature skill grow connector-aware steps, or is there a separate
  `connector-feature.md` skill?
Do not build — just establish the pattern so the aldc-automation structure accommodates it.

**D7 — Migration plan from workflow-automation branch**
The current `feature/paulrussell/workflow-automation/gep-scripted-deploy` branch
contains all the scripts. Plan for moving them:
1. Create aldc-automation repo.
2. Copy scripts (not git history — fresh repo, clean start).
3. Update skill path resolution.
4. Archive/close the workflow-automation feature branch (or let it die).
5. Rebase GP-208 onto current clients HEAD (SQL + artifacts stay; scripts gone from clients).
Confirm this plan or adjust.

Done criteria:
- `aldc-automation` repo structure agreed and documented in a new wiki page:
  `C:\Users\PaulRussell\repos\wiki\entities\repos\aldc-automation.md`
- `config/gep.yaml` schema fully specified (every field, type, purpose)
- Skill path-resolution pattern agreed (how skill finds scripts at runtime)
- Manifest location decided (aldc-automation or clients)
- Connector integration pattern sketched (enough to not have to redesign later)
- Migration plan written (step-by-step, Paul owns git operations)
- This tracker's session log updated with all decisions and the next boot prompt
  written for the implementation session (Sonnet, execution)

Out of scope this session — do NOT touch:
- Actual repo creation or file moves (implementation session, after this spec is done)
- GP-208 dogfood re-run (blocked until repo is created)
- Tranche D prod auto-apply
- pbi_scan.py TE3 hang fix
- Any code changes to deploy.py, validate.py, or gep-feature.md
````

---

### ~~🔴 CURRENT~~ (complete 2026-04-26) — Tranche G: GP-208 full E2E dogfood — scoping → sandbox → TEST (Sonnet + `/effort high`)

**Primary goal:** Run GP-208 end-to-end through `/gep-feature` from a clean re-scope all
the way through Sub-step 2 TEST deploy — exercising the PBI model apply to GEP Test Models
for the first time. Prove the full Snowflake + PBI sandbox → TEST promotion flow. Capture
every Sub-step 2 gap in real time.

**Why this matters:** Sub-step 1b (sandbox PBI apply) was proven on 2026-04-25 (Tranche F).
Sub-step 2 (TEST PBI apply via `§G env=test`) has never been exercised. `pbi_config.yaml`
test entries are now filled. GP-208 artifact was deleted for a clean re-scope. This session
is the first full end-to-end dogfood of the complete workflow.

````
You are running Tranche G of the client-workflow-automation workstream — the first full
end-to-end dogfood of /gep-feature: GP-208 scoping → implementing → sandbox → Sub-step 2 TEST.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker (you are here) — focus on the 2026-04-25 Tranche F execution log
   (all gaps found + fixed) and the Tranche G goal above.
3. Read `C:\Users\PaulRussell\repos\wiki\tickets\gep\GP-208.md` — all prior scoping
   decisions, requirements, and business logic. Use this to fast-track scoping Q&A.
4. Read `GEP/scripts/pbi_config.yaml` — confirm test entries are fully populated
   (id, dataset_id, dataset_name all non-null). If any are null, STOP and surface to Paul.
5. Read `.claude/commands/gep-feature.md` — Sub-step 2 APPLY MODEL SCRIPT TO TEST block
   and the §G / §H helper specs. Pay attention to the `env=test` code paths.
6. Read `GEP/tickets/GP-208/pbi_model_script.cs` — the current script uses Snowflake
   names (INVENTORY_FCT_BALANCE, EXTRACT_INVENTORY_CURRENT). It must be updated for
   the naming convention decision before being applied to TEST (see Step G.1 below).

Pre-session state (do NOT re-do these):
- pbi_config.yaml sandbox: id=8545f3cb, dataset_id=fb41970d, dataset_name=GEP_Sandbox_Current ✅
- pbi_config.yaml test: id=a29d4c01, dataset_id=66151728, dataset_name=Data Model ✅
- GP-208 artifact.yaml: DELETED — skill will start at scoping stage ✅
- GP-208 notes.md: DELETED — use wiki/tickets/gep/GP-208.md for all prior decisions ✅
- GEP/tickets/GP-208/pbi_model_script.cs: EXISTS (has relationship-cleanup fix from Tranche F)
- GEP/tickets/GP-208/pbi_model_columns.cs: EXISTS (27 + 32 DataColumn defs from generator)
- GEP/snowflake/warehouse/inventory_fct_balance.sql: EXISTS in working tree (final SQL)
- Branch feature/paulrussell/GP-208/inventory-feed-ingestion-and-modeling: EXISTS in git

Step G.1 — Naming convention update (do BEFORE running /gep-feature)
   GEP PBI model convention is Title Case display names, not Snowflake identifiers.
   Paul's decision (2026-04-25): INVENTORY_FCT_BALANCE → "Inventory Current".
   Ask Paul what display name to use for EXTRACT_INVENTORY_CURRENT before proceeding.

   Update pbi_model_script.cs to use display names everywhere:
   - Drop-if-exists guards: Model.Tables.Contains("Inventory Current") etc.
   - Model.AddTable("Inventory Current") — table is created with the display name
   - Relationship checks: scr.FromTable.Name == "Inventory Current"
   - Model.Tables["Inventory Current"] lookups
   The M query RESULTANT_VIEW step still references the Snowflake table name internally
   — that stays as INVENTORY_FCT_BALANCE. Only the TOM table.Name changes.

   After updating, run the dry-run compile check to confirm:
   GEP/scripts/pbi_model_apply/bin/Release/net8.0-windows/pbi_model_apply.exe
     --script GEP/tickets/GP-208/pbi_model_script.cs
     --workspace "GEP Sandbox Models" --dataset "GEP_Sandbox_Current" --dry-run

Step G.2 — Fast scoping via /gep-feature GP-208
   All GP-208 requirements are known. Use wiki/tickets/gep/GP-208.md as the source.
   Present each scoping question with the known answer for Paul to confirm — don't
   re-ask from scratch. The branch already exists; confirm it. The deploy manifest and
   validate manifest already exist; confirm or update.

   Key scoping decisions to lock at this stage:
   - PBI model changes required: true
   - visual_required: false (metadata-only — no PBIX republish needed)
   - PBI model description: "Add Inventory Current and <EXTRACT display name> tables"
   - scan_option_chosen: B (drop and replace)

Step G.3 — Sub-step 1 (Snowflake sandbox) + Sub-step 1b (PBI sandbox) with renamed tables
   Snowflake sandbox: run deploy.py + validate.py as usual.
   PBI sandbox: confirm the rename landed — the model should now show "Inventory Current"
   (not INVENTORY_FCT_BALANCE) in the GEP Sandbox Models dataset after apply.
   Validate links should appear per the F.1 change.

Step G.4 — Sub-step 2: TEST deploy + PBI model apply to GEP Test Models (first run)
   This is the main new thing being exercised. Watch for:

   Snowflake TEST deploy:
   - Run deploy.py --env test --ticket GP-208 --run-task
   - Run validate.py --env test --ticket GP-208 --save-results
   - Rollback command is available if TEST breaks something:
     python GEP/scripts/deploy.py --env test --ticket GP-208 --rollback --run-task

   PBI model apply to TEST (skill prompts "Apply validated PBI model script to GEP Test Models?"):
   - §G with env=test: targets workspace "GEP Test Models", dataset "Data Model"
   - MSAL token should be cached from the sandbox run (~1h window); if stale, wrapper
     exits 2 and §G prompts for --clear-token-cache.
   - dry-run compile check fires first (Tranche F hardening).
   - On success: test_applied_at + test_refresh_id are set in the artifact for the
     first time. These fields have never been written by the skill before.
   - TEST model validation links emit per F.1 extension (sandbox-only today;
     if TEST links are desired here, that is a Tranche G gap to fix in-session).

   Likely Sub-step 2 gaps to watch for:
   - MSAL token expired between sandbox and TEST apply (~4-5 min refresh + time for
     Snowflake TEST deploy). May need --clear-token-cache.
   - TEST dataset has a different XMLA path — confirm "GEP Test Models" / "Data Model"
     resolves. The wrapper error message on connect failure is exit code 3.
   - poll_refresh for TEST: "Data Model" refreshes may include more tables than sandbox
     (full model vs. 2-table sandbox). Expect longer refresh time (~5-10 min).
   - Validation links for TEST: skill currently only emits links for env=sandbox.
     If Paul wants TEST links too, add the same pattern as F.1 but for env=test.
     File as a gap and fix in-session if it surfaces.

Step G.5 — Capture every gap in real time
   Same discipline as Tranche F: every glitch goes into the tracker session log
   immediately. Fix in-session where possible. File as follow-up where not.

Step G.6 — Evaluate Tranche D (prod auto-apply)
   If Sub-step 2 is clean: assess whether Tranche D (prod-deployed conditional
   auto-apply, plan §3.7) can be built in the same session. Tranche D only adds
   the visual_required == false branch at prod-deployed — it is ~40 lines of skill
   code and the §G/§H helpers are already there. Decision criteria:
   - Sub-step 2 exit 0 ✅
   - test_applied_at set in artifact ✅
   - No blocking gaps requiring another §G/§H redesign
   If yes: build Tranche D. If no: file as follow-up.

Step G.7 — Wiki + tracker update
   - Add 2026-04-25 Tranche G session log entry with all gaps and resolutions.
   - Update phase6-pbi-automation-plan.md to mark Tranche G complete.
   - Update pbi-xmla-automation.md if any new TEST-specific patterns emerge.

Done criteria:
   - /gep-feature GP-208 runs from scoping through test-deployed with no manual rescue.
   - Tables appear in GEP Test Models as "Inventory Current" (not SCREAMING_SNAKE_CASE).
   - test_applied_at and test_refresh_id are set in the artifact from a skill-driven run.
   - Every Sub-step 2 gap is either fixed or filed.

Out of scope this session — do NOT touch:
   - Phase 7 architecture redesign (separate Opus planning session).
   - prod-deployed apply (Tranche D — evaluate at G.6 but don't force it).
   - pbi_scan.py TE3 hang fix.
   - workspaces.prod.* in pbi_config.yaml.
   - Connector repo automation.

Constraints:
   - Paul handles git commits. Summarise changes per step for manual staging.
   - Never log bearer tokens. The wrapper handles MSAL internally.
   - pbi_config.yaml is gitignored — test entries are local-only (expected).
   - Update this tracker's session log AS YOU GO — gaps captured in real time.
````

---

### ✅ COMPLETE (2026-04-25) — Phase 6 Tranche F: Harden GP-208 PBI sandbox automation through the skill (Sonnet + `/effort high`)

**Primary goal:** Make Sub-step 1b run cleanly end-to-end against GP-208's sandbox
through `/gep-feature` itself — a cold `force` re-run produces a populated model and
a clickable validation link with zero manual rescue. Sandbox-only; TEST tail and
Tranche D (prod auto-apply) are explicitly deferred until sandbox is stable.

**Context:** Sub-step 1b was proved end-to-end on 2026-04-24 by running each step
*outside* the skill (manual wrapper invocations + REST calls). Since then the skill
itself has been heavily revised — §G was rewritten to call `pbi_model_apply.exe`
(MSAL inside, no `--token`), a MODEL SCAN step was added, a GENERATE COLUMN
DEFINITIONS step was added, and `warn_only` support landed in `validate.py`. None
of those skill paths have been exercised on GP-208. This tranche's job is to drive
the whole flow through the skill, capture every gap, and close them.

````
You are working on Phase 6 Tranche F of the client-workflow-automation workstream
— hardening the PBI sandbox automation in `/gep-feature` Sub-step 1b. Sandbox-only
this session. TEST and PROD are out of scope.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker (you are here) — focus on the 2026-04-25 session log entry
   describing Tranche F's plan, and the 2026-04-24 entry for prior validation.
3. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md`
   §6.8 (Tranche F — Sandbox hardening) for the authoritative spec.
4. Read `C:\Users\PaulRussell\repos\wiki\concepts\patterns\pbi-xmla-automation.md`
   for the canonical pattern.
5. Read `.claude/commands/gep-feature.md` Sub-step 1b end-to-end (the MODEL SCAN,
   PRE-FLIGHT, GENERATE COLUMN DEFINITIONS, REBIND, APPLY MODEL SCRIPT, refresh +
   poll, MANUAL VISUAL CHECK blocks). Diff vs HEAD shows ~216 uncommitted lines.
6. Read `GEP/tickets/GP-208/artifact.yaml` — current state of the test ticket.
   `sandbox_validated: true` from 2026-04-24, but validated outside the skill.
7. Read `GEP/scripts/pbi_config.yaml` — sandbox workspace + dataset are populated;
   test/prod are deliberately null and stay null this session.

Step F.1 — Add sandbox validation link emission to the skill (no Paul input needed)
   - In §G's success branch (after `pbi_model_apply.exe` exits 0), print the dataset
     details URL constructed from `pbi_config.workspaces.sandbox.id` + `dataset_id`:
       Workspace: https://app.powerbi.com/groups/<workspace_id>/list
       Dataset:   https://app.powerbi.com/groups/<workspace_id>/datasets/<dataset_id>/details
   - In §H `poll_refresh` Completed branch, print the same URLs plus per-table
     refresh status from the response body.
   - Replace the bare "Open GEP Sandbox Models workspace in Power BI Service" text
     in the existing MANUAL VISUAL CHECK block with the constructed URL.
   - Scope: sandbox only. Do NOT add link emission for TEST or PROD this session
     (their config entries are null and the code paths aren't being exercised).

Step F.2 — Decide the MODEL SCAN path
   The MODEL SCAN block calls `pbi_scan.py`, which is currently `if False`-gated for
   the TE3 path due to a subprocess hang. `pbi_config.yaml` now points at TE3, but
   the hang fix has not been verified. Default to skipping the scan for GP-208's
   dogfood (the skill already falls back gracefully). File the TE3 hang fix or a
   TOM-based replacement as a follow-up — DO NOT scope-creep it into this session.

Step F.3 — Reset GP-208 sandbox state
   The 2026-04-24 run left tables populated. To genuinely prove the cold-start
   flow, drop the two GP-208 tables before re-running:
     - Easiest: re-run the existing pbi_model_script.cs — drop-if-exists guards make
       it idempotent.
     - Cleaner: ad-hoc one-liner script that removes both tables, then run the
       full script.

Step F.4 — Run Sub-step 1b end-to-end through the skill on GP-208
   Invoke `/gep-feature GP-208 force` and walk Paul through every prompt. Confirm
   in order:
     - MODEL SCAN gracefully skips per F.2.
     - PRE-FLIGHT finds existing pbi_model_script.cs.
     - GENERATE COLUMN DEFINITIONS recognises columns are wired and skips.
     - §H update_parameters rebinds sandbox to SANDBOX_DG1_GEP_GP208.
     - §G applies via pbi_model_apply.exe (MSAL device-code or cached).
     - §H refresh_dataset + poll_refresh → Completed.
     - F.1 link is printed; Paul clicks and validates.
     - Artifact updated with new sandbox_applied_at, sandbox_refresh_id, script_hash.

Step F.5 — Capture every gap as we go
   For each glitch, surprising prompt, missing affordance, or manual rescue:
     - Log it to the 2026-04-25 session-log entry as it happens.
     - Fix it in the skill (or wrapper) immediately.
     - Re-run from F.3 until a cold run produces "link printed, model validated"
       with no manual rescue.

   Likely gaps:
     - MSAL token cache stale → wrapper exits 2 → §G prompt for --clear-token-cache
       (untested code path).
     - pbi_model_apply.exe missing → §G prompts to build (also untested).
     - §H 20-min poll timeout → currently aborts; may need a "keep polling?" branch.
     - Skill prompts that interrupt the flow needlessly → tighten or auto-confirm.

Step F.6 — Wiki consolidation (sandbox only)
   - phase6-pbi-automation-plan.md §6.8 — mark each Tranche F sub-step done with date.
   - pbi-xmla-automation.md — add "Validation links" item to The Pattern; annotate
     Required Pieces §4 step 8 with link emission. Sandbox only — no TEST/PROD yet.
   - Tracker — fill in the 2026-04-25 session log entry with what was done, every
     gap found, and the resolution.
   - pbi-xmla-model-changes.md — append any new gotchas surfaced in F.5.

Done criteria:
   - `/gep-feature GP-208 force` runs Sub-step 1b end-to-end with zero manual rescue.
   - Validation link is printed and works.
   - GP-208 artifact has fresh sandbox_applied_at and sandbox_refresh_id timestamps
     from a skill-driven run (not a manual one).
   - All gaps surfaced during F.4/F.5 are either fixed or filed as follow-ups.
   - Wiki updates from F.6 are committed (or staged for Paul to commit).

Out of scope this session — do NOT touch:
   - Sub-step 2 TEST promotion (skill code exists; not exercising it).
   - Tranche D prod auto-apply (not built yet; explicitly deferred).
   - workspaces.test.* and workspaces.prod.* in pbi_config.yaml (stay null).
   - pbi_scan.py TE3 hang (file as follow-up; do not diagnose this session).
   - GP-208 naming-convention reconciliation (Title Case vs SCREAMING_SNAKE).

Constraints:
   - Paul handles git commits. Summarise changes per step so he can stage manually.
   - Never log bearer tokens. The wrapper handles MSAL internally; the skill never
     constructs or sees a token.
   - Update this tracker's session log AS YOU GO, not at the end — every gap from
     F.5 needs to be captured in real time, not reconstructed afterward.
````

---

### 🟡 SUPERSEDED — Phase 6: Make Sub-step 1b work via automation (superseded 2026-04-25)

The work this prompt described — first-pass end-to-end validation of Sub-step 1b
against GP-208 — was completed on 2026-04-24 by running each step *outside* the
skill. Tranche F (above) supersedes it by driving the same flow through the skill
itself and hardening every code path. Kept here for historical context; do not boot
from it.

**Primary goal (historical):** Get the PBI model-change step in `gep-feature` Sub-step 1b working
reliably end-to-end — either fully automated or with a documented, minimal manual step
that is locked into the workflow. GP-208 is the **test vehicle**, not the deliverable.

**Context (historical):** See [[pbi-xmla-model-changes]] for the full TE3 CLI investigation.
GP-208 sandbox is the live test case — tables have been added to the model but are
refreshing with "no columns" (likely wrong partition type). Fix GP-208 to prove the
workflow step works, then lock in the automation approach for all future tickets.

````
You are working on the client-workflow-automation workstream — specifically fixing and
validating Phase 6 Sub-step 1b (PBI model changes step in the gep-feature skill).

GP-208 is being used as a live test ticket. The goal is NOT to ship GP-208 — it is to
make the PBI model-change automation step work reliably so every future ticket uses it.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker (you are here) — focus on the 2026-04-22/23 session log entry.
3. Read `C:\Users\PaulRussell\repos\wiki\processes\deployment\pbi-xmla-model-changes.md`
   — full TE3 CLI diagnosis, GEP M expression conventions, and Sub-step 1b status.
4. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md`
   — the authoritative Phase 6 plan.
5. Read `GEP/tickets/GP-208/artifact.yaml` — current state of the test ticket.
6. Read `GEP/scripts/pbi_config.yaml` — sandbox workspace/dataset IDs.

Immediate blocker to fix first (GP-208 sandbox):
Tables `INVENTORY_FCT_BALANCE` and `EXTRACT_INVENTORY_CURRENT` exist in the sandbox
dataset but refresh with "no columns" — most likely the partition type is DAX instead
of M Query. Fix via TE3 GUI:
1. Open TE3 → File → Open from DB → GEP Sandbox Models → GEP_Sandbox_Current
2. Tables → INVENTORY_FCT_BALANCE → Partitions → verify partition type = M Query
3. If not M Query: change type, paste expression from
   `GEP/tickets/GP-208/pbi_partition_expressions.md`
4. Repeat for EXTRACT_INVENTORY_CURRENT
5. Save (Ctrl+Alt+S) → close TE3 → trigger refresh via REST API → verify rows > 0

Once GP-208 tables are loading correctly, focus shifts to automation:

Primary investigation — make Sub-step 1b work without manual TE3 GUI:
TE3 CLI hangs from any subprocess context (GUI app, message loop). Investigate:
  Option A: Thin .NET console wrapper around the TOM libraries TE3 uses
  Option B: Direct XMLA SOAP requests with bearer token (no TE3 at all)
  Option C: Search PyPI / GitHub for Python XMLA or TOM clients
  Option D: Document the manual TE3 GUI step as an explicit, locked workflow step
             with a skill prompt that walks Paul through it reliably

The right outcome is one of:
  - A fully automated CLI command the skill calls via §G
  - A documented 3-step manual process locked into the skill as a first-class step
    (not a workaround — if automation isn't feasible, the manual step IS the workflow)

After resolving the automation question:
1. Update `gep-feature.md` §G helper or Sub-step 1b to reflect the chosen approach
2. Apply second TE3 script for metadata (relationship, format strings, hide PRODUCT_KEY)
3. Record `changes.pbi_model.sandbox_validated = true` in GP-208 artifact
4. Update [[pbi-xmla-model-changes]] with final findings
5. Update this tracker's session log

Constraints:
- Close TE3 before triggering any dataset refresh (exclusive XMLA session)
- Never log bearer tokens — substitute <bearer> in all displayed output
- `pbi_scan.py` TE3 path is disabled (if False guard) — REST scan only
- Paul handles git commits; summarise changes when done
````

---

### Phase 6 — Implementation (run after Tranche A setup; Sonnet + `/effort high`)

**Prerequisite:** The Opus planning session is complete. The plan is at
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md`
— it is the authoritative spec. Read it verbatim before touching any files.

**Prerequisites (Paul must complete before session starts):** Tranche A.0.1–A.0.6
(capacity check, Azure CLI install, TE 2 install, sandbox workspace create, seed
PBIX downloaded, seed PBIX parameterised with `SNOWFLAKE_DATABASE` and
`SNOWFLAKE_ROLE`). Plan §6.1 has step-by-step. If A.0.6 is not complete, the
seed script (A.1) will refuse to run — it checks for both parameters on the
uploaded dataset and errors with a clear message if missing.

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

**Implementation order (tranches — do NOT skip ahead):**

Tranche A — external setup + `pbi_seed_sandbox.py`:
- A.0.1–A.0.5: Paul's manual steps (capacity check, Azure CLI install, TE 2 install,
  workspace creation, PBIX download). Skill session should NOT run these.
- A.1: write `GEP/scripts/pbi_seed_sandbox.py` (idempotent PBIX upload + dataset
  ID discovery + `pbi_config.yaml` population).
- A.2: write `GEP/scripts/pbi_config.yaml` skeleton (gitignored).
- A.3: smoke test — Paul runs the seed, confirms XMLA write works end-to-end via
  Tabular Editor interactively.

Tranche B — skill primitives (no behaviour change):
- B.1–B.2: add §G (TE CLI helper), §H (PBI REST helper), §I (Azure CLI bearer token
  helper) to the `## MCP setup` section of `.claude/commands/gep-feature.md`.
- B.3: extend artefact schema with Phase 6 fields (`visual_required`, `script_path`,
  `script_hash`, `sandbox_validated`, `sandbox_applied_at`, `sandbox_refresh_id`,
  `test_applied_at`, `test_refresh_id`, `prod_applied_at`, `prod_refresh_id`,
  `findings`).
- B.4: skip — `pbi_config.yaml` is the source; the skill just reads it. No artefact
  config block needed.
- B.5: add rules 9–11 to `## Rules` in the skill.

Tranche C — main behaviour change:
- C.1: extend `scoped` stage PBI question to capture `visual_required`.
- C.2: insert Sub-step 1b in `implementing` (pseudocode is plan §3.3 — copy verbatim).
- C.3: extend Sub-step 2 TEST deploy with TE CLI apply + refresh tail (plan §3.5).
- C.4: refine `test-deployed` step 3 to note refresh is already done (plan §3.6).

Tranche D — `prod-deployed` conditional auto-apply (plan §3.7). Ship AFTER Tranche C
has been dogfooded on a real ticket.

Tranche E — wiki docs (plan §6.5).

````
You are implementing Phase 6 of the GEP workflow automation skill (Tranche A + B).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md` — look at Phase 6 session log entries and the boot prompt below.
3. Read the plan: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md` — it is the authoritative spec. Tranche A is §6.1; Tranche B primitives are §3.10 (§G/§H/§I) and §3.8 (artefact schema).
4. Confirm Paul has completed A.0.1–A.0.5 (capacity check, az CLI, TE 2 install, sandbox workspace created, seed PBIX downloaded). If not, STOP and surface to Paul.
5. Read `.claude/commands/gep-feature.md` in full.
6. Checkout automation branch: `git checkout feature/paulrussell/workflow-automation/gep-scripted-deploy`.

Goal: build `GEP/scripts/pbi_seed_sandbox.py` (Tranche A.1), populate `GEP/scripts/pbi_config.yaml` (Tranche A.2), and add §G/§H/§I + artefact schema additions + rules 9–11 to `.claude/commands/gep-feature.md` (Tranche B.1–B.5).

Constraints:
- Paul handles git commits. Summarise each tranche's changes after completing so Paul can review before committing.
- Tranche A and Tranche B are independent — do A first, smoke-test, THEN do B. Don't start Tranche C in this session; that's a separate session gated on Paul's Q4 answer.
- `pbi_seed_sandbox.py` must be idempotent — re-running against an existing sandbox dataset updates instead of erroring.
- Never log bearer tokens. Substitute `<bearer>` literal when showing commands to Paul.
- Add `GEP/scripts/pbi_config.yaml` to `.gitignore` before writing the file.
- Update the session log in this tracker after each tranche.
````

````
You are planning Phase 6 of the GEP workflow automation skill — Power BI model automation.
Run `/effort xhigh` before starting.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read the workstream tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md`.
3. Read the design doc: `C:\Users\PaulRussell\repos\wiki\entities\projects\workflow-automation.md` — §3.2 and §3.6 are the most relevant (PBI limitations and why true ephemeral sandbox was ruled out).
4. Read the current skill file: `C:\Users\PaulRussell\repos\clients\.claude\commands\gep-feature.md` — pay attention to the `test-deployed` stage and the existing `changes.pbi_model` fields added in Phase 5 Tier 3.
5. Read the open blocker in the tracker: "Multi-feature conflict in TEST / PBI" — this is the problem Phase 6 is meant to solve.

Context:
- Branch: `feature/paulrussell/workflow-automation/gep-scripted-deploy`
- GEP Snowflake envs: `TEST_DG1_GEP` (og35375), `PROD_DG1_GEP` (wj66376)
- Power BI workspaces: "GEP Test Models" (client UAT), Production workspace
- **XMLA / .NET endpoint is confirmed available** for GEP's Power BI workspace. The REST API
  was evaluated previously and lacked the model-change functionality required. XMLA write
  is the confirmed path for programmatic model changes.
- Currently: PBI model changes (new relationships, measures, calculated columns) are made
  manually in Power BI Desktop, then published via the UI. This is the last manual,
  untracked step in the workflow.
- Phase 5 Tier 3 already added `changes.pbi_model.required / description / published` fields
  to the artifact and a gate at `prod-deployed`. The gap is there is no sandbox-equivalent
  for PBI — the client validates through the PBI Test Model, which is shared and manually
  maintained.

Goal:
Design a Phase 6 that adds a PBI model automation stage to the workflow, so that after
Snowflake sandbox validation passes, any required PBI model changes are also applied and
validated in a sandboxed or isolated PBI environment before the feature reaches the shared
TEST workspace used for client UAT.

The plan must address four questions in order:

**Q1 — Technical feasibility audit**
What programmatic options exist for making Power BI Desktop model changes (adding
relationships, measures, calculated columns) without using the UI? Research and evaluate:
- Tabular Editor CLI (`TabularEditor.exe /s <xmla-connection> /script <script.cs>`) —
  C# scripting against the tabular model via XMLA. **This is the confirmed available path.**
- pbi-tools (open source, `.pbix` extract/deploy, PBIP format, TMDL support)
- BIM/TMDL files (JSON/text representation of tabular model, version-controllable,
  deployable via Tabular Editor or `msdeploy`)
- Power BI REST API — dataset refresh, workspace management (already ruled out for model
  changes; evaluate only for refresh triggering and status polling)
- Power BI Deployment Pipelines API — programmatic pipeline stage promotion
For each option: capability, what it can and cannot do, realistic implementation effort,
and how it composes with the XMLA-confirmed path.

**Q2 — Sandbox isolation design**
The existing Snowflake sandbox is a full DB clone (`SANDBOX_DG1_GEP_<ticket>`). What is
the equivalent isolation model for Power BI given XMLA write access is available?
- Option A: Per-feature Power BI workspace clone — clone "GEP Test Models" to a new
  workspace per ticket via REST API; connect it to the sandbox Snowflake DB; validate;
  tear down after sandbox validate passes.
- Option B: Dedicated "sandbox" semantic model within the existing TEST workspace — a
  second dataset that points at the sandbox Snowflake DB. Cheaper than a full workspace
  clone but still isolated from the client-facing model.
- Option C: Model-file validation only — use pbi-tools/TMDL to version-control model
  changes; validate the diff against schema (column names, relationship integrity) without
  a live workspace. The "sandbox" is the file, not a live dataset.
- Option D: Hybrid — TMDL/BIM for version control + Tabular Editor CLI to apply to a
  sandbox dataset (Option B) + REST API to trigger refresh and poll status.
Evaluate each against: feasibility given confirmed XMLA access, implementation effort,
client UAT impact, and alignment with the Snowflake sandbox pattern.

**Q3 — Workflow integration design**
Given the chosen option(s) from Q2, where does the PBI stage fit in the current workflow?

Currently:
  scoping → scoped → implementing → test-deployed → uat → prod-deployed → complete

Proposed insertion point — after Snowflake sandbox validate passes (Sub-step 1 of
`implementing`), add Sub-step 1b:

  Sub-step 1b — PBI sandbox validation (only fires if `changes.pbi_model.required == true`)
    - Apply PBI model changes to the sandbox/isolated model via Tabular Editor CLI or
      pbi-tools
    - Refresh the sandbox dataset against the sandbox Snowflake DB (REST API)
    - Confirm visuals/measures look correct in the isolated environment
    - Only after this passes: proceed to TEST deploy (Sub-step 2)

Design the exact skill file changes needed:
  - New prompts/gates in `implementing` Sub-step 1b
  - Changes to `changes.pbi_model` artifact fields (add `sandbox_validated`,
    `sandbox_workspace_id`, `sandbox_dataset_id`, etc.)
  - How the `test-deployed` PBI smoke-test step changes (or stays the same)
  - How `prod-deployed` publish gate changes (can it now be scripted rather than manual?)

**Q4 — Automation depth recommendation**
Given XMLA write is confirmed, recommend a v1 automation depth on this spectrum:
  - **Level 1**: Skill generates a Tabular Editor C# script from `changes.pbi_model.description`;
    Paul runs it manually against the XMLA endpoint; skill tracks completion in artifact
  - **Level 2**: Skill runs Tabular Editor CLI directly to apply model changes to a sandbox
    dataset; triggers REST API refresh; polls until complete; Paul reviews then promotes
  - **Level 3**: Fully automated — apply model change, refresh, validate, promote sandbox
    dataset to TEST workspace via Deployment Pipelines API; Paul approves at each gate

Recommend the highest level that is practically achievable as a v1. Design v2 stretch goals.
Justify the recommendation and call out any unknowns that would change the answer.

Output format:
Produce a plan document at:
  `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase6-pbi-automation-plan.md`

The document must include:
1. Technical feasibility matrix (Q1) — table of options with capability, confirmed/blocked,
   effort
2. Chosen sandbox isolation model (Q2) — recommended option with rationale and trade-offs
3. Workflow integration design (Q3) — exact stage/step changes to `gep-feature.md`, with
   skill pseudocode for Sub-step 1b
4. Recommended automation level (Q4) — with specific tools, commands, and call sequence
5. Open questions for Paul — Tabular Editor licence/install, workspace IDs, Deployment
   Pipelines availability, TMDL vs BIM preference
6. Implementation order — which pieces to build first

Also:
- Update the "Open blocker — Multi-feature conflict in TEST / PBI" section of the tracker
  to note that Phase 6 is the planned resolution and reference the new plan file
- Add an entry to the tracker's Session Log
- Update `C:\Users\PaulRussell\repos\wiki\index.md` with the new plan page
- Append to `C:\Users\PaulRussell\repos\wiki\log.md`

Do NOT edit `gep-feature.md` in this session — this is planning only.
After producing the plan, surface the 3–5 most important open questions for Paul before
implementation begins.
````

---

### Phase 5 Tier 3 — Implementation ✅ (complete 2026-04-21)

**Recommended model:** Sonnet 4.6. Run `/effort high`.

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

**Prerequisite:** The Opus planning session is complete. The plan is at
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase5-tier3-plan.md`
— exact skill-file edits, artifact schema additions, MCP call signatures, edge-case
handling, and implementation order/rationale. It is the authoritative spec; read it
verbatim before touching any files.

````
You are implementing Phase 5 Tier 3 of the GEP workflow automation skill.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md` — the Phase 5 Tier 3 section has the full item list.
3. Read the implementation plan: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\phase5-tier3-plan.md` — this is the authoritative spec. Every skill edit, artifact field, MCP call, and edge case is specified there. Do not deviate without surfacing to Paul.
4. Read `.claude/commands/gep-feature.md` in full.
5. Checkout automation branch: `git checkout feature/paulrussell/workflow-automation/gep-scripted-deploy`

Goal: implement items 7–13 as specified in the plan. All changes go in `.claude/commands/gep-feature.md` plus the artifact schema block within that file. Do NOT edit deploy.py or validate.py.

Before coding two items, verify external schemas per the plan's "Notes for the Sonnet session":
  - Item 10 → read `GEP/scripts/validate_manifest/GP-208.yaml` to confirm tables.<name>.* field names.
  - Item 12 → read `GEP/scripts/validate.py` (the --save-results writer) to confirm JSON output schema.

Constraints:
- Paul handles git commits. Do not run `git commit`. Summarise each item's changes after editing so Paul can review before committing.
- Implement in the order specified by the plan (Preamble → 8 → 9 → 7 → 13 → 11 → 12 → 10). Complete and summarise each item before starting the next.
- Every MCP call added must include the offline/failure fallback from Preamble §B.
- Before item 7, add `GEP/tickets/*/_pr_body.md` to `.gitignore` in a trivial commit.
- After all items are done, update the session log in this tracker.
````

---

### Phase 5 Tier 3 — Planning (run this first, in Opus + effort xhigh)

**Recommended model:** Opus 4.7. Run `/effort xhigh`.

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

````
You are planning Phase 5 Tier 3 of the GEP workflow automation skill.
Run `/effort xhigh` before starting.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md`.
3. Read `.claude/commands/gep-feature.md` in full — this is the only file being changed.

Context:
- Branch: `feature/paulrussell/workflow-automation/gep-scripted-deploy`
- Phase 5 Tier 1+2 (items 1–6) are fully implemented and committed.
- Validation results are written to `GEP/tickets/<ticket>/validate_<env>_<ts>.json` by
  `python GEP/scripts/validate.py --save-results` (already live).
- MCP tools available: full Atlassian suite (`addCommentToJiraIssue`,
  `transitionJiraIssue`, `getTransitionsForJiraIssue`, `createIssueLink`, etc.).

Goal: produce a detailed implementation plan for items 7–13 below. The plan must be
specific enough that a separate Sonnet session can implement it by reading the plan +
the skill file — no ambiguity, no design decisions left open.

Items to plan:

**7 — Skill: PR creation step**
Between `test-deployed` and `uat`, offer to run:
  `gh pr create --base GEP/user-testing --title "..." --body "..."`
Pre-fill title from `jira_summary` and body from artifact fields (branch, requirements
summary, decisions). Show the full command for Paul to confirm before running. Record
the PR URL in the artifact (`pr_url` field). Currently a manual step easy to forget
before notifying the client.

**8 — Skill: Jira status transitions**
At each stage transition, show the proposed Jira status move and require Paul's
explicit "yes" before calling `transitionJiraIssue`. Mappings:
  `implementing` entered → "In Progress"
  `uat` entered → "In Review"
  `complete` entered → "Done"
Handle: MCP offline gracefully (skip with warning, don't block the transition), and
the case where the ticket is already in the target status.

**9 — Skill: Eclipse/PBI change tracking**
At the `scoped` stage, ask whether this feature requires:
  a) Eclipse connector template or connection changes
  b) PBI Desktop model changes (new table relationships, measures, calculated columns)
Add optional fields to the artifact schema to record this. If either applies, add
checklist items to the relevant deploy stage guidance (Eclipse changes block sandbox
deploy; PBI model changes must be published before `prod-deployed` is marked complete).

**10 — Skill: data dictionary update prompt**
At `prod-deployed` stage, if the delivery field references a new fact or dimension
(heuristic: table name contains `_FCT_` or `_DIM_`), prompt:
  "This ticket delivers a new fact/dimension. Update the wiki data dictionary for
   <table_name>? (yes / skip)"
If yes, show what page to update (wiki path) and what fields to document (grain, key
columns, date column, freshness window — all available from the validate manifest).

**11 — Skill: design summary comment at `test-deployed`**
Before transitioning to `uat`, draft a Jira comment that includes:
  - Locked requirements (all fields from artifact)
  - Key decisions (each with rationale)
  - Branch name
  - PR URL (from item 7, if available)
Pull all values from artifact — no manual copy-paste. Show the draft to Paul and
require "yes" before posting via `addCommentToJiraIssue`.

**12 — Skill: QA evidence comment at `test-deployed` and `prod-deployed`**
After validate.py passes, read `validate_<env>_<ts>.json` from the artifact's
`validate_results` path and build a Jira comment with:
  - Environment, database, git SHA + commit message
  - Validation timestamp
  - Full results table (check name / result value / ✅ or ❌)
  - Pass/fail summary line (e.g. "9/9 checks passed")
  - Path to the JSON results file
Only auto-draft for fully-passing runs. For failing runs: surface failures and ask
Paul whether to post a findings note — don't auto-draft.
Always require Paul's approval before calling `addCommentToJiraIssue`.
Post at both `test-deployed` (UAT evidence) and `prod-deployed` (production record).

**13 — Skill: PR remote link on Jira ticket**
When the PR is created (item 7), also surface the PR URL as a Jira remote link.
First determine whether the repo has Jira's native GitHub integration active — if it
does, this is a no-op. If not, use `createIssueLink` or include the PR URL in the
design summary comment (item 11). Plan which approach to use and why, then specify
the exact implementation.

Output format — for each item produce:
1. Exact skill file changes: which stage handler is affected, what text is added or
   replaced, with precise wording for any prompts shown to Paul.
2. Artifact schema changes: any new fields with types and default values.
3. MCP calls: exact tool name, parameters, and how to handle failure.
4. Interactions with other items: dependencies, sequencing requirements.
5. Edge cases: offline mode, MCP failure, field missing from artifact, etc.

Conclude with a recommended implementation order for the Sonnet session, with
rationale (e.g. item 13 depends on 7; item 12 depends on validate_results being
present from Phase 5 Tier 2 which is already live).

Do NOT write any code or edit any files. This is a planning-only session.
After producing the plan, update the session log in this tracker.
````

---

### Phase 5 — Observability, reliability & workflow completeness (Tier 1+2 complete ✅)

**Recommended model:** Sonnet 4.6 (execution session). Run `/effort high`.

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

**Context:** Phase 4 hardening complete and end-to-end tested via GP-197 feature-update
dry-run (2026-04-21). The dry-run surfaced new gaps across safety, observability, and
workflow completeness. This session implements the high-priority items.

**Tier 1 — Quick wins (implement now, commit each separately):**

1. **`validate.py` — git state in header** *(Trivial)*
   Same SHA + commit message line added to deploy.py in Phase 4. validate.py header
   should show the same so both outputs are self-describing snapshots of what was tested.

2. **Skill — SQL confirmation before TEST deploy** *(Low effort)*
   Sub-step 1 (sandbox) now confirms SQL is in place before deploying. Sub-step 2 (TEST)
   has no equivalent check — engineer could deploy stale SQL to the shared TEST env.
   Add the same confirmation prompt to Sub-step 2 before showing the TEST deploy command.

3. **Skill — sandbox teardown prompt after sandbox validate passes** *(Low effort)*
   Sandbox clones accumulate silently. After sandbox validate passes and before
   transitioning to Sub-step 2, prompt: "Sandbox validated. Tear down the sandbox clone
   now? (recommended — saves Snowflake storage)". If yes, show:
   `python GEP/scripts/deploy.py --env sandbox --ticket <ticket> --teardown`

4. **`deploy.py` — share health check flag** *(Medium effort)*
   Add `--check-share` flag that scans ALL warehouse SQL files (not just the manifest)
   for `PROD_DG1_GEP.*` references and probes each for accessibility. Run as a standalone
   pre-deploy health check. Skill should prompt to run this at the start of Sub-step 1
   (first deploy of a session, not every re-deploy).

**Tier 2 — Observability / artifact tracking (implement in this session):**

5. **`validate.py` — `--save-results` flag** *(Low effort)*
   Write structured JSON to `GEP/tickets/<ticket>/validate_<env>_<ts>.json` so results
   are persisted alongside the artifact without relying on Paul to report them manually.
   Skill should pass `--save-results` automatically and read the file to update the
   artifact instead of asking for results verbally.

6. **Artifact schema — formalise `sandbox` in `deploy_history`** *(Low effort)*
   The schema in the skill shows only `test` and `prod` under `deploy_history`. Sandbox
   was added manually during GP-197. Add `sandbox` as a first-class field with
   `deployed_at`, `validate_pass`, and `findings` — matching test/prod structure.

**Tier 3 — Workflow completeness (plan now, implement in follow-on session):**

7. **Skill — PR creation step**
   Between `test-deployed` and `uat`, skill should offer to run
   `gh pr create --base GEP/user-testing` automatically. Currently a manual step that
   is easy to forget before notifying the client.

8. **Skill — Jira status transitions**
   At each stage transition, auto-move the Jira ticket status via MCP
   (`transitionJiraIssue`). Map: `implementing` → In Progress, `uat` → In Review,
   `complete` → Done. Always show the proposed transition and require Paul's confirmation
   before calling the MCP.

9. **Skill — Eclipse/PBI change tracking**
   Add optional fields to the artifact for Eclipse connector changes and PBI model
   changes. Skill should ask at `scoped` stage whether the feature requires Eclipse
   template/connection changes or PBI Desktop model changes, and add checklist items
   to the relevant deploy stages.

10. **Skill — data dictionary update prompt**
    When a new fact or dimension is delivered, prompt at `prod-deployed` stage to update
    the wiki data dictionary page for that table.

**Tier 3b — Jira evidence integration (plan now, implement with Tier 3):**

11. **Skill — design summary comment at `test-deployed`**
    Before notifying the client, draft a Jira comment summarising locked requirements,
    key decisions (with rationale), PR link, and branch name. Pull all fields from the
    artifact — no manual copy-paste. Show draft to Paul and require "yes" before posting
    via `addCommentToJiraIssue`. This gives the client and team a permanent record of
    what was built and why, directly on the ticket.

12. **Skill — QA evidence comment at `test-deployed` and `prod-deployed`**
    After validate.py passes (all checks green), read the `validate_<env>_<ts>.json`
    written by `--save-results` and build a formatted Jira comment:
    - Environment, database, git state (SHA + commit message)
    - Validation timestamp
    - Full results table (check name / result value / pass ✅)
    - Pass/fail summary line
    - Path to the JSON results file for full detail
    Only auto-draft for **passing** runs. For failing runs: show Paul the failures and
    ask whether he wants to post a findings note — don't auto-draft, don't silently skip.
    Always require Paul's approval before calling `addCommentToJiraIssue`.

    **Post twice:** once at `test-deployed` (TEST evidence for client UAT sign-off) and
    once at `prod-deployed` (PROD evidence as permanent production-verified record).

13. **Skill — PR remote link on Jira ticket**
    When the PR is created (item 7 above), also add it as a remote link on the Jira
    ticket via `createIssueLink` or by including the PR URL in the design comment (item
    11). Jira's native GitHub integration may cover this automatically if the repo is
    connected — check before implementing to avoid duplication.

**Boot procedure:**
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker (you are here)
3. Read `GEP/scripts/deploy.py`, `GEP/scripts/validate.py`, `.claude/commands/gep-feature.md`
4. Checkout automation branch: `git checkout feature/paulrussell/workflow-automation/gep-scripted-deploy`
5. Implement Tier 1 items 1–4 and Tier 2 items 5–6, committing each separately
6. Update this tracker's session log when done

---

### Phase 4 — Hardening pass ✅

**Recommended model:** Sonnet 4.6 (execution session). Run `/effort medium`.

**Branch:** `feature/paulrussell/workflow-automation/gep-scripted-deploy`

**Context:** Phases 1–3 are implemented and end-to-end tested via GP-197. The workflow is functional but has 5 known robustness gaps that must be fixed before using on the next ticket. This session implements all 5 in one pass.

**Hardening items (implement all, commit to automation branch):**

1. **`validate.py` — table-not-found pre-check** *(Low effort)*
   Universal checks fail with an unhelpful Snowflake error if the target table doesn't exist yet (e.g. a new-table ticket deployed for the first time). Add a pre-check that queries `INFORMATION_SCHEMA.TABLES` for each table in the `tables:` section and skips universal checks with a clear warning if not found, rather than crashing.

2. **`deploy.py` — explicit new-view handling in snapshot** *(Low effort)*
   `snapshot_views()` currently logs a WARN and continues if `GET_DDL` fails for a view (e.g. the view is brand-new and doesn't exist yet). This is correct behaviour but should print a clear "new view — no rollback point exists for this view" message rather than a generic warning, so the engineer understands what the rollback covers.

3. **Skill — backward stage transition guard** *(Low effort)*
   The skill has no protection against accidentally moving to an earlier stage (e.g. re-running scoping on a `prod-deployed` ticket). Add a check: if the artifact exists and the requested operation would move to an earlier stage, show the current stage and require explicit confirmation (`force`) before proceeding.

4. **Skill — Jira MCP graceful fallback** *(Low effort)*
   If the Jira MCP call fails (network, auth, unavailable), the skill currently hard-fails. Add a fallback: catch the error, warn the user, and offer to continue in offline mode (skip Jira fetch; Paul supplies ticket summary manually). Artifact fields that would have been populated from Jira get a `"[manual entry required]"` placeholder.

5. **Process — TEST serialisation checklist** *(Documentation only)*
   No process exists for coordinating concurrent TEST deploys. Add a short checklist to `GEP/tickets/README.md` (create if not exists): before deploying to TEST, check whether another ticket is in `uat` stage (scan `GEP/tickets/*/artifact.yaml` for `stage: uat`). If yes, coordinate with the client before deploying. The skill should surface this warning automatically at the Sub-step 2 (TEST deploy) prompt.

**Out of scope for this session:**
- `WAREHOUSE_TEST_GP197` orphan schema — drop manually in Snowflake (one-off, not code)
- GP-197 PROD deploy — separate session after UAT sign-off
- GP-208 PROD deploy — separate session

**Boot procedure:**
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker (you are here)
3. Read `GEP/scripts/deploy.py`, `GEP/scripts/validate.py`, `.claude/commands/gep-feature.md` — these are the three files being hardened
4. Checkout automation branch: `git checkout feature/paulrussell/workflow-automation/gep-scripted-deploy`
5. Implement all 5 items above, committing each separately with a clear message
6. Update this tracker's session log when done

````
You are starting the client workflow automation workstream (Phase 4: hardening pass).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md` — the Phase 4 hardening section has the full task list.
3. Read these three files in full before making any changes:
   - `GEP/scripts/deploy.py`
   - `GEP/scripts/validate.py`
   - `.claude/commands/gep-feature.md`
4. Checkout the automation branch: `git checkout feature/paulrussell/workflow-automation/gep-scripted-deploy`

Goal: implement all 5 hardening items listed in the tracker under "Phase 4 — Hardening pass". Each item is self-contained and low-effort. Commit each separately. Do not touch warehouse SQL or GP-197 ticket files.

The workflow has been end-to-end tested via GP-197. These hardening items are the delta between "functional" and "reliable enough to use on the next ticket without surprises".
````

### Phase 3 — `/gep-feature` skill (complete, for reference)

**Recommended model:** Sonnet 4.6 (execution session). Run `/effort medium`.

Copy-paste into a fresh Claude Code session to implement Phase 3.

````
You are starting the client workflow automation workstream (implementation — Phase 3: feature workflow skill).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md`.
3. Read the design doc: `C:\Users\PaulRussell\repos\wiki\entities\projects\workflow-automation.md` — §2.4 and §3.7 are the most relevant sections (Phase 3 design).
4. Read `GEP/scripts/deploy.py` for repo conventions (path patterns, .env loading style).

Phases 1 (deploy.py) and 2 (validate.py) are complete on branch `feature/paulrussell/workflow-automation/gep-scripted-deploy`.

Goal for this session: implement the `/gep-feature` Claude Code skill (Phase 3).

The skill is a stateful feature workflow system — NOT a standalone script. It lives in `.claude/commands/gep-feature.md` (or the appropriate Claude Code skill location). Key capabilities:

- Jira MCP integration: list/fetch GEP tickets assigned to paul.russell@aldc.io; offer to post question lists as Jira comments (always require Paul's approval before posting)
- Per-ticket artifact: `GEP/tickets/<ticket>/artifact.yaml` (stage + requirements + decisions + change history) and `GEP/tickets/<ticket>/notes.md` (human narrative)
- Stage model: scoping → scoped → implementing → test-deployed → uat → feature-update → prod-deployed → complete
- Re-entry: `feature-update` stage reads existing artifact, asks only delta questions, appends to change_requests
- Wiki/Obsidian integration: create/update `wiki/tickets/gep/<ticket>.md` after each stage transition

Invocation examples (from the design doc §3.7):
  /gep-feature              → list assigned GEP tickets
  /gep-feature GP-208       → open at current stage, or start scoping if new
  /gep-feature GP-208 change "client wants weekly history not current snapshot"

Stay in lane: `.claude/commands/gep-feature.md` (skill) + `GEP/tickets/` (artifacts, gitignored or committed TBD). Do not edit deploy.py, validate.py, or warehouse SQL.

First implementation step: agree on the skill file location and artifact schema with Paul before writing any code. Check where Claude Code skills live in this repo first.
````

### Phase 2 — validation suite (complete, for reference)

**Recommended model:** Sonnet 4.6 (execution session). Run `/effort medium`.

````
You are starting the client workflow automation workstream (implementation — Phase 2: validation suite).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\client-workflow-automation.md`.
3. Read the design doc: `C:\Users\PaulRussell\repos\wiki\entities\projects\workflow-automation.md` — §3.5 (validate.py design sketch) is the most relevant section.
4. Read `GEP/scripts/deploy.py` for conventions and patterns to follow (auth, .env loading, logging style, manifest format).

Phase 1 (deploy.py) is complete and committed on branch `feature/paulrussell/workflow-automation/gep-scripted-deploy`.

Goal for this session: implement `validate.py` (Phase 2) at `GEP/scripts/validate.py`.
- Python 3.11, `snowflake-connector-python` (same venv and .env as deploy.py)
- `--env sandbox|test|prod`, `--ticket <ID>` flags
- Universal checks: row count non-zero, no nulls in key columns, PRODUCT_KEY join rate ≥95%, no duplicates on primary key, data freshness
- Per-ticket checks loaded from `GEP/scripts/validate_manifest/<ticket>.yaml`
- Structured pass/fail output with row counts and diffs
- GP-208 ticket config as the first example (see design doc §3.5 for the check definitions)

Stay in lane: only `GEP/scripts/validate.py` (new file) and `GEP/scripts/validate_manifest/` (per-ticket YAMLs). Do not edit deploy.py or warehouse SQL.
````

## See Also

- [[../README]]
- [[../orchestration-pattern]]
- [[../session-lifecycle]]
- [[GEP]]
- [[gep-snowflake-pbi-deployment]]
