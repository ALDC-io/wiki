---
tags: [project, automation, gep, snowflake, workflow, design]
aliases: [Client Workflow Automation, Feature Delivery Automation, GEP Automation Design]
sources: [processes/distributed-workflow/active/client-workflow-automation.md, wiki pages: GEP, gep-snowflake-pbi-deployment, flight-check, git-branching-strategy, ticket-breakdown-to-ship, GP-207, GP-208, accumulating-source-tables, snowflake-data-share-refresh]
created: 2026-04-18
updated: 2026-04-18 (Phase 3 design expanded)
---

# Client Workflow Automation — Design

Design for an automated, sandboxed feature-delivery flow for client data engineering work, targeting the [[GEP]] stack as the primary case. This document covers the current lifecycle map, the highest-leverage automation candidates, a sandbox implementation design, and a phased build roadmap.

> **Status**: Design approved 2026-04-18. Implementation is a follow-on workstream gated on this document. See the workstream tracker at [[processes/distributed-workflow/active/client-workflow-automation]].

---

## 1. Current GEP Feature Lifecycle

### 1.1 End-to-End Map (Requirements → Ship)

The table below maps every phase from ticket creation to production cleanup. "Human touches" rates how much manual effort falls on the engineer.

| Phase | Key steps | Human touches |
|---|---|---|
| **0. Scoping** | Read ticket; draft questions for client (data source, grain, delivery, business logic); wait for client response | **High** — responses take days to weeks |
| **1. Research & Design** | Check existing patterns in [[clients-repo]]; verify dimension table completeness; audit data share against all `PROD_DG1_GEP.*` references; draft SQL | Medium |
| **2. Implementation** | Feature branch; SQL views/tables; Eclipse connection/template JSONs if new source; CosmosDB registration; personal test schema (`WAREHOUSE_TEST_PAUL`) | Medium |
| **3. Code review** | PR to `GEP/development`; reviewer feedback; merge | Low |
| **4. TEST deploy ★** | Snapshot baseline counts → open Snowsight → copy-paste each SQL file in dependency order → watch for errors → navigate to Task History → trigger `TASK_WAREHOUSE_ORDERLINE_0` manually → watch 10 DAG steps → run functional / volume / currency queries → trigger PBI refresh → smoke-test in browser | **Highest friction** |
| **5. PR to user-testing + notify** | PR `GEP/development` → `GEP/user-testing`; email client | Low |
| **6. UAT** | Client tests in GEP Test Models; may surface issues needing hotfix branches | **Blocked on client** — days to weeks |
| **7. PROD deploy ★** | Repeat all of Phase 4 against `PROD_DG1_GEP`; PBI Desktop: download `.pbix`, set prod params, refresh data, publish; PR `GEP/user-testing` → `main` | **Highest friction** (same as Phase 4, done again) |
| **8. Cleanup** | Drop personal test schema; archive scratch files; file follow-up tickets | Low |

### 1.2 Friction Analysis — Highest-Pain Steps

Six concrete friction sources, ordered by severity:

**1. Manual SQL deploy to Snowsight (Phases 4 + 7)**
The engineer opens the Snowsight UI, pastes each changed SQL file individually, executes them in dependency order, and repeats for both the test and production environments. There is no automation, no rollback mechanism, and no record of what ran in what order. A missed file or wrong order causes a task chain failure that is only discovered minutes later.

**2. Ad-hoc eyeball QA**
Validation queries are written fresh for each ticket. Results are compared visually against baseline counts that were captured earlier and saved in a text file. There is no standardized check suite, no threshold enforcement, and no pass/fail output. "Looks about right" is the acceptance criterion. This produced real bugs: GP-208 discovered two code defects (FBA stale-row bug, MAX-date filter silently dropping Sellercloud rows) only because Paul happened to notice anomalous row counts by eye.

**3. Data-share gap discovery at runtime**
The test data share (`PROD_DG1_GEP`) is manually maintained in the Snowflake prod UI — its contents are not tracked in the repo. Gaps are only discovered when a view fails to compile during the task chain run. GP-200 surfaced two missing objects (`CURRENT_MAIN_PURCHASEITEM`, `CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`) this way, costing significant debugging time.

**4. Share freshness going undetected**
Eclipse shows partitions as "Complete" regardless of whether the downstream Snowflake data share is propagating new data. The GP-208 incident: `PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_INVENTORY_PANDL` was frozen for 42 days. No alerting fired. Client didn't notice because inventory dashboards were not actively used. Detection was accidental. See [[snowflake-data-share-refresh]] for the full failure-mode analysis.

