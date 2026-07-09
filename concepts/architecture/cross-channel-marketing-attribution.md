---
tags: [architecture, marketing, attribution, roas, mer, snowflake, navira, gep, fusion92, schema-design]
aliases: [Cross-Channel Attribution, Marketing Measurement Model, Blended ROAS, MER, True ROAS]
sources: [clients/GEP/snowflake/warehouse/marketing_fct_activity.sql, clients/GEP/snowflake/warehouse/sales_fct_orderline.sql, clients/GEP/snowflake/warehouse/shared_dim_product_base.sql, clients/GEP/snowflake/warehouse/sales_fct_lectric_amazon_orderline.sql]
created: 2026-05-29
updated: 2026-07-09
---

# Cross-Channel Marketing Attribution — Tiered Measurement Model

Design for tying ad spend to **actual orders** as a single source of truth, instead of trusting each platform's self-reported conversion value. Driven by Navira ([[GP-225]]) but the model is reusable for any ALDC client with both ad-spend and sales data (e.g. [[fusion92]]).

## The Problem — platform-attributed value is not truth

Adding the [[Windsor]] revenue fields (`conversions_value`, `action_values_purchase` — see [[GP-225]]) unblocks **per-channel** ROAS. It does **not** give true cross-channel attribution, because platform-reported conversion value has three structural flaws:

1. **Double-counting.** Google and Meta each claim the *same* sale (both fired a pixel on the same converting customer). Summing `conversions_value` across channels exceeds real revenue — often by a lot.
2. **Modeled, not measured.** Each value is attributed by that platform's own pixel/SDK within its own attribution window (Google data-driven, Meta 7d-click/1d-view, Amazon 14d/30d). It is the platform's *estimate* of credit, optimised to flatter the platform.
3. **Doesn't reconcile to orders.** None of it ties to `SALES_FCT_*` — the actual orders ALDC ingests via Amazon SP-API / Sellercloud. You cannot point at a number and say "this is real revenue driven by marketing."

> **Core principle:** keep two clearly-separated layers — **platform-reported** metrics (tactical, for in-channel optimisation) and **ground-truth** metrics (strategic, derived from actual orders). Never let the first masquerade as the second.

## The Tiered Model

| Tier | Metric | Revenue source | Source of truth? | Use |
|---|---|---|---|---|
| **0 — Spend** | spend / clicks / impressions per channel·campaign·product·date | — (measured) | ✅ always | Cost control, pacing |
| **1 — Platform ROAS** | per-channel ROAS = platform conversion value ÷ spend | platform-attributed (Windsor) | ❌ platform-reported; **never sum across channels** | In-channel optimisation — *what GP-225's field fix delivers* |
| **2 — Blended MER** | total spend ÷ **actual revenue** (all channels combined) | `SALES_FCT_*` (real orders) | ✅ top-line truth | Overall marketing efficiency, board-level trend |
| **3 — Product-grounded** | spend on an ASIN/SKU vs **actual sales** of that SKU | `SALES_FCT_*` (real orders) | ✅ grounded, directional | Which products marketing is efficient on |
| **3.5 — Contribution Margin** | gross contribution (net sales − COGS) and margin-after-ad-spend; margin-MER / margin-ROAS | `SALES_FCT_ORDERLINE` COGS | ✅ profit truth (coverage-gated) | Profit, not just revenue — efficiency on margin rather than top-line |
| **4 — Causal / incrementality** | true lift from MMM or geo/holdout tests | experiment / model | ✅ causal (only tier that is) | Budget reallocation between channels — **future, out of schema scope** |

**The source of truth is Tier 2 + Tier 3** — both put **actual orders in the denominator**. Tier 1 stays, clearly labelled "platform-reported," for tactical use.

### Honest caveats (state these on every dashboard)
- **MER over-credits marketing.** Tier 2's denominator includes *organic* sales, so blended ROAS attributes all revenue (incl. non-ad) to spend. Its value is a **consistent top-line trend and an efficiency ceiling**, not channel attribution. A *falling* MER at constant spend is a real warning sign; the absolute number is not "ad-driven revenue."
- **Tier 3 is directional, not causal.** Ad spend on a product on day D ≠ sales of that product on day D (lag, halo, organic baseline). Surface it with a stated attribution-window assumption; it answers "where is marketing money working," not "what would we have sold anyway."
- **Only Tier 4 isolates incremental lift.** Treat it as a separate data-science initiative (MMM / geo holdouts), not a warehouse view. Document it as the eventual answer to "true per-channel causal ROAS" so nobody expects Tiers 1–3 to deliver it.

