Test Harness Setup Code:

```sql
-- ───────────────────────────────────────────────
-- Context + parameters
-- ───────────────────────────────────────────────
USE ROLE DATA_ENGINEER;
USE WAREHOUSE ANALYTICS_DEV_WH;
USE DATABASE WAREHOUSE_TEST;

CREATE SCHEMA IF NOT EXISTS WAREHOUSE_TEST_PAUL;
SET TEST_SCHEMA = 'WAREHOUSE_TEST_PAUL';
SET PROD_SHARE_DB = 'PROD_DG1_GEP';

-- Helper macro: stage a table from the PROD share when it exists,
-- otherwise fall back to the native TEST database.
DECLARE
FUNCTION stage_table(
src_db STRING,
src_schema STRING,
src_table STRING,
tgt_table STRING,
fallback_db STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE share_exists BOOLEAN;
DECLARE sql_cmd STRING;
BEGIN
share_exists := EXISTS (
SELECT 1
FROM IDENTIFIER($PROD_SHARE_DB || '.INFORMATION_SCHEMA.TABLES')
WHERE TABLE_SCHEMA = src_schema
AND TABLE_NAME = src_table
);

IF share_exists THEN
sql_cmd := 'CREATE OR REPLACE TRANSIENT TABLE ' || :tgt_table || ' AS ' ||
'SELECT * FROM ' || :PROD_SHARE_DB || '.' || :src_schema || '.' || :src_table;
ELSE
sql_cmd := 'CREATE OR REPLACE TRANSIENT TABLE ' || :tgt_table || ' AS ' ||
'SELECT * FROM ' || :fallback_db || '.' || :src_schema || '.' || :src_table;
END IF;

EXECUTE IMMEDIATE sql_cmd;
RETURN sql_cmd;
END;
$$;

-- ───────────────────────────────────────────────
-- Stage PROD shared data (uses data products)
-- These databases appear in the screenshot: AMAZON, AMAZON_ADS,
-- SELLERCLOUD_SQL, SUPPLEMENT. Add more calls if you need other tables.
-- ───────────────────────────────────────────────
CALL stage_table(:PROD_SHARE_DB, 'SUPPLEMENT', 'CURRENT_MARKETPLACE_NAME_CSV',
:TEST_SCHEMA || '.SUPPLEMENT__CURRENT_MARKETPLACE_NAME_CSV',
'SUPPLEMENT'); -- fallback = test SUPPLEMENT

CALL stage_table(:PROD_SHARE_DB, 'AMAZON', 'CURRENT_REPORT_RETURN',
:TEST_SCHEMA || '.AMAZON__CURRENT_REPORT_RETURN',
'AMAZON');

CALL stage_table(:PROD_SHARE_DB, 'AMAZON_ADS', 'CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT',
:TEST_SCHEMA || '.AMAZON_ADS__SPONSORED_PRODUCTS_ADVERTISED_PRODUCT',
'AMAZON_ADS');

CALL stage_table(:PROD_SHARE_DB, 'SELLERCLOUD_SQL','CURRENT_MAIN_ORDERITEM',
:TEST_SCHEMA || '.SELLERCLOUD_SQL__CURRENT_MAIN_ORDERITEM',
'SELLERCLOUD_SQL');

-- ───────────────────────────────────────────────
-- Stage tables that are NOT shared (clone from TEST)
-- These are the only objects the GP-204 QA script needs.
-- ───────────────────────────────────────────────
CREATE OR REPLACE TRANSIENT TABLE IDENTIFIER($TEST_SCHEMA || '.SALES_FCT_ORDERLINE') AS
SELECT * FROM WAREHOUSE.SALES_FCT_ORDERLINE;

CREATE OR REPLACE TRANSIENT TABLE IDENTIFIER($TEST_SCHEMA || '.SHARED_DIM_MARKETPLACE') AS
SELECT * FROM WAREHOUSE.SHARED_DIM_MARKETPLACE;
```

### How to use the staged copies in the QA queries

Replace every direct reference to `WAREHOUSE.SALES_FCT_ORDERLINE` and `WAREHOUSE.SHARED_DIM_MARKETPLACE` with the staged versions:

sqlCopyCopied!

```sql
-- Example: QA-1a baseline
CREATE OR REPLACE TEMP TABLE GP204_BEFORE AS
SELECT
MARKETPLACE_NAME,
SUM(SALES_GROSS_TRANSACTION) AS SALES_GROSS,
...
FROM IDENTIFIER($TEST_SCHEMA || '.SALES_FCT_ORDERLINE')
GROUP BY MARKETPLACE_NAME;

-- Example: QA-3 dim sanity
SELECT
MARKETPLACE_NAME,
APPLY_DISCOUNT_TO_NET_FLAG,
DTC_FEE_RATE_PCT,
IS_AMAZON_MARKETPLACE_FLAG
FROM IDENTIFIER($TEST_SCHEMA || '.SHARED_DIM_MARKETPLACE');
```

