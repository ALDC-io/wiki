---
tags: [pattern, power-bi, enablement, documentation, navira, gep, deliverable]
aliases: [enablement guide, model guide, cookbook, model walkthrough, data model guide]
sources: [conversation 2026-08-13, GP-318 minutes item 8, aldc-launchpad docs/evidence/gp318]
created: 2026-08-13
updated: 2026-08-13
---

# Model enablement guide — the deliverable that makes a data model usable

A **model enablement guide** is a self-contained, designed HTML page that teaches a client's analysts
to use a Power BI semantic model correctly and confidently: what the tables are, how they relate,
which questions each can answer, **which it cannot**, and a cookbook of ready-made recipes for the
pivots people actually want.

Agreed with Paul 2026-08-13. Committed to the client in the [[GP-318]] meeting minutes (item 8:
*"guide documenting table relationships + example pivots"*) and carried as tail item **T1**. It will
be produced **at least four times**, so it is a pattern rather than a one-off:

| # | Subject | When | Depth |
|---|---|---|---|
| 1 | **Navira Daily Sales Model** (`66151728`) | ✅ **built 2026-08-13** | full |
| 2..n | **Marketing model — one per candidate design** | [[GP-319]] Phase 1/2 | thin, comparative (see §Sizing) |
| final | **Marketing model — the chosen design** | [[GP-319]] Phase 3 | full |

## Why it exists

Every defect on [[GP-318]] was, at bottom, a user being invited to ask a question the model could not
answer and being given a confident number instead of a refusal:

- **B1** — 21 of 22 visible fields containing the word "Spend" were wrong on a product axis, and 0
  were right. A user choosing by name chose wrongly.
- **The answerability guard** (`__ME Answerable`) — pivoting Marketing Efficiency on Product, Brand,
  Vendor, Customer, Location, Order, Warehouse, Campaign or Platform used to return the *portfolio
  total* against every member.
- **The margin scope defect** (item 3) — three measures summing three different row populations,
  side by side in one folder, with names that invite subtraction.

⭐ **So the load-bearing content of the guide is not the diagram — it is the boundary.** A guide that
documents only the happy paths teaches users to walk into exactly the walls this ticket spent weeks
removing. See §Non-negotiable content.

## Shape

Design reference Paul named: **an Amazon-console-style layout** — clean, dense, sectioned, with real
navigation rather than a wall of prose. Built as a single self-contained HTML page.

1. **Orientation** — what the model is for, in three sentences; the grain of each fact table.
2. **Architecture diagram** — all tables, with the **new** tables, columns and relationships
   highlighted against the pre-existing ones. Relationship direction and cardinality must be visible,
   because that is what determines answerability.
3. **Table reference** — per table: grain, what one row means, which dimensions can slice it, date
   coverage, and known coverage gaps.
4. **Measure reference** — per measure: definition in words, **the population it sums**, its scope
   caveats, and which measures it is safe to combine with. (Measure descriptions are already being
   written into the models themselves — the guide should be generated from them, not re-typed.)
5. **The boundary** — §Non-negotiable content below.
6. **Cookbook** — templated recipes for common pivots and reports (see §Cookbook).
7. **Glossary** — every term that has more than one meaning in this estate: TACoS vs ACoS vs MER,
   gross vs net, attributed vs allocated vs measured spend, contribution margin vs margin after ad
   spend vs net margin loaded.

## Non-negotiable content — the boundary

These are what make the guide worth more than a screenshot tour. Each is drawn from a real defect:

- **"What this model cannot answer."** A first-class section, not an appendix. E.g. the Daily model
  cannot attribute Google/Meta spend to a marketplace, cannot report UK ad spend at order level
  (PROD holds no UK profile), and cannot report ad spend per product from the Marketing Efficiency
  table at all.
- **Which dimensions each table can be sliced by** — and what happens when you use one it cannot.
  On the Daily model that is now a BLANK, by design. Say so, so a blank reads as a refusal rather
  than as zero.
- **ZERO vs NOT-RECORDED vs NOT-VISIBLE.** The single most repeated failure in this estate. The
  warehouse holds ad instrumentation for **four** marketplaces only; the other ~26 carry sales with
  no ad measurement. A blank there is a measurement gap, not a media-buying fact — Mexico's
  $152,869.82 of margin is the worked example.
