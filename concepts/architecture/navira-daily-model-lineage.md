---
tags: [architecture, lineage, data-flow, navira, gep, power-bi, snowflake, daily-model, sales-model]
aliases: [Navira Daily Model Lineage, 66151728 Lineage, Daily Data Model Data Flow, Navira Sales Model Lineage]
sources: [aldc-launchpad/pbi_ops/_gp291_baselines/Data_Model_66151728_20260722T033253Z.tmsl.json, aldc-launchpad/.claude/plans/lovely-brewing-simon.md]
created: 2026-07-22
updated: 2026-08-09
---

# Navira Daily "Data Model" (`66151728`) — Data-Flow / Lineage Map

**Purpose.** Single reference for **what feeds every table** in the Navira Daily (Sales) Power BI model
`66151728`, so any future edit (add/remove a column, chase a wrong number, re-point a source) starts from the
proven source object rather than inference. Evidence-gated per the global change rules — always confirm the
object a consumer reads before changing it (`[[star-schema-convention]]`, `[[data-pipeline-flow]]`).

> **Two-model context (2026-07-22).** There are now two PBI models: this **Daily *Sales* Model** (`66151728`,
> workspace `GEP Test Models`) and the separate **Marketing Model** (`2d8587b5`). GP-291 Phase 1 stripped Daily
> to sales-only (44→33 tables); the current session selectively re-adds the two ad-spend tables. See
> [[navira-roadmap-status]] and `aldc-launchpad/pbi_ops/_gp291_phase1_deletion_record.md`.
>
> **UPDATE 2026-07-23 (live-verified):** the GP-226 re-add is **done and live** — a fresh read-only TMSL pull
> shows Daily = **35 tables**, with `Marketing Efficiency` (24 cols incl. the `SPEND_USD_AMAZON_SP/SB/SD`
> ad-type split; 48 measures, 19 visible / 29 hidden — only `Spend` + `Contribution Margin` folders visible)
> and `Marketing Efficiency Product` (10 cols, 3 measures) present. The friendly-name + definition map for
> every table below now lives in [[navira-metric-dictionary]] (feeds [[GP-292]] + [[GP-290]]).

## Model facts
- **Dataset:** `Data Model`, id `66151728-f00f-4a08-af91-6687de5f13dc`, workspace **GEP Test Models**.
- **Shape (pre-GP-291 baseline `…033253Z`):** 44 tables / 381 measures / 38 relationships. Post-Phase-1 live
  shape = 33 / 281 / 19 (marketing tables removed; being partially re-added this session).
- **Snowflake account (M params):** host `og35375.canada-central.azure.snowflakecomputing.com`, warehouse
  `COMPUTE_WH`, database resolved via `PARAM_SHORT_CODE` → **`TEST_DG1_GEP`**.
- **Two Snowflake schemas feed the model:** **`WAREHOUSE`** (star-schema dims/facts) and **`REPORT_COMMON`**
  (report-layer views: Agency, Marketing Efficiency, Google grounding, MAP overview, Default). A few tables are
  fed by the **CORE_API** report endpoint or are inline/calculated (see below), not Snowflake.
- **Refresh:** Eclipse rebuilds the `WAREHOUSE`/`REPORT_COMMON` layer nightly (~06:00 PDT); PBI import model
  refreshes on the GEP Test Models schedule. `Order`, `Order Line`, `Traffic Activity` use **PBI incremental
  refresh** (RangeStart `2025-07-01` → RangeEnd `2026-07-01` window; historical fixes need a full-partition
  reprocess, `RefreshType.Full`). See `[[project_navira_consumer_layer_pipeline]]`.

