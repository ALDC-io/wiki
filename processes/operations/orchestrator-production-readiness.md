---
tags: [process, orchestrator, prefect, production, plan, aldc-launchpad, conductor]
aliases: [Orchestrator Prod Readiness, Pipeline Hardening Plan]
sources: [orchestrator.md, conductor, GP-218, GP-219, GP-242, GP-244, GP-246, GP-261]
created: 2026-05-22
updated: 2026-05-25
---

# Orchestrator Production Readiness Plan

**Goal:** Get the orchestrator pipeline engine to the point where it can safely deploy, validate, and promote connectors from QA → UAT → Prod with rollback capability and evidence capture at every gate.

**Current state:** Pipeline engine runs, sessions launch, DAG execution works. But the stage scripts are ~30% implemented (skeletons/TODOs), there's no rollback mechanism, no data validation, and no evidence capture. The UI shell exists but isn't wired to live backend state.

**Current location:** The orchestrator, credential exchange portal, and connector activation API have been migrated into `prefect-connectors` (Phase 0 DONE 2026-05-25, commit `946a6d3`). See Phase 0 below for details.

**Scope:** Three core pipelines only: (1) credential exchange, (2) connector migration (Eclipse → Prefect), (3) new connector onboarding. Everything else (warehouse DDL, PBI/Superset, dbt, incident response, doc sync) is deferred until these three are production-proven.

**Connector types:** The plan originally assumed all connectors are API → Python → Snowflake. GP-261 introduces a new type: **Snowflake-to-Snowflake** (Navira's Snowflake → ALDC's Snowflake). This is the first connector that reads from an external Snowflake account rather than a third-party API. The pattern will likely recur for other clients/partners. See "Snowflake-to-Snowflake Connector Variant" section below for the extensions this requires across Phases A, B, and E.

**Related tickets:** GP-218 (work pools), GP-219 (Sellercloud migration), GP-242 (credentials), GP-244 (GHCR auth), GP-246 (testing protocol), GP-261 (Navira Snowflake → ALDC ingestion)

---

## Phase 0: Orchestrator Migration Decision (Do First)

**Problem:** The orchestrator currently lives in `aldc-launchpad` (a monorepo for the ALDC platform). The intent was to migrate it into `prefect-connectors` (the Prefect v3 data-plane repo) so that pipeline orchestration, connector deployment, and connector code all live together. This migration has not happened yet.

**Current location (aldc-launchpad):**
- `scripts/orchestrator.py` (1,649 lines) — HTTP server, session management, context enrichment
- `scripts/pipelines.py` (1,173 lines) — pipeline DAG engine, stage execution
- `scripts/stage_scripts/` (7 files) — per-stage implementations (~30% complete)
- `platform/master/pages/orchestrator/index.html` (4,480 lines) — dashboard UI

**Target location (prefect-connectors):**
- Currently has zero orchestrator code
- Has `.deploy/` Azure Functions for connector-activation and credential exchange
- Has connector flows, base patterns, account configs

### Decision: Migrate to prefect-connectors first (DECIDED 2026-05-22)

Migrate the orchestrator engine into `prefect-connectors` so all hardening work lands in the right repo from the start. The orchestrator's production focus is credential exchange, connector migration, and new connector onboarding — these are all prefect-connectors concerns.

**What moves to prefect-connectors:**
- `scripts/orchestrator.py` — HTTP server, session management, context enrichment
- `scripts/pipelines.py` — pipeline DAG engine, stage execution
- `scripts/stage_scripts/` — per-stage implementations

