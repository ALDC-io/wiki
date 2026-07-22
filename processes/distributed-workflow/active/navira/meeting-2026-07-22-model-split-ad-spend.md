---
tags: [meeting, gep, navira, navira-roadmap, pbi, data-model, ad-spend, agency, attribution, scope]
aliases: [Navira 2026-07-22 Meeting, Model Split + Ad Spend Meeting, Navira Data Model Split Meeting]
sources: [client meeting minutes 2026-07-22 (Lori Beck / Heather Tabor / Justin Shuster)]
created: 2026-07-22
updated: 2026-07-22
---

# Navira Meeting — Data-Model Split + Cross-Channel Ad Spend (2026-07-22)

Client review (Lori Beck, Heather Tabor, Justin Shuster + Paul) confirming the **two-model split** and defining
the **cross-channel ad-spend + agency** requirements for the Daily *Sales* Model, plus the **campaign-attribution
gap** that is paused pending Nicholas. This page is the scope-anchor for the follow-on build. Execution boot:
`aldc-launchpad/boot-prompts/navira-daily-model-marketing-efficiency-addback.md`. Hub: [[navira-roadmap-status]].

## ⭐ Key takeaways
- **Two models, by design:** a cleaned **Daily *Sales* Model** (business-friendly names, agency, + ad-spend
  columns) and a separate **Marketing Model** (`2d8587b5`, full marketing views) so marketing detail doesn't
  clutter sales users. (GP-291 already made Daily `66151728` sales-only; this **adds a minimal ad-spend layer back**.)
- **Amazon UK ads confirmed flowing into the Marketing Model**, but showed **$0 in Heather's test workbook** →
  Paul to verify the test workbook refresh/access and report back. See the DQ-001 reframe below.
- **Cross-channel attribution (Google/Meta → Amazon at ASIN level) is nontrivial** — blocked on **campaign
  tagging**. Needs Nicholas to define identifiers/tagging; **paused** until his input.
- **Priority + timeline:** confirm UK ad-data visibility in the test workbook **and** deliver the two separate
  models (business/sales + agency) by **end of week (Fri 2026-07-24)**.

## 🎯 Action items
- **Justin Shuster** — brief **Nicholas** before the next meeting on the tagging/attribution gap so he can propose
  identifiers for mapping Google/Meta campaigns → Amazon sales; review Nicholas's marketing dashboard via Heather's
  login (act as technical bridge).
- **Paul Russell** — verify the test workbook; confirm whether Amazon UK ad orders flow into the test model; report
  findings to the team. *(→ Gate 0 of the boot prompt.)*
- **Heather Tabor** — forward Justin the marketing-dashboard login + the downloaded-workbook link.
- **Lori Beck** — answer Heather on the UK Amazon ad work; prioritise review; deliver the separate data models by EOW.

## 📋 Decisions / scope for the Daily Sales Model
1. **Include cross-channel ad-spend columns** — **UK + Google + Meta**, USD-consolidated, **by ad type**
   (Sponsored Products / Sponsored Brand / Sponsored Display) → users pull **total ad spend per SKU** and **spend
   by ad type**. Source = `Marketing Efficiency` (+ `Marketing Efficiency Product` for SKU grain). Ad-type spend
   already exists in the warehouse (SP/SB via activity branches; SD integrated 2026-06-25).
2. **Agency data flows into the Daily model.** Sales-by-agency already works (GP-254/GP-291 kept the `Agency` dim +
   Agency↔Order Line edge); the add-back makes **ad spend agency-sliceable** too.
3. **Business-friendly column names** — remove raw Snowflake CAPS/table names in the sales model (= **GP-292**).
4. Marketing views/metrics stay in the **Marketing Model** only (not in the Daily model).

> **⚠ Reframe — DQ-001 (do not conflate):** the client's "Amazon UK = $0" symptom is on the **"Actual − Cost −
> Advertising"** measure, which is **Amazon settlement *fees*** from `Order Line` (`*_ADVERTISING_FEE_CONSOLIDATED`),
> **Amazon-only — NOT** the marketing ad-spend table. So UK=$0 there reflects **UK Order-Line P&L**, and **adding
> `Marketing Efficiency` will not change that measure.** Fixing/relabelling it is **GP-292 / DQ-001** work. The
> cross-channel ad-*spend* visibility ask (decision 1) is a separate add. UK *sales* are in Order Line (~2,413
> lines), so a hard $0 points at a stale/wrong-dataset workbook or a tiny CY2026 slice — verify (Gate 0).

## 🚧 Attribution — PAUSED (out of scope for this build)
Reliable ASIN-level attribution of Google/Meta spend to Amazon sales **requires campaign tagging that doesn't yet
exist**. **Nicholas** is the technical owner and will propose an approach; **Justin** briefs him first; feedback
expected at the **Fri 2026-07-24** discussion. **Do not build attribution logic** — surface spend totals only, no
ASIN-level channel-attribution claim. Tracked: [[GP-295]] (BLOCKED, campaigns/tagging) + [[GP-287]] (Amazon
Attribution feed). A future "campaign tagging column on sales records" is a later item.

## Risks
- **Refresh/access discrepancy** may be why UK Amazon ads read $0 in the test model — check the workbook's dataset
  binding + refresh date (the client downloaded from `https://eclipse-test.aldc.io/report/51/`; the validated live
  daily download per the hub is `app_report` 56 — **resolve which report 51 is**).
- **Inaccurate attribution** if tagging isn't implemented — cannot claim precise channel→Amazon sale attribution at
  ASIN level until Nicholas's tagging lands.

## People
- **Lori Beck** — EI lead; pushing EOW delivery. · **Heather Tabor** — testing/validation, owns dashboard login.
- **Justin Shuster** — technical bridge to Nicholas. · **Nicholas** — Navira technical owner for campaign
  attribution/tagging; built a Navira-side marketing dashboard (Justin to review).

## See also
- [[navira-roadmap-status]] · [[GP-292]] · [[GP-295]] · [[GP-287]] · [[GP-257]] · [[GP-291]]
- Boot: `aldc-launchpad/boot-prompts/navira-daily-model-marketing-efficiency-addback.md`
- DQ register: `aldc-launchpad/navira-dashboard-redesign/reports/navira-data-issue-register.md`
