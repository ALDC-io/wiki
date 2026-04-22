---
tags: [concept, pattern, naming, azure, on-prem, infrastructure, aldc]
aliases: [ALDC Naming Convention, Azure Standards, On Premise Standards, Resource Naming, aldc naming]
sources: [Confluence INFRA/233897985 (Azure Standards), Confluence INFRA/343506945 (On Premise Standards)]
created: 2026-04-17
updated: 2026-04-17
---

# ALDC Resource Naming Convention

All ALDC-managed infrastructure resources follow a multi-part naming convention. The same basic pattern applies to [[Azure]] resources, on-prem VMs, and anything else ALDC provisions. **Lowercase `a–z` and `0–9` only; no dashes** (not all resource types support them).

## Azure resources

Pattern: `<company><environment><resource-type><internal-function><deployment-group><region><instance>`

Example: `aldcprodfnapcore1c01` → `aldc` + `prod` + `fnap` + `core` + `1` + `c` + `01`.

| Position | Purpose | Options |
|---|---|---|
| Company | Namespace prefix | `aldc` (Analytic Labs Data Corporation) |
| Environment | Subscription / env — controls access + billing | `dev` (Development 2) · `stg` (Stage 1) · `test` (Test 1) · `demo` (Demo 1) · `prod` (Production 2) · `supt` (Support 1) · `qa` (Quality 1) |
| Resource type | Kind of resource | `csdb` CosmosDB · `apin` App Insights · `fnap` Function App · `wbap` Web App · `apsp` App Service Plan · `asvc` Analysis Services · `stac` Storage Account · `sqdb` SQL Database · `rsgp` Resource Group · `dafc` Data Factory · `pgdb` Postgres Database · `swsp` Synapse Workspace · `agnt` Work Agent · `aprg` App Registration · `psip` Public Static IP · `vnet` Virtual Network · `ntgw` NAT Gateway · `ctin` Container Instance · `ctap` Container App. Missing? email architecture@analyticlabs.io |
| Internal function | Optional — what the resource does | `core`, `port` |
| Deployment group | Single digit. Increments then wraps. Once a group is succeeded, its resources are deleted. Paired with the resource group | `1`, `2`, `3` |
| Region | Single char | `c` Canada · `w` West USA · `e` East USA · `i` Ireland · `n` Netherlands · `a` Australia |
| Instance sequence / Account ID | Within a cluster: sequence `01–99`. Or: 32-bit hex account ID for per-client resources, lowercase `00000000`–`ffffffff` |

### Deployment groups pair with resource groups

Examples:

- `aldctestfnapcore1c01` → lives in resource group `aldctestrsgp1c`
- `aldctestpgdbport3c05` → lives in resource group `aldctestrsgp3n` (deployment group `3`, sequence/region `c`/`n`)

### DNS entries

APIs and portals get DNS records of the form:

```
dg<deployment-group>-<sequence>.<function>.<region-full-name>.aldc.io
```

Example: `dg1-01.api.test.canada.aldc.io`

Region code translates to full region name (`c → canada`, `w → west-usa`, `n → netherlands`, etc.).

### Tagging

| Tag | Optional / Required | Values |
|---|---|---|
| `deployment_group` | **Required** | `0-9` |
| `instance` | Optional | `01-99` |
| `account_id` | Optional | `00000000–ffffffff` (or a reserved string for internal instances) |
| `internal_function` | Optional | as above |

> **Naming-vs-subscription gotcha**: [[Prefect]]'s resource groups carry the `aldcprod*` prefix but **live in the QA subscription**, not Production 2. The `prod` here refers to the logical Prefect production instance, not the Azure subscription. See [[Azure]] § Pitfalls and [[Prefect]] § Deployment.

## On-prem resources

Pattern: `<company><environment><resource-type><cluster><sequence><account-id><internal-function>`

| Position | Purpose | Options |
|---|---|---|
| Company | `aldc` |
| Environment | `dev` · `stg` (Stage / technical testing) · `uat` (UAT / client testing) · `prd` (Production) |
| Resource type | `lnxn` Linux Node · `winn` Windows Node |
| Instance cluster | 2-char cluster name (`aa`–`zz`) — groups resources regardless of region |
| Instance sequence | `01–99` |
| Account ID (optional) | `00000000–ffffffff` for client-dedicated resources |
| Internal function (optional) | `control` · `logging` · `billing` · `subscription` · `extract` |

Example: `aldcdevlnxnaa01extract` → dev Linux node, cluster `aa`, seq `01`, function `extract`.

## Named on-prem VM inventory

ALDC operates named VMs (ESXi on the Janus / Pallas hypervisors). Full admin credentials for each are in `vault/infra-credentials.md`; this table lists hostnames, purpose, and hypervisor only.

| Hostname | Purpose | Hypervisor / OS |
|---|---|---|
| `aldcdevlnxnaa01extract` | Common data extracts host | Janus / Ubuntu Desktop |
| `aldcdevlnxnaa02extract` | Linux worker | Ubuntu Desktop |
| `aldcstgwinnextr01` | Windows Agent test workstation | Windows 10 |
| `aldcdevwinn01template` | Windows 10 workstation template | Windows 10 |
| `aldcdevlnxn01template` | Ubuntu Desktop template | Ubuntu Desktop |
| Tynan | Daniel Petrolito's workstation | Janus / Windows 10 |
| Donnager | John Moran's workstation | Janus / Windows 10 |
| Dewalt | Sean O'Grady's workstation | Janus / Windows 10 |
| Mowteng | Shared workstation ([INFR-21](https://analyticlabsdc.atlassian.net/browse/INFR-21)) | Pallas / Windows 10 |
| Resolute | Shared workstation ([INFR-29](https://analyticlabsdc.atlassian.net/browse/INFR-29)) | Janus / Windows 10 |
| Hammurabi | Shared workstation ([INFR-39](https://analyticlabsdc.atlassian.net/browse/INFR-39)) | Janus / Windows 10 |
| Nauvoo | Unknown | ESXi VM |
| **Galactica** | **Database Server** (SQL Server + Postgres + MySQL) | Janus / Windows 10 |
| Normandy | Stage / client onboarding / cloud | Janus / Windows 10 |

## Related pointer — not yet ingested

Confluence INFRA/343506945 notes: "VM INSTANCE DOCUMENTATION IS LOCATED HERE" pointing at CORE space page `CORE/800489527`. That CORE page is outside the current TECH/INFRA ingest scope — follow-up to pull in.

## See Also

- [[Azure]] — broader Azure overview; per-env resource table uses this naming convention
- [[Prefect]] — `aldcprod*`-named resources in QA subscription (naming gotcha)
- [[azure-environments]] — subscription-to-environment model
- [[eclipse-azure-deployment]] — deploy slots named per this convention
- [[azure-environment-bootstrap]] — the runbook that produces these resources
- `vault/infra-credentials.md` — per-VM admin credentials + Galactica SQL Server credentials
