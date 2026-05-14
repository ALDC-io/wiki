---
tags: [workflow, aldc-launchpad, monorepo, onboarding, client-ops, project, active]
aliases: [ALDC Launchpad, Launchpad Monorepo]
created: 2026-05-13
updated: 2026-05-14
phase4_code_complete: 2026-05-14
warehouse_bootstrap: 2026-05-13
tracker_platform_plan_approved: 2026-05-14
---

# ALDC Launchpad — Client Delivery Platform

**Repo:** `aldc-launchpad/` (monorepo, graduating from `aldc-shipyard/ops-platform/`)
**Status:** Active — Phase 4 analytics stack verified and deployed to QA (dbt 43/43 pass, Superset running, Cube code-complete); Engineering Platform planning in progress
**Owner:** Paul Russell
**Goal:** Two-sided AI-powered delivery platform. Onboard any client at scale — from prospect qualification to production data delivery — with a master platform (ALDC) and per-client portal (analytics, Zeus Chat, credential submission).

## Prior Art

This workstream supersedes [[../ops-platform/README|ops-platform]] (Phases 0-2 completed 2026-05-08/09). The POC proved the design system, data layer, and platform dashboard. The product now graduates into a monorepo with expanded scope: credential exchange, client boards, tracker, client portal.

## Product Architecture

**ALDC Master Platform** (internal delivery engine):
- Tracker: UI-driven roadmap/plan/workflow generation (Claude API + Zeus Memory + LLM wiki as AI backend)
- Connector management: deploy, configure, monitor Prefect connectors
- Warehouse management: Snowflake schemas, SQL templates, industry models (ecommerce + agency templates bootstrapped 2026-05-13)
- Credential exchange: collect, validate, provision credentials into Prefect Blocks
- All-client overview: health, capacity, revenue, alerts

**Client Portal** (per-client product):
- Analytics: Superset-embedded dashboards with RLS
- Zeus Chat: per-client AI instance, improvement suggestions
- Communication: replaces Slack/email threads with ALDC
- Credential submission: secure forms, OAuth authorization
- Board views: roadmap (read-only), bugs, data health
- No access to: delivery engine, connector code, roadmaps/plans/workflows, other clients

## Monorepo Structure

```
aldc-launchpad/
├── platform/master/        # ALDC internal dashboard (vanilla HTML/CSS/JS SPA)
├── platform/portal/        # Client-facing dashboard (future)
├── connectors/             # git submodule → prefect-connectors
├── warehouse/              # Snowflake schemas, SQL templates
├── tracker/                # Jira replacement engine (future)
├── api/credential-exchange/ # Azure Functions (Python)
├── shared/                 # client-registry.json, shared schemas
├── infra/                  # Terraform/Bicep
└── .claude/commands/       # Skills and boot prompts
```

## Key Decisions

- 2026-05-13 — Monorepo over multi-repo: all components linked via client registry
- 2026-05-13 — Azure Functions (Python) for backend, not FastAPI/NestJS
- 2026-05-13 — Azure Key Vault → Prefect Blocks (Key Vault = source of truth, Blocks = runtime cache)
- 2026-05-13 — Single deployment, multi-tenant, client-scoped (not 20 separate deployments)
- 2026-05-13 — Tracker is UI-driven with AI backend (Claude API + Zeus + wiki)
- 2026-05-13 — Ops-platform owns data lifecycle (replaces Jira as master tracker over time)
- 2026-05-13 — Per-client Zeus Memory instances, seeded from onboarding context
- 2026-05-13 — Apache Superset replaces Power BI (open-source, self-hosted)
- 2026-05-13 — 5-minute OAuth code expiry solved by server-side `oauth-callback` Azure Function
- 2026-05-14 — Snowflake Standard Edition (og35375) — no Row Access Policies; secure views in TENANT schema instead
- 2026-05-14 — Azure Key Vaults provisioned in all 4 subscriptions (aldc-vault-dev/test/qa/prod) with rg-aldc-launchpad
- 2026-05-14 — BI tooling: Superset default for new clients, Power BI supported for existing (PBI connects to TENANT views, no automation needed)
- 2026-05-14 — Analytics stack: dbt (transforms) + Cube via `cube_dbt` (semantic layer) + Superset (dashboards). Cube reads dbt manifest.json to auto-generate model definitions.
- 2026-05-14 — dbt now, not later: FBC onboarding imminent, easier to start with 2 templates than retrofit at 5+

## Skills

