---
tags: [concept, architecture, prefect, azure, cost, infrastructure]
aliases: [Prefect Cost Analysis, Azure Cost Model]
sources: [conversation 2026-05-03, Azure CLI queries against Production 2 subscription]
created: 2026-05-03
updated: 2026-05-03
---

# Prefect Infrastructure Cost Analysis

Cost model for ALDC's self-hosted [[Prefect]] infrastructure on Azure (Canada Central). Analysis performed 2026-05-03 by querying actual Azure resource SKUs and comparing against Prefect Cloud pricing.

## Key Findings

1. **Self-hosted is the right call.** At 141 deployments (47 connectors x 3 environments), Prefect Cloud requires Enterprise tier (custom pricing, likely $1K+/month). Self-hosted runs ~$155–495/month.
2. **Prefect Cloud no longer charges per-task-run.** Current model is seat-based + serverless compute minutes. The original per-task-run concern is moot.
3. **Infrastructure is significantly overprovisioned** for current load (1 active connector). Right-sizing saves ~$335–370/month.
4. **ACI Spot Containers are NOT available in Canada Central** — only East US 2, West Europe, West US. Not viable for this setup.

## Actual Azure Resource SKUs (confirmed via `az` CLI)

| Resource | Name | Actual SKU | Spec | Resource Group |
|----------|------|-----------|------|----------------|
| App Service Plan | `aldcprodapspprefectserver1c01` | **P2v3 PremiumV3** | 2 vCPU, 8 GiB | `aldcprodrsgpconnector1c` |
| PostgreSQL Flexible Server | `aldcprodpgdbconnector1c01` | **Standard_D2ads_v5 GeneralPurpose** | 2 vCore, 8 GiB, 64 GB P6 storage, v17 | `aldcprodrsgpconnector1c` |
| VM (jump host) | `aldcprodvmconnector1c01` | **Standard_D2as_v5** | 2 vCPU, 8 GiB, Linux, **deallocated** | `aldcprodrsgpconnector1c` |
| Container App (QA worker) | `aldcprodctapprefectwpqa1c01` | Consumption | 0.5 vCPU, 1 GiB, min/max replicas: 1 | (Container App Env) |
| Container App (UAT worker) | `aldcprodctapprefectwpuat1c01` | Consumption | 0.5 vCPU, 1 GiB, min/max replicas: 1 | (Container App Env) |
| Container App (Prod worker) | `aldcprodctapprefectworkpool1c01` | Consumption | 0.5 vCPU, 1 GiB, min/max replicas: 1 | (Container App Env) |
| ACI workers (ephemeral) | per-run | per-deployment | ~1 vCPU, 1.5 GiB, ~3 min avg | `aldcprodrsgpprefectworkers1c` |

All resources in **Production 2** subscription (`6389f755-3ff7-488a-a56c-7ea8297730bc`), Canada Central.

## Monthly Cost Breakdown

### Current State (actual SKUs)

| Component | SKU | Est. $/month | Notes |
|-----------|-----|-------------|-------|
| App Service Plan (P2v3) | PremiumV3 | **~$175–200** | Hosts Prefect Server UI/API |
| PostgreSQL (D2ads_v5 + 64GB P6) | GeneralPurpose | **~$140–165** | Prefect metadata store |
| Container Apps (3 workers) | 0.5 vCPU, 1 GiB × 3 | **~$113** | Always-on, polling work queues |
| ACI ephemeral (full migration) | per-run | **~$12** | 47 connectors × 3 envs × 3 min avg |
| VM jump host (deallocated) | D2as_v5 | **~$4** | Disk only while stopped |
| Private DNS Zone | — | **~$0.50** | |
| **Total (current SKUs)** | | **~$445–495** | |

### Container Apps Cost Detail

3 workers × 0.5 vCPU × 1 GiB, running 24/7:

| Component | Calculation | $/month |
|-----------|------------|---------|
| vCPU | (3 × 0.5 × 730 hr × 3600 s) − 180K free = 3,762,000 × $0.000024 | $90 |
| Memory | (3 × 1.0 × 730 hr × 3600 s) − 360K free = 7,524,000 × $0.000003 | $23 |
| **Subtotal** | | **$113** |

### ACI Ephemeral Cost by Scale

Rates (Canada Central approx): ~$0.049/vCPU-hr, ~$0.0054/GiB-hr. Assuming 1 vCPU, 1.5 GiB, ~3 min avg per run.

