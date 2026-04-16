Created GEP/_testing/gp200_sandbox_validation.sql. Here's the approach:

  Setup — Creates a GP200_SANDBOX schema with mock tables mirroring the production structure (orders US, orders UK, Seller Cloud orders/items, currency map, marketplace fallback)

  Test data — 2 US orders, 3 UK orders, with 1 US and 1 UK already in Seller Cloud (for dedup testing)

  Test views — TEST_AMAZON_ALL_ORDERS exercises the UNION ALL CTE, TEST_ORDER_BASE_AMAZON exercises the dedup + company mapping logic

  12 tests covering:
  - T1-T3: UNION ALL correctness — total, UK, and US row counts
  - T4-T5: Dedup — orders in Seller Cloud are excluded (both US and UK)
  - T6-T8: Currency → company mapping — GBP→178, USD→163
  - T9: Marketplace fallback includes Amazon UK
  - T10: No duplicate order IDs after dedup
  - T11: Ship country preserved correctly for UK
  - T12: Fulfillment channel → location_id mapping works for UK

  Summary query — single result set showing all PASS/FAIL at a glance

  Teardown — DROP SCHEMA CASCADE at the end (comment out to inspect on failure)

# Integration Testing - Real Data

Created GEP/_testing/gp200_integration_validation.sql. Key differences from the mock version:

  Setup copies real production tables into GP200_INTEGRATION schema:                                                                                                                              - CURRENT_REPORT_ALL_ORDERS (US + UK)
  - Seller Cloud orders + order items (for dedup)                                                                                                                                               
  - Company currency map, state name map, product base
  - Baseline snapshots of current SALES_DIM_ORDER_BASE, SALES_FCT_AMAZON_ORDERLINE, and SHARED_DIM_MARKETPLACE for before/after comparison
  
  12 tests:
  - T1: Schema compatibility — US and UK tables have identical columns/types (catches drift)
  - T2-T3: UNION ALL integrity with real row counts
  - T4-T6: Currency → company mapping against real data
  - T7-T8: Dedup — no duplicate orders, Seller Cloud orders excluded
  - T9: Baseline comparison — non-GBP order count stable (delta ≤ 5 tolerance)
  - T10: No NULL company_id for known currencies
  - T11-T12: UK data quality — ship country, date sanity

  Tests that depend on UK data auto-SKIP if the UK table is empty (so you can run it before or after data flows). There's also a diagnostic query that shows a sample of 20 UK orders for       
  eyeball validation.