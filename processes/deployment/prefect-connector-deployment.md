---
tags: [process, deployment, prefect, connector, runbook]
aliases: [Prefect Connector Deployment, prefect-run-guide]
sources: [GP-243 validation 2026-05-01, GP-218 work pool setup 2026-05-02, phase-0-prefect-foundation, prefect-connector skill]
created: 2026-05-01
updated: 2026-05-02
---

# Prefect Connector Deployment Guide

How to run and deploy Prefect connectors in any environment: local dev, Azure QA, and Azure Prod. Covers environment switching and the auth required to reach the Azure server.

See also: [[Prefect]] (architecture + resource inventory), [[prefect-v3-reference]] (Prefect v3 concepts), `/prefect-connector` skill (step-by-step workflow).

---

## Overview

There are four modes of operation:

| Mode | Prefect Server | Work Pool | Snowflake target | Use when |
|---|---|---|---|---|
| **Local** | `http://127.0.0.1:4200` (ephemeral) | — (`serve_local`) | `QA_DG1_ALDC_QA` on og35375 | Building + unit-testing a connector |
| **Azure QA** | `https://prefect.analyticlabs.io` | `azure-aci-qa` | `QA_DG1_{account}` on og35375 | ALDC internal integration testing |
| **Azure UAT** | `https://prefect.analyticlabs.io` | `azure-aci-uat` | `TEST_DG1_{account}` on og35375 | Client-facing UAT (Navira validates in PBI) |
| **Azure Prod** | `https://prefect.analyticlabs.io` | `azure-aci-production` | `PROD_DG1_{account}` on wj66376 | Production runs |

The same Prefect Server serves all environments. The environment is controlled by the **Work Pool** env vars, not by which server you point at. Each pool has a dedicated worker Container App.

---

## Prerequisites

### Tools

- Python venv: `.venv/Scripts/python` exists, `import prefect` succeeds
- Docker: for building images (Azure mode only)
- Azure CLI: logged in (`az account show`)
- GHCR access: `docker login ghcr.io` with a PAT (in `vault/credentials.md` → GitHub)

### Azure server credentials

The Prefect Server uses **HTTP Basic auth**. Retrieve the password:

```bash
az webapp config appsettings list \
  --name aldcprodwbapprefectserver1c01 \
  --resource-group aldcprodrsgpconnector1c \
  --subscription 6389f755-3ff7-488a-a56c-7ea8297730bc \
  --query "[?name=='PREFECT_API_AUTH_STRING'].value" -o tsv
# Returns: prefect-admin:<password>
```

Set these for any Azure session (do not commit to `.env`):

```bash
export PREFECT_API_URL=https://prefect.analyticlabs.io/api
export PREFECT_API_AUTH_STRING=prefect-admin:<password>
```

Verify:
```bash
curl -s -u "prefect-admin:<password>" https://prefect.analyticlabs.io/api/health
# Expected: true
```

---

## Mode 1: Local Development

Run a connector against a local ephemeral Prefect Server. No Azure access required.
Snowflake writes to `QA_DG1_ALDC_QA` on og35375.

### 1. Start Prefect server (Terminal 1)

```bash
cd C:\Users\PaulRussell\repos\connector
git checkout operation-fiasco
.venv/Scripts/prefect server start
# UI available at http://127.0.0.1:4200
```

### 2. Register credential blocks (Terminal 2)

**Connector connection block** (example: ExchangeRates):
```bash
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python -c "
import asyncio, os
os.environ['PREFECT_API_URL'] = 'http://127.0.0.1:4200/api'
from connector.connectors.exchangeratesapi import ExchangeRatesApiConnection
async def main():
    conn = ExchangeRatesApiConnection(client_key='<paid_api_key>')
    await conn.save('exchange-rates-api-aldc-qa', overwrite=True)
asyncio.run(main())
"
```

**Snowflake credentials block** — retrieve password from CosmosDB:
```bash
# 1. Get CosmosDB key (Quality 1 subscription for QA)
az account set --subscription "Quality 1"
COSMOS_KEY=$(az cosmosdb keys list --name aldcqacsdb1c01 \
  --resource-group aldcqarsgp1c --query primaryMasterKey -o tsv)

# 2. Register block
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python -c "
import asyncio, os
os.environ['PREFECT_API_URL'] = 'http://127.0.0.1:4200/api'
from azure.cosmos import CosmosClient
from prefect_snowflake import SnowflakeCredentials
from pydantic import SecretStr

async def main():
    client = CosmosClient('https://aldcqacsdb1c01.documents.azure.com:443/', '$COSMOS_KEY')
    items = list(client.get_database_client('core').get_container_client('account_secret').query_items(
        query=\"SELECT c.snowflake_service_core_password FROM c WHERE c.id = 'f49f9aa3'\",
        enable_cross_partition_query=True))
    creds = SnowflakeCredentials(
        account='og35375.canada-central.azure',
        user='QA_DG1_CORE_SVC_F49F9AA3',
        role='QA_DG1_ROLE_CORE_SVC_F49F9AA3',
        password=SecretStr(items[0]['snowflake_service_core_password']))
    await creds.save('snowflake-qa-aldc-qa', overwrite=True)
    print('Snowflake block registered')
asyncio.run(main())
"
```

