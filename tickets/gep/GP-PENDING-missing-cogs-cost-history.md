---
tags: [ticket, gep, navira, sku-profitability, cogs, cost-history, snowflake, sellercloud, in-progress]
aliases: [Missing COGs, COGS cost-history fix, Heather Missing COGs]
sources: []
created: 2026-05-28
updated: 2026-06-12
---

# Missing COGs / Cost-History Fix (GEP / Navira)

Catalog-wide blank-COGS / overstated-margin issue on the [[GEP]]/Navira SKU Profitability dashboard. Surfaced by Heather Tabor (Navira COO) via [[Lori Beck]] as a "Missing COGs" request for 5 CIBU CBD SKUs — investigation showed it is a **much broader, catalog-wide** cost-attribution issue. Distinct from [[GP-259]] (which is about adding dashboard *measures*); this is about the COGS *data* being blank.

> **Status (2026-05-28): root cause confirmed + fix validated. Awaiting Navira's choice of option (sent to Lori). No production change made yet. May warrant its own Jira ticket.**
>
> **UPDATE (2026-06-12): Option A built + validated in TEST as a non-destructive evidence pack — the artifact that unblocks Navira's sign-off. $20.5M recovered / 1,024,475 lines, zero regression (0 per-item mismatches / 2.77M lines), CIBU 5 SKUs auto-recover EXACTLY $12.82/12.25/11.84/26.91/26.91 with NO override table. Live TEST deploy DEFERRED (Paul, 2026-06-12) pending resolution of an intermittent UK-share dependency. PROD stays gated on Navira sign-off. See § 2026-06-12 below.**

## The request (entry point)

- Heather emailed Lori: "update these orders with the COGs in column F … something happened in SellerCloud … messing up our margin." Sheet: `Missing COGs.xlsx` (in `~/Downloads`).
- 5 CIBU CBD SKUs: `PRODUCT_ID` **30004, 30005, 30006, 30009, 30010**. 94 order lines / 58 orders / **$4,331.50** gross / proposed COGS **$1,995.08** (column F unit costs 12.82 / 12.25 / 11.84 / 26.91 / 26.91). All validated to the penny against PROD.

## Root cause (two distinct causes — confirmed with reproducible queries on PROD `wj66376` / `PROD_DG1_GEP`)

COGS on the final fact comes from `WAREHOUSE.SALES_FCT_COST_HISTORY` (a **VIEW**, derived from SellerCloud `COMBINED_MAIN_PRODUCT` SITECOST change-history via LAG/LEAD). The COGS-per-item logic in `WAREHOUSE_SOURCE.SALES_FCT_SELLER_CLOUD_ORDERLINE`:
```sql
CASE WHEN COST_HISTORY.LANDED_COST != 0 THEN COST_HISTORY.LANDED_COST
     WHEN COST_HISTORY.SITE_COST   != 0 THEN COST_HISTORY.SITE_COST END  -- no ELSE -> NULL when cost is 0
```
joined point-in-time on `DIM_ORDER.CREATE_DATE BETWEEN COST_HISTORY.VALID_FROM AND VALID_TO`.

- **Cause A — Historical cost horizon (~94% of the gap).** Cost history (`COMBINED_MAIN_PRODUCT`) begins **2024-05-30**; sales go back to **2023-01-01**. ~17 months of older orders have no cost record to attribute → blank COGS. ~994K lines / ~$44M gross. One-time, bounded (does not grow). The costs almost certainly existed in SellerCloud then; we just never ingested history that far back.
- **Cause B — New-product / cost-field timing (small, ongoing).** A product sells before a usable cost is on record. CIBU example: created 2026-03-18, first sold 2026-04-29; cost `$12.82` was in **AVERAGECOST/LASTCOST from 2026-04-16** (before first sale) but the **SITECOST field the view reads** wasn't set until **2026-05-20**. ~2,300 lines + new products as they launch.

Scale: ~**36%** of all gross>0 order lines currently have blank COGS (~1.05M of ~2.74M); blended COGS ratio ~27.6% (artificially low). Not limited to CIBU — top affected SKUs: REVO830W/EVO820GM (Kuvings juicers), DWPSK5A (Drain Weasel), 135B (Thomastik strings).

## The fix (recommended: Option A) — validated, not yet deployed