| Scenario | Runs/day | vCPU $/mo | Memory $/mo | Total |
|----------|---------|-----------|------------|-------|
| Current (1 connector × 3 envs) | 3 | $0.22 | $0.04 | $0.26 |
| 17 connectors × 3 envs | 51 | $3.75 | $0.61 | $4.36 |
| 47 connectors × 3 envs (full migration) | 141 | $10.37 | $1.71 | $12.08 |

### PostgreSQL Pricing (confirmed Canada Central)

| SKU | Tier | $/month | Spec |
|-----|------|---------|------|
| B1ms | Burstable | $12.41 | 1 vCore, 2 GiB |
| B2ms | Burstable | $99.28 | 2 vCores, 8 GiB |
| **Standard_D2ads_v5** | **GeneralPurpose (current)** | **~$140–165** | **2 vCores, 8 GiB** |

Storage: $0.115/GiB/month. Current 64 GB = ~$7.37/month.

## Right-Sizing Recommendations

| Component | Current | Recommended | Monthly Savings |
|-----------|---------|------------|----------------|
| App Service Plan | P2v3 ($175–200) | B2 ($26) or S1 ($55) if VNET needed | $120–174 |
| PostgreSQL | D2ads_v5 GeneralPurpose ($140–165) | B1ms Burstable ($12) + 32GB ($3.70) | $124–149 |
| Container App workers | 0.5 vCPU / 1 GiB ($113) | 0.25 vCPU / 0.5 GiB (~$55) | ~$58 |
| **Total savings** | | | **~$302–381** |
| **Right-sized total** | | **~$110–125/month** | |

**VNET caveat:** If the App Service needs VNET integration to reach PostgreSQL's private endpoint, B-tier won't work — S1 ($55/month) is the minimum tier supporting VNET integration. Verify whether Prefect Server connects via private endpoint or public connection string before downsizing.

**Worker sizing caveat:** Workers poll the Prefect API for queued runs. 0.25 vCPU / 0.5 GiB should suffice for polling, but test with a few connectors before committing across all 3 workers.

## Prefect Cloud Comparison

Prefect Cloud pricing (2026) is seat-based, not per-task-run:

| Tier | $/month | Developers | Deployments | Serverless Min |
|------|---------|-----------|------------|----------------|
| Hobby | Free | 2 | 5 | 500 |
| Starter | $100 | 3 | 20 | 4,500 |
| Team | $400 | 8 | 50 | 13,500 |
| Enterprise | Custom | Unlimited | Unlimited | Unlimited |

47 connectors × 3 environments = **141 deployments** — exceeds Starter (20) and Team (50). Enterprise required.

Even with Prefect Cloud, you'd still need Azure compute (Container Apps workers + ACI ephemeral). Cloud only replaces the orchestration layer (App Service + PostgreSQL), saving ~$180–365/month at current SKUs but costing $1K+/month for Enterprise. Self-hosted wins.

## ACI Spot Containers — Not Viable

| Constraint | Detail |
|-----------|--------|
| Region lock | Only available in East US 2, West Europe, West US |
| VNET restriction | Cannot deploy into VNETs |
| No SLA | Excluded from service level agreements |
| Preview status | Not recommended for production |
| No maxPrice | Unlike Spot VMs, no custom eviction policies |

Moving compute to a US region for Spot savings would add latency to Canada-hosted [[Snowflake]] and break data residency posture.

## Verification Commands

Run against Production 2 subscription (`6389f755-3ff7-488a-a56c-7ea8297730bc`):

```powershell
az account set --subscription "6389f755-3ff7-488a-a56c-7ea8297730bc"
az appservice plan show --name aldcprodapspprefectserver1c01 -g aldcprodrsgpconnector1c --query sku
az postgres flexible-server show --name aldcprodpgdbconnector1c01 -g aldcprodrsgpconnector1c --query sku
az vm show --name aldcprodvmconnector1c01 -g aldcprodrsgpconnector1c --query hardwareProfile.vmSize
```

For actual spend (last 30 days), use Azure Cost Analysis filtered by resource groups `aldcprodrsgpconnector1c` and `aldcprodrsgpprefectworkers1c`.

## See Also

- [[Prefect]] — orchestration platform overview, migration context, Work Pool architecture
- [[azure-environments]] — subscription-to-environment mapping
- [[deployment-groups]] — Azure resource inventory by environment
- [[GP-218]] — QA/UAT/Prod Work Pool setup (Container Apps, worker YAML specs)
- [[prefect-connector-deployment]] — deployment runbook
