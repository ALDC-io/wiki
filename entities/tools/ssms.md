---
tags: [entity, tool, ssms, sql-server, power-bi]
aliases: [SSMS, SQL Server Management Studio]
sources: [daily/2026-04-17.md, processes/operations/knowledge-transfer-log.md]
created: 2026-04-17
updated: 2026-04-17
---

# SSMS (SQL Server Management Studio)

Microsoft's SQL Server client, used at ALDC to manage the SQL Server database that sits **between** [[Snowflake]] and [[Power BI]]. Data from Snowflake lands in this SQL Server DB first; PBI then consumes from there. SSMS is how engineers edit or reprocess that intermediate data — most commonly for re-processing old data or running partitions.

## Where SSMS fits in the pipeline

The data path is **Snowflake → SQL Server DB → Power BI** (not Snowflake → PBI directly, as one might assume from [[data-pipeline-flow]] at first glance). SSMS is the client used to interact with that SQL Server layer.

```
Snowflake (warehouse / report_common)
        │
        ▼
SQL Server DB  ◄──── SSMS (engineer edits, partition re-processing)
        │
        ▼
Power BI (model import)
```

A more detailed dataflow diagram exists in Confluence — see [[Confluence]] for the link.

## Common SSMS tasks at ALDC

- **Re-processing old data** into PBI (typical reason to open SSMS at all)
- **Partition processing** — usually on orderline and marketing activity tables
- Most clients do **not** need manual partition processing. **[[GEP]] is the exception** — it regularly requires partition runs

## Setup

Per-client setup (including when SSMS runs on a schedule) is documented in [[Confluence]]. Check the client-specific page there for SSMS setup or login, and for when the jobs need to run.

## Pitfalls

- **VPN required** — running against the SellerCloud SQL Server backend needs VPN access (config from Sean O'Grady at 5x5inc.ca, captured in [[knowledge-transfer-log]])
- **Don't assume Snowflake → PBI is direct** — new engineers often model this as Snowflake → PBI, but the SQL Server layer is a real hop and owns some processing

## Partition Refresh (Historical Data)

Source: Confluence CLIEN/1294794754.

When historical data is reloaded into Snowflake, or code is changed and you're testing outside the incremental refresh window, those changes may not appear in the PBI model. Steps to refresh specific partitions:

1. **Open SSMS and connect.** The server name corresponds to the workspace in the Power BI Service — go to **Workspace Settings → Premium → Workspace connection**, copy that value as the Server Name.
2. **Navigate:** expand the model → tables → right-click the table requiring a reload → **Partitions**.
3. **Process:** select **Process**, switch Mode to **Process Full**, then select the partitions to reload.
4. **Reprocess the full table** afterward (right-click table → **Process Table** → Process Full). This is mandatory when fixing a data loading error.

> **Tip:** On the processing screen, use **Script → Script Action to New Query Window** instead of running directly. Click Execute from the action ribbon — progress appears in the output window.

## See Also

- [[Power BI]] — downstream consumer of the SQL Server data
- [[Snowflake]] — upstream source that feeds the SQL Server DB
- [[data-pipeline-flow]] — overall pipeline (SSMS layer should be explicit there)
- [[Confluence]] — holds detailed dataflow diagrams and per-client SSMS schedules
- [[knowledge-transfer-log]] — Steven's notes on VPN/SSMS and GEP-specific partition processing