- **Every figure's basis** — `MEASURED | DERIVED | ASSUMED | PROXY`. UK's USD figure is DERIVED
  (GBP frozen at 1.330663 since 2026-03-03).
- **Known-stale mechanisms** — anything that goes wrong quietly and would not announce itself.

## Cookbook

Templated, ready-to-run recipes for the pivots people actually want, each with: the question in plain
language, the fields to drag, the expected shape of the answer, and **the trap it avoids**.

⚠ **Delivery constraint, decide up front.** If the guide is published as an Artifact, the viewer
sandbox **blocks any download the page starts itself** — `<a download>`, blob/data hrefs and
script-driven saves are all inert for viewers. So "downloadable cookbook" resolves to one of:

- **(a) Copy-paste inline** — recipes rendered in the page as steps + DAX, with a copy button. Works
  everywhere, nothing to host, nothing to go stale separately. *Default choice.*
- **(b) A real file hosted elsewhere** — .xlsx/.pbix in the repo or SharePoint, linked from the page.
  Use when the client wants a working workbook rather than instructions.

Do not promise (b) and ship (a) by accident.

## Sizing — do not build n full guides before the design is chosen

For [[GP-319]], each candidate marketing-model design is to get a walkthrough so Nicholas can choose
between them. ⚠ **A full guide per option is mostly work that gets thrown away.** Recommended split,
unless Paul says otherwise:

- **Per candidate (thin, comparative):** one page each — the shape, what it makes easy, what it makes
  hard, the boundary it draws, and *one* worked pivot. Enough to choose between them.
- **For the chosen design (full):** the complete treatment above.

If the walkthroughs exist specifically to *drive* the choice, thin-and-comparable beats deep-and-
incomparable: three guides in one format can be read side by side, three deep guides cannot.

## Reusable assets that already exist

Do not start from scratch:

- `aldc-launchpad/pbi_ops/_build_metric_dictionary.py` — generates a measure dictionary from the
  live models.
- `aldc-launchpad/pbi_ops/_build_*_report.py` — existing builders that already emit branded HTML.
- `docs/evidence/gp318/GP318-DEMO-PIVOTS-2026-08-12.xlsx` and `GP318-QA-WORKBOOK-2026-08-12.xlsx` —
  6 tabs of worked pivots, already validated; the seed of the cookbook.
- The measure **descriptions now written into both models** — generate the measure reference from
  TOM rather than re-typing it, so the guide cannot drift from the model.

## Rules

- **Generate from the live model wherever possible.** A hand-typed field list is stale the day a
  measure is renamed. The models are the source of truth; the guide is a rendering of them.
- **Sequence after the model stops moving.** Writing the Daily-model guide before the [[GP-318]] tail
  is wrapped would document field names, visibility and guards that are still changing. This is why
  the guide is scheduled after the tail wrap, not alongside it.
- **Client-shareable subset only** — curated, labelled artifacts, never raw internal dumps.
- **No client comms without Paul's explicit go**, this guide included.

## What the first build actually taught

Produced for the Daily Sales Model on 2026-08-13 from `pbi_ops/_gp318_guide_extract.py` →
`_guide_reach_matrix.py` → `_build_guide.py`.

- ⭐ **The architecture diagram was the wrong figure.** A picture of 21 tables says less than the
  field list. The load-bearing figure is a **reach map**: which dimensions can slice which fact, and
  what happens when one cannot. That is the single thing a field list cannot show and every
  [[GP-318]] defect came from.
- ⭐ **Do not infer the reach map — measure it.** The first draft built it from the relationship
  graph and asserted two falsehoods: an edge that does not exist, and reach derived from *direct*
  relationships only, which understates transitive routes. See [[answerability-guard]] §Detecting.
- ⭐ **Do not invent measure descriptions.** 70 of 122 visible measures had none. The guide prints
  "not documented" and counts the gap in the page, so it gets fixed in the **model** — where the
  descriptions also become Power BI tooltips — rather than papered over in a document.
- The boundary section writes itself once the guards exist: it is generated from the deployed guard
  expressions, so the document cannot claim an enforcement the model does not have.

## Related

[[GP-318]] · [[GP-319]] · [[consumer-layer-validation]] · [[power-bi]] · [[pbi-xmla-automation]] ·
[[cross-channel-marketing-attribution]] · [[GEP]]
