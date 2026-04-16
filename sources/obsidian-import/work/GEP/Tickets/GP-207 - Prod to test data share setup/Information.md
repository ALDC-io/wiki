GP-207  
Description

Set all GEP tables to use PROD_DG1_GEP data share table when referencing the current views. All current and combined views are now available. Adding the prefix should allow both test and prod tables to have the same table names and always reference the same raw data through the share.


# Potential Approach

1. **Understand the target share + scope.** Verify the full Snowflake identifier for the PROD_DG1_GEP share (database + schema) and confirm it exposes every raw table currently referenced by GEP views (both “current” and “combined”). Capture that mapping in the ticket so everyone knows which share/schema names we expect.
    
2. **Inventory dependencies.** In `repos/clients/GEP/snowflake/`, grep the warehouse + warehouse_source SQL for fully-qualified references to the old raw databases/schemas. Build a checklist of affected views/tables (likely all marketing fact/dim objects and any helper views) so we don’t miss oddballs like staging QA views.
    
3. **Decide on the refactor style.** Ideally introduce a single alias (e.g., CTE or view wrapper) or shared dim that points to `PROD_DG1_GEP.<schema>.<table>` so both test and prod environments import the same share without duplicating prefixes. If a global search/replace is safer, stage the changes file-by-file but document the pattern (old `GEP_RAW.<schema>` → new `PROD_DG1_GEP.<schema>`). Update any deploy scripts or docs that mention the old source.
    
4. **Implement + verify locally (test env).** Edit the SQL files to use the share prefix, then run whatever local validation we have (Snowflake dry-run, syntax check) to ensure the views compile. Capture diff snippets in the ticket.
    
5. **QA with parity checks.** In Snowflake test, run row-count + checksum comparisons between the updated views (pointing at the share) and the current prod versions to prove the data matches. Store the SQL + results under `notes/projects/GP-207/testing.md`.
    
6. **Document + ticket updates.** Summarize the change, add deploy/rollback steps (since both test/prod will now point at the same share), and note any required coordination (e.g., ensuring the share is refreshed regularly). Only move to implementation once the ticket is marked READY or you explicitly green-light it.




# Solidified Approach

### 1. Tables to update directly in Snowflake UI (non-`WAREHOUSE*`, all `CURRENT_/COMBINED_` sources)

Re-point each of these raw views to `PROD_DG1_GEP.<schema>.<table>` so both TEST and PROD land on the same prod data share. Grouped by schema for easier find/replace:

- **AMAZON**  
    `CURRENT_REPORT_ALL_ORDERS`, `CURRENT_REPORT_RETURN`, `CURRENT_REPORT_FBA_RETURN`, `CURRENT_REPORT_FBA_INVENTORY`, `CURRENT_REPORT_SALES_AND_TRAFFIC_CHILD`, `CURRENT_SELLER_PARTICIPATION`, `CURRENT_CLASSIFICATION_ITEM`, `COMBINED_REPORT_FBA_INVENTORY`, `COMBINED_REPORT_MERCHANT_LISTINGS`, `COMBINED_REPORT_OPEN_LISTINGS`
    
- **AMAZON_ADS**  
    `CURRENT_API_BRAND`, `CURRENT_API_PORTFOLIO`, `CURRENT_SPONSORED_PRODUCTS_CAMPAIGN`, `CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`, `CURRENT_SPONSORED_PRODUCTS_PURCHASED_PRODUCT_REPORT`, `CURRENT_SPONSORED_BRANDS_CAMPAIGN`, `CURRENT_SPONSORED_BRANDS_CAMPAIGN_REPORT`, `CURRENT_SPONSORED_DISPLAY_CAMPAIGN`, `CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT`
    
