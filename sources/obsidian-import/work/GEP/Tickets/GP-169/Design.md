### ```
## Objective
Attach Marketplace Name/ID to Marketing Activity fact rows using deterministic profile-based mapping rather than currency inference.

## Inputs
- Sponsored Brands Campaign report (`CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT`) — has `PROFILEID`, campaign/currency metrics.
- Sponsored Products Advertised Product report (`CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`).
- Sponsored Display Campaign report (`CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT`).
- Marketplace dimension (`WAREHOUSE.SHARED_DIM_MARKETPLACE`) for canonical IDs + names.

## Proposed Flow
1. **Extend BASE_METRICS**
- Project `PROFILEID` from each Amazon Ads adapter query into `BASE_METRICS` CTE.
- Add Sponsored Display metrics block (mirrors other adapters) so Display spend joins the fact; without this union, Display campaigns never surface in Marketing_FCT or receive marketplace attribution.
- Preserve existing KPI columns (clicks, cost, conversions, sales, units, spend model, etc.).
2. **Profile → Marketplace mapping**
- Introduce `MARKETPLACE_PROFILE_MAP` CTE with columns: `PROFILE_ID`, `COUNTRY_CODE`, `CURRENCY_CODE`, `MARKETPLACE_ID`, `MARKETPLACE_NAME` (ensure both ID + human-readable name are available downstream without extra joins).
- Seed using Justin’s list (US/CAD/MX/BR). For MX and BR look up `MARKETPLACE_ID` in `WAREHOUSE.SHARED_DIM_MARKETPLACE` (expect `NULL_NULL_-1_168` for MX and a new ID for BR once `COMPANY_ID` confirmed).
- Keep map small + in-SQL for now; later option is a maintained table.
3. **Join logic**
- Replace current currency-based `MARKETPLACE_MAP` CTE with the new profile map.
- Join clause: `LEFT JOIN MARKETPLACE_PROFILE_MAP AS MARKETPLACE ON BASE.PROFILE_ID = MARKETPLACE.PROFILE_ID` and select both `MARKETPLACE_ID` + `MARKETPLACE_NAME` into the fact.
- Fallback: if no profile match, emit `MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'`, `MARKETPLACE_NAME = 'Unknown'`, and flag via QA query.
4. **Comments + rationale**
- Inline comments noting: profile IDs are 1:1 with marketplaces; currency-only inference failed once multi-country share a currency.
5. **Deployment scope**
- Update both `WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY` and `WAREHOUSE.MARKETING_FCT_ACTIVITY` (same SQL file) since downstream inherits via `SELECT *`.
- Ensure Sponsored Display addition doesn’t double-count (keep unioned metrics aligned with dedupe keys).

## Validation Plan
- Aggregation check: `SELECT PROFILE_ID, MARKETPLACE_ID, MARKETPLACE_NAME, CURRENCY_CODE, SUM(COST) FROM WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY GROUP BY 1,2,3,4;` expect 1 marketplace per profile.
- Coverage: query for `MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'` — should be zero once map seeded.
- Spot-check campaigns per profile to confirm Marketplace labels (e.g., `SELECT DISTINCT CAMPAIGN_ID, MARKETPLACE_NAME FROM ... WHERE PROFILE_ID = '2874274850477920';`).
- Currency sanity: ensure `CURRENCY_CODE` coming from base rows aligns with marketplace expectation (USD for US, CAD for CA, etc.).

## Data Flow Diagram (text)
`Amazon Ads Reports (Brands/Products/Display w/ PROFILEID)` → `BASE_METRICS (PROFILEID-projected)` → `MARKETPLACE_PROFILE_MAP` → `MARKETING_FCT_ACTIVITY` → `Downstream facts`.



## User Impact / Use Cases:

1. **Consistent marketplace filters**

- Analysts can now filter any marketing dashboard by a single canonical ID (e.g., `MARKETPLACE_ID = 'NULL_NULL_-1_163'`) and capture _all_ US spend, even if additional Amazon Ads profiles are onboarded later. No more alias lists or manual profile lookups.

2. **Cross-profile rollups without double counting**

- Finance can sum `COST`/`SALES_AMOUNT` by `MARKETPLACE_ID` or `MARKETPLACE_NAME` to compare US vs. CA performance. Because the mapping enforces one marketplace per profile, the rollup won’t merge unrelated spend or split a marketplace across multiple IDs.

3. **Regional aggregations independent of profile metadata**

- Once the downstream semantic layer groups canonical IDs into regions (e.g., Americas vs. EMEA), users can roll KPIs up by region without caring which advertiser profile generated the spend. The canonical ID becomes the single join key into region/group dims.

4. **Exception monitoring**

- Operations can run `SELECT PROFILE_ID FROM ... WHERE MARKETPLACE_ID = 'UNKNOWN_MARKETPLACE'` to spot newly ingested profiles that lack a mapping. This gives a clear QA hook for onboarding workflows.





### 2026-03-03 — Implementation notes
- `MARKETPLACE_PROFILE_MAP` now uses an inline `VALUES` block (one row per Amazon Ads profile) that surfaces `PROFILE_ID`, country, currency, canonical `MARKETPLACE_ID`, and human-readable name. This keeps the mapping self-contained and guarantees every row has a marketplace assignment even when `SHARED_DIM_MARKETPLACE` is missing canonical entries (e.g., Brazil).
- Sponsored Display union is deferred: the code block remains in comments, but the fact currently unions only Sponsored Brands + Sponsored Products until the senior dev green-lights Display metrics.