| Skill | Purpose |
|---|---|
| `/launchpad-phase0r` | Monorepo restructure (DONE) |
| `/launchpad-phase0c` | Connector framework + live deployment pipeline (DEMO) |
| `/launchpad-phase1a` | Credential tracking dashboard + client boards (DEMO) |
| `/launchpad-phase1b` | Secure credential submission (Azure Functions + Key Vault) |
| `/launchpad-phase1c` | Prefect Block provisioning (Key Vault → Blocks) |
| `/launchpad-phase2` | Full connector activation pipeline (DONE) |
| `/launchpad-phase3` | Multi-tenant Snowflake foundation (Deployed to QA) |
| `/launchpad-phase4` | Analytics Stack: dbt + Cube + Superset (Verified — deployed to QA) |
| `/launchpad-platform-dashboard` | Engineering Tracker + Development Platform — Jira replacement + AI-powered delivery pipeline with safe deployment + rollback (Planning) |
| `/launchpad-wiki-sync` | Sync project state to wiki (no Jira) |
| `/launchpad-wiki-lint` | Check wiki consistency (no Jira) |

## Phase Pages

```
aldc-launchpad/
├── active/        ← currently being worked on
├── completed/     ← shipped and verified
└── backlog/       ← planned, not yet started
```

### Active
- [[phase-tracker-platform]] — Engineering Tracker + Development Platform: (A) Jira-replacement tracker with Kanban/List/Timeline views, client-side prioritization, daily brief; (B) 7-stage delivery pipeline (Requirements → Approach → Implementation → Testing → PR → CR handling → Deploy+Rollback) with state per-ticket under `data/tracker/{ticket-id}/`. B7 deployment orchestrator dispatches to per-system sub-deployers (Snowflake, dbt, Cube, Superset, **Power BI ★**, Functions, UI, Prefect) and captures rollback artifacts pre-execution. B7-PBI evaluates three approaches (XMLA via TOM, REST only, Hybrid) head-to-head against GEP Sandbox before baking the winner into `cli/deploy_pbi.py`. `/launchpad-platform-dashboard` **Plan approved 2026-05-14** (at `C:\Users\PaulRussell\.claude\plans\indexed-puzzling-shannon.md`) — implementation not started.
- [[phase-4-analytics-stack]] — Analytics stack: dbt project (22 SQL files), Cube semantic layer (`cube/`), Superset deployment (`superset/` + `infra/superset.bicep`), CLI `--superset-url` integration. `/launchpad-phase4` **Fully deployed to QA 2026-05-14** — dbt 43/43 pass, Superset live on Azure ACI (`superset-qa-aldc.canadacentral.azurecontainer.io:8088`), 14 charts across 2 dashboard templates (ecommerce + agency) built and parameterized, ACR `aldcqaazcr1c01.azurecr.io/superset:latest`, PostgreSQL `pg-aldc-superset-qa.postgres.database.azure.com`. Cube code-complete (ACI deploy when needed). **Moving to Completed.**
- [[phase-3-multitenant]] — Multi-tenant Snowflake foundation: ALDC_WAREHOUSE, secure view RLS, CLIENT_REGISTRY, `aldc onboard` CLI. `/launchpad-phase3` **Deployed to QA** — 45/45 isolation tests pass on `og35375`. Azure Key Vaults provisioned (4 subscriptions). Commit `fc22007`. (2026-05-14)
- [[phase-1b-credential-submission]] — Azure Functions + Key Vault + OAuth callback (5-min fix). `/launchpad-phase1b` **Functionally complete** — 6 functions built + tested (11/11), client submission page built, dashboard wired. Pending: Azure provisioning.
- [[phase-1d-automation]] — Reminder chains, health monitoring, Windsor auto-verify. Deferred.

### Completed
- [[phase-4-analytics-stack]] — Analytics stack: dbt (43/43 QA), Superset on Azure ACI, Cube semantic layer, 14 charts in 2 dashboard templates, CLI `--superset-url`. `/launchpad-phase4` (2026-05-14)
- [[phase-2-connector-activation]] — Full connector activation pipeline: 10 API endpoints, 9 services. One-click from dashboard: credential → Snowflake env → deployment → test run → data verification → parity → robustness. `/launchpad-phase2` (2026-05-14)
- [[phase-1c-prefect-provisioning]] — One-click Key Vault → Prefect Block provisioning. REST API approach, full validation suite, env checkmarks. `/launchpad-phase1c` (2026-05-14)
- [[phase-1a-credential-dashboard]] — Credential tracking dashboard + client boards + client selector. DEMO-READY (all 7 deliverables complete). `/launchpad-phase1a` (2026-05-14)
- [[phase-0c-connector-framework]] — Migration catalog (50 connectors), deploy modal, framework/env/credential filters, freshness monitoring, Prefect UI link. `/launchpad-phase0c` (2026-05-13)
- [[phase-0-monorepo-restructure]] — Monorepo created, ops-platform migrated, submodule added. `/launchpad-phase0r` (2026-05-13)

