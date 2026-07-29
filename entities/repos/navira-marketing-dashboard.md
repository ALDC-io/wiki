---
tags: [repo, gep, navira, dashboard, insite, marketing, advertising, nextjs, vercel, snowflake]
aliases: [navira-marketing-dashboard, GEP InSite, InSite, navira-mktg, insite-prototype]
sources: []
created: 2026-07-09
updated: 2026-07-19
---

# navira-marketing-dashboard (GEP InSite)

ALDC-built **Next.js 16 (App Router) / React** advertising-analytics dashboard for [[GEP]]/Navira — "**GEP InSite — Advertising Analytics**". Repo: `github.com/ALDC-io/navira-marketing-dashboard`. Local: `C:\Users\PaulRussell\repos\navira-marketing-dashboard`. Prod: **https://navira-mktg.analyticlabs.io** (Vercel project `navira-marketing-dashboard` under the **ALDC** team; behind HTTP Basic Auth). Not to be confused with [[concept-gep-data]] (the "SKU Profitability" concept app) or the Datavize `navira-demo`.

## Architecture
- **Data provider seam** (`src/lib/data/provider.ts`): `SyntheticProvider` (default demo data) vs `WarehouseProvider` (`src/lib/data/providers/warehouse.ts`, real Snowflake). Selected by env `DATA_SOURCE=warehouse`.
- **Reads Snowflake `TEST_DG1_GEP.WAREHOUSE_TEST_GP226`** (the canonical, Lectric-fixed, UK-folded TEST slice — see [[GP-225]]/[[project_gp226_roadmap_gap]]). Objects consumed: `MARKETING_EFFICIENCY` (+`_MONTHLY`, `_PRODUCT`), `MARKETING_FCT_ACTIVITY_UNIFIED`, and `REPORT_COMMON.MARKETING_DIM_AGENCY` (agency display names).
- **Prod Snowflake identity**: user `NAVIRA_MKT_APP`, role **`NAVIRA_MKT_RO`** (read-only, key-pair auth), warehouse `COMPUTE_WH`. NOT ACCOUNTADMIN.
- **Views**: Brand · Product · Campaign · **Ad Platform** · Trends (URL `?view=`). Filters live in the URL (`?entity`/`brand`/`platform`/`q`/`match`/`range`), shareable deep links. All money is USD-consolidated in the warehouse ([[transaction_currency_handling]]); the scorecard leads with **MER + Marketing Cost %** on real data (never a blended cross-channel Ad Sales/ROAS headline — the "Flag A" guard).
- **Two entities today**: Navira (role HOUSE) + Lectric (role AGENCY, sales-only, no ad spend). Model: *Navira is the house; its client companies are "agencies"* — dimension `REPORT_COMMON.MARKETING_DIM_AGENCY` (`ENTITY_CODE, AGENCY, ENTITY_ROLE`).

## 2026-07-09 — first-look deploy + feature/fix session
Branch `feature/insite-calendar-brand-reach-region` (pushed; ~14 commits). Deployed to prod for a client first look. Green: tsc + eslint(max-warnings 0) + **265 unit tests**; prod verified `GET / 200`.

**Features shipped:**
- **Ad Platform tab = one unified table at (platform × region) grain.** Amazon split by marketplace (US/CA/UK/MX/BR) + Google→Amazon + Meta→Amazon as cross-channel rows. Full column set: Agency, Platform, Region, Campaigns, Ad Spend, Ad Sales, Conversions, ROAS, Actual/Net Sales, Orders, Units, TACoS, MER, AOV, Clicks, Impressions, Avg CPC, CTR. (Replaced the earlier separate by-channel + by-region tables; the standalone Region tab was folded in and removed.)
- **Per-region Amazon UK ad spend now visible** ($3,968 USD / 2,651 clicks / £2,982 FX-consolidated) — previously hidden inside the Amazon channel rollup. Reach (clicks/impr) joined from `MARKETING_FCT_ACTIVITY_UNIFIED` by marketplace; reconciles to the channel total (2,631,012 Amazon clicks).
- **Brand/product ad reach** (Clicks/Impressions/CPC/CTR) populated — sourced from the new `MARKETING_EFFICIENCY_PRODUCT.CLICKS/IMPRESSIONS` (SKU→ASIN-bridged; 2.48M clicks). Previously hardcoded 0.
- **Calendar date picker** — native From/To `<input type=date>` replacing the preset dropdown; custom window round-trips through `?range=YYYY-MM-DD~YYYY-MM-DD` (open-ended either side); `parseDateRange` validates real calendar days + rejects injection; server-side SQL predicate on `ACTIVITY_DATE`.
- **Agency column** (dimension-sourced: Navira / Lectric / future agencies) — replaces the generic "Agency" label; scales as agencies are added. Distinguishes the two Amazon-US rows (Navira $74.76M vs Lectric $2.52M).
- **Agency (sales-only entity) no longer dead-ends** — its marketplace sales show on Ad Platform + Trends; empty states point there instead of "select Navira".

**Fixes (found on review):**
- Campaign scorecard no longer blends native-currency, cross-channel money (Flag A) — warehouse campaign scorecard shows currency-free cards only; the per-row table keeps native figures with a caveat.
- No-spend guard: spend-derived ratios (ROAS/MER/TACoS/CPC) render "—" not a misleading "0.0x" (fixes the Agency scorecard).
- Product view drops the "Conv. Rate: TBD" column in warehouse mode (matches Campaign/Platform).
- Trends default columns add Entity (the monthly series carries both entities) + spendMeta.
- **Clear filters + all filters reliably re-render**: client-side filters (entity/brand/platform/search) use `history.pushState` for instant re-render (no re-query); only the date window uses `router.push`. Clear was previously stuck behind a slow re-query.

**Perf:**
- Region query collapsed from 3× `MARKETING_EFFICIENCY` scans → 1 scan (~31s → ~13s).
- `unstable_cache` per-(source,range) enabled in **dev too** (was uncached); cold first-load-per-range warms it, then reads are ~0.1s.
- `export const maxDuration = 300` on the page so the ~60-90s cold render completes and warms the cache (default serverless timeout was killing it).

## 2026-07-10 — redesign initiative (evolve toward the prototype)
Client emailed prototype mockups → full redesign initiative. **Hub:** `aldc-launchpad/navira-dashboard-redesign/`
(`specs/{design-spec,gap-matrix,current-state,data-catalog,source-registry}.md`, `plan/{PLAN,PHASES}.md`,
`prototypes/`); boot prompt `aldc-launchpad/boot-prompts/navira-marketing-dashboard-redesign.md`.
**Evolve in place, iterate locally, single prod deploy at the END.**

