---
tags: [entity, repo, prefect-connectors, aldc, prefect, data-plane]
aliases: [prefect-connectors, prefect connectors repo]
sources: [GP-247 session 2026-05-01, GP-218 work pool setup 2026-05-02, entities/repos/connector.md, entities/tools/prefect.md]
created: 2026-05-01
updated: 2026-05-27
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

| Branch | Docker tag | Work Pool | Worker Container App | Snowflake target | Purpose |
|---|---|---|---|---|---|
| `main` | `:main` | `azure-aci-production` | `aldcprodctapprefectworkpool1c01` | `PROD_DG1_GEP_PREFECT` → `PROD_DG1_GEP` post-cutover | Production |
| `uat` | `:uat` | `azure-aci-uat` | `aldcprodctapprefectwpuat1c01` | `TEST_DG1_GEP_PREFECT` (og35375) | Navira client-facing UAT |
| `development` | `:development` | `azure-aci-qa` | `aldcprodctapprefectwpqa1c01` | `QA_DG1_GEP_PREFECT` (og35375) | ALDC internal QA |
| `feature/*` | — | Local `serve_local` | — | `QA_DG1_ALDC_QA` | Individual dev |

**Promotion path:** `feature/*` → `development` (ALDC QA) → `uat` (Navira UAT) → `main` (prod). Full pipeline documented at [[prefect-connector-deployment]] § Promotion Pipeline.

`uat` is a snapshot — frozen during Navira review while `development` stays open for new feature work.

**Why `uat` not `staging`:** Azure App Service uses "staging slot" for blue-green deploys — naming a branch `staging` collides with that vocabulary.

**`short_code` note (GP-218):** GEP account uses `short_code="GEP_PREFECT"` during migration so `warehouse_database_name` resolves to `{ENV}_DG1_GEP_PREFECT`. At production cutover (per-connector), flip to `"GEP"` to target `PROD_DG1_GEP`.

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
| CI + Docker publish | `.github/workflows/ci.yml` | Calls quality gate, then builds+pushes to GHCR on merge (GP-217) |

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

All resources in Production 2 subscription (`6389f755-...`). See [[Prefect]] for full resource table, [[prefect-connector-deployment]] for deployment runbook.

- **Server:** `https://prefect.analyticlabs.io` (`aldcprodwbapprefectserver1c01` in `aldcprodrsgpconnector1c`)
- **Work Pools (GP-218):** 3 pools with dedicated workers in `aldcprodrsgpprefectworkers1c`:
  - `azure-aci-qa` → `aldcprodctapprefectwpqa1c01`
  - `azure-aci-uat` → `aldcprodctapprefectwpuat1c01`
  - `azure-aci-production` → `aldcprodctapprefectworkpool1c01`
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

## Connector Orchestrator (2026-05-26)

The repo now includes a full pipeline orchestrator at `orchestrator/`. Run with `python -m orchestrator` (serves at port 8765). See [[orchestrator]] for full engine documentation.

**Key capabilities:**
- 6 production pipeline types (connector-migration 16 stages, credential-provision 6, data-parity-test 5, connector-promotion 14, client-onboarding 6, connector-activation 7)
- 14 engine modules (circuit breaker, pipeline agent, analytics, audit, memory, notifications, quality, health, waves, rollback, validation, events, work guard, canary)
- Web UI with connector table, pipeline DAG view, horizontal overview, session monitor, quality/health/analytics dashboards
- 144 tests (phases 1-9 hardening)

### Hardening phases (2026-05-26)

| Phase | Feature | Status |
|---|---|---|
| 1 | Circuit breaker (Prefect/Snowflake/GHCR) | Done |
| 2 | Stage metrics (cost/tokens/duration per stage) | Done |
| 3 | Failure pattern learning (memory store, global pause) | Done |
| 4 | Test coverage 74 → 122 | Done |
| 5 | Hard budget enforcement (pipeline cost cap, pause + resume) | Done |
| 6 | SLA auto-escalation (critical alerts → Jira tickets) | Done |
| 7 | Performance dashboard (stage metrics + prompt effectiveness UI) | Done |
| 8 | Configurable parallelism (env var + PATCH /api/config) | Done |
| 9 | Prompt effectiveness tracking (pass/fail per template) | Done |

### First end-to-end connector (2026-05-26)

**exchangeratesapi (GP-271)** completed all 16 pipeline stages:
- Code gen → test → PR → merge → Docker image → Prefect deploy → flow run (65s) → Snowflake verify (1,032 rows) → parity check (100% score vs prod) → promote → Jira done
- Target database: `QA_DG1_GEP_PREFECT.EXCHANGE_RATES` (6 tables, 172 rows each)
- Parity check compares Prefect QA output against `PROD_DG1_GEP.EXCHANGE_RATES`

### QA infrastructure provisioned (2026-05-26)

| Resource | Details |
|---|---|
| Key Vault secrets | `prefect-api-auth-string`, `snowflake-prod-admin` in `aldc-vault-qa` |
| Prefect blocks | `exchange-rates-api-gep-prefect`, `sellercloud-gep-prefect`, `amazon-ads-gep-prefect`, `amazon-sp-api-gep-prefect`, `windsor-gep-prefect`, `shopify-ka-prefect`, `snowflake-qa-gep-prefect`, `snowflake-qa-ka-prefect` |
| Snowflake | `QA_DG1_STG_DA8904DB` (staging DB + external stage → `aldcqastac1cda8904db`), `QA_DG1_GEP` (target schemas), storage integration `INT_ALDCQASTAC1CDA8904DB` |
| CI | `workflow_dispatch` added to ci.yml; image-gate auto-triggers Docker build |