> ### ⚠⚠ A CIRCULAR DEPENDENCY LIVES IN THIS LINEAGE — `SALES_FCT_COST` ↔ `SALES_DIM_ORDER`
> **Proven [[GP-322]] 2026-08-10.** `WAREHOUSE_SOURCE.SALES_DIM_ORDER` appends rows read back out of
> `WAREHOUSE.SALES_FCT_COST` (`ATTRIBUTION_TYPE = 'No Match'`, the `UNK_` rows of
> [[gep-unknown-order-placeholders]]), while the cost fact's ad-cost **allocation denominator** reads
> that same dimension. A cycle cannot be scheduled, only broken — and the nightly build breaks it in the
> damaging direction:
>
> ```
> 06:00:01  SALES_DIM_ORDER_BASE   <- allocation's CONSUMER side   T-0 fresh
> 06:02:32  SALES_FCT_COST         <- the allocation materialises HERE
> 06:02:48  SALES_DIM_ORDER        <- allocation's DENOMINATOR      T-1 STALE
> ```
>
> ⇒ the allocated ad-cost columns are **wrong on the trailing ~3 days of every single build** (the newest
> day by up to ~27×), and self-heal as orders land. Closed months are correct. **This inflates ad cost and
> therefore UNDERSTATES net margin** — `Actual - Margin - Net`, `Net Margin Loaded (USD)` and
> `MARGIN_NET_CONSOLIDATED` all inherit it. **Anyone reading a current-month figure off this lineage must
> know this.** Mechanism, detection recipe and remedy: [[circular-dependency-build-order]].
>
> ⚠ Note `Net Margin Loaded (USD)` inherits the defect **through the warehouse**
> (`MARGIN_NET_CONSOLIDATED` subtracts the three fee columns), so a TOM/DAX dependency closure does **not**
> reveal it. Enumerating measure bodies alone undercounts the affected set by one.

## Table → source object (verified offline from the TMSL baseline, 2026-07-22)
`vis` = visible in the client field list (blank = hidden). `IR` = PBI incremental-refresh (source is the
refresh-policy source expression). All Snowflake objects are in `TEST_DG1_GEP`.

### Sales facts & the shared star (KEEP — the Daily model core)
| PBI table | vis | Snowflake source | type | Role / grain |
|---|---|---|---|---|
| **Order Line** | ✓ | `WAREHOUSE.SALES_FCT_ORDERLINE` | Table (IR) | Core sales fact — gross/net/units/returns/COGS/fees/margin; multi-brand `ENTITY_CODE` (121 cols) |
| **Order** | ✓ | `WAREHOUSE.SALES_DIM_ORDER` | Table (IR) | Order header dim |
| **Traffic Activity** | (H) | `WAREHOUSE.TRAFFIC_FCT_ACTIVITY` | View (IR) | Sessions / page views / buy-box |
| **Date** | ✓ | `WAREHOUSE.SHARED_DIM_DATE` | View | Date dim |
| **Product** | ✓ | `WAREHOUSE.SHARED_DIM_PRODUCT` | Table | Product dim (45 cols) |
| **Marketplace** | ✓ | `WAREHOUSE.SHARED_DIM_MARKETPLACE` | View | Marketplace dim |
| **Vendor** | ✓ | `WAREHOUSE.SHARED_DIM_VENDOR` | View | Vendor dim |
| **Location** | (H) | `WAREHOUSE.SHARED_DIM_LOCATION` | View | Location dim |
| **Customer** | (H) | `WAREHOUSE.SHARED_DIM_CUSTOMER` | View | Customer dim (+10 measures) |
| **Customer Cohort** | ✓ | `WAREHOUSE.SHARED_DIM_CUSTOMER_COHORT` | Table | Cohort dim (TREATAS-joined) |
| **Periodicity** | ✓ | `WAREHOUSE.SHARED_DIM_PERIODICITY` | View | Time-period toggle (`[[periodicity]]`) |
| **Warehouse** | (H) | `WAREHOUSE.SHARED_DIM_WAREHOUSE` | View | Warehouse dim (orphan — not joined) |
| **Agency** | ✓ | `REPORT_COMMON.MARKETING_DIM_AGENCY` | View | Agency dim (`ENTITY_CODE`/`Agency`/`ENTITY_ROLE`) — Navira/Lectric |
| **Brand** | ✓ | *(calculated DAX table)* | calc | Distinct brand from `Product[Brand]` |
| **Inventory Balance** | (H) | `WAREHOUSE.INVENTORY_FCT_BALANCE` | Table | FBA/on-hand inventory |
| **Purchasing Balance** | (H) | `WAREHOUSE.PURCHASING_FCT_BALANCE` | Table | PO balances |

