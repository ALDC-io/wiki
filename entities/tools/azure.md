---
tags: [entity, tool, azure, cloud, infrastructure, hosting]
aliases: [Azure, Microsoft Azure]
sources: [daily/2026-04-17.md, prefect-connectors session 2026-08-14 (az CLI MSYS path-conversion correction)]
created: 2026-04-17
updated: 2026-08-14
---

# Azure

ALDC's primary cloud hosting platform. Runs the majority of production and non-production services: web apps (Eclipse, [[core_api]]), [[CosmosDB]] (Eclipse template/schema storage), function apps (transport layer pieces), and storage accounts (intermediate landing for [[connector]] pulls before they are ingested into [[Snowflake]]).

## Subscriptions (environment model)

ALDC organizes Azure resources by subscription. Each subscription acts as an isolated environment. See [[azure-environments]] for the full model and access notes.

| Subscription | Purpose | Notes |
|--------------|---------|-------|
| Production 2 | **Primary production** | Main prod IAM needed here. Hosts core_api, Eclipse web apps, CosmosDB |
| Production 1 | Legacy production | Not really used anymore |
| Quality 1 | QA resources | Hosts Snowflake test (non-prod) references and the CosmosDB test instance |
| TEST 1 | Staging (shared with clients) | Staging slot lives here — swap from here to deploy to prod |
| Development 2 | Development | For local connections / development work. Two Development-type subscriptions exist |
| DEMO 1 | Demo | Not really used anymore |
| QA | Prefect sandbox | Where the [[Prefect]] deployment currently lives — sandbox-style environment |

## What runs on Azure (by service type)

- **Web Apps** — Eclipse (portal and node variants — see below), [[core_api]]. Check the domain name in the resource's configuration to tell which service a given web app is backing
  - **Eclipse 1** = portal web app
  - **Eclipse 2** = node web app
- **Function Apps** — [[core_api]] and related services. `aldcprodfnapcore1c01` is the primary prod core_api function app; also serves as the env-var source of truth (the Azure extension can pull app settings directly into your local `local.settings.json`)
- **CosmosDB** — stores Eclipse connection and template documents in a `schema` container; queried by [[core_api]] at runtime. Separate instances per environment (prod / test / qa)
- **Storage Accounts** — transport layer for [[connector]] output: connector writes pulled data here; Snowflake then runs a query to ingest into the DWH. Also the backing store for Azure Functions (`AzureWebJobsStorage`)
- **Servers** — a small number of on-prem or VM-style resources; most net-new workloads use web apps + function apps

## Named resources per environment

Resource names follow the ALDC convention (`aldc<env><type>...`) — full breakdown at [[aldc-naming-convention]].

Source: Steven's `local.settings.json` (`vault/core-api-local-settings.md`) and [[postman-collections]] PROD env file.

| Env | Resource Group | core_api Function App | Storage (core) | Storage (queue) | [[CosmosDB]] | Subscription ID |
|-----|----------------|----------------------|----------------|-----------------|--------------|-----------------|
| **prod** | `aldcprodrsgp1c` | `aldcprodfnapcore1c01` (+ `aldcprodfnapcore1c03` alt) | `aldcprodstaccore1c01` | `aldcprodstacqueue1c01` | `aldcprodcsdb1c01` | `6389f755-3ff7-488a-a56c-7ea8297730bc` |
| **qa** | `aldcqarsgp1c` | `aldcqafnapcore1c01` | `aldcqastaccore1c01` | `aldcqastacqueue1c01` | `aldcqacsdb1c01` | `efe036d8-0ca0-4b41-b794-f90543a11061` |
| **test** | `aldctestrsgp1c` | (confirm — function app name not captured) | `aldcteststaccore1c01` | `aldcteststacqueue1c01` | `aldctestcsdb1c01` | `6969113c-ad7c-47da-8684-4795c635c959` |