- **Prototype finding:** ~70% of the mockup is fabricated (SmartScout, keywords, New-to-Brand, DSP
  reach, inventory, ratings — hash-seeded). Its IA already matches this app (segmented lens toggle,
  one dataset). It commits metric-law bugs — sums attributed sales across channels, and "TACoS" is
  actually ACoS — the redesign fixes them (see [[cross-channel-marketing-attribution]]).
- **Locked decisions:** (1) ROAS-led **Overview** lens, feature-flagged (easy on/off); (2) unsourced
  fields as **Live/Coming/Gated** (never fabricate) — **SmartScout first to activate** (contracted,
  pending client credentials), then Email, then Inventory (client pushed out, expected later);
  (3) fix metric-law (per-channel + MER, relabel ACoS, build true-TACoS); (4) restore UK+marketplace
  grain ([[project_gp226_roadmap_gap]]), true-TACoS view, defer campaign-USD (no `CURRENCY_CODE`).
- **Phase 0 foundation ✅ merged** to `feature/insite-calendar-brand-reach-region` (359 vitest +
  build green; e2e 42/42): design system + chart kit (`src/components/ui/`, light=canonical, dataviz
  palette), Playwright harness (`e2e/`), data-wiring — `getTraffic()` (`TRAFFIC_FCT_ACTIVITY`:
  sessions/buy-box/CVR), `getPlatformDetail()` (`MARKETING_FCT_PLATFORM_DETAIL`: Google SOV/video,
  Meta reach), real campaign names via `MARKETING_DIM_CAMPAIGN` join.
- **Phase 2 (build) in progress:** ROAS-led Overview, then restyle the lenses onto the design system
  with Live/Coming/Gated states. **Phase 3 (data, evidence-gated):** UK/marketplace grain + true-TACoS;
  a gated Snowflake read verifies the newly-wired object schemas. Roadmap + DoD: `plan/PHASES.md`.

## 2026-07-12 — prototype CARD rebuild (all views)
Branch `feature/insite-calendar-brand-reach-region`, commits **`c1a1704`** (rebuild) + **`978b65a`**
(orphan cleanup). NOT deployed — local review only (`http://localhost:3300`, warehouse). Gate green:
tsc + **363 vitest** + build + **50 Playwright** + lint.

Every view now matches the client prototype's **card-per-entity** layout: a card per entity → header →
8-tile KPI scorecard → **ONE unified expandable section table** (grey caption, sticky "Section / Row"
column, blue section-header rows with "N rows" + expand toggle, row-type badges). All sections share
**ONE global 40-column set** with a **global Customize Columns + Download CSV** in the toolbar
(prototype parity — replaced the prior per-drill-table pickers/CSV).

- **Paul's decision: "full prototype scaffold — so we know what is left to populate."** Columns &
  sections with no warehouse source render as honest **Coming** (Amazon Ads / Attribution / DSP /
  Traffic) or **Gated** (SmartScout) placeholders — never a fabricated number. **The dashboard IS the
  data-enablement roadmap now.**
- **New reusable engine:** `src/lib/insite-table.tsx` (shared `INSITE_COLUMNS`, byte-faithful to the
  prototype's `BRAND_TABLE_COLUMNS`, with per-`_kind` resolvers + `availability` live/coming/gated +
  `source`; `INSITE_CARD_LIMIT=50`), `InsiteColumnsContext` (global visible-column state, localStorage
  `insite:columns:card`, + CSV registry), `CardSectionTable`, `InsiteCard`, `CardTruncationNote`;
  `matrixToCsv` added to `src/lib/csv.ts`.
- **Views:** Brand (real: Ad platforms / Top products / Campaigns; kept coverage note + `?focus=`
  scroll), Product (real: marketplace-context row only — no product↔campaign link), Campaign (real:
  Campaign summary; currency-free KPI + native-currency caveat), Ad Platform (real: Brands / Campaigns
  / Top products **+ a "Marketplaces" section beyond the prototype** preserving per-marketplace UK
  detail — [[project_gp226_roadmap_gap]]; the page now passes `campaigns`+`products` to PlatformView).
  Trends chart swapped to the design-kit `LineChart`.
- **Cards capped to top-50 by spend** (`INSITE_CARD_LIMIT`) with a truncation note — the warehouse
  returns up to 2,500 products; a unified table per card ×2,500 isn't viable. Brand renders all filtered.
- **Removed orphaned `EntityCard.tsx` + `RegionView.tsx`** (superseded by the unified card).
- **Data-enablement backlog the scaffold makes explicit** (= the `next:`): **SmartScout** (Gated —
  market share, ratings/reviews, organic rank, win rates, search volume; biggest unlock, next source),
  **Amazon Ads** (portfolio/bid strategy/dates/top-of-search), **Amazon Attribution** (new-to-brand,
  long-term), **Amazon DSP** (reach/video), **Amazon Traffic** (detail/store page views), plus the
  **product↔campaign bridge** (warehouse/query change: ASIN via `MARKETING_FCT_ACTIVITY_UNIFIED.
  PRODUCT_ID` ↔ `SHARED_DIM_MARKETPLACE`, evidence-gated).
- Consumer render verified (warehouse): Brinno $7.47M / NAVAC $7.16M brand cards; Amazon channel $83.1M
  total sales, MER 34.0x; Google→Amazon Total Sales $0 (honest — cross-channel has no marketplace actual).
- Boot prompt: `aldc-launchpad/boot-prompts/navira-prototype-card-rebuild-done-next-enablement.md`.

## 2026-07-13 — data-enablement lane 1: Amazon Traffic (detail page views)
First scaffold column turned real. Branch `feature/insite-calendar-brand-reach-region`, commit
**`becf603`**. NOT deployed — local review only. Gate green: tsc + **365 vitest** (+2 grain tests) +
build; consumer render verified in warehouse mode.

Replaced the prototype's **mocked** `detail_page_views` (the mockup computes `rowClicks × 0.78` on every
row — `brandRowValue` ~L12522) with **real per-ASIN Amazon on-platform traffic** from
`TEST_DG1_GEP.WAREHOUSE.TRAFFIC_FCT_ACTIVITY`.

- **Join key proven by discriminating probe (not inferred):** `Product.asin` →
  `TRAFFIC_FCT_ACTIVITY.CHILD_ASIN` — **92.1% distinct / 98.7% views-weighted** coverage. The fact's
  `PRODUCT_ID` is the internal **merchant SKU** (`FBM_…`/`GEP_…`), NOT an ASIN (matched 1 product);
  `PARENT_ASIN` is the variation group (47%). See [[star-schema-convention]] — this is a case where three
  ASIN-ish columns exist and only the child is the reporting/join grain.
