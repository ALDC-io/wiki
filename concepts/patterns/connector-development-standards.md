---
tags: [pattern, connector, prefect, migration, development-standards]
aliases: [Connector Development Standards, ALDC Connector Pattern]
sources: [entities/tools/prefect.md, entities/repos/connector.md, connector/accounts/ALDC_QA/deployments/exchange_rates.py, prefect-connectors connector/lib/warehouse/lib.py + connector/base_connector.py (branch development @ 62556f1, 2026-08-14)]
created: 2026-04-18
updated: 2026-08-14
---

# Connector Development Standards

Canonical pattern for building and migrating ALDC connectors to [[Prefect]] flows. All new connectors and Prefect-migrated connectors must follow this pattern. Part of the PRE-000 migration effort converting 47 legacy `BaseConnector`-based connectors.

## Attribute Hierarchy

Every Prefect connector consists of three typed classes:

```python
# 1. Connection class — replaces dict-style connection config
class MyConnectorConnection(ConnectorConnectionBase):
    api_key: str
    endpoint: str
    call_interval: float = 0.5

# 2. Options class — replaces dict-style options config
class MyConnectorOptions(ConnectorOptionsBase):
    category: str
    date_range: dict

# 3. Connector class — generic over connection + options types
class MyConnector(BaseConnector[MyConnectorConnection, MyConnectorOptions]):
    def run(self) -> None:
        ...
        self.add_response(df)  # Parquet write + blob upload + Snowflake merge
```

`ConnectorConnectionBase` holds auth credentials. `ConnectorOptionsBase` holds pull parameters (date range, metrics, dimensions). `BaseConnector[C, O]` is the generic base that handles output via `add_response()` — Parquet write, Azure blob upload, and Snowflake staging/merge.

## Migration Steps

For each legacy `BaseConnector`-style connector:

1. Create typed `BaseConnector[ConnectionType, OptionsType]` subclass
2. Define `ConnectorConnectionBase` subclass with typed fields (replaces dict config)
3. Define `ConnectorOptionsBase` subclass with typed fields
4. Create Prefect flow/deployment per account under `connector/accounts/<ACCOUNT>/deployments/`
5. Register via `Account.register_flow`, use `MergeScheme` + `PartitionScheme`, reuse block IDs

## PartitionScheme and MergeScheme Selection

| Scenario | PartitionScheme | MergeScheme |
|----------|-----------------|-------------|
| Static snapshots (CSV files, exchange rates) | `PartitionSchemeFull` | `MergeSchemeReplace` |
| Date-windowed API data (ad metrics, analytics) | `PartitionSchemeDate` | `MergeSchemeMerge` |
| Incremental with unique keys | `PartitionSchemeKey` | `MergeSchemeMerge` |

Use `PartitionSchemeFull` for connectors where source data is a complete snapshot on every pull (e.g., Nextcloud CSV). Use `PartitionSchemeDate` for date-range APIs where data is additive and keyed on date + dimensions.

