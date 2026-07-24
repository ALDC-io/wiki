---
tags: [architecture, navira, gep, power-bi, metrics, dictionary, glossary, dq-001, dq-005, gp-292, gp-290]
aliases: [Navira Metric Dictionary, Navira Metric Contract, navira_metric_dictionary, GP-292 name map, GP-290 glossary source]
sources: [aldc-launchpad/pbi_ops/navira_metric_dictionary.json, aldc-launchpad/pbi_ops/_build_metric_dictionary.py, aldc-launchpad/pbi_ops/_gp291_baselines/Data_Model_66151728_20260723T025351Z.tmsl.json, aldc-launchpad/pbi_ops/_gp291_baselines/Marketing_Model_2d8587b5_20260723T025351Z.tmsl.json, aldc-launchpad/.claude/plans/peppy-strolling-dewdrop.md]
created: 2026-07-23
updated: 2026-07-24
---

# Navira Canonical Metric / Column Dictionary

> **Phase B APPLIED to both live TEST models (2026-07-24, commit `9b06091`).** The dictionary's renames are now
> live on Daily `66151728` (42 column renames + 4 DQ-001 relabels + 5 hides) and Marketing `2d8587b5` (110 + 6 +
> 8). **0 visible raw ALL-CAPS columns remain** on either model. Applied via `pbi_ops/_gp292_apply_renames.py`
> (by-name TOM, in-transaction reference-rewrite, atomic + `RefreshType.Calculate`); validated at model/DAX +
> report-binding layers (all measures evaluate; SP+SB+SD==Spend-Amazon exact; Navira CM==total CM $37.97M,
> Lectric CM BLANK; COGS coverage 77.83%). **Scope applied = columns + the 6 DQ-001 relabels only**; cosmetic
> measure renames excluded; **TACOS formula rebase held** for client sign-off. Report "New Data Showcase"
> rebound (ACOS); embedded "Data Model" + UK Orders unaffected; CEO `888d72c2` not in the workspace (stale id).
> Rollback: `_gp292_rollback.py` + `…063756Z` TMSL backups. **Remaining gate: rendered-visual validation +
> Navira sign-off** (GP-301 finishing session). Evidence: `aldc-launchpad/docs/evidence/gp292/gp292-phase-b.md`.
>
> **Follow-ups 2026-07-24 (commit `5259d57`, branch `feature/gp298-brinno-comparison-columns` — ⚠ branch split
> from the `9b06091` Phase-B commit on `feature/lectric-scheduled-connector`, reconcile):** (a) **Agency filter
> confirmed** on Daily — `Order Line` slices Navira $126.05M / Lectric $2.74M / total $128.79M (GP-254 Option C
> live). (b) **`Customer Cohort` HIDDEN on the Daily sales model** (table + 3 measures; Marketing keeps it) to
> declutter — `_gp292_hide_cohort_daily.py`. (c) **Eclipse-2.1 hidden-object behaviour verified in `core_api`:**
> the builder field picker (`v1/route_dataset.py` getInfo L1216/1229/1259) filters `isHidden==False` so hidden
> objects leave the picker, but runtime `model_query` uses explicit locators + does NOT filter hidden → existing
> dashboards keep being fed. Build cohort on the Marketing model; Daily needs an Eclipse schema re-sync to
> propagate (watch the `accountsynchronize` crash bug → `[[reference core_api sync bug]]`). (d) `BRAND`→`Brand`
> + `CLASSIFICATION`→`Classification` renamed (commit `5477666`) — **0 non-acronym ALL-CAPS columns remain**.
> (e) **Eclipse builder re-sync DEFERRED → bug [[GP-302]]** (assigned Paul, sprint S8): the sanctioned
> `dataset_synchronize` crashes (`model_get_cardinality` None → TypeError, `route_dataset.py:1280`); client
> download unaffected, only the internal builder picker is stale. (f) **Eclipse dashboard binding check
> DONE + CLEAN** (2026-07-24, commit `08973a0`): scanned all 96 eclipse-2.1 Explorer docs in the `core` Cosmos;
> one hit — "Universe View" dataView referenced the renamed `Periodicity[Periodicity Name]` → rebound in Cosmos
> to `[Time Period]` (backup `_gp292_universe_view_ROLLBACK.json`); re-scan clean.
> **✅ GP-292 TRANSITIONED TO DONE 2026-07-24** (TEST-accepted; PROD out of scope; rendered sign-off accepted at
> close). Split follow-ups: **[[GP-302]]** (Eclipse builder re-sync crash bug, assigned Paul, S8) + **[[GP-303]]**
> (TACOS *formula* rebase → spend ÷ total sales; client-gated on Lori's "advertising cost" answer; the relabel
> already shipped). Full revisit/rollback pointers in the GP-292 close-out comment.

Single source of truth for the **business-friendly name + definition of every user-visible column/measure**
across the two Navira Power BI models (**Daily "Data Model"** `66151728` + **Marketing Model** `2d8587b5`) and
**every metric the Navira marketing dashboard displays** ([[navira-marketing-dashboard]]). Built so the two
metric-legibility tickets consume one artifact instead of authoring names + definitions twice: **[[GP-292]]**
(PBI friendly names + DQ-001 relabel + TACOS rebase) and **[[GP-290]]** (dashboard glossary — its
`metrics-glossary.ts` and the `pbiEquivalent` column resolve from here). This is the "metric contract" the
[[navira-data-issue-register|data-issue register]]'s QA strategy called for.