- **Re-grained `buildTrafficQuery` to `CHILD_ASIN`** (the consumer grain). It was speculatively grouped by
  SKU×child×parent + capped at 2,500 rows-by-sessions — fine when nothing consumed it, but that would
  truncate a per-product join. Now ~5,886 bounded rows (cap raised to a 25,000 safety net); the feed is
  **Amazon US-only** (single MARKETPLACE_KEY, decoded to "Amazon US"). `Traffic` type/mapper/tests reshaped;
  dropped the vestigial `productId`/`parentAsin` (nothing consumed them — the whole feature was dead-ended
  at the provider before this).
- **`detail_page_views` column flipped Coming → live** (real number on product rows, honest `—` where
  there's no per-row traffic). `brand_store_page_views_new` stays honestly **Coming** (separate Brand-Store
  report, not in this fact).
- **Wired `getTraffic` through** `page.tsx` (new `traffic` slice) → Brand/Product/Platform views; helpers
  `buildTrafficByAsin`/`detailPageViewsFor`/`trafficFor`/`trafficMetaSummary` in `insite-table.tsx`
  (ASIN join is case/space-normalized via `asinKey`). Product/Brand/Platform product-rows carry
  `detailPageViews` by ASIN; **Product cards gained a real "On-platform traffic (Amazon)" section** whose
  row `_meta` surfaces the richer real feed (sessions · buy-box · unit-session) **inline — deliberately NOT
  as new global columns** (prototype is the north star: no columns beyond its set).
- **Consumer-layer proof:** rendered values `750,213` & `239,613` are **byte-exact** to independently-queried
  DB values; the re-grained query reconciles to **28,989,203.95** total views / 5,886 child-ASIN rows / single
  "Amazon US"; other columns + KPI grid unchanged (no regression). Screenshot: Slobproof card = `33,541` real
  + honest `—` on the SmartScout-pending marketplace-context row.
- Evidence recorded in `aldc-launchpad/navira-dashboard-redesign/specs/data-enablement-findings.md`. Boot
  prompt: `aldc-launchpad/boot-prompts/navira-traffic-enabled-next-enablement.md`.

## 2026-07-13 — demo prep: default columns + product↔campaign bridge (DEFERRED)
Branch `feature/insite-calendar-brand-reach-region`, commit **`ae33a20`**. Local-only. Client demo ran on
localhost (warehouse mode). Gate: tsc + **365 vitest** + build; warehouse smoke on all 5 views (0 console
errors, cards render).

- **Default columns reworked to lead with real data** (`INSITE_DEFAULT_COLUMNS`): cards now open showing
  impressions/clicks/CTR/total_cost/CPC + the now-live **detail_page_views** + sales/ACoS/ROAS, plus a small
  SmartScout teaser (review rating/count) + the Amazon-Ads portfolio placeholder. Dropped the default-visible
  organic-rank/win-rate/search-volume **Gated** columns (still one click away in Customize Columns) so the
  first impression isn't a wall of "Gated". Trimmed from the prototype's own default for presentation.
- **Demo-day gotcha:** the per-(source,range) cache is **in-memory per server process** — a fresh `next
  start` is cold (~13–18s/view first hit, worst case ~60–90s per code comments). Demo runbook = start ONE
  warehouse server, warm every view once (`for v in brand product campaign platform trend; do curl -s -o
  /dev/null "localhost:3300/?view=$v"; done`), then KEEP THAT PROCESS ALIVE. A stale overnight process drops
  its Snowflake connection and starts 500ing — restart fresh.

### Product↔Campaign bridge — DEFERRED (by design, not a bug)
Attempted to populate Product "Campaigns" + Campaign "Advertised products". **The warehouse keys advertised
products by merchant/SellerCloud SKU, but the product roster by ASIN, with no crosswalk between them:**
- `MARKETING_FCT_ACTIVITY_UNIFIED.PRODUCT_ID` is **~99%-of-spend a merchant SKU** (`6007`, `amzn.gr.*`,
  `FBM_*`), NOT an ASIN (spend-weighted format: 80% other + 19% numeric + 0.8% ASIN). `SHARED_DIM_MARKETPLACE`
  is in the same SKU space (why the vendor bridge works: activity SKU → dim = 2,643/3,102 ≈ 85%).
  `MARKETING_EFFICIENCY_PRODUCT` (the product roster) carries **only ASIN**, no SKU.
- ⇒ direct `activity.PRODUCT_ID = Product.asin` covers **6.3% of products / <1% of spend** → would leave
  Campaigns empty for 94% of products. Not shippable; **kept the sections honest "Coming"** (the evidence
  gate correctly killed it). Brand↔Campaign linkage already works (~99% spend, DEFAULT_VENDOR path).
- **Corrected a contradiction:** the 2026-07-10 lane-(b) finding called activity `PRODUCT_ID` "the ASIN" — it
  is the SKU; the coverage number it cited is a SKU→vendor match. Superseded (see
  `data-enablement-findings.md`).
- **Candidate crosswalk for later:** `TRAFFIC_FCT_ACTIVITY` carries BOTH an internal `PRODUCT_ID` and
  `CHILD_ASIN` — evidence-gate whether its SKU space reconciles with the activity fact's before building.
- **Latent cleanup (non-urgent):** `buildProductsQuery`'s `dm.PRODUCT_ID = p.ASIN` vendor join is ASIN-vs-SKU
  so it rarely matches → silently `COALESCE`s to the product-view BRAND (cards still render fine).
- Boot prompt: `aldc-launchpad/boot-prompts/navira-demo-day-and-enablement.md`.

