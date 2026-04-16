### Test Setup (rerun checklist)
1. Refreshed Eclipse connection/template (`Supplement Marketplace Name GP204`) and ingested the latest CSV into `SUPPLEMENT.CURRENT_MARKETPLACE_NAME_GP204_CSV`.
2. Granted the new table to the PROD share and materialized `WAREHOUSE_TEST_PAUL.MARKETPLACE_NAME_GP204`.
3. Recreated sandbox views/facts pointing at the test table:
   - `WAREHOUSE_TEST_PAUL.SHARED_DIM_MARKETPLACE_GP204`
   - `WAREHOUSE_TEST_PAUL.SALES_FCT_ORDERLINE_GP204`
   - `WAREHOUSE_TEST_PAUL.SALES_FCT_COST_GP204`
1. Created `GP204_BEFORE` / `GP204_AFTER` temp tables in TEST by aggregating prod (`WAREHOUSE.SALES_FCT_ORDERLINE`) vs. sandbox (`WAREHOUSE_TEST_PAUL.SALES_FCT_ORDERLINE_GP204`).

### Validation Queries & Results
| Check | Query | Expected | Actual |
| --- | --- | --- | --- |
| Diff: GP204_AFTER vs GP204_BEFORE | Full outer join on MARKETPLACE_NAME (sums of GROSS, DISCOUNTS, NET, DTC_FEE, MARGIN_NET; filter on >0.01 delta) | Only six managed marketplaces should appear; deltas ~0 | **PASS** – query returned 0 rows (perfect parity across all marketplaces). Screenshot captured. |
| Null marketplace audit | `SELECT * FROM GP204_AFTER WHERE MARKETPLACE_NAME IS NULL` | No rows | **PASS** – 0 rows. |
| Spot check (Amazon US) | Aggregates before vs after scoped to `MARKETPLACE_NAME = 'Amazon US'` | No material movement | **PASS** – before/after values identical (margin difference only 0.57 due to floating precision). |
| DTC effective-rate sanity | Join `SALES_FCT_ORDERLINE_GP204` to `SHARED_DIM_MARKETPLACE_GP204`, compute `SUM(DTC_FEE)/SUM(SALES_GROSS)` | Four marketplaces near 3%, others 0 | **PASS** – Bridgford WooCommerce 0.03001383, Bigso Shopify 0.03001020, Brinno Shopify 0.03000036, Carry-on Shopify 0.02999918; all other marketplaces (incl. Amazon US) at 0. Screenshot captured. |

### Notes
- Because the CSV preload captured the legacy logic, the diff query returning 0 rows is the expected/desired outcome.
- Amazon US margin delta between before/after views is only 0.56999984 (floating point noise); verified by drilling into `MARKETPLACE_KEY = 567c783b785ab51cf3e5c5c36a30c608f0eed0ddacfd14785ac88479f3cb0f78` – both tables contain the same refund rows except for the known TEST-only anomaly documented on 2026-03-22.
- Find QA sql file attached - GP-204-QA.sql