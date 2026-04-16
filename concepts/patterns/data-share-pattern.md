---
tags: [concept, pattern, snowflake, data-share]
aliases: [data share, Snowflake data share, data sharing]
sources: [GEP/snowflake/data_share/warehouse.sql, GP-207, GP-208 notes]
created: 2026-04-16
updated: 2026-04-16
---

# Data Share Pattern

How ALDC exposes data to clients and receives data from clients via Snowflake's native data sharing mechanism. Used for both outbound (ALDC → client) and inbound (client → ALDC) sharing.

## Outbound: ALDC → Client

ALDC creates secure views in the `DATA_SHARE` schema and shares them with client Snowflake accounts.

### Setup Steps

1. **Create secure view** in `DATA_SHARE` schema:
   ```sql
   CREATE OR REPLACE SECURE VIEW DATA_SHARE.WAREHOUSE_SHARED_DIM_PRODUCT AS
   SELECT
       PRODUCT_KEY,
       PRODUCT_ID,
       MASTER_SKU,
       -- ... explicit column list (NEVER use SELECT *)
   FROM WAREHOUSE.SHARED_DIM_PRODUCT;
   ```

2. **Create share** (or add to existing):
   ```sql
   CREATE SHARE IF NOT EXISTS share_name;
   GRANT USAGE ON DATABASE db_name TO SHARE share_name;
   GRANT USAGE ON SCHEMA DATA_SHARE TO SHARE share_name;
   GRANT SELECT ON VIEW DATA_SHARE.view_name TO SHARE share_name;
   ```

3. **Add consumer account**:
   ```sql
   ALTER SHARE share_name ADD ACCOUNTS = 'consumer_account_locator';
   ```

4. Client accepts the share on their end and maps it to a database.

### Critical Rule: No SELECT *

Data share views must use **explicit column lists**, never `SELECT *`. Snowflake materializes the column list at view creation time — `*` doesn't dynamically update when source table columns change, causing silent breakage.

### GEP Example

`GEP/snowflake/data_share/warehouse.sql` — shares product dimension (68 columns explicitly listed), along with other warehouse objects.

## Inbound: Client → ALDC

When a client shares data with ALDC (e.g., [[GP-208]] inventory feed from Navira/GEP):

### What ALDC Needs from the Client

1. **Snowflake account identifier** (account locator or org.account format)
2. **Table/view name** being shared
3. **Refresh cadence** (hourly, daily, etc.)
4. **Timezone** of any timestamp columns (UTC preferred)
5. **Historical backfill scope** (how far back, who is responsible)

### ALDC Setup

1. Accept the incoming share
2. Map to a database in the client's Snowflake environment (e.g., `PROD_DG1_GEP.GEP_INVENTORY`)
3. Grant appropriate roles `USAGE ON DATABASE` and `SELECT ON SHARE`
4. Build WAREHOUSE_SOURCE views on top of the shared data
5. Integrate into the normal [[data-pipeline-flow]]

## Capacity Query API (Alternative)

For smaller datasets or when a full data share is overkill, ALDC uses a capacity query API:

- Found in `GEP/scripts/data-share-capacity-query.py`
- Makes HTTP requests to a capacity API endpoint with account/capacity IDs
- Returns data as JSON, can be loaded into Snowflake

## Fallback: File Stage

When data sharing isn't ready, CSV file drops serve as a stopgap:

1. Client delivers CSV (SFTP, manual drop, or scheduled export)
2. Validate on receipt: row count + SHA256 checksum
3. Load via `COPY INTO` with named file format:
   ```sql
   TYPE = CSV, SKIP_HEADER = 1, FIELD_OPTIONALLY_ENCLOSED_BY = '"'
   ```
4. Migrate to data share once ready — no Layer 2/3 changes needed

## Related Tickets

- [[GP-207]] — Prod to test data share setup
- [[GP-208]] — Inventory feed via data share (pending client response)

## See Also

- [[Snowflake]] — the platform
- [[data-pipeline-flow]] — where data shares fit in the pipeline
- [[GEP]] — primary client using data shares
