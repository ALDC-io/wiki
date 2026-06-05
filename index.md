---
tags: [index, navigation]
updated: 2026-06-01
last_ingest: 2026-04-27
last_runbook_update: 2026-04-24
---

# Wiki Index

Master catalog of all wiki pages. Search here to find relevant pages.

---

## Action Items

- [[action-items]] — central TODO registry. Populated automatically from daily notes (explicit `type: action` + prose heuristics) and manually. Complete by ticking the checkbox and moving to Done.

---

## Potential Tickets

- [[potential-tickets]] — pre-Jira catalog of gaps, bugs, and improvements surfaced while working on other tickets. Each entry has enough detail to file a Jira ticket directly without rediscovery. Different purpose from [[action-items]] (which is personal TODOs).

---

## Entities

### People
- [[erik-johnston]] — AI Engineer candidate (interview 2026-05-08). Next.js/React/TS strength; complementary hire analysis (7.55/10). Scenario-based interview questions mapped to ALDC use-cases.

### Clients — Active
- [[GEP]] — E-commerce analytics client (Navira). Amazon US/UK/CA, SellerCloud, Galactica. 14 connections, 62 templates, 37 warehouse views.
- [[fusion92]] — Media activation client. Meta, Google, Viant, Trade Desk, Amazon Ads. 11 connections, 50+ templates, 10 warehouse views.

### Clients — Inactive
- [[adm]] — ADM marketing dashboard. Fusion92 sub-client. GCP-native stack: BigQuery, Looker Studio, Funnel.io, Google Analytics.
- [[dish-duer]] — Dish & Duer Apparel Inc. Retail client (SAP + Shopify). Finance + Sales models. Full dimensional model spec.
- [[kit-ace]] — Kit and Ace Technical Apparel Inc. Retail client (NetSuite). Finance model (OLS: Inventory + Finance roles) + Google Analytics integration.
- [[book-depot]] — Book Depot. Wholesale book distributor. Standard Retail Dimensional Model. Requires IPSEC VPN (CUST-202).
- [[terrayn]] — Terrayn. Cannabis retail client. AWS Athena data source; creds in vault.
- [[aspire-north]] — Aspire North. Early-stage engagement (2022-12 kickoff only).
- [[indochino]] — Indochino Apparel Inc. Custom apparel; detailed 2021 architecture assessment (SQL Server, SSIS, 12 recommendations).
- [[drop-in-gaming]] — Drop In Gaming. Gaming/tournament platform. 2022-11 discovery phase.
- [[heartland-dental]] — Heartland Dental. (Empty Confluence page — no content ingested.)

### Repos
- [[clients-repo]] — Primary ALDC repo. Per-client Eclipse configs + Snowflake warehouse SQL. 19 active clients, 150+ connections, 300+ templates, 200+ warehouse views.
- [[aldc-shipyard]] — Workflow automation infrastructure + **ALDC Launchpad** (Client Operations Platform at `ops-platform/`). Deploy/validate scripts, PBI XMLA wrapper, onboarding wizard, prospect intelligence, infrastructure planner, engineering dashboards. Renamed from `aldc-automation` 2026-04-29.
- [[eclipse_exp]] — Next-gen ALDC platform. Contract-first, AI-native, multi-tenant. FastAPI + Next.js 15 + PostgreSQL RLS. 50 connectors, 87 migrations, AI onboarding, strangler-fig migration from [[Eclipse]] + [[core_api]].
- [[entities/repos/eclipse|eclipse (repo)]] — Legacy Next.js 14 (Pages Router) portal UI. Auth, account management, connection/template config, iframe app hosting. Every API call proxies to [[core_api]]. Being replaced by [[eclipse_exp]]. *(Note: [[Eclipse]] = platform concept page; this = UI repo page.)*
- [[core_api]] — ALDC core API service. Eclipse backend (control plane). Hosts warehouse-rebuild functions; reads Eclipse configs from CosmosDB.
- [[connector]] — Data-plane repo (legacy). Pulls from sources → Azure Storage → Snowflake via on-prem Docker agents. Still live in production — do NOT archive. Prefect migration ongoing.
- [[prefect-connectors]] — New Prefect v3 data-plane repo (`ALDC-io/prefect-connectors`). Forked from `connector` 2026-05-01. Branches: `main`/`uat`/`development`. Docker image: `ghcr.io/aldc-io/prefect-connectors`. Smoke test COMPLETED 2026-05-01.
- [[custom-fusion-92-audience-api]] — Fusion92 DIOS-to-DAX audience-data-formatter API. FastAPI + Gunicorn + pandas. 14 platforms, 17 FileSpecifications. On-prem Docker + Nginx + Cloudflare DNS (proxying disabled). 60 GB-memory requirement blocks cloud migration.
- [[entities/repos/flight-check|flight-check (repo)]] — Next.js 16 frontend for the [[dax-media-app|DAX Media App]]. Iframes into the Eclipse portal; proxies to core_api, DAX API, DIOS, and F92 NetSuite Workflow. *(Not the [[flight-check]] ops runbook.)*
- [[entities/repos/claude_code_enhanced|claude_code_enhanced (repo)]] — ALDC's Claude Code Enhanced toolkit. 20-hook runtime enforcement system, 195-skill library, `cce` Bash launcher (8-phase startup with auto-update + auto-learn), Zeus Memory integration, project-template CLI. Companion to [[cce]] (project page).
- [[workflows]] — Azure Functions + Python backend for [[dax-media-app|DAX Media App]]. DAX API (12 HTTP routes), NetSuite PO sync, Microsoft Ads token refresh, notification cron jobs, Snowflake sync. `fusion_92/F92_workflow_app` is the production app; two one-shot Cosmos migration scripts alongside.
- [[entities/repos/prospect-site-template|prospect-site-template]] — Next.js 15 template for ALDC prospect microsites (15 deployed sites at `*.analyticlabs.io`). One config file drives three templates (landing / dashboard / pitch). Claude Code generates `site.config.ts` from a natural-language prompt; template folder copied per site and deployed independently (Vercel). Optional AI chat proxy to Anthropic + [[zeus-memory]] logging. Future home: [[eclipse_exp]] (planned `prospect-created` webhook will absorb site generation into the platform onboarding flow).
- [[aldc-scripts]] — Grab-bag of internal ALDC utility scripts (Python + Bash). Fusion92 ticket-status PDF generator (Airtable → PDF), generic Slack-webhook helper, and the weekly corporate cost-monitoring dashboard (Azure 9 subs + GitHub aldc-io + Anthropic → `#the-olds` Slack). Runs via cron on Server4; no CI/CD. **Status: likely legacy — verify before relying on.** Candidate for future absorption into [[Prefect]] flows or [[eclipse_exp]] ops dashboards.
- [[entities/repos/power_bi|power_bi (repo)]] — Binary-artefact store for ALDC's Power BI reports. ~94 `.pbix` files + 3 `.pbit` templates + 6 CosmosDB report-JSON companions, Git LFS (~16 GB), no code. Organised `common/` (Retail starter set), `custom/<CLIENT>/` (bespoke, dated snapshots), `internal/`, `sales/` (pre-sales demos), `templates/` (stale; canonical copies in Nextcloud). Active clients: GEP (20 snapshots, 2026-03 latest), Fusion92 (13 snapshots, 2025-12 latest). Legacy: DISH_DUER, BOOK_DEPOT, KIT_ACE, ALDC_FINANCE. No CI/CD; all deploys are manual Publish from Power BI Desktop — see [[gep-snowflake-pbi-deployment]] / [[model-deploy-production]]. For Power-BI-the-tool see [[entities/tools/power-bi|Power BI (tool)]].

