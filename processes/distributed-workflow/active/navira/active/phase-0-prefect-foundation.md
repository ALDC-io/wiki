---
tags: [workflow, navira, phase-0, prefect, foundation, connector, infrastructure, priority-0]
aliases: [Navira Phase 0, Prefect Foundation]
sources: [connector repo review 2026-04-27, entities/tools/prefect.md, concepts/patterns/connector-development-standards.md, prefect-v3-reference, prefect-v3-patterns]
created: 2026-04-27
updated: 2026-04-30 (session 4 — Jira alignment)
---

# Phase 0 — Prefect Foundation & Connector Migration

**Priority:** 0 (prerequisite for all other phases) · **Status:** In Progress (Sprints 0A–0D merged to `operation-fiasco`; G1 PR #118 merged 2026-04-30; Sellercloud migration next)

This phase proves the Prefect connector pattern end-to-end by migrating 1–2 existing production connectors, then hardens the framework for the 17 new connectors in Phases 1A–4. All cross-cutting concerns (CC1–CC7) are resolved here.

## Architecture Assessment (2026-04-27)

The existing Prefect implementation in the `connector` repo (`operation-fiasco` branch) was reviewed. **The core pattern is sound** — the 3-class hierarchy, auto-registration, and Snowflake loading pipeline should be kept. Six gaps need closing before scaling to 17 connectors.

### What to keep

- `@account.register_flow()` decorator → Prefect flow registration
- `BaseConnector[ConnectionType, OptionsType]` generic hierarchy with auto-registration metaclass
- `ConnectorConnectionBase` extending Prefect `Block` (encrypted secrets via `SecretStr`)
- `add_response()` → Parquet → Azure blob → Snowflake staging → merge pipeline
- `MergeScheme` / `PartitionScheme` concepts
- `DeploymentRunner` CLI entry point (`main.py serve-local` / `deploy-image`)
- Reference implementations: `exchange_rates.py` (43 lines), `nextcloud_csv.py` (43 lines)

### Gaps to close

| # | Gap | Location | Impact |
|---|---|---|---|
| G1 | `DateWindow` partition not implemented | `base_connector.py:711` (FIXME) | Can't do rolling lookback windows for ad platform APIs (Google Ads retroactively adjusts 7–30 days) |
| G2 | No pytest framework | `tests/verify_nextcloud.py` is a script, not pytest | Each connector needs custom test logic; no mocks for blocks/connections |
| G3 | Account discovery hardcoded | `account_registry.py:58` only registers `ALDC_QA` | Adding Navira account requires code change |
| G4 | `run()` only accepts date-based options | `ConnectorRunOptions` = date or empty | Ad APIs need pagination tokens, cursor state, rate limit backoff context |
| G5 | ~~No structured logging/alerting~~ | ✅ Done 2026-04-29 | `get_run_logger()` in `run_workflow()` + `_upload_data()`; `log_prints=True` + `on_failure` hook in `register_flow()` |
| G6 | No connector scaffold/generator | Copy-paste from reference impl | Repetitive; easy to miss steps |

---

## Sprint 0A — Full E2E Proven (2026-04-28) ✅

ExchangeRates connector running fully end-to-end through the Prefect pipeline — API call through to Snowflake data landing, COMBINED + CURRENT views created, flow state `COMPLETED`.

### Final E2E result

| Metric | Value |
|---|---|
| **Flow state** | `COMPLETED` |
| **Run name** | `tangible-hoatzin` |
| **Tables created** | 6 (`HISTORY_EXCHANGE_RATES` through `_5`) |
| **Views created** | `COMBINED_HISTORY_EXCHANGE_RATES`, `CURRENT_HISTORY_EXCHANGE_RATES` |
| **Total rows** | 1,032 (172 rates × 3 days × ~2 partitions) |
| **Base currency** | USD |
| **Date range** | 2026-04-26 to 2026-04-28 |
| **Columns** | `BASE`, `CONVERSION`, `DATE`, `TARGET` + 11 metadata columns. Clean — no artifacts. |
| **Snowflake target** | `QA_DG1_ALDC_QA.EXCHANGE_RATES.*` on og35375 (TEST) |

### What was done (chronological)

1. **Branch:** `operation-fiasco` confirmed as the correct base (wiki + team convention)
2. **`deployment_runner.py` fix:** Added `_build_serve_deployments()` method that builds deployments without `work_queue_name` — required for `serve-local` to work. The original `build_all_deployments()` includes `work_queue_name` which needs a work pool.
3. **Venv:** Python 3.13 + Prefect 3.6.9 + all deps already installed
4. **Local Prefect server:** `prefect server start` → healthy at `http://127.0.0.1:4200`
5. **Block registration — API key:** Initial key from Eclipse connection file (`d6768177...`) was free-tier, blocking USD base. Updated to paid-tier key from Dashlane (`2ca5cbab...`, Professional plan under `support@aldc.io`).
6. **Block registration — Snowflake:** Password retrieved programmatically from CosmosDB (`aldcqacsdb1c01` → `core.account_secret` → `f49f9aa3.snowflake_service_core_password`). Block `snowflake-qa-aldc-qa` registered with real credentials.
7. **Account naming investigation:** Attempted rename to `PREFECT_DEV` but reverted — `short_code` is overloaded as both display name AND module path (`connector.accounts.{short_code}.deployments`). Renaming requires directory rename or G3 fix. Account remains `id="f49f9aa3", short_code="ALDC_QA"`.
8. **FIXME fix:** Removed `random_field = random.randbytes(10).hex()` from `exchangeratesapi.py`. This was creating a unique random column per run, polluting the schema registry and breaking the COMBINED view.
9. **Old table cleanup:** Dropped 10 pre-existing tables (`HISTORY_EXCHANGE_RATES` through `_9`) — all had random columns from the FIXME. Clean slate for final run.
10. **Final run:** `COMPLETED` — full pipeline green.

### What this proves

- **Full pipeline:** API call → DataFrame → `add_response()` → Parquet → Azure blob → Snowflake staging → merge → COMBINED view → CURRENT view
- **3-class connector pattern:** `ExchangeRatesApiConnection` (Block) + `ExchangeRatesApiOptions` + `ExchangeRatesApiConnector(BaseConnector[C, O])` works
- **Block-based credentials:** Both connector API key and Snowflake credentials loaded from Prefect blocks
- **Snowflake credential automation:** CosmosDB (`aldcqacsdb1c01`) → `account_secret` container → `snowflake_service_core_password` field. No manual password management needed.
- **`PartitionSchemeDateExact`:** Iterates `time_to_live=3` days, calls `run()` per date, each date creates/merges correctly
- **Schema versioning:** Framework creates new table versions when schema changes, COMBINED view UNIONs all versions

### Key findings and gotchas

**`connector/__init__.py` import-time config:** Calls `get_global_config()` at import time, requiring all env vars (`CORE_URL`, `CORE_API_TOKEN`, `ENVIRONMENT_LEVEL`, `ENVIRONMENT_DEPLOYMENT_GROUP`) via `.env` or the process aborts. The `.env` file has dummy values for `CORE_URL` and `CORE_API_TOKEN` which is fine for local dev.

**`short_code` is overloaded (G3 blocker):** Used for both infrastructure naming (`QA_DG1_{short_code}`, block slugs, tags) AND Python module path (`connector.accounts.{short_code}.deployments`). Cannot rename without also renaming the directory or fixing G3 (auto-discovery).

**exchangeratesapi.io API tier:** Free tier returns `base_currency_access_restricted` for non-EUR base. ALDC has a Professional plan (`support@aldc.io`). The old Eclipse connection file had a different (free-tier?) key. Paid key: `2ca5cbab84b8b2d481b5fc976acf3524`.

**Snapshot naming collision:** Table snapshots named `{TABLE}__PREFECT_SNAPSHOT_{ts}` get picked up by the framework's schema scanner (which finds all tables matching `{TOPIC}_{TABLE}%`). Snapshots must use a separate schema or a prefix that doesn't match the topic/table pattern. Tracked as `/prefect-connector` skill gap.

### `/prefect-connector` skill

Created at `~/.claude/commands/prefect-connector.md`. Codifies the connector development lifecycle: `scoping → implementing → local-test → deployed → verified`. Three modes: new, migrate, modify. Key features added during Sprint 0A:

- **Automated Snowflake credential retrieval** from CosmosDB (Step 2b)
- **Table snapshot safety mechanism** before flow runs (Step 3) — snapshot target tables, restore on failure, cleanup on success
- **Environment reference table** mapping env → Snowflake locator → CosmosDB instance → Azure subscription

### Boot prompt — local Prefect development

```bash
# Start session from connector repo on operation-fiasco
cd C:\Users\PaulRussell\repos\connector
git checkout operation-fiasco

# Prerequisites
.venv/Scripts/python -c "import prefect; print(f'Prefect {prefect.__version__}')"

# Start Prefect server (separate terminal or background)
.venv/Scripts/prefect server start

# Register Snowflake block (one-time — retrieves password from CosmosDB)
# Requires: az account set --subscription "Quality 1"
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python -c "
import asyncio
from azure.cosmos import CosmosClient
from prefect_snowflake import SnowflakeCredentials
from pydantic import SecretStr
import os; os.environ['PREFECT_API_URL'] = 'http://127.0.0.1:4200/api'

async def main():
    client = CosmosClient('https://aldcqacsdb1c01.documents.azure.com:443/', '<cosmos_key>')
    items = list(client.get_database_client('core').get_container_client('account_secret').query_items(
        query=\"\"\"SELECT c.snowflake_service_core_password FROM c WHERE c.id = 'f49f9aa3'\"\"\",
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

# Register connector-specific block (ExchangeRates example)
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python -c "
import asyncio
from connector.connectors.exchangeratesapi import ExchangeRatesApiConnection
async def main():
    conn = ExchangeRatesApiConnection(client_key='<paid_api_key>')
    await conn.save('exchange-rates-api-aldc-qa', overwrite=True)
asyncio.run(main())
"

# Serve all deployments locally
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/python main.py serve_local

# Trigger a deployment run
PREFECT_API_URL=http://127.0.0.1:4200/api .venv/Scripts/prefect deployment run "Exchange Rates - ALDC_QA/Exchange Rates - ALDC_QA"

# Check run result
curl -s http://127.0.0.1:4200/api/flow_runs/<id> | python -m json.tool
```

### Boot prompt — G3 complete (merged 2026-04-29)

G3 is done. See Sprint 0D below for results, decisions, and the GEP account setup prereqs.

### Boot prompt — GP-247: Fork connector repo → prefect-connectors

````
You are working on **GP-247** (Fork connector repo → prefect-connectors).

**Goal:** Create `ALDC-io/prefect-connectors` repo from `operation-fiasco` branch, set up branch protection, CI secrets, and verify first Docker push + QA Work Pool deployment.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read `C:\Users\PaulRussell\repos\wiki\entities\repos\connector.md` — legacy repo context
3. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\prefect.md` — existing Prefect Server infrastructure (Azure resources, Work Pool architecture, environment switching)
4. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\phase-0-prefect-foundation.md` — Phase 0 status + connector promotion lifecycle
5. In the connector repo: `git log --oneline operation-fiasco -10` to confirm latest state

**Existing Prefect infrastructure (Brayden built this):**
- Server: `aldcprodwbapprefectserver1c01` at `https://prefect.analyticlabs.io`
- Work Pool: `aldcprodctappprefectworkpool1c01` (ACI-based)
- Database: `aldcprodpgdbconnector1c01` (Azure Postgres, VNET-private)
- Workers: auto-generated ACI in `aldcprodrsgpprefectworkers1c`
- Environment switching: `ENVIRONMENT_LEVEL` + `ENVIRONMENT_DEPLOYMENT_GROUP` env vars on Work Pool

**Steps:**
1. Create `ALDC-io/prefect-connectors` repo on GitHub (empty, then push operation-fiasco content as `main`)
2. Create `development` branch from `main`
3. Set branch protection: require PR + CI pass for both `main` and `development`
4. Configure GitHub Actions secrets: GHCR token, Azure credentials, Snowflake test/prod credentials
5. Update Dockerfile, CI workflows, CLAUDE.md, README — reference `prefect-connectors` not `connector`
6. Push first Docker image to `ghcr.io/aldc-io/prefect-connectors`
7. Validate GP-243: hit `https://prefect.analyticlabs.io` — confirm Prefect Server is healthy
8. Register ExchangeRates deployment against QA Work Pool as smoke test
9. Update wiki: [[connector]] repo page (note the fork), [[Prefect]] (reference new repo), [[repo-integration-map]]

**Branch strategy:**
- `main` → Prod Work Pool (`PROD_DG1_GEP` on wj66376)
- `uat` → UAT Work Pool (`TEST_DG1_GEP_PREFECT` on og35375) — Navira client-facing; frozen during client review
- `development` → QA Work Pool (`QA_DG1_GEP_PREFECT` on og35375) — ALDC internal; stays open during UAT
- Feature branches → local dev only

**Promotion path:** `feature/*` → `development` (ALDC QA) → `uat` (Navira UAT) → `main` (prod)

**Why `uat` not `staging`:** Azure App Service uses "staging slot" for blue-green deploys — naming a branch `staging` would collide with that vocabulary when discussing Azure infra. `uat` is unambiguous.

**Scope:** Repo creation + infrastructure validation. Do NOT migrate any connectors in this ticket — that's GP-219 (Sellercloud).
````

### Boot prompt — GP-248: Snowflake Environment Isolation

````
You are working on **GP-248** (Prefect Snowflake Environment Isolation — QA, UAT, Prod Staging Databases + PBI Workspaces).

**Goal:** Create 3 isolated Snowflake databases and 2 PBI workspaces for the Prefect connector migration. Zero impact on legacy production data.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\prefect.md` — existing Prefect infrastructure + environment switching mechanism
3. Read `C:\Users\PaulRussell\repos\wiki\concepts\architecture\azure-environments.md` — subscription model
4. Read `C:\Users\PaulRussell\repos\wiki\concepts\patterns\sandbox-feature-delivery.md` — existing sandbox pattern (references TEST_DG1_GEP structure)
5. Read `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\navira\active\phase-0-prefect-foundation.md` — the Snowflake Environment Model table and promotion lifecycle

**What to create:**

Snowflake databases:
1. `QA_DG1_GEP_PREFECT` on og35375 — `CREATE DATABASE QA_DG1_GEP_PREFECT CLONE TEST_DG1_GEP;` (inherits schemas + prod data share)
2. `TEST_DG1_GEP_PREFECT` on og35375 — `CREATE DATABASE TEST_DG1_GEP_PREFECT CLONE TEST_DG1_GEP;` (client UAT)
3. `PROD_DG1_GEP_PREFECT` on wj66376 — `CREATE DATABASE PROD_DG1_GEP_PREFECT;` (empty, create schemas: WAREHOUSE, WAREHOUSE_SOURCE, REPORT_COMMON)

Service accounts:
- QA/UAT (og35375): dedicated Prefect role with write access to `QA_DG1_GEP_PREFECT` and `TEST_DG1_GEP_PREFECT` only. NO write to `TEST_DG1_GEP`.
- Prod staging (wj66376): dedicated Prefect role with write access to `PROD_DG1_GEP_PREFECT` only. NO write to `PROD_DG1_GEP`.

PBI workspaces:
- "GEP Prefect QA" → `QA_DG1_GEP_PREFECT` (ALDC internal)
- "GEP Prefect Test" → `TEST_DG1_GEP_PREFECT` (Navira client-facing UAT)

**Snowflake credentials:** Use Paul's personal credentials for the setup (SYSADMIN role). Service account passwords from CosmosDB `account_secret` container (same pattern as Sprint 0A).

**Scope:** Database creation + service accounts + PBI workspace creation. Do NOT configure Prefect Work Pool env vars — that's GP-218.
````

### Boot prompt — GP-243: Validate Existing Prefect Server

````
You are working on **GP-243** (Validate existing Prefect Server).

**Goal:** Confirm Brayden's self-hosted Prefect Server on Azure is healthy and accessible. Quick validation — should take under an hour.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\entities\tools\prefect.md` — full resource inventory

**Validation steps:**
1. Hit `https://prefect.analyticlabs.io` in a browser — does the Prefect UI load?
2. Check Azure Portal: is `aldcprodwbapprefectserver1c01` (App Service) running?
3. Check Azure Portal: is `aldcprodpgdbconnector1c01` (Postgres) running?
4. Check Azure Portal: is `aldcprodctappprefectworkpool1c01` (Container App) running?
5. From Prefect UI: can you see the Work Pool? Any existing deployments?
6. Test: `PREFECT_API_URL=https://prefect.analyticlabs.io/api prefect block ls` — does it connect?
7. Test: register a dummy block and verify it persists
8. Check Prefect version — is it compatible with the connector code (Prefect 3.6.9)?
9. Document any issues (expired TLS cert, stale Prefect version, dead Postgres, etc.)

**If the server is DOWN:** Document what's broken. The fix is GP-218's scope, not this ticket. This ticket is diagnosis only.

**Scope:** Validation + documentation. Do NOT configure Work Pools or deploy connectors.
````

---

## Sprint 0D — G3 Account Auto-Discovery (2026-04-29) ✅

G3 complete. PR #117 (`feature/paulrussell/phase-0/g3-account-autodiscovery` → `operation-fiasco`).

### What was built

| File | Change |
|---|---|
| `connector/account_registry.py` | `register_all_accounts()` globs `connector/accounts/*/account.py`, dynamically imports `ACCOUNT` from each — no hardcoded names |
| `connector/accounts/account.py` | `discover_deployments()` accepts optional `package_name` param; catches `ModuleNotFoundError` for accounts with no deployments yet |
| `connector/accounts/ALDC_QA/account.py` | Added `ACCOUNT = ALDC_QA_ACCOUNT` (standard contract export) |
| `connector/accounts/ALDC_QA/__init__.py` | Emptied — registry handles discovery; old call would have caused double-registration |
| `connector/CLAUDE.md` | New — branch model, skill pointer, account contract, test requirements |
| `tests/test_account_registry.py` | 4 tests covering discovery, type safety, no-hardcoding contract, graceful skip of non-conforming modules |

### Account module contract

Every `connector/accounts/*/account.py` must export a top-level variable named `ACCOUNT` of type `Account`. The registry scans for this — no other shared file needs to change when adding a new account.

### GEP account — naming decisions and prereqs

When GEP is ready to run connectors via Prefect:

**Naming:** `connector/accounts/GEP/account.py` with `short_code="GEP"` — no environment suffix. The environment is a runtime concern handled by `setup_account_blocks()`, which creates blocks for all `EnvironmentLevel` values:
```
snowflake-qa-gep   → og35375 (non-prod Snowflake)
snowflake-test-gep → og35375 (non-prod Snowflake)
snowflake-prod-gep → wj66376 (prod Snowflake)
```

**Blocker:** the `id` field in `Account` feeds into Snowflake service account naming:
```
TEST_DG1_CORE_SVC_<id.upper()>
TEST_DG1_ROLE_CORE_SVC_<id.upper()>
```
The real GEP account ID must be looked up from CosmosDB (`aldcqacsdb1c01` → `core` → `account_secret` container) before `connector/accounts/GEP/account.py` can be created. It follows the same pattern as `ALDC_QA` (`id="f49f9aa3"`).

**Do not commit a stub** until the real CosmosDB ID is confirmed. The auto-discovery is proven by the test suite (`test_new_account_discovered_without_registry_change`), not by a premature directory.

**Note on `ALDC_QA` naming:** `ALDC_QA` is a misnomer — the `_QA` suffix reflects where it lives, not that it's environment-scoped. The account concept is per-client, not per-environment. Rename to `ALDC` in a future cleanup.

### Key design decisions

**No real account stub committed to prove auto-discovery.** The smoke test uses `sys.modules` injection to simulate a new account directory, avoiding premature production stubs with fake IDs. The test proves the mechanism without coupling the codebase to accounts that aren't provisioned yet.

**`ALDC_QA/__init__.py` emptied** (not deleted) — the old `discover_deployments()` call there would have caused double-registration when the registry also calls it. The registry is now the single orchestrator of account discovery.

---

## Sprint 0B — pytest Framework (2026-04-29) ✅

G2 complete. `pytest tests/` passes with 15 tests, no real credentials or running Prefect server required.

### What was built

| File | Purpose |
|---|---|
| `tests/conftest.py` | Session fixture infrastructure |
| `tests/test_exchange_rates.py` | 15 tests covering the reference connector |
| `tests/conftest_template.py` | Copy-paste template for new connectors |

**`conftest.py` fixtures:**
- `prefect_test_fixture` — autouse session-scoped `prefect_test_harness` (required for Block subclass support)
- `mock_storage_handler` — patches `StorageAccountHandler` in `base_connector` (for future `run_workflow()` tests)
- `mock_snowflake_client` — patches `SnowflakeClient` in `base_connector` (same)
- `mock_account_infra` — patches `AccountInfrastructureDetails.from_account` as `AsyncMock` (same)
- `collect_ignore = ["test_utils.py"]` — excludes legacy runner script (imports `connector.Router` which no longer exists after the BaseConnector refactor)

**`test_exchange_rates.py` — 15 tests across 4 classes:**
- `TestOptionsValidation` — typed field acceptance, missing-field rejection, wrong-type rejection
- `TestConnectionBlock` — direct Block instantiation (no `.aload()`), URL construction assertions
- `TestRun` — mocks `requests.get` at `connector.connectors.exchangeratesapi.requests.get`, verifies row counts, multi-currency concat (6 rows for 2 currencies × 3 rates), unsupported options type rejection, category/table names
- `TestAddResponse` — verifies all 4 `MetadataColumnName` columns (`___ALDC___GLOBAL_*___`), uppercase normalization, primary key casing, row count

### Key design decisions

**Env vars pre-seeded at top of conftest.py** — `connector/__init__.py` calls `get_global_config()` at module import time and calls `os.abort()` if `CORE_URL`, `CORE_API_TOKEN`, `ENVIRONMENT_LEVEL`, `ENVIRONMENT_DEPLOYMENT_GROUP` are missing. The `os.environ.setdefault()` calls at the top of `conftest.py` (before any imports) are the only reliable fix. If a `.env` file exists, `dotenv.load_dotenv(override=True)` in `global_config.py` will override with real values — both paths work.

**Patch at the use site, not the definition site** — `requests.get` is patched as `connector.connectors.exchangeratesapi.requests.get`, not `requests.get` globally. `StorageAccountHandler`/`SnowflakeClient` patched as `connector.base.base_connector.StorageAccountHandler` etc.

**`run()` tests are fully synchronous** — `run()` is sync; only `run_workflow()` is async. No `pytest-asyncio` needed for Sprint 0B. `pytest-asyncio` is already installed (`mode=STRICT`); use `@pytest.mark.asyncio` when `run_workflow()` tests are added in a later sprint.

### Reliability gap — what this framework does NOT enforce

The framework makes it easy to write correct tests and provides the infrastructure. It does NOT enforce that a developer ships tests with a new connector. Two additions would close that gap:

1. **CI gate** — require `pytest tests/` to pass before a PR merges (GitHub Actions step). Without this, tests are optional.
2. **G6 scaffold** — auto-generate a stub `tests/test_<connector>.py` when `connector scaffold` is run, so tests exist from day one even if minimal.

Until both are in place, the testing pattern relies on discipline rather than enforcement.

### Known issues / tech debt noted

- `base_connector.py:657` — `DeprecationWarning: is_datetime64tz_dtype is deprecated`. Use `isinstance(dtype, pd.DatetimeTZDtype)` instead. Not blocking but will become an error in a future pandas version.
- `tests/test_utils.py` — imports `from connector import Router` (legacy pre-BaseConnector class). File is excluded via `collect_ignore`. Should be deleted or rewritten if ever needed.

### `/prefect-connector` skill — G2 update needed

Add a `pytest` step to the `local-test` stage of the skill:
```
3b. Run tests:
    cd C:\Users\PaulRussell\repos\connector
    .venv/Scripts/python -m pytest tests/test_<connector>.py -v
    All tests must pass before proceeding.
```

---

---

## Sprint 0C — G5 Logging + CI Pipeline (2026-04-29) ✅

### What was built

**G5 — Structured logging (complete):**

| File | Change |
|---|---|
| `connector/base/base_connector.py` | `get_run_logger()` in `run_workflow()` (row counts per partition) and `_upload_data()` (upload, Azure stage, Snowflake merge log lines) |
| `connector/accounts/account.py` | `log_prints=True` + `on_failure=[_on_failure_hook]` wired into `register_flow()`; hook uses `flow_run_logger` (safe outside flow context), emits structured ERROR with flow name, run name, state message |

**CI quality gate (new — full pipeline):**

| File | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Entry point — triggers on PRs to `master`, `development`, `operation-fiasco` |
| `.github/workflows/quality-gate.yml` | Semgrep, TruffleHog, pytest, PyTestArch, Claude Opus review, aggregator gate |
| `REVIEW.md` | Connector-specific review standards for the Opus reviewer (BaseConnector rules, Prefect patterns, known false-positive exclusions) |
| `requirements-test.txt` | Lean test-only deps for CI (8 packages instead of full `requirements.txt`) |

**All 7 CI checks green on PR #116** (feature → operation-fiasco):
`semgrep` · `trufflehog` · `pytest/unit` · `architecture/check` · `claude/review` · `quality-gate` · `semgrep-cloud-platform`

**PR #116 merged 2026-04-29.** Code reviewer recommendations applied before merge. Branch `feature/paulrussell/phase-0/prefect-foundation` closed. Sprints 0A–0C (E2E proof, pytest, logging, CI) now in `operation-fiasco`. G3 continues on `feature/paulrussell/phase-0/g3-account-autodiscovery` cut from updated `operation-fiasco`.

### Branch and PR structure established

```
master
  └── operation-fiasco        ← Prefect migration work; feature PRs target here
        └── feature/paulrussell/phase-0/prefect-foundation  ← PR #116
  └── development             ← Created this session; future staging buffer before master
```

Feature branches should PR into `operation-fiasco`, not `development` or `master` directly. The `development` branch exists as a staging buffer for when `operation-fiasco` is ready to promote.

### Key decisions and gotchas

**PR base must be `operation-fiasco`, not `development` or `master`** — the feature branch was cut from `operation-fiasco`. PRing to `development` or `master` shows the entire `operation-fiasco` divergence as a diff (hundreds of files) and creates merge conflicts. Always PR feature branches to their actual parent.

**`requirements-test.txt` exists for CI speed** — full `requirements.txt` includes pyodbc (needs native ODBC libs), bingads, firebase-admin etc. The lean file installs in ~45s vs several minutes. Keep it in sync with azure-* and prefect package versions when those change in `requirements.txt`.

**pytest command must be `pytest tests/` not `pytest tests/test_*.py`** — the shell glob explicitly passes `test_utils.py` to pytest, bypassing `conftest.py`'s `collect_ignore`. Using `pytest tests/` lets conftest filter it out.

**`on_failure` hook is a stub** — logs to Prefect UI only. Slack/email alerting is deferred. To add Slack: load a `SlackWebhook` block inside `_on_failure_hook` in `account.py`.

---

### Next steps (aligned with roadmap update 2026-04-28)

**Roadmap context:** Target+ moved to Phase 1A (confirmed active spend by Heather). Phase 1B deprioritized (TikTok/Email/Creator Connections not confirmed as current spend). Amazon UK PPC is blocked on Navira authorizing the UK ad profile — no code change needed, just config. Amazon US PPC (708K rows) and CA PPC (68K rows) already live.

**Phase 0 remaining work (in recommended order):**

1. ~~**G2 (pytest framework)**~~ ✅ **Done** — `conftest.py` + mock fixtures + `test_exchange_rates.py` (15 tests) + `conftest_template.py`. `pytest tests/` passes.
2. ~~**G5 (logging)**~~ ✅ **Done** — `get_run_logger()` in `run_workflow()` + `_upload_data()`; `log_prints=True` + `on_failure` hook in `register_flow()`. CI gate enforces `pytest tests/` passes on every PR.
3. ~~**G3 (account auto-discovery)**~~ ✅ **Done** — `register_all_accounts()` globs `connector/accounts/*/account.py`, dynamically imports `ACCOUNT`; GEP account added. PR #117 merged to `operation-fiasco` 2026-04-29.
4. ~~**G1 (DateWindow partition)**~~ ✅ **Done** — `_compute_date_window()` helper + `DateWindow` branch in `run_workflow()`; `ConnectorRunOptionsDateRange` passed to `run()`; 13 tests in `test_base_connector.py`. PR #118 merged to `operation-fiasco` 2026-04-30. Tracked as GP-220 (QA).
5. ~~**Repo fork**~~ ✅ **Done 2026-05-01 (GP-247)** — `ALDC-io/prefect-connectors` live at `github.com/ALDC-io/prefect-connectors`. Branches: `main`/`uat`/`development` with branch protection + org secrets inherited. Docker publish CI pushing to `ghcr.io/aldc-io/prefect-connectors`. Smoke test `astute-waxbill` **COMPLETED** in ACI: API → Parquet → Azure blob → Snowflake. Data in `QA_DG1_ALDC_QA.EXCHANGE_RATES.*` on og35375. Three bugs fixed (Windows entrypoint path, WebSockets disabled on App Service, Prefect events WebSocket crash → `sitecustomize.py` NullEventsClient). See [[prefect-connectors]] for full repo page.
6. **Snowflake environment isolation** (GP-248, S2) — Create 3 isolated databases + 2 PBI workspaces for the Prefect migration. See § Snowflake Environment Model below.
7. **Validate existing Prefect Server** (GP-243, S2) — Brayden's self-hosted server at `https://prefect.analyticlabs.io` already exists. Validate it's healthy, Postgres connected, Work Pool running.
8. **CI/CD pipeline** (GP-217, S3) — GitHub Actions on new repo: merge to `development` → Docker build → GHCR push → QA Work Pool. Merge to `main` → Prod Work Pool.
9. **QA/UAT/Prod Work Pools** (GP-218, S3) — Configure Work Pool env vars per environment (see table below).
10. **Testing protocol** (GP-246, S3) — Formal validation process: compare Prefect output vs legacy Eclipse output, < 1% variance, per-connector sign-off.
11. **Sellercloud migration** (GP-219, S2 build / S3 QA deploy) — First production connector on Prefect. Build locally in S2, deploy to QA via new repo in S3, validate through UAT, promote to prod.
11. **Snapshot naming fix** — Move snapshots to `_PREFECT_SNAPSHOTS` schema so the framework's schema scanner doesn't pick them up.
12. **G4 (extended run options)** — Needed for connectors with pagination, cursors, rate limit context. Can defer until Phase 1A connectors actually need it.
13. **G6 (scaffold CLI)** — Nice-to-have. Defer until we've manually built 2–3 connectors and the pattern is stable.

### Snowflake Environment Model (GP-248)

| Tier | Database | Account | Work Pool / Branch | PBI Workspace | Who Validates |
|---|---|---|---|---|---|
| **Dev** | `QA_DG1_ALDC_QA` | og35375 | Local `serve_local` | None | Paul (local dev) |
| **QA** | `QA_DG1_GEP_PREFECT` | og35375 | QA Work Pool / `development` | GEP Prefect QA (new) | ALDC team |
| **UAT** | `TEST_DG1_GEP_PREFECT` | og35375 | UAT Work Pool / `uat` | GEP Prefect Test (new) | Navira (Heather, Lori) + ALDC |
| **Prod Staging** | `PROD_DG1_GEP_PREFECT` | wj66376 | Prod Work Pool / `main` (staging) | None (SQL only) | Paul |
| **Production** | `PROD_DG1_GEP` | wj66376 | Prod Work Pool / `main` (post-cutover) | GEP Production (existing) | Everyone |

**Safety rules:**
- Service accounts per tier — prod staging role has NO write access to `PROD_DG1_GEP`
- Legacy databases (`TEST_DG1_GEP`, `PROD_DG1_GEP`) untouched until explicit per-connector cutover
- PBI workspaces fully isolated — no shared credentials between tiers

### Connector promotion lifecycle (every connector follows this)

```
prefect-connectors repo                    connector repo (legacy)
─────────────────────                      ───────────────────────
feature/<connector> → PR → development → PR → uat → PR → main (on-prem agents)

  ┌─ Tier 2: QA ────────────────────┐
  │ QA_DG1_GEP_PREFECT (og35375)    │     PROD_DG1_GEP (wj66376)
  │ ALDC validates row counts,      │←──── Compare via data share
  │ metrics, PBI refresh (GP-246)   │
  └──────────────┬──────────────────┘
                 ↓
  ┌─ Tier 3: UAT ───────────────────┐
  │ TEST_DG1_GEP_PREFECT (og35375)  │
  │ Navira validates in PBI         │
  │ Client sign-off required        │
  └──────────────┬──────────────────┘
                 ↓
           PR → main
                 ↓
  ┌─ Tier 4: Prod Staging ──────────┐
  │ PROD_DG1_GEP_PREFECT (wj66376)  │
  │ Real API pulls on prod infra    │
  │ SQL parity check vs legacy      │
  └──────────────┬──────────────────┘
                 ↓
  ┌─ Tier 5: Production ────────────┐
  │ Switch target → PROD_DG1_GEP    │
  │ Decommission legacy Eclipse     │
  │ connector for this source       │
  └─────────────────────────────────┘
```

Roll out per-connector — don't wait for all (per Mike).

**Parallel (non-blocking):**
- Amazon UK PPC: waiting on Navira to authorize UK ad profile. Once done, add UK profile ID to `MARKETPLACE_PROFILE_MAP` in `marketing_fct_activity.sql`. No connector code changes.

### Deferred design questions

These should be addressed in a future session:

1. **Connector sandbox pattern** — Should Prefect connector development use a create/teardown sandbox DB pattern (like gep-feature) for per-connector validation? Current assessment: probably not needed — connectors write fresh API data to their own topic/table namespace, so there's no risk of corrupting shared data. A persistent dev environment is simpler. Revisit if connector testing needs isolation.

2. **Parent orchestrator skill** — Design a parent skill (e.g., `/feature`) that sequences `/prefect-connector` (data acquisition) → `/gep-feature` (warehouse + PBI delivery) for tickets that need both. Defer until the interface between the two skills is clear from real usage.

3. **`/prefect-connector` skill gaps** — Being tracked inline with `📝 Skill gap:` markers. Known gaps: `deployed` + `verified` stages are placeholders, no pytest step, no account auto-discovery flow, Snowflake admin provisioning step needed, snapshot naming collision with framework schema scanner.

---

## Stages

### Stage 1: Framework Hardening (resolve gaps G1–G6)

**Objective:** Make the framework production-ready for 17+ connectors.

#### 1.1 Complete DateWindow partition (G1) ✅ Done 2026-04-29

`_compute_date_window(reference_date, offset, window_type) → (start, end)` added as a module-level helper in `base_connector.py`. Supports `Day`, `Month`, `Year` window types (`Week` deferred — add when a connector actually needs it). `DateWindow` branch in `run_workflow()` iterates `time_to_live` windows from newest to oldest, clamps `window_end` to today, breaks early on `min_date`, passes `ConnectorRunOptionsDateRange` to `run()`. 13 tests in `tests/test_base_connector.py`.

#### 1.2 Build pytest framework (G2)

Create a reusable test infrastructure in `tests/`:

- `conftest.py` with Prefect `prefect_test_harness` session fixture
- Mock connection blocks (no real API calls needed)
- Mock `StorageAccountHandler` and `SnowflakeClient` for unit testing
- Base test class that verifies: options validation, block loading, `run()` signature, response format
- Template test file for each new connector to copy

**Acceptance:** `pytest tests/` runs all connector tests. A new connector can be tested by copying the template and adding connector-specific assertions.

#### 1.3 Auto-discover accounts (G3)

Modify `AccountRegistry.register_all_accounts()` to scan `connector/accounts/*/account.py` and import + register each `Account` instance dynamically. Adding a new account (e.g., Navira production) should only require creating a new folder + `account.py` — no changes to `account_registry.py`.

**Acceptance:** Adding `connector/accounts/NAVIRA_PROD/account.py` auto-registers without modifying any existing files.

#### 1.4 Extend ConnectorRunOptions (G4)

Add a `ConnectorRunOptionsCustom` variant that accepts arbitrary key-value context. This allows ad platform connectors to pass pagination tokens, cursor state, and API-specific parameters through the partition loop.

Alternatively, allow connectors to override `run_workflow()` for custom partition logic while reusing `_upload_data()` for the Snowflake pipeline.

**Acceptance:** A connector can access custom context in `run()` beyond just date parameters.

#### 1.5 Integrate Prefect logging (G5)

Replace `print()` calls with `get_run_logger()` throughout connectors. Add structured metadata (account, connector name, row counts, duration) to log entries. Configure `log_prints=True` as the default on `@account.register_flow()`.

Add `on_failure` hook to the flow decorator that sends an alert (Slack webhook block or email) with error context.

**Acceptance:** Flow logs appear in Prefect UI. Failed flows trigger an alert with connector name, account, and error message.

#### 1.6 Connector scaffold CLI (G6)

Create a CLI command or script that generates skeleton files for a new connector:

```bash
python -m connector.scaffold --name google_ads --connection-fields "client_id,developer_token,refresh_token" --options-fields "account_id,lookback_days:int"
```

Generates:
- `connector/connectors/google_ads.py` (Connection + Options + Connector skeleton)
- `connector/accounts/NAVIRA_PROD/deployments/google_ads.py` (deployment file)
- `tests/test_google_ads.py` (test skeleton from template)

**Acceptance:** Generated files pass linting and the test skeleton runs (with mocks).

---

### Stage 2: Migrate Existing Connectors (prove end-to-end)

**Objective:** Prove the Prefect pattern works in production by migrating 1–2 connectors that are already running for Navira/GEP.

#### 2.1 Migrate Sellercloud connector

Sellercloud is already in production for Navira Sales Data (Live). Migrating it to Prefect proves:
- The full pipeline works with real data at production scale
- Snowflake loading is correct (reconcile against existing data)
- Block-based credential management works for a complex API (API key + VPN context)
- The migration doesn't disrupt existing data flows

**GEP account credential status (confirmed 2026-04-29):**
- Account: `connector/accounts/GEP/account.py` — `id=da8904db`, `short_code=GEP` (from Test 1 CosmosDB)
- Snowflake service account password confirmed present in Test 1 `account_secret` container
- Target database: `TEST_DG1_GEP` on `og35375.canada-central.azure` (non-prod Snowflake)
- Register the real block with password from CosmosDB (same pattern as ALDC_QA in Sprint 0A) before first connector run

**Steps:**
1. Create typed `SellercloudConnection(ConnectorConnectionBase)` and `SellercloudOptions(ConnectorOptionsBase)` from the existing legacy `connector/connectors/sellercloud*.py` files
2. Implement `SellercloudConnector(BaseConnector[...])` wrapping the existing logic
3. Create `connector/accounts/GEP/deployments/sellercloud.py` (GEP account already in repo)
4. Register Sellercloud connection block in Prefect with credentials from vault
5. Register real Snowflake block for GEP (`snowflake-test-gep`) with password from CosmosDB `account_secret` → `da8904db`
6. Run in QA Prefect against `TEST_DG1_GEP` Snowflake

**Step 6 verification — prod data share comparison:**
Mirror the [[GP-207]] pattern used for warehouse SQL: clone `PROD_DG1_GEP` production data into `TEST_DG1_GEP` via the existing prod→test data share, then compare Prefect output row counts and key totals against the production baseline. This is the connector-side equivalent of the warehouse sandbox pattern — proves Prefect output matches legacy Eclipse output without touching prod.

```sql
-- Example reconciliation check (run in TEST_DG1_GEP after Prefect run)
SELECT COUNT(*), SUM(<key_metric>) FROM TEST_DG1_GEP.<schema>.<table>
-- compare against PROD_DG1_GEP equivalent
```

7. Run Prefect connector alongside legacy Eclipse connector in parallel, compare outputs
8. Cut over when row counts and key metrics match within < 1% variance

**Acceptance:** Sellercloud data lands in `TEST_DG1_GEP` via Prefect with < 1% variance vs legacy Eclipse pipeline. Legacy connector can be decommissioned.

#### 2.2 Migrate Amazon US connector (optional — stretch goal)

Amazon US (Seller Central via SP-API) is the second production connector for Navira. Migrating it validates:
- SP-API OAuth integration works with Prefect blocks
- `PartitionSchemeDateExact` or `DateWindow` handles multi-day pulls correctly
- Multi-marketplace pattern (US first, then UK/CA in Phase 1A are trivial additions)

If Sellercloud migration goes smoothly, this can proceed in parallel. If not, defer to Phase 1A.

---

### Stage 3: Resolve Cross-Cutting Concerns (CC1–CC7)

By completing Stages 1–2, most CC questions are answered empirically:

| CC | Question | Answer (from Stage 1–2) |
|---|---|---|
| CC1 | Ingestion framework | **Confirmed:** `BaseConnector[C, O]` + `run_workflow()` + `add_response()` pattern. Shared across all connectors. |
| CC2 | Scheduling & Orchestration | **Confirmed:** [[Prefect]] with ACI work pools. Cron schedules on deployments. |
| CC3 | Secrets management | **Confirmed:** Prefect Blocks (`ConnectorConnectionBase` extends `Block`). `SecretStr` fields encrypted at rest. |
| CC4 | Monitoring & alerting | **Confirmed:** Prefect UI for flow/task state tracking. `on_failure` hooks for Slack/email alerts (Stage 1.5). |
| CC5 | Snowflake architecture | Partially answered by Stage 2 — production connector validates schema. Marketing schema design still needed for Phase 1A. |
| CC6 | Data quality & reconciliation | **Confirmed:** Stage 2 reconciliation process becomes the template. Add row-count + spend-total assertions to connector tests. |
| CC7 | Change management | **Confirmed:** `operation-fiasco` branch → PR → merge to main. Docker image build → GHCR → ACI work pool deployment. |

**Remaining for Phase 1A:** CC5 (marketing-specific Snowflake schema design) and the credential provisioning from [[navira-credentials-access]].

---

### Gate: Ready for Phase 1A

Phase 0 is complete when:

- [ ] All 6 gaps (G1–G6) closed and merged to `operation-fiasco`
- [ ] At least 1 production connector (Sellercloud) running on Prefect with verified data
- [ ] Navira production account auto-discovered
- [x] pytest framework in place (`conftest.py` + mocks + template) — connector-specific suites added as connectors are migrated
- [ ] CC1–CC4, CC6, CC7 answered with working implementations
- [ ] Connector scaffold generates working skeletons
- [ ] Flow failures trigger alerts

---

## Estimated Effort

| Stage | Effort | Notes |
|---|---|---|
| ~~1.1 DateWindow partition~~ | ~~1 day~~ | ✅ Done 2026-04-30 — `_compute_date_window` + DateWindow branch + 13 tests. PR #118. GP-220 (QA). |
| ~~1.2 Pytest framework~~ | ~~2 days~~ | ✅ Done 2026-04-29 — 15 tests passing |
| ~~1.3 Account auto-discovery~~ | ~~0.5 day~~ | ✅ Done 2026-04-29 — PR #117 merged |
| 1.4 Extend run options | 1 day | Custom context or overridable run_workflow |
| ~~1.5 Prefect logging + alerts~~ | ~~1 day~~ | ✅ Done 2026-04-29 — get_run_logger + on_failure hook; Slack stub deferred |
| 1.6 Connector scaffold CLI | 2 days | Jinja templates + CLI |
| 2.1 Sellercloud migration | 3–5 days | Typed classes + testing + reconciliation |
| 2.2 Amazon US (stretch) | 3–5 days | SP-API + multi-marketplace |
| **Total** | **~10–17 days** | |

---

## See Also

- [[navira/README|Navira Roadmap]] — master hub (this phase feeds into all others)
- [[Prefect]] — ALDC deployment architecture, Azure resources, env switching
- [[prefect-v3-reference]] — Prefect v3 core concepts
- [[prefect-v3-patterns]] — development patterns (retries, caching, testing, Docker/ACI)
- [[connector-development-standards]] — current ALDC connector pattern (to be updated by this phase)
- [[connector]] — repo where all work happens (`operation-fiasco` branch)
- [[phase-1a-marketing-ad-platforms]] — first phase that depends on this foundation
- [[navira-credentials-access]] — credential status for all platforms
