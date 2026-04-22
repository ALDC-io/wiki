---
tags: [concept, business-logic, power-bi, periodicity, reporting]
aliases: [Periodicity, YoY, MTD, YTD, Time Intelligence]
sources: [Confluence CLIEN/1407877121, Confluence CLIEN/1281228804]
created: 2026-04-18
updated: 2026-04-18
---

# Periodicity

The ALDC periodicity system enables Power BI models to show time-relative measures (YTD, MTD, YoY, etc.) via a dedicated `SHARED_DIM_PERIODICITY` dimension in Snowflake and corresponding DAX measure patterns in `.pbix` files.

## Periodicity Types

| Code | Name | Description |
|---|---|---|
| C | Current | Results for the grain of calendar/date selected in the model |
| MTD | Month to Date | Accumulated results from the start of the current month |
| QTD | Quarter to Date | Accumulated results from the start of the current quarter |
| WTD | Week to Date | Accumulated results from the start of the current week |
| YTD | Year to Date | Accumulated results from the start of the current year |
| Previous Actual Day/Week/Month/Quarter/Year | Previous Actual | Full results for the entire prior period (e.g. full previous quarter even if only in month 1) |
| Y1YD / D1YD / etc. | 1 Year Back to Date | Results for the same time range, 1 year prior |
| Y1YCD / D1YCD / etc. | 1 Year Back % | Year-over-year % change |

## Snowflake — Periodicity Dimension

The dimension is sourced from `TEST_DG1_ALDC_LIBRARY.SUPPLEMENT.CURRENT_KPI_PERIODICITY`. Create a secure view in each client's warehouse:

```sql
CREATE OR REPLACE SECURE VIEW WAREHOUSE.SHARED_DIM_PERIODICITY AS
SELECT
    SHA2(PERIODICITY_ID) :: VARCHAR AS PERIODICITY_KEY,
    PERIODICITY_ID :: VARCHAR AS PERIODICITY_ID,
    PERIODICITY_NAME :: VARCHAR AS PERIODICITY_NAME,
    PERIODICITY_TYPE :: VARCHAR AS PERIODICITY_TYPE,
    INTERVAL :: VARCHAR AS INTERVAL,
    COMPARISON :: VARCHAR AS COMPARISON,
    COMMENT :: VARCHAR AS COMMENT
FROM (
    SELECT
        PERIODICITY_ID,
        NAME AS PERIODICITY_NAME,
        TYPE AS PERIODICITY_TYPE,
        _GROUP AS INTERVAL,
        SUBGROUP AS COMPARISON,
        COMMENT
    FROM TEST_DG1_ALDC_LIBRARY.SUPPLEMENT.CURRENT_KPI_PERIODICITY
);
```

## Power BI — DAX Patterns

Every measure (e.g. Actual - Sales - Returns) requires a set of base measures plus a SWITCH-based dispatch measure. The DAX differs depending on whether the model has **single** or **multiple** calendar types.

### Multiple Calendar Types

Each date table has a `Calendar Type` column. Use `ALLEXCEPT` to prevent calendar-type bleed between dates.

**Base measure (references all calendar types):**

```dax
_BASE_ACT_SALE_RET = 
IF(
    NOT(ISFILTERED('Date (Order Create)') && HASONEVALUE('Date (Order Create)'[Calendar Type (Order Create)])) &&
    NOT(ISFILTERED('Date (Requested Ship)') && HASONEVALUE('Date (Requested Ship)'[Calendar Type (Requested Ship)])) &&
    -- ... (repeat for all date tables in use)
    ,
    IF(COUNTROWS('Order Line') > 0, "Please select one Calendar Type for each Date table in use", BLANK()),
    SWITCH(
        IF(HASONEVALUE(Consolidation[Consolidation Type]), MAX(Consolidation[Consolidation Type]), "Consolidated"),
        "Consolidated", SUM('Order Line'[SALES_RETURNS_CONSOLIDATED]),
        "Subsidiary",   SUM('Order Line'[SALES_RETURNS_SUBSIDIARY]),
        "Transaction",  SUM('Order Line'[SALES_RETURNS_TRANSACTION])
    )
)
```

