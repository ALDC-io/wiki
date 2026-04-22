---
tags: [entity, tool, snowflake, data-warehouse]
aliases: [Snowflake, SF]
sources: [clients repo snowflake/ directories, __TEMPLATE_ACCOUNT/snowflake/readme.txt, INFRA/1532067843, INFRA/1034092551, CORE/1571160065, CORE/374341641, CORE/418873390]
created: 2026-04-16
updated: 2026-04-18
---

# Snowflake

ALDC's data warehouse platform. Each client has a dedicated Snowflake environment with a star schema of dimensions, facts, extracts, and report-common views. [[Power BI]] consumes the report_common views.

## Environment Naming

Pattern: `{ENV}_DG1_{CLIENT}`

| Environment | Example | Purpose |
|-------------|---------|---------|
| PROD | `PROD_DG1_GEP` | Production |
| TEST | `TEST_DG1_GEP` | User testing / staging |

## Schema Architecture

Each client environment contains these schemas (see [[star-schema-convention]] for details):

| Schema | Purpose | Materialization |
|--------|---------|----------------|
| Source schemas (e.g., `AMAZON`, `SELLERCLOUD_SQL`, `SUPPLEMENT`) | Raw data from [[Eclipse]] connectors | Tables populated by Eclipse |
| `WAREHOUSE_SOURCE` | Intermediate views — clean, join, standardize source data | Views (not materialized) |
| `WAREHOUSE` | Final star schema — dimensions and facts | Physical tables via scheduled tasks |
| `REPORT_COMMON` | Pre-aggregated BI-optimized views | Views consumed by [[Power BI]] |
| `DATA_SHARE` | Secure views for Snowflake-to-Snowflake sharing | Secure views |

### Data flow through schemas

```
Source systems → Eclipse → Source schemas (AMAZON.*, SELLERCLOUD_SQL.*, SUPPLEMENT.*)
    ↓
WAREHOUSE_SOURCE.* (intermediate views — joins, SHA2 keys, type casting)
    ↓
WAREHOUSE.* (physical tables — scheduled task: CREATE TABLE AS SELECT)
    ↓
REPORT_COMMON.* (pre-aggregated views for Power BI)
    ↓
DATA_SHARE.* (secure views for external consumers, optional)
```

## Key SQL Patterns

### SHA2 Key Hashing
All surrogate keys use SHA2:
```sql
SHA2(PRODUCT_ID) AS PRODUCT_KEY
SHA2(TO_DATE(DATE)) AS DATE_KEY
SHA2(BALANCE_DATE::VARCHAR) AS BALANCE_DATE_KEY
```

### Currency Handling (Triple Measure Pattern)
All monetary measures appear in three versions:
```sql
AMOUNT_TRANSACTION    -- In transaction currency
AMOUNT_SUBSIDIARY     -- In subsidiary currency (often 0.0 for single-currency clients)
AMOUNT_CONSOLIDATED   -- Converted to reporting currency via CONSOLIDATED_RATE
```
Exchange rates from [[star-schema-convention|SHARED_FCT_EXCHANGE_RATE]] in `ALDC_LIBRARY`.

### Division Safety
```sql
DIV0(numerator, denominator)  -- Returns 0 on division by zero (not NULL)
```

### Window Functions
```sql
DENSE_RANK() OVER(ORDER BY DATE) :: INT AS DATE_SEQUENCE
QUALIFY ROW_NUMBER() OVER(PARTITION BY key ORDER BY date DESC) = 1  -- Latest row
```

### Null Coalescing
```sql
COALESCE(field1, field2, field3) AS final_field
EQUAL_NULL(a, b)  -- Treats NULLs as equal in comparisons
```

## Scheduled Tasks

WAREHOUSE tables are materialized from WAREHOUSE_SOURCE views using Snowflake scheduled tasks:
- Tasks run on a schedule (hourly for inventory, varies by client)
- Pattern: `CREATE OR REPLACE TABLE WAREHOUSE.X AS SELECT * FROM WAREHOUSE_SOURCE.X`
- Incremental pattern: `INSERT INTO ... WHERE timestamp > MAX(existing)`

## Dynamic Tables (Newer Pattern)

[[fusion92]] uses Snowflake dynamic tables instead of scheduled tasks:
```sql
CREATE OR REPLACE DYNAMIC TABLE ... TARGET_LAG = '1 hour'
```
Auto-refreshes without explicit task management. [[GEP]] still uses the older secure view + task pattern.

## Data Shares