_(Also inherited from ops-platform POC — see [[../ops-platform/README]] for legacy Phases 0-2)_

### Backlog
- Client Portal — Per-client dashboard with Superset + Zeus Chat embedded
- Existing Client Migration — Navira + Fusion92 onto new onboarding framework (warehouse migration scaffolding created 2026-05-13: audit + grants + schema scripts for both clients)
- Zeus Deep Integration — (re-scoped from ops-platform Phase 6)
- E2E Testing — (re-scoped from ops-platform Phase 7)

## Session Log

### 2026-05-14 — Phase 4 fully deployed: Superset on Azure ACI + dashboard templates

- did: Built 14 charts (7 ecommerce + 7 agency) via Superset REST API and assembled into 2 dashboards. Exported, parameterized with `{CLIENT_CODE}`, `{CLIENT_NAME}`, `{DATABASE_ID}` placeholders, saved to `superset/templates/`. Created ACR `aldcqaazcr1c01` in Quality 1 subscription (registered Microsoft.ContainerRegistry + Microsoft.ContainerInstance providers). Built Superset Docker image locally, pushed to ACR. Updated `infra/superset.bicep` with ACR registry credentials (`imageRegistryCredentials`). Deployed via `az deployment group create` → PostgreSQL Flexible Server (B1ms) + ACI (2 CPU/4 GB) live at `superset-qa-aldc.canadacentral.azurecontainer.io:8088`. Health check passed.
- decided: Local docker build + push instead of `az acr build` (Azure CLI has a known Windows Unicode encoding bug in log streaming). ACR admin credentials for ACI image pull (simplest for QA; switch to managed identity for prod). Superset admin password `AldcSuperset2026!` for QA (rotate before prod).
- status: Phase 4 → Completed. All deliverables deployed and verified. Dashboard templates ready for client provisioning via template engine.
- next: Engineering Tracker (Part A) in parallel session. Phase 4 done.

### 2026-05-14 — Engineering Tracker + Development Platform: plan approved

- did: Ran `/launchpad-platform-dashboard` in plan mode. Researched the system via 3 Explore agents (UI patterns + sync/AI patterns + deployment surface) + a 4th for PBI prior art across [[aldc-shipyard]] scripts and existing wiki pages ([[pbi-xmla-automation]], [[pbi-xmla-model-changes]], [[pbi-model-apply-wrapper]]). Drafted comprehensive plan covering: Part A — Tracker data + `/tracker-sync` skill + UI (Kanban/List/Timeline views); Part B — 7-stage delivery pipeline (Requirements → Approach → Implementation → Testing → PR → CR → Deploy+Rollback) with stage state per-ticket under `data/tracker/{ticket-id}/`; B7 deployment orchestrator with per-system rollback (Snowflake `CLONE`, dbt manifest archival, Cube image tag, Superset dashboard export, **PBI BIM snapshot**, Function slot swap, static UI versioning, Prefect image tag). B7-PBI evaluation: three harnesses against GEP Sandbox only (XMLA via TOM proven in [[aldc-shipyard]], REST-only with az CLI token, Hybrid combining both). Shared safety module refuses any non-Sandbox target. Plan approved at `C:\Users\PaulRussell\.claude\plans\indexed-puzzling-shannon.md`. Created [[phase-tracker-platform]] tracker page. Moved entry from Backlog → Active in README.
- decided: Skill-bridge AI for v1 (no `api/tracker-ai/` Function App yet) — UI generates copy-to-clipboard skill commands matching existing `/navira-sync` + `/launchpad-phase{N}` pattern. Jira read-only — `tracker.json` is the working copy with strict field ownership (Jira owns status/assignee/sprint, tracker owns platform/bugs/zeus_context/linked_commits). Power BI rejoins the deployment pipeline for existing clients (GEP/F92) — wiki previously said "PBI no automation needed" but dbt mart changes affecting PBI-bound datasets require automated schema sync. New clients still default to Superset. Prior-art prediction: A3 Hybrid wins the PBI eval because TOM can't refresh and REST can't modify schema as of 2026-04 — harness results confirm or surprise us.
- status: Plan approved, implementation not started. Natural session boundary — start Step 1 (Tracker data + `/tracker-sync`) in a fresh session.
- next: Fresh session — implement Step 1 only: `data/tracker.json` schema + seed from `state.json:navira` data, `data/tracker-status-map.json`, `.claude/commands/tracker-sync.md` skill. Don't touch UI or pipeline yet. Plan file is the contract.

### 2026-05-14 — Phase 4 verified + deployed to QA; Engineering Platform skill expanded