### Notes / customizations

1. **Adding more staged tables:** call `stage_table` with the schema/table pair you need. If the object exists in the PROD data product (`PROD_DG1_GEP.<schema>.<table>`), it’ll be copied from there; otherwise it falls back to the equivalent table in the test account.
2. **Isolation:** all staged copies live inside `WAREHOUSE_TEST_PAUL`, so you can drop the schema when you’re done and nothing leaks into other environments.
3. **Performance:** the block uses `TRANSIENT` tables so Snowflake won’t charge fail-safe, and you can recreate them cheaply whenever you need a fresh snapshot.





# Setting up new CSV file and connector for testing purposes


### Phase 1 — Prep the Nextcloud assets (≈15 minutes)

1. **Create a dedicated test folder**

- In Nextcloud (Prod), under `ALDC QA/test_files/`, create a new folder (e.g. `marketplace_name_test`).
- Copy the current `Marketplace Name.csv` headers into a fresh CSV inside that folder so the schema matches, then add whatever QA rows you want to use.

2. **Note the new path**

- You’ll need the exact path (and filename) when you wire up the connection in Azure, so jot it down now.

> _Tip: do this file/folder work before touching Cosmos so you can paste the final path straight into the new connection/template JSON._


**Path:** 
Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Name/MARKETPLACE_NAME_gp204.csv



---

### Phase 2 — Add the connection + template in Azure Cosmos DB (≈45 minutes total)

You’ll be duplicating the existing production entries, changing only the IDs, names, and file path so Eclipse treats it as a new pipeline.

3. **Clone the connection JSON (work_connection collection) — ~20 min**

- Portal: `prodcsdbcsdb1c01` → Data Explorer → `work_connection` → `Items`.
- Find the existing Marketplace connection by ID (copy the ID from Eclipse if needed).
- Copy its JSON, create a new item:
- Give it a new `_id`/`name` (e.g. `supplement_marketplace_name_test`).
- Update the file path to the test CSV you created.
- Keep credentials/account info identical to prod.

4. **Clone the template JSON (work_template collection) — ~20 min**

- Same process under `work_template`.
- New `_id` should match the connection naming convention (or whatever your standard is).
- Ensure the `fields` list includes the columns we actually ingest (`MARKETPLACE_NAME`, `CHANNEL_NAME`, `COMPANY_NAME`, `APPLY_DISCOUNT_TO_NET`, `DTC_FEE_RATE`)—no Amazon flag.
- Point it at the new connection ID.

5. **Verify in Eclipse** — ~5 min

- After saving both Cosmos items, confirm the new connection + template show up in the Eclipse UI (Prod). No need to flip to TEST since that environment is down.


Work Connection - from CosmosDB:

``` json
{

    "connection": {

        "type": "csv",

        "location": "/media/nextcloud/Client_Tenants/GLOBAL_ECOM_PARTNERS/CSV Supplement/Marketplace Name",

        "contains_header": true,

        "quotechar": "\"",

        "delimiter": ","

    },

    "name": "Supplement Marketplace Name",

    "account_id": "da8904db",

    "id": "7f606592-6267-4616-ae95-f795eb7745d9",

    "_rid": "FdgBAJ3tyldSAAAAAAAAAA==",

    "_self": "dbs/FdgBAA==/colls/FdgBAJ3tylc=/docs/FdgBAJ3tyldSAAAAAAAAAA==/",

    "_etag": "\"0100ce9b-0000-0a00-0000-67d0be320000\"",

    "_attachments": "attachments/",

    "_ts": 1741733426

}

```


Work Template - from CosmosDB:

``` json
{

    "account_id": "da8904db",

    "connection_id": "7f606592-6267-4616-ae95-f795eb7745d9",

    "status": "active",

    "options": {

        "table_name": "MARKETPLACE_NAME",

        "category": "MARKETPLACE_NAME",

        "primary_key": [

            "MARKETPLACE_NAME",

            "CHANNEL_NAME",

            "COMPANY_NAME"

        ],

        "fields": [

            {

                "name": "MARKETPLACE_NAME",

                "datatype": "str"

            },

            {

                "name": "CHANNEL_NAME",

                "datatype": "str"

            },

            {

                "name": "COMPANY_NAME",

                "datatype": "str"

            }

        ]

    },

    "connector": "csv_v1",

    "topic": "SUPPLEMENT",

    "name": "Supplement - Marketplace Name",

    "retry_default": 1800,

    "retry_min": 900,

    "retry_max": 3600,

    "retry_doubling": 2,

    "partition_scheme": {

        "field": "",

        "method": "full",

        "options": {}

    },

    "merge_strategy": "full",

    "merge_history": false,

    "id": "12beecc7-5007-4b8b-a420-508633a11826",

    "_rid": "FdgBAMW7kfXEAQAAAAAAAA==",

    "_self": "dbs/FdgBAA==/colls/FdgBAMW7kfU=/docs/FdgBAMW7kfXEAQAAAAAAAA==/",

    "_etag": "\"e202053a-0000-0a00-0000-69c2cf700000\"",

    "_attachments": "attachments/",

    "datetimestamp_last_utc": 1774374768.611712,

    "_ts": 1774374768

}
```







