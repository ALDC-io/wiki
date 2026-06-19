---
tags: [ticket, gep, navira, navira-roadmap, roadmap, status, hub, pbi, cogs, marketing, map-violators]
aliases: [Navira Roadmap Status, Navira Completion Status, Navira Roadmap Hub]
sources: [aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md, aldc-launchpad/boot-prompts/navira-roadmap-review-and-ceo-report.md]
created: 2026-06-16
updated: 2026-06-19
---

# Navira Roadmap — Completion Status Hub

> **Single source of truth for "what's done, where (PROD vs UAT), and what's left"** on the Navira/[[GEP]] roadmap. Reconciles Jira status vs actual implementation. Compiled 2026-06-16 from Jira (`navira-roadmap` label, cloudId `239c1bf0-93f4-4201-95fe-ab73ce4a6eff`), the per-ticket wiki pages, the live model, and the [[processes/distributed-workflow/active/navira/README|Navira workflow hub]]. Master plan: `aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md`.

## CEO-facing report

**`Navira — Executive Overview`** — **7-page** exec report (Lectric agency tab + Proposed-Dashboards page added 2026-06-17), deployed to **GEP Test Models**, report `888d72c2-3854-4d00-ae84-43e5c4797950`, bound to the live UAT `Data Model` (`66151728-f00f-4a08-af91-6687de5f13dc`). Pages: (1) Executive Summary, (2) Data Ingested & Available, **(3) Agency Integration — Lectric Bikes**, (4) New Analytics Features, (5) Data Quality & Coverage Wins, (6) Roadmap Status, **(7) Proposed Dashboards** (D1–D8 buildable-now matrix). Every figure is live from the model (SQL == DAX validated). MAP Violators is referenced (separate model), not embedded. Builder: `aldc-launchpad/pbi_ops/_build_navira_ceo_report.py`. **Modeling note:** `Sales Measures` are NOT agency-aware (return the full company total regardless of the Agency filter) because the `Agency` dim relates only to the 3 marketing tables and `Order Line` has no entity key (Lectric isn't even in `Order Line`); only `Marketing Efficiency` measures respect the `Agency` dim → any agency-scoped visual must use Marketing Efficiency measures only. **Scoped fix (2026-06-17): `aldc-launchpad/warehouse_ops/_lectric_native_sales_fact_PLAN.md`** — Option C native agency-aware sales fact (conform Lectric into shared dims + union into the Order Line source view + add `Order Line[ENTITY_CODE]→Agency` relationship). Adds an `ENTITY_ROLE` dim attribute (`HOUSE`=Navira / `AGENCY`=Lectric+future) enabling **"All Agencies"** (agency subset, excludes Navira) and **"Company Total"** (grand total) rollups. Not started; evidence-gated; D1–D5 logged (D5 resolved). Lectric margin stays blank until COGS lands regardless.

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

## TEST↔PROD parity + client-readiness pass (2026-06-19)

**TEST↔PROD model diff (TOM, `pbi_ops/_compare_models.py`) — every difference maps to a roadmap ticket.** TEST is a superset of PROD; **GP-199 + GP-200 are present in both** (data-level within shared tables, no structural delta). TEST-ahead = in-flight roadmap (not yet promoted): 5 tables (`Agency`/`Marketing Efficiency`/`Marketing Efficiency Product`/`Google Brand Grounding`/`Google Product Grounding`) + ~49 measures (GP-277 efficiency + Flag A/B), `Marketing Activity[ENTITY_CODE]` + Agency rels (GP-225), `Order Line` return cols (GP-259). Two items where TEST trailed PROD were the only anomalies:
- **GP-256 `Actual - Sales - Return Rate %`** (a *Done/PROD* deliverable) was missing from TEST → **fixed 2026-06-19**: added to TEST `Sales Measures` identical to PROD (`DIVIDE([Actual - Sales - Returns (Quantity)],[Actual - Sales - Gross (Quantity)],0)`, fmt `0.00%`), validates **4.20%** (131,683/3,132,563). Builder `pbi_ops/_integrate_marketing_efficiency.py`-style via XmlaClient; rollback = delete the measure.
- **`Traffic Activity[MARKETPLACE_KEY]` + its Marketplace relationship** (PROD-only) — still missing in TEST (test's Traffic source view lacks the column). **Open** — warehouse-side, deferred (low client priority). See boot prompt.

**Relationship health check (`pbi_ops/_wire_islands.py`, TOM):** all relationships are clean Many:One single-direction — **no inactive, many-to-many, bidirectional, or ambiguous (duplicate-path)** relationships. Fixed 3 visible **island** tables (no relationships → ignored every slicer):
- `Google Brand Grounding[ENTITY_CODE]→Agency` and `Google Product Grounding[ENTITY_CODE]→Agency` — now agency-aware (validated: Brand Grounding = Navira $89,400, Lectric absent). Date NOT joined (monthly `ACTIVITY_MONTH` grain, no daily key).
- `Marketing Activity[CAMPAIGN_KEY]→Campaign` (key unique 144,641/144,641) — **enables campaign-level marketing breakdown** that was impossible before (validated; no-regression on MA totals; ~$223K spend lands in a blank-campaign bucket = Google/Meta/unmapped, expected). Rollback: drop relationships `Relationship 2/3/4`.

**Remaining client-readiness items (→ boot prompt / next session):**
1. **Sales Measures not agency-aware** (the big one) — agency-sliced Sales/Orders show the full company total; only Marketing Efficiency respects Agency. Fix = GP-254 Option C native agency sales fact (`warehouse_ops/_lectric_native_sales_fact_PLAN.md`), not started.
2. **`Traffic Activity[MARKETPLACE_KEY]`** parity (warehouse-side).
3. **Redundant dataset** `Data Model (Unified TEST Preview)` (`19cf5ef9`) still in GEP Test Models — client sees TWO "Data Model" datasets; hide/remove (confirm no dependency first).
4. **Google Grounding date integration** deferred (monthly grain).

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
| [[GP-257]] | Amazon UK ad spend | QA | TEST end-to-end | 733 rows/96 days/£3,075; 0 regression US/CA |
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
| [[GP-254]] | Lectric agency | QA | **Source-verified 2026-06-17 (PBI model == `WAREHOUSE_SOURCE.SALES_FCT_LECTRIC_AMAZON_ORDERLINE`, exact):** $2,520,823 gross · 4,206 orders · 4,800 units · $599 AOV · **25 ASINs / 28 SKUs** · **Amazon US only** (ship-country US; no .ca/.mx/.br data present) · ~2 yrs (2024-06-01→2026-06-03). **No COGS** (source feed has no cost column) → CM=100% artifact. **$0 ad spend** (Amazon/Google/Meta all 0) — blocker is **client-side: Navira awaiting advertising-API access FROM Lectric** (confirmed 2026-06-17). Native agency-fact integration scoped (see CEO-report modeling note → `_lectric_native_sales_fact_PLAN.md`). cross-DB view; raw refresh_token in repo. See [[project_lectric_ad_spend_gap]], [[project_lectric_cm_data_gap]] |
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
5. **Redundant model** — `Data Model (Unified TEST Preview)` (`19cf5ef9`, refresh 06-12) is superseded by the in-place repoint of the live `Data Model`. Cleanup candidate (left in place for now).

## Environment quick-ref
- **TEST:** `og35375.canada-central.azure` / `PAULRUSSELLADMIN`; DB `TEST_DG1_GEP`; share `PROD_DG1_GEP`. PBI model `66151728` (GEP Test Models).
- **PROD (share/grants only):** `wj66376` / `PROD_DG1_CORE_ADMIN`. Self-heal task `AMAZON.TASK_REGRANT_REPORT_ALL_ORDERS_SHARE` keeps the Amazon all-orders share stable ([[GP-PENDING-data-share-stability]]).

## Related
[[GP-225]] · [[GP-259]] · [[GP-281]] · [[GP-261]] · [[GP-277]] · [[GP-257]] · [[GP-254]] · [[GP-PENDING-missing-cogs-cost-history]] · [[GP-PENDING-data-share-stability]] · [[processes/distributed-workflow/active/navira/README|Navira workflow hub]]