## Enabling Assets — what exists vs. the gaps

Grounded attribution needs three things joined at a common grain: **actual revenue**, **ad spend**, and a **product/entity bridge**. Most of this already exists for Navira.

| Asset | Exists? | Notes |
|---|---|---|
| **Actual revenue (Navira)** | ✅ | `SALES_FCT_ORDERLINE` — internal-SKU grain, `SALES_GROSS_CONSOLIDATED` already in consolidated currency, `MARKETPLACE`, date. |
| **Actual revenue (agency)** | ✅ (sales) | `SALES_FCT_LECTRIC_AMAZON_ORDERLINE` — `ENTITY_CODE='LECTRIC'`, carries **both ASIN and SELLER_SKU** inline. See [[navira-dwh-data-landing]]. |
| **Ad spend (all channels)** | ✅ | `MARKETING_FCT_ACTIVITY` — 7 branches, grain `PLATFORM·CAMPAIGN·AD_GROUP·PROFILE·PRODUCT_ID·DATE·MARKETPLACE·ENTITY_CODE`. |
| **Tier-1 platform value** | ⏳ | Pending the [[GP-225]] Windsor field fix (Google/Meta currently `SALES_AMOUNT=0`). Amazon branches already carry attributed sales. |
| **ASIN ↔ internal-SKU bridge (Navira)** | ✅ **already built** | `SHARED_DIM_PRODUCT_BASE` maps `PRODUCT.ID` (internal SKU) ↔ `ASIN` / `PARENT_ASIN` / `AMAZON_SKU` / vendor SKUs from the Sellercloud product master. This is the keystone for Tier 3 — and it **already exists** for Navira. (This is the [[GP-225]] Q8 "no ASIN→SKU dimension" worry — true for the *unified ad fact's* `PRODUCT_ID`, but the bridge itself is present in the product dim.) |
| **Entity bridge** | ✅ | `SHARED_DIM_ENTITY` (marketing, account-id map) + landing-schema/`ENTITY_CODE` literal (sales). See [[navira-dwh-data-landing]]. |
| **Reconciliation view (spend ⨝ actual sales)** | ❌ **the real missing piece** | No view joins `MARKETING_FCT_ACTIVITY` to `SALES_FCT_*`. This is what Tiers 2–3 need built. |
| **Agency product dim** | ❌ gap | Agency customers' ASINs/SKUs aren't in Navira's Sellercloud master; their ASIN↔SKU is only inline in their all-orders report. A per-entity product dim (derived from the orders/catalog report) is needed for agency Tier 3. |
| **Spend currency consolidation** | ⚠️ partial | Spend is in platform/account currency; revenue is already consolidated (`SALES_GROSS_CONSOLIDATED` via `CONSOLIDATED_RATE`). Spend must be converted to the same reporting currency before ratios are valid — reuse the existing consolidated-rate / FX rates mechanism. |

## Channel Groundability Matrix

How far up the tiers each channel can go depends on whether ad rows carry a product key that joins to real sales.

| Channel | Product key on ad row | Max grounded tier | Why |
|---|---|---|---|
| **Amazon SB** | ASIN (via GP-199 ASIN map) | **Tier 3** | ASIN → `SHARED_DIM_PRODUCT_BASE` → SKU → `SALES_FCT_*`. See [[GP-199]]. |
| **Amazon SP** | `ADVERTISEDSKU` | **Tier 3** | SKU joins directly to sales. |
| **Amazon SD** | ASIN | **Tier 3** | As SB. |
| **Google** | none in landed fact (`PRODUCT_ID='-1'`); Windsor *can* expose `product_item_id`/`offer_id` for PMax+Shopping (~61% of spend) | **Tier ~2.7 (brand-grounded) today; Tier 3 blocked** | See "Google grounding — evidence" below. offer_ids are **Shopify Merchant-Center ids** (`shopify_us_<pid>_<vid>`) that do **not** join to `SHARED_DIM_PRODUCT_BASE` (direct SKU bridge = **6%**). Brand-grounded ROAS vs Websites-channel sales is built + validated; per-SKU needs a Shopify variant-id→SKU crosswalk. |
| **Meta** | **`product_id` DOES return per-product rows** (`<variant_id>, <name>`), like Google; $8,158 total spend | **Tier ~2.7 / Tier 3 feasible — but ROI-gated** | Same shape as Google (Shopify variant ids; model in the name). Both brand- and per-SKU grounding repeat via the **same channel-agnostic crosswalk**. NOT pursued as its own effort — folds in nearly free once Google is built. Spend is the gate, not data. *(corrected 2026-06-09 — earlier "no per-product id" was a field-catalog scan miss; the live pull shows `product_id` populates.)* |

=> **Amazon is fully groundable today** (revenue + product bridge both exist). **Google is now BRAND-grounded** (Phase 2a, 2026-06-09 — validated penny-exact at the DAX layer) for the Websites/DTC destination; **per-SKU Google grounding (Tier 3) is blocked on a Shopify-id→SKU crosswalk** (Phase 2b — title-model derivation reaches ~80% in a spike). **Meta supports BOTH approaches via the same channel-agnostic crosswalk** but is ROI-gated ($8,158 spend) — it rides along with the Google build rather than being its own effort.

### Google grounding — evidence (2026-06-09, sandbox `WAREHOUSE_TEST_GP226`)
Read-only probes established (scripts in `aldc-launchpad/warehouse_ops/_windsor_product_grounding_probe.py`, `_google_bridge_matchrate.py`, `_google_brand_crosswalk_build.py`):
- **Coverage:** PMax $114K + Shopping $8.6K ≈ 61% of Google spend is product-capable; the rest (Search/Display/Demand-Gen) carries no product.
- **Adding the product breakdown changes the spend total** ($349→$261/day) — a product pull is **not** a clean superset of the campaign pull, so grounding must be a *separate reconciled branch*, never a replacement for the campaign fact.
- **Bridge blocker:** PMax/Shopping `offer_id`s are Shopify feed ids (`shopify_us_8981760409788_45208025530556`, brand in `product_title` only). Direct `offer_id → SHARED_DIM_PRODUCT_BASE` join = **5.8–6.2%** of product spend (only Bridgford `bfw_ka_*` ≈ Websites `PRODUCT_ID`). The other ~94% (Brinno, Slobproof — the biggest spenders) have **no warehouse SKU** → a **data-acquisition gap**, not a SQL gap.
- **What works today — brand × destination:** campaign names cleanly carry brand + destination (`Shopify - PMax - Brinno BCC300` → Websites; `Amazon - Brinno_B0…` → Amazon). Brand bridges to `SHARED_DIM_PRODUCT_BASE.BRAND` and to Websites-channel sales. **Amazon-destination Google spend is NOT grounded** (Google is a rounding-error driver of Amazon sales — grounding it against total Amazon brand sales gave absurd 1500–6800x ROAS); it's kept spend-only. ~44% of Google spend is brand-grounded; the remainder is honestly bucketed (multi-brand / amazon-dest / no-brand).
- **Validated grounded ROAS (Websites):** Brinno 13.2x · Bridgford 11.1x · Bigso 8.4x · Cibu 22.7x · Slobproof 1.3x. Spend reconciles to the fact ($179,086.92) to the penny; grounded sales reconcile to `SALES_FCT_ORDERLINE` Websites cells to the penny; DAX == warehouse to 2dp.

#### Why only ~44% grounds at brand level (full spend breakdown, 2026-06-09)
| Reason | Spend | % | Recoverable? |
|---|---|---|---|
| **Grounded** (brand-scoped + has Websites sales) | $79,523 | 44% | ✅ done |
| **Multi-brand catch-all campaigns** (`Remaining Products`, `Top 8`, `All Products`, `Generic`) | $73,968 | 41% | only via **per-SKU** — these advertise the whole catalog, not one brand |
| **Amazon-destination** (branded search → Amazon) | $14,361 | 8% | ✗ excluded by design (Google ≠ Amazon driver; gave 1500–6800x) |
| **No brand signal** in campaign name | $11,235 | 6% | partially (more seed tokens / land `product_brand`) |

Key: **$50,708 (28% of all Google spend) sits in multi-brand campaigns that ARE PMax/Shopping** — i.e. they carry `product_item_id`. Brand-level can't split them, but **per-SKU grounding (Phase 2b) can** — that's the real unlock, not better parsing. Conversely, $23,803 of the *grounded* total is branded **Search** (no product feed, clear brand in name) — which per-SKU never catches. The two methods are complementary.

## Proposed Build — `REPORT_COMMON.MARKETING_EFFICIENCY`

A reconciliation view (not a new ingest) that LEFT-JOINs aggregated spend to aggregated actual sales:

- **Spine grain:** `ENTITY_CODE × MARKETPLACE × ACTIVITY_DATE` (Tier 2). Add `PRODUCT_KEY` (via the bridge) for the Amazon product-level slice (Tier 3); Google/Meta contribute only to the no-product spine.
- **Columns:** `SPEND_CONSOLIDATED`, `PLATFORM_ATTRIBUTED_VALUE` (Tier 1, labelled, per-platform, never summed), `ACTUAL_SALES_CONSOLIDATED` (from `SALES_FCT_*`), `BLENDED_ROAS = ACTUAL_SALES / SPEND`, `MER = SPEND / ACTUAL_SALES`.
- **Currency:** consolidate spend to the reporting currency using the existing `CONSOLIDATED_RATE` / FX rates before computing ratios; preserve original-currency columns (currency-triple convention, [[star-schema-convention]]).
- **Multi-tenant:** every row tagged `ENTITY_CODE`; isolation test must assert no foreign `ACCOUNT_ID`/ASIN bleeds across entities (the [[project_windsor_fusion92_filter|cross-client filter]] risk is amplified here — cross-tenant leakage is the catastrophic-failure mode for [[phase-1c-sales-agency-customers|Phase 1C]]).

## Decisions

1. **Headline truth metric** — ✅ **DECIDED 2026-05-29 (Paul): adopt blended MER** as the board-level "marketing efficiency" number, surfaced with the over-credit caveat (denominator includes organic; it's a trend/ceiling, not channel attribution).
2. **Google/Meta product linkage** — ✅ **DECIDED 2026-05-29 (Paul): defer, but PLAN to integrate.** Google/Meta stay blended-only initially; lift after Phase 1 proven. **UPDATE 2026-06-09 (Paul): build brand-grounded Google now (Phase 2a, DONE), sandbox-first.** Evidence (above) showed per-SKU Google grounding covers only 6% by direct join (Shopify offer_ids carry no warehouse SKU) → the achievable deliverable is **brand × destination-channel** grounding, validated penny-exact. Per-SKU (Phase 2b) is filed but **gated on a Shopify variant-id→SKU crosswalk**. Meta dropped (no product id + negligible spend). The original "UTM click→order" framing was heavier than needed — the brand path reuses the existing `SHARED_DIM_PRODUCT_BASE.BRAND` bridge with no new tracking infra.
3. **Reporting currency** — ✅ **DECIDED 2026-05-29 (Paul): USD** as the consolidation target (matches `SALES_GROSS_CONSOLIDATED`). All spend converted to USD via `CONSOLIDATED_RATE` before computing ratios; original-currency columns preserved.
4. **Amazon headline attribution window** — ✅ **DECIDED 2026-05-29 (Paul): keep 30-day**, matching the current Snowflake warehouse design (prod `MARKETING_FCT_ACTIVITY` already surfaces the `*30D` window columns). Revisit only if Navira requests a different window. *(Carried from [[GP-225]] Q3.)*

## Phased Rollout

| Phase | Scope | Tiers delivered | Gate |
|---|---|---|---|
| **1 — Initial (prove it)** | `REPORT_COMMON.MARKETING_EFFICIENCY`: all-channel **blended MER** (Tier 2) + **Amazon product-grounded** (Tier 3, via the existing `SHARED_DIM_PRODUCT_BASE` bridge). Google/Meta contribute spend + Tier-1 value + blended only. | T1 (via [[GP-225]]) · **T2 all-channel** · **T3 Amazon** | — |
| **2a — Google brand-grounded** ✅ DONE 2026-06-09 | `MARKETING_EFFICIENCY_GOOGLE_BRAND` (sandbox): Google PMax/Shopping spend × **brand** grounded to actual Websites-channel sales. Seed (`navira_google_brand_seed.sql`) + live resolution view + grounding view; wired into PBI sandbox + DAX-validated. | **Tier ~2.7 Google (brand)** | Phase 1 proven ✓ |
| **1.5 — Contribution Margin** ✅ BUILT/live TEST 2026-06-12 | `REPORT_COMMON.MARKETING_EFFICIENCY_MARGIN` (additive column-superset of `MARKETING_EFFICIENCY` adding COGS/margin) + PBI measures `Contribution Margin (USD)`, `Margin After Ad Spend (USD)`, `Margin ROAS`, `Contribution Margin %`, `COGS Coverage %`. Headline = gross contribution (net − COGS); margin-after-ad-spend = gross contribution − Windsor spend (double-count-safe, since fully-loaded `MARGIN_NET_CONSOLIDATED` already nets ad fees — exposed only as a labelled reference). COGS from `SALES_FCT_ORDERLINE` (no new connector). DAX==SQL validated, zero regression. **Coverage ~83%** of recent NAVIRA lines (0% pre-May-2024; agency=0) — surfaced via `COGS Coverage %`; lifts when the GP-259 Option-A backfill lands. | **Tier 3.5** | Phase 1 proven ✓ |
| **2b — Google per-SKU** ✅ BUILT in sandbox 2026-06-09 | True product (SKU) grounding via a **`product_title`→SKU title-model crosswalk** (the Shopify-feed connector turned out unnecessary): `MARKETING_GOOGLE_PRODUCT_SPEND` (materialized) + `MARKETING_GOOGLE_OFFER_SKU` (resolution view, locked logic in SQL) + `MARKETING_EFFICIENCY_GOOGLE_PRODUCT` (SKU-grain); PBI-wired + DAX-validated. **81% of product-grain spend resolves** (validated 100% brand-consistent, 227/227); remaining 19% (Bigso `V####`, Slobproof) is a surfaced `(UNRESOLVED)` bucket needing a curated map or Shopify feed. | **Tier 3 Google (81%)** | Phase 1 + 2a proven ✓ |
| **2c — Meta** | Deferred — connector exposes no per-product id and Meta spend is negligible ($6,667). | — | Not pursued. |
| **3 — Causal (optional, later)** | MMM / geo-holdout incrementality. Separate data-science initiative (Python job → `REPORT_COMMON.MARKETING_INCREMENTALITY`), not a warehouse view. **Method DECIDED 2026-06-12 (deep-research): PyMC-Marketing** (Bayesian; Meridian fallback) on `MARKETING_MMM_INPUT`; minimum-defensible spec only (Amazon+Google already have ~105 wks each; Meta excluded). ~105 wks × 2 channels is "small-sample" (Jin 2017) → prior-dominated, report with credible intervals, **observational not causal** until a geo-holdout lift test calibrates it. See `aldc-launchpad/warehouse_ops/tier4-methodology.md`. | T4 | Business demand. |

## PROD promotion gate (efficiency + Contribution-Margin stack)

The full marketing-efficiency + Contribution-Margin (Tier 3.5) stack is live in **TEST only**
(`TEST_DG1_GEP.REPORT_COMMON.*`, GEP Test Models "Data Model" `66151728`). The PROD repoint
(onto `PROD_DG1_GEP` / `GEP Prod Models`) is **deliberately deferred** and gated on BOTH of the
following — the trigger is the conditions, not a date:

1. **Client (GEP/Navira) review + sign-off of the design in TEST** — the new measures, the
   gross-contribution definition, and the coverage caveat. Any requested change to the margin
   basis (gross vs. fully-loaded, headline metric) is made + re-validated in TEST first; PROD
   inherits only an *accepted* design. (GP-277 sits in QA / client-review for exactly this.)
2. **COGS coverage is trustworthy** — the GP-259 **Option-A catalog backfill has landed** (or
   PROD launches with `COGS Coverage %` extremely prominent). At ~83% coverage, PROD margin
   would show execs *overstated* margin on the ~17% of no-COGS lines — the precise
   "numbers don't match my spreadsheet" failure mode. See
   `aldc-launchpad/boot-prompts/navira-gp259-cogs-backfill-optionA.md`.

Until both hold, TEST is the correct home.

## Two-Model Architecture + Channel-Attributed Margin (2026-07-08, Navira)

Driven by a Lori↔Heather review: Heather's hard constraint is **"do not change the daily Data Model my
team uses"** (new fields/relationships in her daily model = a hard no; she wants to just pick Agency and
have everything else unchanged). Decision (Paul + Lori):

- **Model-naming convention (2026-07-09):** environment is conveyed by the **workspace** (`GEP Test Models` /
  `GEP Prod Models`), NOT the dataset name — so datasets carry no `(Test)`/`(Prod)` suffix (matches how
  `Data Model` already works). The pair is **`Data Model`** (daily/sales — left *exactly* as-is; renaming it
  would break Heather's "nothing changed" promise) + **`Marketing Model`** (the sibling). The dataset was
  renamed from `Navira Marketing Model (Test)` → `Marketing Model` on 2026-07-09 (Fabric item rename; id
  `2d8587b5` unchanged); the two bound reports were re-deployed with `initial catalog=Marketing Model`, the
  workbook binds by ID so was unaffected.
- **Two-model architecture.** Leave the **daily `Data Model`** (PROD, Amazon-scoped, familiar) untouched.
  Stand up a **separate `Marketing Model`** (GEP Test Models, dataset id `2d8587b5`) as a
  sibling — it holds Agency, Google/Meta, cross-channel, and the ad-spend-inclusive margin. Split rule:
  *a feature goes in the marketing model iff it adds a relationship/dim to the star* (Agency dim,
  Google/Meta platform/campaign, marketing→marketplace attribution). Purely additive-to-the-Amazon-star
  features (UK marketplace, ASIN attribution) may stay in the daily model. The loaded TEST model
  `66151728` is the prototype of the marketing model; **PROD daily model is never repointed**.
  - ⚠ **Evidence correction (2026-07-08, empirical probe of all 3 models — `INFO.VIEW.TABLES()` +
    measure-resolution).** PROD daily (`74a529b3`) is **not** zero-new-tables as first assumed. It
    *already contains* **MAP Violators** (all 3 tables, visible — **757 sellers / 20.6% rate live in
    PROD**) and the **`Marketing Activity` fact + `Campaign`/`Platform` dims** (Amazon ASIN attribution:
    **Ad Sales $12.55M / Ad Cost $2.44M resolve in PROD**). These were already there and don't add a
    cross-channel relationship → they correctly belong to the **daily** model. PROD genuinely **lacks**
    (marketing-model-only): `Agency`, `Marketing Efficiency` (+Product), `Marketing Platform Detail`,
    `Creative` (+Placement), `Google Ad Spend (Dest)` + margin, Google Grounding, Customer Cohort. So
    **no destructive migration is needed** — the daily model never gained the relationship-heavy features.
    Net: the split is *already real at the model level*; the showcase just had to **label** it correctly.
- **Margin including Google/Meta ad spend** (Heather asked for Google spend as a *separate margin column,
  marketplace-specific*). Finding: **neither existing margin netted Google/Meta** — `Margin After Ad Spend`
  = Contribution Margin − *Amazon* spend only (the $219K Google+Meta "Cross-Channel" bucket was undeducted).
  - **Option B (blended, shipped):** `Margin incl. Ad Spend (USD)` = `Margin After Ad Spend` − (Google+Meta),
    total grain. The seam measure `G/M Ad Spend (in Margin)` is the B→C swap point.
  - **Option C1 (Google channel-attributed, shipped):** warehouse view
    `WAREHOUSE_TEST_GP226.MARKETING_GOOGLE_SPEND_BY_DEST` (deduped campaign→`DESTINATION_CHANNEL` crosswalk ⨝
    Google fact, `ACTIVITY_DATE>='2024-06-01'`) → reconciles to `Spend - Google` to the penny (Amazon
    $53,520 / Websites $151,075). Wired into the marketing model as table `Google Ad Spend (Dest)` + the
    seam redefined to read it → `Margin incl. Ad Spend - Amazon` / `- Websites` slice by channel; blended
    total unchanged.
  - **Attribution grain = CHANNEL (Amazon vs Websites), by design.** This *aligns with the existing Amazon
    convention*: attribute ad spend to the finest marketplace the **source** identifies. Amazon reaches
    specific marketplace (US/CA/UK) only because Amazon ad data is marketplace-tagged; Google/Meta data only
    carries destination *channel* (via campaign-name classification), so channel is the honest max. Per-
    specific-marketplace would *invent* a US/CA split Amazon never had to.
  - **C3 (Meta) UNBLOCKED (2026-07-08) — was "no name source found".** Source = **`META.CURRENT_FACEBOOK_AD_INSIGHTS`**
    (`CAMPAIGN_ID`, `CAMPAIGN` name, `ADSET_NAME`) — the direct analog of Google's `GOOGLE_ADS.CURRENT_GOOGLE_ADS_CAMPAIGN`.
    Join: fact `CAMPAIGN_ID` = `'META_'||raw.CAMPAIGN_ID`. All **13** Meta campaigns ($14,668) use an **"M2W"
    (Meta-to-Web)** convention (`M2W_US_CIBU_SALES`, `..._WebVisitors`, `..._ATC/IC`, `Retargeting_Catalog`)
    with **zero Amazon signal → all classify to Websites** (Brinno/Cibu Shopify traffic). Build recipe (mirror
    C1): `MARKETING_META_SPEND_BY_DEST` + a Meta-by-dest measure family → net Meta into `Margin incl. Ad Spend
    - Websites` (blended total unchanged; only the Amazon/Websites split shifts −$14,668 → Websites).
    ✅ **SHIPPED 2026-07-08** (view `_marketing_meta_spend_by_dest.sql` + `_marketing_model_C3_wire.py`).
    Gates PASS: view reconciles $14,668.24, 100% Websites; DAX-validated blended $37,080,620 UNCHANGED,
    Amazon $36,008,358 UNCHANGED, Websites $376,458→$361,789. Live 66151728 untouched. Underlying Meta
    *numbers* still gated on Nicholas before PROD promotion.
- **Surfaced:** report `Navira - Cross-Channel Margin` (GEP Test Models, bound to the marketing model).
- **Currency rule reinforced** (see [[star-schema-convention]] Currency Triple Pattern): the destination
  view only reconciles because Google is USD-native and it applied the efficiency view's exact date filter;
  any new ad source must land USD before feeding margin. Open item: standardize model-wide USD-at-ingestion.
- **Showcase reframe SHIPPED (2026-07-08).** The "New Data Showcase" was rebuilt to the two-model story
  (was "everything in one model, bound to live 66151728"):
  - **xlsx workbook** (`pbi_ops/demo/_build_demo_workbook.py`) — **Section A (daily model)**: A1 UK Orders ·
    A2 ASIN · A3 UK Ad Spend · A4 MAP; **Section B (Marketing Model)**: B1 Blended · B2 Google+Meta ·
    B3 Agency/Lectric · B4 **Margin by Channel (NEW)**. Evidence-based binding: ASIN + MAP pull live from
    **PROD 74a529b3** ("live in production"); UK tabs House-scoped from the marketing model with a
    "deploying to production (#490)" badge (PROD's UK is only partially backfilled — $141.8K + zero UK ad
    spend, vs full $307.6K + $2,982 in the marketing model).
  - **Native PBI report** `Navira — New Data Showcase` (`_build_navira_showcase_report.py`, report id
    `c194abf5`) — rebound to the marketing model (one dataset can't split PROD+MKTG, and Margin-by-Channel
    needs the marketing model), 9 pages, two-section nav + per-page "Lives in" badges + Margin-by-Channel page.
  - Talking points / walkthrough script / onepager(+PDF) rewritten to the two-model spine.
  - Live `66151728` confirmed **untouched (44 tables)** throughout.
- **PROD promotion** of the marketing model is gated on **Nicholas** (Google/Meta validation, YTD) +
  **Heather** (Lectric sales). Open: Paul to eyeball both PBI reports + publish the workbook to Eclipse
  app_report 57. Build/rollback scripts: `aldc-launchpad/pbi_ops/_build_xchannel_demo_clone.py` (variant
  `marketing`), `_marketing_model_margin_B.py`, `_marketing_model_C1_wire.py`,
  `_build_marketing_margin_report.py`; full record in `aldc-launchpad/pbi_ops/navira_heather_requirements_and_plan.md`.
  ⚠ Latent tooling bug to fix: `pbi_ops/xmla.py` `XmlaClient._get_model()` returns `Databases[0]`
  (ignores Initial Catalog) — select the target DB by name via TOM.

## Implications for Tickets

- **[[GP-225]]** delivers **Tier 1 only** (per-channel ROAS via the Windsor field fix). It does *not* close the cross-channel-truth gap — that's this design.
- **New ticket (Phase 1):** build `REPORT_COMMON.MARKETING_EFFICIENCY` — all-channel blended MER (Tier 2) + Amazon product-grounding (Tier 3) via the existing bridge, spend⨝actual-sales reconciliation + currency consolidation. This is the real "true ROAS" deliverable and the design to **prove first**.
- **Phase 2a (DONE 2026-06-09):** Google **brand × destination-channel** grounding — `MARKETING_EFFICIENCY_GOOGLE_BRAND` + seed + resolution view in sandbox; PBI-wired + DAX-validated. Rides the next sandbox→live-TEST cutover (not folded into the current GP-199 cutover).
- **Follow-on ticket (Phase 2b, gated):** Google **per-SKU** grounding — needs a **Shopify variant-id→internal-SKU crosswalk** (the ~94% of PMax/Shopping spend whose `offer_id` is an opaque Shopify composite). Build a Shopify/Merchant-Center product-feed source (deterministic) or a curated `product_title`→SKU map (fuzzy). Not started until the crosswalk source exists. *(navira-roadmap)*
- **Agency ([[phase-1c-sales-agency-customers]]):** same model per `ENTITY_CODE`. Agency Amazon Ads → Tier 3 once a per-entity product dim is derived from their orders/catalog; until then Tier 2. Each new tenant inherits the model with zero per-tenant schema work beyond its product dim.
- **GP-199** already supplies the Amazon-SB ASIN key that Tier 3 joins on — no rework.

## Calibrated ROAS — capped vs uncapped (OPEN client decision, surfaced 2026-06-05)

Tier 2.5 Calibrated ROAS rescales platform-attributed value by a **calibration factor** (`actual revenue ÷ Σ platform-attributed`) so channels reconcile to real revenue. Two definitions exist and **diverge hard for Navira** (factor ≈ 6.4 — platforms collectively *under*-claim, organic-heavy):

- **Uncapped** (total-grain; the Sandbox measure): factor applied as-is → Amazon 32.5x / Google 18.0x / Meta 6.4x. The directional **channel-mix** signal.
- **Capped** (`LEAST(1, factor)` per month; warehouse `MARKETING_EFFICIENCY_MONTHLY`): never over-claims → for Navira the cap is **inert** and Calibrated ROAS collapses to Platform ROAS (5.05 / 2.80 / 0.99x).

Both are now built in the Sandbox model (capped DAX verified == the `_MONTHLY` view to 4 dp). **Recommendation:** default the dashboard to **uncapped** (only it adds channel-mix insight) with the directional caveat; keep capped as a conservative cross-check. Decision belongs to Navira.

> **Build reference for dashboards:** `aldc-launchpad/pbi_ops/navira_marketing_data_dictionary.md` — the elite grounding doc (object dictionary, grain, caveats, measure list, dashboard recipes). Team builds on the `GP225 Test Model Preview` Sandbox model / the `WAREHOUSE_TEST_GP226_TEAM` schema snapshot.

## See Also

- [[GP-225]] — unified marketing schema; delivers Tier 1 (the Windsor revenue-field fix)
- [[GP-199]] — Amazon SB ASIN attribution (supplies the product key for Tier 3)
- [[Windsor]] — verified conversion-value field names + row-split gotcha
- [[navira-data-dictionary-phase1a]] — platform-value-≠-revenue caveat at field level
- [[navira-dwh-data-landing]] — sales/marketing entity segmentation, agency model
- [[phase-1c-sales-agency-customers]] — agency multi-tenant context
- [[star-schema-convention]] — SHA2 keys, currency-triple convention (FX consolidation via `CONSOLIDATED_RATE`)
