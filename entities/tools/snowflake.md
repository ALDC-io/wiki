---
tags: [entity, tool, snowflake, data-warehouse]
aliases: [Snowflake, SF]
sources: [clients repo snowflake/ directories, __TEMPLATE_ACCOUNT/snowflake/readme.txt, INFRA/1532067843, INFRA/1034092551, CORE/1571160065, CORE/374341641, CORE/418873390]
created: 2026-04-16
updated: 2026-07-29
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

### Dropping a view safely — consumer-check + rollback gotchas (2026-07-22, GP-226)

Before dropping a view you believe is orphaned, prove no consumer AND make the rollback actually work. Two traps burned in during the GP-226 `_FIXED` view cleanup:

- **`ACCESS_HISTORY.base_objects_accessed` MASKS secure-view names.** For a **secure** view it records only the underlying base tables (lineage is redacted), so filtering `base_objects_accessed` for the view name returns a **false "no reads."** Use `direct_objects_accessed` instead, PLUS a `QUERY_HISTORY` text-match on the `FROM` target. (Also: `ACCESS_HISTORY` has **no `role_name`** column — only `user_name`.) `OBJECT_DEPENDENCIES` catches internal view→view refs but NOT external readers (PBI/Eclipse) — you need query history for those. Discriminating consumer check = "who SELECTed this object, and does the real consumer now read the replacement?"
- **A captured `GET_DDL` is NOT a working rollback until rehearsed.** `GET_DDL` emits **unqualified** names (needs a `USE SCHEMA` header) and a trailing `;;`. If the view's `COMMENT='…'` contains literal semicolons, a naive `split(';')` statement runner **shreds** the DDL — use the quote-aware `snowflake.connector.util_text.split_statements` (or `execute_string(remove_comments=True)`). And `CREATE OR REPLACE` **strips grants** — the rollback must re-`GRANT SELECT` to the consumer role and recreate as the original owner. **Rehearse** the rollback (recreate → verify selectable + grants + anchor → re-drop to desired end state); the rehearsal is what exposes all of the above. Reference tooling: `aldc-launchpad/warehouse_ops/_gp226_fixed_consumer_check*.py`, `_gp226_FIXED_drop_ROLLBACK.sql` (+ runner).

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
  AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;   -- was 300; see snowflake-cost-analysis

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

### ⭐ Phase 3 enforcement — measured state of prod `wj66376` (2026-09-08)

Snowflake's single-factor-password deprecation runs in three phases; **Phase 3 is a per-account
rolling window, Aug–Oct 2026 — not a fixed date.** At enforcement: all non-human users are blocked
from password auth, and existing `LEGACY_SERVICE` users are auto-converted to `TYPE = SERVICE`.
A `SERVICE` user *cannot* log in with a password or SAML SSO, cannot enroll in MFA, and supports
**key-pair** + programmatic access tokens only. (`SERVICE_AGENT` adds workload identity federation.)

⭐ **The account-specific enforcement date — and the option to EXTEND it — live in
Snowsight → Governance & security → Trust Center → Overview → "Strong authentication progress".**
Viewing needs `TRUST_CENTER_VIEWER`; extending needs MODIFY on the account (ACCOUNTADMIN).
This is the single highest-value read-only check before any Phase 3 work.

Measured `SHOW USERS` on `wj66376`, 2026-09-08 — **17 `LEGACY_SERVICE` users, 16 with an RSA key
registered, exactly one without: `SERVICE_POWER_BI`** (see [[ALDC-1164]]). Two users are already
fully migrated (`TYPE = SERVICE`, `has_password = false`): `PROD_DG1_CORE_SVC_F49F9AA3` and
`PROD_DG1_PREFECT_SVC_DA8904DB`. Password auth still worked at **2026-09-08 17:01Z**, so
enforcement had not landed on this account.

### ⛔ ENFORCEMENT LANDED THE NEXT DAY — 2026-09-09 (supersedes the line above)

**It landed ~24 hours later and caused a client-facing outage.** See [[ALDC-1191]].