**What stays in aldc-launchpad (for now):**
- `platform/master/pages/orchestrator/index.html` — dashboard UI (it's a platform SPA page; can call the orchestrator API cross-origin or be migrated later)

**What to strip / defer:**
The current orchestrator has broad ambitions (15 pipeline types, Zeus Chat, voice alerts, 5 AI agents). For production hardening, focus ONLY on:
1. **Credential exchange pipeline** — collect → validate → vault → Prefect block
2. **Connector migration pipeline** — implement → test → QA → UAT → Prod with parity checks
3. **New connector pipeline** — scaffold → implement → test → deploy (includes Snowflake-to-Snowflake variant for GP-261)

Everything else (warehouse DDL, PBI model changes, dbt, Cube, Superset, incident response, doc sync) stays as pipeline definitions but is not part of this hardening pass. It will be added incrementally once the core three pipelines are proven.

### Steps (Day 1) — DONE 2026-05-25

1. ~~Start the orchestrator locally — confirm it boots~~ ✓
2. ~~Move orchestrator engine files to `prefect-connectors/orchestrator/`~~ ✓ (12 files)
3. ~~Verify imports, fix paths~~ ✓ (split REPO_ROOT → CONNECTORS_ROOT + LAUNCHPAD_ROOT)
4. ~~Confirm the four core pipelines load~~ ✓ (connector-migration, credential-provision, data-parity-test, connector-promotion)
5. ~~Strip non-core pipeline types as `status: deferred`~~ ✓ (prefect-infra deferred)
6. ~~Move `api/connector-activation/` → `connectors/.deploy/connector-activation/`~~ ✓ (10 files)
7. ~~Move `api/credential-exchange/` → `connectors/.deploy/credential-exchange/`~~ ✓ (8 core files, design docs excluded)
8. ~~Update all cross-repo path references to internal~~ ✓ (`ACTIVATION_API_DIR` now points to `.deploy/`)

**Commit:** `946a6d3` in prefect-connectors (41 files, 7,794 lines). Run: `cd connectors && python -m orchestrator`

---

## Phase 0.5: Conductor Component Adoption (Do after Phase 0, before Phase A)

**Problem:** The orchestrator in `aldc-launchpad` is a monolithic pair of files (orchestrator.py: 1,934 lines, pipelines.py: 1,322 lines, dashboard: 4,479-line single HTML). Meanwhile, `repos/conductor` — a general-purpose AI product orchestrator extracted from the same patterns — has evolved several subsystems into cleaner, more modular, more production-ready forms. Migrating the orchestrator without adopting Conductor's improvements means rebuilding things Conductor already solved.

**Source repo:** `C:\Users\PaulRussell\repos\conductor`

### What to adopt from Conductor (file-by-file)

| Conductor file | Adopt as | What it replaces/adds | Effort |
|---|---|---|---|
| `engine/events.py` | `orchestrator/engine/events.py` | Replaces 2–5s polling with SSE pub/sub. In-memory ring buffer (500 events), per-connection subscriber queues, 25s keepalive pings. | 1h (adopt + wire into server) |
| `engine/audit.py` | `orchestrator/engine/audit.py` | Adds append-only per-pipeline audit trail (stage start/complete/fail, cost, tokens, gate approvals, output summaries). **This is Phase D1 delivered for free.** | 30min (adopt + wire callbacks) |
| `engine/validation.py` | `orchestrator/engine/validation.py` | Adds automated quality gate checks (pytest, file_exists, grep) against worktrees. Maps results to `quality_gates` dict. Currently the orchestrator only has manual UI toggles. | 1h (adopt + integrate with stage completion) |
| `engine/work_guard.py` | `orchestrator/engine/work_guard.py` | Adds repo safety: lock file + heartbeat + dirty-tree gate + policy JSON. Critical when multiple pipelines could run concurrently against prefect-connectors. | 30min (adopt + add policy config) |
| `engine/memory.py` | `orchestrator/engine/memory.py` | Adds persistent per-project memory (decisions, learnings, patterns, incidents) with evidence links. Replaces the orchestrator's ephemeral "prior session learnings" passed in prompts. | 30min (adopt, wire to session completion) |
| `engine/sessions.py` | Refactor guide for `orchestrator.py` | Conductor extracted session lifecycle into its own module. Use as a template to split the orchestrator's session logic (~800 lines) out of the monolith. Not a direct copy — the orchestrator's context enrichment is richer. | 1-2h (refactor, not drop-in) |
| `engine/pipelines.py` | Refactor guide for `pipelines.py` | Conductor's DAG engine is cleaner but the orchestrator's pipeline definitions are domain-specific and must be preserved. Adopt Conductor's YAML template pattern for pipeline definitions; keep the orchestrator's 5 pipeline types as YAML. | 1-2h (extract definitions to YAML) |
| `engine/stage_scripts/git_ops.py` | `orchestrator/engine/stage_scripts/git_ops.py` | Adds `snapshot_branch`, `rollback_to_snapshot`, `commit_changes`, `create_pr`. **This is Phase C1–C2 partially delivered.** The orchestrator's `promotion_ops.rollback_deployment` handles Prefect rollback; this handles git rollback. | 30min (adopt directly) |
| `engine/onboarding.py` | Defer (evaluate after core pipelines proven) | AI conversational project wizard. Could power "new connector onboarding" scaffold step, but not needed for the three core pipelines. | — |
| `engine/bootstrap.py` | Defer (evaluate after core pipelines proven) | Phase dependency engine. Could track connector migration fleet status, but over-engineering for now. | — |

### Dashboard restructuring

The orchestrator dashboard is a single 4,479-line HTML file. Conductor splits its dashboard into 14 separate page files loaded into a SPA shell. Adopt this pattern:

| New file | Source content |
|---|---|
| `dashboard/index.html` | SPA shell + router + SSE status bar (from Conductor) |
| `dashboard/styles/base.css` | Design system CSS custom properties (from Conductor, re-themed to orchestrator's glassmorphism) |
| `dashboard/pages/sessions.html` | Session kanban board + slideout (from orchestrator `index.html` lines ~1200–2800) |
| `dashboard/pages/pipelines.html` | Pipeline cards + DAG renderer (from orchestrator `index.html` lines ~2800–3800) |
| `dashboard/pages/deploy.html` | Deploy board / environment matrix (from orchestrator `index.html` lines ~3800–4100) |
| `dashboard/pages/zeus-chat.html` | Zeus Chat panel (from orchestrator, keep TTS) |

**Key UI upgrade:** Replace the orchestrator's polling loops with SSE event listeners using Conductor's `events.py` backend. This eliminates the 2s/5s polling intervals and gives instant UI updates.

### Agent definitions

Move from hardcoded Python dict to Conductor's markdown+YAML frontmatter pattern:

```
orchestrator/agents/
├── zeus-review.md      # Operational status brief + gate recommendations
├── code-review.md      # 4-check security/correctness protocol
├── user-testing.md     # 6-step flight check (Snowflake, PBI, data freshness)
├── deploy.md           # 11-phase GEP deployment runbook
└── refactor.md         # DRY/naming/pattern adherence analysis
```

### What NOT to adopt from Conductor

- **`engine/server.py` routing style** — Conductor uses regex route matching on `SimpleHTTPRequestHandler`. The orchestrator does the same thing. Neither is great, but swapping one for the other gains nothing. If we ever need a real framework, both should move to FastAPI.
- **Conductor's `standard-phase.yaml` pipeline** — too generic. Keep the orchestrator's 5 domain-specific pipeline types.
- **Conductor's project/phase model** — the orchestrator doesn't manage "projects" and "phases" in Conductor's sense. It manages connectors, environments, and promotion gates.
- **Conductor's sub-projects** (neurospect, groovenet, labs-institute) — domain-specific, not relevant.

### Steps

1. ~~After Phase 0 migration lands, create the `orchestrator/engine/` module structure~~ ✓
2. ~~Copy Conductor modules directly: `events.py`, `audit.py`, `validation.py`, `work_guard.py`, `memory.py`, `git_ops.py`~~ ✓
3. ~~Wire `events.py` into the server (emit events on session/pipeline state changes, add `/api/events/stream` SSE endpoint)~~ ✓
4. ~~Wire `audit.py` into pipeline stage callbacks (stage start/complete/fail → audit append)~~ ✓
5. ~~Wire `validation.py` into session completion (auto-run checks, populate quality gates)~~ ✓ (configured; checks run on demand)
6. ~~Add `config/work-guard-policy.json` with prefect-connectors-specific policy~~ ✓
7. ~~Split the monolithic dashboard HTML into separate page files~~ ✓ (4,479 lines → 7 files)
8. ~~Replace polling with SSE listeners in each dashboard page~~ ✓ (removed 2s/5s setInterval, replaced with EventSource)
9. ~~Extract pipeline type definitions from Python to YAML templates~~ ✓ (5 YAML files, 634 lines)
10. ~~Extract agent definitions to markdown files~~ ✓ (5 files, 393 lines)

**Commits:** `b13ed0c` in prefect-connectors (steps 1-6: 11 files, 1,357 lines). Steps 7-10 DONE 2026-05-25.

**Step 7-10 details (2026-05-25):**
- **Dashboard split** (step 7): `platform/master/pages/orchestrator/index.html` (807 lines — SPA shell with router, SSE status bar, inbox sidebar, Zeus Chat panel, modals), `styles/orchestrator.css` (1,500 lines), `scripts/shared.js` (339 lines — state management, utilities, SSE connection, pipeline helpers), `pages/pipelines.html` (137 lines — pipeline cards + DAG + gate actions), `pages/sessions.html` (266 lines — session kanban + slideout), `pages/deploy.html` (98 lines — environment matrix QA/UAT/Prod), `pages/zeus-chat.html` (64 lines — agent dispatch panel).
- **SSE replacement** (step 8): Removed `setInterval` polling (2s sessions, 5s pipelines), replaced with `EventSource` to `/api/events/stream`. Auto-reconnect with 3s backoff.
- **Pipeline YAML extraction** (step 9): 5 YAML files at `connectors/orchestrator/pipelines/*.yaml` — connector-migration, credential-provision, data-parity-test, connector-promotion, prefect-infra. `pipelines.py` updated with YAML loader.
- **Agent markdown extraction** (step 10): 5 files at `connectors/orchestrator/agents/*.md` with YAML frontmatter — zeus-review, code-review, user-testing, deploy, refactor. `server.py` updated with agent loader + `/api/agents` and `/api/agents/run` endpoints.

**Estimated effort:** ~~6-8 hours total~~ Steps 1-6 done in ~1 hour. Steps 7-10 done 2026-05-25. Phase 0.5 complete.

**Impact on downstream phases:**
- **Phase C** (Rollback) — `git_ops.py` provides git-level rollback out of the box. Still need Prefect deployment rollback from the orchestrator's `promotion_ops.py`, but the git side is done.
- **Phase D** (Evidence Capture) — `audit.py` delivers D1 (pipeline evidence accumulator). D2 (Jira comments) and D3 (dashboard viewer) still needed but the data layer is done.
- **Phase E1** (Gate UI) — SSE + page separation makes the gate approval card implementation cleaner and faster.

**Net effect:** ~4-6 hours saved in Phases C, D, and E by adopting proven Conductor modules instead of building from scratch.

---

## Phase A: Data Validation Layer (Priority 1 — blocks everything else)

**Why first:** You can't promote anything without proving the data is correct. Every downstream phase depends on this.

### A1. Implement `snowflake_ops.py`

**File:** `scripts/stage_scripts/snowflake_ops.py`

Functions needed:
- `compare_row_counts(source_db, target_db, tables, source_connection=None)` — row count comparison with tolerance threshold (< 1% per GP-246 spec). Optional `source_connection` param for cross-account comparison (GP-261)
- `compare_aggregates(source_db, target_db, table, metrics, source_connection=None)` — sum/avg/min/max on key numeric columns (revenue, spend, quantity)
- `compare_schemas(source_db, target_db, table, schema_contract=None)` — column names, types, nullability alignment. Optional `schema_contract` param validates against an agreed schema definition (GP-261)
- `check_freshness(db, table, timestamp_col, max_age_hours)` — latest row timestamp vs now
- `sample_diff(source_db, target_db, table, key_cols, n=100, source_connection=None)` — random sample row-by-row comparison
- `generate_parity_report(results) → dict` — structured JSON report for evidence capture

**Cross-account support (GP-261):** The `source_connection` parameter defaults to `None` (same-account comparison for existing API connectors). For Snowflake-to-Snowflake connectors, pass a separate Snowflake connection to query the external account. This allows comparing Navira's source views against ALDC's ingested tables across accounts.

**Data sources:** Connect via Snowflake Python connector using the existing per-environment credentials (QA/UAT/Prod service accounts from GP-248).

**Deliverable:** Running `snowflake_ops.compare_all(source="PROD_DG1_GEP", target="QA_DG1_GEP_PREFECT", tables=[...])` produces a JSON parity report with pass/fail per table.

**Estimated effort:** 3-4 hours (the SQL is straightforward; the wiring is the work).

### A2. Parity report persistence

Store parity reports in `platform/master/data/parity-reports/{pipeline_id}_{stage}_{timestamp}.json`. The orchestrator dashboard can render these later.

**Estimated effort:** 1 hour.

---

## Phase B: Deployment & Promotion Pipeline (Priority 2)

### B1. Complete `prefect_ops.py`

**File:** `scripts/stage_scripts/prefect_ops.py`

Functions needed:
- `deploy_connector(connector_name, work_pool, env, blocks=None)` — register a Prefect deployment for a connector against the correct work pool (azure-aci-qa / azure-aci-uat / azure-aci-production). Optional `blocks` param supports registering multiple Prefect blocks per connector (GP-261 Snowflake-to-Snowflake connectors need both a reader block for the external account and the standard ALDC writer block)
- `trigger_and_wait(deployment_name, timeout_minutes=30)` — trigger a flow run, poll until COMPLETED/FAILED/CANCELLED, return run metadata
- `get_deployment_status(deployment_name)` — current state, last run, schedule status
- `disable_schedule(deployment_name)` / `enable_schedule(deployment_name)` — for safe promotion windows

**Dependencies:** Prefect Python client (`prefect`), environment-specific API URLs and keys (already in Key Vault per GP-218).

**Estimated effort:** 2-3 hours.

### B2. Complete `promotion_ops.py`

**File:** `scripts/stage_scripts/promotion_ops.py`

Functions needed:
- `validate_source_env(connector, source_env)` — confirm deployment exists, last run COMPLETED, schedule active
- `snapshot_deployment(connector, env) → dict` — capture current deployment config (work pool, schedule, parameters, image tag) for rollback
- `promote(connector, source_env, target_env)` — create/update deployment in target env using source env's config + target env's work pool/credentials
- `verify_promotion(connector, target_env)` — trigger a run in target, confirm COMPLETED, run parity check against source

**Critical:** `snapshot_deployment()` is what enables rollback (Phase C). Must be called before every promotion.

**Estimated effort:** 2-3 hours.

### B3. Wire the `connector-promotion` pipeline (14 stages)

The pipeline template exists in `pipelines.py` but stage prompts reference functions that don't exist yet. After B1 and B2, update the stage scripts to call the real functions instead of printing TODOs.

**Estimated effort:** 1-2 hours (mostly wiring, not new logic).

---

## Phase C: Rollback Mechanism (Priority 3) — DONE 2026-05-25

### C1. Deployment snapshots ✓

Before any promotion, `snapshot_deployment()` writes to `platform/master/data/deployment-snapshots/{connector}_{env}_{timestamp}.json`:
```json
{
  "connector": "exchange_rates",
  "env": "prod",
  "timestamp": "2026-05-23T10:00:00Z",
  "work_pool": "azure-aci-production",
  "image_tag": "main",
  "schedule": { "cron": "0 6 * * *" },
  "parameters": { ... },
  "prefect_deployment_id": "abc-123",
  "snapshot_reason": "pre-promotion from UAT"
}
```

### C2. Rollback function ✓ (2026-05-25)

`rollback_to_snapshot(ctx)` in `promotion_ops.py` — reads snapshot JSON (from explicit path, prior stage results, or auto-discovers latest for connector/env via `_find_latest_snapshot`), restores full deployment config via Prefect API (work pool, work queue, image, entrypoint, tags, parameters), disables schedule for safety. The original `rollback_deployment()` (schedule-only disable) is preserved for simpler rollback scenarios.

### C3. Rollback gate in pipeline ✓ (2026-05-25)

Two rollback-gate stages added to `connector-promotion.yaml`: `uat-rollback-gate` (after `uat-parity`, before `uat-gate`) and `prod-rollback-gate` (after `prod-robustness`, before `prod-gate`). Pipeline now has 19 stages (was 16).

**Design:** Parity/robustness stages use gated wrappers (`run_parity_gated`, `run_robustness_gated`) that always return `success=True` with the actual pass/fail in `data.check_passed`. This ensures the pipeline engine dispatches the rollback gate regardless of parity outcome. `evaluate_rollback_gate` checks `check_passed`: if passed, auto-advances; if failed, restores the pre-promotion snapshot and reports the rollback. Always returns `success=True` so the manual approval gate fires for operator review.

**Commits:** `cf34ef4` (prefect-connectors), `e998a54` (aldc-launchpad submodule update).

---

## Phase D: Evidence Capture & Audit Trail (Priority 4) — DONE 2026-05-25

### D1. Pipeline evidence accumulator ✓ (Phase 0.5)

Adopted from Conductor's `engine/audit.py`. Append-only per-pipeline audit trail with events for stage start/complete/fail, gate approvals, validation runs, pipeline completion. Stored at `DATA_DIR/audits/{pid}.json`.

### D2. Jira comment generation ✓ (2026-05-25)

`post_pipeline_evidence(ctx)` in `jira_ops.py` — auto-generates a structured Atlassian Document Format (ADF) comment at pipeline completion. Sections: heading, status panel (success/warning color), stage results (bullet list), flow runs, rollback snapshots, rollback events (error panel), issues, timestamp. ADF helper functions (`_adf_heading`, `_adf_paragraph`, `_adf_text`, `_adf_bullet_list`, `_adf_panel`) for clean document construction. Added as `post-evidence` stage in the pipeline between `enable-schedule` and `jira-done`.

### D3. Dashboard evidence viewer ✓ (2026-05-25)

"Evidence" tab added to the orchestrator dashboard session detail slideout. Appears only for pipeline-linked sessions. Fetches audit trail from `../../data/audits/{pipeline_id}.json`. Renders: summary cards (completed/failed/gates counts + total cost), vertical timeline with color-coded event cards (started=cyan, completed=green, failed=red, gates=amber), detail rows per event (duration, cost, tokens, files changed, validation results, errors).

**Commits:** `cf34ef4` (prefect-connectors — promotion_ops + jira_ops + pipeline YAML), `e998a54` (aldc-launchpad — sessions.html Evidence tab + submodule pointer).

---

## Phase E: Gate Wiring & Work Pool Validation (Priority 5) — DONE 2026-05-25

### E1. Manual gate UI ✓ (2026-05-25)

Gate approval cards in the pipeline card expansion now show full **Pipeline Context**: rollback gate status (green/red/amber panels), parity/robustness results, flow run metadata (run ID, state, duration), deployment snapshot references. Notes textarea for operator comments (persisted in audit trail). **Approve** and **Reject** buttons — approve calls `/api/pipelines/{id}/advance`, reject calls new `/api/pipelines/{id}/reject` endpoint. `reject_stage()` in `pipelines.py` marks the gate as failed and records `gate_rejected` in audit trail.

SSE: `_dispatch_gate_stage` now emits `pipeline.gate_waiting` event with pipeline_id, stage_name, prompt, ticket_id — dashboard reacts instantly via existing `orch-event` listener.

### E2. Work pool health check ✓ (2026-05-25)

`gate_checks.verify_work_pool(pool_name)` queries Prefect API: `GET /work_pools/{name}` for existence and status (rejects PAUSED), `POST /work_pools/{name}/workers/filter` for online workers. ACI pools pass with 0 workers (workers spin up on demand). Wired as inline pre-flight in `promote_deployment()` — promotion fails immediately if pool is unhealthy, before creating the deployment.

### E3. Credential validation ✓ (2026-05-25)

`gate_checks.verify_credentials(ctx)` — pipeline stage wrapper. `_verify_snowflake_target(env)` connects to ALDC Snowflake (og35375/wj66376), runs `SELECT 1`. `_verify_snowflake_source(account, schema_contract)` for GP-261: connects with key-pair auth, runs `SELECT 1`, then verifies `SELECT COUNT(*)` on each contracted view — catches access revocation on specific views while service account still works.

Added `preflight-uat-creds` and `preflight-prod-creds` stages to the pipeline (21 stages total, was 19).

**Commits:** `006ff0f` (prefect-connectors), `505a375` (aldc-launchpad submodule update + pipelines.html).

---

## Snowflake-to-Snowflake Connector Variant (GP-261)

GP-261 introduces the first Snowflake-to-Snowflake connector: Navira's Snowflake → ALDC's Snowflake. This is architecturally different from API connectors and requires extensions across the plan.

**Architecture decision (2026-05-25):** After evaluating three options (Direct Data Share, Share + Local Materialization, Prefect ETL Pipeline), **Prefect ETL Pipeline** was chosen. Rationale:
- ALDC's own documented share failure modes (4 grant drops, 42-day frozen share, 14-hour outage) make shares too fragile
- Cross-region/cross-cloud connectivity is handled implicitly by Prefect (Navira's region unconfirmed — possibly AWS us-east-1 vs ALDC's Azure Canada Central)
- Fits the existing connector architecture — just another Prefect flow
- Full analysis: `C:\Users\PaulRussell\.claude\plans\whimsical-honking-clarke.md`
- Email sent to Justin Shuster (Navira) 2026-05-25 with the recommendation

### What makes Snowflake-to-Snowflake different

| Aspect | API Connector | Snowflake-to-Snowflake |
|---|---|---|
| Source | Third-party REST API | External Snowflake account |
| Auth | OAuth / API keys | Key-pair auth (RSA) |
| Prefect blocks | 1 (ALDC writer) | 2 (external reader + ALDC writer) |
| Validation | API response count vs table count | Cross-account row count, schema, aggregate comparison |
| Schema contract | Discovered from API response | Agreed with partner, tracked in contract file |

### Schema contract tracking

Unlike API connectors where the schema is defined by the API response, Snowflake-to-Snowflake connectors have an agreed schema contract. Track this per connector:

```json
// e.g., connectors/navira/schema_contract.json
{
  "source_account": "GEP-NAVIRA",
  "views": [
    {
      "name": "SCHEMA.VIEW_NAME",
      "columns": ["COL_A", "COL_B", "COL_C"],
      "agreed_date": "2026-05-25"
    }
  ]
}
```

Phase A's `compare_schemas` validates ingested data against this contract, catching drift on both sides.

### New connector pipeline — Snowflake-to-Snowflake scaffold

When pipeline 3 (new connector) detects a Snowflake-to-Snowflake type, the scaffold step should generate:
1. A flow template with dual Snowflake connections (reader + writer)
2. A `schema_contract.json` template
3. Key Vault secret entries for the external account's private key
4. Two Prefect blocks (reader + writer) instead of one

### Extensibility

Adding new views from Navira in the future:
1. Navira grants SELECT on the new view to their existing read-only role (one SQL statement)
2. ALDC adds the view to the flow config + `schema_contract.json`
3. Redeploy the flow via the standard QA→UAT→Prod promotion pipeline

No share renegotiation, no risk to existing data flows. The service account and key-pair don't change.

### Blocked until Justin responds

- Navira's Snowflake account locator, cloud, and region
- List of views and their schemas
- Service account credentials (key-pair)
- Preferred refresh frequency

---

## Execution Order & Session Recommendations

| Day | Phase | What to boot | Ticket(s) to update |
|-----|-------|-------------|---------------------|
| Day 1 | Phase 0 ✓ | ~~Migrate orchestrator engine from aldc-launchpad into prefect-connectors.~~ DONE 2026-05-25 (`946a6d3`). Also migrated connector-activation + credential-exchange APIs into `.deploy/`. | GP-218 |
| Day 1 | Phase 0.5 (steps 1-6) ✓ | ~~Adopt Conductor engine modules: `events.py`, `audit.py`, `validation.py`, `work_guard.py`, `memory.py`, `git_ops.py`. Wire SSE + audit callbacks.~~ DONE 2026-05-25 (`b13ed0c`). | GP-218 |
| Day 1-2 | Phase 0.5 (steps 7-10) ✓ | ~~Split dashboard HTML into pages, replace polling with SSE, extract pipeline YAML templates + agent markdown files.~~ DONE 2026-05-25. Dashboard 4,479→7 files, SSE replaces polling, 5 pipeline YAMLs (634 lines), 5 agent MDs (393 lines). | GP-218 |
| Day 2 | A1 + A2 | `snowflake_ops.py` — data validation layer | GP-246 |
| Day 2-3 | B1 + B2 | `prefect_ops.py` + `promotion_ops.py` | GP-218, GP-219 |
| Day 3 | B3 | Wire connector-promotion pipeline stages | GP-219 |
| Day 3 | C1-C3 ✓ | ~~Rollback mechanism~~ DONE 2026-05-25. C2: `rollback_to_snapshot` reads snapshot JSON, restores deployment config. C3: rollback-gate stages (19 stages, gated parity wrappers). Commits `cf34ef4` + `e998a54`. | GP-218, GP-219 |
| Day 3-4 | D1-D3 ✓ | ~~Evidence capture~~ DONE 2026-05-25. D2: `post_pipeline_evidence` generates structured ADF Jira comments. D3: Evidence tab in session slideout (vertical timeline, summary cards). | All Prefect tickets |
| Day 4 | E1-E3 ✓ | ~~Gate UI + health checks~~ DONE 2026-05-25. E1: gate approval cards with context panels, notes, approve/reject + SSE `gate_waiting` event + `/api/pipelines/{id}/reject`. E2: `verify_work_pool` pre-flight in `promote_deployment`. E3: `verify_credentials` + `preflight-*-creds` stages (21 stages total). Commits `006ff0f` + `505a375`. | GP-244 |
| After Sellercloud proven | GP-261 | Build Navira Snowflake-to-Snowflake flow. Blocked on Justin's response. | GP-261 |

**Model recommendation:** Opus for Phase 0.5 (architectural merge decisions, dashboard restructuring). Sonnet for execution phases (A, B, C). Opus for D3 (dashboard evidence viewer) and E1 (gate approval UX).

---

## First Session Boot Prompt (Day 1)

Start with:
```
/launchpad-phase0c
```

Then: "Read `wiki/processes/operations/orchestrator-production-readiness.md`. Start with Phase 0: migrate the orchestrator engine (orchestrator.py, pipelines.py, stage_scripts/) from aldc-launchpad into prefect-connectors. Verify it boots, strip non-core pipelines to `deferred`, confirm the three core pipelines load (credential exchange, connector migration, new connector). Then move to Phase 0.5: adopt Conductor modules from `repos/conductor/engine/` — copy `events.py`, `audit.py`, `validation.py`, `work_guard.py`, `memory.py`, `git_ops.py` into `orchestrator/engine/`. Wire SSE into the server, wire audit into pipeline callbacks. Split the monolithic dashboard HTML into separate page files per the plan."

### Second Session Boot Prompt (Day 2)

"Read `wiki/processes/operations/orchestrator-production-readiness.md`. Phase 0.5 dashboard restructuring should be complete. Move to Phase A: implement `snowflake_ops.py` — data validation layer. Use existing Snowflake credentials from GP-248 (QA/UAT/Prod service accounts). Start with `compare_row_counts` and `compare_aggregates`, test against `QA_DG1_GEP_PREFECT` vs `PROD_DG1_GEP`."

---

## Definition of Done

The orchestrator is production-ready when:

1. **Sellercloud SQL connector** (GP-219) has been deployed to QA via the pipeline, validated with a parity report showing < 1% variance, promoted to UAT, re-validated, and promoted to Prod — all through the orchestrator
2. **Rollback** has been tested: intentionally deploy a bad config, confirm rollback restores the previous state
3. **Evidence** for the full QA → UAT → Prod journey is captured in JSON files and posted to the Jira ticket as a structured comment
4. **Gates** pause the pipeline and require explicit approval before promotion
5. **Work pool health** is validated before every deployment

When all 5 are demonstrated on a real connector (Sellercloud), the pattern is proven and can be applied to all remaining migrations.

6. **Navira Snowflake-to-Snowflake connector** (GP-261) has been deployed through the same pipeline, validating that the pattern generalizes beyond API connectors to cross-account Snowflake ingestion

---

## See Also

- [[orchestrator]] — tool page (architecture, bugs fixed, agent types)
- [[conductor]] — general-purpose AI product orchestrator (source for engine modules adopted in Phase 0.5)
- [[prefect-v3-patterns]] — Prefect deployment and testing patterns
- [[phase-0-prefect-foundation]] — original Prefect migration plan
- GP-218 — Work pool infrastructure
- GP-219 — Sellercloud migration (first real test of this pipeline)
- GP-246 — Testing protocol spec
- GP-261 — Navira Snowflake → ALDC ingestion (first Snowflake-to-Snowflake connector)
- [[GP-261]] — Architecture decision: Prefect ETL Pipeline over Direct Share / Hybrid