Replace `f49f9aa3` and field names with the target account ID and CosmosDB field.

### 3. Serve and trigger

```bash
# Serve all deployments locally
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python main.py serve_local

# In another terminal — trigger a run
PREFECT_API_URL=http://127.0.0.1:4200/api \
  .venv/Scripts/prefect deployment run "Exchange Rates - ALDC_QA/Exchange Rates - ALDC_QA"
```

Monitor at `http://127.0.0.1:4200`.

---

## Mode 2: Azure Deployment

Run a connector on the Azure Prefect Server using the ACI Work Pool. The environment
(QA or Prod) is controlled by which Work Pool env vars are active — see §Environment Switching.

### 1. Point CLI at Azure server

```bash
export PREFECT_API_URL=https://prefect.analyticlabs.io/api
export PREFECT_API_AUTH_STRING=prefect-admin:<password>
```

### 2. Build and push Docker image

```bash
cd C:\Users\PaulRussell\repos\connector
TAG=$(git rev-parse --short HEAD)

docker build -t ghcr.io/aldc-io/connector:$TAG .
docker push ghcr.io/aldc-io/connector:$TAG
```

> GP-217 (CI/CD pipeline) will automate this on merge to `operation-fiasco`. Until then, manual.

### 3. Register credential blocks on the Azure server

Same scripts as local development (§1 Step 2), but with env vars pointing at Azure:

```bash
export PREFECT_API_URL=https://prefect.analyticlabs.io/api
export PREFECT_API_AUTH_STRING=prefect-admin:<password>
# Then run the same block-registration scripts
```

Verify blocks registered:
```bash
curl -s -u "prefect-admin:<password>" \
  -X POST -H "Content-Type: application/json" \
  -d '{"limit": 50}' \
  https://prefect.analyticlabs.io/api/block_documents/filter | \
  python -c "import sys,json; [print(d['name']) for d in json.load(sys.stdin)]"
```

### 4. Deploy to Work Pool

> `main.py deploy_image` is currently a stub (wrong work pool name, placeholder image).
> Use this script until GP-217 fixes it:

```bash
PREFECT_API_URL=https://prefect.analyticlabs.io/api \
PREFECT_API_AUTH_STRING=prefect-admin:<password> \
.venv/Scripts/python -c "
import asyncio, os
os.environ['PREFECT_API_URL'] = 'https://prefect.analyticlabs.io/api'
os.environ['PREFECT_API_AUTH_STRING'] = 'prefect-admin:<password>'
from prefect import deploy
from connector.account_registry import AccountRegistry

async def main():
    AccountRegistry.register_all_accounts()
    deployments = await AccountRegistry.build_all_deployments()
    await deploy(
        *deployments,
        work_pool_name='azure-aci-production',
        image='ghcr.io/aldc-io/connector:<tag>',
        build=False,
        push=False,
    )
asyncio.run(main())
"
```

### 5. Trigger and monitor

```bash
PREFECT_API_URL=https://prefect.analyticlabs.io/api \
PREFECT_API_AUTH_STRING=prefect-admin:<password> \
.venv/Scripts/prefect deployment run "<Flow Name> - <ACCOUNT>/<Flow Name> - <ACCOUNT>"
```

Or use the UI: `https://prefect.analyticlabs.io` → Deployments → Run.

Allow ~2 min for ACI container spin-up before the flow begins executing.

---

## Work Pool Configuration (GP-218)

Three dedicated Work Pools, each with its own worker Container App. Configured 2026-05-02.

### Work Pool matrix

| Work Pool | Worker Container App | `ENVIRONMENT_LEVEL` | `ENVIRONMENT_DEPLOYMENT_GROUP` | Image tag | Snowflake target |
|---|---|---|---|---|---|
| `azure-aci-qa` | `aldcprodctapprefectwpqa1c01` | `qa` | `1` | `:development` | `QA_DG1_{account}` (og35375) |
| `azure-aci-uat` | `aldcprodctapprefectwpuat1c01` | `test` | `1` | `:uat` | `TEST_DG1_{account}` (og35375) |
| `azure-aci-production` | `aldcprodctapprefectworkpool1c01` | `prod` | `1` | `:main` | `PROD_DG1_{account}` (wj66376) |

### Environment map

| `ENVIRONMENT_LEVEL` | `ENVIRONMENT_DEPLOYMENT_GROUP` | Snowflake DB | Account | CosmosDB (for passwords) | Azure sub |
|---|---|---|---|---|---|
| `qa` | `1` | `QA_DG1_{account}` | og35375 | `aldcqacsdb1c01` | Quality 1 |
| `test` | `1` | `TEST_DG1_{account}` | og35375 | `aldctestcsdb1c01` | Test 1 |
| `prod` | `1` | `PROD_DG1_{account}` | wj66376 | `aldcprodcsdb1c01` | Production 2 |

### GEP Snowflake blocks (registered 2026-05-02)

