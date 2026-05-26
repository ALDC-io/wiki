---
tags: [launchpad, connectors, framework, deployment, complete]
created: 2026-05-13
updated: 2026-05-25
deliverables_built: 2026-05-13
deliverables_complete: 2026-05-13
deploy_ux_polished: 2026-05-14
---

# Phase 0C: Connector Framework & Live Deployment

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase0c.md` → `/launchpad-phase0c`
**Status:** Complete
**Effort:** 1 day
**Demo target:** Tomorrow — deploy a connector live from the Launchpad dashboard

## Goal

Analyze legacy connector code (prefect-connectors + core_api), create a migration catalog, standardize the connector creation/deployment pattern, and build a UI-driven deployment pipeline. Enable fast migration of all non-priority connectors and live demo of end-to-end deployment.

## Motivation

- prefect-connectors mixes framework code with per-connector implementations
- core_api patterns are not well-designed — extract useful bits, leave the rest
- Navira has 20+ connectors to build; standardizing the framework accelerates all of them
- Demo impact: showing credential tracking + live connector deployment = full pipeline story

## Deliverables

1. `migrations/connectors/catalog.json` — every legacy connector cataloged with auth, schema, schedule, migration status
2. Connector template/generator — standardized creation pattern
3. Platform UI deploy flow — button to trigger connector deployment from dashboard
4. Live deployment pipeline — UI → Prefect deployment → data lands

## Key Decisions

- 2026-05-13 — Run from aldc-launchpad repo (submodule access to prefect-connectors, UI in platform/master)
- 2026-05-13 — core_api is read-only reference, not modified
- 2026-05-13 — Amazon Ads US is the demo candidate (already provisioned, known-good)

## Session Log

### 2026-05-25 — Phase E: gate approval UI, work pool health, credential pre-flight

- did: Implemented Phase E per [[orchestrator-production-readiness]]. E1: gate approval cards with context panels (rollback status, parity, flow runs, snapshots), notes textarea, Approve/Reject buttons, SSE `gate_waiting` event, `/api/pipelines/{id}/reject` endpoint. E2: `verify_work_pool` pre-flight in `promote_deployment`. E3: `verify_credentials` + `preflight-*-creds` pipeline stages (21 stages total).
- result: All orchestrator hardening phases complete (0, 0.5, C, D, E). Ready for Sellercloud E2E test.
- commits: `006ff0f` (prefect-connectors), `505a375` (aldc-launchpad)
- next: Test Definition of Done on Sellercloud (GP-219).

### 2026-05-25 — Phases C + D: rollback mechanism + evidence capture

- did: Implemented orchestrator hardening Phases C (rollback) and D (evidence) per [[orchestrator-production-readiness]]. C2: `rollback_to_snapshot` in `promotion_ops.py` — reads snapshot JSON, restores deployment config via Prefect API. C3: rollback-gate stages in `connector-promotion.yaml` (19 stages total) with gated parity/robustness wrappers. D2: `post_pipeline_evidence` in `jira_ops.py` — structured ADF Jira comments. D3: Evidence tab in session slideout — vertical timeline with summary cards.
- result: Pipeline hardening Phases 0, 0.5, A, B, C, D all complete. Only Phase E (gate UI + health checks) remains.
- commits: `cf34ef4` (prefect-connectors), `e998a54` (aldc-launchpad)
- next: Phase E (gate approval UI, work pool health, credential validation) or Sellercloud E2E test.

### 2026-05-25 — Phase 0.5 steps 7-10: Dashboard split + SSE + YAML pipelines + agent markdown

- did: Completed Phase 0.5 steps 7-10 per [[orchestrator-production-readiness]] plan. (1) **Split monolithic dashboard HTML** (4,479 lines → 7 files): `index.html` (807 lines — SPA shell with router, SSE status bar, inbox sidebar, Zeus Chat panel, modals), `styles/orchestrator.css` (1,500 lines — extracted CSS), `scripts/shared.js` (339 lines — state management, utilities, SSE connection, pipeline helpers), `pages/pipelines.html` (137 lines — pipeline cards + DAG + gate actions), `pages/sessions.html` (266 lines — session kanban + slideout), `pages/deploy.html` (98 lines — environment matrix QA/UAT/Prod), `pages/zeus-chat.html` (64 lines — agent dispatch panel). (2) **Replaced polling with SSE**: removed `setInterval` polling (2s sessions, 5s pipelines), replaced with `EventSource` to `/api/events/stream`, auto-reconnect with 3s backoff. (3) **Extracted pipeline definitions to YAML** (5 files, 634 lines): `connectors/orchestrator/pipelines/*.yaml` for connector-migration, credential-provision, data-parity-test, connector-promotion, prefect-infra. Updated `pipelines.py` with YAML loader. (4) **Extracted agent definitions to markdown** (5 files, 393 lines): `connectors/orchestrator/agents/*.md` with YAML frontmatter for zeus-review, code-review, user-testing, deploy, refactor. Updated `server.py` with agent loader + `/api/agents` and `/api/agents/run` endpoints.
- result: Phase 0.5 fully complete. All Conductor component adoption steps (1-10) done. Dashboard is now modular (7 files vs 1 monolith), SSE replaces polling for instant UI updates, pipeline definitions are declarative YAML, agent definitions are human-readable markdown.
- decided: Dashboard pages loaded by SPA router into shell container. SSE auto-reconnect uses 3s backoff (matches Conductor's `events.py` keepalive at 25s). Pipeline YAML templates use the same stage schema as the Python definitions. Agent markdown uses YAML frontmatter for metadata (name, type, capabilities) with markdown body for the system prompt.
- impact: Phase 0.5 complete. Ready for Phase A (data validation layer). SSE + page separation accelerates Phase E1 (gate approval UX).
- next: Phase A — implement `snowflake_ops.py` data validation layer (compare_row_counts, compare_aggregates, compare_schemas, check_freshness, sample_diff).

### 2026-05-25 — Phase 0.5: Conductor engine modules adopted into orchestrator

- did: Adopted 6 production-ready modules from `repos/conductor/engine/` into `connectors/orchestrator/engine/` per the [[orchestrator-production-readiness]] plan (Phase 0.5, steps 1-5). Created `orchestrator/engine/` package with: `events.py` (SSE pub/sub, 500-event ring buffer, 25s keepalive), `audit.py` (append-only per-pipeline audit trail), `validation.py` (automated quality gate checks: pytest, file_exists, grep), `work_guard.py` (repo lock + heartbeat + dirty-tree gate), `memory.py` (per-pipeline persistent memory store), `stage_scripts/git_ops.py` (branch snapshot, rollback, commit, PR creation). All imports adapted from `from engine import` → `from orchestrator.engine import`. `work_guard.py` paths adapted from Conductor's `REPO_ROOT` → orchestrator's `CONNECTORS_ROOT`. `memory.py` uses `scope` parameter (client code or pipeline ID) instead of Conductor's `project_slug`. `audit.py` reads session output from orchestrator's `SESSIONS_DATA_DIR`. `git_ops.py` adapted `task_id/project_slug` → `ticket_id/client_code`. Created `config/work-guard-policy.json` (auto-recover stale locks, no dirty-tree block). Wired `server.py`: added `/api/events/stream` SSE endpoint, `/api/events` history, `/api/events/stats`, `/api/work-guard` status, `/api/pipelines/{id}/audit`. Event emission on session start/complete/cancel, pipeline create/advance. All engine modules initialized in `main()`, shutdown in `_shutdown()`. Wired `pipelines.py`: audit recording on stage dispatch/complete/fail, gate approval audit, pipeline completion events.
- result: All 6 modules import and initialize correctly. Full boot simulation passed: events emit and subscribe, audit writes to disk, work_guard reports safe_to_run=True, memory configures storage dirs. Commit `b13ed0c` in prefect-connectors (11 files, 1,357 lines). Pushed to origin/main.
- decided: `blockOnDirtyWorkingTree: false` in work-guard policy because prefect-connectors often has local-only config files. `staleLockBehavior: auto-recover` since pipelines run unattended. Lock file location: `.orchestrator/runtime/session-lock.json` (not `.conductor/`).
- impact: Phase C (Rollback) — `git_ops.py` delivers git-level rollback out of the box. Phase D (Evidence) — `audit.py` delivers D1 pipeline evidence accumulator. Phase E (Gate UI) — SSE + events make gate approval cards instant-update.
- next: Phase 0.5 steps 6-10 — split monolithic dashboard HTML (4,479 lines) into separate page files, replace polling with SSE listeners, extract pipeline definitions from Python to YAML templates, extract agent definitions to markdown files.

### 2026-05-25 — Phase 0 orchestrator migration: engine + APIs into prefect-connectors

- did: Migrated the orchestrator engine, credential exchange portal, and connector activation API from `aldc-launchpad` into `prefect-connectors` per the [[orchestrator-production-readiness]] plan (Phase 0). Created `orchestrator/` package (12 files: HTTP server, DAG pipeline engine, 6 stage scripts, paths module, entry point). Moved `api/connector-activation/` (10 endpoints, 8 service modules) and `api/credential-exchange/` (OAuth providers, HMAC tokens, Key Vault, Prefect blocks) into `connectors/.deploy/`. All imports updated from `scripts.stage_scripts.*` → `orchestrator.stage_scripts.*`. Split `REPO_ROOT` into `CONNECTORS_ROOT` + `LAUNCHPAD_ROOT` via `orchestrator/paths.py`. `ACTIVATION_API_DIR` now points internally within the submodule (`.deploy/connector-activation/`) instead of back to launchpad. Stripped `prefect-infra` pipeline type to `status: deferred` (one-time setup already done). Removed GP-218 from `PHASE0_TICKETS` seed list. Stripped agent registry + Zeus Chat handlers from server (move to dashboard in Phase 0.5). Cleaned up design docs and data copies from credential-exchange before commit.
- result: All imports verified. Boot simulation passed: 4 active pipeline types (connector-migration 13 stages, credential-provision 6, data-parity-test 5, connector-promotion 14), 1 deferred. Static file serving, data layer, credential loading all resolve correctly from new location. Commit `946a6d3` in prefect-connectors (41 files, 7,794 lines).
- decided: API services live at `connectors/.deploy/` (Azure Function deployment artifacts, separate from connector runtime). `portal-auth/` stays in aldc-launchpad (client-facing, not connector infrastructure). Original files in `aldc-launchpad/scripts/` not deleted yet — cleanup deferred.
- next: Phase 0.5 — adopt Conductor modules (`events.py`, `audit.py`, `validation.py`, `work_guard.py`, `memory.py`, `git_ops.py`), wire SSE into server, split monolithic dashboard HTML into pages.

### 2026-05-21 — Exchange-rates promoted QA → UAT → Prod (all COMPLETED)

- did: Full QA → UAT → Prod promotion of exchange-rates connector. Provisioned complete per-environment infrastructure that was missing: Azure Storage Accounts (`aldcteststac1cf49f9aa3` in Test 1, `aldcprodstac1cf49f9aa3` in Production 2) with `stage` containers + RBAC for both Prefect ACI managed identity and Snowflake service principals. Snowflake on og35375: role `TEST_DG1_ROLE_CORE_SVC_F49F9AA3`, SERVICE user with RSA keypair, storage integration `INT_ALDCTESTSTAC1CF49F9AA3`, staging DB/stage/format, warehouse DB `TEST_DG1_ALDC_QA`. Same stack on wj66376 (prod). Updated Prefect blocks with PEM private keys. Patched `SnowflakeClient` to support key-pair auth alongside password (backward compatible). Merged to `uat` → `main`, new `:uat` and `:main` images built. Separated Prefect deployments per env: `smoke-test-exchange-rates` (QA), `exchange-rates-uat`, `exchange-rates-prod`.
- result: QA: 58s COMPLETED (previous session). UAT: 59.8s COMPLETED. Prod: 56.2s COMPLETED. All three environments running.
- bugs found: (1) Snowflake BCR 2024_08 blocks LEGACY_SERVICE user creation — new service accounts must use SERVICE type (key-pair auth). (2) Connector code only supported password auth — needed 15-line patch. (3) Private key must be stored as PEM string in Prefect block, not base64(DER) — `load_pem_private_key` expects PEM. (4) Deployment name reuse overwrites source env — use separate names per env. (5) Storage integration URL needs `/stage/` path suffix and correct tenant ID (`e2bae64b-...`).
- infra lessons: connector warehouse DB = `{ENV}_DG1_{ACCOUNT_SHORT_CODE}`, not the `_PREFECT` suffix database. Must provision per environment. Separate Azure subscriptions per tier: Quality 1 (efe036d8), Test 1 (6969113c), Production 2 (6389f755). Snowflake accounts: nonprod og35375, prod wj66376.
- next: Enable prod cron schedule. Then `/promote-sellercloud-sql`.

### 2026-05-20 — Orchestrator hardening: E2E smoke test PASSED on real Prefect

- did: Hardened `api/connector-activation/services/prefect.py` — added CSRF token handling (Prefect v3 self-hosted requires `GET /csrf-token` + `Prefect-Csrf-Token` header on all POST/PATCH), retry logic via `urllib3.Retry` (3 retries, backoff on 429/502/503/504), `health_check()` method, block type cache invalidation. Added `"path": "/app"` and `"pull_steps": []` to all deployment payloads — required for code-in-image deployments, without these the ACI container crashes with `FileNotFoundError: /app/None`. Fixed `connector_catalog.py` entrypoint for exchange-rates (was `connector/flows/` which doesn't exist; correct path is `connector/accounts/ALDC_QA/deployments/`). Added `scripts/smoke_test_e2e.py` — standalone E2E test with 8 steps: health check → catalog → work pool → GHCR image → deploy → trigger → poll → Snowflake verify.
- result: `smoke_test_e2e.py --skip-snowflake` ran successfully end-to-end. Flow run "lyrical-raven" deployed to `azure-aci-qa`, ran on ACI, COMPLETED in 58 seconds. First proven E2E execution of the Prefect pipeline from orchestrator code.
- bugs found and fixed: (1) All POST/PATCH return 403 without CSRF token — not needed by Prefect Cloud, only self-hosted. (2) `pull_steps` missing → "storage at None" crash. (3) `path` missing → `/app/None` FileNotFoundError. (4) Wrong entrypoint in catalog. (5) Local dev mock always returns COMPLETED, hiding all real Prefect errors.
- credential source: `PREFECT_API_AUTH_STRING` is in Azure App Service settings on `aldcprodwbapprefectserver1c01` (not Key Vault — KV is on private endpoint, not accessible without VPN). Retrieve: `az webapp config appsettings list --name aldcprodwbapprefectserver1c01 --resource-group aldcprodrsgpconnector1c --subscription 6389f755-3ff7-488a-a56c-7ea8297730bc --query "[?name=='PREFECT_API_AUTH_STRING'].value" -o tsv`
- next: A4 (provision GEP credentials to Key Vault + Prefect blocks), then A6 (sellercloud-sql E2E with real credentials).

### 2026-05-14 — wiki-sync: deploy UX polish (Quick-Deploy banner + Action column)

- did: Surfaced the Deploy action so users can find it without expanding rows. Added a Quick-Deploy banner above the filter panel with a grouped dropdown (Ready to deploy / Provisioned ready to build / Active — promote) and a primary Deploy button that opens the existing modal. Added a new Action column on the right of every table row with a contextual button: `Deploy →` (status=ready or planned+provisioned), `Promote →` (active with next env available, qa→uat or uat→prod), `Redeploy` (fully deployed), `Awaiting cred` (disabled, credential not provisioned), `—` (not yet deployable). New `inlineActionButton(c)` helper + `populateQuickDeploy()` in `pages/connectors/index.html`. Tip text under the table reminds users they can still click a row for the full detail panel. SPA shell fix in the same session (real `<script>` injection in place of `new Function()`) means every onclick across all PoC pages now works — connectors page already used window.* assignments so no regression there.
- decided: Discoverability rule for the platform — if a primary action (Deploy / Submit / Approve) is only reachable via an expand/detail pattern, always also surface it inline in the collapsed row AND as a top-of-page quick-action. Captured in `/launchpad-master-page` skill.
- bug fixed: "where can I deploy the CA connector from — it didn't work." Root cause: Deploy button was hidden inside expandable row, not discoverable on first scan. Specifically `gep-amazon-ads-ca` (status=deploying) now shows `Redeploy` inline + appears in the "Active — promote" group in the dropdown.
- commits: `87a807b` (connector UX), `21d6859` (SPA shell fix that unblocks all PoC handlers).
- status: Phase 0C remains Complete. Deploy flow now demo-ready end-to-end with mock pipeline; real pipeline pending `window.ACTIVATION_API_URL` wire-up.
- next: After demo — set `window.ACTIVATION_API_URL` to hit the real activation endpoint instead of `USE_MOCK_API=true`.

### 2026-05-13 — wiki-sync: Phase 0C complete — all 4 deliverables shipped

- did: Built all remaining Phase 0C deliverables. Deploy modal with animated 6-step pipeline (verify credential → resolve image → register deployment → push to work pool → trigger test run → verify data in Snowflake). Framework column added (Eclipse/Prefect Legacy/Prefect v3) — confirmed with Paul that only Exchange Rates is on Prefect (legacy core_api design), all other active connectors are Eclipse template-based. Environment column + filter (QA/UAT/Prod/Not Deployed). Corrected work pool names to actual Azure infrastructure: `azure-aci-qa`, `azure-aci-uat`, `azure-aci-production`. Filter panel redesigned into labeled groups (Client, Environment, Framework, Status, Credential). Freshness monitoring: schedule-aware overdue/stale warnings with pulsing dots, freshness KPI card. Prefect UI link (`prefect.analyticlabs.io`) in header + deep-link "View in Prefect" buttons on active connectors. Inactive status filter for paused/error connectors.
- decided: core_api is NOT in the Prefect data path — architecture is clean (Prefect → Azure Storage → Snowflake). `global_config.py` env vars (CORE_URL, CORE_API_TOKEN) only needed by legacy connectors. New framework connectors use Prefect Blocks only. Paul confirmed: 0 connectors on Prefect v3 yet, 2 on Prefect Legacy (Exchange Rates), 21 on Eclipse.
- status: All 4 deliverables complete. Migration catalog (50 connectors), connector template docs, deploy flow UI, live deployment pipeline. Demo-ready.
- next: Phase 1A — credential tracking dashboard (`/launchpad-phase1a` in new session).

### 2026-05-13 — wiki-sync: deliverables verified

- did: Connector catalog built (`data/connectors.json` — 42 connectors: 8 active, 2 deploying, 4 ready, 28 planned across GEP/F92/ALDC_QA). Connector management page (`pages/connectors/index.html`) built and registered in SPA shell. Data pre-loaded via `window.LaunchpadData.connectors`. By-client breakdown: GEP 17 (4 active, 2 deploying, 3 ready, 8 planned), Fusion92 9 (7 active, 2 planned), ALDC_QA 1 (active).
- status: Core deliverables 1 (catalog) and 3 (UI page) complete. Deliverable 2 (connector template/generator) and 4 (live deployment pipeline triggering Prefect from UI) not yet built — these are the demo-day items.
- next: Build deploy flow (UI button → Prefect deployment → data lands). Amazon Ads US is the demo candidate.

### 2026-05-13 — Phase created

- did: Created phase tracker and `/launchpad-phase0c` boot prompt skill
- decided: This phase runs before/alongside Phase 1A to enable the full demo story
- next: Analyze prefect-connectors and core_api, build migration catalog, implement deploy flow

## See Also

- [[phase-0-monorepo-restructure]] — Repo structure this phase builds on
- [[phase-1a-credential-dashboard]] — Credential tracking that feeds into deployment
- [[../README]] — Launchpad project overview