- **SELLERCLOUD_SQL**  
    `CURRENT_MAIN_ORDER`, `CURRENT_MAIN_ORDERITEM`, `CURRENT_MAIN_ORDERPAYMENT`, `CURRENT_MAIN_ORDERTRANSACTIONITEM_PANDL_EXTENDED`, `CURRENT_MAIN_PRODUCT`, `CURRENT_MAIN_PRODUCT_PROPERTIES_AMAZON`, `CURRENT_MAIN_PRODUCT_PROPERTIES_USER_DEFINED`, `CURRENT_MAIN_PURCHASE`, `CURRENT_MAIN_PURCHASEITEM`, `CURRENT_MAIN_VENDOR`, `CURRENT_MAIN_VENDOR_PRODUCT`, `CURRENT_MAIN_INVENTORY_PANDL`, `CURRENT_MAIN_WAREHOUSE`, `CURRENT_MAIN_BRAND`, `CURRENT_MAIN_MANUFACTURER`  
    plus the history tables that use combined snapshots: `COMBINED_MAIN_PRODUCT`, `COMBINED_MAIN_PRODUCT_PROPERTIES_USER_DEFINED`, `COMBINED_MAIN_PURCHASEITEM`
    
- **SUPPLEMENT**  
    `CURRENT_TIME_CALENDAR`, `CURRENT_ACCOUNT_MANAGER_CSV`, `CURRENT_COMPANY_NAME_CSV`, `CURRENT_FINANCE_CURRENCY`, `CURRENT_FORECAST_CSV`, `CURRENT_KPI_PERIODICITY`, `CURRENT_MARKETPLACE_NAME_CSV`, `CURRENT_SELLERCLOUD_CHANNEL_MAP_CSV`, `CURRENT_SKU_KITS_CSV`, `CURRENT_STATE_NAME_MAP_CSV`
    
- **Other schemas referenced** (double-check they exist in the share; if not, we may need an alternate source)  
    `DUER_ANALYTICS.CURRENT_ANALYTICS_DIM_CALENDAR`, `SELLERCLOUD.CURRENT_CUSTOMER_MAIN`, `SELLERCLOUD.CURRENT_ORDERS_HEADER`
    

**Snowflake procedure:** for each affected view in TEST (and later PROD), run `CREATE OR REPLACE VIEW <DB>.<schema>.<view> AS SELECT ... FROM PROD_DG1_GEP.<schema>.<table>;`. Keep the view bodies identical, only the fully qualified table prefixes change. Capture the list + commands in the ticket so we know what was touched server-side before Git catches up.

---

### 2. GitHub updates (clients/GEP repo)

1. **Inventory + checklist.** Inside `repos/clients/GEP/snowflake/`, enumerate every file that references the tables above (you can reuse the Python regex output we just generated). Log the list under `notes/projects/GP-207/discovery.md`.
    
2. **Introduce a consistent prefix.** In each SQL file, replace the existing database references (`TEST_DG1_GEP`, `WAREHOUSE_SOURCE`, etc.) with `PROD_DG1_GEP.<schema>` for those raw `CURRENT_/COMBINED_` tables. Keep `WAREHOUSE*` objects pointing where they already point (per Steven’s guidance). If certain views (e.g., `shared_dim_date`) reference schemas not included in the share, flag them in the ticket for follow-up before editing.
    
3. **Batch edits > piecemeal.** Make the replacements per schema so you can sanity-check diffs (e.g., all SELLERCLOUD_SQL updates in one commit chunk, all SUPPLEMENT in another). Don’t implement yet until the ticket is READY, but having the patch staged locally will make review easy.
    
4. **Documentation + QA prep.** Update the ticket worklog with:
    
    - the Snowflake UI changes already applied,
    - any schemas that still need share coverage, and
    - the plan for parity testing (row counts + sample diffs comparing TEST vs PROD after the prefix swap).
5. **Future deploy steps.** Once the ticket is approved for implementation, push the SQL changes, run the standard Snowflake QA (rowcount + checksum on the key warehouse facts/dims), and document deploy/rollback instructions so the team can keep TEST/PROD aligned.