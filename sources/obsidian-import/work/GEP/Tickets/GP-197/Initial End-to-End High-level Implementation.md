**Current behavior (warehouse/sales_fct_cost.sql)**  
`ORDERLINE_BASE` pulls SellerCloud + Amazon order lines, left joins `WAREHOUSE.SHARED_DIM_MARKETPLACE`, then hard-filters `MARKETPLACE_NAME IN ('Amazon US','Amazon CA','Amazon Mexico')`. Any new Amazon locale (UK, DE, AU, etc.) is dropped before fee allocation, so their orders never share in ad spend.

**Future-proof design**

1. **Centralize the Amazon definition** – Instead of hard-coding names inside `sales_fct_cost.sql`, derive an `IS_AMAZON_MARKETPLACE` flag once inside `WAREHOUSE_SOURCE.SHARED_DIM_MARKETPLACE` (or a small companion view). Logic: `LOWER(MARKETPLACE_NAME) LIKE 'amazon%' OR LOWER(COMPANY_NAME) LIKE 'amazon%'` plus any known aliases (e.g., “Amazon EU”, “Amazon JP”). This leverages the same marketplace enrichment already feeding that view, so future additions flow in automatically as soon as the CSV/source table gets a new “Amazon …” row.
    
2. **Filter via the flag** – Update `ORDERLINE_BASE` to `WHERE IS_AMAZON_MARKETPLACE = TRUE` (or join to a `WITH AMAZON_MARKETPLACES AS (...)` CTE selecting `MARKETPLACE_KEY`s with that flag). This keeps downstream logic untouched and makes the scope auditable.
    
3. **Document the assumption** – Add a short comment near the filter + in GP-197 notes clarifying that ad data is Amazon-only and tied to the new flag, so future ad sources will need their own flag/condition.
    

**Implementation outline**

1. Modify `warehouse/shared_dim_marketplace.sql`:
    - Introduce a computed column `IS_AMAZON_MARKETPLACE BOOLEAN`.
    - Populate it with `LOWER(COALESCE(MARKETPLACE_NAME, COMPANY_NAME, CHANNEL_NAME, '')) LIKE 'amazon%'`.
    - Keep existing output columns/backwards compatibility; adding a new column doesn’t break consumers.
2. Recreate both `WAREHOUSE_SOURCE.SHARED_DIM_MARKETPLACE` and the downstream `WAREHOUSE.SHARED_DIM_MARKETPLACE`.
3. Update `warehouse/sales_fct_cost.sql`’s `ORDERLINE_BASE` CTE to:    
    ```sql
    LEFT JOIN WAREHOUSE.SHARED_DIM_MARKETPLACE USING (MARKETPLACE_KEY)
    WHERE COALESCE(IS_AMAZON_MARKETPLACE, FALSE)
    ```
    
4. Recreate `WAREHOUSE_SOURCE.SALES_FCT_COST` and refresh the physical table `WAREHOUSE.SALES_FCT_COST` (per existing script footer).

**Testing plan**

1. **Coverage check** – In Snowflake, run `SELECT DISTINCT MARKETPLACE_NAME FROM WAREHOUSE.SHARED_DIM_MARKETPLACE WHERE IS_AMAZON_MARKETPLACE` to confirm the flag captures every Amazon locale (US, CA, MX, UK, EU, JP, etc.) and nothing else. If any Amazon name misses the pattern (e.g., “Amazon.co.uk”), add an explicit `OR` case.
2. **Filter diff** – Compare order-line counts before vs. after the change:

    ```sql
    WITH BEFORE AS (
      SELECT COUNT(*) AS orderlines
      FROM WAREHOUSE.SALES_FCT_COST -- current table (hard-coded filter)
    ),
    AFTER AS (
      SELECT COUNT(*) AS orderlines
      FROM WAREHOUSE_SOURCE.SALES_FCT_COST -- rebuilt via new filter
    )
    SELECT * FROM BEFORE CROSS JOIN AFTER;
    ```

The “after” number should be ≥ “before”; investigate any spikes to ensure only newly included Amazon marketplaces are responsible.
3. **Marketplace attribution smoke test** – `SELECT MARKETPLACE_NAME, SUM(PRODUCT_ADVERTISING_FEE_TRANSACTION) FROM WAREHOUSE_SOURCE.SALES_FCT_COST GROUP BY 1` and confirm non-Amazon marketplaces remain at zero.
4. **Fee allocation sanity** – Spot-check a few ASINs sold on Amazon UK (or another previously excluded locale) to verify they now get non-zero advertising allocations.