### Ad-spend layer (this session's re-add targets)
| PBI table | vis | Snowflake source | type | Role / grain |
|---|---|---|---|---|
| **Marketing Efficiency** | ✓ | `REPORT_COMMON.MARKETING_EFFICIENCY_MARGIN` | View | Spend/sales/COGS/margin at `ENTITY × MARKETPLACE × DATE`; Amazon UK/US/CA + Google/Meta (Cross-Channel) (21 cols / 45 measures) |
| **Marketing Efficiency Product** | ✓ | `REPORT_COMMON.MARKETING_EFFICIENCY_PRODUCT` | View | Per-ASIN spend + grounded ROAS (SP+SB; SD excluded, no SKU) (10 cols / 3 measures) |

### Other marketing (removed from Daily by GP-291 → live in Marketing Model `2d8587b5`)
| PBI table | Snowflake source | Note |
|---|---|---|
| Marketing Activity | `WAREHOUSE.MARKETING_FCT_ACTIVITY_UNIFIED` | Ad activity fact; **ad type = `PLATFORM_ID`** (SP/SB/SD, Google, Meta) |
| Marketing Platform Detail | `WAREHOUSE.MARKETING_FCT_PLATFORM_DETAIL` | Google/Meta platform metrics |
| Google Brand Grounding | `REPORT_COMMON.MARKETING_EFFICIENCY_GOOGLE_BRAND` | Grounded ROAS (brand) |
| Google Product Grounding | `REPORT_COMMON.MARKETING_EFFICIENCY_GOOGLE_PRODUCT` | Grounded ROAS (product) |
| Creative | `WAREHOUSE.MARKETING_FCT_CREATIVE` | Ad creative perf |
| Creative Placement | `WAREHOUSE.MARKETING_FCT_CREATIVE_PLACEMENT` | Placement perf |
| Campaign | `WAREHOUSE.MARKETING_DIM_CAMPAIGN` | Campaign dim |
| Platform | `WAREHOUSE.MARKETING_DIM_PLATFORM` | Platform dim |
| Navira MAP Violators | `REPORT_COMMON.NAVIRA_MAP_VIOLATORS_OVERVIEW` | MAP monitoring (→ GP-293 native Eclipse) |
| MAP Violators Daily | `WAREHOUSE.NAVIRA_MAP_VIOLATORS` | MAP daily |
| MAP Violators by Brand | `REPORT_COMMON.NAVIRA_MAP_VIOLATORS_SELLER_BRAND_90D` | MAP brand roll-up |

### Report plumbing / measure hosts (NOT Snowflake facts — leave as-is)
| PBI table | Source | Note |
|---|---|---|
| **API Metadata** | **CORE_API** `POST {CORE_API_URL}/v1/report/detail` (account `da8904db`, report `25ca82be…`) | The one live web call; report template metadata (capacity/glossary/config) |
| Report Metadata / Glossary / Configuration | derived from `#"API Metadata"` | GEP report-template metadata |
| PARAM_SHORT_CODE | `API Metadata[capacity].options.database_warehouse` | Resolves the Snowflake DB name (multi-tenant) |
| Default Warehouse | `REPORT_COMMON.DEFAULT_DEFAULT` | GEP template harvester |
| Sales Measures (174) / Marketing Measures (24) / Marketplace Measures (16) / Inventory Measures (36) | inline `Table.FromRows(Json.Document(…))` | Measure-group hosts — no data columns |
| Consolidation / COGS Behavior | inline constant table | Single-column harvester toggles |
| RangeStartDate / RangeEndDate | derived from `RangeStart`/`RangeEnd` params | Incremental-refresh bounds (leave hidden) |

## Snowflake upstream chains — ✅ TRACED LIVE via `GET_DDL` (2026-07-22)
⚠ **Drift caught:** the base efficiency view the PBI chain actually reads is **`REPORT_COMMON.MARKETING_EFFICIENCY`**,
NOT `WAREHOUSE_TEST_GP226.MARKETING_EFFICIENCY` (what the repo DDLs imply). Always trace live
(`[[project_navira_deployed_truth_parity]]`).

