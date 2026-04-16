

# Clarifying questions

←  ☐ DTC fee base  ☐ sales_fct_cost  ✔ Submit  →

The existing code computes DTC fee as `SALES_GROSS_TRANSACTION * 0.03`. The GP-204 QA spec references `SALES_NET_TRANSACTION * DTC_FEE_RATE_PCT`. Which base should the new formula use?

❯ 1. Keep gross (Recommended) 

**Choice:** Keep gross.




## Overview

**Goal:** remove hard-coded marketplace-specific CASE statements from `sales_fct_orderline.sql`, allow analysts to configure net-discount + DTC fee behaviour via `SUPPLEMENT.CURRENT_MARKETPLACE_NAME_CSV`, and generalize the Amazon-only scope in `sales_fct_cost.sql`. The approach keeps logic centralized in the marketplace dimension so every fact that consumes it inherits the metadata.

Each design choice below includes the selected approach, why it was chosen, and a simpler (but less capable) alternative for future reference.

---

## 1. Store behaviour flags in the marketplace CSV

- **Decision:** Add three columns to `Marketplace Name.csv` (`APPLY_DISCOUNT_TO_NET`, `DTC_FEE_RATE`, `IS_AMAZON_MARKETPLACE`) and let analysts maintain them via the existing CSV workflow.
- **Why:**
    - Keeps marketplace-specific rules in the same artifact that already controls `MARKETPLACE_NAME`, so we avoid scattered config files.
    - Business users can update the CSV without any code deploys, speeding up marketplace onboarding.
    - Aligns with other GEP metadata patterns (CSV → SUPPLEMENT schema → shared dims).
- **Simpler option:** Hard-code JSON or YAML lookup tables inside the repo (or keep the CASE statements) and require dev deploys for every marketplace tweak. Lower initial effort, but still brittle and pushes ongoing maintenance back onto engineering.

## 2. Register the new columns with Eclipse

- **Decision:** Update `GEP/eclipse/templates/supplement/marketplace_name.json` so Eclipse ingests the three new fields automatically when the CSV refreshes.
- **Why:**
    - Keeps ingestion declarative; no manual Snowflake DDL needed when columns change.
    - Ensures the SUPPLEMENT table always matches the CSV schema.
- **Simpler option:** ALTER the SUPPLEMENT table by hand and skip the template update. Faster one-time change, but it will drift out of sync the next time Eclipse re-generates the table, so it’s fragile.

## 3. Surface normalized flags in `shared_dim_marketplace.sql`

- **Decision:** Pull the raw CSV columns into the view, convert them to strongly typed outputs (`*_FLAG`, `*_RATE_PCT`), and default NULLs to `FALSE/0` in the outermost SELECT.
- **Why:**
    - Centralizes parsing (string → boolean/number) in one place; downstream facts don’t need to repeat TRY_CAST/COALESCE logic.
    - The union-all rows that fabricate “unknown” marketplaces automatically inherit safe defaults.
    - Any other model that joins `shared_dim_marketplace` can reuse the flags immediately.
- **Simpler option:** Leave the dim untouched and join directly to `SUPPLEMENT.CURRENT_MARKETPLACE_NAME_CSV` (or parse strings) inside each fact. Less up-front work, but duplicates logic and increases the chance of inconsistent behaviour across facts.

## 4. Refactor `sales_fct_orderline.sql` to consume the new metadata

- **Decision:**
    - Replace the net-sales CASE with `IFF(APPLY_DISCOUNT_TO_NET_FLAG, …)`.
    - Replace the DTC `IFF` block with `SALES_GROSS_TRANSACTION * DTC_FEE_RATE_PCT`, preserving the existing gross base and consolidated counterpart.
    - Keep the DTC subtraction inside `MARGIN_NET_CONSOLIDATED` (already present).
- **Why:**
    - Removes all marketplace-name comparisons from the fact, so new marketplaces only require CSV edits.
    - `SALES_GROSS * rate` maintains current financial outputs for the four marketplaces that previously had the 3% fee.
    - Pulling the flags through the inner SELECT keeps the column set explicit for readers and BI tooling.
- **Simpler option:** Only refactor the net-sales CASE (leave the DTC block hard-coded). That would reduce code churn, but we’d still need deploys to onboard another DTC marketplace, **undermining the “self-serve” objective.**

## 5. Add `IS_AMAZON_MARKETPLACE_FLAG` for `sales_fct_cost.sql`

- **Decision:** Push an Amazon indicator from the CSV through the shared dim and replace the `WHERE MARKETPLACE_NAME IN ('Amazon US','Amazon CA','Amazon Mexico')` clause with `IS_AMAZON_MARKETPLACE_FLAG = TRUE`.
- **Why:**
    - Eliminates another brittle marketplace-name list and keeps Amazon scope aligned with metadata.
    - Future Amazon geos (e.g., Brazil) can be toggled via CSV without SQL edits.
- **Simpler option:** Leave the static WHERE clause. Lowest-effort change today, but every new Amazon marketplace would still need a code edit.

## 6. QA harness (`GEP/snowflake/GP-204-qa.sql`)

- **Decision:** Provide a reusable script that captures before/after aggregates, validates DTC effective rates, inspects the new dimension columns, and confirms Amazon marketplaces remain unchanged (aside from the metadata-driven filter).
- **Why:**
    - Repeatable proof for stakeholders; can be re-run whenever the CSV changes.
    - Temp-table pattern makes it easy to diff results and screenshot evidence for the ticket.
- **Simpler option:** Run ad-hoc queries in the worksheet and eyeball results. Faster initially, but harder to reproduce and easy to forget a check when revalidating later.

---

## Next Steps / Operational Notes

1. Update the Marketplace Name CSV with the three new columns + values (see table in the Claude plan for starters).
2. Allow Eclipse/SUPPLEMENT to ingest the new schema, then redeploy `shared_dim_marketplace`, `sales_fct_orderline`, and `sales_fct_cost`.
3. Run `GEP/snowflake/GP-204-qa.sql` before and after to capture evidence; stash outputs in `notes/projects/GP-204/testing.md` and paste highlights into `tickets/backlog/GP-204.md`.
4. Document who owns future CSV edits so ops knows how to adjust marketplace behaviour without code changes.