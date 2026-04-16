
# 25th Feb 2026

1. **VIANT adapter source + dedupe strategy**

- Switch from `VIANT.CONVERSION_REPORT_CAMPAIGN` to `VIANT.CURRENT_CONVERSION_REPORT_CAMPAIGN`. - **DONE**
- Confirm the current view already dedupes; if so, drop the SUM/GROUP BY so each row flows through untouched. If duplicates still appear, document why and how we handle them (aggregate vs. split). - Duplicates appear - **WE AGGREGATE**
- Update the comment that claims Viant needs aggregation; adjust the LinkedIn note since both adapters should now be unique.

```
-- PR Comment 1:
-- 1) Count total rows vs. distinct grains
WITH base AS (
SELECT
ADVERTISER_ID::VARCHAR AS platform_account_id,
CAMPAIGN_ID::VARCHAR AS platform_campaign_id,
ORDER_ID::VARCHAR AS platform_order_id,
CONVERSION_EVENT_ID::VARCHAR AS conversion_id,
TO_DATE("DATE", 'MM/DD/YY') AS conversion_date
FROM VIANT.CURRENT_CONVERSION_REPORT_CAMPAIGN
WHERE TO_DATE("DATE", 'MM/DD/YY') BETWEEN '2026-01-01' AND '2026-01-31'
)
SELECT
COUNT(*) AS total_rows,
COUNT(DISTINCT SHA2(CONCAT_WS('|',
platform_account_id,
platform_campaign_id,
COALESCE(platform_order_id, ''),
conversion_id,
TO_VARCHAR(conversion_date)
))) AS distinct_grain
FROM base;
```

**Result:** Duplicates Confirmed

![[Pasted image 20260225161531.png]]
426 rows - with row count > 1
**Duplicates File:** 
"C:\Users\PaulRussell\OneDrive - Analytic Labs Data Corporation\Tickets\fusion92\fu92-342\viant_current_conversion_report_campaign_dupes_20260225.csv"

## Clarifications:**
- Is there are a reason to not to filter duplicates when reading into the fact?

2. **Shared flight-ID CTE reuse (follow-up planning)**

- Steven wants these `PLATFORM_*` and `FLIGHT_PLATFORM_IDS` CTEs extracted from this fact + `fct_platform_spend` into a shared helper before merging. Decide whether to:
- a) do the refactor now (create a shared view/temporary table and point both facts to it), or
- b) document as a follow-up ticket/commit if refactor scope is large. Either way, note it in DE-007.

### Clarifications:

- Will I go ahead and create this flight utility table as part of this ticket or create a separate ticket?



3. **Join expressions**

- Replace `COALESCE(..., 'NO_ORDER')` equality checks with `EQUAL_NULL` to simplify null comparisons in both `CONVERSIONS_WITH_FLIGHTS` and `MARKED_CONVERSIONS`.

## DONE

4. **BETWEEN semantics confirmation**

- Verify that `BETWEEN F.START_DATE AND F.END_DATE` is inclusive (>=, <=). If we need explicit comparisons, adjust the condition and update comments.

**Result:**
- It is inclusive - same logic as >= and <=
- Can be changed if other syntax is preferred.

## DONE

5. **FINAL_CONVERSIONS output typing**

- Promote `FINAL_CONVERSIONS` to be the top-level SELECT (remove the extra ROW_NUMBER dedupe). Add explicit column casts/types per other dynamic tables (e.g., `FLIGHT_ID :: VARCHAR`, etc.), and decide whether to keep `FLIGHT_COUNT`/`ALL_FLIGHT_IDS` exposed or just documented.

## TO-DO

6. **Duplicate-handling strategy**

- With the Viant adapter fixed, confirm whether duplicates still occur downstream. If not, we can drop the duplicate-detect/dedup CTEs entirely. If yes, ensure we split conversions appropriately and document the reasoning.

### Clarifications:
- Do we want to remove the group-by logic on the viant adapter and just drop the duplicates at the end?


7. **Documentation & testing**

- Update DE-007 with what changed, validation queries run, and any follow-up work (shared CTE refactor, etc.).