**5. Dependency-order management**
The engineer must mentally track view dependencies (e.g., `sales_dim_order_base` must precede `sales_fct_amazon_orderline` which must precede `sales_fct_orderline`). This knowledge is documented in the runbook but not enforced programmatically. A wrong order fails silently at deploy time.

**6. Power BI validation**
Triggering a PBI refresh, waiting for it to complete, and then navigating the browser to smoke-test data visually takes 20–40 minutes and cannot be automated today (no public API for PBI workspace refresh status monitoring or Explore-mode scripting). This is an accepted manual half-step — see §3.6.

---

## 2. Automation Candidates

### 2.1 Scoring Methodology

Each candidate scored 1–5 on two dimensions:
- **Impact**: how much engineer time / risk / reliability does this recover per deploy cycle?
- **Feasibility**: how achievable is this with the existing stack (Snowflake Python connector, TEST environment, branch model) and without new infrastructure?

Score = Impact × Feasibility.

### 2.2 Candidate A — Scripted SQL Deploy + Task-Chain Trigger

**What it replaces**: The copy-paste-into-Snowsight workflow for both TEST and PROD deploys.

**How it works**: A Python script (`deploy.py`) reads a deploy manifest (ordered list of SQL files for the changeset), executes each file against the target environment via the Snowflake Python connector, then programmatically triggers `TASK_WAREHOUSE_ORDERLINE_0` and polls until all DAG steps complete. Output: per-step success/failure log.

```
deploy.py --env test --ticket GP-208 --files inventory_fct_balance.sql,extract_inventory_current.sql
  → CREATE SCHEMA IF NOT EXISTS WAREHOUSE_TEST_GP208
  → execute inventory_fct_balance.sql (WAREHOUSE_TEST_GP208 context)
  → execute extract_inventory_current.sql
  → trigger TASK_WAREHOUSE_ORDERLINE_0
  → poll task history → all 10 steps SUCCEEDED
  → report: ✅ Deploy complete in 4m 12s
```

**Data share pre-flight check** baked in: before running any SQL, the script runs a `SELECT COUNT(1)` against every `PROD_DG1_GEP.*` object referenced in the target files. Any "object not found" errors surface before the task chain runs, not during it.

**Impact**: 5 — eliminates the most error-prone, time-consuming manual step; every deploy benefits. Paid back on the first use.
**Feasibility**: 5 — `snowflake-connector-python` is well-supported; Snowflake task execution and history are fully API-accessible.
**Score**: 25

### 2.3 Candidate B — Structured Post-Deploy Validation Suite

**What it replaces**: Ad-hoc eyeball QA; manually saved baseline counts.

**How it works**: A validation harness (`validate.py`) runs a standard suite of checks against the just-deployed schema and compares against expected thresholds. Checks are a mix of universal (always run) and ticket-specific (declared in a per-ticket config). Output: structured pass/fail report with diffs against baseline.

Universal checks:
- Row count is non-zero for each deployed fact/extract
- No null values in mandatory key columns (`PRODUCT_ID`, `ORDER_KEY`, `BALANCE_DATE`)
- `PRODUCT_KEY` join rate to `SHARED_DIM_PRODUCT` ≥ 95%
- Duplicate check on primary key (zero-tolerance for Phase 1 current-snapshot facts)
- Data freshness: `MAX(date column)` within expected recency window

Ticket-specific checks (example for GP-208):
- `INVENTORY_FCT_BALANCE` row count = `SELLERCLOUD_GEP2 ∪ AMAZON_FBA` count (± 1% tolerance per [[accumulating-source-tables]])
- `MIN(BALANCE_DATE) = MAX(BALANCE_DATE)` for current-snapshot invariant (Phase 1)
- All `GEP2_ON_HAND_QTY` and `US_FBA_AVAILABLE_QTY` ≥ 0 (negative reserved values logged separately)

**Impact**: 5 — converts "looks about right" into an objective pass/fail gate; catches bugs that GP-208's code fixes only found by eye.
**Feasibility**: 3 — the queries exist (in [[flight-check]] and [[gep-snowflake-pbi-deployment]]); the harder part is a robust baseline management system and a per-ticket config schema. Medium engineering work.
**Score**: 15

### 2.4 Candidate C — Stateful Feature Workflow System

**What it replaces**: The entire manual coordination layer — question drafting, requirements tracking, decision logging, change-request triage, and the currently absent re-entry mechanism when a client raises an issue mid-UAT.

