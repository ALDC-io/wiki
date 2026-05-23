---
tags: [process, orchestrator, prefect, production, plan, aldc-launchpad]
aliases: [Orchestrator Prod Readiness, Pipeline Hardening Plan]
sources: [orchestrator.md, GP-218, GP-219, GP-242, GP-244, GP-246]
created: 2026-05-22
updated: 2026-05-22
---

# Orchestrator Production Readiness Plan

**Goal:** Get the orchestrator pipeline engine to the point where it can safely deploy, validate, and promote connectors from QA → UAT → Prod with rollback capability and evidence capture at every gate.

**Current state:** Pipeline engine runs, sessions launch, DAG execution works. But the stage scripts are ~30% implemented (skeletons/TODOs), there's no rollback mechanism, no data validation, and no evidence capture. The UI shell exists but isn't wired to live backend state.

**Current location:** The orchestrator lives entirely in `aldc-launchpad` — it has NOT been migrated to `prefect-connectors`. See Phase 0 below for the migration decision.

**Scope:** Three core pipelines only: (1) credential exchange, (2) connector migration (Eclipse → Prefect), (3) new connector onboarding. Everything else (warehouse DDL, PBI/Superset, dbt, incident response, doc sync) is deferred until these three are production-proven.

**Related tickets:** GP-218 (work pools), GP-219 (Sellercloud migration), GP-242 (credentials), GP-244 (GHCR auth), GP-246 (testing protocol)

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
3. **New connector pipeline** — scaffold → implement → test → deploy

Everything else (warehouse DDL, PBI model changes, dbt, Cube, Superset, incident response, doc sync) stays as pipeline definitions but is not part of this hardening pass. It will be added incrementally once the core three pipelines are proven.

### Steps (Day 1)

1. Start the orchestrator locally (`python scripts/orchestrator.py`) — confirm it boots
2. Move orchestrator engine files to `prefect-connectors` (new directory, e.g. `orchestrator/`)
3. Verify imports, fix paths
4. Confirm the three core pipelines (credential, migration, new connector) still load
5. Strip or flag non-core pipeline types as `status: deferred`

**Estimated effort:** 2-4 hours (migration + verification).

---

## Phase A: Data Validation Layer (Priority 1 — blocks everything else)

**Why first:** You can't promote anything without proving the data is correct. Every downstream phase depends on this.

### A1. Implement `snowflake_ops.py`

**File:** `scripts/stage_scripts/snowflake_ops.py`

Functions needed:
- `compare_row_counts(source_db, target_db, tables)` — row count comparison with tolerance threshold (< 1% per GP-246 spec)
- `compare_aggregates(source_db, target_db, table, metrics)` — sum/avg/min/max on key numeric columns (revenue, spend, quantity)
- `compare_schemas(source_db, target_db, table)` — column names, types, nullability alignment
- `check_freshness(db, table, timestamp_col, max_age_hours)` — latest row timestamp vs now
- `sample_diff(source_db, target_db, table, key_cols, n=100)` — random sample row-by-row comparison
- `generate_parity_report(results) → dict` — structured JSON report for evidence capture

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
- `deploy_connector(connector_name, work_pool, env)` — register a Prefect deployment for a connector against the correct work pool (azure-aci-qa / azure-aci-uat / azure-aci-production)
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

## Phase C: Rollback Mechanism (Priority 3)

### C1. Deployment snapshots

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

### C2. Rollback function

`rollback_deployment(connector, env, snapshot_path)` — reads snapshot, restores deployment config, disables the bad deployment, triggers a verification run.

### C3. Rollback gate in pipeline

Add a "rollback-gate" stage to the `connector-promotion` pipeline after each promotion boundary. If parity check fails, the pipeline pauses and offers rollback using the pre-promotion snapshot.

**Estimated effort:** 2-3 hours total for C1-C3.

---

## Phase D: Evidence Capture & Audit Trail (Priority 4)

### D1. Pipeline evidence accumulator

Each pipeline run accumulates evidence in `platform/master/data/pipeline-evidence/{pipeline_id}/`:
- `parity-report.json` — from Phase A
- `deployment-snapshot-pre.json` — from Phase C
- `deployment-snapshot-post.json` — after promotion
- `flow-run-metadata.json` — Prefect run ID, duration, logs URL
- `gate-approvals.json` — who approved each gate, when, any notes

### D2. Jira comment generation