**MTD base measure example:**

```dax
_BASE_ACT_SALE_RET_MTD = 
VAR LastDayAvailable  = MAX('Date (Order Create)'[Date Sequence (Order Create)])
VAR LastResetAvailable = MAX('Date (Order Create)'[Month Sequence (Order Create)])
VAR Amount = CALCULATE(
    [_BASE_ACT_SALE_RET],
    ALLEXCEPT('Date (Order Create)', 'Date (Order Create)'[Calendar Type (Order Create)]),
    'Date (Order Create)'[Date Sequence (Order Create)] <= LastDayAvailable,
    'Date (Order Create)'[Month Sequence (Order Create)] = LastResetAvailable
)
RETURN IF(HASONEVALUE('Date (Order Create)'[Calendar Type (Order Create)]), Amount, BLANK())
```

### Single Calendar Type

Simpler — no Calendar Type column filtering needed.

**Base measure:**

```dax
_BASE_ACT_SALE_RET = SWITCH(
    IF(HASONEVALUE(Consolidation[Consolidation Type]), MAX(Consolidation[Consolidation Type]), "Consolidated"),
    "Consolidated", SUM('Order Line'[SALES_RETURNS_CONSOLIDATED]),
    "Subsidiary",   SUM('Order Line'[SALES_RETURNS_SUBSIDIARY]),
    "Transaction",  SUM('Order Line'[SALES_RETURNS_TRANSACTION])
)
```

**MTD measure (single calendar type):**

```dax
_BASE_ACT_SALE_RET_MTD = 
VAR LastDayAvailable  = MAX('Date (Order Create)'[Date Sequence])
VAR LastResetAvailable = MAX('Date (Order Create)'[Month Sequence])
VAR Amount = CALCULATE(
    [_BASE_ACT_SALE_RET],
    FILTER(
        ALL('Date (Order Create)'),
        'Date (Order Create)'[Date Sequence] <= LastDayAvailable &&
        'Date (Order Create)'[Month Sequence] = LastResetAvailable
    )
)
RETURN Amount
```

### Dispatch Measure (User-Facing)

The final measure shown to the customer SWITCH-dispatches to the appropriate base measure based on the `PERIODICITY_ID` selected:

```dax
Actual - Sales - Returns = SWITCH(
    IF(HASONEVALUE(Periodicity[PERIODICITY_ID]), MAX(Periodicity[PERIODICITY_ID]), "C"),
    "C",    [_BASE_ACT_SALE_RET_C],
    "YTD",  [_BASE_ACT_SALE_RET_YTD],
    "MTD",  [_BASE_ACT_SALE_RET_MTD],
    "QTD",  [_BASE_ACT_SALE_RET_QTD],
    "WTD",  [_BASE_ACT_SALE_RET_WTD],
    "Y1YD", [_BASE_ACT_SALE_RET_Y1YD],
    "M1YD", [_BASE_ACT_SALE_RET_M1YD],
    "W1YD", [_BASE_ACT_SALE_RET_W1YD],
    "D1YD", [_BASE_ACT_SALE_RET_D1YD],
    "Y1YCD",[_BASE_ACT_SALE_RET_Y1YCD],
    "M1YCD",[_BASE_ACT_SALE_RET_M1YCD],
    "W1YCD",[_BASE_ACT_SALE_RET_W1YCD],
    "D1YCD",[_BASE_ACT_SALE_RET_D1YCD]
)
```

## Usage Examples in PBI

**Current actuals + accumulated amounts:**
1. Set Calendar date filter to a single month
2. Bring `PERIODICITY_NAME` into columns; filter to: Current, MTD, QTD, WTD, YTD
3. Bring Date into rows; add a measure

**YoY performance:**
1. Filter `PERIODICITY_NAME` to multi-select: Current + Day 1 Year Back % To Date + Day 1 Year Back to Date
2. Renders current-day results alongside same-day last-year actuals and % change

## See Also

- [[Power BI]] — PBI models that use periodicity
- [[star-schema-convention]] — SHARED_DIM_PERIODICITY follows the SHA2-key convention
- [[GEP]] — GEP model includes periodicity (REQ-422 for YTD vs full-year previous year)
