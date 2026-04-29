---
tags: [entity, tool, prefect, orchestration, connector-migration]
aliases: [Prefect]
sources: [sources/obsidian-import/work/PREFECT/PRE-000 - Initial Prefect Setup.md, sources/obsidian-import/work/PREFECT/Claude Planning/Planning.md, daily/2026-04-17.md, Confluence TECH/1766260745 (Prefect subtree, Brayden Offboarding), TECH/1772126209 (Azure Resources Reference), TECH/1774256132 (Github Repo and Branch Reference)]
created: 2026-04-16
updated: 2026-04-27
---

# Prefect

Workflow orchestration platform being adopted at ALDC to replace the legacy [[Eclipse]] connector scheduling. The migration (PRE-000) converts all legacy connectors to Prefect-compatible flows.

## Migration Context (PRE-000)

The connector repo (`C:\Users\PaulRussell\repos\connector`) is being migrated from legacy `BaseConnector`-based connectors to Prefect flows. There are 47 legacy connectors to migrate.

### Current Architecture

| Layer | Location | Pattern |
|-------|----------|---------|
| Legacy connectors | `connector/connectors/*.py` | `BaseConnector`-based, dict-style options/connection. Not registered with Prefect. |
| Prefect bootstrap | `main.py → DeploymentRunner.serve_local()` | Registers block schemas, serves deployments from `connector/accounts/<account>/deployments/` |
| Reference implementation | `connector/accounts/ALDC_QA/deployments/exchange_rates.py` | Senior dev example of the target pattern |
| Output handling | `BaseConnector.add_response()` | Parquet write, blob upload, Snowflake staging/merge |

### Migration Pattern

For each connector:
1. Create typed `BaseConnector[ConnectionType, OptionsType]` subclass
2. Define `ConnectorConnectionBase` subclass with typed fields (replaces dict config)
3. Define `ConnectorOptionsBase` subclass with typed fields
4. Create Prefect flow/deployment per account under `connector/accounts/<ACCOUNT>/deployments/`
5. Register via `Account.register_flow`, use `MergeScheme` + `PartitionScheme`, reuse block IDs

### Migration Order (47 connectors)

1. **nextcloud-csv** (first — establishes Nextcloud auth + Prefect pattern)
2. **migration-scaffold** (extract template from nextcloud-csv)
3. **financial-connectors** (lowest risk, closest to reference)
4. **sql-connectors**
5. **aws-connectors**
6. **nosql-connectors**
7. **netsuite-connectors**
8. **ecommerce-connectors**
9. **crm-connectors**
10. **ad-platform-connectors**
11. **analytics-platform-connectors**
12. **geo-weather-connectors**
13. **scrape-connectors**
14. **misc-api-connectors**

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Wrap vs rewrite legacy logic | **Wrap** | Legacy FlatCsv has quirky edge-case handling (BOM stripping, schema validation, rest_field, ad-hoc casting) built from real customer data issues. Rewriting risks breaking silent edge cases. |
| Nextcloud auth | Basic auth (host, user, password) | Same as existing NextcloudFileHandler. App-token/OAuth2 deferred. |
| CSV partition scheme | `PartitionSchemeFull` | Full replace each run — CSV files are static snapshots, not date-windowed. |
| File reading | Direct via `nextcloud_client.get_file_contents()` | Not through NextcloudFileHandler (which is write/move/delete only). Single-responsibility. |

### Nextcloud CSV Test Setup

```bash
# Environment variables
NEXTCLOUD_HOST=cloud.aldc.io
NEXTCLOUD_USER=paul.russell@aldc.io
NEXTCLOUD_TEST_CSV_PATH=/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv

# Run tests
MSYS_NO_PATHCONV=1 PYTHONPATH=. .venv/Scripts/python -m tests.test_connectors.nextcloudcsv
```

Note: Must use `MSYS_NO_PATHCONV=1` in Git Bash to prevent MSYS2 path translation converting leading `/` to `C:/Program Files/Git/`.

## Active Branch

Prefect / new connector development lives on the `operation-fiasco` branch of the `connector` repo (not `main`). The `main` branch continues to serve old/current connector agents. Source: Confluence TECH/1774256132 (Github Repo and Branch Reference). See [[repo-integration-map]] § Product-to-Branch Reference.

## Deployment

Prefect runs in the **QA subscription** in [[Azure]] — a sandbox for the in-flight migration. See [[azure-environments]] for the subscription map. The [[connector]] repo holds the Prefect flow definitions.

> **Naming gotcha**: the Prefect resources carry an `aldcprod*` prefix (e.g. `aldcprodrsgpconnector1c`) even though they live in the QA subscription. The `prod` here refers to the logical "production Prefect instance" that workflows point to, *not* the ALDC production Azure subscription. This naming collides with the standard ALDC convention where `aldcprod*` = Production 2 subscription resources. Reconciled 2026-04-17 per Paul.

URL: https://prefect.analyticlabs.io

Architecture + resource inventory below sourced from Confluence TECH/1767014406 subtree (Brayden Offboarding), ingested 2026-04-17.

### Deployment architecture

Four moving parts:

