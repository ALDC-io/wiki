

### 2026-02-27 — Sponsored Display union in marketing fact
**Decision:** Add the Sponsored Display metrics union into `MARKETING_FCT_ACTIVITY` alongside Brands/Products.
**Rationale:** Ensure all Amazon Ads surfaces are represented in the fact without waiting on upstream restructuring.
**Follow-up:** Monitor performance once Display traffic increases; revisit aggregation keys if double-counting surfaces.

### 2026-02-27 — Platform name lookup for Sponsored Display
**Decision:** Keep the Sponsored Display branch’s platform name as a hard-coded literal until `MARKETING_DIM_PLATFORM_NAME` exposes a Display column (flagged for senior dev review).
**Rationale:** The current dim only returns Sponsored Brands/Products, so a literal avoids incorrect joins.
**Follow-up:** Track upstream dim change request; remove the literal once Display is available.

### 2026-03-02 — Marketplace profile mapping ownership
**Decision:** Plan to break the profile→marketplace mapping logic out of the fact into a dedicated dimension/table (target: next Monday).
**Rationale:** Multiple facts will need the same mapping; centralizing avoids repeated SQL edits when new profiles onboard.
**Follow-up:** Draft the standalone dimension design and migration steps; schedule implementation.

### 2026-03-03 — Brazil marketplace handling
**Decision:** Leave the Brazil Amazon Ads profile mapped to `UNKNOWN_MARKETPLACE` until `WAREHOUSE.SHARED_DIM_MARKETPLACE` adds the canonical row (`PRODUCT_ID = NULL`, `DEFAULT_VENDOR = NULL`, `LOCATION_ID = -1`, `COMPANY_ID = 174`).
**Rationale:** Avoid hard-coded marketplace IDs that drift from the shared dimension.
**Follow-up:** Monitor for the canonical row; wire it into the profile map once available.

### 2026-03-03 — Sponsored Display union deferred
**Decision:** Comment out the Sponsored Display branch in `MARKETING_FCT_ACTIVITY` for now; only Sponsored Brands/Products feed the fact.
**Rationale:** Senior dev requested parity with the legacy fact until downstream consumers are ready for Display spend.
**Follow-up:** Keep the Display block documented; re-enable once stakeholders approve.

### 2026-03-03 — Inline marketplace profile map
**Decision:** Keep `MARKETPLACE_PROFILE_MAP` as an inline `VALUES` CTE (one row per Amazon Ads profile) instead of joining to `SHARED_DIM_MARKETPLACE` or creating a new seed table.
**Rationale:** Guarantees we only emit valid profile↔marketplace pairs and avoids null `MARKETPLACE_ID`s when the shared dim lacks canonical rows (e.g., Brazil).
**Follow-up:** Add new rows to the CTE when additional profiles are onboarded; monitor Amazon Ads sources for unseen profile IDs.