**Ad-spend chain (the this-session targets):**
- `REPORT_COMMON.MARKETING_EFFICIENCY_MARGIN` ← `REPORT_COMMON.MARKETING_EFFICIENCY` (spend/sales base)
  + `WAREHOUSE.SALES_FCT_ORDERLINE` (COGS/margin join) + `WAREHOUSE.SHARED_DIM_MARKETPLACE`.
- `REPORT_COMMON.MARKETING_EFFICIENCY` ← (a) `WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY` = Amazon **SP+SB**
  (passthrough of `PROD_DG1_GEP.WAREHOUSE.MARKETING_FCT_ACTIVITY` via share); (b)
  `WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY_PREPROD` = **UK-SP** (`WAREHOUSE_TEST_NAVIRA_ROADMAP.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`)
  + **SD** (`PROD_DG1_GEP.AMAZON_ADS.CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT`) + **Google**
  (`GOOGLE_ADS.CURRENT_GOOGLE_ADS_CAMPAIGN`) + **Meta** (`META.CURRENT_FACEBOOK_AD_INSIGHTS`) + `SHARED_DIM_ENTITY`;
  (c) `WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` (FX to USD); (d) `WAREHOUSE.SALES_FCT_ORDERLINE` (actual orders);
  (e) `WAREHOUSE_SOURCE.SALES_FCT_LECTRIC_AMAZON_ORDERLINE` (Lectric).
  - **CTE structure:** `AMZ_DAY` unions Amazon SP+SB (from `MARKETING_FCT_ACTIVITY`) + SP+SD (from `_PREPROD`,
    `PLATFORM_ID IN ('Amazon Ads Sponsored Products','Amazon Ads Sponsored Display')`) → the inner union
    **currently drops `PLATFORM_ID`** (selects only mkt/date/COST/SALES). `GM_DAY` = Google/Meta on the
    `Cross-Channel` marketplace row. **⇒ SP/SB/SD ad-type split must be injected here:** carry `PLATFORM_ID`
    through `AMZ_DAY`→`AMZ_USD`→`COMBINED`, emit `SPEND_USD_AMAZON_SP/SB/SD`, then pass them through
    `MARKETING_EFFICIENCY_MARGIN`.
- `REPORT_COMMON.MARKETING_EFFICIENCY_PRODUCT` ← `WAREHOUSE.SALES_FCT_ORDERLINE` + `WAREHOUSE.SHARED_DIM_PRODUCT_BASE`
  (SKU→ASIN bridge) + `WAREHOUSE.SHARED_FCT_EXCHANGE_RATE` + `WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY`
  (**Amazon SP+SB only — NO `_PREPROD`, so no UK/SD/Google/Meta per-ASIN**; SD excluded anyway, `PRODUCT_ID='-1'`).

**Consolidation (2026-07-22, GP-226).** There were two near-identical view pairs:
`MARKETING_EFFICIENCY(_MARGIN)` (Daily) and `..._FIXED` (Marketing Model `2d8587b5`). The `_FIXED` pair alone
carried the `AND OL.ENTITY_CODE='NAVIRA'` filter on `SALES_DAY`/`COGS_DAY`; without it the canonical pair let
Lectric orders (native in Order Line via GP-254, $0 COGS) leak into the NAVIRA branch, **overstating Navira
Contribution Margin by ~$2.72M ($40.61M → correct $37.89M)**. Fix: the **canonical `MARKETING_EFFICIENCY(_MARGIN)`
now carries the NAVIRA filter + the `SPEND_USD_AMAZON_SP/SB/SD` ad-type split**, and **both PBI models read this
one pair** (Marketing Model repointed off `..._MARGIN_FIXED`). The `_FIXED` base+margin pair is now **orphaned →
flag for cleanup** once no other consumer is confirmed. Repo templates: `clients/GEP/snowflake/warehouse/`
`marketing_efficiency.sql`, `marketing_efficiency_margin.sql`, `marketing_fct_activity_preprod.sql`
(branch `feature/paulrussell/gp226-uk-source-parity-adtype`).