**Original design (superseded 2026-04-18)**: a simple CLI script that generated a list of clarifying questions. Replaced because it only addressed the front end of the problem (initial scoping) and produced no persistent artifact, making re-entry impossible.

**Revised design**: A Claude Code skill that manages a ticket through its full lifecycle. The skill is stateful — it reads and writes a per-ticket artifact in the repo, knows the current stage, and re-enters at the right point without re-asking questions already answered. See §3.7 for the full design.

**Key capabilities added over the original sketch:**
- Full stage model (scoping → designed → implementing → test-deployed → UAT → feature-update → prod-deployed → complete)
- Per-ticket artifact (`GEP/tickets/<ticket>/`) as the source of truth for requirements, decisions, and change history
- Jira MCP integration — fetch tickets assigned to Paul, post question lists as comments
- Re-entry at any stage — client change request drops back into the workflow at `feature-update`; only delta questions are asked
- Wiki/Obsidian integration — ticket page created/updated after each stage transition

**Impact**: 4 — closes the loop on the entire pre-implementation and post-deploy-change workflow; not just question generation.
**Feasibility**: 3 — more complex than the original sketch; requires Jira MCP, artifact schema, and stage-aware skill logic.
**Score**: 12

### 2.5 Ranking Summary

| Rank | Candidate | Impact | Feasibility | Score | v1? |
|---|---|---|---|---|---|
| 1 | Scripted SQL deploy + task-chain trigger | 5 | 5 | 25 | ✅ |
| 2 | Data share freshness monitoring | 4 | 5 | 20 | ⏸ deferred |
| 3 | Structured post-deploy validation suite | 5 | 3 | 15 | ✅ |
| 4 | Auto dependency-order resolution | 3 | 4 | 12 | baked into deploy script |
| 5 | Stateful feature workflow system | 4 | 3 | 12 | ✅ |

> **Note on share freshness monitoring (Rank 2)**: This was the quickest win technically — a single Snowflake scheduled task, a few detection queries (documented in [[snowflake-data-share-refresh]]), and an alert. It's deferred from v1 not because it's hard but because the three selected candidates represent the full feature-delivery loop. Freshness monitoring is infrastructure/ops rather than feature-delivery. Recommend picking it up in a standalone v2 ops ticket.

---

## 3. Top Candidate: Scripted Deploy + Automated Validation

### 3.1 What the Automated Loop Looks Like

The v1 loop replaces the highest-friction phases (4 and 7 from §1.1):

```
Developer opens feature branch
  │
  ├─ [manual] Write SQL, Eclipse configs
  ├─ [manual] PR to GEP/development, code review, merge
  │
  ▼
deploy.py --env test --ticket <ID> --files <list>
  ├─ pre-flight: SELECT COUNT(1) on all PROD_DG1_GEP.* references
  ├─ CREATE SCHEMA IF NOT EXISTS WAREHOUSE_TEST_<ticket>
  ├─ execute each SQL file (dependency order from manifest)
  ├─ trigger TASK_WAREHOUSE_ORDERLINE_0
  ├─ poll task history until all steps SUCCEEDED (or timeout + error)
  └─ ✅ "Deploy complete" / ❌ "Step N failed: <error>"
  │
validate.py --env test --ticket <ID>
  ├─ universal checks (nulls, key join rate, duplicates, freshness)
  ├─ ticket-specific checks (from <ticket>.yaml config)
  └─ ✅ "All 12 checks passed" / ❌ "3 checks failed: [details]"
  │
  ├─ [manual] Review validation report
  ├─ [manual] PBI: trigger refresh, smoke-test in browser (§3.6)
  ├─ [manual] PR GEP/development → GEP/user-testing
  ├─ [manual] Notify client; UAT
  │
deploy.py --env prod --ticket <ID> --files <list>
validate.py --env prod --ticket <ID>
  │
  ├─ [manual] PBI Desktop: set prod params, publish
  ├─ [manual] PR GEP/user-testing → main
  └─ [manual] flight-check
```

**What's automated**: SQL deploy, dependency ordering, data share pre-flight, task chain execution, structured QA checks.

**What stays manual**: PBI refresh + smoke-test (§3.6), prod PBI publish, git merges, client notifications.

### 3.2 Sandbox Scope — Why True Ephemeral Isn't Practical

