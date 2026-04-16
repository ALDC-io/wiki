---
tags: [process, operations, validation, flight-check]
aliases: [Flight Check, Pre-flight Check, Deployment Validation]
sources: [sources/obsidian-import/work/Documentation/Knowledge Transfer/Flight Check.md, sources/obsidian-import/work/Documentation/Knowledge Transfer/To-Do.md]
created: 2026-04-16
updated: 2026-04-16
---

# Flight Check

A validation process run to verify that all systems are healthy and data is flowing correctly. Referenced during knowledge transfer sessions and in to-do items as a recurring operational concern.

> **Note**: The source material for this page was minimal (a reference to scheduling a session and an email related to a flight check issue). This page captures the known context and should be expanded as the process is formalized.

## Prerequisites

- Access to [[Snowflake]] (Snowsight web UI)
- Access to [[Power BI]] Service
- Access to [[Eclipse]] dashboard (to check connector/task status)
- Understanding of expected data freshness per client and data source

## When to Run

- **Before a deployment** -- confirm baseline health so you can distinguish deploy-caused issues from pre-existing ones
- **After a deployment** -- verify that the deploy did not break any existing data flows
- **On a regular cadence** -- as a routine operational health check (cadence TBD -- recommend weekly or before each deploy cycle)
- **When a stakeholder reports an issue** -- as a first-pass triage to rule out data pipeline problems

## Steps

### 1. Check Eclipse Connector Status

1. Log into the [[Eclipse]] dashboard
2. Verify that scheduled templates are running on their expected cadence
3. Look for failed or stalled tasks
4. For any failures, check the error logs and determine if the issue is transient (API timeout, rate limit) or structural (bad credentials, schema change)

### 2. Check Snowflake Task Health

1. In Snowsight, go to **Monitoring -> Task History**
2. Verify that key task chains completed successfully:

```sql
-- GEP warehouse task chain
SELECT NAME, STATE, SCHEDULED_TIME, COMPLETED_TIME, ERROR_MESSAGE
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
))
WHERE NAME LIKE 'TASK_WAREHOUSE_ORDERLINE%'
ORDER BY SCHEDULED_TIME DESC;
```

3. All steps should show `SUCCEEDED`. Any `FAILED` or `SKIPPED` entries need investigation.

### 3. Check Data Freshness

Verify that key tables have recent data:

```sql
-- Check most recent data in key tables
SELECT MAX(CREATE_DATE) AS latest_order
FROM WAREHOUSE.SALES_DIM_ORDER_BASE;

SELECT MAX(PURCHASE_DATE) AS latest_amazon_pull
FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS;
```

Compare against expected freshness. If data is stale by more than the expected refresh interval, investigate the upstream connector or task.

### 4. Check Power BI Model Refresh

1. Go to `app.powerbi.com`
2. Navigate to the relevant workspace (e.g., `GEP Test Models` or Production)
3. On the Semantic model row, check **... -> Refresh history**
4. Verify the most recent refresh succeeded and completed within the expected timeframe
5. If refresh failed, check for expired credentials or Snowflake connectivity issues

### 5. Spot-Check Key Metrics

Build a quick validation visual in Power BI Explore or run a Snowflake query to confirm that key metrics are in expected ranges:

- Total order count by marketplace
- Revenue totals by company
- Date range coverage (no unexpected gaps)

### 6. Check Data Share Health (if applicable)

If the environment uses a prod->test data share:

```sql
-- Verify share objects are accessible
SELECT COUNT(*) FROM PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS;
SELECT COUNT(*) FROM PROD_DG1_GEP.SELLERCLOUD_SQL.CURRENT_MAIN_ORDER;
```

Failures here indicate the share has been modified or objects removed.

## Pitfalls / Gotchas

- **Task failures can cascade.** If the root task (`TASK_WAREHOUSE_ORDERLINE_0`) fails, all downstream steps are skipped. Always check from the root.
- **Stale data may not be a failure.** If the connector is working but the raw data hasn't changed (e.g., no new orders for a low-volume marketplace), the freshness check will show an old date. Cross-reference with the source system.
- **Power BI refresh can succeed but show stale data** if the underlying Snowflake views/tables weren't updated. Always check Snowflake freshness first.
- **Flight check issues should be documented.** When something is found, note it in the ticket/to-do system and communicate to the relevant team member.

## See Also

- [[gep-snowflake-pbi-deployment]] -- deployment runbook (includes validation phases)
- [[Snowflake]] -- data warehouse details
- [[Power BI]] -- reporting tool details
- [[Eclipse]] -- connector platform
- [[data-pipeline-flow]] -- end-to-end data flow architecture
- [[knowledge-transfer-log]] -- related knowledge transfer context
