1. **Extend the marketplace metadata source (CSV):**
    
    - Add `APPLY_DISCOUNT_TO_NET` (Yes/No/blank) and `DTC_FEE_RATE` (decimal percent) to `SUPPLEMENT.CURRENT_MARKETPLACE_NAME_CSV`, keeping the current join keys (lowercased `CHANNEL_NAME` + `COMPANY_NAME`) intact.
    - Backfill values for the six marketplaces that currently live in the inline CASE for net discounts (`Target`, `Bridgford WooCommerce`, `Bigso Shopify`, `Brinno Shopify`, `Carry-on Shopify`, `GEP Brands`) plus whatever set triggers the 3 % DTC fee today, so behaviour stays unchanged after the flip.
2. **Surface the new columns through `shared_dim_marketplace.sql`:**
    
    - Project the CSV columns as typed fields, e.g., `APPLY_DISCOUNT_TO_NET_FLAG BOOLEAN` (treat null/blank as FALSE) and `DTC_FEE_RATE_PCT NUMBER(5,3)` (default 0). These will sit alongside `MARKETPLACE_NAME/KEY`, so every fact that joins the dimension can inherit the metadata without hard-coding names.
    - Sanity-check that the “unknown marketplace” UNION ALL block also emits defaults for the new fields, so fallback rows never produce null behaviour.
3. **Refactor the order-line fact(s):**
    
    - In `sales_fct_orderline.sql`, pull the new columns from `DIM_MARKETPLACE` inside the large SELECT and replace the `MARKETPLACE_NAME IN (…)` logic at lines 72‑92 with a flag-driven expression: `IFF(DIM_MARKETPLACE.APPLY_DISCOUNT_TO_NET_FLAG, SALES_GROSS - REFUNDS - DISCOUNTS, SALES_GROSS - REFUNDS)`.
    - Add a dedicated `DTC_FEE_TRANSACTION` (and consolidated counterpart) field that multiplies `SALES_NET_TRANSACTION` by `DTC_FEE_RATE_PCT`; subtract it in the `MARGIN_NET_CONSOLIDATED` rollup the same way we already subtract commissions, shipping, advertising, etc. Use the same flag to emit 0 for marketplaces without a rate.
    - Mirror the change anywhere else the CASE might exist (quick grep for `MARKETPLACE_NAME IN` shows `sales_fct_cost.sql` still whitelists Amazon marketplaces—decide whether that should eventually key off metadata too).
4. **QA + deployment steps:**
    
    - Diff row counts and measure aggregates (net, consolidated net, new DTC fee, margin) per marketplace before/after in Snowflake TEST to prove no regressions outside the flagged marketplaces.
    - Validate at least one marketplace with the new DTC percentage to ensure the fee equals 3 % (or whatever is set in the CSV) of net, and that unaffected marketplaces remain identical.
    - Document the CSV schema change, data-entry ownership, and QA evidence in `notes/projects/GP-204/` plus the ticket before promoting.

This keeps marketplace-specific business rules in a self-service CSV, avoids brittle name comparisons, and gives us a clean hook for any future per-marketplace behaviour (fees, tax rules, etc.).