**Sales chain:** `WAREHOUSE.SALES_FCT_ORDERLINE` is a **materialized table** (Eclipse-built, no view refs).
Composed upstream (seen via `SHARED_DIM_MARKETPLACE` lineage) from `WAREHOUSE.SALES_FCT_AMAZON_ORDERLINE` +
`WAREHOUSE.SALES_FCT_SELLER_CLOUD_ORDERLINE` + `WAREHOUSE_SOURCE.SALES_FCT_LECTRIC_AMAZON_ORDERLINE`
(GP-259 COGS backfill; GP-254 Lectric). Carries the DQ-001 fee columns `{BRAND,NOSALE,PRODUCT}_ADVERTISING_FEE_CONSOLIDATED`.

**Data notes (verified 2026-07-22):**
- UK **ad spend** live in `REPORT_COMMON.MARKETING_EFFICIENCY` = **£2,982 / $3,968.17** (feed 2026; through
  2026-07-22). ⚠ Roadmap hub cited UK ≈ £4,961 / $6.6K on 2026-07-21 → **drift between the WAREHOUSE_TEST_GP226
  copy and the REPORT_COMMON copy the PBI reads — reconcile during Step 1.**
- UK **advertising FEES** (`Order Line`, the DQ-001 measure) = **$0** for CY2026 (only Amazon US $656K / CA $7.6K
  carry fees) — but UK **sales are present & fresh** (786 CY2026 lines, $115,050 gross, through 2026-07-21).
  So "UK = $0" on `Actual − Cost − Advertising` is a genuine Amazon-fee-scope reality, not a stale workbook.

**Ad-spend basis + UK findings (verified 2026-07-23, TEST):**
- **Two "advertising" figures, not one.** `Actual - Cost - Advertising` = Order-Line
  `{BRAND,NOSALE,PRODUCT}_ADVERTISING_FEE_CONSOLIDATED` = Amazon **settlement FEES** (finance), Amazon US/CA
  only. `Spend - Amazon` (+SP/SB/SD) = **campaign ad spend** (Ads API → `REPORT_COMMON.MARKETING_EFFICIENCY`),
  all marketplaces incl UK + Google/Meta. Within ~3% for US/CA; UK is the real gap. **Decision: ADDITIVE —
  keep both, relabel distinctly, do NOT swap** (zero change to existing numbers). Dictionary `sm_adv_cost_total`
  friendly name → "Amazon Advertising Fees (settlement)".
- **UK settlement fee genuinely $0 (not a bug):** UK order lines exist (2,793 lines / $336K gross) with the fee
  columns **non-null but zero** — Amazon UK settlement carries no advertising fees (US = $2.28M / 3.16M lines).
- **UK ad spend = Sponsored Products ONLY — coverage gap:** the source has only `Amazon Ads Sponsored Products`
  for UK ($4,962.86 local / $6,602 USD); **no UK SB/SD rows exist** (only the SP advertised-product feed was
  connected via GP-257). Cannot confirm whether UK ran SB/SD → propose connecting UK SB/SD feeds.
- **Three fixes shipped (TEST, additive, rollback-enabled):** (1) A3/A2 ad cost USD-consolidated
  (`WAREHOUSE.MARKETING_FCT_ACTIVITY_UNIFIED` gained `COST_USD`/`SALES_AMOUNT_USD`; the 2 activity measures
  redefined to USD); (2) `Marketing Efficiency` now relates to the `Marketplace` dim (calc key
  `MARKETPLACE_KEY_XREF` = MIN dim key per name — the raw hash key is ~12,000×/name, so a name join fan-outs);
  (3) `MARKETING_EFFICIENCY_PRODUCT` extended base→base∪PREPROD(SP+SD) so UK appears at ASIN grain
  ($6,603.89, fully resolved). Client uses the **Live models** (not the deprecated reports). Client discussion
  doc + comparison: `aldc-launchpad/docs/evidence/gp226/`. Branch `feature/lectric-scheduled-connector`.

## ⭐ Consumer-layer defects found 2026-08-09/10 (`/assay`, 7 lenses) — READ BEFORE EDITING THIS MODEL