| Block | User | Snowflake Account |
|---|---|---|
| `snowflake-qa-gep-prefect` | `QA_DG1_PREFECT_SVC_DA8904DB` | og35375 |
| `snowflake-test-gep-prefect` | `TEST_DG1_PREFECT_SVC_DA8904DB` | og35375 |
| `snowflake-prod-gep-prefect` | `PROD_DG1_PREFECT_SVC_DA8904DB` | wj66376 |

Passwords in `vault/infra-credentials.md` § Prefect Service Accounts. Registration script: `prefect-connectors/scripts/register_gep_blocks.py`.

---

## Promotion Pipeline

Code flows through branches; each branch maps to a Work Pool and Docker tag. No env var is hardcoded in Python — all reads come from `ENVIRONMENT_LEVEL` + `ENVIRONMENT_DEPLOYMENT_GROUP`.

```
feature/*  ──PR──►  development  ──PR──►  uat  ──PR──►  main
                        │                   │              │
                   CI builds            CI builds      CI builds
                   :development          :uat           :main
                        │                   │              │
                   azure-aci-qa      azure-aci-uat   azure-aci-production
                        │                   │              │
                   QA_DG1_*_PREFECT  TEST_DG1_*_PREFECT  PROD_DG1_*_PREFECT
                        │                   │              │
                   ALDC validates    Navira validates   Production
```

### Promoting a connector

1. **QA:** PR `feature/*` → `development`. CI builds `:development`. QA pool picks up new image on next run. Validate row counts + metrics in `QA_DG1_GEP_PREFECT`. See [[connector-migration-testing]] (GP-246) for formal protocol.
2. **UAT:** PR `development` → `uat`. CI builds `:uat`. UAT pool picks up new image. Navira validates in "GEP Prefect Test" PBI workspace.
3. **Prod:** PR `uat` → `main`. CI builds `:main`. Prod pool picks up new image. Data lands in `PROD_DG1_GEP_PREFECT` (staging). At cutover, flip `short_code` from `GEP_PREFECT` to `GEP` to target `PROD_DG1_GEP`.

### Rollback

Revert the PR on the target branch. On next CI build, the image reverts to the previous code. The next ACI worker run picks up the old image automatically. No manual redeploy needed.

For immediate rollback (before CI completes): update the deployment's `job_variables.image` to a known-good SHA tag (e.g., `ghcr.io/aldc-io/prefect-connectors:<sha>`).

### Moving a single deployment between pools

```python
from prefect.client.schemas.actions import DeploymentUpdate
await client.update_deployment(
    deployment_id=<id>,
    deployment=DeploymentUpdate(work_pool_name="azure-aci-<target>"),
)
```

Or in the Prefect UI: Deployments → Edit → Work Pool.

### Local `.env` environment

For local development, `ENVIRONMENT_LEVEL` and `ENVIRONMENT_DEPLOYMENT_GROUP` come from `.env` in the connector repo root. The defaults are `qa` / `1`.

---

## Azure Resources Quick Reference

All in **Production 2** subscription (`6389f755-3ff7-488a-a56c-7ea8297730bc`).

| Resource | Type | Resource Group | Pool | Status (2026-05-02) |
|---|---|---|---|---|
| `aldcprodwbapprefectserver1c01` | App Service (Prefect Server) | `aldcprodrsgpconnector1c` | — | Running |
| `aldcprodpgdbconnector1c01` | Azure Postgres v17 | `aldcprodrsgpconnector1c` | — | Ready |
| `aldcprodctapprefectworkpool1c01` | Container App (Prod Worker) | `aldcprodrsgpprefectworkers1c` | `azure-aci-production` | Running |
| `aldcprodctapprefectwpqa1c01` | Container App (QA Worker) | `aldcprodrsgpprefectworkers1c` | `azure-aci-qa` | Running |
| `aldcprodctapprefectwpuat1c01` | Container App (UAT Worker) | `aldcprodrsgpprefectworkers1c` | `azure-aci-uat` | Running |
| `aldcprodmgidprefectworkers1c` | Managed Identity | `aldcprodrsgpprefectworkers1c` | — | — |

Worker image: `prefecthq/prefect-azure:0.4.9-python3.14` (all 3 workers).
Setup scripts: `prefect-connectors/scripts/setup_work_pools.py` + `create_tier_workers.ps1`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `prefect block ls` returns `401 Unauthorized` | Missing `PREFECT_API_AUTH_STRING` | Set both `PREFECT_API_URL` and `PREFECT_API_AUTH_STRING` env vars |
| `Missing CSRF token` on POST | Write ops need a CSRF token | Use the Prefect Python client (handles CSRF automatically) instead of raw curl |
| ACI container never starts | Image not pushed or wrong tag | Verify image exists in GHCR; confirm tag matches deployment's `job_variables.image` |
| Flow `FAILED` immediately | Missing blocks on server | Register credential blocks on the Azure server (not just locally) |
| `prefect server start` already running warning | Port 4200 in use | Kill existing: `Get-Process -Name "uvicorn" | Stop-Process` (Windows) |