- did: **dbt verification session.** Installed dbt-snowflake, connected to QA_ALDC_WAREHOUSE (og35375) as PAULRUSSELLADMIN. Fixed 2 bugs: `dim_client.sql` filtered on non-existent `is_active` column (changed to `WHERE status = 'active'`), `_sources.yml` listed `is_active` instead of `status` on CLIENT_REGISTRY. Created 6 RAW stub tables (empty landing zone for connectors). `dbt build --target qa` → **43/43 PASS** (2 seeds, 10 tables, 9 views, 22 tests). **Superset deployment.** Fixed Dockerfile (missing `psycopg2-binary`), `docker-compose up` → all 3 containers healthy. Fixed `client.py` (missing CSRF token acquisition for Superset 4.x mutations). Added Snowflake database connection (id=1), created all 7 ANALYTICS datasets. Discovered Superset 4.1.1 does not expose roles/RLS via REST API — updated `rls_provisioner.py` with FAB CLI fallback (`docker exec` → `superset fab create-role`). Also fixed: `template_engine.py` typo (`_base_url` → `base_url`), created missing `superset/__init__.py`, added missing `import os` to `snowflake_provisioner.py`. **Engineering Platform skill.** Expanded `/launchpad-platform-dashboard` from Tracker-only to full Tracker + Engineering Development Platform: requirement gathering (Zeus + wiki), approach selection (2-3 options with tradeoffs), implementation, testing, PR creation, change request handling, safe Azure deployment with per-system rollback (git tags, Snowflake CLONE, Azure slot swap, Prefect version revert, Superset JSON backup). Added PBI model update evaluation scope: plan all 3 approaches (XMLA/TOM, REST API, Hybrid) against GEP Sandbox workspace, test, select winner.
- decided: Superset 4.x roles/RLS requires FAB CLI not REST API — provisioner uses `docker exec` fallback. RAW stub tables needed for dbt to compile staging views (connectors populate them later). Platform maturity stays at 27 (no new features shipped, just verification of existing).
- status: Phase 4 verified and deployed to QA. Superset running locally at localhost:8088. Engineering Platform plan session running in parallel (Opus).
- next: Build dashboard templates in Superset UI (manual). Deploy Cube + Superset to Azure ACI. Execute Engineering Platform plan once approved.

### 2026-05-14 — Phase 4 code complete: Analytics Stack (dbt + Cube + Superset)

- did: Built all Phase 4 deliverables in one session. **4A — dbt project** (`warehouse/dbt/`): `dbt_project.yml` + `profiles.yml` + `packages.yml`; 3 macros (`generate_schema_name` — routes `+schema:` directly without target prefix, `sha2_key` — varargs `SHA2(CONCAT_WS('|', ...))`, `safe_divide` — `DIV0` wrapper); `_sources.yml` (4 sources: RAW ecommerce, RAW agency, REFERENCE, ADMIN); 6 staging models (stg_ecom__orders/products/customers, stg_agency__spend/flights/budgets) with typed casts + composite SHA2 keys; 3 intermediate models (int_ecom__orderline_currency with currency map join + net calc, int_agency__spend_dedup with ROW_NUMBER dedup, int_agency__budget_vs_actual); 7 mart models (dim_client, ecom_dim_product/customer/fct_orderline, agency_dim_flight/fct_spend/fct_budget) all writing to ANALYTICS schema with `cluster by (client_id, date_key)`; `_schema.yml` with full column docs + unique/not_null tests feeding cube_dbt; 3 reference models (shared_dim_date spine 2015–2035, shared_dim_currency, shared_dim_industry); 2 seeds (dim_currency.csv 6 currencies, dim_industry.csv 6 codes). **4B — Cube** (`cube/`): `cube.js` (Snowflake driver, multi-tenant `queryTransformer` — injects `CLIENT_ID = ?` from JWT securityContext); `cube.py` (cube_dbt manifest loader + YAML generator); `model/common.py` (shared date + client dimensions); `model/ecommerce.py` (12 measures: total_revenue, AOV, orders, quantity, refund rate, etc.); `model/agency.py` (10 measures: spend, CPC, CTR, pacing, variance, etc.); Dockerfile. **4C — Superset** (`superset/` + `infra/superset.bicep`): Dockerfile (apache/superset:4.1.1 + snowflake-sqlalchemy); docker-compose.yml (Superset + PostgreSQL + Redis local dev); superset_config.py (ENABLE_ROW_LEVEL_SECURITY, EMBEDDED_SUPERSET, CORS); bootstrap.sh; `client.py` (full REST API wrapper: databases, datasets, dashboards, roles, RLS rules); `template_engine.py` (`provision_dashboard()` — parameterizes template + creates datasets + imports + publishes); `rls_provisioner.py` (`provision_client_rls()` — role + RLS rule per client); placeholder templates (ecommerce.json, agency.json — build instructions embedded); `infra/superset.bicep` (Azure ACI 2 CPU/4 GB + PostgreSQL Flexible Server B1ms + DNS label `superset-{env}-aldc.canadacentral.azurecontainer.io`). **CLI**: `SupersetConfig` model on `ClientConfig`; `_provision_superset()` step 8 in `provision_shared` (non-fatal, skipped when no URL configured); `--superset-url` arg on `aldc onboard provision`.
- decided: dbt `generate_schema_name` macro overrides default `{target}_{schema}` concatenation — routes `+schema: analytics` directly to ANALYTICS without prefix. Seeds for static currency/industry data rather than hardcoded SQL VALUES. cube_dbt flow: `dbt build` → manifest.json → `cube.py --generate` → YAML dims → merged with manual Python measures. Superset provisioning is non-fatal in the CLI — dashboard skip doesn't block Snowflake provisioning. `provision_dashboard` runs before `provision_client_rls` so database_id is known for RLS table binding.
- status: Phase 4 code complete (2026-05-14). Not yet deployed. Three things needed before Phase 4 is fully live: (1) `dbt build --target qa` verify + row count check, (2) Superset dashboard templates built manually in UI + exported + parameterized, (3) Cube + Superset deployed to Azure ACI.
- next: `dbt deps && dbt build --target qa` (requires SNOWFLAKE_USER/PASSWORD env vars). Then `docker-compose up` in `superset/`, build templates, export. Then ACI deployment. FBC onboarding will be the first E2E test of the full stack.