At pipeline completion (or failure), auto-generate a structured Jira comment summarizing:
- What was promoted, from where to where
- Parity results (pass/fail per table, key metric comparisons)
- Flow run ID and duration
- Rollback snapshot reference
- Any open issues

This replaces manual ticket commenting. The `jira_ops.py` stage script posts it.

### D3. Dashboard evidence viewer

Add an "Evidence" tab to the orchestrator dashboard session detail panel. Renders the accumulated evidence files as a structured timeline.

**Estimated effort:** 3-4 hours total for D1-D3.

---

## Phase E: Gate Wiring & Work Pool Validation (Priority 5)

### E1. Manual gate UI

Wire the merge-gate, uat-gate, and prod-gate pipeline stages to the orchestrator dashboard. When a pipeline hits a gate:
1. Pipeline pauses (already works)
2. Dashboard shows a gate approval card with context (parity results, deployment status)
3. Approver clicks Approve/Reject with optional notes
4. Pipeline resumes or aborts

### E2. Work pool health check

`gate_checks.verify_work_pool(pool_name)` — confirm the work pool exists, has at least 1 online worker, and isn't in maintenance mode. Run this before any deployment or promotion.

### E3. Credential validation

`gate_checks.verify_credentials(connector, env)` — attempt a lightweight auth check (e.g., Snowflake `SELECT 1`, API health endpoint) using the credentials that the connector will use. Fail fast before running a full flow.

**Estimated effort:** 3-4 hours total for E1-E3.

---

## Execution Order & Session Recommendations

| Day | Phase | What to boot | Ticket(s) to update |
|-----|-------|-------------|---------------------|
| Day 1 (tomorrow) | Phase 0 | Verify orchestrator boots + runs; decide migrate vs stay; migrate if Option A | GP-218 |
| Day 1 (tomorrow) | A1 + A2 | `snowflake_ops.py` — data validation layer | GP-246 (parity test suite now has live Snowflake backing) |
| Day 1-2 | B1 + B2 | `prefect_ops.py` + `promotion_ops.py` | GP-218 (promotion pipeline wired), GP-219 (can now deploy Sellercloud to QA) |
| Day 2 | B3 | Wire connector-promotion pipeline stages | GP-219 |
| Day 2-3 | C1-C3 | Rollback mechanism | GP-218, GP-219 |
| Day 3 | D1-D2 | Evidence capture + Jira auto-comments | All Prefect tickets |
| Day 3-4 | E1-E3 | Gate UI + health checks | GP-244 (GHCR verified as part of work pool check) |

**Model recommendation:** Sonnet for execution phases (A, B, C). Opus for D3 (dashboard evidence viewer — UI design judgment) and E1 (gate approval UX).

---

## First Session Boot Prompt (Day 1)

Start with:
```
/launchpad-phase0c
```

Then: "Read `wiki/processes/operations/orchestrator-production-readiness.md`. Start with Phase 0: migrate the orchestrator engine (orchestrator.py, pipelines.py, stage_scripts/) from aldc-launchpad into prefect-connectors. Verify it boots, strip non-core pipelines to `deferred`, confirm the three core pipelines load (credential exchange, connector migration, new connector). Then move to Phase A: implement `snowflake_ops.py` — data validation layer. Use existing Snowflake credentials from GP-248 (QA/UAT/Prod service accounts). Start with `compare_row_counts` and `compare_aggregates`, test against `QA_DG1_GEP_PREFECT` vs `PROD_DG1_GEP`."

---

## Definition of Done

The orchestrator is production-ready when:

1. **Sellercloud SQL connector** (GP-219) has been deployed to QA via the pipeline, validated with a parity report showing < 1% variance, promoted to UAT, re-validated, and promoted to Prod — all through the orchestrator
2. **Rollback** has been tested: intentionally deploy a bad config, confirm rollback restores the previous state
3. **Evidence** for the full QA → UAT → Prod journey is captured in JSON files and posted to the Jira ticket as a structured comment
4. **Gates** pause the pipeline and require explicit approval before promotion
5. **Work pool health** is validated before every deployment

When all 5 are demonstrated on a real connector (Sellercloud), the pattern is proven and can be applied to all remaining migrations.

---

## See Also

- [[orchestrator]] — tool page (architecture, bugs fixed, agent types)
- [[prefect-v3-patterns]] — Prefect deployment and testing patterns
- [[phase-0-prefect-foundation]] — original Prefect migration plan
- GP-218 — Work pool infrastructure
- GP-219 — Sellercloud migration (first real test of this pipeline)
- GP-246 — Testing protocol spec
