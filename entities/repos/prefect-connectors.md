---
tags: [entity, repo, prefect-connectors, aldc, prefect, data-plane]
aliases: [prefect-connectors, prefect connectors repo]
sources: [GP-247 session 2026-05-01, entities/repos/connector.md, entities/tools/prefect.md]
created: 2026-05-01
updated: 2026-05-01
---

# prefect-connectors

ALDC's Prefect v3 connector runtime. Forked from the `operation-fiasco` branch of [[connector]] on 2026-05-01 (GP-247). Houses Prefect flow definitions that pull data from source APIs/DBs → Azure Blob Storage → Snowflake, replacing the legacy BaseConnector / Eclipse agent architecture.

GitHub: `ALDC-io/prefect-connectors`
Docker: `ghcr.io/aldc-io/prefect-connectors`

## Role in the pipeline

Replaces [[connector]] (legacy) as the data-plane repo for Prefect-based connectors:

```
Source APIs / DBs
        │
        ▼
prefect-connectors (Prefect flow, runs in ACI via Work Pool)
        │  writes pulled data
        ▼
Azure Blob Storage  ◄──── transport layer
        │
        │  Snowflake COPY INTO / MERGE
        ▼
Snowflake DWH
```

The legacy [[connector]] repo continues running on-prem Docker agents for all unconverted connectors. It is NOT archived until every connector has been migrated, validated, and cut over — per-connector.

## Branch model

| Branch | Docker tag | Work Pool | Snowflake target | Purpose |
|---|---|---|---|---|
| `main` | `:main` | Prod Work Pool | `PROD_DG1_GEP` (wj66376) | Production |
| `uat` | `:uat` | UAT Work Pool | `TEST_DG1_GEP_PREFECT` (og35375) | Navira client-facing UAT |
| `development` | `:development` | QA Work Pool | `QA_DG1_GEP_PREFECT` (og35375) | ALDC internal QA |
| `feature/*` | — | Local `serve-local` | `QA_DG1_ALDC_QA` | Individual dev |

**Promotion path:** `feature/*` → `development` (ALDC QA) → `uat` (Navira UAT) → `main` (prod)

`uat` is a snapshot — frozen during Navira review while `development` stays open for new feature work.

**Why `uat` not `staging`:** Azure App Service uses "staging slot" for blue-green deploys — naming a branch `staging` collides with that vocabulary.

## Architecture

| Layer | Location | Pattern |
|---|---|---|
| Prefect bootstrap | `main.py → DeploymentRunner` | Registers block schemas, registers deployments |
| Account registry | `connector/account_registry.py` | Auto-discovers `connector/accounts/*/account.py` |
| Account pattern | `connector/accounts/<ACCOUNT>/account.py` | Must export `ACCOUNT: Account` |
| Deployment pattern | `connector/accounts/<ACCOUNT>/deployments/<name>.py` | `@account.register_flow()` decorator |
| Reference implementation | `connector/accounts/ALDC_QA/deployments/exchange_rates.py` | 43-line reference |
| Output handling | `BaseConnector.add_response()` | Parquet → Azure blob → Snowflake staging/merge |
| Test framework | `tests/conftest.py` + `tests/test_*.py` | Session-scoped `prefect_test_harness`, mocked Block/Azure/Snowflake fixtures |
| CI quality gate | `.github/workflows/quality-gate.yml` | Semgrep · TruffleHog · pytest · PyTestArch · Claude Opus review |
| Docker publish | `.github/workflows/docker-publish.yml` | Builds and pushes to GHCR on merge to `main`/`uat`/`development` |

## Known issues / gotchas

### Windows entrypoint path (FIXED — 2026-05-01)
`account.py:build_deployments()` derived entrypoint paths from local file paths. On Windows this generated backslashes (`connector\accounts\...`) that Linux ACI containers couldn't resolve. Fixed: `build_deployments()` normalizes `\\` → `/` after `ato_deployment()`.

### Prefect events WebSocket (MITIGATED — 2026-05-01)
`PrefectEventsClient` doesn't include `Authorization` header in WebSocket handshakes. Azure App Service proxy blocks WebSocket auth, so `/api/events/in` returns HTTP 403 even with correct credentials. This crashes the ACI container with exit code 1.

**Mitigation:** `sitecustomize.py` in the Docker image patches `get_events_client` to return `NullEventsClient` when `PREFECT_API_AUTH_STRING` is set. Events streaming (task-run UI visibility) is disabled; flow execution is unaffected.

**Permanent fix:** Either upgrade Prefect when upstream adds WebSocket Basic auth support, or configure TLS mutual auth between ACI and App Service to bypass the proxy auth layer.

### GHCR credentials block
The Prefect server's `ghcr-io-aldc-io` `DockerRegistryCredentials` block was set to `brayden-marshall` (offboarded). Updated to `russell94paul` on 2026-05-01. If this account changes, update the block via `prefect_docker.DockerRegistryCredentials(...).save('ghcr-io-aldc-io', overwrite=True)`.

### WebSockets on App Service
`aldcprodwbapprefectserver1c01` had `webSocketsEnabled: false` by default. Enabled 2026-05-01. If the App Service is ever recreated, re-enable: `az webapp config set --web-sockets-enabled true`.

## Prefect infrastructure

All resources in `aldcprodrsgpconnector1c` (Production 2 subscription `6389f755-...`). See [[Prefect]] for full resource table.

- **Server:** `https://prefect.analyticlabs.io` (`aldcprodwbapprefectserver1c01`)
- **Work Pool:** `azure-aci-production` (`aldcprodctapprefectworkpool1c01`, ACI-based)
- **Workers RG:** `aldcprodrsgpprefectworkers1c`
- **Managed Identity:** `aldcprodmgidprefectworkers1c` (attached to each ACI worker container)

Auth: HTTP Basic auth via `PREFECT_API_AUTH_STRING`. Retrieve password:
```bash
az webapp config appsettings list --name aldcprodwbapprefectserver1c01 \
  --resource-group aldcprodrsgpconnector1c \
  --subscription 6389f755-3ff7-488a-a56c-7ea8297730bc \
  --query "[?name=='PREFECT_API_AUTH_STRING'].value" -o tsv
```

## Smoke test result (GP-247, 2026-05-01)

Flow run `astute-waxbill` (UUID `ef442cb4`): **COMPLETED**
- Image: `ghcr.io/aldc-io/prefect-connectors:development`
- Work Pool: `azure-aci-production` (`ENVIRONMENT_LEVEL=qa`)
- Snowflake target: `QA_DG1_ALDC_QA.EXCHANGE_RATES.*` on og35375
- All pipeline layers proven: GHCR pull → managed identity → Prefect server → Snowflake

## See Also

- [[connector]] — legacy data-plane repo (still live, do NOT archive)
- [[Prefect]] — orchestration infrastructure, Azure resources, Work Pool config
- [[connector-development-standards]] — canonical Prefect connector pattern
- [[phase-0-prefect-foundation]] — Phase 0 sprint results and roadmap
- [[azure-environments]] — subscription map