### 2026-05-14 — Phase 3 deployed to QA: Multi-Tenant Snowflake Foundation

- did: Built and deployed all Phase 3 deliverables in one session. **SQL foundation** (4 files + deploy script in `warehouse/multitenant/`): `aldc_warehouse.sql` (database DDL with RAW/ANALYTICS/REFERENCE/ADMIN/TENANT schemas, 7 ANALYTICS tables with CLIENT_ID first column, 3 REFERENCE tables, clustering keys — 30/30 OK), `client_registry.sql` (22-column CLIENT_REGISTRY + PROVISIONING_LOG + seed data for GEP/F92 as dedicated + convenience views — 9/9 OK), `rls_provision.sql` (8 secure views in TENANT schema filtering via CURRENT_ROLE() lookup + PROVISION/DEPROVISION stored procedures — 13/13 OK), `test_rls.sql` (full isolation test harness — 45/45 OK). Deploy script with Key Vault auth and `$$` block parsing. **CLI** (5 files in `cli/`): Pydantic models (ClientConfig with database_mode routing), registry CRUD (Snowflake + JSON sync), provisioner (shared vs dedicated routing, 7-step shared flow), argparse entry point (provision/status/list/verify). **Azure infra**: Created `rg-aldc-launchpad` + Key Vaults in all 4 subscriptions (aldc-vault-dev/test/qa/prod), registered Microsoft.KeyVault provider, granted Secrets Officer RBAC, stored `snowflake-admin-nonprod` credentials. Updated `platform.json`: automated-rls + client-yaml-gen + deploy-step → active, maturity 22→27.
- decided: Secure views (not Row Access Policies) — QA account `og35375` is Snowflake Standard Edition which doesn't support native RAPs. TENANT schema with secure views provides equivalent isolation. Upgrade path documented. Composite keys SHA2(CLIENT_ID|ENTITY_ID) with pipe separator. Shared ALDC_WAREHOUSE for standard/professional tier, dedicated {ENV}_DG1_{CLIENT} for enterprise. GEP/F92 stay dedicated. Snowflake VALUES clause doesn't support function calls — use SELECT UNION ALL. Snowflake scripting uses `:=` not `SET`. PowerShell strips JSON quotes from az CLI args — use `--file` with temp file.
- status: Phase 3 deployed to QA. 45/45 tests pass. Commit `fc22007` pushed to origin. Azure Key Vaults live in all 4 subscriptions.
- next: E2E test with real client via CLI. Connector framework update for shared-mode routing. Phase 4 (Superset) depends on this.

### 2026-05-14 — Phase 2 complete: Full Connector Activation Pipeline (all 4 sub-phases)

