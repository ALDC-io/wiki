---
tags: [process, deployment, onboarding, new-client, eclipse, snowflake, power-bi]
aliases: [New Client Setup, Client Onboarding Deployment, Deployment Guides]
sources: [Confluence INFRA/937984005 (Deployment Guides), ingested 2026-04-17]
created: 2026-04-17
updated: 2026-04-17
---

# New Client Setup

First-time onboarding runbook for standing up a brand-new ALDC client. Distinct from [[client-release-checklist]] which is for **incremental** releases on existing clients, and from [[azure-environment-bootstrap]] which brings up a new Azure environment.

## Steps

1. **Load account document** into [[CosmosDB]]
2. **Create account in [[Eclipse]]** — currently via the `/admin/` function only
3. **Assign base user access** for ALDC staff in Eclipse
4. **Ensure appropriate parent capacity exists** in [[Snowflake]]
5. **Load capacity document** into CosmosDB
6. **Run `setup/azurestorage`** — creates blob storage for parquet files
7. **Run `setup/capacity`** — creates Snowflake tables and credentials
8. **Load all connection documents** into CosmosDB
9. **Load all template documents** into CosmosDB
10. **Load all task documents** into CosmosDB
    - Modify cron schedules appropriately for the target environment
11. **Create agent** (`agent/create`) if a new agent is needed
12. **Attach connections to supporting agents** — watch for:
    - Source-system IP allowlisting
    - Driver support on each agent
    - OS compatibility for connections needing specific OS libraries
13. **Manually trigger Scan** on all templates, or wait for the `work/scan` task to collect enough work to create all supporting source tables
14. **Load all SQL code** to the relevant database / tenant space in Snowflake — only after source tables exist
15. **Load all [[Power BI]] reports** to the `<TENANT_NAME> Prod Reports` workspace. For a brand-new workspace, follow the process at Confluence PRTL/484835329 (not yet migrated)
16. **Add reports to Eclipse**, create groups, assign user access

## See Also

- [[client-release-checklist]] — generic incremental-release checklist (distinct from first-time onboarding)
- [[gep-snowflake-pbi-deployment]] — GEP-specific deployment runbook
- [[azure-environment-bootstrap]] — environment-level bringup (where `setup/azurestorage` and `setup/capacity` are originally scripted)
- [[Eclipse]] — platform being set up
- [[Snowflake]] — where SQL code lands
- [[Power BI]] — where reports land
- [[clients-repo]] — where the account/capacity/connection/template JSON lives
- [[aldc-naming-convention]] — the naming convention for Azure resources provisioned during setup