Modify the cost-history view `WAREHOUSE_SOURCE.SALES_FCT_COST_HISTORY`:
1. **Field fallback:** effective cost = `COALESCE(NULLIF(SITECOST,0), NULLIF(AVERAGECOST,0), NULLIF(LASTCOST,0))` — fixes Cause B (would have caught CIBU).
2. **Back-fill:** drop leading null-cost intervals and extend the first known-cost interval's `VALID_FROM` backward, so orders predating the cost inherit the earliest known cost — fixes Cause A.
Preserve the existing `LANDED_COST` priority in the COGS CASE.

### Validation (full-catalog, non-destructive — shadow views in a `SCRATCH_GP259` schema, dropped after)
- **Zero regression:** of ~1,695,715 already-costed lines, **0 changed**, **$0.00 delta** (isolated fix-view vs current-view, both live).
- **Recovery:** ~**977,427** previously-blank lines populated, ~**$21.1M** COGS added.
- CIBU subset: 94 lines → $1,995.08, 0 null; the 46 already-correct CIBU lines unchanged ($916.32).
- Margins on worst SKUs move from implausible (0.4–4% COGS) to realistic (30–69%).

### Edge-case residual (irreducible) — 272 lines / 42 products / ~$14.1K gross
Products with no cost in any SellerCloud field, ever. Categories: replacement parts (`P-…`), used-condition variants (`…-Used-VG`), open-box (`…_OB`), unmatched Amazon placeholders (`…missing`/`FBA…`), RMA/automation/parent placeholders (`TLC5000`, `…_Automation_UnexpectedItem`, `INGRED3`). Handling options offered: (1) leave as-is, (2) inherit base-product cost for variants (7 have a costed base), (3) exclude/flag non-sales placeholders.

## 2026-06-12 — Option A built + validated in TEST (evidence pack)

Validated in `TEST_DG1_GEP` (prod-share-fed), read-only, **nothing live mutated**. Full pack: `aldc-launchpad/warehouse_ops/_gp259_optionA_EVIDENCE_PACK.md`.

**Implementation chosen (refinement of the earlier plan):** instead of rewriting the cost-history view's `VALID_FROM`, Option A is added as **additive branches in the per-item cost CASE** of `WAREHOUSE_SOURCE.SALES_FCT_SELLER_CLOUD_ORDERLINE` — fires ONLY when the existing point-in-time cost is NULL/0, so already-costed lines are byte-identical (zero regression *by construction*):
1. `COST_EARLIEST` CTE = product's earliest known real cost (landed→site) → backfills orders predating the cost record (Cause A).
2. current `AVERAGECOST`→`SITECOST` from the order line → new-product timing gap (Cause B, incl. CIBU).
3. `COGS_SOURCE_GP259A` classifier column = transparency (point-in-time vs which backfill).

