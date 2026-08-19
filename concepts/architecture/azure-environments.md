---
tags: [concept, architecture, azure, environments, infrastructure]
aliases: [Azure environments, Azure subscription model, ALDC environments]
sources: [daily/2026-04-17.md, session 2026-08-13 (Azure CLI inventory)]
created: 2026-04-17
updated: 2026-08-13
---

# Azure Environments

ALDC's environment model is rooted in [[Azure]] **subscriptions** — each subscription is effectively a distinct environment with its own resources (web apps, [[CosmosDB]] instances, storage accounts, function apps). This page documents which subscription is which and what lives where, because the naming is a common source of confusion for new engineers.

## Subscription → environment mapping

| Subscription     | Environment             | Primary purpose                                                                  | Active?       |
| ---------------- | ----------------------- | -------------------------------------------------------------------------------- | ------------- |
| **Production 2** | Production              | **The real prod.** Hosts core_api, Eclipse web apps, prod CosmosDB               | ✅ Active      |
| Production 1     | Legacy prod             | Older prod subscription, effectively unused                                      | ❌ Dead weight |
| TEST 1           | Staging (client-shared) | Staging slot target for Eclipse-style deploys; clients have visibility here      | ✅ Active      |
| Quality 1        | QA resources            | Houses Snowflake-test references, test CosmosDB, general QA workloads            | ✅ Active      |
| Development 2    | Development             | For local dev / local-connection work. Two Development-style subscriptions exist | ✅ Active      |
| QA               | Prefect sandbox         | Where the [[Prefect]] deployment currently lives — sandbox-style                 | ✅ Active      |
| DEMO 1           | Demo                    | Not really used anymore                                                          | ❌ Dormant     |

## Deployment-slot flow across environments

Most Eclipse-adjacent web apps use [[Azure]] deployment slots. The flow:

```
[GitHub Actions: Deploy to Azure (Staging)]
             │
             ▼
    Production 2 ─── staging slot
             │
        (manual swap)
             │
             ▼
    Production 2 ─── production slot  ◄── [[Cloudflare]] CNAME target
```

Full runbook: [[eclipse-azure-deployment]].

> **Confusing naming alert:** "TEST 1" is a full subscription *and* shared with clients. It is **not** the same as the staging-**slot** that lives inside Production 2. A deploy pipeline targets a staging **slot** within the Production 2 subscription, then swaps in place. TEST 1 (the subscription) is a separate client-shared staging environment.

## What lives where (prod)

In **Production 2**, browse resources and identify services by domain name:

- **Eclipse 1** web app — the **portal** (front-end UI)
- **Eclipse 2** web app — the **node** (backend / API worker)
- **core_api** function app — `aldcprodfnapcore1c01` (plus `aldcprodfnapcore1c03` as an alternate, and legacy `aldcprodfnap08core`)
- **CosmosDB** prod — `aldcprodcsdb1c01` (Eclipse connection/template storage)
- **Storage accounts** — `aldcprodstaccore1c01` (core functions + transport) and `aldcprodstacqueue1c01` (queues)
- **Resource group** — `aldcprodrsgp1c`
- **Subscription ID** — `6389f755-3ff7-488a-a56c-7ea8297730bc`
- **Fusion92 function app** — `aldcprodfnapf921c01`

## What lives where (QA / test / dev)

**Quality 1** — subscription ID `efe036d8-0ca0-4b41-b794-f90543a11061`. Core resources:

- Web apps: `aldcqawbapportal1c01` (portal) / `aldcqanode1c01` (node) — **no custom domains**
- Function apps: `aldcqafnapcore1c01`, `aldcqafnapdispatch1c01`, `aldcqafnaptaskdaemon`,
  `aldcqafnapf921c01` (Fusion92)
- Storage: `aldcqastaccore1c01` (core) / `aldcqastacqueue1c01` (queue)
- CosmosDB: `aldcqacsdb1c01`
- Resource group: `aldcqarsgp1c` (+ `rg-aldc-launchpad`, `aldcqarsgpswsp1c01`)

> **Contradiction (flagged 2026-08-13, unresolved):** the table above lists "Quality 1" and "QA"
> as two separate subscriptions, but the subscription ID previously documented under
> "QA subscription" (`efe036d8-…`) **is Quality 1**. Only four subscriptions are visible to Paul
> in the tenant: Production 2, Test 1, Quality 1, Development 2. Either "QA" is an alias for
> Quality 1, or it is a subscription Paul cannot see. Needs confirming with Vlad or Brayden.

**TEST 1 / test values** — shared-with-clients staging. Core resources:

- Web apps: `aldctestwbapportal1c01` → **`eclipse-test.aldc.io`** (Python 3.11) /
  `aldctestnode1c01` → **`eclipse2-test.aldc.io`** (Node 20 LTS)
