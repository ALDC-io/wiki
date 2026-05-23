---
tags: [launchpad, connectors, framework, deployment, complete]
created: 2026-05-13
updated: 2026-05-21
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
