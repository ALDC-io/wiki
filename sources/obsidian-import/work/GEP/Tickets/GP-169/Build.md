Steps to re-design solution using PROFILE ID column

### 1. Confirm the join path (what lives where)

- Every adapter table (`CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT`, `CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`, `CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT`) already has `PROFILEID`.
- `marketing_fct_activity.sql` is the single place those adapters union into `BASE_METRICS`. So we simply add `PROFILEID AS PROFILE_ID` to each branch, include it in the `GROUP BY`, and expose it in the outer `SELECT`. No other files need touching.

### 2. Build a profile → marketplace map that leans on existing dims

Instead of hard-coding full `MARKETPLACE_ID` strings, piggyback on `WAREHOUSE.SHARED_DIM_MARKETPLACE` (same file you pointed to) so the IDs/names stay canonical:

```sql
MARKETPLACE_PROFILE_MAP AS (
SELECT
PROFILE_MAP.PROFILE_ID,
PROFILE_MAP.COUNTRY_CODE,
PROFILE_MAP.CURRENCY_CODE,
DIM.MARKETPLACE_ID,
DIM.MARKETPLACE_NAME
FROM (
SELECT * FROM VALUES
('2874274850477920', 'US', 'USD', 163), -- Amazon US
('410071870980733', 'CA', 'CAD', 166), -- Amazon CA
('1359269695432602', 'MX', 'MXN', 168), -- Amazon MX
('2944710254877284', 'BR', 'BRL', 174) -- Amazon BR (company id from dim lookup)
) AS PROFILE_MAP(PROFILE_ID, COUNTRY_CODE, CURRENCY_CODE, COMPANY_ID)
LEFT JOIN WAREHOUSE.SHARED_DIM_MARKETPLACE AS DIM
ON DIM.MARKETPLACE_ID = CONCAT('NULL_NULL_-1_', PROFILE_MAP.COMPANY_ID)
)
```

That way, if `MARKETPLACE_NAME` ever changes upstream, the fact inherits it automatically. To finish this, we just need to confirm the `COMPANY_ID` for Brazil in the dim (MX already appears as 168 in `shared_dim_marketplace.sql`). So yes—lookup those IDs now via:

```sql
SELECT DISTINCT COMPANY_ID, COMPANY_NAME, MARKETPLACE_ID, MARKETPLACE_NAME
FROM WAREHOUSE.SHARED_DIM_MARKETPLACE
WHERE MARKETPLACE_NAME ILIKE 'Amazon %';
```

Grab the Mexico/Brazil company IDs and plug them into the VALUES list.

### 3. Update `BASE_METRICS` + the final SELECT

For each adapter:

```sql
SELECT
...,
PROFILEID AS PROFILE_ID,
CAMPAIGNBUDGETCURRENCYCODE AS CURRENCY_CODE,
SUM(...) AS ...
FROM AMAZON_ADS.CURRENT_SPONSORED_...
GROUP BY
PLATFORM_ID, CAMPAIGN_ID, AD_GROUP_ID, <product column>,
ACTIVITY_DATE, SPEND_MODEL, PROFILE_ID, CURRENCY_CODE;
```

Then in the final SELECT:

```sql
SELECT
...,
BASE.PROFILE_ID,
COALESCE(MARKETPLACE.MARKETPLACE_ID, 'UNKNOWN_MARKETPLACE') AS MARKETPLACE_ID,
SHA2(COALESCE(MARKETPLACE.MARKETPLACE_ID, 'UNKNOWN_MARKETPLACE')) AS MARKETPLACE_KEY,
COALESCE(MARKETPLACE.MARKETPLACE_NAME, 'Unknown') AS MARKETPLACE_NAME,
...
FROM BASE_METRICS AS BASE
LEFT JOIN MARKETPLACE_PROFILE_MAP AS MARKETPLACE
ON BASE.PROFILE_ID = MARKETPLACE.PROFILE_ID;
```

### 4. Refresh the build doc

Add explicit steps to `notes/projects/DE-006/build.md`:

- “Lookup MX/BR `COMPANY_ID`/`MARKETPLACE_ID` from `WAREHOUSE.SHARED_DIM_MARKETPLACE` and update the profile map VALUES list.”
- “Project `PROFILE_ID` through BASE_METRICS + outer SELECT.”
- “Replace `MARKETPLACE_MAP` with the new CTE that joins to `SHARED_DIM_MARKETPLACE`.”

### 5. Validate

Use the testing queries we outlined, plus:

```sql
SELECT PROFILE_ID, MARKETPLACE_NAME, COUNT(*)
FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY
GROUP BY 1,2;
```

should show 1:1 mapping; check for `UNKNOWN_MARKETPLACE`.




# Action Items/Build Steps


# DE-006 / GP-169 — Build Checklist

1. **SQL prep**
- Update `repos/clients/GEP/snowflake/warehouse/marketing_fct_activity.sql`:
- Add `PROFILE_ID` projection + grouping to each BASE_METRICS union branch.
- Add Sponsored Display branch mirroring other adapters (ensure `PROFILEID`, `CAMPAIGNBUDGETCURRENCYCODE`). Without this union, Display campaigns stay invisible in Marketing_FCT and never receive marketplace attribution.
- Replace `MARKETPLACE_MAP` CTE with `MARKETPLACE_PROFILE_MAP` containing Justin’s mappings + MX/BR IDs from `SHARED_DIM_MARKETPLACE`.
- Join BASE → MAP on `PROFILE_ID`.
  
1. **Comments & QA hooks**
- Document why profile-based mapping is required vs currency inference.
- Surface `MARKETPLACE_NAME` in the final select so QA/consumers can see the label without another join.
3. **Local validation**
- Run `snowsql`/dbt equivalent or `SELECT * FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY LIMIT ...` in DEV to ensure SQL compiles.
- Execute validation queries listed in `testing.md` (profile coverage, unknown marketplace detection, campaign spot checks).
4. **Version control**
- `git status` to confirm only intended files changed.
- Stage + commit with message like `GP-169: add profile-based marketplace map to marketing fact` (only after Paul approves commits).
- Push branch `feature/paulrussell/GP-169/profile-marketplace-map` once approved.




## 2026-03-03 

- Updated `MARKETPLACE_PROFILE_MAP` CTE to derive `COMPANY_ID` via `SPLIT_PART(MARKETPLACE_ID, '_', 4)` because `SHARED_DIM_MARKETPLACE` doesn’t expose the column directly.
- No temporary override for the Brazil profile; expect `MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'` until the canonical dim row (`NULL_NULL_-1_174`) exists.



### 2026-03-03
- Reworked `MARKETING_FCT_ACTIVITY`:
- Replaced `MARKETPLACE_MAP` with an inline `MARKETPLACE_PROFILE_MAP` (`VALUES` CTE returning profile → canonical marketplace ID/name).
- Commented out the Sponsored Display union per senior-dev guidance (Brands/Products only for now).
- Prefixed final SELECT columns with `BASE.` and added inline comments about the Brazil placeholder mapping.
- Recreated `WAREHOUSE_TEST_PAUL.MARKETING_FCT_ACTIVITY_GP169` with the new logic; validated row count + metric parity and verified the unknown-marketplace audit.