**Validated at the CONSUMER layer** (final fact, via the proven identity `SALES_COGS_CONSOLIDATED = ROUND(per_item × SALES_COGS_QUANTITY, 2)`):
- **Control fidelity:** 0 per-item mismatches across 2,771,445 lines (a control column reproduces the live table exactly — proves the validation view is faithful even with the absent UK arm neutralized).
- **Regression:** 1,742,623 covered lines; 2 lines differ by $0.02 (a penny round-half artifact of the recompute, not Option A) → zero true regression, proven per-line.
- **Recovery:** **$20,503,906 across 1,024,475 lines** (277 stay blank — no cost anywhere). Matches the ~$21M estimate.
- **Coverage:** 54.5% → 86.0% whole-fact; **99.97% of sales-bearing SC lines** (the 86% is dragged by the 452K-line zero-sales "UNK / No-Match" branch which correctly stays blank).
- **Transparency split:** ~$16.3M earliest-site + ~$4.2M earliest-landed (pre-2024 backfill) + small current-cost tail (CIBU).
- **CIBU 5 SKUs:** Option A independently recovers $12.82/12.25/11.84/26.91/26.91 (= Heather's column F) via current-avg fallback — **no manual override table needed**.

**Lineage confirmed (TEST):** fact `WAREHOUSE.SALES_FCT_ORDERLINE` is a BASE TABLE rebuilt by `TASK_WAREHOUSE_ORDERLINE_0..9` (CTAS chain) from the source view. Blank COGS is 97.5% pre-2024 SellerCloud lines; the Amazon-report branch is negligible (26,861 lines, 102 blank) → the single SC-view edit is the catalog-wide fix.

**CORRECTION to earlier note:** TEST *does* now contain the CIBU products (Q5 returned them with 54/31/28/41/38 lines) — the prod→test share has them. CIBU validation no longer requires PROD.

**Live TEST deploy — what remains (gated):** the live SC view references the SHARED `PROD_DG1_GEP.AMAZON.CURRENT_REPORT_ALL_ORDERS_UK`, which is intermittently absent (present at the 06:01 `TASK_2` build, gone midday — GP-257 UK never promoted to the prod→test share). Fact rebuild fails when UK is absent. Resolve that first; deploy as owner role `TEST_DG1_ROLE_CORE_SVC_DA8904DB` + `COPY GRANTS`; then validate at PBI/DAX model `66151728` (GEP Test Models). Deploy artifact: `_gp259_optionA_SHADOW_scview.sql`; rollback `_gp259_optionA_ROLLBACK_TEST_*.sql`.

## Cost-VALUE feed stall (2026-03-03) — separate upstream issue → **Jira [[GP-281]]** (NEXT workstream)

Discovered while validating Option A; **does not block it** (Option A backfills blanks; this is staleness on *covered* lines). Diagnosed read-only (`_gp259_costfreeze_rootcause.py`):
- **Product cost VALUES (`SITECOST`/`LANDEDCOST`) stopped changing ~2026-03-03.** SITECOST-changes/month: healthy 875–4,643 through Feb-2026 → 279 in early Mar → zero after.
- **NOT a warehouse/history bug:** CURRENT_MAIN_PRODUCT.SITECOST == latest cost-history value for 38,239 / 39,387 products (97%) → current agrees with frozen history ⇒ costs genuinely aren't changing.
- **NOT a general sync outage:** products modified May/Jun-2026 (22,861 / 18,670); `LASTTIMEUPDATEDFORPANDL` active through Jun. Only the cost *values* froze.
- **Root cause (hypothesis):** the upstream **ALDC Library cost integration** that writes SellerCloud product costs died 2026-03-03 — same date as exchange rates ([[exchange-rate-pipeline]] / `project_exchange_rate_pipeline`). Compare [[GP-PENDING-sales-data-outage-2026-05-22]] (also an ALDC Library grant/feed failure). **Fix is upstream (ALDC Library / connector), cross-repo — not the warehouse.**
- **Harm:** silent staleness on covered lines (true cost moved post-Mar, COGS keeps the Mar-03 value). Option A cannot correct these.

## Options presented to Navira (via Lori, 2026-05-28)
- **A. Back-fill + field fallback** (recommended — recovers ~$21M, self-healing, zero regression)
- **B. Field fallback only** (~5% fixed)
- **C. Keep blank but flag/exclude** (accurate-but-incomplete)
- **D. Manual per-SKU override** (reactive, doesn't scale)
- **E. Source pre-2024 cost history** (most accurate for history; depends on retrievability — Paul to dig into whether SellerCloud history before 2024-05-30 is obtainable; can complement A)

Full options doc: `aldc-launchpad/gp259-cogs-fix-options-gep.md`. Reply email to Heather (sent) + options email to Lori (sent 2026-05-28).

## Next steps (pick up tomorrow)
1. **Await Navira's option choice** (via Lori). Likely Option A.
2. On confirmation: write production DDL for `WAREHOUSE_SOURCE.SALES_FCT_COST_HISTORY` (fallback + back-fill, landed-cost preserved) + decide edge-case handling (1/2/3).
3. **Investigate Option E feasibility** — can we get SellerCloud cost history before 2024-05-30?
4. Promote QA → UAT → PROD; rebuild warehouse fact chain; refresh PBI model so the dashboard reflects it.
5. Decide whether this needs its own Jira ticket (currently logged here; GP-259 is the measures issue).
6. Optional: "sales-with-no-cost" monitor for the residual new-product lag window.

## Key references
- Diagnostic/validation scripts: `aldc-launchpad/scripts/_gp259_*.py` (esp. `_gp259_verify.py`); saved DDLs `_gp259_srcview_prod.sql`, `_gp259_costhist_view.sql`.
- Snowflake creds: [[infra-credentials]] vault — TEST `og35375` `PAULRUSSELLADMIN`, PROD `wj66376` personal `paulrussell` (SYSADMIN). **NOTE: TEST does not contain the CIBU products — validation must be done against PROD.**
- Objects: `WAREHOUSE.SALES_FCT_COST_HISTORY` (view), `WAREHOUSE_SOURCE.SALES_FCT_SELLER_CLOUD_ORDERLINE`, `WAREHOUSE_SOURCE.SALES_FCT_ORDERLINE`, `SELLERCLOUD_SQL.COMBINED_MAIN_PRODUCT`.

## Related
- [[GP-259]] — Orders/Return & COGs *measures* for SKU Profitability (distinct; measures, not data)
- [[GEP]] — Client
- [[data-pipeline-flow]]