The clean theoretical model is: each feature branch gets a fully isolated environment (Snowflake + PBI workspace) that is auto-provisioned on branch open and auto-destroyed on merge. This is achievable on the Snowflake side. It is **partially** achievable on the Power BI side — enough to unblock most automation, but not enough for per-ticket workspace clones.

**PBI constraint (revised 2026-04-24 after Phase 6 validation)**: Power BI supports three relevant APIs:
- **XMLA write** (Premium/PPU/Fabric) — full programmatic model metadata changes (tables, columns, relationships, measures, partitions). Available and in use — see [[pbi-xmla-automation]] and the 2026-04-24 GP-208 validation.
- **REST refresh + parameter update** — trigger refreshes, poll status, rebind data-source parameters. Available and in use.
- **REST workspace / `.pbix` import** — creating workspaces and importing `.pbix` files programmatically *does* work (2025 API update), but each workspace consumes Premium capacity. We chose one **persistent sandbox workspace** over per-ticket clones for capacity reasons — see [[phase6-pbi-automation-plan]] §2.
- **Visual layer** — still no public API for pages, visuals, bookmarks, colours. These remain manual PBI Desktop edits.

**Consequence (revised 2026-04-24)**: the automatable PBI stack is now: rebind sandbox dataset parameters → apply model metadata via XMLA → trigger refresh → poll → verify rows via DAX. Visual validation is the only remaining manual step for metadata-only changes; visual-bearing changes (`changes.pbi_model.visual_required = true`) still require the PBI Desktop republish path.

### 3.3 Practical Sandbox: Per-Feature Schema in TEST_DG1_GEP

**Decision** (confirmed 2026-04-18): sandbox = Option B — TEST_DG1_GEP + per-feature Snowflake schemas.

The sandbox is defined as:

| Layer | How it's isolated | Lifecycle |
|---|---|---|
| Snowflake compute | WAREHOUSE_TEST_<ticket> schema in TEST_DG1_GEP | Auto-created by `deploy.py`; auto-dropped by teardown script or on PR merge |
| Raw source data | PROD_DG1_GEP data share (via GP-207) — same data as production | Persistent; not per-feature |
| Power BI | GEP Test Models workspace (shared across all in-flight features) | Persistent; manual refresh per feature |

**Why this is sufficient**:
- The GP-207 prod→test data share means test schemas see production data volumes — the main historical reason "test ≠ prod" was that test had its own smaller source tables.
- Per-ticket schema isolation prevents in-flight features from clobbering each other in the WAREHOUSE layer.
- The validation harness (§3.5) provides the QA rigour that previously depended on eyeball interpretation.

**Known limitation**: two in-flight features that touch the same PBI test workspace can conflict if both trigger a PBI refresh simultaneously. Accept this — it's the same limitation as today and is managed by coordination, not tooling.

### 3.4 deploy.py — Script Design Sketch

Language: Python 3.11, using `snowflake-connector-python`.

```python
# Usage:
#   python deploy.py --env test --ticket GP-208 \
#     --files inventory_fct_balance.sql,extract_inventory_current.sql

# Key operations:
# 1. Parse --env (test → TEST_DG1_GEP, prod → PROD_DG1_GEP)
# 2. Load deploy manifest (explicit file list, or infer from ticket YAML)
# 3. Pre-flight: scan SQL files for PROD_DG1_GEP.*.* references;
#    run SELECT COUNT(1) on each; fail fast if any object not found
# 4. Create target schema: WAREHOUSE_TEST_<ticket> (test) or WAREHOUSE (prod)
# 5. Execute each SQL file in order against the target schema
# 6. Trigger TASK_WAREHOUSE_ORDERLINE_0 via EXECUTE TASK
# 7. Poll INFORMATION_SCHEMA.TASK_HISTORY every 30s; timeout after 20m
# 8. Print structured log: step name, state, duration, error_message if any
```

**Dependency ordering**: initially managed by an explicit per-ticket manifest file (`GEP/snowflake/deploy/<ticket>.yaml`) that lists SQL files in order. A future enhancement can infer the order by parsing `FROM WAREHOUSE_SOURCE.*` and `FROM WAREHOUSE.*` references in each file.

**Credentials**: loaded from environment variables (`SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_ACCOUNT`) or a local `.env` file (gitignored). Never hardcoded.

**Idempotency**: `CREATE OR REPLACE` semantics in the SQL files mean re-running the script is safe. The pre-flight check ensures the schema is clean before triggering the task chain.

### 3.5 Validation Harness — Design Sketch

Language: Python 3.11, using `snowflake-connector-python` + `pytest` or a lightweight custom reporter.

