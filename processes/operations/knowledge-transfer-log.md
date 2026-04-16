---
tags: [process, operations, knowledge-transfer, onboarding, handoff]
aliases: [Knowledge Transfer Log, KT Log, Steven to Paul Handoff]
sources: [sources/obsidian-import/work/Documentation/Knowledge Transfer/Asks-Requests.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/To-Do.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/sessions/Session 1.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/sessions/Session 2.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/Flight Check.md]
created: 2026-04-16
updated: 2026-04-16
---

# Knowledge Transfer Log -- Steven to Paul

Institutional knowledge captured during the handoff from Steven (previous data engineer) to Paul Russell. This log covers key topics from KT sessions, outstanding asks/requests, and to-do items that emerged during the transfer.

## Context

Paul joined the ALDC data engineering team and took over primary responsibility for the [[GEP]] client and related work. Steven conducted knowledge transfer sessions covering deployment processes, [[Snowflake]] operations, [[Power BI]] model management, [[Eclipse]] connectors, and client-specific business logic.

## Session 1: VPN, SSMS, Power BI, and Client Context

**Key topics covered:**

### VPN Access and SSMS
- VPN access is required for querying SellerCloud SQL Server databases
- Configuration provided by Sean O'Grady (sean.ogrady@5x5inc.ca)
- SSMS is used for running partitions -- usually orderline and marketing activity tables
- Most tables do not need manual partition processing; GEP is the exception

### Power BI Web Access
- Service account credentials are required for [[Power BI]] web access
- Stored in Dashlane as "PBI Snowflake Non-Prod" (for test environment)
- Use anonymous/private browser mode before logging in with service account credentials

### Client-Specific Notes

**[[GEP]] / Navira:**
- Uses ALDC APIs to generate reports
- Has a PBI model for internal analytics
- Uses [[Eclipse]] for external customer dashboards
- If something looks wrong in Eclipse, check the PBI data model first

**Fusion92:**
- If changing the interface for Fusion's data warehouse, they need advance notice
- This applies to new fact tables or changes to existing table structures

### Prod Model Takeover
- Test model handoff is complete
- Production model takeover still needs to be done (as of Session 1)

## Session 2: Tickets and Process Notes

**Key topics covered:**

### Outstanding Ticket Work
- **Inventory pipeline**: Need to go through the inventory feed and understand the pipeline for the GP-208 modelling ticket. Potentially schedule a call with Justin for details.
- **Google Ads ticket**: Get it prepped for implementation. Two approaches under consideration:
  - Windsor approach (how Fusion92 does Google)
  - Connector approach (Prefect-native, possibly no need for Windsor)
  - Rate limiting concern: if GEP shares credentials and both parties use them concurrently
- **Windsor templates**: Consider shutting off Windsor templates to prevent duplicates. Set up alias account, invite GEP to manage ad accounts through it.
- **HT-Pet ticket**: Ping Lori if no update appears on the Kanban board

### Process Documentation Need
- Outline full detailed steps for developing and deploying changes in the data warehouse ([[clients-repo]])
- Topics to document:
  - Dynamic tables in [[Snowflake]]
  - Task graphs that need to be run
  - Whether table definitions are just manually run in Snowflake UI to deploy
  - Confirmation: code merge does NOT trigger a deploy

### Periodicity
- Periodicity is stored in [[Snowflake]]; could be changed in the future to work properly with date dimensions

### Flight Check
- Email related to a flight check issue was flagged
- Session on flight check process to be scheduled (Thursday or Friday)

## Outstanding Asks & Requests

These were identified during KT sessions and should be tracked to completion:

1. **Eclipse access** -- Paul needs access to review client dashboard issues. Can ask Marshall if needed.
2. **Prefect deep dive** -- End-to-end session on deploying a connector via Prefect. **Scheduled with Brayden.**
3. **Prod model takeover** -- Test model is transferred; prod model handoff still pending.

## To-Do Items from Knowledge Transfer

These are actionable items that emerged from the KT sessions:

- [ ] **Take over prod [[Power BI]] model** -- test is done, prod not yet
- [ ] **Understand inventory pipeline** for GP-208 -- schedule call with Justin for drilldown
- [ ] **Check Google Ads ticket** -- prep for implementation, decide Windsor vs connector approach
- [ ] **Windsor template management** -- set up alias account, invite GEP to control ad account settings
- [ ] **Ping Lori** about HT-Pet ticket status on Kanban board
- [ ] **Get Eclipse access** from Marshall
- [ ] **Complete Prefect deep dive** with Brayden
- [ ] **Document deployment steps** for the data warehouse (captured in [[gep-snowflake-pbi-deployment]])
- [ ] **Investigate flight check issue** referenced in email
- [ ] **Drop WAREHOUSE_TEST_PAUL** in prod (maintenance cleanup noted in Session 2)

## Key Institutional Knowledge

### Deployment Model
The single most important thing learned during KT: **code merge does NOT trigger deployment.** [[Snowflake]] views are deployed by manually running SQL in Snowsight. [[Power BI]] models are deployed by publishing from Desktop. This is documented in detail in [[gep-snowflake-pbi-deployment]].

### Eclipse and PBI Relationship
When an [[Eclipse]] dashboard shows incorrect data, the root cause is often in the [[Power BI]] data model, not in Eclipse itself. Check the PBI model first.

### Client Communication Norms
- **GEP**: Direct API/data interaction; uses Eclipse dashboards
- **Fusion92**: Requires advance notice for any interface changes to their data warehouse

### Data-Specific Knowledge
- Periodicity is currently stored in Snowflake but may need rework to align with date dimension usage
- SSMS partition processing is a GEP-specific operational task (not needed for most other clients)
- The prod->test data share is manually maintained and can have gaps (see [[gep-snowflake-pbi-deployment]] Pitfalls)

## Pitfalls / Gotchas

- **Prod model files in the repo must always point to test.** If you set prod parameters for a production publish, save to a temporary location -- never commit that copy to GitHub.
- **Service account vs personal account confusion.** Use anonymous browser mode for Power BI web service account access to avoid session conflicts with personal accounts.
- **Eclipse access may need to be requested separately.** It is not automatically granted with other ALDC tool access.
- **Prefect knowledge is not yet transferred.** Until the deep dive with Brayden is complete, escalate Prefect issues to the team.

## See Also

- [[GEP]] -- primary client context
- [[gep-snowflake-pbi-deployment]] -- the deployment runbook that was the main output of formalizing KT knowledge
- [[environment-setup]] -- developer setup guide
- [[flight-check]] -- operational validation process
- [[Eclipse]] -- connector platform
- [[Power BI]] -- reporting tool
- [[Snowflake]] -- data warehouse
- [[ticket-breakdown-to-ship]] -- ticket lifecycle process
- [[data-pipeline-flow]] -- end-to-end data flow
