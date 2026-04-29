---
tags: [entity, tool, ssms, sql-server, power-bi, xmla]
aliases: [SSMS, SQL Server Management Studio]
sources: [daily/2026-04-17.md, processes/operations/knowledge-transfer-log.md, GP-208 Data Source Settings check 2026-04-21, GP-208 XMLA validation session 2026-04-24]
created: 2026-04-17
updated: 2026-04-24
---

# SSMS (SQL Server Management Studio)

Microsoft's SQL Server client. At ALDC, SSMS's primary ongoing use is **as an XMLA client connecting into Power BI Premium's tabular model** — specifically for re-processing partitions of the tabular model cache after data changes upstream. SSMS can also be used against on-prem / vendor SQL Server backends (SellerCloud) when VPN access is configured, but that is a less common path.

> **Correction (2026-04-24):** earlier versions of this page described an "intermediate SQL Server DB sitting between Snowflake and Power BI" as the main role of SSMS. That DB **does not exist** in the GEP PBI data path (verified via Data Source Settings 2026-04-21; architecturally confirmed during the 2026-04-24 GP-208 XMLA validation). PBI imports directly from [[Snowflake]] into its own VertiPaq column-store cache. The "partitions" processed via SSMS are partitions of that PBI tabular-model cache, exposed over Power BI Premium's XMLA endpoint. SSMS is acting as an Analysis Services client, not as a relational DB client to an ALDC-owned SQL Server. See [[Power BI]] § Data flow into Power BI for the corrected architecture.

## Where SSMS fits in the pipeline

```
Snowflake (warehouse, report_common)
        │  (M query import, per PBI refresh schedule or on-demand)
        ▼
Power BI tabular model — VertiPaq cache (partitioned)
        ▲
        │  XMLA endpoint (powerbi://api.powerbi.com/v1.0/myorg/<workspace>)
        │
        └─── SSMS (connect as Analysis Services; Process Partition / Process Full)
        └─── TE3 GUI (same endpoint; metadata editing)
        └─── pbi_model_apply.exe (same endpoint; scripted metadata apply — see [[pbi-xmla-automation]])
```

All three clients speak the same XMLA protocol against the same PBI tabular model. SSMS is the oldest of the three and the one Steven historically used for partition re-processing.

## Common SSMS tasks at ALDC

- **Partition re-processing** on the PBI tabular model — typically on `Order Line` and `Marketing Activity` tables when historical data is reloaded in Snowflake (outside the incremental refresh window). See § Partition Refresh below.
- Most clients do **not** need manual partition processing. **[[GEP]] is the exception** — it regularly requires partition runs when reprocessing historical data.
- Ad-hoc queries against vendor SQL Server backends (e.g., SellerCloud) when diagnosing data source issues — requires VPN.

## Setup

Per-client setup (including scheduled partition-processing jobs, where they exist) is documented in [[Confluence]]. For PBI XMLA connections, the Server Name is the Power BI workspace connection string (Workspace Settings → Premium → Workspace connection).

## Pitfalls

- **VPN required for vendor backends** — running against the SellerCloud SQL Server needs VPN access (config from Sean O'Grady at 5x5inc.ca, captured in [[knowledge-transfer-log]]).
- **Don't confuse "PBI partitions" with a separate SQL Server DB** — new engineers often think SSMS is editing an intermediate database. It isn't (in the GEP path). It's editing the PBI tabular model over XMLA.
- **Close SSMS before triggering a PBI dataset refresh** — an active SSMS XMLA session holds a write lock; refresh will fail. Same gotcha applies to TE3 GUI.

## Partition Refresh (Historical Data)

Source: Confluence CLIEN/1294794754.

When historical data is reloaded into Snowflake, or code is changed and you're testing outside the incremental refresh window, those changes may not appear in the PBI model. Steps to refresh specific partitions:

1. **Open SSMS and connect.** The server name corresponds to the workspace in the Power BI Service — go to **Workspace Settings → Premium → Workspace connection**, copy that value as the Server Name.
2. **Navigate:** expand the model → tables → right-click the table requiring a reload → **Partitions**.
3. **Process:** select **Process**, switch Mode to **Process Full**, then select the partitions to reload.
4. **Reprocess the full table** afterward (right-click table → **Process Table** → Process Full). This is mandatory when fixing a data loading error.

> **Tip:** On the processing screen, use **Script → Script Action to New Query Window** instead of running directly. Click Execute from the action ribbon — progress appears in the output window.

## See Also

- [[Power BI]] — the tabular model SSMS connects to via XMLA
- [[pbi-xmla-automation]] — programmatic alternative for metadata model changes (replaces TE3 GUI / SSMS manual scripting)
- [[pbi-xmla-model-changes]] — TOM gotchas, drop-if-exists pattern, schema-discovery constraint
- [[Snowflake]] — upstream source the PBI model imports from
- [[data-pipeline-flow]] — overall pipeline
- [[Confluence]] — detailed diagrams and per-client SSMS schedules (note: older docs may describe a non-existent SQL Server intermediate — use the corrected framing on this page)
- [[knowledge-transfer-log]] — Steven's notes on VPN/SSMS and GEP-specific partition processing