**Config file** (`GEP/snowflake/validate/<ticket>.yaml`):

```yaml
ticket: GP-208
env: test  # overridden at runtime

checks:
  - name: inventory_fact_non_empty
    query: "SELECT COUNT(*) FROM WAREHOUSE_TEST_GP208.WAREHOUSE.INVENTORY_FCT_BALANCE"
    assert: "count > 0"

  - name: no_null_product_id
    query: "SELECT COUNT(*) FROM WAREHOUSE_TEST_GP208.WAREHOUSE.INVENTORY_FCT_BALANCE WHERE PRODUCT_ID IS NULL"
    assert: "count = 0"

  - name: product_key_join_rate
    query: |
      SELECT 100.0 * SUM(CASE WHEN PRODUCT_KEY IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*)
      FROM WAREHOUSE_TEST_GP208.WAREHOUSE.INVENTORY_FCT_BALANCE
    assert: "value >= 95"

  - name: fba_data_present
    query: |
      SELECT COUNT(*)
      FROM {db}.WAREHOUSE.INVENTORY_FCT_BALANCE
      WHERE FBA_AVAILABLE_QUANTITY IS NOT NULL
    assert: "result > 0"  # no SOURCE column — FBA presence is implicit via non-null qty

  - name: no_duplicate_product_id
    query: |
      SELECT COUNT(*) FROM (
        SELECT PRODUCT_ID, COUNT(*) c
        FROM WAREHOUSE_TEST_GP208.WAREHOUSE.INVENTORY_FCT_BALANCE
        GROUP BY PRODUCT_ID HAVING c > 1
      )
    assert: "count = 0"
```

Output format:

```
validate.py --env test --ticket GP-208

  ✅ inventory_fact_non_empty         3,510 rows
  ✅ no_null_product_id               0 nulls
  ✅ product_key_join_rate            97.3% (≥ 95%)
  ✅ current_snapshot_single_date     1 distinct FBA date
  ✅ no_duplicate_product_id         0 duplicates

  5/5 checks passed. Ready for PBI validation.
```

**Baseline comparison**: for volume sanity (not individual fact correctness), the harness can optionally accept a `--baseline` path to a previously-saved JSON of row counts and emit a diff. This replaces the manual "snapshot counts before deploy, compare after" step from [[gep-snowflake-pbi-deployment]] Phase 4.

### 3.7 Phase 3: Feature Workflow System — Design

#### Tool form

A **Claude Code skill** (not a standalone script). Runs inside a Claude Code session where the Atlassian MCP, wiki files, and repo files are all accessible in context. Skills are invoked as `/gep-feature <ticket-id>` and maintain state across turns within the session via the artifact on disk.

#### Artifact structure

One folder per ticket in the repo:

```
GEP/tickets/
  GP-208/
    artifact.yaml    # machine-readable: stage, requirements, decisions, change history
    notes.md         # human narrative — generated/updated by the skill after each stage
```

`artifact.yaml` schema:

```yaml
ticket: GP-208
jira_summary: "Inventory feed ingestion & modeling"
assignee: paul.russell@aldc.io
stage: scoped                      # current stage (see stage model below)
stage_history:
  - stage: scoping
    entered: 2026-04-18
    exited: 2026-04-18
  - stage: scoped
    entered: 2026-04-18
    exited: null

requirements:
  data_source: "Sellercloud GEP2 + Amazon FBA"
  grain: "One row per product (current snapshot)"
  delivery: "WAREHOUSE.INVENTORY_FCT_BALANCE"
  business_logic: "..."
  history_scope: "current only (Phase 1)"
  open_questions: []              # questions pending client response

decisions:
  - date: 2026-04-18
    decision: "Use ARRAY_MIN of all source dates for BALANCE_DATE"
    rationale: "Products may have inventory in multiple sources with different dates"
    alternatives_considered:
      - "Use MAX date"
      - "Source-specific date columns"

change_requests: []              # appended on each feature-update entry
```

#### Stage model

```
scoping        → interactive Q&A to gather requirements from Jira + Paul
scoped         → requirements locked; pending implementation
implementing   → code being written; branch name recorded
test-deployed  → deploy.py + validate.py run against TEST; results recorded
uat            → client testing; awaiting feedback
feature-update → change request received; re-entering workflow (delta Q&A only)
prod-deployed  → deploy.py + validate.py run against PROD; results recorded
complete       → shipped and signed off
```

`feature-update` is a re-entry point that can follow `uat` or even `prod-deployed`. Multiple rounds are supported — each appends to `change_requests:` in the artifact.

