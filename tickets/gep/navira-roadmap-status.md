---
tags: [ticket, gep, navira, navira-roadmap, roadmap, status, hub, pbi, cogs, marketing, map-violators]
aliases: [Navira Roadmap Status, Navira Completion Status, Navira Roadmap Hub]
sources: [aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md, aldc-launchpad/boot-prompts/navira-roadmap-review-and-ceo-report.md]
created: 2026-06-16
updated: 2026-07-08
---

# Navira Roadmap — Completion Status Hub

> **▶ 2026-07-08 — Cross-channel marketing model state (read [[GP-225]] §"2026-07-08" for full detail).**
> The unified marketing fact already spans Amazon+Google+Meta in the live TEST model; the "why isn't
> Google/Meta in the same table" perception was the Amazon-scoped `Marketing Measures`. This session (TEST +
> repo only, live `66151728` untouched): built an isolated **`Data Model — Cross-Channel Preview`** clone
> (+cross-channel measures + Sponsored-Display dim; validated all 5 platforms populate) + comparability
> report; reconciled canonical marketing SQL on branch `feature/paulrussell/navira-marketing-canonical-consolidation`
> (equivalence gate caught+fixed a Google/Meta revenue-zeroing regression + UK `_170→_178`). **NEW direction
> (Paul):** stand up a SEPARATE **`Navira Marketing Model (Test)`** sibling dataset rather than promoting into
> the daily `Data Model`. Architecture gaps to "pivot new like old": conformed **Channel** dim, `SPEND_USD`
> on the fact, sentinel relabels, grain guards. Lori/Heather meeting shifted requirements — diff against this.

> **Single source of truth for "what's done, where (PROD vs UAT), and what's left"** on the Navira/[[GEP]] roadmap. Reconciles Jira status vs actual implementation. Compiled 2026-06-16 from Jira (`navira-roadmap` label, cloudId `239c1bf0-93f4-4201-95fe-ab73ce4a6eff`), the per-ticket wiki pages, the live model, and the [[processes/distributed-workflow/active/navira/README|Navira workflow hub]]. Master plan: `aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md`.

## CEO-facing report

**`Navira — Executive Overview`** — **7-page** exec report (Lectric agency tab + Proposed-Dashboards page added 2026-06-17), deployed to **GEP Test Models**, report `888d72c2-3854-4d00-ae84-43e5c4797950`, bound to the live UAT `Data Model` (`66151728-f00f-4a08-af91-6687de5f13dc`). Pages: (1) Executive Summary, (2) Data Ingested & Available, **(3) Agency Integration — Lectric Bikes**, (4) New Analytics Features, (5) Data Quality & Coverage Wins, (6) Roadmap Status, **(7) Proposed Dashboards** (D1–D8 buildable-now matrix). Every figure is live from the model (SQL == DAX validated). MAP Violators is referenced (separate model), not embedded. Builder: `aldc-launchpad/pbi_ops/_build_navira_ceo_report.py`. **Modeling note (UPDATED 2026-06-19 — GP-254 Option C DEPLOYED to TEST):** `Sales Measures` are **now agency-aware** — `Order Line` carries `ENTITY_CODE` (NAVIRA/LECTRIC) with a relationship to the `Agency` dim, so every sales/orders/units/COGS/margin measure responds to the Agency slicer (previously only Marketing Efficiency did). Built the **full conformed-component** way (Lectric conformed into product/order/marketplace dims + unioned into the `Order Line` source view; `ENTITY_ROLE` HOUSE/AGENCY added; 12 `… (All Agencies)` / `… (Company Total)` rollup measures). Validated in TEST: Lectric $2,520,823 / Navira $121,205,026 / **Company Total $123,725,849** / All Agencies = $2,520,823 (Lectric only). **Consequence handled (Paul chose Company-Total default):** the model's default unfiltered sales total now includes Lectric ($123.7M). **CEO report REVIEWED + UPGRADED 2026-06-19:** exec/business headline visuals scoped to Navira/HOUSE (16 NAV filters across Pages 1/2/4/5 → Navira MER 30.99x not blended 32.0x, Gross $121.2M; Page-1 slicer removed); the new agency-aware sales is now showcased (Page 1 "What's new" leads with it; Page 3 has a Sales-Measures Sales-by-Agency table + Company-Total callout; Page 6 roadmap lists GP-254). Deployed (Fabric updateDefinition), verified live. Builder committed `aldc-launchpad` `a32c20a`; rollback `pbi_ops/_ceo_report_LIVE_rollback.json`. Open: COGS-coverage card denominator call (77.8% window vs 83.9% whole-fact); return-rate text card still hardcoded. Design + deploy detail: `aldc-launchpad/warehouse_ops/_lectric_native_DESIGN_v2_GROUNDED.md`; metrics/schema guide `pbi_ops/navira_metrics_guide.md` (§A schema map + §5 agency). Lectric margin stays blank until COGS lands. Rollback bundles intact (warehouse `_lectric_native_24_rollback.py`; model = drop 12 measures + 2 cols + relationship).