- Function apps: `aldctestfnapcore1c01` + `aldctestfnapcore1c03` (core_api `v1`),
  `aldctestfnaptrigger1c01` (`task_daemon`), `aldctestfnapqueuetrigger1c01` +
  `aldctestfnapqueuetrigger1e01` (`dispatcher`), `aldctestfnapf921c01` (Fusion92)
- Storage: `aldcteststaccore1c01` / `aldcteststacqueue1c01`
- CosmosDB: `aldctestcsdb1c01`
- Postgres: `aldctestpgdbportal1c01` (holds the eclipse-test `app_user` login store)
- Key Vault: `aldc-vault-test` — **lives in `rg-aldc-launchpad`, NOT `aldctestrsgp1c`**
- Resource group: `aldctestrsgp1c` (+ `rg-aldc-launchpad`, `aldctestrsgp1e`)
- Subscription ID: `6969113c-ad7c-47da-8684-4795c635c959`

> **Not purely a test environment:** `aldctestfnapf921c01` runs **live Fusion92 client
> integrations** — NetSuite PO sync, publishers feed, notifications, and a Microsoft Ads token
> refresh on a daily 07:00 timer (verified firing 30/30 days). Disabling this subscription would
> break production client plumbing, not just testing. See [[azure-nonprod-cost-reduction]].

**Dev** — legacy function app `aldcdevfnap02core` (older core version)

**Shared tenant** (all envs): `e2bae64b-6e5f-4f55-b81c-ada320c7f572`

## Naming convention

Resource names follow a prefix + env + type + role + instance pattern:

```
aldc <env> <type> <role> <instance>
     prod   fnap   core   1c01
     qa     staccore       (implicit no instance → 1c01)
     test   csdb           (implicit no instance)
```

Typical type codes: `fnap` = function app, `staccore` = storage account (core), `stacqueue` = storage account (queue), `csdb` = Cosmos DB, `rsgp` = resource group, `fnapf92` = function app (fusion92-specific).

## Access (Paul, as of 2026-08-13)

| Access | Status |
|--------|--------|
| Eclipse production | ✅ Granted 2026-04-17 |
| Production 2 read/dev | ✅ (implied by Eclipse prod access) |
| Azure owner permissions | ✅ **Owner on all four subscriptions** (verified 2026-08-13) |
| Local connection env file | ❌ Pending — Brayden to provide |
| [[Cloudflare]] | ✅ Granted 2026-04-17 by Brayden |

### Who can grant subscription access (verified 2026-08-13)

Owner / User Access Administrator at subscription scope:

| Principal | Test 1 | Quality 1 | Production 2 | Development 2 |
|---|---|---|---|---|
| Vlad Ryzhkov | Owner | Owner | Owner | Owner |
| Paul Russell | Owner | Owner | Owner | Owner |
| Brayden Marshall (`@prod.aldc.io`) | Owner | — | Owner | — |
| **Sean O'Grady** | Owner | Owner | Owner | Owner |

> **⚠ Sean O'Grady has left the company.** His account is **disabled**
> (`accountEnabled: false`) but retains **Owner on all four subscriptions** and
> **Global Administrator** in Entra. Stale standing privilege — see
> [[azure-nonprod-cost-reduction]] open items. Lori Beck and Mike Stuart hold **no**
> subscription roles.

**Billing is a separate plane.** Subscription Owner does not grant billing access. Entra
directory roles as of 2026-08-13 — *Global Administrator*: Sean (disabled), John Moran, Brayden,
Lori Beck, Mike Stuart; *Billing Administrator*: John Moran, Lori Beck. Entra Billing Admin
covers M365 billing, **not** Pay-As-You-Go Azure billing (tied to a separate Account
Administrator identity). A Global Admin can self-elevate to root-scope Azure access via
Entra ID → Properties → *Access management for Azure resources* → Yes.

## On-prem counterparts

Not everything is on Azure. Relevant on-prem servers referenced from the same mental model:

- **`aldc-ca-w1`** — on-prem server. Only prod artifact still running here is the **DIOS API**
- **Galactica** on-prem SQL Server VM — pending decommission per [[knowledge-transfer-log]]

## See Also

- [[Azure]] — tool page with resource-level detail
- [[azure-nonprod-cost-reduction]] — 2026-08 cost pass on Test 1 + Quality 1; gotchas, open items
- [[eclipse-azure-deployment]] — how code flows from GitHub → staging slot → prod
- [[CosmosDB]] — environment-scoped instances live in these subscriptions
- [[Prefect]] — QA subscription is its current home
- [[Cloudflare]] — fronts the Production 2 web apps via CNAMEs
- [[data-pipeline-flow]] — the data pipeline runs inside these environments
