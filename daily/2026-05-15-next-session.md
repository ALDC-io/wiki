---
tags: [daily, navira, orchestrator, sprint, connector-migration, prefect]
created: 2026-05-15
---

# Next Session: Navira Orchestrator — Parallel Ticket Execution

**Start with:** `/model opus` then paste the prompt below.

---

## Prompt

I want to use the Session Orchestrator (`scripts/orchestrator.py`) to work through my Navira (GEP) sprint tickets in parallel. The orchestrator is built — it launches `claude -p` subprocesses in git worktrees, has context enrichment from wiki/Zeus/registry, and a Kanban UI at `pages/orchestrator/index.html`. What's missing: the 15 pipeline types were identified but none implemented. I need you to build the first 4 pipeline types as DAGs, then start executing tickets through them.

### Pipeline types to build

1. **connector-migration** — Eclipse→Prefect migration. Steps: analyze legacy connector config → create Prefect flow (Python) → register deployment → test in QA → data parity check vs Eclipse → promote to prod.
2. **prefect-infra** — Prefect infrastructure provisioning. Steps: configure work pool → set up deployment templates → CI/CD integration → QA validation.
3. **credential-provision** — Credential retrieval + Prefect block provisioning. Steps: generate HMAC collection link → track submission → validate credential → provision to Key Vault → create Prefect block.
4. **data-parity-test** — Post-migration data validation. Steps: run connector in QA → query Snowflake landing tables → compare row counts/aggregates vs Eclipse → flag discrepancies → generate report.

### Tickets to execute (prioritized)

**Phase 0 — Foundation blockers (do first, Jun 30 deadline):**
- GP-218: Prefect Work Pools & Promotion Pipeline (Development, High) → `prefect-infra`
- GP-219: Sellercloud SQL → Prefect Migration (Consulting/Design, High) → `connector-migration`
- GP-242: Sellercloud Credentials → Prefect Block (Consulting/Design, High) → `credential-provision`
- GP-246: Migration Testing Protocol (Consulting/Design, High) → `data-parity-test`

**Phase 1a — Marketing connectors (after Phase 0 unblocks):**
- GP-238: Google Ads — MCC Access + Credentials (Development, Highest) → `credential-provision`
- GP-239: Facebook/Meta — Business Manager + API (Development, High) → `credential-provision`
- GP-240: Target+ — Access Method (Consulting/Design, High) → `credential-provision`
- GP-225: Unified Marketing Schema Design (Consulting/Design, High) → `snowflake-ddl`

**Non-roadmap highest priority:**
- GP-199: ASIN Data on Ad Spend Interface (Development, Highest)
- GP-261: Configure Navira Snowflake → ALDC ingestion (To Do, High)
- GP-265: Google Ad Spend into data (To Do, High)
- GP-264: Marketing Dashboard — All connections (To Do, High)

**13 more at Medium/Low** (dashboard features, UK orders, BSR, forecasting, etc.)

### Key context
- Orchestrator code: `scripts/orchestrator.py` (HTTP server port 8765, max 4 parallel sessions)
- Orchestrator UI: `platform/master/pages/orchestrator/index.html` (Neurospect design, Kanban view)
- Connector repo: `connectors/` submodule → prefect-connectors
- Warehouse: `warehouse/multitenant/` (deploy.py, RLS, client registry)
- Credential exchange API: `api/credential-exchange/` (6 endpoints, HMAC tokens, Key Vault, Prefect blocks)
- CLI: `cli/aldc_onboard.py` (provision, status, list, verify + dry-run + credential links)
- Jira cloud ID: `239c1bf0-93f4-4201-95fe-ab73ce4a6eff`
- Wiki: `C:\Users\PaulRussell\repos\wiki\` (read CLAUDE.md, check ticket pages under tickets/gep/)
- Navira phases in `platform/master/data/state.json`

### What I expect
1. Design the 4 pipeline DAGs as stage definitions the orchestrator can execute
2. Wire them into `orchestrator.py` (or a new `pipelines/` module it loads)
3. Start executing Phase 0 tickets in parallel (GP-218 + GP-219 can run simultaneously)
4. Each completed ticket: update Jira status, commit to worktree branch, create PR

### Constraints
- Connectors repo is a git submodule — work there for Prefect flow code
- Snowflake credentials needed for live provisioning (Key Vault or env vars)
- Paul handles git commits unless explicitly asked
- Jun 30 deadline for Navira Phase 0 completion
