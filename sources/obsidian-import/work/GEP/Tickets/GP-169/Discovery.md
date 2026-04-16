# Inventory

Inspecting the source tables confirms Sponsored Brands/Products/Display tables present in `TEST_DG1_GEP.AMAZON_ADS`.

```sql
-- Confirm Amazon Ads connector schemas
SHOW SCHEMAS IN DATABASE TEST_DG1_GEP;

-- List tables under Amazon Ads schema (should include CURRENT_* reports)
SHOW TABLES IN SCHEMA TEST_DG1_GEP.PUBLIC;

-- Inventory Amazon Ads connector tables (row counts + last refresh)
SELECT table_catalog, table_schema, table_name, row_count, last_altered AS last_refresh
FROM TEST_DG1_GEP.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'AMAZON_ADS'
AND table_name ILIKE 'CURRENT_%'
ORDER BY table_name, last_refresh DESC;
```

Verifies `MARKETING_FCT_ACTIVITY` lives in both `WAREHOUSE_SOURCE` and `WAREHOUSE`.

```sql
-- Marketing fact views in warehouse schemas
SELECT table_catalog, table_schema, table_name, row_count, last_altered
FROM TEST_DG1_GEP.INFORMATION_SCHEMA.TABLES
WHERE table_schema IN ('WAREHOUSE_SOURCE', 'WAREHOUSE')
AND table_name ILIKE 'MARKETING_%'
ORDER BY table_schema, table_name;
```

---

# Source Currency Integrity

## Check 1

```sql
-- Null currency audit across all campaign report types
SELECT 'SPONSORED_PRODUCTS' AS source_table,
COUNT(*) AS total_rows,
SUM(IFF(CAMPAIGNBUDGETCURRENCYCODE IS NULL, 1, 0)) AS null_currency_rows
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT
UNION ALL
SELECT 'SPONSORED_BRANDS',
COUNT(*),
SUM(IFF(CAMPAIGNBUDGETCURRENCYCODE IS NULL, 1, 0))
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT
UNION ALL
SELECT 'SPONSORED_DISPLAY',
COUNT(*),
SUM(IFF(CAMPAIGNBUDGETCURRENCYCODE IS NULL, 1, 0))
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT;
```

![Pasted image 20260227105653.png]

**Finding:** `null_currency_rows = 0` for all three sources—currency is always populated.

## Check 2

```sql
-- Currency distribution by source table
SELECT source_table,
campaignbudgetcurrencycode AS currency_code,
COUNT(*) AS row_count
FROM (
SELECT 'SPONSORED_PRODUCTS' AS source_table, CAMPAIGNBUDGETCURRENCYCODE
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT
UNION ALL
SELECT 'SPONSORED_BRANDS', CAMPAIGNBUDGETCURRENCYCODE
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT
UNION ALL
SELECT 'SPONSORED_DISPLAY', CAMPAIGNBUDGETCURRENCYCODE
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT
)
GROUP BY source_table, campaignbudgetcurrencycode
ORDER BY source_table, campaignbudgetcurrencycode;
```

**Finding:** Only `USD` and `CAD` appear in current data; aligns with known US/CA marketplaces. Need to accommodate MXN/BRL profiles once they’re ingested.

---

# Profile Coverage (Newly Added)

```sql
SELECT PROFILE_ID,
CAMPAIGNBUDGETCURRENCYCODE AS currency_code,
COUNT(*) AS num_rows
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT
GROUP BY 1,2
ORDER BY 1;

SELECT PROFILE_ID,
CAMPAIGNBUDGETCURRENCYCODE AS currency_code,
COUNT(*) AS num_rows
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT
GROUP BY 1,2
ORDER BY 1;

SELECT PROFILE_ID,
CAMPAIGNBUDGETCURRENCYCODE AS currency_code,
COUNT(*) AS num_rows
FROM TEST_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT
GROUP BY 1,2
ORDER BY 1;
```

**Findings:**

- Only two active profiles appear across all adapters:
- `2874274850477920` (USD) — Amazon US
- `410071870980733` (CAD) — Amazon CA
- Sponsored Products shows one additional profile (`3378484324565094`, USD, 1 row). Since it isn’t in Justin’s list, treat it as `UNKNOWN_MARKETPLACE` until confirmed.
- No MX (`1359269695432602`) or BR (`2944710254877284`) profiles exist in current source data, so their marketplace IDs can’t be validated yet. Keep placeholders in the profile map and rely on QA to flag any `UNKNOWN_MARKETPLACE` rows when those profiles start ingesting.

---

# Marketplace Dimension Notes

