---
tags: [ticket, gep, navira, navira-roadmap, roadmap, status, hub, pbi, cogs, marketing, map-violators]
aliases: [Navira Roadmap Status, Navira Completion Status, Navira Roadmap Hub]
sources: [aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md, aldc-launchpad/boot-prompts/navira-roadmap-review-and-ceo-report.md]
created: 2026-06-16
updated: 2026-06-16
---

# Navira Roadmap — Completion Status Hub

> **Single source of truth for "what's done, where (PROD vs UAT), and what's left"** on the Navira/[[GEP]] roadmap. Reconciles Jira status vs actual implementation. Compiled 2026-06-16 from Jira (`navira-roadmap` label, cloudId `239c1bf0-93f4-4201-95fe-ab73ce4a6eff`), the per-ticket wiki pages, the live model, and the [[processes/distributed-workflow/active/navira/README|Navira workflow hub]]. Master plan: `aldc-launchpad/boot-prompts/navira-roadmap-master-plan.md`.

## CEO-facing report

**`Navira — Executive Overview`** — 5-page exec report deployed 2026-06-16 to **GEP Test Models**, report `888d72c2-3854-4d00-ae84-43e5c4797950`, bound to the live UAT `Data Model` (`66151728-f00f-4a08-af91-6687de5f13dc`). Pages: (1) Executive Summary, (2) Data Ingested & Available, (3) New Analytics Features, (4) Data Quality & Coverage Wins, (5) Roadmap Status. Every figure is live from the model (SQL == DAX validated). MAP Violators is referenced (separate model), not embedded. Builder: `aldc-launchpad/pbi_ops/_build_navira_ceo_report.py`.

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
| [[GP-254]] | Lectric agency | QA | Sales in TEST ($2.52M/4,206 orders) but **no COGS → CM N/A** (CM=100% artifact); cross-DB view; raw refresh_token in repo. See [[project_lectric_cm_data_gap]] |
| [[GP-282]] | Amazon UK order-line dedup | To Do | **Not built** — UK branch missing SellerCloud anti-join → 1,154 dup lines / ~$137K (0.11%); inflates COGS once Option A backfills SC copies |
| [[GP-208]] | Inventory feed | Paused | Awaiting client Q&A; SellerCloud share staleness; Inventory/Purchasing tables in model but not consumer-validated |
| DAX Flags A/B | cross-platform guard + spend-inclusive profit | — | **Drafted (`pbi_ops/navira_dax_flags_A_B.md`), not applied** |

### ⬜ Not started / deferred
| Ticket | Title | Jira | Note |
|---|---|---|---|
| GP-227 | Historical backfill | QA ⚠️(not actually started) | Needed for real Tier-4 MMM |
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
