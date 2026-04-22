---
tags: [pattern, connector, prefect, migration, development-standards]
aliases: [Connector Development Standards, ALDC Connector Pattern]
sources: [entities/tools/prefect.md, entities/repos/connector.md, connector/accounts/ALDC_QA/deployments/exchange_rates.py]
created: 2026-04-18
updated: 2026-04-18
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