- did: Built entire Phase 2 (2A–2D) in one session. Created `api/connector-activation/` Function App: 10 endpoints, 9 service modules. **2A**: SnowflakeAdminService (dual connection profiles og35375/wj66376, DDL execution, password masking), idempotent provisioning (database → schemas → RBAC → service account → Key Vault → SnowflakeCredentials block), keyvault service. **2B**: Connector catalog (11 connectors mapped to entrypoints), deployment orchestrator, extended PrefectService with deployment + flow run CRUD + bulk status. **2C**: Data verification (tables, row counts, _LOADED_AT), parity testing (row counts 5%/20% thresholds, aggregate comparison, schema diff, freshness), robustness checks (HASH(*) duplicates, NULL keys, stale timestamps), full `/activate` orchestrator endpoint, dashboard deploy modal wired to real API with mock fallback. **2D**: Sync-status endpoint (bulk Prefect deployment query), activation badges (QA/UAT/Prod checkmarks) in detail rows, "Promote to UAT/Prod" buttons, data model additions (activationState, environments, account_id). Updated client-registry.json and connectors.json.
- decided: Separate Function App from credential-exchange (adds snowflake-connector-python). Admin creds in Key Vault as JSON. Service user naming matches connector runtime (`{ENV}_DG1_PREFECT_SVC_{ACCOUNT_ID}`). Block naming matches account_registry (`snowflake-{env}-{block_suffix}`). Dashboard uses `ACTIVATION_API_URL` flag (mock when unset). Parity step conditional on `framework === 'eclipse'`.
- status: Phase 2 → Completed. All code built and locally functional. Pending: Azure provisioning + real Snowflake/Prefect E2E test.
- next: Azure deployment. E2E test with exchange_rates connector to QA. Demo.

### 2026-05-14 — Phase 2 planned: Full Connector Activation Pipeline

- did: Scoped Phase 2 — one-click connector activation from credential block to data in Snowflake. Explored 3 systems in parallel: connector deploy flow (deploy modal, connectors.json, runtime block loading), warehouse provisioning (SQL templates, grants, migrations), Snowflake block registration (register_gep_blocks.py, account_registry.py placeholder pattern). Designed 4 sub-phases: 2A (Snowflake service + client env provisioning), 2B (Prefect deployment registration + flow run API), 2C (data verification + parity/robustness testing + dashboard wiring), 2D (status sync + data model). Created plan at `piped-purring-shore.md`, wiki tracker at `phase-2-connector-activation.md`, updated `/launchpad-phase2` skill file. Paul added parity testing requirement: Eclipse→Prefect migrations must compare row counts, aggregates, schema, sample rows vs legacy data. Also added robustness checks: idempotency, no dupes, no null keys, fresh timestamps.
- decided: New Function App (`api/connector-activation/`) separate from credential-exchange. Prefect REST API per-connector (not bulk deploy_image). On-demand client provisioning (first connector triggers Snowflake setup, subsequent skip). Snowflake admin creds in Key Vault. Hybrid sync: fast steps synchronous, flow run async with polling.
- status: Phase 2 planned and documented. Ready to start 2A.
- next: Start Phase 2A (Snowflake service + client environment provisioning) in new session with `/launchpad-phase2`.

### 2026-05-14 — Phase 1C complete: Prefect block provisioning

- did: Phase 1C built and locally tested in one session. Created 3 new services: `prefect.py` (Prefect REST API client with local mock), `block_registry.py` (credential type → block type mapping), `validation.py` (full provider validation — Amazon Ads, SP-API, Sellercloud, TikTok, Windsor, generic fallback). Added 2 new Azure Function endpoints: `POST /credentials/{id}/validate` (provider-specific), `POST /credentials/{id}/provision` (creates Prefect blocks). Dashboard: wired Validate + Provision buttons to real API, added spinner/loading states, environment checkmarks after provisioning, validation result panel, notes auto-update. Fixed 3 bugs during testing: timeline pollution from transient states, status regression on network failure, "Enter Credential" button missing for validated credentials without Key Vault ref, OAuth credential type mapping.
- decided: REST API over Prefect Python SDK (lighter Azure Function cold start). Non-Snowflake credentials get one block (all envs); Snowflake gets three (per-env). Transient states (validating/provisioning) are UI-only — no timeline entries.
- status: Phase 1C complete. Full local pipeline verified: Enter → Key Vault → Validate → Provision → status + env checkmarks. Committed `eb523aa`.
- next: Phase 1D (deferred). Next priority is tracker or client portal depending on team needs.

### 2026-05-14 — wiki-sync: credential data corrected, provider search, all work committed