Secure views in `DATA_SHARE` schema expose data to external Snowflake accounts:
- Always use explicit column lists (never `SELECT *`) — prevents breakage when source columns change
- Pattern: `CREATE OR REPLACE SECURE VIEW DATA_SHARE.X AS SELECT col1, col2, ... FROM WAREHOUSE.X`
- See [[data-share-pattern]] for full setup guide

## Deployment

Deploys are **manual** — code merging to a branch does NOT auto-deploy to Snowflake. See deployment processes for each client (e.g., [[gep-snowflake-pbi-deployment]]).

Steps:
1. Copy SQL from the repo file
2. Paste and execute in Snowflake UI (worksheet)
3. Verify view/table was created correctly
4. Pause → recreate → resume any scheduled tasks that reference the changed objects

## Core API Integration

Source: Confluence INFRA/1532067843 (ALDC Snowflake ecosystem / integration, 2025-02-05). A General Datawarehouse workflow diagram existed on the source page but is image-only and unretrieval via MCP — deferred.

[[core_api]] connects to Snowflake directly through four route modules:

### route_capacity.py

| Function | Purpose |
|---|---|
| `create_snowflake_connection` | **Main entry point** — creates a Snowflake connection object based on the capacity and capacity-provider document |
| `capacity_usage` | Queries Snowflake traffic and usage for an account |
| `capacity_monitor` | Queries the most recent hour of warehouse history — average queries blocked |
| `create_reader_account` | Creates and enables a Snowflake reader account for external (non-ALDC) users |
| `add_user_to_reader_account` | Adds a new user to a Snowflake share/reader account |
| `remove_user_to_reader_account` | Removes a user from a Snowflake share/reader account |

### route_dataset.py

| Function | Purpose |
|---|---|
| `get_snowflake_tables` | Retrieves all tables and views for an account |
| `data_columns` | Finds columns/fields for a given table/view |
| `data_fetch` | Fetches data with filters from a table/view |
| `data_fetch_random_sample` | Like `data_fetch` but returns a random sample |

### route_setup.py

| Function | Purpose |
|---|---|
| `setup_query` | Sets up a new Snowflake account using superuser access |
| `setup_snowflake_query` | Similar to `setup_query`; used for new user/client accounts |

### route_warehouse.py

| Function | Purpose |
|---|---|
| `warehouse_query` | **Main entry point** — executes any Snowflake-related command, including staging and merging data into Snowflake |

## Reader Accounts

Source: Confluence INFRA/1034092551 (Snowflake Reader Accounts, 2022-11-03).

Reader accounts allow external (non-ALDC) users to query a Snowflake data share without an ALDC Snowflake subscription. Provisioned programmatically via `create_reader_account` / `add_user_to_reader_account` in [[core_api]], or manually with the SQL patterns below.

### Active reader accounts

| Account ID | URL |
|---|---|
| AH87540 | https://ah87540.canada-central.azure.snowflakecomputing.com/ |

Admin user: `READER_ADMIN_BACA483F` — password in `vault/infra-credentials.md` § Snowflake Reader Account admin.

### SQL reference — reader account lifecycle (run on ALDC account)

```sql
-- Create a managed reader account
CREATE MANAGED ACCOUNT <name>
  admin_name = aldc, admin_password = '{{READER_ADMIN_PASSWORD}}', type = reader;

-- Create a share and grant access
CREATE SHARE <share_name>;
GRANT USAGE ON DATABASE "<DB>" TO SHARE <share_name>;
USE DATABASE <DB>;
GRANT USAGE ON SCHEMA "<SCHEMA>" TO SHARE <share_name>;
USE SCHEMA <SCHEMA>;
GRANT SELECT ON TABLE "<TABLE>" TO SHARE <share_name>;

-- Add reader account to share, then inspect
ALTER SHARE <share_name> ADD ACCOUNTS = <account_id>;
SHOW GRANTS TO SHARE <share_name>;
SHOW SHARES;
SHOW MANAGED ACCOUNTS;

-- Tear down
DROP MANAGED ACCOUNT <name>;
DROP SHARE <share_name>;
```

### SQL reference — reader account setup (run ON the reader account)