### Other Considerations:
- The table will be created in the WAREHOUSE schema  not the WAREHOUSE_UTILITY schema.
- If we create the flight duplicate handling table it will be placed in WAREHOUSE_UTILITY schema.


# 26th Feb 2026

### 1. Must finish for the current PR

| Area                              | Tasks Still Needed                                                                                                                                                                                                                                                                                                                                                                                              | Notes / References                                                                                                                                                     | Status |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **Final SELECT shape**            | Promote `FINAL_CONVERSIONS` to be the outermost SELECT (remove the nested ROW_NUMBER block), cast output columns explicitly (e.g., `FLIGHT_ID::VARCHAR`, `CONVERSIONS::FLOAT`). Decide whether to surface `FLIGHT_COUNT` / `ALL_FLIGHT_IDS` or keep them comment-ready.                                                                                                                                         | Addresses TODO #5 in your notes and the reviewer request to simplify the final projection.                                                                             | DONE   |
| **Duplicate handling logic**      | Keep the `DUPLICATE_CONVERSIONS → MARKED_CONVERSIONS → FINAL_CONVERSIONS` chain, but verify it actually splits metrics evenly without zeroing rows. Run the validation query on the previously failing flight/date combos (e.g., flight `6P0KJ`, dates 2025‑04‑09/10/21/24). Document the before/after row counts in DE‑007.<br><br>**NOTE:**<br><br>- Need to check splitting logic in other conversion table? | Reviewer feedback was to fix the splitting, not to remove it. We already have the even-split logic; we just need to confirm it works with the current adapter changes. |        |
| **Viant adapter comments**        | Update the comments to match reality: we still aggregate Viant because `VIANT.CURRENT_CONVERSION_REPORT_CAMPAIGN` emits duplicates. Note the row-count evidence (426 total vs. smaller distinct grain) and that we have a CSV of dupes.                                                                                                                                                                         | Satisfies section 1 of your notes; keeps reviewers aligned with the latest findings.                                                                                   |        |
| **Documentation/testing updates** | Add the validation evidence (row counts, duplicate split proof, LinkedIn currently zero rows) to `tickets/backlog/DE-007.md` and/or `notes/tests/fct_campaign_conversions.md`. Mention that you verified `BETWEEN` inclusivity and the `EQUAL_NULL` swap.                                                                                                                                                       | Ensures the ticket reflects all completed PR feedback before requesting another review.                                                                                |        |
|                                   |                                                                                                                                                                                                                                                                                                                                                                                                                 |                                                                                                                                                                        |        |

---

### 2. Items to clarify with the senior dev

|Topic|Your Question|Suggested Talking Points|
|---|---|---|
|**Viant duplicate policy**|“Is there a reason not to filter duplicates at ingestion instead of aggregating here?”|Share the duplicate counts you computed and ask whether upstream dedupe is planned. Emphasize that the current approach (adapter `SUM`) keeps the fact clean but hides raw duplication.|
|**Shared flight-ID helper**|“Should I create the shared helper table/view as part of DE‑007 or spin a follow-up ticket?”|Outline the scope: today both `fct_platform_spend` and `fct_campaign_conversions` duplicate the `PLATFORM_*` CTEs. Propose either a shared view in `WAREHOUSE_UTILITY` or a separate dynamic table, and ask for a go/no-go decision.|
|**Viant GROUP BY vs. downstream dedupe**|“Do we want to remove the adapter GROUP BY and dedupe later?”|Explain that we still see exact duplicates in the Viant view, so removing the GROUP BY would reintroduce them unless we rely solely on the ROW_NUMBER filter. Ask whether they prefer end-of-pipeline dedupe or keeping the adapter aggregation.|
|**Schema location note**|“Table should live in `WAREHOUSE` vs. `WAREHOUSE_UTILITY`; is that intentional?”|Confirm whether leadership wants the dynamic table in `WAREHOUSE` (per your note) even though the SQL currently targets `WAREHOUSE_UTILITY`. If the plan is to relocate during deployment, make sure it’s documented.|
|**Flight-duplication helper location**|“If we build the shared flight lookup, is `WAREHOUSE_UTILITY` the right schema?”|Double-check before implementing; they may prefer `WAREHOUSE_SOURCE` or a view that can be reused by other facts.|

---

### 3. Recommended next steps