Re-measured `SHOW USERS` on `wj66376`, 2026-09-09: **`LEGACY_SERVICE` = 0.** All **20** non-person
users are now `TYPE = SERVICE`, `has_password = false`. `PERSON` users kept their passwords.
`SHOW AUTHENTICATION POLICIES IN ACCOUNT` → **0 rows** (so it was the type conversion, not a policy
attach). Conversion window: last successful password auth anywhere **09:15:15 PDT**, first failure
**10:03:05 PDT** — 48 minutes.

Snowflake's own tasks are visible in the account and name the mechanism:

```
2026-09-13 07:41  SCHEDULED  SECURITY_ESSENTIALS_STRONG_AUTH_LEGACY_SERVI…
2026-09-13 07:41  SCHEDULED  SECURITY_ESSENTIALS_STRONG_AUTH_PERSON_USERS
2026-09-09 18:50  SCHEDULED  THREAT_INTELLIGENCE_PASSWORD_SERVICE_USERS_T…
```

⭐ **Phase 3 STRIPS THE PASSWORD; it does not block the login.** The symptom is therefore
`390100 INCORRECT_USERNAME_PASSWORD` — **indistinguishable from a rotated password**. Expect the
first diagnosis to be "someone rotated the credential"; it was wrong on ALDC-1191. Two things
separate the cases cheaply:

- **Population, not sample.** One user failing looks like a rotation; *every non-person user*
  converting is the platform. `SHOW USERS` and count `LEGACY_SERVICE` — that single row count is
  the discriminator.
- **Vault metadata.** `az keyvault secret show --query attributes.updated` tells you whether OUR
  copy drifted, with **no secret retrieval**. On ALDC-1191 `prod-dg1-core-admin` was untouched since
  2026-06-03 while no longer authenticating — which is what proved the change was Snowflake-side.

⭐ **A `SERVICE` user cannot hold a password, and NO admin can restore one — `ACCOUNTADMIN`
included.** It is a type constraint, not a permission: Snowflake's `CREATE USER` reference defines
`LEGACY_SERVICE` as *"similar to `SERVICE`, but allows password and SAML authentication"*. So the
natural question "can an admin just reset the password?" has a definitive **no**, and a Snowflake
support ticket is not on the recovery path. Reverting to `LEGACY_SERVICE` is what Phase 3 removes,
and the conversion task above re-runs on **2026-09-13**.

⚠ **Non-prod `og35375` is under it too.** `PERSON` accounts there are MFA-gated: `PAULRUSSELLADMIN`
and `paulrussell` return **"MFA with TOTP is required"** — i.e. the password was *accepted* and the
second factor is the wall. **That error is good news dressed as failure**: it confirms the stored
password is still correct. Consequence: there is **no automated route into og35375**, so anything
needing `ALTER USER` there requires a human in Snowsight ([[ALDC-1192]]).

⚠ **A helper's failure is only evidence about what the helper actually tried.** `connect_nonprod()`
failing was read as "og35375 is converted" and that was wrong — it only ever tries an MFA-gated
PERSON account and a Key Vault copy known to be stale (the `TEST_DG1_CORE_ADMIN` rotation of
2026-09-08 updated the **wiki vault**, not Key Vault). Enumerate what the instrument covers before
believing its zero.

⚠ **"has a key" is NOT "uses a key".** `PROD_DG1_CORE_SVC_DA8904DB` carries
`has_rsa_public_key = true` **and authenticated by Password** on 2026-09-08 (~15 sessions via
PythonConnector 3.12.3). A registered-but-unused key does not survive Phase 3. Audit
`SNOWFLAKE.ACCOUNT_USAGE.SESSIONS.AUTHENTICATION_METHOD` — actual events — never the config flag.
This puts [[ALDC-1002]]'s completeness in question.

⚠ Human accounts used programmatically also break: `VLADRYZHKOV` (`TYPE = PERSON`) authenticates
by password via PythonConnector.

Useful instrument — names the user, driver and auth method in one read-only query:

```sql
SELECT USER_NAME, AUTHENTICATION_METHOD, CLIENT_APPLICATION_ID,
       COUNT(*) AS SESSIONS, MAX(CREATED_ON) AS LAST_SEEN
FROM SNOWFLAKE.ACCOUNT_USAGE.SESSIONS
WHERE CREATED_ON >= DATEADD(day, -14, CURRENT_TIMESTAMP())
GROUP BY 1,2,3 ORDER BY 1,4 DESC;
```