#### Jira MCP integration

- **List**: fetch tickets from the GEP project assigned to `paul.russell@aldc.io` — this is the default entry point when no ticket ID is given.
- **Fetch**: pull a specific ticket by key (summary, description, acceptance criteria, comments) and cache into `artifact.yaml`.
- **Comment**: after scoping is complete, the skill formats the open-questions list and offers to post it as a Jira comment for Paul to review before sending.
- Filter is always `assignee = currentUser()` — never pulls unassigned or other-team tickets.

#### Re-entry for feature-update

When the skill detects an existing artifact in `feature-update` stage (or Paul invokes with a change description):

1. Read and summarise existing `artifact.yaml` — show current requirements and prior decisions.
2. Read the change request (Paul describes or pastes the client feedback).
3. Identify which existing requirements/decisions are affected.
4. Ask only the delta questions — no re-asking of already-answered items.
5. Present solution options with tradeoffs where there is design choice.
6. Append to `change_requests:` and record affected decisions.
7. Transition stage back to `implementing` or `designing` as appropriate.

#### Wiki/Obsidian integration

After each stage transition, the skill creates or updates `wiki/tickets/gep/<ticket>.md` using standard wiki conventions (frontmatter, wikilinks, created/updated dates). Sections:

- **Summary** — Jira summary + one-line description
- **Requirements** — structured requirements from artifact
- **Decisions** — each decision with rationale and alternatives considered
- **Change Requests** — chronological log of client-requested changes
- **Deploy history** — links to TEST and PROD validate.py run results
- **See Also** — wikilinks to [[GEP]], related tickets, relevant patterns

This file IS the Obsidian ticket page — the wiki is already Obsidian-compatible (YAML frontmatter, `[[wikilinks]]`). No separate sync needed.

#### Skill invocation examples

```
/gep-feature              → list my assigned GEP tickets via Jira MCP; pick one
/gep-feature GP-208       → open existing artifact at current stage, or start scoping if new
/gep-feature GP-208 change "client wants weekly history, not just current snapshot"
                          → re-enter at feature-update stage with that change description
```

### 3.6 The Remaining Manual Half (Visual Validation Only, as of 2026-04-24)

> **Revised 2026-04-24** after Phase 6 shipped. What this section described as "always manual" is now mostly automated for metadata-only changes. The only genuinely manual PBI step for metadata-only tickets is the visual pass/fail gate.

**For metadata-only PBI changes (new tables, columns, relationships, measures, format strings):**

1. **Model apply** — `pbi_model_apply.exe` over XMLA, invoked by `/gep-feature` Sub-step 1b. Automated.
2. **Refresh** — REST `POST /refreshes` + poll. Automated.
3. **Row-count verification** — DAX `COUNTROWS` via REST `executeQueries`. Automated.
4. **Visual pass/fail** — Paul opens the workspace, confirms affected visuals render correctly with no regressions. **Manual, by design** — no public API can render visuals.

See [[pbi-xmla-automation]] for the full loop and [[pbi-model-apply-wrapper]] for the .NET wrapper.

**For visual-bearing changes** (`changes.pbi_model.visual_required = true` — e.g. new report pages, visual swaps, bookmark changes):

The manual PBI Desktop flow still applies: download `.pbix` from `repos/power_bi`, edit, republish. The `visual_required` flag set at `scoped` stage routes these tickets to the manual path and skips the auto-apply at prod-deployed.

**Prod deploy**: `deploy.py --env prod` + `validate.py --env prod` for Snowflake. For PBI, metadata-only changes auto-apply via XMLA (Tranche D of [[phase6-pbi-automation-plan]], staged for post-dogfood); visual-bearing changes republish manually in PBI Desktop per [[gep-snowflake-pbi-deployment]] §10.

---

## 4. Existing Automation Primitives

The v1 design deliberately composes from what already exists rather than building new infrastructure.