### Tools
- [[orchestrator]] — Session Orchestrator (ALDC Launchpad). Autonomous multi-stage pipeline executor — launches isolated Claude Code sessions in git worktrees, manages concurrency, monitors execution, surfaces results via web UI. 15 pipeline types identified (connector credential retrieval, Prefect implementation, Snowflake warehousing, bug fix, new client onboarding, existing client migration, Azure provisioning, Eclipse→Prefect migration, dbt, Cube, data quality, CI/CD, incident response, credential rotation, documentation sync). Context-enriched sessions (wiki + client registry + credentials + tracker data + prior learnings pre-loaded).
- [[Snowflake]] — Data warehouse. Star schema with shared_dim_*, *_fct_*, extract_*, report_common. Manual deployment.
- [[Eclipse]] — Connector platform. JSON-based connections + templates. Pulls from APIs/DBs, loads into Snowflake.
- [[Power BI]] — Reporting layer. Consumes report_common views. Refresh cadence per semantic model (GEP Test: scheduled daily; ad-hoc refresh available). See [[Power BI]] § Model Refresh.
- [[Prefect]] — Workflow orchestration replacing Eclipse. PRE-000 migration: 47 legacy connectors to Prefect flows.
- [[prefect-v3-reference]] — Prefect v3 core concepts reference (flows, tasks, blocks, work pools, deployments, schedules, states). Extracted from official docs.
- [[prefect-v3-patterns]] — Prefect v3 development patterns (retries, caching, concurrency, testing, logging, secrets, Docker/ACI deployment). ALDC connector checklist.
- [[Azure]] — Primary cloud host. Subscriptions = environments. Hosts web apps (Eclipse, core_api), CosmosDB, storage accounts, function apps.
- [[CosmosDB]] — Azure NoSQL store for Eclipse connection/template configs. `schema` container is a common source of stale-template bugs.
- [[Cloudflare]] — DNS and domain registration. All hosted sites' CNAMEs live here; most point to Azure web apps.
- [[Postman]] — API client for reproducing and debugging Eclipse template calls during warehouse-load investigations.
- [[SSMS]] — SQL Server Management Studio. Edits intermediate SQL Server DB between Snowflake and PBI (GEP partition runs, reprocessing old data).
- [[Confluence]] — Team wiki. Holds detailed dataflow diagrams, per-client SSMS setup, Prefect/Azure docs (Brayden's offboarding space).
- [[Windsor]] — Windsor.ai marketing data aggregation. Used by Fusion92 + GEP/Navira; Eclipse pulls via `windsorai_v1`. Auth + account management documented. Field-selection gaps (revenue not selected by default), row-splitting gotcha, cross-client account caveat.
- [[proxmox]] — Proxmox VE hypervisor: host administration, guest provisioning (Windows/Linux), disk expansion, vGPU (NVIDIA M40) setup.
- [[mailjet]] — Mailjet email service: API credentials, Python integration, @aldc.io sender domain.
- [[dashboard]] — Eclipse Dashboard feature: CosmosDB dashboard/dataset documents + Postgres report row. Synapse analytics integration.
- [[nextcloud]] — ALDC Cloud file sharing. Syncs Client_Tenants assets to Agent VMs. 16 users (internal + clients). Preferred pattern: cluster-level Samba relay.
- [[GitHub Actions]] — CI/CD. Manually triggered "Deploy to Azure (Staging)" builds + pushes container + deploys to staging slot; manual swap promotes to prod.
- [[postman-collections]] — Collection catalog + canonical clean workspace design (team workspace, renamed collections, 4 envs, auto-bearer pre-request script, variable-placement rules, env-precedence gotcha). Extractor/generator at `vault/postman-build.py`.

### Projects
- [[dax-media-app]] — DAX Media App (Flight Management web app for Fusion92). Replaces legacy Firebase Flight Check app. Built on Eclipse 2.0. Phases 1–2, PRJ505/538/537, NetSuite PO sync.
- [[dax-ai]] — DAX AI dashboard suite for Fusion92. Activation Model (client testing), Performance Summary + Financial Reporting (ON HOLD), External Dashboard (deferred).
- [[cce]] — Claude Code Enhanced. Auto-updating wrapper with hooks, Zeus memory integration, and cross-machine messaging.
- [[observability-platform]] — Lightweight, company-wide observability & monitoring platform (3-plane self-host: Uptime Kuma + Prom/Grafana + Python job-health + obs-api + Mailjet→Jira). Week 1 complete 2026-04-25.
- [[factoria]] — Autonomous data engineering platform. Docker runner-split architecture, agent operating model.
- [[ai-driven-dev-workflow]] — AI-assisted development workflow research. Multiple versions (v2, v3, v3.1). ALDC Agentic Coding Guidelines.
- [[zeus-memory]] — Zeus Memory (OpenTribe) product. Knowledge integrity platform: cross-source drift detection, auto-sync proposals, human approval. Streamlit prototype built against Lululemon use case.
- [[phaselab]] — PhaseLab. AI prototype exploration product: brief → spec → multi-variant generation → evaluator → review. Demo-ready (Phase 0). Phase Forge execution layer planned.
- [[cpma]] — Early-stage product concept exploring continuous product iteration via real-time user feedback loops and regulatory change management.
- [[monorepo-research]] — Monorepo + CCE Integration analysis. 38 improvements across 8 categories. Research complete, pending decision.
- [[openclaw]] — Open-source agent runtime/gateway used by Factoria. Multi-agent isolation, tool policy enforcement, session management.
- [[workflow-automation]] — Client Workflow Automation — design for automated sandboxed feature-delivery flow targeting GEP. Phase-1 sandbox pattern + phased build roadmap.
- [[neurospect]] — NeuroSpect. AI trading intelligence platform for ICT/Smart Money traders. 13-component architecture: Trader Workspace, Prop Shield, ICT Event Engine, EdgeLab, Mentor, Edge Forensics, NeuroCore, NSLM, NeuroGraph, NeuroScore, NeuroFund Elite, NeuroQuant, NeuroTrader. v3 roadmap (13 phases, data-first). Orchestrator UI with autonomous pipeline. **Stage: Phase 0 active, marketing site live.**
- [[devflow-os]] — Developer Workflow OS. All-in-one dev workflow platform: roadmap viz, boot prompt generation, cross-engineer intelligence, change management, ticket tracking. Built as internal tooling for NeuroLLM, extractable as standalone product. **Stage: idea.**

---

## Concepts

### Business Logic
- [[gep-inventory-data-dictionary]] — Column-by-column reference for `INVENTORY_FCT_BALANCE` and `EXTRACT_INVENTORY_CURRENT`.
- [[periodicity]] — ALDC periodicity system: SHARED_DIM_PERIODICITY Snowflake view + DAX SWITCH dispatch pattern for MTD/YTD/YoY/etc. in Power BI models. Sources, validated FBA identities (TOTAL and WAREHOUSE formulas), placeholder columns, and out-of-scope items.

### Architecture
- [[observability-architecture]] — v1 design: component diagram, data flows, full alert system (throttle/escalation/recovery/grouping/blast-radius/staleness), OBSERVABILITY.JOB_RUNS schema, fate-sharing mitigations, rejected alternatives. Week 1 complete 2026-04-25.
- [[data-pipeline-flow]] — End-to-end: Eclipse/connector → Azure Storage → Snowflake source schemas → WAREHOUSE_SOURCE → WAREHOUSE → REPORT_COMMON → (SQL Server) → Power BI.
- [[cross-channel-marketing-attribution]] — Tiered marketing measurement model (platform ROAS → blended MER → product-grounded → causal). Why platform-attributed value isn't truth; the `MARKETING_EFFICIENCY` reconciliation view tying spend to actual orders. Drives a follow-on ticket beyond [[GP-225]].
- [[flight-check-engineering-guide]] — Consolidated engineering + onboarding guide for the Flight Management app (DAX Media App). Synthesises [[entities/repos/flight-check|flight-check]] + [[workflows]] + [[dax-media-app]] with architecture/data-flow Mermaid diagrams, full integration table, and an end-to-end local dev setup walkthrough.
- [[repo-integration-map]] — Cross-repo map of ALDC's 12-repo estate: current data flow, dependency graph, strangler-fig overlay (eclipse_exp absorption + Prefect migration), and per-repo integration notes.
- [[azure-environments]] — Subscription-to-environment mapping (Production 2, TEST 1, Quality 1, Development 2, QA for Prefect, etc.). Deployment-slot flow. Access state.
- [[deployment-groups]] — Per-environment Azure resource inventory for Canada DGs (Prod2, QA1, Test1, Demo1, Dev DG1–4). Resource names, deployment playbook, credential vault pointers.
- [[cosmosdb-schema]] — core_api CosmosDB collection schema reference: account, capacity_provider, capacity, agent, work_connection, work_template, work_partition, task, staff, report, schedule, session.
- [[core-api-data-model]] — core_api v1 domain model (2021): routine, schedule, session, schema, merge strategies, history tracking. Predecessor to cosmosdb-schema.
- [[local-network]] — On-prem: Nginx reverse proxy (NPM + Cloudflare DDNS), TrueNAS/Covenant storage (30 TiB, Surrey), Tailscale VPN (kookiet subnet router).
- [[star-schema-convention]] — ALDC naming: shared_dim_*, *_fct_*, extract_*. SHA2 keys, currency triple pattern, common SQL patterns.
- [[prefect-cost-analysis]] — Prefect Azure infrastructure cost model: actual SKUs (P2v3, D2ads_v5, 3x Container Apps), right-sizing recommendations (~75% savings), Prefect Cloud comparison, ACI Spot analysis. 2026-05-03.
- [[workflow-analysis-current-vs-future]] — End-to-end feature delivery workflow analysis: current state diagrams, gap analysis (17 gaps across Snowflake/PBI/Prefect/cross-cutting), future state target, three implementation options (Incremental → Data Quality Platform → Full CI/CD).
- [[snowflake-data-share-refresh]] — Producer `CREATE OR REPLACE TABLE` semantics across a data share: atomic within producer DB, transparent handoff to name-referencing consumers, mitigation options for transient failures.
- [[accumulating-source-tables]] — `CURRENT_REPORT_*` and `CURRENT_MAIN_*` tables retain multiple ingestion batches per key; dedup required at read time. Includes moving-target QA workflow (drift diagnostic, acceptable tolerance).
- [[connector-timeout-outage]] — Post-mortem: `/work/pick` Azure Function timeout caused by O(N_accounts x N_connections) global queue sweep. Short-term and long-term fixes documented.
- [[fusion92-platform-ids]] — Platform account/campaign/order ID mapping for Fusion92 Flight Check. Format rules, matching logic, overlap caveats, Google Ads vs SA360 precedence.
- [[fusion92-data-architecture]] — Fusion92 Snowflake setup decisions (Azure, Standard Edition, account structure, implementation checklist) + DIOS→DAX→DSP audience integration flow.

### Patterns
- [[client-repo-structure]] — Standard folder layout: eclipse/ (connections + templates) + snowflake/ (warehouse + report_common + data_share).
- [[data-share-pattern]] — Snowflake-to-Snowflake sharing: outbound (ALDC → client) and inbound (client → ALDC). Setup steps, secure view rules, fallback to file stage.
- [[cce-troubleshooting]] — Known issues and fixes for CCE: settings.local.json parsing, Windows path bugs, Zeus API key, poller daemon startup.
- [[python-development-standards]] — ALDC Python conventions: PEP 8 (with spaces-around-operators exception), Google docstrings, VS Code + PyLint + Azure extensions. Applies to core_api, connector, and internal tooling.
- [[git-branching-strategy]] — Per-client `<CLIENT>/development` → `<CLIENT>/user-testing` → `main` model. Happy-path walkthrough + cheatsheet for routine changes, user-test-fixes, and hotfixes-to-prod. Plus commit-message format (`<Jira-ID>-<WorkTitle>`) and semver release conventions.
- [[ai-development-project-standard]] — ALDC's tracking standard for AI-developed projects (>50% AI). Mandatory header (tokens, cost, time, model, last-updated), ROI template, 🤖 tagging. Established 2025-05-28.
- [[ai-pr-workflow]] — ALDC definitive PR workflow: Jira → branch → CCX → PR → Semgrep + TruffleHog + Claude Opus review + PyTestArch → code owner → merge → auto-deploy. All checks live as of 2026-04-10. Bypass list empty.
- [[connector-token-refresh]] — OAuth token refresh runbook. Bing Ads 90-day cycle (automated daily + manual PowerShell). Facebook 60-day long-lived token.
- [[connector-development-standards]] — Canonical ALDC/Prefect connector pattern: typed attribute hierarchy (ConnectorConnectionBase/OptionsBase), migration steps, PartitionScheme/MergeScheme selection, reference implementation.
- [[sandbox-feature-delivery]] — Per-feature Snowflake schema pattern (`WAREHOUSE_TEST_<TICKET_ID>`) for isolating in-flight warehouse changes. PBI workspace creation now automatable via PowerShell (updated 2026-05-02).
- [[snowflake-environment-provisioning]] — Idempotent Snowflake provisioning pattern: databases, service accounts, grants via Python. Role hierarchy, Git Bash path gotchas, utility scripts. Extracted from GP-248.
- [[pbi-xmla-automation]] — Programmatic PBI metadata changes via XMLA + TOM + Roslyn (`pbi_model_apply.exe`) + Snowflake-schema-derived column generator. The PBI sibling of sandbox-feature-delivery; validated end-to-end on GP-208 2026-04-24.
- [[adversarial-investigation-skill]] — `/investigate-adversarial` Claude Code skill (Vlad). 6-phase adversarial protocol: ANCHOR → OUTSIDE-IN → FORENSIC EVIDENCE → PROVE/DISPROVE/BLIND-SPOT → QUANTIFY → CONVERGE. For bugs, arch decisions, tech evals, concept validation.

### Connectors (entities/tools/connectors/)
- [[google-analytics]] — GA4 + Universal Analytics connector. Connection string schema, options dict, Python libraries, service account setup.
- [[facebook-ads]] — Facebook/Meta Marketing API connector. 5-credential OAuth setup, long-lived token (~60 day expiry), Business SDK object hierarchy.
- [[bing-ads]] — Microsoft Advertising connector. Azure App Registration OAuth2, 90-day refresh token lifecycle, automated daily refresh workflow.
- [[google-ads]] — Google Ads connector. 4-credential model: Developer Token + OAuth Client ID/Secret/Refresh Token. Approval process ~1-2 weeks.
- [[amazon-ads]] — Amazon Ads + DSP connector. Centralized ALDC OAuth app + per-client refresh tokens. DSP advertiser IDs currently manual (beta API).
- [[trade-desk]] — The Trade Desk My Reports API. Stateful workflow: schedule → execution → download. Backdating, schedule limits, warehouse reset procedure.
- [[google-oauth-python]] — Pattern for Google OAuth in Python (`google-auth-oauthlib`): auth URL generation, token exchange, refresh-token usage with Google Ads client. Used across Google-adjacent Eclipse connectors.
- [[aldc-naming-convention]] — Multi-part naming for all ALDC resources: Azure `aldc<env><type><func><group><region><seq>` (e.g. `aldcprodfnapcore1c01`) and on-prem `aldc<env><type><cluster><seq><acct><func>`. Plus named-VM inventory (Galactica, Normandy, etc.) with hostnames only — credentials in `vault/infra-credentials.md`.

---

## Processes

### Deployment
- [[prefect-connector-deployment]] — Runbook for running Prefect connectors locally, deploying to Azure, and switching environments (QA/Test/Prod). Covers auth, Docker build/push, Work Pool env vars, and per-deployment environment override.
- [[model-deploy-production]] — Production model deployment checklist: connections/templates, Snowflake views, PBI publish, client user access grant.
- [[gep-snowflake-pbi-deployment]] — End-to-end GEP deployment runbook: 11 phases from data source registration through production deploy. 7 documented pitfalls with exact error messages and fixes.
- [[pbi-xmla-model-changes]] — PBI model changes via XMLA/Tabular Editor: TE3 CLI hang diagnosis, GEP M expression conventions (PARAM_SHORT_CODE), partition type gotcha, manual workaround.
- [[pbi-model-apply-wrapper]] — Phase 6 Option A plan: thin .NET 8 console wrapper around TOM that runs TE3-compatible C# scripts via Roslyn. Resolves the TE3 CLI subprocess hang documented in [[pbi-xmla-model-changes]].
- [[client-release-checklist]] — Generic client-agnostic release checklist (branch gating, Cosmos prod sync, Snowflake update with data-share re-share, Power BI, Jira/Service Request hygiene).
- [[new-client-setup]] — First-time new-client onboarding runbook (load account/capacity → `setup/azurestorage` → `setup/capacity` → load connections/templates/tasks → create agent → trigger Scan → Snowflake SQL load → Power BI reports → Eclipse groups).
- [[azure-environment-bootstrap]] — End-to-end bringup of a new ALDC Azure environment: Powershell-driven (`deployment.ps1`, `configuration_api.ps1`, `configuration_portal.ps1`), Function App + Portal deploy, storage/capacity setup, authorization + agent creation. Credentials at `vault/infra-credentials.md`.
- [[environment-setup]] — 12-step new developer onboarding: core software, Python venv, Git, Snowflake, Power BI, VPN, Docker agents.
- [[connector-docker-deployment]] — Docker agent build and deploy: SSH to workstation-agent, build.sh, push to GHCR, deploy via Portainer across test/prod/QA servers.
- [[eclipse-azure-deployment]] — Eclipse / core_api web-app deploy via GitHub Actions → Azure staging slot → swap. Must swap frontend AND backend. Swap-back = rollback.
- [[credential-exchange-function-deploy]] — Deploy `func-aldc-cred-qa` (Linux Consumption Python) + the GEP Data Model / Validation Report export. Two traps: `func publish` needs Python 3.11 on PATH (crashes on 3.14), and `config-zip` silently no-ops (use `func publish --build remote`). openpyxl `write_only` mandatory (OOM on Y1). Manual upload fallback via Cosmos `account_secret.storage_sas_1` → blob + Postgres `app_report` bump.
- [[core-api-local-setup]] — Full developer runbook for running core_api locally (Python 3.11 + Azure Functions Core Tools + `local.settings.json` + Postman via `vault/postman-build.py`). Includes curl smoke-test, clean Postman workspace setup, and common-failures table with the Python-3.13-pyarrow trap and the Postman bearer_token precedence trap. Daily driver for any core_api debugging.

### Ticket Lifecycle
- [[ticket-breakdown-to-ship]] — Generic workflow from requirements gathering through deploy and verification. Patterns from GP-200, GP-208, and knowledge transfer sessions.

### Operations
- [[orchestrator-production-readiness]] — 5-phase plan (A-E) to harden the Launchpad orchestrator pipeline for safe connector promotion QA → UAT → Prod. Data validation, deployment, rollback, evidence capture, gate wiring.
- [[flight-check]] — Operational validation process: Eclipse connector health, Snowflake task chain, data freshness, Power BI refresh, data share integrity.
- [[eclipse-incident-response]] — Outage-recovery runbook for Eclipse connectors (power/network/agent loss). Read-only triage via `observability/ops/incident_triage.py` → classify casualties vs noise → canary re-trigger → warehouse verify. Documents the zombied single-`full`-partition queue-drain gotcha. Proven on the 2026-06-01 Kamloops power outage (ALDC-244).
- [[client-deactivation]] — Client deactivation checklist: Postgres users, Eclipse tasks, Snowflake shares, PBI licenses, invoicing stop dates, NextCloud access.
- [[client-vm-setup]] — Setting up a Windows VM (via Parsec) for Mac clients who can't install Parallels.
- [[client-invoicing]] — Three invoicing models: project-based gates, quarterly payment plans (GEP), monthly recurring.
- [[client-communications]] — Email templates: outage/maintenance notifications, data model access onboarding email.
- [[client-onboarding-checklist]] — New client onboarding: KT from sales, technical setup (Eclipse/Snowflake/NextCloud), data connection collection.
- [[jira-board-structure]] — ALDC Scrum Board layout: 3 swimlanes (Support, Development, Research & Tooling), column definitions, Waiting On Client cross-cutting state, graduation rule for research items.
- [[knowledge-transfer-log]] — Steven to Paul handoff: KT session notes, outstanding asks/requests, to-dos, institutional knowledge about GEP, Fusion92, and deployment processes.
- [[debugging-warehouse-loads]] — Runbook for failing warehouse loads: Eclipse template → Postman → core_api → CosmosDB schema-container inspection.
- [[employee-onboarding]] — Account & software access checklist for a new ALDC hire (M365, Slack, GitHub, Atlassian, Eclipse, Snowflake, Azure, Postman, training). Pair with [[environment-setup]] for the technical machine setup.
- [[synapse-analytics-setup]] — Azure Synapse Analytics + CosmosDB Analytical Store: linked service, server credentials, serverless SQL view templates.
- [[confluence-migration]] — Runbook + progress tracker for migrating Confluence content into this wiki via Atlassian MCP. Per-space status, next-batch queue, protocol (scope → propose → extract → map → apply), and credential-extraction rules. Start here when resuming migration work.
- [[agent-builds]] — Proxmox Agent VM provisioning (Windows + Linux), backup/restore, VM numbering, SQL Server ODBC 18 Ubuntu workaround, NextCloud cluster daemon pattern.
- [[tailscale-linux]] — Tailscale install + Remmina remote desktop on Ubuntu. Connects to on-prem Agent VMs.
- [[powerbi-secret-refresh]] — Operational procedure for refreshing Azure AD PBI registration secrets and updating Django admin. Current expiry table for DISH_DUER, FUSION92, GEP, KIT_ACE.
- [[executive-snapshot-email]] — Executive Snapshot email automation on Auriga VM 11099. Cron schedule (7:30 AM test, 8:00 AM prod, Pacific time).
- [[erik-johnston-interview-guide]] — Interview flow guide for Erik Johnston (2026-05-11). 10-section structure with deep-dive questions mapped to ALDC stack.

### Distributed Workflow
- [[processes/distributed-workflow/README|distributed-workflow]] — Coordination kit for parallel Claude Code sessions across separate workstreams. Session-level extension of [[CLAUDE|Parallel Ingestion]]. Read first when running multi-front days.
- [[processes/distributed-workflow/orchestration-pattern]] — Lanes, write isolation, shared-file protocol, performance techniques.
- [[processes/distributed-workflow/session-lifecycle]] — Boot → plan-mode → approval → implementation → checkpoint → handoff. Includes the consolidated when-to-enter-plan-mode table.
- [[processes/distributed-workflow/tracker-template]] — Copy this when starting a new workstream.
- [[processes/distributed-workflow/workflow-diagram]] — Mermaid diagram: full ticket-to-delivery flow through the distributed workflow.
- [[processes/distributed-workflow/active/observability-platform]] — Active workstream tracker (execution phase: company-wide lightweight observability & monitoring platform — app health, data jobs, on-prem + Azure infra, support inbox). Week 1 complete 2026-04-25.
- [[processes/distributed-workflow/active/confluence-migration]] — Active workstream tracker (session coordinator for the Confluence ingest; mechanics in [[confluence-migration]]).
- [[processes/distributed-workflow/active/client-workflow-automation]] — Active workstream tracker (design phase: sandboxed feature-delivery flow for GEP-style work).
- [[processes/distributed-workflow/active/ops-platform/README|ops-platform (ALDC Launchpad POC)]] — Completed POC workstream (Phases 0-2: design system, data layer, platform dashboard). Superseded by aldc-launchpad monorepo.
- [[processes/distributed-workflow/active/aldc-launchpad/README|aldc-launchpad]] — Active workstream: Two-sided AI delivery platform (monorepo). Phases 0R–3 complete. Phase 4 (Analytics Stack): verified and deployed to QA — dbt 43/43, Superset running, Cube code-complete. Engineering Tracker + Development Platform planning in progress.
- [[processes/distributed-workflow/active/navira/README|navira]] — Active workstream: Navira/GEP integration roadmap. 6 phased workflows (1A–4), 17 interfaces, credentials tracker, 8 dashboard recs, Phase 1A data dictionary, credential validation toolkit. Priority order: Marketing Ad Platforms → Social/Emerging → Agency Sales → Inventory → Competitor → Unstructured.
- [[processes/distributed-workflow/active/phase6-pbi-automation-plan]] — Phase 6 PBI model automation plan. XMLA-scripted sandbox dataset via Tabular Editor CLI + PBI REST refresh. Resolves "Multi-feature conflict in TEST / PBI" blocker. Level 2 for v1; Deployment Pipelines (Level 3) + TMDL version control deferred to v2.
- [[processes/distributed-workflow/backlog/wiki-client-restructure]] — Backlog: reorganize wiki into client-first structure (GEP/Fusion92 top-level folders, frontmatter-driven Jira state, hub README per client). ~2-3hr migration script.
- [[processes/distributed-workflow/archive/dv-444-dashboard-rename]] — ✅ Archived 2026-04-21: DV-444 Navira-demo sidebar app rename "Dashboard" → "SKU Profitability". Pure CosmosDB data change on `application_metadata`; no eclipse-2.1 code commits.
- [[processes/distributed-workflow/active/azure-deploy-automation]] — Active workstream tracker (Phase 1–3: automate CI → stage deploy → Playwright E2E → slot swap for eclipse + core_api). Phased to-do with boot prompts per phase.
- [[processes/distributed-workflow/active/zeus-memory/README|zeus-memory]] — Active workstream: Automated Tenant Data Source Ingestion. 5 phases (0–4): Discovery → Confluence ingestion → Jira+Git → Batch orchestration → Self-service onboarding. Phase 0 current (no codebase access yet).
- [[processes/distributed-workflow/active/wiki-zeus-ingestion/README|wiki-zeus-ingestion]] — Active workstream: Ingest ALDC LLM Wiki (262 pages) into Zeus Memory. Heading-aware semantic chunking, git-native change detection, per-directory classification. Epic ALDC-209 + 7 stories. Pending team review.
- [[processes/distributed-workflow/archive/repo-documentation]] — ✅ Archived 2026-04-20: Repo documentation workstream complete. 9 ALDC repos documented + cross-repo [[repo-integration-map]]. 10 new wiki pages, 4 memories, 1 potential ticket (`.pbip` migration), 11 stale cross-references flagged.
- [[processes/distributed-workflow/complete/fu92-394-viant-dsp-fix]] — ✅ Complete 2026-05-08: Viant DSP connector timeout fix fully deployed (Kamloops + Coquitlam), backfill confirmed, PBI validated. FU92-394 Done, FU92-399 Done.
- [[processes/distributed-workflow/active/fu92-394-viant-dsp-fix]] — Active workstream: FU92-394 Viant DSP connector timeout fix + re-enable + backfill + client comms. 4 phases with boot prompts.

---

## Tickets

### Templates
- [[tickets/_bug-template|_bug-template]] — Bug ticket template with boot prompt, investigation log, ranked causes

### GEP
- [[GP-169]] — Marketing activity marketplace attribution. Profile-based mapping of Amazon Ads profiles to canonical marketplaces in `MARKETING_FCT_ACTIVITY`.
- [[GP-197]] — Future-proof Amazon marketplace filter in `sales_fct_cost.sql`. Replaced hard-coded name list with `IS_AMAZON_MARKETPLACE` flag. Subsumed into GP-204.
- [[GP-200]] — Amazon UK addition to orders. End-to-end new-marketplace onboarding (Eclipse connection/template + SQL UNION + deployment runbook). UAT in progress — data confirmed present 2026-05-20; customer meeting 2026-05-21.
- [[GP-203]] — Add Canadian traffic data to `TRAFFIC_FCT_ACTIVITY`. Defended per-marketplace grain during PR review.
- [[GP-204]] — CSV-driven marketplace metadata (net discount, DTC fee, Amazon flag). Self-service CSV replaces hard-coded CASE statements in order-line facts.
- [[GP-207]] — Prod-to-test data share setup. Re-pointed all GEP warehouse SQL to `PROD_DG1_GEP` share so test and prod reference the same raw data.
- [[GP-199]] — ASIN Brand Campaign Attribution. Attributes SB spend to targeted ASINs (ad-creative equal-split). Deployed to Prod 2026-05-21, client UAT. Confirmed safe to promote independently of [[GP-225]] (cost-only allocation).
- [[GP-277]] — Core API fixes: dtype-tolerant schema versioning (Fix 2) + work_pick connection scoping (Fix A). Branch `fix/warehouse-schema-version-dtype-tolerant`, deployed to TEST core_api STAGE slot (not promoted). Pick fix unblocks scoped-agent TEST validation (was blocking [[GP-199]] phase-2 + connector testing); Fix 2 stops 24-version dtype-drift forking. Gate before promote: consumer-side varchar-gravitation validation.
- [[GP-225]] — Unified Marketing Schema Design (Snowflake). Phase 1A prerequisite. Finding: `MARKETING_FCT_ACTIVITY` already unifies all channels; Q3 (attribution) → store raw; Q8 (SKU map) → no ASIN→SKU dimension yet. Real blocker = Google/Meta revenue not loaded from [[Windsor]] (field-selection gap, not capability gap). **2026-06-04: Sandbox validation complete** (unified fact + preview clone + 4-page report + agency tenant; Flag A/B reproduced + addressed); cutover gated. **2026-06-05:** Jan-2026 FX-gap CONFIRMED+FIXED + Amazon-UK $0 = [[GP-221]] blocked (both pre-cutover investigations closed); MER shifted 30.29→31.52 post-fix (re-derive before sign-off). **2026-06-05 (pm):** re-derived MER **31.33x**; capped+uncapped Calibrated ROAS both built; shadow Platform/Marketplace dims (Google/Meta resolve); data dictionary + `WAREHOUSE_TEST_GP226_TEAM` handoff ready; repo moved to ALDC org.
- [[GP-254]] — Lectric eBike agency onboarding (Phase 1C). First multi-tenant agency tenant: isolated `AMAZON_LECTRIC` schema → `SALES_FCT_LECTRIC_AMAZON_ORDERLINE` (`ENTITY_CODE='LECTRIC'`, sales-only). **2026-06-05: REAL backfill done** — 5,192 US order-lines / $2.52M / 4,206 orders (2024-06→2026-06), replacing the 327 mock; validated (NAVIRA isolated). Finding: SP-API marketplace filter ignored → Lectric US-only via these creds. Still a `_DEV` cross-DB view (PBI re-materialize deferred).
- [[GP-208]] — Inventory feed ingestion & modelling. Phase 1 (current snapshot) built on existing Sellercloud + Amazon FBA pipelines — no data share. Data dictionary at [[gep-inventory-data-dictionary]]. Phase 2 (historical accumulation) pending.
- [[GP-217]] — CI/CD Pipeline + Infrastructure Right-Sizing. Docker publish gated behind quality gate, standalone `docker-publish.yml` removed. PostgreSQL D2ads_v5→B1ms, App Service P2v3→S1. ~$265/mo saved. 2026-05-03.
- [[GP-218]] — QA/UAT/Prod Work Pools & Promotion Pipeline. 3 Work Pools, 3 worker Container Apps, 3 Snowflake blocks, `short_code` fix, promotion pipeline documented. Infra complete 2026-05-02, GEP E2E pending PR #1.
- [[GP-248]] — Prefect Snowflake Environment Isolation. 3 databases (`QA/TEST/PROD_DG1_GEP_PREFECT`), 3 `PREFECT_SVC` service accounts, 2 PBI workspaces. Done 2026-05-02.
- [[GP-256]] — Add Return Rate KPIs (unit-based) to SKU Profitability Dashboard. DAX measure deployed to Prod via XMLA 2026-05-22. Navira-demo frontend update remaining.
- [[GP-259]] — Orders/Return and COGs for SKU Profitability. Measures already exist in GEP Prod model. Navira-demo frontend update remaining.
- [[GP-261]] — Navira Snowflake → ALDC ingestion. First Snowflake-to-Snowflake connector. Decision revised 2026-06-01 (Prefect shelved): native Secure Data Share + local materialization, hardened with share-drop detection + stale-but-available mitigation. Snowsight setup guide drafted for Justin; ALDC identity confirmed. Awaiting Justin's view list + region.
- [[GP-PENDING-missing-cogs-cost-history]] — Catalog-wide blank-COGS / overstated margin on SKU Profitability (Heather "Missing COGs"). Root cause = cost-history horizon (begins 2024-05-30 vs sales from 2023) + cost-field/timing lag. Fix (back-fill + field fallback) validated: ~$21M COGS recovered, zero regression. Awaiting Navira's option choice (2026-05-28).
- [[GP-PENDING-data-share-stability]] — PENDING: research share gap detection/prevention. Tables drop from PROD outbound share silently; task chain only fails at runtime. Four options researched.
- [[GP-PENDING-infra-connector-failures]] — PENDING: four long-running infra failures (NFS mount missing, SQL Server unreachable, Eclipse Core API DNS, Fusion92 expired credentials). Discovered 2026-05-22. 10 GEP + 7 F92 templates failing, 13–27+ days stale.
- [[GP-PENDING-sales-data-outage-2026-05-22]] — RESOLVED incident: ~14-hour task chain suspension (2026-05-21 19:52 – 2026-05-22 09:14 PT). `PROD_DG1_ROLE_CORE_SVC_DA8904DB` lacked USAGE on `PROD_DG1_ALDC_LIBRARY`; `SALES_FCT_ORDERLINE` view expansion failed at step 7; Snowflake auto-suspended root task. Fix: explicit USAGE + SELECT grants. PBI refreshed 16:18 UTC. +1,387 orders / +5,114 order lines recovered.

### Fusion92
- [[FU92-342]] — Viant campaign conversions fact table. Root cause: CONVERSION_EVENT_ID missing from connector PK caused duplicates. Fixed at source.
- [[FU92-394]] — Viant DSP actuals missing after 4/2. Connector timeout bug → schedules disabled → never re-enabled. Fix + backfill.
- [[FU92-393]] — NetSuite sandbox 500 error. Root cause: wrong Client ID stored in Azure env var. Fix: new integration + cert + updated env vars on aldctestfnapf921c01. **Status: In Progress — auth fixed, needs E2E PO sync test.**
- [[FU92-395]] — DAX user role error on approved flight. Ken Kocna can't view flight, persists after re-login. Resolved via FU92-396.
- [[FU92-396]] — Stale JWT role blocking Manual Metrics Input. Fix: periodic role refresh from CosmosDB in JWT callback. PR #35.
- [[FU92-397]] — NetSuite PO Employee field shows wrong person. Root cause: employee set to project PM, not syncing user. Fix: pass user identity from frontend, look up NS employee. **Status: Deployed to Production 2026-05-22 — Awaiting Client Confirmation.**
- [[FU92-398]] — Meta data discrepancies across all clients for April. Root cause: 25-day connector loading gap (Apr 5–28), self-recovered. No data loss. Ready for Customer.
- [[FU92-415]] — Meta connector token refresh automation + CCCU/PCU template cleanup + connector monitoring. Follow-up to FU92-398.
- [[FU92-416]] — Trade Desk + Viant auth token lifespan investigation. Unknown expiry, no auto-refresh.

### Internal / Research & Tooling
- [[SHIP-001]] — Rename aldc-shipyard to shipyard. Drop `aldc-` prefix, update all refs. ~15-20 min dedicated session.
- [[SHIP-002]] — Team Pulse: Highs/Lows/Celebrations + Coffee Recognition. Scans Jira + Wiki + Zeus Memory for per-person and company-wide summaries. CLI MVP → skill → UI (Claude Design).

### DV (Eclipse 2.1)
- [[DV-444]] — Rename GEP/Navira's `navira-demo` sidebar app label from "Dashboard" → "SKU Profitability". Data change in `application_metadata` CosmosDB doc; no eclipse-2.1 code change. Surfaced v2 write-endpoint gap in [[core_api]].
- [[DV-506]] — Eclipse invitation emails not received by external user (brinno.com). Mailjet deliverability issue — 5+ invites sent by Navira admin, none received. Same pattern as DV-194.

---

## Vault

- `vault/credentials.md` — Centralized credentials reference (gitignored). All passwords, tokens, keys, connection strings organized by client.
- `vault/core-api-local-settings.md` — Full `local.settings.json` for core_api (prod/test/qa blocks). Env-var schema reference. Gitignored.
- `vault/postman-collections.md` — Storage for Postman collection JSON exports + PROD env bearer tokens. Gitignored.
- `vault/postman-build.py` — Idempotent extractor/generator: reads the embedded collection + env JSON from `daily/2026-04-17.md`, writes 6 clean import-ready files (renamed collections with auto-bearer script + 4 env files) to `C:/Users/PaulRussell/postman-exports/`. Gitignored.

---

## Daily

Handwritten notes inbox. Copy `daily/_template.md` as `daily/YYYY-MM-DD.md`, add notes throughout the day using `## Note` blocks with `type:` tags, then ask Claude to "ingest today's notes."

- [[_template]] — Note format reference and type guide

---

## Work Plan

Start-of-day task tracker. Generated from previous standup's "Plan for Tomorrow" + unblocked items. Updated throughout the day as work progresses. Feeds into the end-of-day standup.

- [[workplan/2026-05-08]] — GP-221 UK PPC OAuth complete, GP-252 created, Snowflake ACCOUNTADMIN reset, FU92-398 Meta investigation complete
- [[workplan/2026-05-07]] — FU92-396 JWT role refresh fix (full cycle: code → deploy → production validation) + FU92-397 triage
- [[workplan/2026-05-05]] — FU92-394 CI deploy + backfill, FU92-395 investigation, GP-218 E2E (blocked)
- [[workplan/2026-05-04]] — FU92-394 Viant connector fix + FU92-395 DAX permissions triage
- [[workplan/2026-05-02]] — GP-248 Snowflake environment isolation execution
- [[workplan/2026-05-01]] — AMZ UK PPC token exchange (unblocked), GP-243 Prefect Server validation, GP-247 repo fork, GP-248 Snowflake env isolation

---

## Stand-Up

End-of-day summaries for next-morning team standup. Generated by scanning `log.md`, updated wiki pages, and session context. Three sections: What I Did Today, Blockers, Plan for Tomorrow.

- [[standup/2026-05-22]] — FU92-415 RBA double-count fix + Smile Doctors Windsor diagnosis, GP-268 missing sales incident, FU92-417 PBI takeover, GP-269 CIFS mount fix
- [[standup/2026-05-21]] — FU92-415 Meta token refresh deployed, GP-199 client UAT ready, Eclipse Test fix, credential exchange migration A+B, CCX leaderboard fix
- [[standup/2026-05-08]] — GP-221 UK PPC OAuth complete, GP-252 pipeline config created, Snowflake admin reset, FU92-398 Meta investigation complete
- [[standup/2026-05-07]] — FU92-396 JWT role fix deployed + validated in production; FU92-397 NetSuite PO Employee bug root-caused
- [[standup/2026-05-04]] — FU92-394 Viant timeout fix + automatic CI deployment wired, FU92-395 triage, 4 wiki pages
- [[standup/2026-05-03]] — GP-217 CI/CD pipeline gated + Azure right-sizing (~$265/mo saved)
- [[standup/2026-05-02]] — GP-248 Snowflake env isolation complete — 3 databases, 3 PREFECT_SVC accounts, 2 PBI workspaces, framework CORE_SVC→PREFECT_SVC rename
- [[standup/2026-05-01]] — GP-243 Prefect Server validated (all green), auth mechanism documented, subscription error corrected, deployment guide written
- [[standup/2026-04-30]] — Navira roadmap breakdown (30+ tickets GP-213–248), sprint S2–S5 planning, repo fork plan, Snowflake 4-tier environment isolation, access epic GP-237
- [[standup/2026-04-29]] — Phase 0 G2+G3 complete (PRs #116/#117 merged, 19 tests), wrong-branch deploy incident + post-mortem, Azure Deploy Automation workstream created, aldc-shipyard rename
- [[standup/2026-04-28]] — Navira roadmap cross-reference, Phase 0 E2E proven, UK PPC auth blocker

---

## Meta

- `log.md` — Append-only operation log. Every ingest, lint, and consolidation pass leaves a row here: `| date | operation | summary |`. Use for auditing what was ingested and when.
