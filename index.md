---
tags: [index, navigation]
updated: 2026-04-16
---

# Wiki Index

Master catalog of all wiki pages. Search here to find relevant pages.

---

## Entities

### Clients
- [[GEP]] — E-commerce analytics client (Navira). Amazon US/UK/CA, SellerCloud, Galactica. 14 connections, 62 templates, 37 warehouse views.
- [[fusion92]] — Media activation client. Meta, Google, Viant, Trade Desk, Amazon Ads. 11 connections, 50+ templates, 10 warehouse views.

### Repos
- [[clients-repo]] — Primary ALDC repo. Per-client Eclipse configs + Snowflake warehouse SQL. 19 active clients, 150+ connections, 300+ templates, 200+ warehouse views.

### Tools
- [[Snowflake]] — Data warehouse. Star schema with shared_dim_*, *_fct_*, extract_*, report_common. Manual deployment.
- [[Eclipse]] — Connector platform. JSON-based connections + templates. Pulls from APIs/DBs, loads into Snowflake.
- [[Power BI]] — Reporting layer. Consumes report_common views. Manual model refresh.
- [[Prefect]] — Workflow orchestration replacing Eclipse. PRE-000 migration: 47 legacy connectors to Prefect flows.

### Projects
- [[cce]] — Claude Code Enhanced. Auto-updating wrapper with hooks, Zeus memory integration, and cross-machine messaging.
- [[factoria]] — Autonomous data engineering platform. Docker runner-split architecture, agent operating model.
- [[ai-driven-dev-workflow]] — AI-assisted development workflow research. Multiple versions (v2, v3, v3.1). ALDC Agentic Coding Guidelines.
- [[opentribe]] — Zeus Memory product. Knowledge integrity platform with drift detection and automated documentation sync.
- [[neurospect]] — Trading journal and analytics platform. AI-assisted trade analysis, behavioral analytics, Discord bot architecture.
- [[cpma]] — Early-stage product concept exploring continuous product iteration via real-time user feedback loops and regulatory change management.
- [[monorepo-research]] — Monorepo + CCE Integration analysis. 38 improvements across 8 categories. Research complete, pending decision.
- [[openclaw]] — Open-source agent runtime/gateway used by Factoria. Multi-agent isolation, tool policy enforcement, session management.

---

## Concepts

### Architecture
- [[data-pipeline-flow]] — End-to-end: Eclipse → Snowflake source schemas → WAREHOUSE_SOURCE → WAREHOUSE → REPORT_COMMON → Power BI.
- [[star-schema-convention]] — ALDC naming: shared_dim_*, *_fct_*, extract_*. SHA2 keys, currency triple pattern, common SQL patterns.
- [[connector-timeout-outage]] — Post-mortem: `/work/pick` Azure Function timeout caused by O(N_accounts x N_connections) global queue sweep. Short-term and long-term fixes documented.

### Patterns
- [[client-repo-structure]] — Standard folder layout: eclipse/ (connections + templates) + snowflake/ (warehouse + report_common + data_share).
- [[data-share-pattern]] — Snowflake-to-Snowflake sharing: outbound (ALDC → client) and inbound (client → ALDC). Setup steps, secure view rules, fallback to file stage.
- [[cce-troubleshooting]] — Known issues and fixes for CCE: settings.local.json parsing, Windows path bugs, Zeus API key, poller daemon startup.

---

## Processes

### Deployment
- [[gep-snowflake-pbi-deployment]] — End-to-end GEP deployment runbook: 11 phases from data source registration through production deploy. 7 documented pitfalls with exact error messages and fixes.
- [[environment-setup]] — 12-step new developer onboarding: core software, Python venv, Git, Snowflake, Power BI, VPN, Docker agents.
- [[connector-docker-deployment]] — Docker agent build and deploy: SSH to workstation-agent, build.sh, push to GHCR, deploy via Portainer across test/prod/QA servers.

### Ticket Lifecycle
- [[ticket-breakdown-to-ship]] — Generic workflow from requirements gathering through deploy and verification. Patterns from GP-200, GP-208, and knowledge transfer sessions.

### Operations
- [[flight-check]] — Operational validation process: Eclipse connector health, Snowflake task chain, data freshness, Power BI refresh, data share integrity.
- [[knowledge-transfer-log]] — Steven to Paul handoff: KT session notes, outstanding asks/requests, to-dos, institutional knowledge about GEP, Fusion92, and deployment processes.

---

## Tickets

### GEP
- [[GP-169]] — Marketing activity marketplace attribution. Profile-based mapping of Amazon Ads profiles to canonical marketplaces in `MARKETING_FCT_ACTIVITY`.
- [[GP-197]] — Future-proof Amazon marketplace filter in `sales_fct_cost.sql`. Replaced hard-coded name list with `IS_AMAZON_MARKETPLACE` flag. Subsumed into GP-204.
- [[GP-200]] — Amazon UK addition to orders. End-to-end new-marketplace onboarding (Eclipse connection/template + SQL UNION + deployment runbook).
- [[GP-203]] — Add Canadian traffic data to `TRAFFIC_FCT_ACTIVITY`. Defended per-marketplace grain during PR review.
- [[GP-204]] — CSV-driven marketplace metadata (net discount, DTC fee, Amazon flag). Self-service CSV replaces hard-coded CASE statements in order-line facts.
- [[GP-207]] — Prod-to-test data share setup. Re-pointed all GEP warehouse SQL to `PROD_DG1_GEP` share so test and prod reference the same raw data.
- [[GP-208]] — Inventory feed ingestion & modelling. Greenfield fact table from Navira/GEP CSV or data share. Blocked on client responses to data source, grain, and delivery questions.

### Fusion92
- [[FU92-342]] — Viant campaign conversions fact table. Root cause: CONVERSION_EVENT_ID missing from connector PK caused duplicates. Fixed at source.

---

## Vault

- `vault/credentials.md` — Centralized credentials reference (gitignored). All passwords, tokens, keys, connection strings organized by client.

---

## Daily
*(Daily notes / POAs — populate as needed)*
