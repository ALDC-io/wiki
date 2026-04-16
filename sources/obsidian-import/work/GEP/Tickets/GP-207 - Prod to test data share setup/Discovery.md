1. **Share is mounted and accessible.** `PROD_DG1_GEP` shows up via `SHOW DATABASES` and exposes the four schemas we expected (AMAZON, AMAZON_ADS, SELLERCLOUD_SQL, SUPPLEMENT) plus the standard `INFORMATION_SCHEMA`. That covers every `CURRENT_/COMBINED_` source we grep’d in the repo.
    
2. **All required raw sources exist as shared views.** Each schema publishes both CURRENT_* and COMBINED_* view names that match the repo references exactly, so swapping to `PROD_DG1_GEP.<schema>.<view>` will work without additional renaming. (Note: they’re views rather than base tables, but Snowflake treats them the same for our purposes.)
    
3. **Two gaps remain:**
    

- `PROD_DG1_GEP.DUER_ANALYTICS` does **not** exist → `warehouse_comm_src/shared_dim_date.sql` can’t be fully prefixed yet. We’ll need either (a) the share owners to expose DUER_ANALYTICS, or (b) to rework that file to rely solely on the SUPPLEMENT calendar views.
- `PROD_DG1_GEP.SELLERCLOUD` (without `_SQL`) also doesn’t exist → `warehouse/shared_dim_customer.sql` still depends on `SELLERCLOUD.CURRENT_*`. We either stick with the current TEST-vs-PROD behavior for that one view or get SELLERCLOUD schema added to the share.

4. **Action items:**

- Capture these findings (especially the DUER_ANALYTICS/SELLERCLOUD gaps) in `notes/projects/GP-207` + the ticket.
- Decide whether to open a follow-up with the Snowflake admins to extend the share, or document exceptions for those two views before we start editing.
- Once the ticket is marked READY / we get the “go build,” we can run Batch A (data_share files) and continue through the rest of the plan using the confirmed schema list.