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

## ⚠ Corrections measured during [[FU92-427]] (2026-09-03) — this page overstated two things

**1. Backdating is not limited to ~30 days.** A template comment claiming *"appears to have a short
30ish day limit back dating"* has been quoted as fact and is refuted by our own warehouse: one load
session on **2024-09-24 wrote 268 continuous days, zero gaps — a 272-day backdate**. Unique
Impressions separately backdated 40 days *two days before* that comment was written. The comment's
own git history shows a **measured** successor (*"30-45 day limit"*, `b32153a9`) that merge
`c5cd9818` silently reverted. Treat any backdating limit as **unmeasured** until the
`ScheduleStartDate` in a create-schedule response says otherwise.

**2. "Executions expire 2-3 days after completion" is stated too strongly here.** The connector only
enforces `DownloadURLExpirationUTC` (`trade_desk_my_reports.py:254-259`). In the 2025-08 outage a
partition completed **~5 days** after its execution was delivered. The real duration is unmeasured;
do not plan a recovery window on the "2-3 days" figure.

**3. This page says backdating *"creates executions for Jan 1 through today, all immediately
available."*** The script's own docstring — written by whoever ran it — says the opposite:
*"this does not always generate for all of the days. The response will provide a start date that
will indicate how far back reports were generated for."* **Trust the script, not this page.**

## Auth — 365-day static token

`TTD-Auth` header, base64 protobuf (58 bytes), **365-day lifespan**, no refresh logic anywhere.
Connection `2aa7e056-28f9-4bf9-9758-3fdc7217409d`, account `0fc00e34`, whose `connection` sub-dict
holds exactly one key (`auth_token`) and no `encryption`. Expired 2026-08-05 and took the connector
down 29 days; the same thing happened in August 2025. Full runbook, gotchas and the rotation
procedure: [[connector-token-refresh]].

## Recovery behaviour during an outage (measured)

- TTL retirement fires **only on a completed run** (`core_api/v1/route_work.py:1259`), so **nothing
  retires while the connector is broken** — stuck partitions stay `active` / `in_queue` and retry
  ~3×/day indefinitely. Fixing the credential re-attempts them automatically; **no manual re-queue.**
- The retry queue drains **oldest-first**, so permanently-dead old partitions are attempted before
  recent ones on every sweep. If a sweep truncates, the *newest* dates starve. Purging dead
  partitions may be a precondition for a clean backfill.
- ⛔ **Never `work_template_delete` to change a `schedule_id`** — it calls `warehouse_reset` →
  `DROP TABLE` / `DROP VIEW CURRENT_` / `DROP VIEW COMBINED_`. On the Performance template that is
  **14,665,166 rows / 935 days**, of which at most ~45 could be regenerated. Use
  `work_template_update`, and send the **complete** `options` object (top-level keys are replaced
  wholesale, and the type guard passes `raise_exception=False` — a wrong payload returns HTTP 200
  having written nothing).
- A replacement schedule must keep `lookback_days = 5`: `_report_matches_dates` demands an **exact**
  window match, so any drift fails as *"no COMPLETED report executions"* — which reads like missing
  data and is actually a config error.

## See Also

- [[eclipse]] — connector platform
- [[fusion92]] — primary client using Trade Desk connector
- [[connector-development-standards]] — attribute hierarchy and parameter patterns
- [[connector-token-refresh]] — the 365-day lifespan, rotation runbook, and the silent-failure rule