## 2026-07-15 — Google/Meta channel grounding (Option D) + Amazon Attribution GO ([[GP-287]])
Branch `feature/insite-calendar-brand-reach-region`, commit **`3eeadee`**. Local-only — **NOT deployed**
(Paul's call: hold prod until more of the channel story is built). Gate green: tsc + **392 vitest** (+13) +
build; warehouse consumer render reconciled penny-exact.

**Fixed the Google/Meta channel data gap (Option D — destination-honest grounding).** The cross-channel cards
led with each platform's *self-reported* attributed sales and couldn't compute total-sales metrics
(`totalSales` hardcoded 0 for non-Amazon channels). Chose to ground ad spend to **actual orders by destination
channel** using ALDC's penny-validated grounding views (no new source, no DDL) — see
[[cross-channel-marketing-attribution]].
- **Google card → new `"grounded"` headline**: Grounded ROAS / Grounded Sales / Grounded Spend(+coverage %)
  from `MARKETING_EFFICIENCY_GOOGLE_BRAND` (spend reconciled to actual Websites orders: **10.4× on $104,550 →
  $1,082,341**). New "Destination & grounding" section splits Websites-grounded vs ungrounded vs
  **Amazon-destination (spend shown, "attribution pending tagging")**.
- **Meta card → destination-honest**: Ad Sales labelled self-reported; destination spend shown; grounded sales
  honestly "Coming" (no Meta grounding view). Never fabricates a Meta grounded number.
- Display-rename "Google→Amazon"/"Meta→Amazon" card headers → "Google"/"Meta" (internal `PlatformName` keys
  unchanged). New fields `groundedSpend/groundedSales/destSpend*` on `MetricRow`; `groundedRoas` in `metrics.ts`
  (never touches `totalSales`, Flag-A-safe). Cache **v5→v6**.

**Amazon Attribution feasibility PROVEN → [[GP-287]] (In Progress).** The Amazon-destination slice can only be
measured via the Amazon Attribution feed (external click → verified Amazon order). Read-only Windsor probes:
- **Enrollment confirmed** (Brand Registry via Sponsored Brands). **Google tagging LIVE via Quartile** —
  landing URLs carry `?maas=…&ref_=aa_maas&tag=maas`; **93% of Amazon-bound Google spend tagged** ($37,836 of
  $40,682, 90d). **Meta N/A** ($5,969/30d, 0 Amazon-bound, all Websites/M2W).
- **Key finding:** `final_url` is available from Windsor but not pulled (curated `fields` list) — field-selection
  gap, not access gap. The Attribution *report* is a separate `amazon_ads` connector product (LWA OAuth), not
  built. Build boot prompt: `aldc-launchpad/boot-prompts/navira-amazon-attribution-build.md`.


1. `vercel link --yes --scope aldc --project navira-marketing-dashboard`, then **`vercel --prod --yes`** (Vercel CLI as `paulrussell-3307`, which CAN access the ALDC scope). Git-push auto-deploy is author-blocked for russell94paul ([[project_vercel_deploy_author_block]]) — CLI is the path.
2. **Env `SNOWFLAKE_SCHEMA`** must be `WAREHOUSE_TEST_GP226` (was wrongly `..._TEAM`, which also showed pre-Lectric-fix numbers). Env vars are Sensitive → can't `vercel env pull` values; change via `vercel env rm`+`add`.
3. **Grants gotcha (broke the first deploy — 500 "Object … does not exist or not authorized"):** the prod role `NAVIRA_MKT_RO` had grants only on the OLD `_TEAM` schema. When migrating schemas you MUST re-grant it: `USAGE` + `SELECT ON ALL/FUTURE VIEWS IN SCHEMA WAREHOUSE_TEST_GP226`, plus `USAGE ON SCHEMA REPORT_COMMON` + `SELECT ON REPORT_COMMON.MARKETING_DIM_AGENCY` (the new agency dim). Validate by temp-granting `NAVIRA_MKT_RO` to an admin user and running all dashboard queries as that role.
4. **Stale Data Cache gotcha:** Vercel `unstable_cache` persists ACROSS deployments. After a query-SHAPE change (new columns/joins), **bump the cache key version** (`insite-dashboard` → `insite-dashboard-v2` in `page.tsx`) or the new build serves the old payload (symptom: reach columns read 0 despite the warehouse having data).

## 2026-07-16 — real campaign names verified + honest top-level Type (Campaign lens)

First gap-closure lane off the prototype-parity punch-list (`boot-prompts/navira-dashboard-prototype-gap-closure.md`). Committed `f57e0c8` on branch `feature/insite-calendar-brand-reach-region` — **not merged/deployed** (single prod deploy stays the gated end-step).

**Live probe (read-only, `TEST_DG1_GEP`) settled a spec contradiction:** `MARKETING_DIM_CAMPAIGN` = `CAMPAIGN_ID, CAMPAIGN_KEY, CAMPAIGN_NAME` — **no type column** (the gap-matrix had claimed Type "comes with real names from the dim"; `data-catalog.md` was right — both specs now corrected).

- **Campaign names — already wired, now VERIFIED.** The `LEFT JOIN MARKETING_DIM_CAMPAIGN` was written but carried a `⚠ schema unverified` flag. Probe: join resolves **99.0% of Amazon / 95.5% overall**. Dim is **Amazon-only** (all IDs `AMZ_…`) → Google/Meta campaigns carry no dim row and keep the `CAMPAIGN_ID` fallback (honest). Stale comment cleared.
- **Campaign Type — was fabricated, now honest.** `mapCampaigns` had hardcoded `type: "sponsored-products"` for *every* campaign (mislabels the 6% SB/SBV). No type column exists to source, but Amazon names encode the product as a prefix token → new `deriveCampaignType()` maps `SP/SB/SBV/SD` → top-level (`Sponsored Products / Brands / Display`; SBV folds into Brands). Whole-token match (no false-positive on "SPRAY"). Coverage over live real names: **97.2% classify** (SP 93.8 / SB 1.8 / SBV 1.7); the 2.8% legacy agency schemes (`OW_/OP_/BR_…`) + all Google/Meta → honest **"—"**, never a guess. The prototype's richer sub-type ("Sponsored Products Keyword") is itself fabricated (derived from its own synthetic `AMZ_US_…_SP_KW` names) → deliberately NOT reproduced.
- **Files:** `types.ts` (`Campaign.type` → `CampaignType|null`, `CAMPAIGN_TYPE_LABEL` + `campaignTypeLabel()`), `providers/warehouse.ts` (`deriveCampaignType`), `warehouse.test.ts` (mapper + classifier coverage), `CampaignView/BrandView/PlatformView` (render label, "—" when null). Gate: tsc + eslint clean, **399/399 vitest**. Validated at the data + unit-test layer; full consumer-layer SSR eyeball belongs to the deploy gate.
- **Jira:** no ticket cleanly covers a dashboard-frontend population lane (GP-287 = Amazon Attribution; GP-225 = schema; GP-226 = Google connector) — left uncommented pending Paul's call on where the redesign population lanes should be tracked. **Resolved 2026-07-16:** [[GP-288]] created as the home for the whole prototype-gap-closure punch-list; both this lane and platform-detail now logged there.

## 2026-07-16 — platform-detail wiring: Google/Meta search-visibility + Meta video/reach ([[GP-288]])

Second gap-closure lane. Dashboard commits **`698c310`** (platform-detail) + **`015ce4b`** (ThemeToggle lint fix) on branch `feature/insite-calendar-brand-reach-region` — **not merged/deployed**. Consumes `MARKETING_FCT_PLATFORM_DETAIL` (built in Phase 0's `getPlatformDetail()` but until now unwired). Gate: tsc + eslint clean, **413/413 vitest** (+14).

**Live-schema probe (read-only, `TEST_DG1_GEP.WAREHOUSE`) before building** — the 16 assumed columns match the real VIEW, but the probe changed the plan:
- **`GOOGLE_ROAS` is junk** (max 0.12, avg ≈ 0) and **`GOOGLE_VIDEO_VIEWS` is empty** (0 non-null of 11,347 Google rows) → both **skipped**, never surfaced.
- **`AD_GROUP_ID` is NULL on every Google row** → the feed's grain is campaign×day for Google (ad-groups are Meta-only, 27 of them). The type's "campaign×ad-group×day" is Meta-only.
- Impression-share swings hard day-to-day and there are **no per-row impression counts to weight by** → the honest rollup is an **unweighted mean of the daily ratios** (never SUM a ratio — a Flag-A-class error).

**Key attribution decision (no fabrication — [[star-schema-convention]] source-fidelity):** the prototype's target scaffold columns `top_of_search_impression_share` / `top_of_search_bid_adjustment` are tagged **source = Amazon Ads**, but this feed is **Google/Meta**. Rather than mislabel Google data as Amazon's top-of-search IS, the real metrics are surfaced as **correctly-attributed `context` rows** (value in `_meta`, standard metric columns render "—" — the same honest pattern as the Option-D destination/attribution rows) in the previously-empty **"Search visibility / win rates"** section (Google card + Google campaign cards) and a new Meta **"Video & reach"** section. **The Amazon-Ads `top_of_search_*` columns stay "Coming"** until an Amazon Ads feed lands.

- **Fixed a latent fabrication:** `mapCampaigns` hardcoded `dailyBudget/budgetUsedPct/timeInBudgetPct = 0`, so every campaign card rendered "$0.00 daily budget · 0% budget used · 0% in budget". Now shows the **real avg daily budget** (`GOOGLE_CAMPAIGN_BUDGET`, mean over the window) for Google campaigns (**124** carry it) and honest "—" for Amazon/Meta; the fabricated budget-used/in-budget line is dropped (no source).
- **New pure module `src/lib/platform-detail.ts`** = the rollup (raw feed → per-campaign + per-channel grain: mean-of-daily ratios, summed video-quartile counts with retention = Σquartile/Σviews, Σ daily reach labelled *not de-duplicated*). Rolled up **inside the page cache slice** (cache `v8→v9`) so only ~160 rows cache, not the ~12k raw. Presentation row-builders `googleVisibilityRows`/`metaVideoReachRows` in `insite-table.tsx`.
- **Consumer-layer validated through the REAL provider path** (`getPlatformDetail()` → `rollupPlatformDetail` against TEST warehouse, not synthetic): Google search-IS **27.1%**, top-of-search **27.1%**, abs-top **19.0%**, budget-lost **3.5%**, rank-lost **69.7%** (Navira loses most impression share to *rank*, not budget); Meta retention curve **66→32→20→13%** across **83.6k** video views; **124** campaigns with real budget.
- **Deploy prerequisite DONE (only Snowflake mutation this lane):** granted prod role `NAVIRA_MKT_RO` `SELECT` on `TEST_DG1_GEP.WAREHOUSE.MARKETING_FCT_PLATFORM_DETAIL` (additive; role already had schema USAGE + read peer views like `MARKETING_DIM_CAMPAIGN`/`TRAFFIC_FCT_ACTIVITY`). Evidence-gated: verified role/USAGE/no-existing-grant first, view is owner's-rights so the view grant suffices. **Rollback:** `REVOKE SELECT ON VIEW TEST_DG1_GEP.WAREHOUSE.MARKETING_FCT_PLATFORM_DETAIL FROM ROLE NAVIRA_MKT_RO`.
- **ThemeToggle lint fix (`015ce4b`):** read `<html data-theme>` via `useSyncExternalStore` instead of setState-in-a-mount-effect (tripped `react-hooks/set-state-in-effect`, was blocking `npm run lint --max-warnings=0` for the deploy gate). Behaviour identical; no test exists → eyeball at visual QA.
- **Files:** `platform-detail.ts` (+test), `insite-table.tsx`, `page.tsx`, `CampaignView` (+test), `PlatformView` (+test), `ThemeToggle.tsx`. Boot prompt: `aldc-launchpad/boot-prompts/navira-dashboard-prototype-gap-closure.md` (`next:` → traffic completion).

## Open / next
- **2026-07-16 — P3.9 Cost/Sale + Margin columns shipped (TEST, branch)** ([[GP-288]], commits `7905735` Cost/Sale + `9784f25` Margin). Restored v1's two flat-table analytical columns (design-spec §8.7). **Cost/Sale** = spend÷purchases (pure-derived, zero SQL/creds). **Margin** = (netSales−COGS)/netSales, **BRAND-grain**, from `SALES_FCT_ORDERLINE.SALES_COGS_CONSOLIDATED` (USD) — the brand query already SUMs that fact's net, so this adds `SUM(SALES_COGS_CONSOLIDATED)` in the same CTE: **no new grant** (`NAVIRA_MKT_RO` reads the table live), **no new view/DDL, no vault access** (probed with the app's own `.env`). **Null-honest COGS (the [[project_lectric_cm_data_gap|Lectric CM]] trap):** COGS stays NULL where unsourced, NEVER coerces to 0 → `aggregatePlatformMetrics` leaves `cogs` undefined → Margin renders "—" not a fabricated 100%. **Rejected the warehouse's own `MARGIN_NET_CONSOLIDATED`** (probed: does not reconcile to net−COGS; opaque/non-additive). **Consumer-layer validated live:** NAVIRA 92/92 vendors real margins 28–72% (Brinno 41.2%, TF Publishing 72.3%, K&M 48.5%, Thomastik 28.6%; ~99.1% of sales-bearing revenue carries COGS), LECTRIC COGS NULL → "—". Campaign rows → "—"; **per-ASIN Margin (Product lens) shipped 2026-07-16** (commit `72dbcd1`, cache v11→v12, 440/440 vitest — see section below) via the SKU↔ASIN traffic crosswalk. Cache v10→v11; **437/437** vitest (+8). Follows [[star-schema-convention]] source-fidelity + evidence-gate (target proven, no-regression = added SELECT col only, rollback = branch-only/no DDL). Boot prompt `next:` → per-ASIN Margin | P3.10 column prefs | P2 SQL.
- **2026-07-16 — per-brand Amazon Attribution ROAS shipped (TEST) + prototype parity verified.**
  - **Per-brand attribution ROAS** ([[GP-287]]): view `WAREHOUSE_TEST_GP226.MARKETING_ATTRIBUTED_ROAS_BY_BRAND` + "Attribution by brand" section on the Google→Amazon card (commits clients `11892a66`, dashboard `e1eef8f`). Reconciles $91,667.16 sales / $63,902.30 spend (attr 100% / spend 98.9% brand-resolved). **Per-CAMPAIGN grain proven NOT defensible** (Quartile CAMPAIGNID is a re-labeled grouping — ≤50% joinable; ~42% of sales have no matching Google campaign spend); **Meta→Amazon structurally impossible** (walled garden, no history — client conversation). See [[GP-287]] + `boot-prompts/navira-attribution-brand-roas-shipped.md`.
  - **Prototype parity verified by literal mockup diff** (2026-07-16): layout ≈ 1:1 — header/8-tile scorecard exact, **21/21 sections** byte-faithful across all 4 lenses, 60-col table byte-faithful; all 6 metric-law errors fixed; ~70% fabricated prototype fields → honest Coming/Gated. **Gap to prototype = data population** (SmartScout biggest unlock) **+ one UI feature** ("see all" expanded modals). Specs `aldc-launchpad/navira-dashboard-redesign/specs/{design-spec,gap-matrix,current-state}.md` updated. **Gap-closure roadmap:** `boot-prompts/navira-dashboard-prototype-gap-closure.md`.
  - **Operational blocker:** the whole restyle + Option-D + GP-287 + gap-closure ([[GP-288]]) stack is on branch `feature/insite-calendar-brand-reach-region`, **~45 commits ahead of `main`** — NOT on prod. Merge + single prod deploy gates all client-facing progress. **Pre-deploy grant check** must confirm `NAVIRA_MKT_RO` has SELECT on every view the branch now reads (campaign dim, traffic, **platform-detail — granted 2026-07-16**, grounded, attribution, attribution-by-brand).
- **Prototype layout pass ✅ DONE (2026-07-12); data-enablement underway.** The dashboard is the enablement roadmap now — fill the Coming/Gated scaffold source by source. **Lane 1 Amazon Traffic ✅ DONE (2026-07-13)** — `detail_page_views` is real (see that section). **Remaining lanes:** SmartScout (Gated — biggest unlock, blocked on client credentials), Amazon Ads (portfolio/bid/dates/top-of-search), **Amazon Attribution — GO, [[GP-287]] In Progress** (feasibility proven 2026-07-15: Google 93% tagged via Quartile, Meta N/A; build = `amazon_ads` attribution product), Amazon DSP (reach/video), and the **product↔campaign bridge** (no new source, warehouse/query only — lane-(b) already scoped in the findings doc). **Google/Meta channel grounding (Option D) shipped 2026-07-15 (commit `3eeadee`, local-only).** **Platform-detail wiring ✅ DONE 2026-07-16 (commits `698c310`+`015ce4b`, [[GP-288]])** — Google search-visibility + Meta video/reach as honest context rows; real campaign budget replaces the fabricated $0. Cleanup still open: Campaign tile-4 "Top Search Adj." (needs Amazon-Ads top-of-search — NOT this Google feed). **Next solo lane: traffic completion** (buy-box %/sessions/units/CVR; `getTraffic()` already wired). Still local-only — no remote deploy of the rebuild/enablement yet.
- **Perf follow-up:** cold first-load-per-range is ~60-90s (heavy `MARKETING_EFFICIENCY_PRODUCT`/brand views, serial queries on one connection). Materialize the heavy views or parallelize the provider's connections so the client's first hit isn't slow.
- **Security hardening (deferred):** move prod `SNOWFLAKE_ROLE` off ACCOUNTADMIN → a least-privilege role for the service account (kept as-is this deploy to avoid breaking auth).

## 2026-07-16 — per-ASIN Margin in the Product lens ([[GP-288]] Lane 6)
P3.9 follow-on. Branch `feature/insite-calendar-brand-reach-region`, commit **`72dbcd1`** — **not merged/deployed** (single gated prod deploy stays the end-step). Added a per-ASIN contribution **Margin = (net − COGS)/net** to the Product-lens flat table, completing P3.9 (brand-grain Margin was `7905735`+`9784f25`). Gate: tsc + lint clean, **440/440 vitest** (+3).

- **Same-fact self-consistent margin (key design):** both COGS *and* net come from `TEST_DG1_GEP.WAREHOUSE.SALES_FCT_ORDERLINE.SALES_COGS_CONSOLIDATED` / `SALES_NET_CONSOLIDATED` (USD-consolidated — [[transaction_currency_handling]]), rolled from merchant-SKU grain to **ASIN grain via the proven traffic SKU→ASIN crosswalk** (`TRAFFIC_FCT_ACTIVITY`, dominant `CHILD_ASIN` per `PRODUCT_ID`, 1:1 so the join can't fan out — the same crosswalk that turned `detail_page_views` real in the 2026-07-13 traffic lane). Numerator and denominator from the same fact/grain → a self-consistent margin, NOT efficiency-attributed net mixed with orderline COGS. `netSales` is margin-only in the UI (no standalone column) so overriding it has **zero display regression**.
- **Null-honest COGS (the [[project_lectric_cm_data_gap|Lectric CM]] trap):** COGS SUM stays NULL where unsourced (never coerced to 0) → Margin renders "—", never a fabricated 100%. LECTRIC has **0** bridged product rows.
- **Evidence (read-only `.env` probe, no vault):** bridged NET **$75.53M** < universe **$76.51M** (no inflation); **2,417/2,500 (96.7%)** top-roster ASINs carry COGS; **98.6%** of NAVIRA COGS $ bridges to an ASIN; the exact generated query validated live at the consumer layer — top margins byte-match the standalone probe, **max 90.8%** (<100%, no impossible margins), one honest **−52.6%** loss-making ASIN rendered faithfully.
- **Files:** `src/lib/data/providers/warehouse.ts` (`buildProductsQuery` gains `sku2asin` + `cogs_asin` CTEs; `ProductRow` gains `SALES_NET_USD`/`SALES_COGS_USD`; `mapProducts` sets margin-consistent netSales + null-honest cogs), `src/lib/insite-table.tsx` (Margin column comment), `src/app/page.tsx` (cache prefix **v11→v12**), `src/lib/data/providers/warehouse.test.ts` (+3 tests).
- **Follow-on lanes still open:** solo — P3.10 server-side column prefs, P2 new-view SQL (portfolio/bid/status/dates, placement breakdown); client-gated — SmartScout P0, sign-off, keyword text, prod deploy.

## 2026-07-17 — prod outage: NAVIRA_MKT_RO grant gotcha bit a 3rd time → PERMANENTLY CLOSED with FUTURE grants
Reported live as "site not loading." **The 401 was a red herring** — `navira-mktg.analyticlabs.io` sits behind a prod-only fail-closed HTTP Basic Auth gate (`src/proxy.ts`, realm "GEP InSite", live since 2026-06-08, reads `BASIC_AUTH_USER`/`BASIC_AUTH_PASSWORD`). Creds (`Navira.test`/`T3ster!`) are valid and unchanged; a raw `curl` 401s simply because it sends no credentials. **Authenticating revealed the real fault: HTTP 500 on every render** — Snowflake `002003` "Object `TEST_DG1_GEP.WAREHOUSE.SALES_FCT_ORDERLINE` does not exist **or not authorized**."

- **Diagnosis path (reusable):** `vercel logs <prod-deployment-url> --scope aldc --json` surfaces the full Snowflake error behind Next's opaque error `digest`. Then probe as admin (`PAULRUSSELLADMIN`/ACCOUNTADMIN on `og35375.canada-central.azure`, pw in wiki vault §"Snowflake Environment Admin Accounts"): `SHOW TABLES LIKE …`, `SHOW GRANTS ON TABLE …`, `SHOW GRANTS TO ROLE NAVIRA_MKT_RO`. This **disambiguates "missing object" vs "missing grant"** in one shot — Snowflake conflates them in 002003.
- **Root cause (the new insight):** the table EXISTS (3.38M rows) — it's a **grant gap**. The brand-cards feature (commit `8d3cb11`, shipped in the 07-14 prod deploy) added a `SALES_FCT_ORDERLINE` read, but the manual grant was never applied — **and would have been stripped anyway**: Eclipse rebuilds `WAREHOUSE.SALES_FCT_ORDERLINE` **daily ~06:00 PDT via `CREATE OR REPLACE`, which strips object grants** (probe: table `created_on` 06:02 today, only OWNERSHIP at 06:03). This is why the 07-09 and 07-14 per-object `GRANT SELECT` fixes kept coming undone.
- **Durable fix (self-healing, Paul's choice):** `GRANT SELECT ON ALL + FUTURE TABLES AND VIEWS IN SCHEMA TEST_DG1_GEP.WAREHOUSE TO ROLE NAVIRA_MKT_RO` — 45 objects covered now, and FUTURE grants **auto-re-grant on every rebuild/redeploy**, so this class of outage cannot silently recur. Tradeoff accepted: the read-only reporting role can read all WAREHOUSE objects (TEST env). **Codified + rollback:** `aldc-launchpad/warehouse_ops/navira_mkt_ro_grants_RECIPE.sql`.
- **Validated consumer-layer:** `curl -u …` → **500 → 200**; prod log 500s stop 12:29 / clean 200s from 12:37 (grant at 12:37:41). Additive + reversible (read grants only, no data/DDL touched).
- **Rule update:** the "temp-grant role & run every query pre-deploy" check (from 07-14) is now **moot for WAREHOUSE-schema deps** (FUTURE grants cover them). It still matters for **net-new schemas / cross-DB refs** the FUTURE grants don't reach (e.g. `REPORT_COMMON`, `WAREHOUSE_TEST_GP226`).

## 2026-07-17 (session 3) — SmartScout removed, Overview P0 fix, E2E suite → **DEPLOYED to prod + MERGED to `main`**

The branch that had been ~65 commits ahead of `main` since 2026-07-09 finally **shipped and merged**. Commits `e372db7` → `95b16d9` → `dc2a2fc` → `7264fe5` (merge) → `7f5614c`. Full detail on [[GP-288]]; summary:

- **SmartScout removed from scope** (`ed9dfc9`): column picker 60→42, no "Gated" group remains.
- **P0 Overview blank-data fix:** a single non-Amazon **Platform filter** dropped the Amazon `totalSales` anchor (`mapPlatforms`, `warehouse.ts:768`) → Total Sales $0 / MER 0.0x / "—" ROAS on the Overview. **Fix:** the portfolio Overview now **ignores the channel filter** (Entity + Date still scope it) and **hides the Platform control** (matches the Trends-view convention). Reproduced + fixed at the consumer layer on the live TEST warehouse ($83.77M restored); locked with a vitest + E2E regression. NOT data staleness, NOT the SmartScout removal.
- **Google→Amazon brand attribution columns populated** (Total cost/Sales/ROAS via dedicated `attrSpend`/`attrSales` `InsiteRow` fields; walled-garden columns stay honest "—"). **Meta→Amazon** now shows an honest no-brand-attribution explainer (walled garden) instead of a stale note.
- **Two-lane Playwright E2E suite:** *synthetic functional* (per-PR, credential-free, **43/43** — every view/filter + the GP-288 Overview regression lock + SmartScout-gone lock + column-picker/cross-nav/theme/empty-states/metric-law; page-object helpers in `e2e/utils.ts`) and *warehouse data-integrity* (opt-in `playwright.warehouse.config.ts` + `npm run test:e2e:warehouse`, **7/7 on live TEST** — asserts the real dashboard is never silently blank/$0). Nightly + `workflow_dispatch` CI in `.github/workflows/e2e-warehouse.yml` (needs `SNOWFLAKE_*` repo secrets — **still to add**).
- **Deploy = Vercel CLI** (`vercel --prod`, ALDC-linked project; the customer domain stays pinned to the CLI deployment). **`main` IS the Vercel production branch** — a `git push origin main` fires a git-integration prod build, but it does not take over the custom domain. Merged `feature/insite-calendar-brand-reach-region` → `main` (`--no-ff`, `7264fe5`).
- **Greened `main` CI** by fixing two **pre-existing** failures (both predated this work): repo-wide `prettier --write` (49 files, formatting-only) and a flaky `date-filter.spec` (Playwright `fill()` on a native `<input type=date>` intermittently dropped the commit → replaced with the reliable native-setter + `change` dispatch on the To bound; 8/8 chromium+webkit).
- **Gates throughout:** tsc + lint + **475/475 vitest** + 43/43 synthetic E2E + 7/7 warehouse E2E + clean prod build.

Related: [[GP-288]] (prototype gap-closure punch-list) · [[GP-287]] (Amazon Attribution) · [[GP-225]] · [[project_gp226_roadmap_gap]] · [[cross-channel-marketing-attribution]] · [[GP-254]] (Lectric agency) · [[project_vercel_deploy_author_block]] · [[transaction_currency_handling]].

## 2026-07-19 — unified product picker BUILT (committed, held) + client coverage report ([[GP-288]])

New branch `feature/gp288-product-id-filters`, picker commit **`fd2e4b2`** — **committed, NOT deployed, NOT pushed** (deploy HELD). Full detail on [[GP-288]]; summary:

- **Unified "Find products" typeahead** (Product lens) replaces the prototype's three ASIN/SKU/Master-SKU boxes: one search over ASIN + merchant SKU + master SKU + product name → single `?asin=`. **Two halves:** a full-catalogue lightweight **index** for client-side suggestions (`getProductIndex`) + a **server-side `?asin=` fetch** (`buildProductsQuery` drops the top-N cap, `WHERE UPPER(ASIN) IN …`) so a long-tail pick outside the loaded top-2500 still renders (fixes the silent-empty trap). Files: `ProductFinder.tsx`, `lib/product-search.ts`, `FilterBar.tsx`, `lib/filters.ts`, `providers/warehouse.ts`, `app/page.tsx` (cache **v15**).
- **New TEST view (evidence-gated):** `WAREHOUSE_TEST_GP226.MARKETING_DIM_PRODUCT_ATTRS` = `GROUP BY ASIN` over `DATA_SHARE.WAREHOUSE_SHARED_DIM_PRODUCT` (`ASIN, MODE(MASTER_SKU), LISTAGG(DISTINCT AMAZON_MERCHANT_SKU,'|')`), 1 row/ASIN, **99.4% roster coverage**, consumer-agg byte-identical with/without the join, `NAVIRA_MKT_RO` granted. Rollback `DROP VIEW`. **Durable follow-up:** promote to a clients-repo warehouse template — a hand-made TEST view can be wiped by an Eclipse rebuild (same lesson as `MARKETING_DIM_CAMPAIGN_ATTRS`).
- **Teams + Kits stay honest Coming** (source proven, client-/model-gated). SmartScout out of scope.
- **Validation:** unit **517/517**, synthetic e2e **94/94**, live warehouse e2e **2/2**, tsc/lint/prettier clean.
- **Client Delivery & Coverage report produced** (branded HTML → print-to-PDF, `aldc-launchpad/navira-dashboard-redesign/reports/navira-coverage-report.html`, plan `~/.claude/plans/prancy-knitting-fern.md`): exact per-row status of every feature/metric — **34 Live · 8 Partial · 5 Awaiting-data · 2 Pending-decision · 2 Not-in-scope** (51 itemised) — each gap with an honest reason + path forward; grounded against the live build (INSITE `availability`/`source`, FilterBar, view components); leak-scanned clean (no internal object/ticket/infra/person names). **Produced, not sent** — distribution is Paul's.

## 2026-07-20 — Lectric/agency data-quality correctness + gap-spec reconciliation ([[GP-254]] / [[GP-288]])

Branch `feature/gp288-product-id-filters`, commits **`390a1af`** (fix + tests) + **`544275f`** (un-gate). **Committed, HELD** (Vercel-CLI on Paul's go, not pushed/prod). Driven by Paul spotting Lectric per-product **Sales = $0** despite $2.7M of real sales.

- **Root cause (two layers):** the drill-table "Sales" column binds to *ad-attributed* sales (= $0 for a no-ad entity); AND upstream `MARKETING_EFFICIENCY_PRODUCT` tagged Lectric's 29 ASINs `ENTITY_CODE='NAVIRA'` (BRAND='Lectric eBike') while `SALES_FCT` + entity-grain `MARKETING_EFFICIENCY` split LECTRIC correctly → `filterProducts(LECTRIC)` hid the 29 ASINs, so the Product lens falsely read "sales-only, no data". For Lectric the sales-fact `PRODUCT_ID` **is the ASIN** (B0-shaped); the traffic SKU→ASIN crosswalk bridges 0/29 Lectric SKUs.
- **Dashboard fixes (`insite-table.tsx`, `MetricGrid.tsx`):** "Sales" column falls back to actual gross (`totalSales`) when a row has no ad activity (`spend===0`) → sales-only entities show real per-product/platform sales (NAVIRA advertised rows unchanged); CTR renders "—" when `impressions===0` (was misleading "0.00%").
- **Upstream fix (clients repo, parallel session):** `MARKETING_EFFICIENCY_PRODUCT` entity tagging corrected on TEST (Lectric → `ENTITY_CODE='LECTRIC'`, 29 ASINs / $2,713,215 / 5,248u; COPY GRANTS preserved), durable template `GEP/snowflake/warehouse/marketing_efficiency_product.sql`. It is a **VIEW → live immediately, no Eclipse-rebuild wait**. Product lens under the Lectric filter now populated ($347,689 top product).
- **New live-warehouse Lectric data-quality + E2E lane** `e2e/lectric-entity.warehouse.spec.ts`: asserts sales populated / **non-$0 rows** (the bug class), honest "—" (no fabricated 0.0x/0.00%), no blank crash, and a cross-view correctness invariant (Overview == Ad-Platform Total Sales). 5 Lectric + 14 full warehouse lane green; unit 544/544; no NAVIRA regression.
- **[GOTCHA] `unstable_cache` masks a live warehouse fix** — dashboard data fns are wrapped in Next `unstable_cache` (revalidate 3600, persisted to `.next/cache`). A corrected view is invisible in a running `next start` for up to 1h and **a server restart does NOT clear it**; `rm -rf .next/cache` + restart to validate live. Prod self-heals within the hour.
- **Gap-spec reconciliation** (`aldc-launchpad/navira-dashboard-redesign/specs/*`, commit `fe6904d`): the 07-10/16/17 specs were stale — they marked as NEW-VIEW/NOT-INGESTED/UNWIRED a set now BUILT by GP-288 (campaign metadata via `MARKETING_DIM_CAMPAIGN_ATTRS`; master-SKU via `MARKETING_DIM_PRODUCT_ATTRS`; detail-page-views; purchases; true-TACoS). Added 2026-07-20 blocks + 11 inline `BUILT [2026-07-20]` annotations. **Conclusion: essentially all in-scope prototype surface is delivered.** Only remaining in-scope implementable gaps (all data-in-hand): CPM (derivable), Google search-visibility depth (top-of-search/budget-lost/rank-lost IS already in the provider), Meta video-quartile drill columns — scoped to `boot-prompts/navira-minor-gaps-and-delivery-report.md` (which also refreshes the client `reports/navira-coverage-report.html`). Gated/out-of-scope unchanged (keywords/NTB/DSP/inventory/budget-pacing/teams/kits/activity; SmartScout cancelled; email marketing out of scope).