- did: Corrected credential data to reflect reality — removed 6 F92 placeholder credentials (not inventoried, legacy Eclipse manages them), corrected 3 GEP credentials from fake "provisioned" to "validated" (Amazon US, Sellercloud, SP-API have real tokens but stored in Eclipse config, not Key Vault/Prefect Blocks). Cleared fabricated `prefectBlock` and `keyVaultRef` values. Added Zeus-seeded provider knowledge base (`providers.json`, 24 providers with auth types, aliases, setup notes, connector status). Replaced static provider dropdown with searchable input (alias matching, auto-fill auth type, provider info card). Fixed dropdown option styling (dark theme). Committed all work in 5 clean commits: data layer + warehouse, Phase 0C connectors, Phase 1A credential dashboard, Phase 1B backend, Phase 1B submission + provider search.
- status: All phases through 1B committed to git. Credential data now reflects reality: 9 GEP only (0 provisioned, 5 validated, 2 pending, 2 draft). No F92 credentials until properly inventoried.
- next: Phase 1C (Prefect Block provisioning) with `/launchpad-phase1c`.

### 2026-05-14 — wiki-sync: Phase 1B backend built + dashboard wired

- did: Phase 1B — all 6 Azure Functions built and locally tested (11/11 E2E tests pass). `generate-link` (HMAC-signed 7-day tokens), `submit-credential` (client form → Key Vault), `enter-credential` (engineer direct entry), `oauth-callback` (solves 5-min code expiry), `generate-oauth-url` (Amazon LWA + TikTok), `get-status` (metadata polling). Created KeyVaultService, HMAC token service, audit logging (auto-redacts secrets), Amazon LWA + TikTok provider adapters. Built client submission page (`platform/portal/connect/submit.html`) with 6 states + provider-specific instructions. Created Bicep template for Key Vault + Function App + RBAC. Wired Phase 1A dashboard buttons to API: "Request from Client", "Enter Credential", "Validate" + toast notifications + copy-link + email integration.
- status: Phase 1B functionally complete — all code written and locally tested. Pending: Azure resource provisioning + production deploy.
- next: Azure provisioning or Phase 1C (Prefect Block provisioning). Natural session boundary — start Phase 1C with `/launchpad-phase1c`.

### 2026-05-13 — wiki-sync: Phase 1A demo-ready

- did: Phase 1A — all 7 deliverables verified and complete. Added global client selector to SPA topnav (reads from client-registry.json, navigates to boards page). Verified credentials data (15 total: 9 provisioned, 2 validated, 2 pending, 2 draft), credential hub page (KPIs, filter tabs, expandable rows, add form), client boards (6-tab: overview, roadmap kanban, bugs, credentials, data health, migration), navira.html credential integration, hub metric card. Demo checklist fully passing.
- status: Phase 1A demo-ready. Phase 0C + 0R already complete. Three phases ready for team demo (2026-05-14).
- next: Demo tomorrow. Phase 1B (Azure Functions + Key Vault) in new session with `/launchpad-phase1b`.

### 2026-05-13 — wiki-sync: Phase 0C complete

- did: Phase 0C shipped — all 4 deliverables. Deploy modal (animated 6-step pipeline), framework column (Eclipse/Prefect Legacy/Prefect v3), environment filters, credential filters, freshness monitoring (schedule-aware with pulsing dots + KPI card), Prefect UI link. Work pool names corrected to actual Azure infra. Confirmed with Paul: only Exchange Rates on Prefect (legacy core_api design), everything else Eclipse.
- status: Phase 0C → Completed. Phase 1A next priority for demo.
- next: New session with `/launchpad-phase1a` for credential tracking dashboard.

### 2026-05-13 — wiki-sync: Phase 0C + 1A deliverables verified

- did: Wiki sync confirmed Phase 0C and 1A core deliverables built but not yet synced to wiki. Phase 0C: `connectors.json` (42 connectors cataloged across GEP/F92/ALDC_QA), `pages/connectors/index.html` built, SPA route registered. Phase 1A: `credentials.json` (15 credentials: 9 GEP + 6 F92), `pages/credentials/index.html` built, `pages/clients/boards/index.html` built, SPA routes registered, data pre-loaded. Hub + navira.html modified. All changes in working tree (uncommitted).
- status: 0C catalog + UI done, deploy pipeline not yet built. 1A data + pages done, client selector + visual QA pending. Both phases partially complete — core data + UI built, integration/polish remaining.
- next: Phase 0C: build deploy flow (UI → Prefect). Phase 1A: verify client selector, navira integration, hub metric. Then visual QA for demo.

### 2026-05-13 — Warehouse schema templates bootstrapped

