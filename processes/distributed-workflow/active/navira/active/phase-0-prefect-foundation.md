---
tags: [workflow, navira, phase-0, prefect, foundation, connector, infrastructure, priority-0]
aliases: [Navira Phase 0, Prefect Foundation]
sources: [connector repo review 2026-04-27, entities/tools/prefect.md, concepts/patterns/connector-development-standards.md, prefect-v3-reference, prefect-v3-patterns]
created: 2026-04-27
updated: 2026-04-29 (session 2)
---

# Phase 0 — Prefect Foundation & Connector Migration

**Priority:** 0 (prerequisite for all other phases) · **Status:** In Progress (Sprints 0A–0C merged to `operation-fiasco`; G3 starting on new branch)

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

### Boot prompt — next session: G3 Account auto-discovery

**Goal:** Decouple `short_code` from the Python module path so adding a new account (e.g. `NAVIRA_PROD`) only requires creating a folder and `account.py` — no changes to `account_registry.py`.

**Context:**
- `short_code` is currently overloaded: it's both the infrastructure naming prefix (`QA_DG1_{short_code}`, Prefect block slugs, tags) AND the Python module path (`connector.accounts.{short_code}.deployments`). Renaming an account requires renaming the directory.
- `account_registry.py` hardcodes `ALDC_QA` — every new account requires a code change.
- This is the blocker for adding the Navira production account without touching shared files.

**Read first:**
- This page (Sprint 0A–0C results, especially the `short_code` gotcha in Sprint 0A)
- `connector/account_registry.py` — see line 58 where `ALDC_QA` is hardcoded
- `connector/accounts/ALDC_QA/account.py` — the `Account` dataclass definition
- `connector/accounts/ALDC_QA/__init__.py` — understand what the account module exports

**Work in:** `connector` repo, new branch `feature/paulrussell/phase-0/g3-account-autodiscovery` cut from `operation-fiasco`.

**PR target:** `operation-fiasco` (not `master` or `development`).

**Deliverables:**
1. `account_registry.py` — scan `connector/accounts/*/account.py` dynamically, import and register each `Account` instance without hardcoding names.
2. Account module contract — document (or enforce with a test) what each `connector/accounts/*/account.py` must export for auto-discovery to work.
3. New account smoke test — add `connector/accounts/NAVIRA_PROD/account.py` as a minimal stub (no deployments yet) and verify `AccountRegistry.register_all_accounts()` discovers it automatically.
4. Existing `pytest tests/` still passes.

**Acceptance:** Adding a new `connector/accounts/NAVIRA_PROD/account.py` causes it to appear in the Prefect UI without modifying `account_registry.py` or any other shared file. `pytest tests/` is green. PR passes all CI checks.

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
3. **G3 (account auto-discovery)** — Decouple `short_code` from module path. Enables descriptive naming + adding NAVIRA_PROD without code changes to `account_registry.py`.
4. **G1 (DateWindow partition)** — Required for Phase 1A ad platform connectors (Google Ads retroactively adjusts 7–30 days). Implement at `base_connector.py` FIXME.
5. **Sellercloud migration** — First production connector on Prefect. Proves the framework at scale. Validates CC1–CC7 empirically.
6. **Snapshot naming fix** — Move snapshots to `_PREFECT_SNAPSHOTS` schema so the framework's schema scanner doesn't pick them up.
7. **G4 (extended run options)** — Needed for connectors with pagination, cursors, rate limit context. Can defer until Phase 1A connectors actually need it.
8. **G6 (scaffold CLI)** — Nice-to-have. Defer until we've manually built 2–3 connectors and the pattern is stable.

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

#### 1.1 Complete DateWindow partition (G1)

Implement `PartitionSchemeDateWindow` in `base_connector.py`. The existing code has a FIXME placeholder at line 711. This partition scheme should:
- Accept `window_type` (day, week, month)
- Accept `lookback_days` (e.g., 30 for ad platforms)
- Iterate over date windows, calling `run()` per window
- Support `min_date` for historical backfill

This is essential for Phase 1A — Google Ads retroactively adjusts data for 7–30 days, requiring configurable lookback windows.

**Acceptance:** A flow using `PartitionSchemeDateWindow(window_type="day", lookback_days=30)` iterates over the last 30 days and loads each day's data into Snowflake.

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

**Steps:**
1. Create typed `SellercloudConnection(ConnectorConnectionBase)` and `SellercloudOptions(ConnectorOptionsBase)` from the existing legacy `connector/connectors/sellercloud*.py` files
2. Implement `SellercloudConnector(BaseConnector[...])` wrapping the existing logic
3. Create `connector/accounts/NAVIRA_PROD/account.py` (proves G3 auto-discovery)
4. Create `connector/accounts/NAVIRA_PROD/deployments/sellercloud.py`
5. Register Sellercloud connection block in Prefect with credentials from vault
6. Run in QA against test Snowflake, reconcile row counts and totals
7. Run in production alongside legacy connector, compare outputs
8. Cut over when reconciled

**Acceptance:** Sellercloud data lands in Snowflake via Prefect with < 1% variance vs legacy pipeline. Legacy connector can be decommissioned.

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
| 1.1 DateWindow partition | 1 day | FIXME already in code; pattern from DateExact |
| ~~1.2 Pytest framework~~ | ~~2 days~~ | ✅ Done 2026-04-29 — 15 tests passing |
| 1.3 Account auto-discovery | 0.5 day | Dynamic import scan |
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
