---
tags: [process, ticket-lifecycle, workflow, development]
aliases: [Ticket Lifecycle, Ticket Workflow, Breakdown to Ship, Development Workflow]
sources: [sources/obsidian-import/deployments/Order of Operations.md, sources/obsidian-import/deployments/GP-200.md, sources/obsidian-import/deployments/Future Improvements - CREATE TICKET FOR THIS.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Deployment Steps-Guide - Paul.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Deployment Steps-Guide - Steven.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Flight Check.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Asks-Requests.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/To-Do.md]
created: 2026-04-16
updated: 2026-04-16
---

# Ticket Breakdown to Ship

The generic end-to-end workflow for taking a data engineering ticket from requirements through deployment and verification. This process was derived from patterns visible across GP-200 (Amazon UK orders), GP-207 (data-share switch), GP-208 (inventory feed), and knowledge transfer sessions between Steven and Paul.

## Prerequisites

- Jira ticket created with a clear scope
- Access to all relevant tools: [[Snowflake]], [[Power BI]], [[Eclipse]], GitHub, the [[clients-repo]]
- Understanding of the relevant client's data model (see entity pages like [[GEP]])
- Development environment set up (see [[environment-setup]])

## Steps

### 1. Requirements Gathering & Scoping

1. **Read the ticket** thoroughly. Identify what is being asked for (new data source, new fact table, view modification, etc.)
2. **Identify unknowns** and draft questions for the client or team:
   - What is the data source? (API, CSV, database, data share)
   - What is the grain of the data? (per-order, per-line-item, daily aggregate)
   - What delivery method does the client use? (push to us, we pull from them, CSV upload)
   - What business logic applies? (dedup rules, currency mapping, date handling)
3. **Send questions early.** Client response times are often the longest lead time. GP-208 was blocked for weeks waiting on data source and grain answers from GEP.
4. **Create a planning document** in the repo's `_testing/` folder or in Obsidian:
   - Scope definition
   - Data flow diagram (source -> staging -> warehouse -> report)
   - SQL files that will be changed/created
   - Open questions with status tracking

### 2. Research & Design

1. **Examine existing patterns** in the [[clients-repo]]:
   - How do similar data sources flow through the pipeline? (e.g., look at how Amazon US was implemented before adding Amazon UK)
   - What [[star-schema-convention]] patterns apply? (`shared_dim_*`, `*_fct_*`, `extract_*`)
   - What existing views/tables will your change touch?
2. **Check dimension tables** for completeness:
   - `SHARED_DIM_COMPANY_CURRENCY_MAP` -- does it cover your new currency/company?
   - `SHARED_DIM_MARKETPLACE` -- does it have an entry for your new marketplace?
   - CSV supplement tables -- do they need new rows?
3. **Check the data share** if your change references `PROD_DG1_GEP.*` objects:
   - Are all referenced objects included in the prod->test data share?
   - This is manually configured in the Snowflake prod UI, not in the repo
4. **Draft SQL changes** and review them locally

### 3. Implementation

1. **Create a feature branch**: `feature/<your-name>/<ticket-id>/<short-description>`
2. **Write/modify SQL files** following [[star-schema-convention]]:
   - Views go in `WAREHOUSE_SOURCE` schema
   - Physical tables go in `WAREHOUSE` schema (materialized by tasks)
   - Report views go in `REPORT_COMMON` schema
3. **If adding a new data source** (Phase 1 of [[gep-snowflake-pbi-deployment]]):
   - Create [[Eclipse]] connection JSON
   - Create [[Eclipse]] template JSON
   - Register both in CosmosDB
   - Trigger the first data pull and validate ingestion
4. **If adding CSV supplements** (new dimension entries):
   - Add rows to Nextcloud CSV files
   - Wait for or trigger the supplement refresh
5. **Local validation testing**:
   - Create a personal test schema in [[Snowflake]]
   - Run your SQL against it
   - Write validation queries (row counts, mapping checks, dedup verification)
   - Document all validation results in `_testing/`

### 4. Code Review & Merge to Development

1. Open a PR targeting `GEP/development` (or the appropriate development branch)
2. Include in the PR description:
   - Summary of changes
   - Validation results
   - Any known caveats or follow-ups
