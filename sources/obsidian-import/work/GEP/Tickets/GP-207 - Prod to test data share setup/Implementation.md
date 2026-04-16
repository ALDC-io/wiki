
Added prefixes to all tables - excluding the 5 below


Only five objects remain un-prefixed, all intentionally:

1. `DUER_ANALYTICS.CURRENT_ANALYTICS_DIM_CALENDAR` (referenced in `warehouse_comm_src/shared_dim_date.sql`) — DUER isn’t part of the PROD_DG1_GEP share, so we leave this legacy calendar in place.
2. `SELLERCLOUD.CURRENT_CUSTOMER_MAIN` and `SELLERCLOUD.CURRENT_ORDERS_HEADER` (both in `warehouse/shared_dim_customer.sql`) — the share only exposes `SELLERCLOUD_SQL`, so the legacy SELLERCLOUD schema still backs the customer dimension.
3. `TEST_DG1_ALDC_LIBRARY.SUPPLEMENT.CURRENT_KPI_PERIODICITY` (`warehouse/shared_dim_periodicity.sql`) — that KPI periodicity CSV lives in the ALDC library, not the prod share.
4. `TEST_DG1_ALDC_LIBRARY.WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` (`warehouse/shared_fct_exchange_rate.sql`) — the canonical exchange-rate view is published out of the ALDC library and isn’t part of the PROD_DG1_GEP share.

Everything else under `GEP/snowflake/warehouse*/` now points at `PROD_DG1_GEP.<schema>.<CURRENT_/COMBINED_*>` as expected.