```sql
USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE COMPUTE_WH WITH
  WAREHOUSE_SIZE = 'XSMALL' WAREHOUSE_TYPE = 'STANDARD'
  AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;

-- Mount the incoming share as a database
CREATE DATABASE "<SHARE_DB_NAME>"
  FROM SHARE <producer_org>.<producer_account>."<SHARE_NAME>";
GRANT IMPORTED PRIVILEGES ON DATABASE "<SHARE_DB_NAME>" TO ROLE "SYSADMIN";
GRANT IMPORTED PRIVILEGES ON DATABASE "<SHARE_DB_NAME>" TO ROLE "ACCOUNTADMIN";

-- Resource monitor: cap at 2 daily credits, suspend at 90/100%
CREATE RESOURCE MONITOR "RESOURCE_MONITOR" WITH
  CREDIT_QUOTA = 2, FREQUENCY = 'DAILY', START_TIMESTAMP = 'IMMEDIATELY'
  TRIGGERS
    ON 60 PERCENT DO NOTIFY
    ON 90 PERCENT DO SUSPEND
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;
ALTER WAREHOUSE "COMPUTE_WH" SET RESOURCE_MONITOR = "RESOURCE_MONITOR";

-- Create a user (must change password on first login)
CREATE USER <name>
  PASSWORD = '{{PASSWORD}}'
  LOGIN_NAME = '<LOGIN>' DISPLAY_NAME = '<Display>'
  DEFAULT_ROLE = "PUBLIC" DEFAULT_WAREHOUSE = 'COMPUTE_WH'
  MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE "PUBLIC" TO USER <name>;
```

## Infrastructure Architecture

*Source: CF92/1363017731 — general Snowflake reference; not client-specific*

### Account Hierarchy

**Organization → Account → Database** (3-part object coordinates: `database.schema.object`)

- **Organization** — Top-level container. Controls custom URLs, billing, cross-account access.
- **Account** — Self-contained Snowflake instance in a specific region. Independent config, users, capacity, history. Accounts do not affect each other except via shared objects.
- **Database** — Container for data objects.

**Cloud provider:** Azure, AWS, or GCP. GCP not recommended (feature limitations). Azure preferred for SSO/Azure AD integration. Note: Snowflake runs *alongside* cloud providers, not within standard cloud subscriptions.

### Virtual Warehouses & Credit Model

Warehouses are compute containers; storage and compute are fully separated.

| Concept | Detail |
|---------|--------|
| Sizing | X-Small → 6XL; each size doubles cost and typically halves query time |
| Billing | Per-second; auto-suspend after 5 minutes idle |
| Standard Edition | ~$2.00–$2.25 USD/credit/hour |
| Isolation | Unlimited warehouses can be created; separate ETL / Reporting / Ad-hoc to prevent interference |

**Example cost:**

| Warehouse | Size | Hours | Credits | Cost |
|-----------|------|-------|---------|------|
| ETL Loading | X-Small (1 credit) | 14.5 | 14.5 | $29 |
| Standard Reporting | Small (2 credits) | 10.0 | 20.0 | $40 |
| Data Science | Large (8 credits) | 43.9 | 351.2 | $702 |

*Data loading/unloading performance is warehouse-size independent.*

### Access Control

All access is role-based. Users are assigned roles; roles receive grants. Never assign privileges directly to users.

**Built-in roles (highest to lowest):**
`ORGADMIN > ACCOUNTADMIN > SECURITYADMIN > SYSADMIN > USERADMIN > PUBLIC`

Build custom roles from the PUBLIC base role.

### Performance Notes

- Snowflake auto-optimizes storage/compute based on usage patterns.
- Micro-partition cluster keys are available but rarely needed.
- Dynamic Tables + Materialized Views help avoid performance issues with long-chained views.
- Larger warehouse ≠ always faster — test before upsizing.

## Authentication & MFA Hardening

Source: Confluence CORE/1571160065 (Snowflake MFA and OAuth Setup, 2025-04-02). Implementation in progress as of that date.

### Service Account Migration (MFA deadline: Aug 2025)

Service accounts moved to `TYPE = LEGACY_SERVICE` to extend username/password grace period past the MFA enforcement deadline.

```sql
ALTER USER service_account SET TYPE = LEGACY_SERVICE;
```

| Account | Environment | Status |
|---|---|---|
| DEV_MATILLION | dev | LEGACY_SERVICE |
| QA_MATILLION | qa | LEGACY_SERVICE |
| PROD_MATILLION | prod | Pending conversion (owner: Cathy) |
| MATILLION_LOADER | — | Deprecate |
| PBI_GATEWAY | — | Deprecate |
| EXCELBISERVICE | — | Power BI service account |

Long-term target: key-pair authentication or federated credentials for all service accounts.

### Network Policy Audit

```sql
SHOW NETWORK POLICIES;
```

