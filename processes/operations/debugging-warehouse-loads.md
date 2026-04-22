---
tags: [process, operations, debugging, warehouse, eclipse, postman]
aliases: [debugging warehouse loads, debug warehouse load failure, warehouse load debug]
sources: [daily/2026-04-17.md]
created: 2026-04-17
updated: 2026-04-17
---

# Debugging Warehouse Loads

Runbook for investigating a failing warehouse load — where an [[Eclipse]] template is supposed to be loading data into [[Snowflake]] but the data is missing, stale, or wrong. The workflow uses [[Postman]] to reproduce the source API call, [[core_api]] to debug the ingestion side, and [[CosmosDB]] inspection to catch stale-template issues.

> **Status:** Paul's own workflow is still being established. Some steps (especially the local core_api debug loop) are open follow-ups. This page will be updated as the process firms up.

## High-level workflow

```
1. Get the failing template from Eclipse
2. Copy its call into Postman
3. Wait for response — compare to expected shape
4. If source call works → investigate core_api warehouse-rebuild functions
5. If response shape wrong → inspect CosmosDB `schema` container for stale template docs
```

## Step-by-step

### 1. Locate the failing [[Eclipse]] template

- Find the template in [[clients-repo]] under `CLIENT/eclipse/templates/SOURCE_NAME/*.json`
- Note the source, endpoint, and expected response columns

### 2. Reproduce the call in [[Postman]]

- Copy the endpoint, headers, and auth from the Eclipse template into a Postman request
- Fire and inspect the response
- If the response looks correct → the source is fine; the problem is downstream (core_api or Snowflake side)
- If the response is malformed / empty / errored → the problem is at the source or in auth

### 3. Investigate [[core_api]] warehouse-rebuild functions

If the Postman call succeeds but the warehouse still looks wrong, the issue is likely in how [[core_api]] handles the response and writes to Snowflake.

- Main entry point: **`route_warehouse.py` → `warehouse_recreate_current`** — rebuilds the data feeding `CURRENT_*` and combined views in Snowflake
  - Legacy-core equivalent: **`warehouse current rebuild`** in Lawrence's Postman collection
- Run core_api locally per [[core-api-local-setup]] and fire the endpoint via [[Postman]] (use [[postman-collections]] — Steven's new-core collection)
- Watch the VS Code / terminal output for exceptions
- Check [[Snowflake]] **Query History** for failed queries the rebuild emitted
  - Use the `ACCOUNTADMIN` role to see **un-redacted** query text. Without it, parameters are masked, which makes debugging much harder

### 4. Inspect [[CosmosDB]] for stale templates

Common gotcha: multiple template/schema documents exist for the same logical template, and an older one shadows or conflicts with the newer one.

- Open [[Azure]] Portal → the appropriate CosmosDB instance (prod or test, per [[azure-environments]])
- Navigate to the **schema** container
- Search for documents matching the failing template
- If multiple documents exist, identify which one is stale. Typical symptom: the new template was registered but the old document is still being read at runtime, causing the new template to fail

### 5. Cross-check with [[Snowflake]] source schemas

Confirm whether the data ever landed:

- Query the relevant `CURRENT_*` table in the source schema (e.g., `PROD_DG1_<CLIENT>.<SOURCE>.CURRENT_*`)
- Compare `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___` to expected recency (see [[accumulating-source-tables]])
- If the table is frozen (no recent timestamps), the problem is upstream of Snowflake — likely Eclipse / core_api / connector

## When to suspect which layer

| Symptom | Likely culprit |
|---------|---------------|
| Postman call fails | Source API / auth. Start there |
| Postman call works, `CURRENT_*` is empty or stale | [[core_api]] warehouse-rebuild function OR [[connector]] transport path |
| `CURRENT_*` has data but wrong columns | Stale template in [[CosmosDB]] `schema` container |
| Frozen `CURRENT_*` (no recent `___ALDC___GLOBAL_HISTORY_TIMESTAMP_START___`) | Producer / upstream freeze — see [[snowflake-data-share-refresh]] Failure mode 2 |
| Downstream fact table wrong but `CURRENT_*` looks fine | Warehouse SQL / dedup logic — see [[accumulating-source-tables]] |

## Marking stalled items as zombies

Source: Confluence CORE/922583054 (Zombies in ALDC!? What are they?, 2022-04).

> *2022 — verify zombie endpoint name against current [[core_api]] REST API.*

If a schedule or session fails to complete within SLA, mark it "zombie" so the pipeline can restart cleanly:

1. Open [[Postman]] with the ALDC collection
2. Find the zombie-marking endpoints (marked RED in the collection)
3. Verify correct `domain/url` and `account_id` in Postman variables
4. Execute the endpoint

Zombie status lets the system restart without reprocessing already-completed items. See [[core_api]] § REST API Specification for the `session/zombie` and `schedule/zombie` endpoints.

## Aborting stuck Snowflake jobs

Source: Confluence CORE/923238429 (Removing stucked jobs on Snowflake, 2022-04).

> *2022 — verify `work_reset` endpoint name against current [[core_api]].*

Snowflake can deadlock despite design safeguards. If a SQL job stalls indefinitely:

1. **Pause the Agent** — stop the warehouse agent to prevent new submissions
2. **Abort in Snowflake UI:**
   - Login → **History** sidebar
   - Filter by status: `running` / `failed` / `blocked`
   - Click the row → **Abort**
3. **Reset work** — call the `work_reset` API endpoint with the correct `account_id` via [[Postman]]; the work is resubmitted to the queue

## See Also

- [[Eclipse]] — platform owning the templates
- [[Postman]] — tool used to reproduce source API calls
- [[core_api]] — hosts warehouse-rebuild functions; zombie + work_reset endpoints
- [[CosmosDB]] — runtime store for templates; source of stale-template bugs
- [[connector]] — transport layer that writes to Azure Storage → Snowflake
- [[accumulating-source-tables]] — how to read `CURRENT_*` tables correctly
- [[snowflake-data-share-refresh]] — frozen-share failure mode
- [[flight-check]] — preventive validation that catches many of these before they hit prod