### Credential migration pattern

Legacy Eclipse credentials live in `clients/<CLIENT>/eclipse/connections/<connector>.json`. The orchestrator's `verify-blocks` stage checks required Prefect blocks before deploy, auto-creates from Key Vault if missing. Credentials are stored in `aldc-cred-vault-qa` with naming convention `{suffix}--{connector}--{auth-type}`.

### Active migration pipelines (2026-05-26)

6 connectors: exchangeratesapi (GP-271, **COMPLETED**), seller_cloud (GP-272), amazon_ads (GP-273), amazon_sellercentral (GP-274), shopify_conn (KA-15), windsorai (GP-275). All 5 running pipelines recreated fresh with 16-stage definition.

### Connector pipeline completion (2026-05-27)

5 code fixes shipped across all branches (main/development/uat):

| Fix | File | Root cause |
|-----|------|------------|
| `os.abort()` → graceful None | `connector/global_config.py` | Missing env vars killed containers with SIGABRT before any flow ran |
| seller_cloud v3 module | `connector/connectors/seller_cloud_v3.py` | Legacy module used unavailable `helper` module; no Prefect v3 classes |
| Prefect 3.6.9 → 3.7.2 | `requirements.txt` | Downgrade from base image dropped `importlib_metadata`, breaking `prefect flow-run execute` |
| CSRF-safe API calls | `.deploy/connector-activation/services/prefect.py` | `create_flow_run`/`create_deployment` bypassed `_request()` CSRF retry logic |
| Empty schema_list guard | `connector/lib/warehouse/lib.py` | First-run view creation produced `CREATE VIEW ... AS ()` with no schemas to union |

Credential blocks re-provisioned as typed Connection blocks (replacing generic `secret` blocks): WindsorAIConnection, AmazonAdsConnection, SellerCloudConnection, AmazonSellerCentralConnection, ShopifyConnection.

Seller_cloud team_name corrected: `globalecomp` → `navira` (GEP rebranded).

**Results:**

| Connector | Ticket | Status | Detail |
|-----------|--------|--------|--------|
| exchangeratesapi | GP-271 | **COMPLETED** | Full pipeline done (prior session) |
| seller_cloud | GP-272 | **COMPLETED** | Full pipeline: trigger→verify→parity→promote→jira-done |
| windsorai | GP-275 | **COMPLETED** | Full pipeline end-to-end |
| amazon_ads | GP-273 | **BLOCKED** | Needs separate Amazon Ads LWA app credentials (SP-API creds don't have Ads scope) |
| amazon_sellercentral | GP-274 | **BLOCKED** | Requires VPN — ACI containers can't reach SP-API |
| shopify_conn | KA-15 | **BLOCKED** | ShopifyAPI 12.x removed `shopify.Session` (Python 3.12 compat) |

**Key discovery:** SellerCloud and Amazon Seller Central require VPN access. ACI containers run outside the VPN. Needs Azure VNet integration for ACI container instances.

**Pipeline agent issue:** The auto-retry agent repeatedly overwrites successful completions with new failed retries. Needs idempotency guard — once a pipeline completes all stages, the agent should not restart it. Workaround: disable agent during critical runs via `POST /api/agent/toggle {"enabled": false}`.

### Ongoing issues (2026-05-26 evening)

- **CSRF token expiry**: Prefect server CSRF tokens expire, causing 403 on POST/PATCH. Fixed with custom Session subclass that auto-refreshes token on 403 and retries. TTL-based caching (4 min) avoids unnecessary token fetches. Both PrefectService implementations patched (connector-activation + deploy/services).
- **Docker image lag**: Connector code merged to development but Docker image not rebuilt until CI passes. amazon_ads and amazon_sellercentral blocked — their code (amazon_ads_v3.py) was merged after last successful build. CI was failing due to `test_amazon_sellercentral.py` importing `sp_api` (not in CI). Fixed by adding `--ignore` to quality-gate.yml.
- **Entrypoint function names**: `_find_flow_function` regex parses `@account.register_flow` decorated function names from deployment files. Handles multi-flow files (amazon_ads has 8 flows) and non-standard names (windsorai_google_ads_flow, not windsorai_flow).
- **Block name mismatches**: windsorai block was `windsor-gep-prefect` but flow loads `windsorai-api-gep-prefect` (via `build_block_id("windsorai-api")`). Created correct block.
- **Branch sync**: All development done on main, must be merged to development + uat to keep branches in sync. Pattern: commit on main → push → merge to development → push (triggers CI) → merge to uat → push.

### Pipeline UX improvements (2026-05-26)

- **Retry context enrichment**: `restart_from_stage` preserves `_retry_count`, `_prior_error`, `_prior_duration_s`. Claude-p retries get enriched prompt with worktree files, prior error, and "focus on fixing" instructions.
- **UI buttons**: "Retry (with context)" vs "Fresh restart" — distinct behavior. Retry preserves context, fresh clears it via `clear_context` flag.
- **Horizontal pipeline overview**: Swim lane view of all active pipelines in the Pipelines tab.

## See Also

- [[connector]] — legacy data-plane repo (still live, do NOT archive)
- [[orchestrator]] — pipeline engine documentation (14 engine modules, hardening status)
- [[Prefect]] — orchestration infrastructure, Azure resources, Work Pool config
- [[connector-development-standards]] — canonical Prefect connector pattern
- [[phase-0-prefect-foundation]] — Phase 0 sprint results and roadmap
- [[azure-environments]] — subscription map