## Dashboards & metric tiers (clarified 2026-06-17)

**Dashboard format is NOT client-mandated in the roadmap** — it is ALDC's to propose. Of 41 `navira-roadmap` Jira tickets, only ~5 mention fields and those are *warehouse* column specs, not consumer layouts. Proposal artifacts: straw-man **D1–D8** set in `wiki/processes/distributed-workflow/active/navira/navira-dashboard-recommendations.md`; detailed marketing layout + 4 "confirm-with-client" decisions in `aldc-launchpad/pbi_ops/marketing_efficiency_display_design.md`. The only client-driven layout specs that exist: **MAP Violators** (Justin's mockup → built, 6 pages), **Inventory** (client sample CSV → paused on client Q&A), **Return Rate** (Heather's KPI formulas).

**Marketing measurement tier ladder — status 2026-06-17:** Tier 0 spend/engagement ✅ · Tier 1 Platform ROAS ✅ (Amazon 5.07x/Google 2.95x/Meta 1.77x) · Tier 2 Blended MER ✅ (32x) · Tier 2.5 Calibrated ROAS ✅ both built (**open client decision** capped vs uncapped) · Tier 3 Grounded ROAS ✅ (Amazon product only, ~36x) · Tier 3.5 Contribution Margin ✅ **LIVE in TEST** ($38.1M/50.8%) · **Tier 4 causal/MMM ❌ NOT implemented** (gated on GP-227 backfill + order-level UTM/Meta CAPI). ⚠️ `aldc-launchpad/pbi_ops/navira_marketing_presentation_guide.md` (2026-06-05) is STALE where it calls CM "future" — CM landed via GP-259 on 2026-06-16. Google/Meta are campaign-level only (no product grounding yet; ~61% of Google spend PMax+Shopping groundable later). Full meeting guide: `aldc-launchpad/boot-prompts/navira-progress-and-dashboard-guide.md`.

## TEST validation surface — live pivot access + model integration (2026-06-18)

Navira can now validate in TEST **the same way as PROD**:

1. **Live data-model download.** Built the TEST "Analyze in Excel" live-pivot workbook (GUID-swap of the prod workbook → dataset `66151728`), served from legacy Eclipse as **`Data Model (Live)`** (`app_report` id 56, `/file/56/`). The prereq blocker — **GEP Test Models had zero client users** — was fixed by mirroring prod: added `asad.amin`/`shah.muttal`/`sarwar.osama` (@gep.aldc.io) + `lori.beck`/`mike.stuart` as **Contributor**. Full mechanics in [[Power BI]] § Live Data Model.
2. **Marketing Efficiency now Date-integrated.** `Marketing Efficiency` + `Marketing Efficiency Product` were islands (joined only to `Agency`); added **date-to-date relationships to `Date`** (`ACTIVITY_DATE → Date[Date]`, many:1, recalc'd). Validated: grand total unchanged ($2,484,313.74 spend), date slicer now filters (May-2026 = $154,120), full coverage, no blank-date loss. So the efficiency measures respond to the global date slicer model-wide (live pivot, Explore, dashboards, reports). Marketplace/Product cross-filter deliberately **not** added to blended MER (entity-level by design). Builder: `aldc-launchpad/pbi_ops/_integrate_marketing_efficiency.py` (rollback: drop relationships `Relationship`/`Relationship 1`).
3. **Embedded report gained operational ME + Agency pages.** The Eclipse-embedded `Data Model` report (`15128c39`) was a bare template; appended **Marketing Efficiency** (MER/spend/sales/CM, platform ROAS, channel spend, marketplace table, Date+Agency slicers) and **Agency** (entity summary, sales by entity, entity×marketplace, per-ASIN grounded ROAS) pages. `Template Main` preserved. Builder: `aldc-launchpad/pbi_ops/_build_embedded_me_agency.py` (rollback: redeploy `_embedded_report_15128c39_ROLLBACK.json`).
4. **PROD vs TEST model parity** verified — TEST is a structural superset of PROD (all 30 prod tables + 244/245 measures; +5 roadmap tables/47 measures). See [[Power BI]] § PROD vs TEST model parity.

TEST only (per scope); same two changes (Date relationships + report pages) are the PROD step at roadmap promotion.

### Delivery verified end-to-end + static duplicate removed (2026-06-26)

Confirmed the client-facing download chain is fully wired and correct in TEST (no build needed — the 2026-06-18 work completed it):
- **Artifact:** `Data Model (Live).xlsx` (31 KB) in GEP storage `aldcteststac1cda8904db/files/`; embedded connection = `MSOLAP.8` → `Initial Catalog=sobe_wowvirtualserver-66151728-…` (the validated live model).
- **Visibility:** `app_report` 56 (enabled) ∈ group 15 "All Reports"; client users (`htabor`/`jshuster`/… @globalecompartners.com + `jshuster@navira.io`) are group-15 members, active, recent logins (Heather 2026-06-22). `eclipse-test.aldc.io` serves this legacy Django portal.
- **Live-refresh prereq:** the full client roster has `@gep.aldc.io` accounts with **Contributor** on GEP Test Models via the **"Power BI GEP Models Data"** security group (incl. `heather.tabor`, `justin.shuster`). So both auth layers (portal download + XMLA live refresh) are satisfied.
- **Model correctness (re-validated 2026-06-26):** DAX (executeQueries, the path Eclipse uses) == Snowflake `TEST_DG1_GEP`, penny-exact across Marketing/Efficiency/Agency/Sales/Customer/MAP after a fresh refresh; only the live Amazon ad stream drifts ~0.06% (snapshot-vs-live latency, proven by refresh convergence, not a defect). Anchors: Actual Sales $83,493,611.58, MER 32.7x, MAP Sellers 787, Distinct Customers 2,129,106.
- **Static duplicate removed:** the **static** `Data Model` download (`app_report` 50, 41 MB daily dump regenerated by the `func-aldc-cred` timer) was **unlinked from group 15** (`app_group_reports` id=62 deleted) so the client sees one unambiguous live download. Row + blob left intact (timer unaffected); rollback = `INSERT INTO app_group_reports (group_id, report_id) VALUES (15, 50);`.
  - **Gotcha (do not rename 56 to plain "Data Model"):** the timer matches the static report by name "Data Model" / file `Data Model.xlsx`; the `(Live)` suffix + distinct file `Data Model (Live).xlsx` is what protects report 56 from being overwritten with the static dump. Keep a name distinct from "Data Model".

## TEST↔PROD parity + client-readiness pass (2026-06-19)

**TEST↔PROD model diff (TOM, `pbi_ops/_compare_models.py`) — every difference maps to a roadmap ticket.** TEST is a superset of PROD; **GP-199 + GP-200 are present in both** (data-level within shared tables, no structural delta). TEST-ahead = in-flight roadmap (not yet promoted): 5 tables (`Agency`/`Marketing Efficiency`/`Marketing Efficiency Product`/`Google Brand Grounding`/`Google Product Grounding`) + ~49 measures (GP-277 efficiency + Flag A/B), `Marketing Activity[ENTITY_CODE]` + Agency rels (GP-225), `Order Line` return cols (GP-259). Two items where TEST trailed PROD were the only anomalies:
- **GP-256 `Actual - Sales - Return Rate %`** (a *Done/PROD* deliverable) was missing from TEST → **fixed 2026-06-19**: added to TEST `Sales Measures` identical to PROD (`DIVIDE([Actual - Sales - Returns (Quantity)],[Actual - Sales - Gross (Quantity)],0)`, fmt `0.00%`), validates **4.20%** (131,683/3,132,563). Builder `pbi_ops/_integrate_marketing_efficiency.py`-style via XmlaClient; rollback = delete the measure.
- **`Traffic Activity[MARKETPLACE_KEY]` + its Marketplace relationship** (PROD-only) → **DONE 2026-06-19 (later).** ⚠️ *Not* warehouse-side as first assumed: `WAREHOUSE.TRAFFIC_FCT_ACTIVITY` (the view the model imports) **already exposes `MARKETPLACE_KEY`** in TEST, and the TEST/PROD refresh-policy source M are **byte-identical** (select-all from the view, date-windowed) → no M edit, no warehouse change. Gap was purely model-side. Fix = TOM add column (`String`/hidden/`summarizeBy=None`, mirrors PROD) + relationship `Traffic Activity[MARKETPLACE_KEY]→Marketplace[MARKETPLACE_KEY]` (Many:1, OneDir), then enhanced-refresh **type=full on the single table** (`applyRefreshPolicy=false`, ~3 min / 97 incremental partitions) to populate the column, then `type=calculate` recalc. Evidence ALL PASS: measures byte-identical to baseline; `MARKETPLACE_KEY` 1 distinct / 0 blank (Navira traffic = Amazon US only, 6.71M rows → low client value today but clean parity + future-proof); by-marketplace breakdown = grand total under single 'Amazon US' with zero blank bucket; row count 6,609,059→6,714,600 = full source-view parity (reprocess healed a pre-existing 105K zero-value-row partition-window gap). Builders `pbi_ops/_traffic_marketplace_{apply,refresh,validate}.py`; rollback = drop column + remove relationship `Relationship 5`.

**Result: TEST is now a clean structural superset of PROD** — `_compare_models.py` reports **PROD-only relationships: 0, PROD-only measures: 0**. Every PROD column/measure/relationship is present in TEST; the only diffs are TEST's intended roadmap additions.

**Relationship health check (`pbi_ops/_wire_islands.py`, TOM):** all relationships are clean Many:One single-direction — **no inactive, many-to-many, bidirectional, or ambiguous (duplicate-path)** relationships. Fixed 3 visible **island** tables (no relationships → ignored every slicer):
- `Google Brand Grounding[ENTITY_CODE]→Agency` and `Google Product Grounding[ENTITY_CODE]→Agency` — now agency-aware (validated: Brand Grounding = Navira $89,400, Lectric absent). Date NOT joined (monthly `ACTIVITY_MONTH` grain, no daily key).
- `Marketing Activity[CAMPAIGN_KEY]→Campaign` (key unique 144,641/144,641) — **enables campaign-level marketing breakdown** that was impossible before (validated; no-regression on MA totals; ~$223K spend lands in a blank-campaign bucket = Google/Meta/unmapped, expected). Rollback: drop relationships `Relationship 2/3/4`.

**Remaining client-readiness items (→ boot prompt / next session):**
1. ~~**Sales Measures not agency-aware** (the big one)~~ — **DONE 2026-06-19 (GP-254 Option C deployed to TEST):** sales now agency-aware end-to-end (Order Line[ENTITY_CODE]→Agency + ENTITY_ROLE + rollup measures). Default total now = Company Total (incl Lectric) → CEO report review pending.
2. ~~**`Traffic Activity[MARKETPLACE_KEY]`** parity~~ — **DONE 2026-06-19 (see parity bullet above).**
3. ~~**Redundant dataset** `Data Model (Unified TEST Preview)` (`19cf5ef9`)~~ — **DONE 2026-06-19 (later 2): deleted.** Probe confirmed 0 of 3 workspace reports bound it (all bind the real `66151728`), stale since 06-12. Deleted via REST (HTTP 200); GEP Test Models now shows a single `Data Model`. Builders `pbi_ops/_cleanup_redundant_dataset_{probe,delete}.py`; rollback = `python -m pbi_ops._build_test_model_unified`.
4. **Google Grounding date integration** deferred (monthly grain).

## Current-source dashboard-readiness pass + Platform Detail deployed (2026-06-25)

**Goal:** ensure the 5 already-ingested sources (Google/Meta Windsor, Lectric agency orders, Amazon SP-API
multi-tenant, Amazon UK ads) are stored so every navira-roadmap dashboard metric tied to them is present or
trivially derivable — finalize before a client presentation. Plan: `~/.claude/plans/jaunty-plotting-prism.md`.

**Live audit (read-only, model `66151728`): coverage is ~95% already.** 134 measures cover D1/D2/D4/D5/D8 +
most of D3/D6 (ACoS overall+SP+SB, TACoS %, CTR/CPC/CPM, Buy Box %, Conversion Rate %, Sessions, Page Views,
CAC, full Customer LTV/cohort set, all D5 waterfall fees, marketplace YoY). Sales already Agency-sliceable
(GP-254 C). Order Line marketplaces incl **Amazon UK = 2,413 lines** (UK *sales* present). Only two genuine
current-source gaps remained:

1. **`MARKETING_FCT_PLATFORM_DETAIL` — DEPLOYED + imported (2026-06-25).** Was undeployed; the real compile
   blocker was a 1-token bug — the Meta branch referenced `PLATFORM_NAME.META_FACEBOOK` but the
   `WAREHOUSE.MARKETING_DIM_PLATFORM_NAME` column is **`META_FACEBOOK_ADS`** (NOT the Meta-insights "column
   drift" earlier assumed; all Meta-insights + Google cols + dims exist). Fixed repo DDL
   (`clients/GEP/snowflake/warehouse/marketing_fct_platform_detail.sql`), shadow-compiled (10,189 rows =
   Google 9,883 + Meta 306), deployed `WAREHOUSE_SOURCE`+`WAREHOUSE` views (CORE_SVC, COPY GRANTS,
   SELECT→REPORT_SVC), imported into model `66151728` as table **`Marketing Platform Detail`** +
   relationships (`ACTIVITY_DATE→Date[Date]`, `ENTITY_CODE→Agency`, `PLATFORM_ID→Platform`) + 4 measures
   (`Google Search Impression Share` 22.9%, `Avg Campaign Budget`, `Video Views` 52,721, `Meta Reach`
   405,596). DAX-validated, slices by Platform/Agency/Date; existing `Spend (USD)` unchanged (additive, no
   regression). **Unlocks D3 paid-SOV proxy (Google impression share) + D6 budget-pacing & video/reach.**
   Builders: `warehouse_ops/_platform_detail_deploy_TEST.py`, `pbi_ops/_platform_detail_import.py`.
   Rollback: `drop` table / drop the two views. **⚠ TOM gotcha learned:** relationships added *after* the
   data refresh throw "referenced a relationship between A and B" on any traversing query despite
   `IsActive=True` — must run `RequestRefresh(RefreshType.Calculate)` to build cross-filter indexes.
   *(One new model table — justified new grain, conforms to existing dims; not sprawl.)*

2. **Amazon UK ads — INTEGRATED into the consumer fact + efficiency layer (2026-06-25).** Was 682 rows
   isolated in sandbox `WAREHOUSE_TEST_NAVIRA_ROADMAP.CURRENT_SPONSORED_PRODUCTS_ADVERTISED_PRODUCT_REPORT`
   (profile `1236242149887729`, **GBP** £2,982). **Design decision (Paul): no per-source-view proliferation
   — the `…_GOOGLE_META` split was cutover scaffolding.** Renamed that holding view source-neutral →
   **`WAREHOUSE_SOURCE.MARKETING_FCT_ACTIVITY_PREPROD`** and added UK as Branch 8 (Google+Meta+UK in one
   view; `…_UNIFIED` stays at two branches). Repointed all three consumers (UNIFIED, `MARKETING_EFFICIENCY`,
   `MARKETING_EFFICIENCY_GOOGLE_BRAND`) and **dropped `…_GOOGLE_META`** (zero proliferation). UK routed
   through `MARKETING_EFFICIENCY.AMZ_DAY` so it gets the existing `'Amazon UK'→GBP→USD` FX path; `GM_DAY`
   filtered to Google/Meta so UK can't pollute it. **Evidence-gated (shadow):** every existing marketplace
   byte-identical, **UK = +$3,968.17** (£2,982 × FX), total delta == UK exactly (no double-count); Google
   Brand totals byte-identical pre/post repoint. Model `Marketing Activity` + `Marketing Efficiency` tables
   refreshed; DAX-validated UK in headline `Spend (USD)`/`Spend - Amazon`/MER. Builder
   `warehouse_ops/_uk_ads_integrate_TEST.py`; rollback DDLs in scratchpad. **Unlocks D3 Amazon-UK ACoS/spend
   + D8 UK marketplace ad view.** ⚠ CEO-report figures (read `MARKETING_EFFICIENCY_MARGIN`) now include UK
   (Navira spend +~$3,968 / ~0.15%) → re-validate report numbers next. Consolidation into the single
   canonical `marketing_fct_activity.sql` (Branches 1–8) remains the **GP-225 cutover** target.

3. **Amazon Sponsored Display — integrated (2026-06-25).** SD ($3,374.90 / 942 rows / US) added as
   `MARKETING_FCT_ACTIVITY_PREPROD` Branch 9; `MARKETING_EFFICIENCY.AMZ_DAY` filter widened to include SD.
   Shadow-validated (Amazon +$3,374.90, non-Amazon byte-identical, no leakage). Completes Amazon ad-type spend
   visibility (SP/SB/SD). NOTE: SD has **$0 attributed sales**, so `ACoS % - Sponsored Display` is blank.
   Builder `aldc-launchpad/warehouse_ops/_sd_ads_integrate_TEST.py`.
4. **Dashboard quick-win measures (additive DAX, committed spec).** Model `66151728`: `LTV to CAC Ratio`
   (D4 — 9.5×, directional: CAC is blended); `Spend Share`/`Revenue Share - Amazon/Google/Meta` (D2 allocation
   — Amazon 92%/95%, Google 7.6%/4.6%, Meta 0.5%/0.2%); `ACoS % - Sponsored Display` (blank). Captured in the
   committed spec `aldc-launchpad/pbi_ops/navira_dashboard_measures.json` (reproducible / model-rebuild parity).
5. **GP-259 backfill repo parity — committed.** The deployed `WAREHOUSE_SOURCE.SALES_FCT_SELLER_CLOUD_ORDERLINE`
   carried the GP-259 Option-A COGS backfill **and** an `AMAZON_ALL_ORDERS` US∪UK promotion union — neither in
   the clients repo (a redeploy would have reverted the $20.5M backfill). Committed the exact deployed DDL,
   shadow-validated byte-for-byte (rows 2,811,403; COGS/item $54.19M; gross $131.93M): clients `5ca93a70`,
   branch `feature/paulrussell/gp-259/sc-orderline-cogs-backfill-uk-promo-parity` (off main). **Broader
   repo↔TEST drift sweep queued** — `aldc-launchpad/boot-prompts/navira-repo-test-drift-sweep.md`.
6. **Client-facing progress reference** (presentation supplement): navigable HTML built off the navira-roadmap
   layout — implemented / enabled-by-recent-work / upcoming-by-priority + a "verify in the Test Data Model"
   reference table. Artifact: `https://claude.ai/code/artifact/ea77d1ae-1d7a-444a-937e-672b0ec1c164`.

**Out of scope today:** Inventory/Purchasing (hidden, old partial view, separate future ticket — D5 uses
Order-Line fees, unaffected); Wave-3 future sources (email/SmartScout/Target+/creative) — consolidated
access ask drafted at `aldc-launchpad/pbi_ops/navira_wave3_data_access_request.md`, parked.

## Headline live numbers (UAT `Data Model`, all agencies, 2026-06-16)

| Metric | Value | Source measure |
|---|---|---|
| Total gross sales (all channels) | **$120,737,441** | `Sales Measures[Actual - Sales - Gross]` |
| Net sales | $113,318,517 | `[Actual - Sales - Net]` |
| Orders | 2,719,677 | `[Actual - Sales - Gross (Order Count)]` |
| COGS now tracked | **$58,135,082** | `[Actual - Cost - COGS]` (GP-259 validated) |
| Contribution Margin | $38,087,102 | `Marketing Efficiency[Contribution Margin (USD)]` |
| Contribution Margin % | 50.8% | `[Contribution Margin %]` |
| COGS coverage % | 77.8% (model) / 86.1% (order-line, GP-259) | `[COGS Coverage %]` |
| Blended MER | 32.06x | `[MER (Blended ROAS)]` |
| Per-platform ROAS | Amazon 5.07x · Google 2.95x · Meta 1.77x | `[Platform ROAS - *]` |
| Marketing spend | $2,476,373 (Amazon $2.28M / Google $187.7K / Meta $9.5K) | `[Spend (USD)]` + `[Spend - *]` |
| Return rate | 4.2% (131,183 / 3,123,767 units) | computed (not a TEST measure) |
| By agency | Navira MER 31.0x / CM $35.6M · Lectric CM $2.52M (no COGS) | `[…]` by `Agency[Agency]` |

## Completion table (Jira vs reality)

### ✅ Delivered & PROD-live
| Ticket | Title | Jira | Env | Evidence |
|---|---|---|---|---|
| [[GP-199]] | SB ASIN ad attribution v3 | Done | **PROD** | v3 live in `WAREHOUSE.MARKETING_FCT_ACTIVITY`; +607 halo, spend Δ$0.00; daily monitor green |
| [[GP-200]] | Amazon UK orders | Done | **PROD** | +28 UK feed orders, 1,116 lines; US/CA/MX/BR byte-identical |
| [[GP-203]] | Canada traffic | Done | **PROD** | CA 1.40M rows / $1.39M |
| [[GP-204]] | CSV-driven marketplace metadata | Done | **PROD** | before/after diff = 0 rows |
| [[GP-207]] | Prod→Test data share | Done | **PROD** | ~50 views repointed to `PROD_DG1_GEP`; daily sync task |
| [[GP-256]] | Return Rate KPIs (DAX) | Done | **PROD** | 4.2% overall; brand-level agg correct |

### 🟡 Complete & validated in TEST/UAT (PROD promotion gated on sign-off)
| Ticket | Title | Jira | Reality | Evidence |
|---|---|---|---|---|
| [[GP-225]] | Unified marketing schema | Development ⚠️stale | **TEST cutover done** (live Data Model repointed in-place) | `MARKETING_FCT_ACTIVITY_UNIFIED`; 820,388 rows; zero-regression; commit `3f825d6` |
| GP-226 | Google Ads (Windsor) | QA | TEST, real data | live to 06-12; Fusion92 account filter |
| GP-222 | Meta (Windsor) | QA | TEST, real data | near API floor |
| [[GP-277]] | MARKETING_EFFICIENCY + core_api | QA | TEST deployed; **PR not merged → PROD core_api still old** | 34/34 checks; Jan-FX gap healed (MER 30.29→31.52x) |
| [[GP-257]] | Amazon UK ad spend | QA | **TEST end-to-end + now in the consumer model (2026-06-25)** | 682 rows/£2,982 → integrated into `MARKETING_FCT_ACTIVITY_PREPROD` (Branch 8) → flows to `…_UNIFIED` + `MARKETING_EFFICIENCY` (UK +$3,968.17 USD via the Amazon-UK→GBP FX path); no-regression shadow-validated; model refreshed + DAX-validated. See 2026-06-25 section. UK *sales* already in Order Line. |
| [[GP-259]] | COGS / Orders-Return | GEP QA | **TEST deployed + validated** | coverage 53.9%→86.1%; **~$21.25M recovered**; SQL==DAX byte-exact |
| [[GP-281]] | Cost-history clone-staleness | Consulting/Design ⚠️**badly stale** | **TEST deployed + validated** | cost-history `MAX` 03-03→06-15; 18 views swept; CM $38.14M; SQL==DAX |
| Contribution Margin | Tier-3.5 | — | TEST live | `MARKETING_EFFICIENCY_MARGIN` |

### 🔵 Built in TEST, gated on client sign-off
| Ticket | Title | Jira | Reality | Evidence |
|---|---|---|---|---|
| [[GP-261]] | MAP Violators | GEP QA | **TEST pipeline + 6-page report; DAX-validated** | 332,330 rows; 787 sellers; 20.2% blended violation; separate Sandbox model. Pending Lori/Heather + page-1 visual QA |

### 🟠 Partial / known gaps
| Ticket | Title | Jira | Gap |
|---|---|---|---|
| [[GP-254]] | Lectric agency | QA | **Option C native agency-aware sales fact DEPLOYED to TEST 2026-06-19** (full conformed-component): Lectric ($2,520,823 / 4,206 orders / 4,800 units / 25 ASINs / Amazon US) now native in `Order Line` + conformed into product/order/marketplace dims; `Order Line[ENTITY_CODE]→Agency` rel + `ENTITY_ROLE` + 12 rollup measures. Sales now agency-sliceable; Company Total $123,725,849. **Still blocked (client-side):** no COGS (Amazon-direct, no SellerCloud → CM=N/A) + $0 ad spend (awaiting Lectric ad-API access). Design `_lectric_native_DESIGN_v2_GROUNDED.md`; staged DDL committed clients gp-254 `ba55d4ad`. Remaining: CEO-report Navira-scoping, repo↔live reconciliation, PROD promotion. See [[project_lectric_ad_spend_gap]], [[project_lectric_cm_data_gap]] |
| [[GP-282]] | Amazon UK order-line dedup | To Do | **Not built** — UK branch missing SellerCloud anti-join → 1,154 dup lines / ~$137K (0.11%); inflates COGS once Option A backfills SC copies |
| [[GP-208]] | Inventory feed | Paused | Awaiting client Q&A; SellerCloud share staleness; Inventory/Purchasing tables in model but not consumer-validated |
| DAX Flags A/B | cross-platform guard + spend-inclusive profit | — | **Drafted (`pbi_ops/navira_dax_flags_A_B.md`), not applied** |

### ⬜ Not started / deferred
| Ticket | Title | Jira | Note |
|---|---|---|---|
| GP-227 | Historical backfill | QA ⚠️(not actually started) | Needed for real Tier-4 MMM. **Windsor-probe quantified 2026-06-17** (`_windsor_availability_probe.py`): primary Google account `389-957-4788` has data back to **2021-01-01** — **~$163K of pre-2024 Google spend (2021–2023) unpulled** (~$160K across all 6 accts; warehouse currently has Google from 2024-01 only = $212K of $373K available). Other 5 Google accts have genuine later creation dates (complete). **Meta: nothing to backfill** (accts began 2026-04; no older history). Deliver = Windsor re-pull Google `start_date=2021-01-01`. Detail: `aldc-launchpad/boot-prompts/navira-google-backfill-quantification.md` |
| GP-265 | Google spend into data | GEP QA | **Satisfied by GP-226** — close-out candidate |
| GP-252 | UK PPC pipeline config | Consulting/Design | **Satisfied by GP-257** — close-out candidate |
| GP-242 | SellerCloud SQL → Prefect block | QA | Prefect shelved — likely **won't-do** |
| GP-230/231 | Multi-tenant SP-API / Seller Central | Development/Design | backlog (Phase 1C) |
| GP-233 | Purchasing connector & COGS schema | Consulting/Design | backlog — **unblocks Lectric COGS** |
| GP-228/229/234/235 | TikTok / Email / SmartScout / Unstructured | Consulting/Design | Phase 1B+ backlog |

## ⚠️ Gaps / items to address
1. **Jira out of sync** — GP-281 shows *To Do/Consulting-Design* but is deployed+validated in TEST; GP-225 still *Development*; GP-227 shows *QA* but isn't started. Reconcile (comment; transition on Paul's OK).
2. **GP-282 ($137K dedup) genuinely unbuilt** and interacts with the COGS backfill (inflates COGS on UK SC copies) — sequence soon.
3. **DAX Flags A/B not applied** — without them a user can wrongly cross-platform `SUM(SALES_AMOUNT)` / omit Google+Meta spend from profit. Correctness risk on the exact model the CEO report reads.
4. **Everything beyond the 6 "Done" tickets is TEST-only.** Entire unified-marketing + COGS stack awaits a single gated PROD promotion (Navira sign-off + archive-partition reprocess for GP-259/281).
5. ~~**Redundant model** — `Data Model (Unified TEST Preview)` (`19cf5ef9`)~~ **RESOLVED 2026-06-19: deleted** (no report bound it; rollback = rebuild via `_build_test_model_unified`). GEP Test Models now has a single `Data Model`.

## Environment quick-ref
- **TEST:** `og35375.canada-central.azure` / `PAULRUSSELLADMIN`; DB `TEST_DG1_GEP`; share `PROD_DG1_GEP`. PBI model `66151728` (GEP Test Models).
- **PROD (share/grants only):** `wj66376` / `PROD_DG1_CORE_ADMIN`. Self-heal task `AMAZON.TASK_REGRANT_REPORT_ALL_ORDERS_SHARE` keeps the Amazon all-orders share stable ([[GP-PENDING-data-share-stability]]).

## Related
[[GP-225]] · [[GP-259]] · [[GP-281]] · [[GP-261]] · [[GP-277]] · [[GP-257]] · [[GP-254]] · [[GP-PENDING-missing-cogs-cost-history]] · [[GP-PENDING-data-share-stability]] · [[processes/distributed-workflow/active/navira/README|Navira workflow hub]]
