---
tags: [repo, gep, navira, dashboard, insite, marketing, advertising, nextjs, vercel, snowflake]
aliases: [navira-marketing-dashboard, GEP InSite, InSite, navira-mktg, insite-prototype]
sources: []
created: 2026-07-09
updated: 2026-07-09
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

## Deploy runbook (this project) — hard-won
1. `vercel link --yes --scope aldc --project navira-marketing-dashboard`, then **`vercel --prod --yes`** (Vercel CLI as `paulrussell-3307`, which CAN access the ALDC scope). Git-push auto-deploy is author-blocked for russell94paul ([[project_vercel_deploy_author_block]]) — CLI is the path.
2. **Env `SNOWFLAKE_SCHEMA`** must be `WAREHOUSE_TEST_GP226` (was wrongly `..._TEAM`, which also showed pre-Lectric-fix numbers). Env vars are Sensitive → can't `vercel env pull` values; change via `vercel env rm`+`add`.
3. **Grants gotcha (broke the first deploy — 500 "Object … does not exist or not authorized"):** the prod role `NAVIRA_MKT_RO` had grants only on the OLD `_TEAM` schema. When migrating schemas you MUST re-grant it: `USAGE` + `SELECT ON ALL/FUTURE VIEWS IN SCHEMA WAREHOUSE_TEST_GP226`, plus `USAGE ON SCHEMA REPORT_COMMON` + `SELECT ON REPORT_COMMON.MARKETING_DIM_AGENCY` (the new agency dim). Validate by temp-granting `NAVIRA_MKT_RO` to an admin user and running all dashboard queries as that role.
4. **Stale Data Cache gotcha:** Vercel `unstable_cache` persists ACROSS deployments. After a query-SHAPE change (new columns/joins), **bump the cache key version** (`insite-dashboard` → `insite-dashboard-v2` in `page.tsx`) or the new build serves the old payload (symptom: reach columns read 0 despite the warehouse having data).

## Open / next
- **2026-07-10 (later day):** Paul has **prototype HTML files** → iterate the dashboard toward the **client's desired layout**. Expect a layout/design pass.
- **Perf follow-up:** cold first-load-per-range is ~60-90s (heavy `MARKETING_EFFICIENCY_PRODUCT`/brand views, serial queries on one connection). Materialize the heavy views or parallelize the provider's connections so the client's first hit isn't slow.
- **Security hardening (deferred):** move prod `SNOWFLAKE_ROLE` off ACCOUNTADMIN → a least-privilege role for the service account (kept as-is this deploy to avoid breaking auth).

Related: [[GP-225]] · [[project_gp226_roadmap_gap]] · [[cross-channel-marketing-attribution]] · [[GP-254]] (Lectric agency) · [[project_vercel_deploy_author_block]] · [[transaction_currency_handling]].