- **Prefect Server** — API server for workflow scheduling, runs, deployments. Also serves the UI/Dashboard. Connects to a Postgres database for transactional state.
- **Work Pool** — long-running container that watches for workflow runs on the queue and starts a worker per run. ALDC uses the Azure Container Instances work pool type ([Prefect docs](https://docs.prefect.io/v3/concepts/work-pools)).
- **Workers** — short-lived Azure Container Instances started by the Work Pool. Each worker runs one workflow, reports progress back to Prefect Server, uploads output to [[Azure]] storage (which [[Snowflake]] then ingests).
- **Blocks** — where Prefect Server stores credentials (Snowflake creds, Azure creds, per-workflow connection creds). Snowflake-credential Blocks are auto-created when Prefect Deployments are deployed; password fields start as placeholders and must be filled in before use.

### Azure resources (production)

All resources in the `aldcprodrsgpconnector1c` resource group except where noted. See [[Azure]] for the broader ALDC Azure subscription model.

**Prefect Server:**

| Resource | Type | Purpose |
|---|---|---|
| `aldcprodwbapprefectserver1c01` | App Service | Prefect Server (API + UI) |
| `aldcprodapspprefectserver1c01` | App Service Plan | Hosts the server |

**Work Pool / Workers** (in separate `aldcprodrsgpprefectworkers1c` resource group):

| Resource | Type | Purpose |
|---|---|---|
| `aldcprodrsgpprefectworkers1c` | Resource Group | Holds all auto-generated Container Instances for workflow runs (ephemeral — deleted when runs complete) |
| `aldcprodctappprefectworkpool1c01` | Container App | The Prefect Work Pool process. Default Prefect image, runs `prefect worker start` |
| `aldcprodmgidprefectworkers1c` | Managed Identity (user-assigned) | Attached to each Container Instance so workflows can reach other Azure resources |

**Database:**

| Resource | Type | Purpose |
|---|---|---|
| `aldcprodpgdbconnector1c01` | Azure Database for Postgres | Prefect Server's transactional database |
| `aldcprodpgdbconnector1c01.private.postgres.database.azure.com` | Private DNS Zone | Private DNS for the Postgres server inside the VNET |

**Networking / admin:**

| Resource | Type | Purpose |
|---|---|---|
| `aldcprodvnetconnector1c` | Virtual Network | VNET containing all Prefect services. Only Prefect Server is publicly accessible — everything else is VNET-private |
| `aldcprodvmconnector1c01` | Virtual Machine | Admin jump-host for `psql` access to the VNET-bound Postgres. Should be stopped when not in use |

### Switching environments (QA / Test / Prod)

The Work Pool uses two environment variables to pick an environment:

- `ENVIRONMENT_LEVEL`
- `ENVIRONMENT_DEPLOYMENT_GROUP`

Together they select:

- The Azure storage account used for staging data
- The [[Snowflake]] account + target database (including the Snowflake user + role)

To switch **all** Prefect workflows to a different environment, change those two env vars on the Work Pool.

To run a **single** Deployment against a different environment, stand up a second Work Pool with the other env vars and point that Deployment at the new pool. This lets one Work Pool serve production workflows while another serves Test/QA — without switching everything at once.

## Connector Specs

The 6 ad platform connector specs in `entities/tools/connectors/` document the legacy connection/options schemas and auth patterns that Prefect implementations must replicate. Full migration pattern in [[connector-development-standards]].

- [[google-analytics]] — GA4 + Universal Analytics connector
- [[facebook-ads]] — Meta Marketing API connector
- [[bing-ads]] — Microsoft Advertising connector
- [[google-ads]] — Google Ads connector
- [[amazon-ads]] — Amazon Ads + DSP connector
- [[trade-desk]] — The Trade Desk My Reports connector
- [[google-oauth-python]] — shared Google OAuth pattern (used by GA4 + Google Ads)
- [[connector-token-refresh]] — operational token refresh runbook (Bing 90-day, Facebook 60-day)

## Prefect v3 Documentation Reference

For developers building connectors, two wiki pages provide a comprehensive Prefect v3 reference extracted from the official docs:

- [[prefect-v3-reference]] — Core concepts: flows, tasks, blocks, work pools, deployments, schedules, states. Decorator parameters, deployment schema, state lifecycle.
- [[prefect-v3-patterns]] — Development patterns: retries (exponential backoff, conditional), caching (policies, expiration, distributed), concurrency (submit/map, task runners), testing (test harness, `.fn()`), logging, secrets management, Docker/ACI deployment. Includes an ALDC connector checklist.

## See Also

- [[Eclipse]] — the platform being replaced
- [[connector]] — the repo where Prefect flows live
- [[connector-development-standards]] — canonical Prefect connector pattern (attribute hierarchy, migration steps, PartitionScheme/MergeScheme selection)
- [[clients-repo]] — where Eclipse configs live (Prefect configs in connector repo)
- [[data-pipeline-flow]] — Prefect replaces Eclipse in Layer 1
- [[azure-environments]] — QA subscription is Prefect's current home
- [[Confluence]] — holds the Prefect / Azure resources doc