> ⚠ **`MergeStrategy.Insert` is not idempotent.** Re-pulling a date under `Insert` appends a second
> copy — the primary key is enforced *per table*, and the re-pulled rows are identical apart from
> their metadata columns, so nothing dedupes. Measured on `exchange_rates` 2026-08-14:
> `backfill_runs: 1` → parity PASS; `backfill_runs: 8` → **10.57× duplication**. Either use
> `MergeStrategy.Version` (idempotent on the key — what `amazon_sellercentral` and most of
> `amazon_ads` use) or guarantee partitions never overlap. Switching strategy **changes write
> semantics**, so it needs its own evidence, not a swap-and-hope.
>
> ⚠ **`MergeStrategy.Version` is not a safe escape from `Insert` — it triple-inserts** (measured
> 2026-08-14, [[prefect-connectors]] `docs/KNOWN_ISSUES.md` #22). `connector/lib/warehouse/lib.py`
> issues three **byte-identical** INSERT statements (`:927-939`, `:942-954`, `:957-969` — proven by
> programmatic diff). Each is an anti-join that must exclude the *current* `SESSION_ID`, but the rows
> it inserts carry that same session id (`lib.py:115`), so statements 2 and 3 cannot see statement
> 1's rows and re-insert them. **Every staged row lands 3×**, and the `CURRENT_` view
> (`lib.py:606-616`) does not hide it — its `RANK()` ties all three copies at rank 1. `Version` is
> **21 of 25** deployment uses. Until this is fixed, *neither* strategy is duplication-free.
>
> ⚠ **Declared column types must fold Snowflake's alias table before comparison**, or every partition
> forks a new versioned table. `_get_column_list` emits `int -> "bigint"` and
> `datetime -> "datetime"`; Snowflake reports `NUMBER` and `TIMESTAMP_NTZ`. Any connector with a
> `DATE` column forks unconditionally. See **[[schema-dialect-drift]]** — including the only test
> that settles it (virgin-schema fragment count: 48 = broken, 1 = fixed).

### Two more write-path traps in `BaseConnector` (2026-08-14)

Both are **code-established** against `development` @ `62556f1`. Neither is fixed.

**`partition_key` never reaches `_upload_data`.** The `FIXME` sits at
`connector/base_connector.py:829-830` and all three call sites (`:738`, `:752`, `:776`) omit the
argument — so `partition_hash` is `md5("")` for **every date**. Under `MergeStrategy.Insert` the
tombstone filter then selects the whole table's history instead of the single partition being
rewritten. ⚠ *Not yet measured against the warehouse* — treat the real-world firing as unconfirmed.

**`self.responses` accumulates across partitions.** It is never cleared (`base_connector.py:309-311`,
`:422`) while `run_workflow` re-calls `run()` once per partition (`:745-756`) and connectors
`return self.responses`. **Verified in-process:** three successive calls returned lengths **1, 2, 3**.

⭐ **These compound.** With three independent duplication sources live at once, an observed
duplication factor is a **product**, not a diagnosis — the measured 10.57× on `exchange_rates` never
traced to any single mechanism, and fixing one of them will not take it to 1. Establish the
counting basis before quoting a factor; see [[vacuous-verification]] for the sibling failure of
trusting a verdict that never compared anything.

## Prefect Deployment Structure

Each account's deployments live under `connector/accounts/<ACCOUNT_NAME>/deployments/<connector_name>.py`. Deployments are served from `main.py → DeploymentRunner.serve_local()`, which registers block schemas and serves all deployments for the configured account.

```
connector/
└── accounts/
    └── <ACCOUNT_NAME>/
        └── deployments/
            └── <connector_name>.py   # Prefect flow + deployment definition
```

Blocks (Snowflake creds, Azure creds, per-connector connection creds) are stored in the Prefect Server. Password fields are placeholders until populated. Reuse existing block IDs rather than creating new blocks per deployment.

## Reference Implementation

**`connector/accounts/ALDC_QA/deployments/exchange_rates.py`** — the canonical senior-dev example. Use this as the template for all new Prefect connector implementations. It demonstrates: typed connection/options classes, `PartitionSchemeFull`, block ID reuse, and `MergeSchemeReplace`.

## Key Decisions (PRE-000)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Wrap vs rewrite legacy logic | **Wrap** | Legacy connectors have quirky edge-case handling (BOM stripping, schema validation, ad-hoc casting) built from real customer data. Rewriting risks breaking silent edge cases. |
| CSV partition scheme | `PartitionSchemeFull` | Full replace each run — CSV files are static snapshots, not date-windowed. |
| Nextcloud file reading | `nextcloud_client.get_file_contents()` | Not through `NextcloudFileHandler` (write/move/delete only). Single-responsibility. |
| Nextcloud auth | Basic auth (host, user, password) | Same as existing `NextcloudFileHandler`. App-token/OAuth2 deferred. |

## Test Setup (Nextcloud CSV)

```bash
NEXTCLOUD_HOST=cloud.aldc.io
NEXTCLOUD_USER=paul.russell@aldc.io
NEXTCLOUD_TEST_CSV_PATH=/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv

# Run tests (Git Bash — MSYS_NO_PATHCONV prevents path translation)
MSYS_NO_PATHCONV=1 PYTHONPATH=. .venv/Scripts/python -m tests.test_connectors.nextcloudcsv
```

## Migration Order (47 connectors, PRE-000)

1. **nextcloud-csv** (establishes Nextcloud auth + Prefect pattern)
2. **migration-scaffold** (extract template from nextcloud-csv)
3. financial-connectors → sql → aws → nosql → netsuite → ecommerce → crm
4. **ad-platform-connectors** (includes the 6 connector specs below)
5. analytics-platform → geo-weather → scrape → misc-api

## Connector Specs (Ad Platform)

The 6 ad platform connector specs document the legacy connection/options schema and auth patterns the Prefect implementation must replicate:

- [[google-analytics]] — GA4 + UA; service account or OAuth2; `google-analytics-data` library
- [[facebook-ads]] — Meta Marketing API; 5-credential OAuth2; long-lived token (~60 day expiry)
- [[bing-ads]] — Microsoft Advertising; Azure App Registration OAuth2; 90-day refresh token cycle
- [[google-ads]] — Google Ads API; 4-credential model (Developer Token + OAuth Client ID/Secret/Refresh)
- [[amazon-ads]] — Amazon Ads + DSP; centralized ALDC OAuth app + per-client refresh tokens
- [[trade-desk]] — The Trade Desk My Reports; stateful schedule→execute→download workflow

Shared OAuth pattern used by Google connectors: [[google-oauth-python]].
Operational token refresh runbook: [[connector-token-refresh]].

## See Also

- [[Prefect]] — orchestration platform; PRE-000 migration context and full deployment architecture
- [[connector]] — repo where Prefect flows live; Docker deployment; legacy architecture
- [[Eclipse]] — the platform being replaced; connection/template JSON format
- [[python-development-standards]] — PEP 8, Google docstrings, VS Code + PyLint conventions
- [[google-analytics]] — GA4 + Universal Analytics connector spec
- [[facebook-ads]] — Meta Marketing API connector spec
- [[bing-ads]] — Microsoft Advertising connector spec
- [[google-ads]] — Google Ads connector spec
- [[amazon-ads]] — Amazon Ads + DSP connector spec
- [[trade-desk]] — Trade Desk My Reports connector spec
- [[google-oauth-python]] — shared Google OAuth pattern (`google-auth-oauthlib`)
- [[connector-token-refresh]] — operational token refresh runbook
- [[schema-dialect-drift]] — declared vs stored type spellings; why a `DATE` column forks a new table every partition
- [[orchestrator]] — the parity harness that grades a migrated connector, and how to read its PASS
- [[vacuous-verification]] — a verdict is a claim about work; only its content is evidence of work
- [[prefect-connectors]] — the repo these standards apply to
