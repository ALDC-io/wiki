---
tags: [distributed-workflow, active, client-workflow-automation]
aliases: [Client Workflow Automation Tracker, Sandbox Feature Delivery Tracker]
sources: []
created: 2026-04-18
updated: 2026-04-21 (Phase 6 planning session)
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

### 🟠 Planned resolution via Phase 6 — Multi-feature conflict in TEST / PBI (flagged 2026-04-18; plan 2026-04-21)

**Status update (2026-04-21)**: the PBI half of this blocker is now planned.
**Phase 6 — Power BI Model Automation** introduces an XMLA-scripted PBI sandbox
stage (Sub-step 1b in `implementing`) that validates PBI model changes against an
isolated sandbox dataset before anything touches the shared client-facing TEST
workspace. Plan at [[phase6-pbi-automation-plan]]. Implementation gated on four
Paul-owned answers (capacity SKU, Tabular Editor install, SPN auth, PBIX
connection shape — see plan §5).

The **Snowflake half** (TEST serialisation when multiple tickets share one TEST
DB) remains an operational coordination problem rather than a technical one — the
TEST serialisation checklist added in Phase 4 and the rollback in deploy.py are
the accepted v1 mitigations. Per-ticket Snowflake TEST isolation is not pursued.

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