| Primitive | Where it lives | How v1 uses it |
|---|---|---|
| `TEST_DG1_GEP` Snowflake environment | Snowflake (always-on) | Target for per-feature schemas; already has GP-207 share mounted |
| GP-207 prod→test data share | `PROD_DG1_GEP` outbound share | All `WAREHOUSE_TEST_<ticket>` schemas read prod-volume data automatically |
| `TASK_WAREHOUSE_ORDERLINE_0` DAG | Snowflake task chain, 10 steps | `deploy.py` triggers this via `EXECUTE TASK`; already manually triggerable |
| Flight-check query suite | [[flight-check]] (manual process today) | `validate.py` automates the key queries from this page as universal checks |
| Per-ticket test schema pattern | `WAREHOUSE_TEST_PAUL` (informal today) | Formalized as `WAREHOUSE_TEST_<ticket>` + auto-lifecycle |
| Branch model | [[git-branching-strategy]] | deploy.py's `--ticket` param maps naturally to feature branch names |
| `GEP/snowflake/warehouse/` SQL files | [[clients-repo]] | Input files for `deploy.py`; no schema changes needed |
| Snowflake Python connector | pip: `snowflake-connector-python` | Library that powers `deploy.py` and `validate.py`; no infra needed |
| Existing validation queries | [[gep-snowflake-pbi-deployment]] §7 | Starting material for `validate.py` universal check suite |

---

## 5. Implementation Roadmap

Three phases, each independently shippable. No phase depends on the next being complete.

### Phase 1 — Scripted Deploy (highest leverage, ship first)

**Deliverable**: `deploy.py` script in `GEP/scripts/` (or a shared `scripts/` location if multi-client).

Scope:
- Reads deploy manifest (per-ticket YAML)
- Pre-flight share check (SELECT COUNT on all PROD_DG1_GEP.* refs)
- Executes SQL files in declared order against TEST or PROD
- Triggers TASK_WAREHOUSE_ORDERLINE_0 and polls to completion
- Logs per-step result

**Next ticket to validate against**: GP-208 PROD deploy (currently blocked on Sellercloud share restore). Phase 1 script can be written and tested against the GP-208 TEST re-deploy once the share is restored.

### Phase 2 — Validation Suite

**Deliverable**: `validate.py` harness + universal check definitions + GP-208 ticket config as the first example.

Scope:
- Universal check suite (nulls, join rates, duplicates, freshness)
- Per-ticket YAML config schema
- GP-208 checks as the canonical first example (per QA checklist in [[GP-208]])
- Baseline snapshot + diff for volume sanity

**Follow-on**: migrate the ad-hoc validation queries from `GEP/_testing/GP-208/` into formal YAML configs. Use as the template for all future tickets.

### Phase 3 — Stateful Feature Workflow System ✅ design approved 2026-04-18

**Deliverable**: Claude Code skill (`/gep-feature`) + per-ticket artifact schema (`GEP/tickets/<ticket>/`).

Scope:
- Jira MCP integration — list/fetch tickets assigned to `paul.russell@aldc.io`; post question comments
- Interactive requirements Q&A guided by wiki context (client entity, existing patterns, prior tickets)
- Per-ticket artifact: `artifact.yaml` (machine-readable state) + `notes.md` (human narrative)
- Full stage model: scoping → scoped → implementing → test-deployed → uat → feature-update → prod-deployed → complete
- Re-entry at any stage — `feature-update` asks only delta questions; appends to change history
- Solution options with tradeoffs presented before any implementation decision is locked
- Wiki/Obsidian integration: `wiki/tickets/gep/<ticket>.md` created/updated after each stage transition

**Dependency**: independent of Phases 1–2 but designed to hand off into `deploy.py` and `validate.py` at the implement → deploy stages. The three phases compose into a full end-to-end feature delivery loop.

---

## 6. Open Questions + Decisions Needed

| # | Question | Status | Default if unresolved |
|---|---|---|---|
| 1 | Where do `deploy.py` and `validate.py` live — `GEP/scripts/`, a shared `scripts/`, or a separate repo? | **Resolved 2026-04-26** | Separate `aldc-shipyard` repo (formerly `aldc-automation`) — keeps scripts off `clients`/`connector` CI/CD chains; neutral ground for multi-repo orchestration; scalable to other clients. See [[client-workflow-automation]] "Near-term Architecture Goal". |
| 2 | Deploy manifest: explicit per-ticket YAML list vs. inferred from SQL dependency parse | Open | Explicit list first; dependency inference in Phase 1 follow-on |
| 3 | Should `deploy.py` auto-drop `WAREHOUSE_TEST_<ticket>` on script exit, or leave it for manual inspection and teardown by a separate command? | Open | Leave it; explicit `--teardown` flag on a separate run |
| 4 | Validation thresholds (e.g., 95% key join rate) — are these universal or should each client have its own? | Open | Start universal; tune per client as data reveals real distributions |
| 5 | Does Phase 3 live in the `clients` repo or as a Claude Code skill? | **Resolved** | Claude Code skill for the interactive workflow; artifact files (`GEP/tickets/`) live in the repo |
| 6 | Share freshness monitoring (deferred): when does it get prioritized? | Deferred | After v1 ships and the Sellercloud share incident is fully resolved |
| 7 | Phase 3 skill name — `/gep-feature` or something else? | Open | `/gep-feature` proposed; rename before shipping if a better name emerges |
| 8 | Obsidian ticket page structure — what sections, what frontmatter tags? | **Resolved** | Standard wiki format; sections: Summary, Requirements, Decisions, Change Requests, Deploy history, See Also |
| 9 | Should the skill post Jira comments automatically or always require Paul's approval first? | Open | Always require approval — show draft and ask before posting |
| 10 | Multi-round change requests — does `feature-update` support re-entry more than once? | **Resolved** | Yes — each round appends to `change_requests:` array; no limit on rounds |