### Power BI ↔ Snowflake auth — what is actually supported (corrected 2026-09-08)

⭐ **The long-standing belief that Power BI cannot do Snowflake key-pair is FALSE and has been
since 2025.** Connector implementation 2.0 (GA July 2025) replaced the embedded Simba **ODBC**
driver with the Arrow **ADBC** driver; key-pair went GA Feb 2026.

Snowflake's own partner-authentication matrix, for **`TYPE = SERVICE`** users:

| Client | External OAuth | Key pair | PAT |
|---|---|---|---|
| PowerBI Cloud | **No** | **Yes** | No |
| PowerBI Desktop | **No** | **Yes** | No |

So after Phase 3 converts a service user, **key-pair is the supported path and Entra External
OAuth is not**. PAT is also marked "No" — it is not the cheap password-field substitute it looks like.

⚠ Key-pair **forces ADBC**, which removes the documented ODBC fallback and inherits two open
connector defects — including *`count distinct` returns incorrect result*, a **silent** wrong-number
failure. See [[power-bi]] and [[ALDC-1164]].

Formatting trap: Snowflake takes the **public** key *without* PEM delimiters
(`ALTER USER u SET RSA_PUBLIC_KEY='MIIBIjANBgkqh…'`), while Power BI takes the **private** key
*with* `-----BEGIN PRIVATE KEY-----` intact. `RSA_PUBLIC_KEY_2` exists for zero-downtime rotation.

⛔ **Ordering:** register the key and verify it *before* `ALTER USER … SET TYPE = SERVICE` — that
statement immediately invalidates the password.

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

## Cost Analysis & Optimization

Credit + storage cost is tracked as its own workstream — see [[snowflake-cost-analysis]] (epic ALDC-651). Key facts for anyone touching warehouse compute or storage:

- ~~**No cost monitoring exists** beyond the 2-credit/day reader-account cap.~~ **Superseded 2026-07-28/29.** Both accounts now carry an account-level NOTIFY-only resource monitor (`ALDC_NONPROD_MONTHLY` 400/mo, `ALDC_PROD_MONTHLY` 800/mo, triggers at 75/90/100%, `suspend_at` unset), and **non-prod runs a daily serverless guardrail task** (`ALDC_OPS.COST.T_COST_GUARDRAIL`, 14:00 UTC) emailing on zero-suspends / step change / overnight burn / idle % / new principal, plus a Monday heartbeat. Prod's guardrail is **not** deployed — blocked on email verification. Read-only `ACCOUNT_USAGE` toolkit + the guardrail DDL live at `observability/jobs/snowflake-cost/` (run as ACCOUNTADMIN).
- **`AUTO_SUSPEND = 60`, not 300, is now the convention** — see [[snowflake-cost-analysis]]. At 300 the estate billed ~24 credits/day per account for ~1.6–9.5 h of actual work. ⚠ Note `core_api` still provisions new warehouses at **300** (`route_capacity.py`, `route_setup.py`), so anything newly created needs an explicit `ALTER` — **tracked as ALDC-757**; until it lands, every new account is born with the defect. **Any poller whose interval is shorter than the `AUTO_SUSPEND` window turns its warehouse into a 24/7 charge.**
- **Everything runs on one shared `COMPUTE_WH` per account** (no isolation/attribution); all facts are full `CREATE OR REPLACE TABLE ... AS SELECT` (no incremental) — so hourly rebuilds also generate Time Travel + 7-day Fail-safe churn. Convention target: make rebuild tables `TRANSIENT`, right-size `TARGET_LAG`, tag queries.
- **Sandbox/clone sprawl** (`WAREHOUSE_TEST_*`, `_SHADOW`/`_RB`/`_BEFORE`/timestamped clones) is a real storage cost — but `WAREHOUSE_TEST_GP226` / `_NAVIRA_ROADMAP` are live prod deps; never blind-drop.

## Task Suspension Diagnosis

