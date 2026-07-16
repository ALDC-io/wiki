---
tags: [repo, gep, navira, dashboard, insite, marketing, advertising, nextjs, vercel, snowflake]
aliases: [navira-marketing-dashboard, GEP InSite, InSite, navira-mktg, insite-prototype]
sources: []
created: 2026-07-09
updated: 2026-07-16
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
- **Jira:** no ticket cleanly covers a dashboard-frontend population lane (GP-287 = Amazon Attribution; GP-225 = schema; GP-226 = Google connector) — left uncommented pending Paul's call on where the redesign population lanes should be tracked.

## Open / next
- **2026-07-16 — per-brand Amazon Attribution ROAS shipped (TEST) + prototype parity verified.**
  - **Per-brand attribution ROAS** ([[GP-287]]): view `WAREHOUSE_TEST_GP226.MARKETING_ATTRIBUTED_ROAS_BY_BRAND` + "Attribution by brand" section on the Google→Amazon card (commits clients `11892a66`, dashboard `e1eef8f`). Reconciles $91,667.16 sales / $63,902.30 spend (attr 100% / spend 98.9% brand-resolved). **Per-CAMPAIGN grain proven NOT defensible** (Quartile CAMPAIGNID is a re-labeled grouping — ≤50% joinable; ~42% of sales have no matching Google campaign spend); **Meta→Amazon structurally impossible** (walled garden, no history — client conversation). See [[GP-287]] + `boot-prompts/navira-attribution-brand-roas-shipped.md`.
  - **Prototype parity verified by literal mockup diff** (2026-07-16): layout ≈ 1:1 — header/8-tile scorecard exact, **21/21 sections** byte-faithful across all 4 lenses, 60-col table byte-faithful; all 6 metric-law errors fixed; ~70% fabricated prototype fields → honest Coming/Gated. **Gap to prototype = data population** (SmartScout biggest unlock) **+ one UI feature** ("see all" expanded modals). Specs `aldc-launchpad/navira-dashboard-redesign/specs/{design-spec,gap-matrix,current-state}.md` updated. **Gap-closure roadmap:** `boot-prompts/navira-dashboard-prototype-gap-closure.md`.
  - **Operational blocker:** the whole restyle + Option-D + GP-287 stack is on branch `feature/insite-calendar-brand-reach-region`, **43 commits ahead of `main`** — NOT on prod. Merge + single prod deploy gates all client-facing progress.
- **Prototype layout pass ✅ DONE (2026-07-12); data-enablement underway.** The dashboard is the enablement roadmap now — fill the Coming/Gated scaffold source by source. **Lane 1 Amazon Traffic ✅ DONE (2026-07-13)** — `detail_page_views` is real (see that section). **Remaining lanes:** SmartScout (Gated — biggest unlock, blocked on client credentials), Amazon Ads (portfolio/bid/dates/top-of-search), **Amazon Attribution — GO, [[GP-287]] In Progress** (feasibility proven 2026-07-15: Google 93% tagged via Quartile, Meta N/A; build = `amazon_ads` attribution product), Amazon DSP (reach/video), and the **product↔campaign bridge** (no new source, warehouse/query only — lane-(b) already scoped in the findings doc). **Google/Meta channel grounding (Option D) shipped 2026-07-15 (commit `3eeadee`, local-only).** Cleanup: Campaign tile-4 "Top Search Adj." (needs Amazon-Ads top-of-search). Still local-only — no remote deploy of the rebuild/enablement yet.
- **Perf follow-up:** cold first-load-per-range is ~60-90s (heavy `MARKETING_EFFICIENCY_PRODUCT`/brand views, serial queries on one connection). Materialize the heavy views or parallelize the provider's connections so the client's first hit isn't slow.
- **Security hardening (deferred):** move prod `SNOWFLAKE_ROLE` off ACCOUNTADMIN → a least-privilege role for the service account (kept as-is this deploy to avoid breaking auth).

Related: [[GP-225]] · [[project_gp226_roadmap_gap]] · [[cross-channel-marketing-attribution]] · [[GP-254]] (Lectric agency) · [[project_vercel_deploy_author_block]] · [[transaction_currency_handling]].