All read-only, all re-runnable. Evidence: `aldc-launchpad/docs/evidence/gp317/assay-findings-ledger.md`
(+ ~30 JSONs). **None fixed.** Boot prompt for the first one:
`aldc-launchpad/boot-prompts/navira-august-allocation-divergence-inquest.md`.

### ⭐⭐ THE DURABLE LESSON — validate in the gesture the CLIENT uses, not all-time

Seven independent lenses measured this model for hours and all missed the biggest defect, because every
one of them measured **all-time**. Paul then supplied one sentence of context — *"the client normally
uses a pivot with calendar year on it, filtering for current year, so YTD"* — and reproducing that
single gesture exposed a **262% error in the current month**.

| Basis | What it showed |
|---|---|
| all-time | the two Amazon ad figures differ by **+4.1%** — looks reassuring |
| CY2026 YTD | **+12.3%** |
| **August 2026** | **allocated $163,689 vs spend $45,198 — +262%** |

**The all-time view actively hid it**, because CY2024 (−0.2%) and CY2025 (−0.2%) dilute it. So does the
"99.81% reconciliation over 26 months" that had been quoted to the client — measured on PROD, dominated
by the agreeing months. ⇒ **Ask how the consumer slices before choosing a validation window, and put
their pivot in the battery.** A defect can be invisible in every window except theirs.

### The five model-layer defects (all MEASURED, none fixed)

1. **The marketplace SLICER silently drops all Google + Meta; the MATRIX does not.**
   `REPORT_COMMON.MARKETING_EFFICIENCY` relabels the fact's `Unknown` marketplace to `Cross-Channel`,
   which is **not a member of `SHARED_DIM_MARKETPLACE`** ⇒ `MARKETPLACE_KEY_XREF`
   (`MINX(FILTER(...))`) returns BLANK on exactly **768 rows / $244,870.44** ⇒ they attach to the
   relationship's **auto unknown member**: unlabelled, un-renameable, **unselectable by any positive
   slicer choice**. A matrix reconciles to $0.00; ticking named marketplaces drops **$118,206 YTD
   (11.6%)** with no warning. ⚠ **The orphan is created by the view's relabel, not inherited from the
   fact** — all 4 fact marketplace values are in the dim. ⚠ **Do NOT "just add `Cross-Channel` to the
   dim"** — measured, that dim drives *sales* (Amazon US $81.4M), so a synthetic member pollutes every
   sales slicer model-wide. **Channel must leave the marketplace axis.**
2. **Every Brand/Product pivot of ad spend is 175× wrong.** `Marketing Efficiency` has no relationship
   to `Brand`/`Product` (only Agency + Date) ⇒ 175 rows, **1 distinct value**, grand total on every
   row; rows sum to $496,497,407 against a $2,840,291 truth. **The discriminator that makes this a
   defect and not a query artifact: the Date-dim control PASSES** (3 rows / 3 distinct / sums exactly).
   Keep that sentence next to the finding — without it the objection "isn't that just how DAX works?"
   is open. Only correct brand field = `Marketing Efficiency Product[Brand]`, which appears in the
   field list under the **same display name `Brand`**.
3. **Sponsored Display reads a stale PROD source** — see the four-kinds-of-zero case below.
4. **"Blank, never zero" is decided but NOT implemented.** Not one blank exists: the source column
   emits a literal `0`, and the PBI format string `\$#,0;(\$#,0);\$#,0` has **no 4th (blank) section**,
   so SQL `NULL` alone would still paint `$0`. **Two-part fix — SQL and format string.** 26 of 30
   marketplaces, 23 Meta months, 248 UK days and the LECTRIC agency all assert a false `$0`.
5. **`Margin After Ad Spend (USD)` nets Amazon ONLY** — $244,870 of Google+Meta never deducted, while
   [[navira-metric-dictionary]] line 109 documents it as netting all three. Wrong on the model the CEO
   report reads. Residual **$61.69**, entirely Amazon UK, undecomposed. Stored warehouse column, not DAX.

### ⭐ Four-kinds-of-zero case study: Sponsored Display "died 2026-06-05" — it didn't