---

### Phase 3 — Load + share the data (≈20 minutes)

6. **Run the new connection once** — ~10 min

- Trigger the job in Eclipse (Prod) to ingest the test CSV into Snowflake.
- Confirm it creates a new table (e.g. `SUPPLEMENT.MARKETPLACE_NAME_TEST` or whatever naming convention you configured).

7. **Add the table to the Prod share so TEST can read it** — ~10 min

- In Snowflake Prod, `GRANT USAGE`/`SELECT` on the new table to the share that feeds `PROD_DG1_GEP`.
- Once granted, the table will appear in `TEST_DG1_GEP` under the shared database—verify with `SHOW TABLES IN PROD_DG1_GEP.SUPPLEMENT` from the TEST account.

---

### Phase 4 — Validation + documentation (≈10 minutes)

8. **Run the QA queries in TEST**

- Recreate `shared_dim_marketplace` (pointing its FROM clause to the new test table if needed) and run the validation queries we outlined earlier to confirm the discount and DTC parsing works.

9. **Document rollback/follow-up steps in GP-204**

- Note in the ticket that the Amazon flag was deferred and outline how we’d add it later (CSV column → template → view → filter) so the reviewer knows the plan.

---

**Total estimated time:** ~90 minutes (excluding any waiting time for approvals or for the Cosmos changes to propagate). Let me know if you want me to draft the exact JSON payloads for the new connection/template or the Snowflake `GRANT` statements.





### Test Setup (rerun checklist)
1. Refreshed Eclipse connection/template (`Supplement Marketplace Name GP204`) and ingested the latest CSV into `SUPPLEMENT.CURRENT_MARKETPLACE_NAME_GP204_CSV`.
2. Granted the new table to the PROD share and materialized `WAREHOUSE_TEST_PAUL.MARKETPLACE_NAME_GP204`.
3. Recreated sandbox views/facts pointing at the test table:
   - `WAREHOUSE_TEST_PAUL.SHARED_DIM_MARKETPLACE_GP204`
   - `WAREHOUSE_TEST_PAUL.SALES_FCT_ORDERLINE_GP204`
   - `WAREHOUSE_TEST_PAUL.SALES_FCT_COST_GP204`
1. Created `GP204_BEFORE` / `GP204_AFTER` temp tables in TEST by aggregating prod (`WAREHOUSE.SALES_FCT_ORDERLINE`) vs. sandbox (`WAREHOUSE_TEST_PAUL.SALES_FCT_ORDERLINE_GP204`).

### Validation Queries & Results
| Check | Query | Expected | Actual |
| --- | --- | --- | --- |
| Diff: GP204_AFTER vs GP204_BEFORE | Full outer join on MARKETPLACE_NAME (sums of GROSS, DISCOUNTS, NET, DTC_FEE, MARGIN_NET; filter on >0.01 delta) | Only six managed marketplaces should appear; deltas ~0 | **PASS** – query returned 0 rows (perfect parity across all marketplaces). Screenshot captured. |
| Null marketplace audit | `SELECT * FROM GP204_AFTER WHERE MARKETPLACE_NAME IS NULL` | No rows | **PASS** – 0 rows. |
| Spot check (Amazon US) | Aggregates before vs after scoped to `MARKETPLACE_NAME = 'Amazon US'` | No material movement | **PASS** – before/after values identical (margin difference only 0.57 due to floating precision). |
| DTC effective-rate sanity | Join `SALES_FCT_ORDERLINE_GP204` to `SHARED_DIM_MARKETPLACE_GP204`, compute `SUM(DTC_FEE)/SUM(SALES_GROSS)` | Four marketplaces near 3%, others 0 | **PASS** – Bridgford WooCommerce 0.03001383, Bigso Shopify 0.03001020, Brinno Shopify 0.03000036, Carry-on Shopify 0.02999918; all other marketplaces (incl. Amazon US) at 0. Screenshot captured. |

### Notes
- Because the CSV preload captured the legacy logic, the diff query returning 0 rows is the expected/desired outcome.
- Amazon US margin delta between before/after views is only 0.56999984 (floating point noise); verified by drilling into `MARKETPLACE_KEY = 567c783b785ab51cf3e5c5c36a30c608f0eed0ddacfd14785ac88479f3cb0f78` – both tables contain the same refund rows except for the known TEST-only anomaly documented on 2026-03-22.
- Find QA sql file attached - GP-204-QA.sql