3. Tag a reviewer (coordinate with team)
4. Address feedback, then merge

### 5. Deploy to Test

Follow the [[gep-snowflake-pbi-deployment]] runbook:

1. **Snapshot baseline** -- capture pre-deploy counts
2. **Deploy SQL** to Snowflake Test (manual, via Snowsight UI)
3. **Trigger task chain** -- manually run `TASK_WAREHOUSE_ORDERLINE_0`
4. **Validate in Snowflake** -- functional checks, volume sanity, currency mapping
5. **Refresh Power BI test model** and smoke-test
6. **Merge** `GEP/development` -> `GEP/user-testing` via PR

### 6. Stakeholder Notification & UAT

1. Notify the client that changes are available in the test model
2. Include caveats (e.g., volume step-changes, known data quality gaps)
3. Wait for client UAT sign-off
4. Address any UAT feedback

### 7. Deploy to Production

1. Repeat the Snowflake deploy against `PROD_DG1_GEP`
2. Deploy [[Power BI]] model to production workspace:
   - Download `.pbix` from GitHub
   - Set prod parameters in Power BI Desktop
   - Publish to prod workspace
   - Verify refresh
3. Merge `GEP/user-testing` -> `main` via PR
4. Run [[flight-check]] validations

### 8. Cleanup & Follow-ups

1. Drop personal test schemas
2. Archive scratch files
3. File follow-up tickets for anything discovered during deploy:
   - Data quality gaps (e.g., missing currency mappings)
   - Technical debt (e.g., view-vs-table naming conflicts)
   - Data-share completeness gaps
4. Update relevant wiki pages with new knowledge

## Patterns Observed Across Tickets

### Client response time is the bottleneck

For tickets like GP-208 (inventory feed), waiting on the client to answer data source and grain questions took weeks. Send questions as early as possible, batch them, and follow up proactively.

### Deployments surface hidden issues

GP-200 revealed data-share gaps, currency mapping holes, and volume attribution changes that were invisible during local testing. The test environment is not identical to production -- the data share is manually maintained and may lag.

### Always capture follow-up tickets during deploy

Every deployment generates 2-3 follow-up items. Capture them in real time (in the deploy doc or `_testing/` folder) and file them immediately after the deploy completes. Examples from GP-200: EUR currency mapping gap, `extract_warehouse_metadata.sql` view-vs-table fix, data-share completeness audit.

### The dedup rule changes everything

The Amazon/SellerCloud dedup at `sales_dim_order_base.sql:254-265` means that as SellerCloud data grows, `AMZ_*` counts shrink. This is by design but is counterintuitive and will trigger questions from stakeholders every time. Always prepare a stakeholder communication explaining that total per-company volume (AMZ + SC combined) is the meaningful metric.

### Obsidian/wiki notes compound across tickets

Documenting the order of operations, pitfalls, and troubleshooting iterations during GP-200 produced a reusable runbook. Invest the time in documentation during the first deployment -- it pays back on every subsequent one.

## Pitfalls / Gotchas

- **Code merge does NOT deploy.** This is the single most important thing to remember. Every Snowflake and Power BI change requires manual action.
- **Test the data share before the task chain.** Run `SELECT` queries against all `PROD_DG1_GEP.*` objects your views reference before triggering the full task DAG.
- **Volume changes are not always bugs.** Data-share switches, dedup rule changes, and CSV supplement updates all cause legitimate volume shifts.
- **Power BI models in the repo must always point to test.** Never commit a `.pbix` with production parameters.
- **Snowflake tasks are a DAG, not independent.** Triggering the root task fires all 10 steps. If step 4 fails, steps 5-9 are skipped. Fix the root cause and re-trigger from the root.

## See Also

- [[gep-snowflake-pbi-deployment]] -- detailed deployment runbook
- [[environment-setup]] -- developer machine setup
- [[flight-check]] -- operational validation process
- [[knowledge-transfer-log]] -- institutional knowledge from Steven -> Paul handoff
- [[GEP]] -- client entity page
- [[data-pipeline-flow]] -- end-to-end architecture
- [[star-schema-convention]] -- naming conventions
- [[clients-repo]] -- repository structure