Shared tenant across envs: `e2bae64b-6e5f-4f55-b81c-ada320c7f572`.

Adjacent function apps referenced in Postman env files:

- `aldcprodfnapf921c01` — Fusion92 function app (`f92_function_app_url`)
- `aldcdevfnap02core` — older dev core (legacy)
- `aldcprodfnap08core` — older prod core (legacy)

## Prefect infrastructure

[[Prefect]] has its own dedicated resource footprint in Azure, separate from the core_api / Eclipse groups:

| Resource group | Holds |
|---|---|
| `aldcprodrsgpconnector1c` | Prefect Server (App Service + plan), Postgres database, VNET, admin VM |
| `aldcprodrsgpprefectworkers1c` | Work Pool Container App, managed identity, auto-generated workflow Container Instances (ephemeral) |

Prefect URL: https://prefect.analyticlabs.io

**Naming gotcha**: these resources carry the `aldcprod*` prefix but live in the **QA subscription**, not Production 2 — see [[Prefect]] § Deployment. The `prod` refers to the logical Prefect instance, not the Azure subscription.

Full resource inventory: [[Prefect]] § Azure resources (production).

## Deployment slots

All (or almost all) Azure web apps at ALDC use **deployment slots**:

- Code is deployed to a **staging slot** first
- A **swap** operation then points the public-facing hostname at the staging slot (effectively zero-downtime deploy)
- For Eclipse, you must swap both the frontend and backend app services separately

Full procedure documented in [[eclipse-azure-deployment]].

## Access

Paul's current state (as of 2026-04-17):

- Has read/developer access in Production 2 (Eclipse production — confirmed today)
- Does **not** yet have owner permissions in Azure. Brayden will need to reach out to Sean to grant them
- Environment file for local connections not yet received — Brayden to provide

## Pitfalls / things to know

- **Production 1 vs Production 2**: don't get tripped up — Production 2 is the live one. Production 1 is effectively dead
- **Domain → service mapping**: when browsing resources, use the domain name shown in the resource config to figure out which logical service a given web app represents (especially for the two Eclipse web apps)
- **Deployment slots = two halves to swap**: for Eclipse, forgetting to swap either the frontend or backend leaves the pair out of sync
- ⚠ **`az ... --scope /subscriptions/...` fails from Git Bash on Windows with a misleading
  `MissingSubscription`** (measured on `az role assignment create`, 2026-08-14). **MSYS path
  conversion** rewrites the leading-slash scope into a Windows path before `az` ever sees it. It is
  **not a permissions problem** and **not a Claude Code permission-classifier block** — it was
  previously blamed on both. Fix: run it from **PowerShell**, or set `MSYS_NO_PATHCONV=1`. Applies to
  every `az` call carrying a leading-slash resource scope; the same mechanism was recorded earlier
  against `az quota` (see [[prefect-connectors]])
- **`aldcprod*` naming ≠ Production 2 subscription for Prefect**: Prefect's resource groups (`aldcprodrsgpconnector1c`, `aldcprodrsgpprefectworkers1c`) live in the **QA subscription**, not Production 2. The `prod` prefix here refers to the logical Prefect instance, not the Azure subscription. Check the actual subscription before assuming from the name

## See Also

- [[azure-environments]] — subscription-level environment model
- [[eclipse-azure-deployment]] — staging-slot + swap deployment flow
- [[CosmosDB]] — Azure-hosted database for Eclipse templates/schema
- [[core_api]] — Azure-hosted web app
- [[connector]] — writes to Azure storage accounts as transport layer
- [[gpv1-to-gpv2-storage-migration]] — GPv1→GPv2 retirement (2026-10-13, XTKT-BW8); inventory of which accounts are still `Kind: Storage`
- [[Cloudflare]] — CNAMEs that front the Azure web apps
- [[connector-timeout-outage]] — post-mortem involving an Azure Function App
- [[GitHub Actions]] — CI/CD layer that pushes into Azure staging slots