If policies block application auth origins, amend per [Snowflake Network Policies docs](https://docs.snowflake.com/en/user-guide/network-policies#protecting-the-snowflake-service).

### Key-Pair Authentication Setup

For non-interactive service accounts:

```bash
openssl genrsa -out private_key.pem 2048
openssl req -new -x509 -key private_key.pem -out public_key.pem -days 365
```

Store private key in Azure Key Vault:

```bash
az keyvault secret set --vault-name <vault-name> --name <secret-name> --file private_key.pem
```

Set annual rotation reminder after setting up.

### Power BI Integration via Entra (INCOMPLETE as of 2025-04-02)

Checklist:
- [ ] Confirm Azure security integration (enterprise app) exists or re-authenticate
- [ ] `SHOW SECURITY INTEGRATIONS;` — list existing integrations
- [ ] `SHOW GRANTS TO USER <username>;` — review grants; create custom role if over-privileged
- [ ] Map service principal to security integration
- [ ] Power BI → Settings → Manage connections → add service principal connection

## v1 Client Database Structure (2021)

Source: Confluence CORE/374341641 (Snowflake, 2021-04-29).

> *v1 design (2021) — verify naming conventions against current client databases.*

### Database naming per client

Each client has four databases:

| Purpose | Pattern | Example |
|---|---|---|
| Staging (raw ingest) | `STG_<ACCOUNT_ID>` | `STG_D77E717C` |
| Warehouse (historical) | `<SHORT_CODE>_WH` | `WEST_GEOTECH_WH` |
| Reporting (facts/dims) | `<SHORT_CODE>_RPT` | `WEST_GEOTECH_RPT` |
| Sandbox (analyst) | `<SHORT_CODE>_SBOX` | `WEST_GEOTECH_SBOX` |

Object names (databases, schemas, tables): A-Z, 0-9, underscore only — any other character replaced with `_`. Identifiers are case-insensitive (stored uppercase).

### Service account role model (v1)

| Role | Pattern | Privileges |
|---|---|---|
| Service (write) | `CORE_SVC_<ACCOUNT_ID>` | USAGE + OPERATE on COMPUTE_WH; full DML on staging + short-code DB |
| Reporting (read) | `CORE_RPT_<ACCOUNT_ID>` | SELECT on short-code DB; read-only warehouse |
| Client group | `CLIENT_<SHORT_CODE>_<GROUP>` | SELECT on group schema/tables; XS warehouse |

### v1 Snowflake Azure integration setup

Source: Confluence CORE/418873390 (Datawarehouse Integrations, 2021-04-30).

Setup sequence for connecting Snowflake to Azure Blob (Parquet staging):

1. Create staging DB (`STG_<ACCOUNT_ID>`) + stage schema
2. Create storage integration (EXTERNAL_STAGE): link to Azure tenant + storage account; configure `AZURE_MULTI_TENANT_APP_NAME` (Snowflake PAC service principal)
3. Obtain `azure_consent_url` from `DESC INTEGRATION` → authorize in Azure AD (allow ~15 min for sync)
4. Define Parquet file format + external stage pointing to Azure Blob
5. Create service user + `CORE_SVC_<ACCOUNT_ID>` role with granular grants
6. Assign **Storage Blob Data Reader** + **Storage Blob Data Contributor** to the PAC service principal on the Azure storage account

Service account credentials for each client account: see `vault/infra-credentials.md` § Snowflake service accounts.

## Performance Review Notes

Source: Confluence CLIEN/1071644673 (Snowflake Review with Mark, 2023).

Updated data organization on 5 largest DW objects to improve performance: `DIM_ORDER`, `DIM_CUSTOMER`, `FCT_ORDER_LINE`, `FCT_CUSTOMER`, `FCT_ORDER`.

Best practices from the review:
- Avoid Direct Query in Power BI — refresh instead to offload work to the PBI engine
- Use common datasets and build reports from shared datasets to minimize refresh times
- Monthly query credit budget: ~60 credits/month (target ceiling from that engagement)
- Monitor reader account daily

## See Also

- [[star-schema-convention]] — naming patterns
- [[data-pipeline-flow]] — full pipeline flow
- [[Power BI]] — downstream consumer
- [[Eclipse]] — upstream data source
- [[clients-repo]] — where SQL files live
- [[core_api]] — API service that manages Snowflake connections and queries
- [[data-share-pattern]] — Snowflake data share setup patterns
- [[fusion92-data-architecture]] — Fusion92-specific Snowflake setup decisions