| Source | Rows | Cost | Max date |
|---|---:|---:|---|
| **TEST raw** `AMAZON_ADS.CURRENT_SPONSORED_DISPLAY_CAMPAIGN_REPORT` | **9,433** | **$6,485.38** | **2026-08-08** |
| PROD raw (same object) | 942 | $3,374.90 | 2026-06-05 |
| **TEST fact** `MARKETING_FCT_ACTIVITY_UNIFIED` | **942** | **$3,374.90** | **2026-06-05** |

The fact matches **PROD exactly, not TEST** — `_PREPROD` sources SD from `PROD_DG1_GEP.AMAZON_ADS.…`.
⇒ `NOT RECORDED`, **not** `ZERO`. We were one step from telling the client their campaigns had stopped;
they never did. **$3,110.48 invisible**, and Amazon + all-channel totals understated by the same.
**The lesson: a discriminating three-way test (TEST raw / PROD raw / fact) separates a pipeline bug
from a client-behaviour fact. Matching values are not provenance.**

### Other measured facts worth having before any edit
- **The `2024-06-01` date floor appears 5× LIVE**: `MARKETING_EFFICIENCY` L35/51/67, `_MARGIN` L44,
  `_PRODUCT` L66. It cuts **$23,689.66 / 564 rows** of Jan–May-2024 Google from a client-facing figure.
  A fix must touch all five or the layers disagree.
- **Product grain covers 92% of Amazon spend, not ~99%.** `SB US is 88.6% sentinel by spend` — 364 real
  ASINs but only **11.4% ($26,037 of $229,223)** of SB spend carries one. Counting ASINs that *exist*
  ≠ counting spend that *carries* one. Always exclude `PRODUCT_ID = '-1'`.
- **Every object on the marketing path is a secure VIEW, not a table** ⇒ **no ~06:00 Eclipse rebuild
  wait for this family**; a view replace is live immediately, only a PBI refresh is needed. (Contradicts
  the general assumption in [[project_navira_consumer_layer_pipeline]] *for this path only*.)
- **7 of 11 in-scope TEST objects are owned by `ACCOUNTADMIN`** (hand-deployed, not reproducible via the
  Eclipse `CORE_SVC` path); only 4 are `CORE_SVC`-owned.
- **Zero SHARE grants on any in-scope TEST object** — the `COPY GRANTS`/re-grant ceremony applies to
  exactly 2 PROD objects. **But `COPY GRANTS` is still mandatory on TEST**: `NAVIRA_MKT_RO` holds SELECT
  on 3 of them (the client-facing `navira-mktg` dashboard) and a bare `CREATE OR REPLACE` silently 403s
  it while every PBI check still passes.
- **Figures move daily.** Refresh ~14:00 UTC; the all-channel total moved **$3,163** in one day.
  Campaign spend's apparent $2,852 gap vs Snowflake **self-healed to the exact Snowflake value** after
  the next refresh — final-day accrual, not a defect. The *allocated* side is the volatile one
  (+$91,495 in one refresh). **Stamp every figure with the refresh instant.**
- **Visible surface (contract for any "what changes" claim):** 97 measures visible / 164 hidden on
  visible tables / 18 of 35 tables visible. `Marketing Efficiency` = **19 visible / 28 hidden of 47**
  (the "48" in older notes is wrong). A naive `IsHidden=false` count returns 105 and is **wrong** —
  8 unhidden measures are stranded on hidden `Customer` tables. Three visible folders, not two:
  `Spend`, `Contribution Margin`, **`Grounded ROAS`** (on MEP).
- **`executeQueries` redacts `[Expression]`/`[FormatString]`** and rejects `INFO.MEASURES()`
  (`AnalysisServicesErrorCode 3239575574`). Use read-only TOM `JsonSerializer.SerializeDatabase`.
  Do **not** read those NULLs as "no format string".
- **Zero reports render the cross-channel spend measures** — across all 27 enumerable workspaces only 2
  reports bind to `66151728` and neither uses the `Spend` folder. So "show the client what it looks like
  exactly" **cannot be satisfied by pointing at anything today**; an approval surface must be authored.

## Requirement logged 2026-08-09 — cross-**platform** slicing, alongside cross-**channel** (Paul)

