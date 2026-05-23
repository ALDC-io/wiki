---
tags: [workflow, aldc-launchpad, monorepo, onboarding, client-ops, project, active]
aliases: [ALDC Launchpad, Launchpad Monorepo]
created: 2026-05-13
updated: 2026-05-21
phase7a_smoke_test: 2026-05-15
phase4_code_complete: 2026-05-14
warehouse_bootstrap: 2026-05-13
tracker_platform_plan_approved: 2026-05-14
master_demo_prep_complete: 2026-05-14
orchestrator_complete: 2026-05-15
tracker_platform_steps_1_11_complete: 2026-05-15
---

# ALDC Launchpad — Client Delivery Platform

**Repo:** `aldc-launchpad/` (monorepo, graduating from `aldc-shipyard/ops-platform/`)
**Status:** Active — Phase 7b orchestrator + pipeline engine complete (2026-05-15): 4 pipeline types, 3 stage types (claude-p/script/gate), DAG execution, Zeus Chat + voice alerts, Deploy Board, 5 AI agents, Jira integration. Phase 0 tickets executed in parallel (GP-218/219/242/246). DV-465 Eclipse Chat fix shipped (PR#236 pending approval). Phase 7c next: hardening, client onboarding pipeline, live QA→UAT→Prod promotion, Snowflake visualization, UI polish.
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
| `/launchpad-platform-dashboard` | Engineering Tracker + Development Platform — Jira replacement + AI-powered delivery pipeline with safe deployment + rollback (**Steps 1-11 done**, B1-B7 complete, PBI Hybrid deployer built) |
| `/platform-plan` | B1 Requirements brief generator — Zeus/wiki/git/codebase context → `brief.md` |
| `/platform-approach` | B2 Approach options generator — brief → 2-3 approach `options.json` |
| `/platform-session` | B3 Implementation session — loads brief + approach, executes plan with resume log |
| `/launchpad-client-portal` | Client Portal — per-client SPA with embedded Superset + Zeus Chat + chart builder (Code built) |
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
- [[phase-tracker-platform]] — Engineering Tracker + Development Platform: (A) Jira-replacement tracker with Kanban/List/Timeline views, client-side prioritization, daily brief — **Part A complete** (149 tickets, 3 views, detail panel with stage-aware actions); (B) 7-stage delivery pipeline (Requirements → Approach → Implementation → Testing → PR → CR handling → Deploy+Rollback) — **Part B complete** (B1-B7 all built + PBI Hybrid deployer). Full pipeline: `/platform-plan` (B1), `/platform-approach` (B2), `/platform-session` (B3), `b4_test.py` (B4), `b5_pr.py` (B5), `b6_cr.py` (B6), `cli/deploy.py` (B7 orchestrator — 8 sub-deployers + rollback). PBI deployer: `cli/deploy_pbi.py` + `cli/rollback_pbi.py` (Hybrid approach: XMLA schema writes + REST refresh/validate, BIM snapshot rollback). PBI eval harnesses code-complete, run blocked on sandbox IDs. `/launchpad-platform-dashboard` **Steps 1-11 done 2026-05-14**.
- [[phase-4-analytics-stack]] — Analytics stack: dbt project (22 SQL files), Cube semantic layer (`cube/`), Superset deployment (`superset/` + `infra/superset.bicep`), CLI `--superset-url` integration. `/launchpad-phase4` **Fully deployed to QA 2026-05-14** — dbt 43/43 pass, Superset live on Azure ACI (`superset-qa-aldc.canadacentral.azurecontainer.io:8088`), 14 charts across 2 dashboard templates (ecommerce + agency) built and parameterized, ACR `aldcqaazcr1c01.azurecr.io/superset:latest`, PostgreSQL `pg-aldc-superset-qa.postgres.database.azure.com`. Cube code-complete (ACI deploy when needed). **Moving to Completed.**
- [[phase-3-multitenant]] — Multi-tenant Snowflake foundation: ALDC_WAREHOUSE, secure view RLS, CLIENT_REGISTRY, `aldc onboard` CLI. `/launchpad-phase3` **Deployed to QA** — 45/45 isolation tests pass on `og35375`. Azure Key Vaults provisioned (4 subscriptions). Commit `fc22007`. (2026-05-14)
- [[phase-1b-credential-submission]] — Azure Functions + Key Vault + OAuth callback (5-min fix). `/launchpad-phase1b` **QA Deployed 2026-05-21** — 8 functions live at `func-aldc-cred-qa.azurewebsites.net`, Key Vault at `aldc-cred-vault-qa`, E2E verified. **Moving to Completed.**
- [[phase-1d-automation]] — Reminder chains, health monitoring, Windsor auto-verify. Deferred.

### Completed
- [[phase-1b-credential-submission]] — Azure Functions + Key Vault + OAuth callback (5-min fix). 8 functions, QA deployed + E2E verified. `/launchpad-phase1b` (2026-05-21)
- [[phase-4-analytics-stack]] — Analytics stack: dbt (43/43 QA), Superset on Azure ACI, Cube semantic layer, 14 charts in 2 dashboard templates, CLI `--superset-url`. `/launchpad-phase4` (2026-05-14)
- [[phase-2-connector-activation]] — Full connector activation pipeline: 10 API endpoints, 9 services. One-click from dashboard: credential → Snowflake env → deployment → test run → data verification → parity → robustness. `/launchpad-phase2` (2026-05-14)
- [[phase-1c-prefect-provisioning]] — One-click Key Vault → Prefect Block provisioning. REST API approach, full validation suite, env checkmarks. `/launchpad-phase1c` (2026-05-14)
- [[phase-1a-credential-dashboard]] — Credential tracking dashboard + client boards + client selector. DEMO-READY (all 7 deliverables complete). `/launchpad-phase1a` (2026-05-14)
- [[phase-0c-connector-framework]] — Migration catalog (50 connectors), deploy modal, framework/env/credential filters, freshness monitoring, Prefect UI link. `/launchpad-phase0c` (2026-05-13)
- [[phase-0-monorepo-restructure]] — Monorepo created, ops-platform migrated, submodule added. `/launchpad-phase0r` (2026-05-13)

_(Also inherited from ops-platform POC — see [[../ops-platform/README]] for legacy Phases 0-2)_

### Backlog
- [[phase-client-portal]] — Client Portal: per-client SPA at `portal.analyticlabs.io/{client}`. Magic link auth (HMAC 30-day sessions), embedded Superset dashboards (guest tokens + RLS), Zeus Chat with conversational chart builder (Cube API → inline charts → style picker → save to library → compose dashboards), credential status, data health, roadmap. `/launchpad-client-portal` **Code built 2026-05-14** — 14 new files: `api/portal-auth/` (8 endpoints), `platform/portal/` (SPA shell + 6 pages), `superset/client.py` (guest token method), CLI `PortalConfig`. Dev mode tested at localhost:4280. Pending: Azure Functions deploy, Zeus API wiring, Superset guest token E2E.
- **E2E Demo Flow** — Run a full onboarding-to-implementation demo end-to-end from Launchpad: prospect → onboard wizard → credential collection → connector deploy → warehouse provision → dbt build → Superset dashboard → portal access. One golden path through the entire platform for live demos. **Master dashboard demo prep complete 2026-05-14** — nav reorganized into Demos + PoC dropdowns, Hub rebuilt with story metrics + sparklines, Launchpad Roadmap + Portal Adjustments + Architecture pages added, SPA shell fix (`21d6859`) unblocked all PoC onclick handlers, connector deploy now discoverable inline. Remaining: live activation API wire-up + portal endpoint deploy + E2E walk-through.
- **UI/UX Restructure** — Redesign the master dashboard site layout and navigation. **Substantially complete 2026-05-14** — nav restructured (brand mark + Hub + Demos dropdown + PoC dropdown with active-section indicator), `.flashy-*` design tokens added to `styles/base.css` (hero, sparkline, dropdown, modal, toast, pulsing live dot, shimmer progress, animated count-up), new pages (hub / roadmap / portal-adjustments / architecture) adopt the design language. Per-page polish on remaining PoC pages (engineering dashboard, credentials detail, prospects) deferred — they inherit `.flashy-*` via `base.css` but don't yet use the tokens directly.
- **Live Connector Deployment** — Deploy a connector end-to-end from Launchpad dashboard: select connector → configure → provision Snowflake env → register Prefect deployment → trigger flow run → verify data lands → promote to production. Wires the Phase 2 connector-activation API into a working dashboard flow. **UI complete 2026-05-14** — Quick-Deploy banner + inline Action column on every row + animated 6-step deploy modal (`pages/connectors/index.html`, commit `87a807b`). Runs against mock pipeline (`USE_MOCK_API=true`). To wire to the live Phase 2 activation API: set `window.ACTIVATION_API_URL` before page load (e.g. via the SPA shell or `<script>window.ACTIVATION_API_URL='https://...';</script>` in `index.html` before the connectors page loads).
- Existing Client Migration — Navira + Fusion92 onto new onboarding framework (warehouse migration scaffolding created 2026-05-13: audit + grants + schema scripts for both clients)
- Zeus Deep Integration — (re-scoped from ops-platform Phase 6)
- E2E Testing — **Phase 7a smoke test complete 2026-05-15.** TestCorp synthetic client created, SPA golden path validated (21 pages), CLI last-mile gaps closed (wizard adapter + dry-run + credential links), `build_block_data` Snowflake stub fixed. Remaining: credential portal UI, live Snowflake provisioning, Superset E2E, security review.

## Session Log

### 2026-05-21 — Client credential portal live + Amazon UK OAuth E2E verified

- did: Built and deployed Navira client credential portal for meeting. **Portal**: `staldccredqa.z9.web.core.windows.net/dashboard.html` — 12 GEP credentials, HMAC token auth (30-day), status badges, Jira refs, progress bar, mobile responsive. **OAuth flow**: Amazon LWA adapter updated with regional endpoints (NA/EU/FE). Amazon UK uses `api.amazon.co.uk` token endpoint + `advertising-api-eu.amazon.com` profiles verification. Full E2E tested: portal → Authorize Now → Amazon EU login → callback exchanges code in ms → verified → Key Vault → redirect to dashboard. **5-minute token expiry solved.** **Inline forms**: draft credentials have credential-specific input forms → Key Vault + Jira comment notification. **Credential audit**: cross-referenced all Jira ACCESS tickets (ALDC-140, GP-238/239/240/245). Added 3 missing: Target+ (GP-240), SmartScout (GP-245), Purchasing System (GP-245). Corrected Amazon UK from validated → pending_client (prev auth code expired). 12 endpoints on Function App (was 8).
- status: Portal live and tested. 12 credentials (5 validated, 2 pending, 5 draft). OAuth verified end-to-end. Windsor auth links to add tomorrow.
- next: Add Windsor links, meeting with Navira, UAT/Prod promotion after.

### 2026-05-15 — Phase 7a E2E Smoke Test + CLI last-mile gaps closed

- did: Ran `/launchpad-phase7` — scoped as pragmatic Phase 7a smoke test since platform is at POC maturity (27/100). **TestCorp synthetic client** created in `shared/client-registry.json` and `platform/master/data/state.json` (e-commerce, individual tier, 3 connectors: Google Ads, Shopify, GA4). **SPA golden path:** all 21 routes verified against existing HTML files, 12/21 hydrate from JSON data layer, client selector extended for TESTCORP. **Wizard smoke test:** 6-step flow fully parameterized, generates correct output for any client. Fixed: added GA4 to connector catalog + profiler data, replaced PBI→Superset throughout wizard deliverables. **Warehouse multi-tenant SQL review:** all parameterized, zero hardcoded client names, RLS isolation via secure views + CURRENT_ROLE() is correct Snowflake pattern, deploy.py supports --dry-run. **Credential exchange API review:** substantially more built than expected — 6 HTTP endpoints, HMAC tokens, Key Vault, Prefect blocks, audit logging all implemented. **CLI discovery:** `cli/aldc_onboard.py` already existed with full 9-step provisioning flow — was incorrectly flagged as "gap #1" in initial smoke test. **CLI last-mile gaps closed:** (1) `_adapt_wizard_format()` — transforms wizard JSON to ClientConfig (code→short_code, individual→starter tier, flat sources→DataSource objects, connector auth-type lookup table for 20 connectors); (2) `--dry-run` flag — validates config, prints plan + credential links without touching infrastructure; (3) credential link generation — imports `generate_submission_token` from credential-exchange API, generates HMAC-signed URLs per data source; (4) `CLIENT_BLOCK_SUFFIXES` fix in `function_app.py` — `_get_block_suffix()` with dynamic fallback for new clients; (5) `build_block_data` Snowflake stub fixed — structured `{account, user, role, password, database, warehouse}` instead of flat `{value}`, with JSON secret auto-parsing. **Dry-run verified:** `python -m cli.aldc_onboard --env qa provision TESTCORP.json --dry-run` — parses wizard format, validates ClientConfig, prints 6 provisioning steps + 3 credential collection links.
- decided: Phase 7a scoped as "pragmatic-testable" (per Paul's feedback memory) — validate what exists, surface gaps as tracker work. CLI dry-run is sufficient validation without live Snowflake connection. Tier mapping (individual→starter) handled in adapter, not in Pydantic enum (keeps model clean, adapter is the boundary). Block suffix derivation: `client_code.lower().replace("_", "-")` is the fallback for any new client.
- status: Phase 7a complete. Committed `9cf1cfb` (10 files, 512 insertions). SMOKE_TEST.md written. All code gaps resolved. Remaining blockers are infrastructure only.
- next: Pick up in a fresh session. Three options: (1) Credential portal UI — `connect.analyticlabs.io` HTML/JS submission form (backend fully built, needs the client-facing page where HMAC links resolve); (2) Live Snowflake provisioning — run `aldc onboard provision TESTCORP.json --env qa` for real against QA (dry-run verified, needs SNOWFLAKE_USER/PASSWORD env vars); (3) Superset E2E — provision a TestCorp dashboard via `portal_provision.py` (Superset already deployed to QA at `superset-qa-aldc.canadacentral.azurecontainer.io:8088`).

### 2026-05-15 — Session Orchestrator built + debugged (autonomous multi-stage pipeline executor)

- did: Built and debugged the [[orchestrator|Session Orchestrator]] system in `scripts/orchestrator.py` + `platform/master/pages/orchestrator/index.html`. **Python HTTP server (port 8765)**: launches `claude -p` subprocesses with `--output-format stream-json`, per-session watchdog timers (with timeout race-condition fix), thread pool (max 4 parallel), git worktree isolation per session (branch: `session/{ticket}-{hash}`), persistent state in `sessions.json`. **Stream-json parser**: real-time text extraction into formatted prose, tool-call chips, three-path usage extraction (`event.message.usage` / `event.usage` / `event.modelUsage`). **Context enrichment pipeline**: pre-loads wiki page + related pages + client registry + credentials + tracker data + prior learnings before spawning session. **Permission model**: worktree sessions skip permissions (the worktree IS the sandbox), non-worktree sessions use auto mode. **UI**: Neurospect-inspired design (glassmorphism cards, pulsing logo glow, Orbitron typography), output tab renders stream-json as formatted prose + tool chips + completion banners. **Bugs fixed**: (1) Windows pipe buffering — switched to binary I/O + manual decode; (2) timeout race — force status to "succeeded" if result event arrived; (3) usage extraction — added `_extract_usage()` covering all three nested paths; (4) UI logic — cancelSession was PATCH not POST, launchSession fired twice. **15 pipeline types identified** (not yet implemented) — connector credential retrieval, Prefect implementation, Snowflake warehousing, bug fix, new client onboarding, existing client migration, Azure provisioning, Eclipse→Prefect migration, dbt, Cube, data quality, CI/CD, incident response, credential rotation, documentation sync. Each pipeline type = DAG of reusable stages; each stage = one Claude Code session in a worktree; each pipeline run creates a PR at completion. **Next step**: Opus plan-mode session to design the pipeline DAG system (15 types as templates).
- decided: Worktrees are the security boundary — no permissions needed. Stream-json is the right abstraction (captures both text + tool calls + costs in structured form). Context enrichment via wiki + Zeus avoids re-scoping every session. UI displays prose not JSONL (better UX).
- status: Orchestrator system fully operational (local test complete). Wiki page created at `entities/tools/orchestrator.md`. Ready for integration testing with real pipeline types.
- next: Design the pipeline DAG system (15 types) via Opus plan-mode. Once approved, build the first 3 pipeline types as proof-of-concept (connector credential retrieval, Prefect implementation, bug fix).

### 2026-05-14 — Master dashboard overhaul + SPA shell button fix (e2e demo prep)

- did: Rebuilt platform/master/ for the e2e onboarding demo. **Nav:** replaced flat topnav with brand mark + Hub + Demos dropdown + PoC dropdown (animated open/close, active-section indicator). Demos: Vision, Onboarding, Tracker, Connector Deploy, Navira, Client Portal (external), Architecture, Launchpad Roadmap. PoC: Platform, Engineering, Progress, Prospects, Credentials, Boards, Fusion92, Portal Adjustments, Framework, Guide, Infra, Eng Onboarding. **Hub:** animated hero with Launchpad build %, 6 metric tiles with inline SVG sparklines + count-up animations + delta badges, tabbed bar chart (Connectors/Credentials/Onboarding) driven by data layer, recent activity stream, client health cards, quick-action cards. **New pages:** `pages/launchpad-roadmap/` (13 expandable phase cards, animated overall % counter, on-track banner), `pages/portal-adjustments/` (3-lane kanban, modal form, localStorage + JSON seed), `pages/architecture/` (SVG diagram with animated flow edges, clickable node detail modals, components grid). **base.css:** added full `.flashy-*` token set (gradient text, hero, card lift, sparkline, shimmer progress, pulsing status dot, dropdown menu, modal, toast). **SPA shell critical fix:** replaced `new Function(code)()` script execution with real `<script>` element injection — top-level `function foo()` now reaches window so every inline onclick across all PoC pages works. Also handles external `<script src="">` (tracker's prioritize.js) resolved relative to page path. Injected scripts tracked and cleaned up on route change. **Connector UX:** added Quick-Deploy banner (grouped dropdown of deployable connectors + primary Deploy button) and inline Action column on every table row (`Deploy →` / `Promote →` / `Redeploy` / `Awaiting cred`) so deploy is reachable without expanding rows.
- decided: Page cache stays disabled (per SPA feedback memory — always refetch). Worktree branch conflict resolved by creating `paulrussell/feature/master-overhaul` off the same base, Paul merged to e2e-onboarding. Local server: `python -m http.server 8765` from platform/master/ via PowerShell (Bash background doesn't inherit path on Windows). "CA connector" = gep-amazon-ads-ca (Amazon Ads CA, status=deploying) — users couldn't find deploy button before the row-action column was added.
- bugs: (1) `new Function(code)()` SPA shell pattern broke all PoC onclick handlers — fixed by real script injection. (2) Connector deploy not discoverable — fixed by Quick-Deploy banner + row Action column.
- commits: bd1bfad (flashy CSS), 923ede3 (nav + hub), 52be54d (3 new pages), 21d6859 (SPA shell fix), 87a807b (connectors UX) — all merged to paulrussell/feature/e2e-onboarding via 804b72e.
- status: Master dashboard demo-ready. Server running at http://127.0.0.1:8765/. All nav routes resolve. All onclick handlers functional.
- next: Demo the e2e flow. After demo — wire the real activation API URL so connector deploy hits the live endpoint (currently USE_MOCK_API=true). Deploy portal-auth Function App to Azure.

### 2026-05-14 — wiki-sync: Step 11 complete (B7-PBI production deployer + rollback)

- did: Replaced `cli/deployers/pbi.py` placeholder with full Hybrid deployer (XMLA schema writes via TOM wrapper + REST refresh/validate). Built `cli/deploy_pbi.py` standalone PBI deploy CLI (BIM snapshot, schema generation from dbt via `pbi_schema_gen.py`, XMLA apply, REST refresh + poll, DAX validation, parameter updates, deploy receipts). Built `cli/rollback_pbi.py` standalone PBI rollback CLI (BIM restore via XMLA, 24h rollback window, prod guard, post-rollback refresh, rollback receipts). PBI deployer integrates into B7 orchestrator — loads env-aware workspace config from `pbi_config.yaml` (qa/uat→test, prod→prod), auto-finds schema scripts in ticket dirs.
- status: Steps 1-11 complete. All Engineering Tracker + Development Platform code artifacts built. Only Step 12 (wiki sync + demo prep) remains. PBI eval harness run still blocked on sandbox IDs in `pbi_config.yaml`.
- next: Step 12 wiki sync (done). Fill sandbox IDs and run PBI eval harnesses independently.

### 2026-05-14 — wiki-sync: Engineering Tracker Steps 6-9 complete (B4-B7 pipeline)

- did: Built the remaining pipeline stages and deployment system in two sessions. **Steps 6-8 (B4/B5/B6):** `cli/platform/b4_test.py` — auto-generates test plans from git diff with 14 area classification rules (dbt, Snowflake, API, UI, Cube, Superset, etc.), area-specific test generators with real commands, per-test pass/fail/skip tracking. `cli/platform/b5_pr.py` — assembles PR title/body from pipeline artifacts (brief.md + plan.md + test-report.json + deploy receipts), reviewer lookup from `.claude/code-owners.json`, wraps `gh pr create`. `cli/platform/b6_cr.py` — creates CR tickets linked to parent features, computes scope delta (new/modified files + effort estimate), three resolution modes (absorb/defer/split), `pending_crs` on parent for UI banner. **Step 9 (B7):** `cli/deploy.py` orchestrator — detects changes from git diff, dispatches to 8 sub-deployers in dependency order (Snowflake→dbt→Cube→Superset→PBI→Functions→UI→Prefect), captures rollback snapshots BEFORE each step, halts on first failure, writes deploy receipts. `cli/rollback.py` — reverses in inverse order of completed steps, 24h rollback window with `--force --reason` override, production guard. PBI sub-deployer is a placeholder pending eval (Steps 10-11).
- status: Part B pipeline fully operational (B1-B7 + rollback). 10 new Python modules across `cli/platform/` and `cli/deployers/`. Only PBI eval (Steps 10-11) and smart prioritization (deferred A8) remain.
- next: Steps 10-11 — B7-PBI evaluation (XMLA/REST/Hybrid harnesses against GEP Sandbox), then winner → `cli/deploy_pbi.py`.

### 2026-05-14 — Client Portal: code built (14 files, SPA + auth backend + Zeus chart builder)

- did: Built the full Client Portal in one session. **Auth backend** (`api/portal-auth/`): 8 Azure Function endpoints — invite (magic link), auth (validates + sets session cookie), session (returns client config from HMAC token), superset guest-token (generates Superset guest token with RLS), zeus config/chat (proxied, API key never in browser), cube query (proxied with client_id injected into Cube security context), data-health. HMAC session tokens with 30-day TTL, `PORTAL_HMAC_SECRET`, httpOnly + Secure + SameSite=Lax cookies. **Superset integration**: added `create_guest_token()` to `superset/client.py` (POST `/api/v1/security/guest_token/` with dashboard UUID + RLS clause), updated CORS to allow `portal.analyticlabs.io`. **Portal SPA** (`platform/portal/`): shell with auth gate, hash routing, client branding from registry accent color, dev mode bypass for localhost. 6 pages: analytics (Superset iframe + 4-min token refresh), Zeus Chat (conversational chart builder — style picker [bar/line/pie/area/table], save chart, add to dashboard, compose multi-chart dashboards, save to library), credentials (status table + submission link), library (full-page chart/dashboard gallery with mini preview renderings + dashboard drill-in view), data-health (connector freshness cards), roadmap (vertical timeline). **CLI**: added `PortalConfig` to models.py. **Registry**: expanded portal + zeus fields in client-registry.json.
- decided: Magic link auth over Azure AD B2C (extends existing HMAC pattern, no database needed). Zeus Chat as conversational dashboard builder (client asks question → Cube query → chart → pick style → save → compose dashboards). Chart/dashboard library in localStorage per client (simple, no backend storage needed for v1). `portal.analyticlabs.io/{client}` single-domain with path routing (not subdomain per client). Dev mode auto-detected on localhost (skips auth gate).
- status: Client Portal code complete. Dev-tested at localhost:4280. Pending: Azure Functions deploy, Zeus Memory API wiring (chat currently returns placeholder), Superset guest token E2E (needs dashboard UUID in registry), Cube API deployment.
- next: Deploy portal-auth Function App to Azure. Wire Zeus Chat to real Zeus Memory API. E2E test with GEP: invite → login → analytics dashboard → Zeus data query → save chart.

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