---

## 7. Out of Scope (v1)

The following are explicitly excluded from v1 to keep scope bounded:

- ~~**PBI automation**~~: **resolved 2026-04-24 for metadata-only changes** via Phase 6 — see [[pbi-xmla-automation]], [[phase6-pbi-automation-plan]]. Refresh triggering and model-metadata changes are now scripted through XMLA + REST. Per-ticket workspace provisioning is still deferred (one persistent sandbox workspace instead — capacity cost rationale in §2 of the plan). Visual regression automation remains blocked (no public PBI API for visual rendering).
- **PBI visual validation automation** *(future roadmap — v2)*: automated render-and-diff of report visuals post-deploy. Still blocked by the absence of a public PBI API for visual-level rendering or query execution against the visual layer. DAX-level query checks (§3.5 Snowflake validation + `executeQueries` DAX smoke-tests) partially substitute. Track the Microsoft Fabric public roadmap.
- **Prod deploy automation beyond Snowflake SQL**: for metadata-only PBI changes — now automated (Tranche D of [[phase6-pbi-automation-plan]], staged for post-dogfood). For visual-bearing changes (`visual_required = true`), the PBI Desktop publish step (download `.pbix`, set params, republish) stays manual by design.
- **CI/CD integration**: running `deploy.py` and `validate.py` from GitHub Actions on PR events is architecturally clean but adds complexity (secrets management in CI, GH Actions runner access to Snowflake). Phase 2+ concern.
- **Multi-client generalization**: the scripts target GEP specifically. Refactoring to handle Fusion92 or other clients is a Phase 2+ concern once the GEP pattern is proven.
- **Share freshness monitoring**: deferred. Not hard, but it's ops infrastructure rather than feature-delivery. See §2.5 note.
- **Rollback automation**: implemented in v1 via `deploy.py --rollback` — snapshots WAREHOUSE_SOURCE view DDL before every TEST/PROD deploy and restores on demand. Full data rollback (physical WAREHOUSE tables) is not feasible without Snowflake Time Travel, which is a v2+ concern.
- **Historical backfill automation**: Eclipse configuration changes and CosmosDB registration (Phases 1–2 of [[gep-snowflake-pbi-deployment]]) require Eclipse access and remain manual.
- **Connector repo automation** *(future roadmap — v3)*: extend the workflow automation pattern (deploy, validate, /gep-feature-style skill) to the [[connector]] repo (Eclipse connector runtime, Docker-based, Prefect migration in progress). Connectors have a different deployment model (Docker / Prefect) so will need a separate design session. Designed to compose with the clients-repo automation rather than replace it — a ticket may touch both repos.

---

## See Also

- [[processes/distributed-workflow/active/client-workflow-automation]] — workstream tracker for this design
- [[concepts/patterns/sandbox-feature-delivery]] — the per-feature-schema sandbox pattern abstracted for reuse
- [[gep-snowflake-pbi-deployment]] — canonical GEP deployment runbook (read-only; this design extends it, does not replace it)
- [[flight-check]] — operational validation process (source material for `validate.py` universal checks)
- [[ticket-breakdown-to-ship]] — generic ticket lifecycle this automation integrates with
- [[GP-207]] — prod→test data share setup; the primitive that makes per-feature schemas viable
- [[GP-208]] — ticket where manual QA pain was acutely felt; validation suite design draws from its QA checklist
- [[snowflake-data-share-refresh]] — share freshness failure modes; context for the deferred monitoring candidate
- [[accumulating-source-tables]] — moving-target source behavior; drives the ≤1% validation tolerance in `validate.py`
- [[GEP]] — client entity page