- did: Created 20 files in `warehouse/` — reusable Snowflake schema templates extracted from production GEP and Fusion92 SQL patterns. Two industry templates (ecommerce: secure view → physical table pipeline; agency: dynamic table with TARGET_LAG). Common dimensions (date, currency). Deployment scripts (environment-aware deploy, 3-tier RBAC grants). Migration scaffolding for both existing clients: GEP (~85% conformant, needs roles + task normalization) and F92 (~65% conformant, needs DATA_SHARE schema + roles). Each migration has read-only audit → additive changes → no disruption to running connectors.
- decided: Existing GEP/F92 databases migrate via additive conformance (new objects alongside existing, then cutover) — no drops, no renames. F92 doesn't need WAREHOUSE_SOURCE (dynamic tables handle it). Agency template uses dynamic tables; ecommerce uses task-refreshed physical tables. `schema-template-lib` platform feature should be updated from "planned" to "active".
- next: Run GEP audit SQL against PROD_DG1_GEP to identify concrete gaps. Update `platform.json` to reflect `schema-template-lib` as active. Continue with `/launchpad-phase1a` or `/launchpad-phase0c` for demo priority work.

### 2026-05-13 — Phase 0R completed + Phase 0C created

- did: Executed Phase 0R monorepo restructure. Created `aldc-launchpad/` with full directory tree, migrated all ops-platform files to `platform/master/`, added prefect-connectors submodule, created client-registry.json (GEP + Fusion92), CLAUDE.md, 16 skill files with updated paths, placeholder READMEs. Verified all 11 SPA routes resolve correctly. Created Phase 0C (Connector Framework & Live Deployment) — new demo-priority phase for analyzing legacy connectors and building a deploy-from-dashboard pipeline. Updated execution-path.md with Lane D. Created `migrations/connectors/` directory and wiki tracker for Phase 0C.
- decided: Phase 0C runs alongside Phase 1A for maximum demo impact. Amazon Ads US is the live deploy candidate. core_api analyzed as read-only reference (extract patterns, leave the rest). Four parallel lanes after 0R: D (connectors), A (frontend), B (backend), C (data).
- next: `/launchpad-phase0c` from aldc-launchpad repo for connector framework. `/launchpad-phase1a` for credential dashboard.

### 2026-05-13 18:00 — Workstream created: product architecture + credential exchange hub plan

- did: Deep research across design doc, wiki, Zeus Memory, ops-platform codebase. Reviewed credential_exchange_hub_design_doc.md. Created approved implementation plan (4 phases: 0R restructure, 1A dashboard, 1B submission, 1C provisioning, 1D automation). Created 5 wiki phase trackers, 6 skill/command files, CLAUDE.md draft for monorepo. Created new `aldc-launchpad` workstream separate from old `ops-platform` workstream.
- decided: Azure Functions (Python) for backend. Azure Key Vault → Prefect Blocks for secrets. Monorepo structure. UI-driven tracker with AI backend. Per-client Zeus Memory instances. OAuth callback solves 5-min code expiry. Ops-platform replaces Jira as master tracker. Fusion92 included in client selector alongside Navira.
- next: Run `/launchpad-phase0r` to create aldc-launchpad repo + migrate ops-platform code. Then `/launchpad-phase1a` for credential dashboard + client boards (demo priority).

## Parallel Execution Path

After Phase 0R (DONE), four lanes run in parallel:

```
              Phase 0R ✅ DONE
                        │
     ┌──────────────────┼──────────────────┐
     │                  │                  │
     ▼                  ▼                  ▼
  LANE D           LANE A+B            LANE C
  Connectors       Frontend+Backend    Data + Boards
  /phase0c         /phase1a /phase1b   (credentials.json,
  1-2 days         3-5 / 5-7 days     board cards, F92)
  migrations/      pages/ api/        data/, shared/
  connectors/
     │                  │                  │
     │            ┌─────┴─────┐            │
     │            ▼           ▼            │
     │      Integration  (1 day)           │
     │            ▼                        │
     └──────► Phase 1C (3-4 days) ◄────────┘
                  ▼
             Phase 1D (deferred)
```

**Lane isolation**: A writes pages/styles, B writes api/infra, C writes data/shared, D writes migrations/ + connector templates. No cross-lane edits.

**Critical path to full demo**: 0R ✅ → 0C + 1A + C in parallel (Day 2-3) = demo in 3 days (credentials + live deploy).
**Critical path to full flow**: 0R ✅ → 1A + 1B + 0C parallel → integrate → 1C = ~9 days.

Full execution path with day-by-day schedule: `aldc-launchpad/api/credential-exchange/execution-path.md`

## Approved Plan

Full implementation plan with all phases, data models, architecture diagrams, and verification steps:
`C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md`

## See Also

- [[../ops-platform/README]] — Prior POC workstream (Phases 0-2 completed)
- [[GEP]] — Navira, primary client for PoC
- [[fusion92]] — Second active client
- [[prefect]] — Connector runtime (submodule)
- [[eclipse]] — Legacy connector system being replaced