When warehouse tables appear stale (PBI reports show old data), check task state **before** investigating data sources. Snowflake auto-suspends a task DAG's root task after repeated errors — this is a common silent failure mode.

> Pattern added after GP-268 (2026-05-22). See also [[GP-PENDING-sales-data-outage-2026-05-22]] for a real incident where this caused a 14-hour outage.

### Diagnostic steps

```sql
-- Step 1: Check task state (connect to wj66376 as ACCOUNTADMIN)
SHOW TASKS IN DATABASE PROD_DG1_GEP;
-- Look for state='suspended', last_suspended_reason='SUSPENDED_DUE_TO_ERRORS'

-- Step 2: Find the failing step via task history
SELECT NAME, STATE, SCHEDULED_TIME, ERROR_CODE, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('hour', -48, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 50
))
WHERE NAME LIKE 'TASK_WAREHOUSE_ORDERLINE%'
ORDER BY SCHEDULED_TIME DESC;

-- Step 3: If task history is empty, check query history
SELECT QUERY_TEXT, ERROR_CODE, ERROR_MESSAGE, EXECUTION_STATUS, START_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT LIKE 'CREATE OR REPLACE TABLE WAREHOUSE.%'
AND START_TIME >= DATEADD('day', -2, CURRENT_TIMESTAMP())
AND EXECUTION_STATUS = 'FAIL'
ORDER BY START_TIME DESC;

-- Step 4: Fix the issue, then resume
ALTER TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0 RESUME;
EXECUTE TASK WAREHOUSE.TASK_WAREHOUSE_ORDERLINE_0;
```

### Key notes

- Snowflake auto-suspends the **root task** of a DAG after repeated errors — not just the failing child task.
- `TASK_HISTORY` may return no rows for the failing task depending on account/time range. Always start with `SHOW TASKS` to check state.
- `INFORMATION_SCHEMA.TASK_HISTORY` is the fast path; fall back to `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` if rows are missing.
- After fixing the underlying issue, both `RESUME` and an explicit `EXECUTE` are needed to get the task chain running immediately without waiting for the next scheduled window.

## Automated Data Share Sync

A scheduled task on the prod account (`wj66376`) auto-syncs all `CURRENT_*` and `COMBINED_*` views into the `PROD_DG1_GEP` outbound share. This prevents test task chain failures caused by new views being added to the database but not granted to the share.

| Component | Location |
|---|---|
| Stored procedure | `PROD_DG1_GEP.MAINTENANCE.SYNC_DATA_SHARE` |
| Scheduled task | `PROD_DG1_GEP.MAINTENANCE.TASK_SYNC_DATA_SHARE` — daily 05:00 PT |
| Audit log | `PROD_DG1_GEP.MAINTENANCE.SHARE_SYNC_LOG` |
| Service account | `PROD_DG1_CORE_ADMIN` (ACCOUNTADMIN) |

The procedure scans `INFORMATION_SCHEMA.VIEWS` for all `CURRENT_*`/`COMBINED_*` views, ensures USAGE on each schema, and grants SELECT to the share. Idempotent — re-granting an existing grant is a no-op.

> Added 2026-05-27 after a 6-week silent task chain failure on `TEST_DG1_GEP`. Root cause: `WAREHOUSE_SOURCE.SALES_DIM_ORDER_BASE` referenced `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS` (added for [[GP-200]]) which was never granted to the share. 40 total missing views were found and added. See [[GP-PENDING-share-sync-automation]].

## See Also

- [[snowflake-cost-analysis]] — credit + storage cost optimization (epic ALDC-651)
- [[star-schema-convention]] — naming patterns
- [[data-pipeline-flow]] — full pipeline flow
- [[Power BI]] — downstream consumer
- [[Eclipse]] — upstream data source
- [[clients-repo]] — where SQL files live
- [[core_api]] — API service that manages Snowflake connections and queries
- [[data-share-pattern]] — Snowflake data share setup patterns
- [[fusion92-data-architecture]] — Fusion92-specific Snowflake setup decisions
- [[GP-PENDING-sales-data-outage-2026-05-22]] — real incident where task suspension caused a 14-hour outage
- [[GP-PENDING-share-sync-automation]] — automated share sync (prevents missing-object failures)