```sql
-- Inspect marketplace dimension sample
SELECT *
FROM TEST_DG1_GEP.WAREHOUSE.SHARED_DIM_MARKETPLACE
LIMIT 50;

-- Amazon-only slice (shows canonical marketplace_id values)
SELECT marketplace_name,
marketplace_id,
default_vendor,
product_id,
location_id,
REGEXP_SUBSTR(marketplace_id, '[0-9]+$') AS company_id_suffix
FROM TEST_DG1_GEP.WAREHOUSE.SHARED_DIM_MARKETPLACE
WHERE marketplace_name IN ('Amazon US', 'Amazon CA')
ORDER BY marketplace_name;
```

**Notes/Considerations:**

- `MARKETPLACE_ID` structure = `COALESCE(PRODUCT_ID,'NULL') || '_' || COALESCE(DEFAULT_VENDOR,'NULL') || '_' || LOCATION_ID || '_' || COMPANY_ID`.
- Amazon marketplaces we care about use IDs like `NULL_NULL_-1_163` (US) and `NULL_NULL_-1_166` (CA). These IDs already exist in the dimension and match what Marketing fact expects.
- The current `MARKETPLACE_MAP` CTE in `marketing_fct_activity.sql` maps USD → US ID, CAD → CA ID, but doesn’t cover MX/BR.
- _Change required:_ shift to profile-based mapping so each `PROFILE_ID` joins directly to its marketplace. MX/BR entries remain placeholders until their profiles ingest.






## 2026‑03‑03 — Canonical marketplace rows

```sql
SELECT
MARKETPLACE_NAME,
MARKETPLACE_ID,
SPLIT_PART(MARKETPLACE_ID, '_', 4)::INT AS COMPANY_ID
FROM WAREHOUSE.SHARED_DIM_MARKETPLACE
WHERE PRODUCT_ID IS NULL
AND DEFAULT_VENDOR IS NULL
AND LOCATION_ID = -1
ORDER BY COMPANY_ID;
```

Result:
![[Pasted image 20260303101816.png]]
- Amazon US, Amazon CA, Amazon Mexico exist
- There is no marketplace_id for Amazon BRL


### Check explicitly for Amazon Brazil

```sql
SELECT
MARKETPLACE_NAME,
MARKETPLACE_ID
FROM WAREHOUSE.SHARED_DIM_MARKETPLACE
WHERE PRODUCT_ID IS NULL
AND DEFAULT_VENDOR IS NULL
AND LOCATION_ID = -1
AND SPLIT_PART(MARKETPLACE_ID, '_', 4) = '174';
```

**Result:**
![[Pasted image 20260303102335.png]]

- No results returned
- This specific combination does not exist for brazil in shared_dim_marketplace


## Check explicitly for Amazon Brazil - Expand search
- Removing DEFAULT_VENDOR, PRODUCT_ID, LOCATION_ID filter.

**Result:**
![[Pasted image 20260303102505.png]]

- We can now see Amazon Brazil Rows - all with different marketplace_ids

**Clarifications:**
- What do we do with these?
- Are they meant to be filtered out? - I'm confused at this point


## **Finding:** 
- Brazil has only product/vendor-specific rows (`<PRODUCT>_<VENDOR>_<LOCATION>_<COMPANY>`), no canonical `NULL_NULL_-1_174` record. 
- “No canonical row for company 174 as of 2026‑03‑03” .


1. **How to interpret those rows:**

- Each ID encodes a _specific_ SKU + vendor combination shipped via a fulfillment channel (`LOCATION_ID = 20` here).
- Marketing data never carries SKU or vendor, so we can’t pick the right one without guessing. Using them would give us 20+ different “Amazon Brazil” IDs depending on which vendor happened to run the ad, defeating the whole point of deterministic marketplace attribution.
- They exist in the dimension to support sales/order reporting, where joins include `PRODUCT_ID` and `DEFAULT_VENDOR`.

1. **What we should do instead:**
- Stick with the canonical-row strategy. For Brazil, that means asking the data team to insert the missing `PRODUCT_ID = NULL`, `DEFAULT_VENDOR = NULL`, `LOCATION_ID = -1`, `COMPANY_ID = 174` record (with name “Amazon Brazil” or similar).
- Until that row appears, our fact table should continue emitting `UNKNOWN_MARKETPLACE` for the Brazil profile. If we absolutely must show “Amazon Brazil” immediately, we can hard-code a temporary literal inside `MARKETPLACE_PROFILE_MAP`, but we should document that under **Decisions** (e.g., “Temporary override for BR marketplace id until shared dim adds canonical row”).



### 2026-03-03 — Fact parity checks
- Initial row-count delta (new fact = 733,630 vs. old = 724,805) was entirely Sponsored Display. After commenting out the Display union, row counts now match 1:1.
- Legacy `WAREHOUSE.MARKETING_FCT_ACTIVITY` does not project `PROFILE_ID` or `CURRENCY_CODE`; parity checks must target the shared columns only (platform/campaign/ad group/product/date/spend model + metrics).