Captured during the GP-317/GP-318 Daily-model cross-channel ad-spend design session. **Logged only —
not designed, not scoped, not built.** Recorded here because the Daily model is where it lands.

> Paul, 2026-08-09: *"I mentioned cross-channel, but what we will also want is an option for analysis
> and slicing and reporting cross platform too. This is probably straightforward to add to the model."*

**Read the two words in this estate's local sense — they are not synonyms:**

| Term | Axis | Members | Where it lives today |
|---|---|---|---|
| **cross-channel** | the **ad** side — where marketing money is spent | Amazon Ads (SP/SB/SD) · Google Ads · Meta | `MARKETING_FCT_ACTIVITY_UNIFIED.PLATFORM_ID` → `Marketing Efficiency` |
| **cross-platform** | the **selling** side — where revenue is earned | Amazon US/CA/UK/MX/BR/DE/FR/IT/ES · Shopify stores (Brinno, Cibu, Bigso, ION8, Slobproof, Carry-on, AnySharp) · Bridgford WooCommerce · Walmart · eBay · Target · Wayfair · NewEgg · Best Buy US/CA · Etsy · Reverb · GEP Brands · Wholesale | `SHARED_DIM_MARKETPLACE` → `Marketplace` dim, already joined to `Order Line` |

So this is a **sales-side reporting axis**, not a second ad axis. The dimension and the relationship
**already exist** in the Daily model — which is why Paul's "probably straightforward" read is
plausible. The likely real work is *grouping and legibility*, not plumbing.

**Open design questions when this is picked up (do not answer them from this page):**
1. **Is a platform-GROUP level wanted** (e.g. Amazon / DTC-owned-site / retail-marketplace / wholesale),
   or is slicing on the existing per-marketplace members enough? 25+ raw members is a lot of pie slices;
   a grouping column on `SHARED_DIM_MARKETPLACE` is the cheap version. **Ask Paul before assuming.**
2. **What does ad spend do under a cross-platform slice?** Only Amazon ad spend carries a marketplace.
   Under a *Shopify* or *Walmart* platform slice, Amazon/Google/Meta spend must render **blank, never
   zero** — the same rule the cross-channel design is adopting. Google/Meta own-site-destination spend
   is the one bridge between the two axes, and it rests on a fragile campaign-naming convention.
3. **Which measures are even valid cross-platform?** ⚠ **This is the trap.** [[navira-roadmap-status]]
   gap #3 records it: a user can wrongly **cross-platform `SUM(SALES_AMOUNT)`** — platform-attributed
   sales double-count and must never be summed across platforms; use `ACTUAL_SALES_*`. The **DAX Flag A
   guardrail** was drafted for exactly this (`aldc-launchpad/pbi_ops/navira_dax_flags_A_B.md`) and is
   **still not applied**. Shipping cross-platform slicing without Flag A hands users a correctness
   footgun on the model the CEO report reads. **Treat Flag A as a prerequisite, not a follow-up.**
4. **Coverage honesty per platform.** Several marketplace members currently carry no data at all
   (Mexico, Brazil, and the EU members returned NULL in the 2026-08-09 probe). A platform slicer that
   lists 25 members and populates 6 needs the four-kinds-of-zero treatment
   ([[cross-channel-marketing-attribution]]), or users read "no data" as "no sales".

**Related in-flight work:** the GP-317/GP-318 cross-channel design session (branch
`feature/navira-ad-metrics-request`, boot prompt
`aldc-launchpad/boot-prompts/navira-daily-model-cross-channel-adspend.md`). The two axes should share
one blank-vs-zero rule and one legibility standard, so whoever designs cross-platform should read the
cross-channel design's outcome first rather than inventing a parallel convention.

## Related
[[data-pipeline-flow]] · [[star-schema-convention]] · [[Power BI]] · [[Snowflake]] · [[periodicity]] ·
[[navira-roadmap-status]] · [[project_navira_consumer_layer_pipeline]] · [[project_navira_deployed_truth_parity]] ·
[[cross-channel-marketing-attribution]] · [[GP-291]] · [[GP-292]]