1. **Finalize code mechanics**

- Apply the explicit casting + outer SELECT change.
- Re-run duplicate split validation and capture the SQL + results.

2. **Refresh documentation**

- Update DE‑007 with: adapter duplicate counts, dedupe validation screenshot/SQL, LinkedIn status, and any schema-location decisions.

3. **Prepare senior-dev questions**

- Bundle the four clarification bullets above into one comment or meeting agenda so they can respond in a single pass.



## Review call with Steven

**Viant Adapter:**
- Dupes - filter vs grouping and summing
	- We may want to filter the duplicates instead of grouping and summing so we don't skew the conversions number value making reporting inaccurate
- inspect one example
- re-pull the data as duplicates could be created by running the connector multiple times.
	- This is not desired or expected



remove  aliases dup cwf - done
use equal_null() - done
Keep flight_count all_flight_ids columns - done
Copy the notes for flight splitting logic in the other fact into the conversions fact. - done



## Viant Adapter Validation

1. **Reproduce the duplicate grain check exactly**

- Use your earlier CTE (`base AS (...) SELECT COUNT(*), COUNT(DISTINCT …)`) but extend it to include `CONVERSIONS` so we can compare totals before/after deduping.
- Save a sample of rows where `COUNT(*) > 1`, ideally including all raw columns (especially metadata fields like ingestion timestamps).
-
![[Pasted image 20260226142601.png]]
- This tells us duplicates most likely have the same conversion value in their columns


2. **Inspect the duplicate columns**

- Are the dupes truly identical on every column except ingestion metadata (`___ALDC___GLOBAL_*`, `LOAD_TS`, etc.)?
- If yes, `ROW_NUMBER()…WHERE RN = 1` would keep values accurate without summing. If no, we need to identify which fields differ (could be updated conversions, partial loads, etc.).

## Root Cause 
- CONVERSION_EVENT_ID was missing from the PK in the connector template

## Resolving Steps:
- Add CONVERSION_EVENT_ID to PK in connector template.
- Run the adapter duplicate audit queries and expect no results to be returned.
	- **PASS**

Duplicate Audit Query:

`WITH base AS (`
    `SELECT`
        `ADVERTISER_ID::VARCHAR AS platform_account_id,`
        `CAMPAIGN_ID::VARCHAR AS platform_campaign_id,`
        `ORDER_ID::VARCHAR AS platform_order_id,`
        `CONVERSION_EVENT_ID::VARCHAR AS conversion_id,`
        `TO_DATE("DATE", 'MM/DD/YY') AS conversion_date,`
        `CONVERSIONS::FLOAT AS conversions`
    `FROM VIANT.CURRENT_CONVERSION_REPORT_CAMPAIGN`
`),`
`dup_check AS (`
    `SELECT`
        `platform_account_id,`
        `platform_campaign_id,`
        `platform_order_id,`
        `conversion_id,`
        `conversion_date,`
        `COUNT(*) AS row_count,`
        `COUNT(DISTINCT conversions) AS distinct_conversion_values`
    `FROM base`
    `GROUP BY 1,2,3,4,5`
    `HAVING COUNT(*) > 1`
`)`
`SELECT *`
`FROM dup_check`
`WHERE distinct_conversion_values > 1;`



3. **Connector run analysis**

- Pull the distinct values of any run/connector ID column to see if multiple executions on the same day create dupes. If the duplicates stem purely from re-runs, we might dedupe on the latest `LOAD_TS` rather than summing.

4. **Decide on the transformation**

- Option A: **Filter at source** — keep only the latest load per grain (using `QUALIFY ROW_NUMBER() OVER (PARTITION BY … ORDER BY LOAD_TS DESC) = 1`). This preserves original conversion values.
- Option B: **Aggregate in adapter** — current approach. Safe but can hide data issues (if duplicates aren’t perfect copies).
- Option C: **Hybrid** — filter exact dupes, then aggregate if needed as a final guardrail.

No need to validate at source

5. **Validation plan**

- Whatever change we make, rerun the adapter vs. fact totals to prove conversions are untouched.
- Document the logic (e.g., “We keep the latest load per grain using LOAD_TS”) in both the adapter comments and DE-007.

