---
tags: [entity, tool, connector, trade-desk, reporting-api, stateful]
aliases: [Trade Desk Connector, TTD Connector, The Trade Desk]
sources: [Confluence CONN/1458831371]
created: 2026-04-18
updated: 2026-04-18
---

# The Trade Desk Connector

Eclipse connector for The Trade Desk My Reports API. Unlike direct-query ad platform APIs, Trade Desk uses a **stateful, schedule-based reporting workflow** — data access requires pre-created report schedules and execution polling.

> **Prefect migration note:** Trade Desk is architecturally the most complex connector to migrate. The Prefect flow must implement: (1) report schedule lifecycle management (create, delete, backdate), (2) execution polling/waiting until complete, (3) per-execution download URL retrieval, and (4) schedule limit cleanup. The schedule creation script (`scripts/schedule_trade_desk_reports.py`) provides exact parameter mapping. The backdating strategy for historical backfills and warehouse reset procedure are load-bearing patterns.

## Workflow Overview

**Required chain:**
```
Report Template (client-created) 
  → Report Schedule (ALDC-created via script)
    → Report Execution (auto-generated daily)
      → Download URL → Data
```

Every step is sequential. You cannot skip to data without a schedule.

## Report Schedule Creation

### Script

Located at: `scripts/schedule_trade_desk_reports.py`

### Configuration Parameters

```python
partner_id = "frqci16"         # Trade Desk Partner ID (e.g., Fusion92)
template_id = 3375713          # Report template ID from client

schedule_name = "daily-ALDC-fusion-5-day-performance"
timezone = "UTC"
schedule_start = "2024-01-01T00:00:00"   # Can be past date for backdating
schedule_end = None                         # Only for one-time schedules
schedule_frequency = "Daily"               # "Daily" or "Once"
date_range = "LastXDays"                   # "LastXDays" or "Custom"
lookback_days = 5                          # Days of data per report

schedules_to_delete = []                   # Old schedule IDs to clean up
```

### Output

```
=== New Schedule ===
Schedule Start: <ScheduleStartDate>
Schedule Name: <ReportScheduleName>
Schedule ID: <ReportScheduleId>
```

Record the **Schedule ID** for Prefect template configuration.

## Prefect Template Fields

```json
{
  "schedule_id": 55243990,
  "schedule_name": "daily-ALDC-fusion-5-day-performance",
  "lookback_days": 5,
  "report_frequency": "Daily",
  "partner_id": "frqci16",
  "fields": [{"name": "Creative ID", "fillna": "null"}],
  "primary": ["REPORT_HOUR_UTC","ADVERTISER_ID","CAMPAIGN_ID","CREATIVE_ID","PARTNER_ID","AD_GROUP_ID","DEVICE_TYPE"],
  "table_name": "REPORT"
}
```

### `fillna` parameter

Override null values for specific columns. Use for primary key columns that must never be null (e.g., `"fillna": "null"` replaces nulls with the string `"null"`). Use sparingly.

### Report Execution Parameters

```json
{
  "field": "filter_date",
  "method": "date_window_equal",
  "options": {
    "bleed_minus": 0, "bleed_plus": 0,
    "limit_current": true,
    "min_date": "2024-01-01",
    "utc_offset": -28800,
    "window_type": "day"
  },
  "time_to_live": {"interval": 1, "method": "partition_date"}
}
```

`time_to_live.interval: 1` — only the newest execution contains new data; previous executions don't update.

## Execution Lifecycle

| State | Description |
|---|---|
| Created | Schedule runs; execution record appears |
| Processing | Trade Desk generating report |
| Completed | Download URL available |
| Expired | **2-3 days** after completion — data no longer accessible |

Executions are identified by date + schedule ID. Download each execution exactly once.

## Advanced: Backdating & Historical Backfills

Setting a past `schedule_start` causes Trade Desk to immediately generate executions for every day back to that date.

**Example:** `schedule_start = "2024-01-01"`, frequency = Daily, lookback = 5 days → creates executions for Jan 1 through today, all immediately available.

**Caveat:** Executions expire after 2-3 days. For long historical backfills, run partitions promptly after schedule creation.

## Warehouse Reset with New Schedule

When a template change requires complete data reload:

1. Create new schedule with same or earlier start date
2. Add old schedule ID to `schedules_to_delete` in script → run
3. Update Prefect template with new `schedule_id` and fields
4. Wait ~30 minutes for new schedule to generate executions
5. Verify execution completion via Execution Info Endpoint
6. Run historical partitions to catch up to today
7. Resume daily runs

## Schedule Limits

Trade Desk enforces per-partner schedule limits. Delete unused/test schedules regularly using `schedules_to_delete`.

## Key Architectural Differences vs Other Platforms

| Aspect | Trade Desk | Typical ad platform |
|---|---|---|
| Data access | Pre-created schedule required | Direct API query |
| State | Stateful (schedule ID, execution ID) | Stateless |
| Execution timing | Asynchronous — must poll/wait | Synchronous response |
| Data lifetime | Executions expire 2-3 days | Query any time |
| Historical data | Backdate schedule start | Date-range parameter |

## API References

- My Reports Getting Started: https://partner.thetradedesk.com/v3/portal/reds/doc/MyReportsGetStarted
- Create Report Schedule: https://partner.thetradedesk.com/v3/portal/reds/doc/AggregatedReports#create-report-schedules
- Delete Report Schedule: https://partner.thetradedesk.com/v3/portal/reds/doc/AggregatedReports#delete-report-schedule-by-id

## See Also

- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Trade Desk connector
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