## Where it lives
- **`aldc-launchpad/pbi_ops/navira_metric_dictionary.json`** — canonical, machine-readable (both lanes read it).
- **`aldc-launchpad/pbi_ops/navira_metric_dictionary.md`** — generated human view / **client sign-off sheet**.
- **`aldc-launchpad/pbi_ops/_build_metric_dictionary.py`** — the authoring builder (Python data → JSON + MD +
  self-verification). **Edit the builder, not the outputs.** Re-run: `python pbi_ops/_build_metric_dictionary.py`.
- Committed on branch `feature/lectric-scheduled-connector`, commit `e82f601` (2026-07-23). Phase A of the plan
  `aldc-launchpad/.claude/plans/peppy-strolling-dewdrop.md`. **DRAFT** — pending client (Lori) sign-off.

## Shape
**445 entries** (223 columns, 196 measures, 26 dashboard metrics). Each entry:
`concept_key · friendly_display_name · kind · physical{pbi_daily, pbi_marketing, dashboard_key, snowflake_source}
· definition · formula · source_fields · scope · tier · caveats · models_visible · rename_action · rename_risk
· client_signoff · dq_ref`. Shared concepts (MER, ROAS, ACoS, TACoS, Spend, Contribution Margin…) get **one**
`friendly_display_name` used across all three surfaces, so divergence is structurally impossible. The builder
self-verifies: every user-visible column/measure on both live models is covered; `concept_key`s unique.

## Grounding correction (why the fresh pull mattered)
Built on **fresh read-only live TMSL dumps dated 2026-07-23** (`…_20260723T025351Z`), NOT the earlier
`…_201157Z` baselines — those **predated GP-226's PBI work** (a stale-pointer trap the boot fell into). The
live pull confirmed the current truth, updating [[navira-daily-model-lineage]]:
- **Daily `66151728` = 35 tables** — `Marketing Efficiency` (+ `Marketing Efficiency Product`) are **re-added**
  (GP-226), so the Daily model is **no longer sales-only**.
- The **Amazon ad-type split** `SPEND_USD_AMAZON_SP/SB/SD` (+ the 3 `Spend - Amazon Sponsored …` measures) is
  live on **both** models.
- **Per-model visibility differs:** on Daily the analytics measures (MER, TACoS %, Platform ROAS, Calibrated
  ROAS, Attributed Sales, QA flags, Revenue Share) are **hidden** — only the `Spend` + `Contribution Margin`
  folders show (GP-226 kept Daily spend+margin-focused). On the Marketing model all 55 are visible. The
  dictionary records this per entry via `models_visible`.

## Rename guardrails (for GP-292)
- **214 columns → caption rename** (prefer PBI display captions over renaming source columns — a renamed
  source column breaks any measure/relationship/partition-M that references it). 223 are already friendly
  (`rename_action: none`). Each rename entry carries a `rename_risk` note.
- **Phase B (the actual TOM `Name` writes) is gated** on client sign-off + must run against the current
  2026-07-23 dump + update report bindings in lockstep. Not started here.

## DQ-001 — the semantic relabel/rebase (encoded as `rename-source`, 6 measures)
- `Actual - Cost - Advertising` (+ Brand/No-Sale/Product parts) = Amazon **settlement advertising fees** off
  Order Line, Amazon-only → relabel **"Amazon Advertising Cost"**.
- `ACOS - Advertising Cost of Sale` → **"Amazon ACOS"** (Amazon-only by design; a blended ACoS is
  mathematically invalid — attributed sales double-count).
- `TACOS - Total Cost of Advertising` (Marketing Measures, fee-based) → **rebase to ad spend ÷ total sales**.
- **Cross-surface TACoS note:** the dashboard's TACoS is *already* `spend ÷ total sales` (correct), and the
  Marketing Efficiency `TACoS %` measure already equals `Marketing Cost %` (= spend ÷ gross). So the rebase
  **closes a real divergence** rather than creating one. See [[cross-channel-marketing-attribution]] for the
  metric-tier law (never sum platform-attributed sales across channels).

## DQ-005 ≡ "Flag A"
The [[navira-data-issue-register]]'s `DQ-005` tag **does not exist in the dashboard code** — the code names
that exact caveat **"Flag A" / design-spec §7.1**. Verdict **MOOT**, with structural proof:
`warehouse.ts::mapPlatforms()` writes `totalSales` only on the Amazon channel row per entity (Google/Meta rows
carry `totalSales:0`), and `page.tsx` L245-249 forces the `"mer"` headline in warehouse mode — so **no blended
cross-channel ACoS/ROAS is ever rendered**. GP-290 should encode "no blended adSales ratio is ever rendered"
as a checked invariant. The PBI equivalent guardrail is the hidden `Attributed Sales (platform-bound)` measure
(Flag A) + `Ad Spend Integrity Check` (Flag B) on Marketing Efficiency.

## Metric hierarchy (governs the whole model)
**Contribution Margin > MER (blended) > Platform ROAS.** Tiers: 0 measured · 1 platform self-reported
(single-channel only) · 2 MER · 2.5 calibrated · 3 grounded (Amazon ASIN / Google SKU). Full tier + caveat set
per metric is in the dictionary; narrative in `aldc-launchpad/pbi_ops/navira_metrics_guide.md`.

## See Also
- [[navira-daily-model-lineage]] — per-table source map of the Daily model `66151728`.
- [[cross-channel-marketing-attribution]] — the tiered measurement law + the `MARKETING_EFFICIENCY` view.
- [[navira-roadmap-status]] — Navira roadmap completion hub.
- [[navira-marketing-dashboard]] — the Next.js dashboard (GP-290's surface).
- [[GP-292]] · [[GP-290]] — the two tickets this dictionary serves.
