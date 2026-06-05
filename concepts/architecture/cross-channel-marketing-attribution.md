---
tags: [architecture, marketing, attribution, roas, mer, snowflake, navira, gep, fusion92, schema-design]
aliases: [Cross-Channel Attribution, Marketing Measurement Model, Blended ROAS, MER, True ROAS]
sources: [clients/GEP/snowflake/warehouse/marketing_fct_activity.sql, clients/GEP/snowflake/warehouse/sales_fct_orderline.sql, clients/GEP/snowflake/warehouse/shared_dim_product_base.sql, clients/GEP/snowflake/warehouse/sales_fct_lectric_amazon_orderline.sql]
created: 2026-05-29
updated: 2026-05-29
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
| **Google** | none (`PRODUCT_ID='-1'`) | **Tier 2 only** | No SKU linkage until UTM/landing-page → order tracking is built. |
| **Meta** | none (`PRODUCT_ID='-1'`) | **Tier 2 only** | No SKU linkage until catalog/CAPI order-id mapping is built. |

=> **Amazon is fully groundable today** (revenue + product bridge both exist). **Google/Meta are blended-only** until product-level click→order linkage is built (UTM for Google, catalog/CAPI for Meta) — a later, substantial extension.

## Proposed Build — `REPORT_COMMON.MARKETING_EFFICIENCY`

A reconciliation view (not a new ingest) that LEFT-JOINs aggregated spend to aggregated actual sales:

- **Spine grain:** `ENTITY_CODE × MARKETPLACE × ACTIVITY_DATE` (Tier 2). Add `PRODUCT_KEY` (via the bridge) for the Amazon product-level slice (Tier 3); Google/Meta contribute only to the no-product spine.
- **Columns:** `SPEND_CONSOLIDATED`, `PLATFORM_ATTRIBUTED_VALUE` (Tier 1, labelled, per-platform, never summed), `ACTUAL_SALES_CONSOLIDATED` (from `SALES_FCT_*`), `BLENDED_ROAS = ACTUAL_SALES / SPEND`, `MER = SPEND / ACTUAL_SALES`.
- **Currency:** consolidate spend to the reporting currency using the existing `CONSOLIDATED_RATE` / FX rates before computing ratios; preserve original-currency columns (currency-triple convention, [[star-schema-convention]]).
- **Multi-tenant:** every row tagged `ENTITY_CODE`; isolation test must assert no foreign `ACCOUNT_ID`/ASIN bleeds across entities (the [[project_windsor_fusion92_filter|cross-client filter]] risk is amplified here — cross-tenant leakage is the catastrophic-failure mode for [[phase-1c-sales-agency-customers|Phase 1C]]).

## Decisions

1. **Headline truth metric** — ✅ **DECIDED 2026-05-29 (Paul): adopt blended MER** as the board-level "marketing efficiency" number, surfaced with the over-credit caveat (denominator includes organic; it's a trend/ceiling, not channel attribution).
2. **Google/Meta product linkage** — ✅ **DECIDED 2026-05-29 (Paul): defer, but PLAN to integrate.** Google/Meta stay **blended-only (Tier 2)** in the initial build. Lifting them to Tier 3 (UTM click→order for Google; catalog/CAPI order-id for Meta) is a **planned follow-on phase**, sequenced *after* the initial design (Phase 1 below) is implemented and proven — not abandoned. See Phased Rollout.
3. **Reporting currency** — ✅ **DECIDED 2026-05-29 (Paul): USD** as the consolidation target (matches `SALES_GROSS_CONSOLIDATED`). All spend converted to USD via `CONSOLIDATED_RATE` before computing ratios; original-currency columns preserved.
4. **Amazon headline attribution window** — ✅ **DECIDED 2026-05-29 (Paul): keep 30-day**, matching the current Snowflake warehouse design (prod `MARKETING_FCT_ACTIVITY` already surfaces the `*30D` window columns). Revisit only if Navira requests a different window. *(Carried from [[GP-225]] Q3.)*

## Phased Rollout

| Phase | Scope | Tiers delivered | Gate |
|---|---|---|---|
| **1 — Initial (prove it)** | `REPORT_COMMON.MARKETING_EFFICIENCY`: all-channel **blended MER** (Tier 2) + **Amazon product-grounded** (Tier 3, via the existing `SHARED_DIM_PRODUCT_BASE` bridge). Google/Meta contribute spend + Tier-1 value + blended only. | T1 (via [[GP-225]]) · **T2 all-channel** · **T3 Amazon** | — |
| **2 — Google/Meta product linkage** | UTM landing→order mapping (Google) + catalog/CAPI order-id mapping (Meta) to lift those channels to product-grounded. | **T3 Google/Meta** | **Only after Phase 1 implemented & proven** (decision 2). |
| **3 — Causal (optional, later)** | MMM / geo-holdout incrementality. Separate data-science initiative, not a warehouse view. | T4 | Business demand. |

## Implications for Tickets

- **[[GP-225]]** delivers **Tier 1 only** (per-channel ROAS via the Windsor field fix). It does *not* close the cross-channel-truth gap — that's this design.
- **New ticket (Phase 1):** build `REPORT_COMMON.MARKETING_EFFICIENCY` — all-channel blended MER (Tier 2) + Amazon product-grounding (Tier 3) via the existing bridge, spend⨝actual-sales reconciliation + currency consolidation. This is the real "true ROAS" deliverable and the design to **prove first**.
- **Follow-on ticket (Phase 2, gated):** Google/Meta product linkage (UTM + catalog/CAPI) — filed but **not started until Phase 1 is proven** (decision 2).
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
