---
tags: [entity, tool, prefect, orchestration, connector-migration]
aliases: [Prefect]
sources: [sources/obsidian-import/work/PREFECT/PRE-000 - Initial Prefect Setup.md, sources/obsidian-import/work/PREFECT/Claude Planning/Planning.md]
created: 2026-04-16
updated: 2026-04-16
---

# Prefect

Workflow orchestration platform being adopted at ALDC to replace the legacy [[Eclipse]] connector scheduling. The migration (PRE-000) converts all legacy connectors to Prefect-compatible flows.

## Migration Context (PRE-000)

The connector repo (`C:\Users\PaulRussell\repos\connector`) is being migrated from legacy `BaseConnector`-based connectors to Prefect flows. There are 47 legacy connectors to migrate.

### Current Architecture

| Layer | Location | Pattern |
|-------|----------|---------|
| Legacy connectors | `connector/connectors/*.py` | `BaseConnector`-based, dict-style options/connection. Not registered with Prefect. |
| Prefect bootstrap | `main.py → DeploymentRunner.serve_local()` | Registers block schemas, serves deployments from `connector/accounts/<account>/deployments/` |
| Reference implementation | `connector/accounts/ALDC_QA/deployments/exchange_rates.py` | Senior dev example of the target pattern |
| Output handling | `BaseConnector.add_response()` | Parquet write, blob upload, Snowflake staging/merge |

### Migration Pattern

For each connector:
1. Create typed `BaseConnector[ConnectionType, OptionsType]` subclass
2. Define `ConnectorConnectionBase` subclass with typed fields (replaces dict config)
3. Define `ConnectorOptionsBase` subclass with typed fields
4. Create Prefect flow/deployment per account under `connector/accounts/<ACCOUNT>/deployments/`
5. Register via `Account.register_flow`, use `MergeScheme` + `PartitionScheme`, reuse block IDs

### Migration Order (47 connectors)

1. **nextcloud-csv** (first — establishes Nextcloud auth + Prefect pattern)
2. **migration-scaffold** (extract template from nextcloud-csv)
3. **financial-connectors** (lowest risk, closest to reference)
4. **sql-connectors**
5. **aws-connectors**
6. **nosql-connectors**
7. **netsuite-connectors**
8. **ecommerce-connectors**
9. **crm-connectors**
10. **ad-platform-connectors**
11. **analytics-platform-connectors**
12. **geo-weather-connectors**
13. **scrape-connectors**
14. **misc-api-connectors**

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Wrap vs rewrite legacy logic | **Wrap** | Legacy FlatCsv has quirky edge-case handling (BOM stripping, schema validation, rest_field, ad-hoc casting) built from real customer data issues. Rewriting risks breaking silent edge cases. |
| Nextcloud auth | Basic auth (host, user, password) | Same as existing NextcloudFileHandler. App-token/OAuth2 deferred. |
| CSV partition scheme | `PartitionSchemeFull` | Full replace each run — CSV files are static snapshots, not date-windowed. |
| File reading | Direct via `nextcloud_client.get_file_contents()` | Not through NextcloudFileHandler (which is write/move/delete only). Single-responsibility. |

### Nextcloud CSV Test Setup

```bash
# Environment variables
NEXTCLOUD_HOST=cloud.aldc.io
NEXTCLOUD_USER=paul.russell@aldc.io
NEXTCLOUD_TEST_CSV_PATH=/Client_Tenants/ALDC_QA/TEST_FILES/MARKETPLACE_NAME_TEST/MARKETPLACE_NAME_prefect_test_file.csv

# Run tests
MSYS_NO_PATHCONV=1 PYTHONPATH=. .venv/Scripts/python -m tests.test_connectors.nextcloudcsv
```

Note: Must use `MSYS_NO_PATHCONV=1` in Git Bash to prevent MSYS2 path translation converting leading `/` to `C:/Program Files/Git/`.

## See Also

- [[Eclipse]] — the platform being replaced
- [[clients-repo]] — where Eclipse configs live (Prefect configs in connector repo)
- [[data-pipeline-flow]] — Prefect replaces Eclipse in Layer 1
