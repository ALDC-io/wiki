---
tags: [pattern, power-bi, dax, data-modelling, navira, gep, correctness]
aliases: [answerability guard, __ME Answerable, inert axis, silent grand total, guard measure, exact-zero blanking, NOT-RECORDED vs ZERO]
sources: [GP-318 T5/T6/T7 2026-08-13, GP-319 2026-08-24, GP-329 2026-08-28, GP-318 sales-model measurement pass 2026-09-02, aldc-launchpad docs/evidence/gp318 + gp319 + gp329-widen-impact.md + navira-sales-repair, conversation 2026-08-13, conversation 2026-08-24, conversation 2026-08-28, conversation 2026-09-02]
created: 2026-08-13
updated: 2026-09-02
---

# Answerability guard — making a model refuse questions it cannot answer

A semantic model will happily answer a question it has no route to. Slice a measure by a dimension
the fact cannot reach and the filter simply does not propagate: the measure returns the **portfolio
total against every member**, looking entirely credible.

On [[GP-318]] this was the crux defect and it appeared **four separate times**, on four different
tables, over two models. It is not a Navira quirk — it is what star schemas do by default.

> Slicing Navira's ad spend by brand printed **$2,858,931.54** against every brand.
> Slicing sales by campaign printed **$128,757,189.40** against every campaign.
> Both looked like data. Neither was.

## The three verdicts, and why the middle one is the dangerous one

For any (measure, axis) pair there are three outcomes, and a test that only asks "did it error?"
cannot tell them apart:

| Verdict | What happened | Reading |
|---|---|---|
| **SPLITS** | the figure genuinely varies across members | answerable |
| **BLANK** | the model refused | answerable, and honestly refused |
| ⛔ **INERT** | the filter did not propagate; the grand total prints against every member | **the defect** |

⭐ **INERT is invisible to every ordinary check.** The visual paints, the query succeeds, the number
is plausible and the totals reconcile. It is only detectable by asking whether the figure *changes*
across the axis.

## Detecting it

Ask whether the measure **splits across the axis**, not what one member returns:

```dax
EVALUATE TOPN(60, SUMMARIZECOLUMNS('Dim'[Col], "v", [Measure]), [v], DESC)
```

* no non-blank rows → **BLANK**
* every row equals the grand total → **INERT**
* otherwise → **SPLITS**

⚠ **Do not test by filtering to one member.** Picking an arbitrary member gets a SKU with no sales
and reports BLANK — "Product cannot slice sales" — which is a false negative. This exact mistake was
made twice on GP-318, once in the guide's reach map and once in a test battery.

## The guard — and why one operator is not enough

```dax
__Fact Answerable =
IF (
    ISCROSSFILTERED ( 'Brand' ) || ISCROSSFILTERED ( 'Campaign' ) || …
    || ISFILTERED ( 'Order Line' ) || ISFILTERED ( 'Marketing Efficiency Product' ) || …,
    0, 1
)
```

Every visible measure on the fact is then wrapped: `IF ( [__Fact Answerable] = 1, <body> )`.

⭐ **Two operators, because they catch different things and each fails at the other's job:**

| Operator | True when | Use for |
|---|---|---|
| `ISCROSSFILTERED` | the table is filtered **directly or indirectly** | unreachable **dimensions** — catches indirect routes such as filtering Vendor to reach Product |
| `ISFILTERED` | the table is filtered **directly only** | unreachable **facts that a valid axis crossfilters** — Order Line, a per-product fact, anything hanging off Date |

**The mistake to avoid:** naming a fact that hangs off `Date` under `ISCROSSFILTERED` blanks **every
ordinary Date pivot**, because filtering Date crossfilters every fact related to it. The original
Navira guard left ten such tables unguarded for exactly this reason — a structural limit, not an
oversight. `ISFILTERED` closes them safely.

## What must NOT be guarded

* ⭐ **Control / mode-selector tables.** A disconnected table whose members are modes
  (`Consolidation` = Transaction/Consolidated, `Periodicity` = Current/MTD/YoY, a what-if floor) is
  inert **by design** — the fact is genuinely invariant to it. Guarding one blanks every figure the
  moment someone touches a slicer. Tell them apart structurally: control tables have **no
  relationships** and a handful of mode-like members.
  ⚠ And re-measure per fact: on Navira, `Consolidation` and `Periodicity` are inert against the
  marketing facts but genuinely **split** sales.
* **Measure-holder and empty tables** — no pivotable column, so they cannot be dragged onto an axis.
  Naming them adds DAX risk for no benefit.
* **A fact's own self-group columns.** `Marketing Efficiency Product[ASIN]` works without a
  relationship and is the table's entire purpose. A guard must never name its own table.
* ⭐ **Measures on a fact that already carries its own guard.** Double-wrapping produces a measure
  blanked by two boundaries at once. On GP-318 this blanked per-product spend on its own ASIN axis.

## Choosing which measures to wrap

Only measures that actually read the fact. Compute a **transitive closure** over measure
expressions — client-facing measures are usually thin wrappers, so a one-level scan misses most of
them.

⭐ **Exclude the guard helpers from the closure, both as seeds and as bridges.** `__ME Answerable`
*contains* `ISFILTERED('Order Line')`, so a naive scan reads the helper itself as "this measure reads
Order Line" and then cascades through it into every measure that references it. On GP-318 this pulled
30 marketing measures into a sales guard and shipped a regression.

## Testing it — the battery that actually catches things

Both halves are required, and each has a way of quietly evaporating:

**BLANKS** — a filter on an unreachable axis must return BLANK, for a **real** member as well as a
fabricated one. Real members matter more: a fabricated ASIN returning the portfolio total is
obviously absurd; a real brand returning it is the number that reaches a client deck.

**UNCHANGED** — valid axes, control tables, and any *other* fact's measures must be untouched.

Four ways this battery lies, all observed on GP-318 in one day:

1. ⭐ **Comparing a value to itself.** If the reference is the same measure, every UNCHANGED case
   passes for free. Define the **unguarded body in the same query** and compare against that.
2. ⭐ **Rebuilding cases from current state.** After the guard is applied nothing is exposed, so
   cases regenerated post-apply vanish — one battery shrank from 50 cases to 24 and still reported
   ALL GREEN. **Replay the candidate battery verbatim.**
3. ⭐ **Vacuous passes.** An UNCHANGED case where the reference is itself blank proves nothing. Flag
   them, and choose members **by measure value** so the case is load-bearing.
4. ⭐ **No cross-fact cases.** Nothing asserted that a sales guard leaves marketing measures alone,
   so a double-guard regression passed 28/28.

Then gate the deploy: `--apply` should refuse unless the saved candidate run is green **and** tested
a byte-identical expression.

## The diagnostic — a blank must explain itself

Ship a visible companion measure so a blank reads as a refusal rather than missing data:

```dax
Sales figures — Why Blank? =
IF ( <the same condition>,
     "BLANK — sales cannot be split by the field you have used. Order Line reaches
      Brand, Customer, Date, Location, Marketplace, Order, Product and Vendor…",
     "OK — figure is valid on this axis." )
```

⭐ **Generate it from the shipped helper expression.** On GP-318 a pass widened a guard from 9 tables
to 16 and left the diagnostic testing the original nine — so users blanked by the seven new ones were
told *"OK — figure is valid on this axis."* The explanation contradicted the thing it explains.

## ⛔ A measure-level guard cannot close a column-level hole

**Learned GP-319, 2026-08-24, and it is the limit of this whole pattern.** After guarding all three
visible measures on `Marketing Efficiency Product` in the Marketing model `2d8587b5` and verifying
they returned BLANK on `Product[Master SKU]`, the trap was **still live**:

```
SUM('Marketing Efficiency Product'[Grounded Ad Spend (USD)])  by Product[Master SKU]
  -> 2,452,729.7999  repeated down every row, unchanged by the guard
```

The table's raw numeric columns are **visible**, so a PivotTable user drags the column instead of the
measure, Excel aggregates it implicitly, and the guarded measure is never evaluated. For an Excel
consumer — where the field list *is* the interface — the column sits directly beneath `ASIN` and
`Product Name`, which is exactly where someone building a product pivot reaches.

**So a guard is only complete when paired with hiding the raw columns behind it.** Hidden columns
still resolve for existing workbook references (established GP-318), so hiding is additive for
consumers who already use them — but it needs a bound-report scan first.

⭐ **Verify at the column, not just the measure.** A verification pass that only probes measures will
report a clean result on a model that still lies.

## Derive the refuse-list from the relationship graph, never by hand

A hand-written refuse-list is wrong by omission — the standing defect in this idiom. On GP-319 the
list was generated from the model's own relationships using a rule reverse-engineered from the
shipped `__ME Answerable`:

> a table with a **direct edge to `Date` or `Agency`** is crossfiltered whenever the user filters by
> date or entity — both legitimate axes — so it must be tested with **`ISFILTERED`** (direct only).
> Every other table gets **`ISCROSSFILTERED`** (broader).

⭐ **The rule was asserted to reproduce `__ME Answerable`'s own split exactly before being reused.**
If a derived rule cannot reproduce the guard you already trust, the rule is wrong and nothing should
be generated from it. Recipe: `aldc-launchpad/pbi_ops/_gp319_mep_guard_apply.py::build_guard()`,
survey + assertion in `_gp319_guard_survey.py`.

Measured coverage on `2d8587b5`, 2026-08-24 (`pbi_ops/_gp319_guard_coverage.py`, re-runnable):
58 of 59 visible `Marketing Efficiency` measures guarded. The one exception is
`Marketing Efficiency — Why Blank?` — the diagnostic explainer, which **must** stay unguarded
because its job is to answer when everything else is blank.

## ⚠ Global parameter tables are deliberately NOT in the refuse-list

`Consolidation`, `Periodicity`, `MAP Min ASINs Floor` are what-if / parameter tables, not axes.
Refusing on them would blank the measure in **any report that merely has that slicer set** — a
visible regression on a client surface, traded for a trap never measured on them. Record the
exclusion as a stated decision in the script, or a later pass will "fix" it.

## Two verification checks, not one

A guard that blanks *everything* passes a "does it return BLANK on the bad axis?" check perfectly and
is a **deletion**, not a fix. Every guard pass therefore needs both:

1. **BLANK on the axis it cannot answer** — the fix
2. **still VARIES on its own grain and on Date** — proof it is a guard and not a delete

Plus the standard no-regression evidence: totals unchanged to the cent, table/relationship counts
unchanged, measure count up by exactly the number of guards added.

## Where this has been applied

| Model | Fact | Guard |
|---|---|---|
| Navira Daily Sales `66151728` | `Marketing Efficiency` | `__ME Answerable`, 16 tables |
| Navira Daily Sales `66151728` | `Marketing Efficiency Product` | `__MEP Answerable`, 17 tables |
| Navira Daily Sales `66151728` | `Order Line` | `__Sales Answerable`, 9 tables, 38 measures |
| Navira Marketing `2d8587b5` | `Marketing Efficiency` | 20 tables, 58 of 59 visible measures, + 17 hidden columns |
| Navira Marketing `2d8587b5` | `Marketing Efficiency Product` | `__MEP Answerable`, 23 tables, 3 measures — **GP-319, 2026-08-24**. ⚠ raw columns still unhidden |
| Navira Daily Sales `66151728` | `Google Ad Spend (Product)` | `__GASP Answerable` — ⚠ `Google SKU Resolution %` is visible and unguarded |
| Navira Marketing `2d8587b5` | `Sales Measures` | ⛔ **NONE — 38 of 40 unguarded, and 3 axes measured INERT** (GP-319, 2026-08-25) |
| Navira Marketing `2d8587b5` | `Marketing Measures` | ⛔ **NONE — 0 of 24 guarded, 2 axes measured INERT** |

## ⭐ Static coverage is not behaviour, and a single-member axis is not a defect

Two rules earned on 2026-08-25, both of which change a published count.

**1. Counting guard references tells you what CAN inherit blankness, not what returns.** A static DAX
read of the Marketing Model reports `Marketing Measures` 0/24 guarded and `Sales Measures` 2/40 —
true, and it does not tell you which axes actually misbehave. Only a behavioural probe does.
*Propagation, not adjacency — and behaviour decides.*

**2. An axis with exactly ONE member correctly equals the grand total.** Calling that inert is a
false positive. The first behavioural run on `2d8587b5` reported **nine** inert combinations; four
were single-member axes (`Marketplace[Channel Name]`, and `Agency[Entity Code]` on three facts).
Inertness is only demonstrated when a **real split was available and ignored**, so the verdict needs
`rows > 1`. Without that rule the finding would have overstated by 80%.

The three verdicts a reach probe must separate:

| verdict | meaning | how it reads to a user |
|---|---|---|
| `SPLITS` | the figure genuinely varies | correct |
| `BLANK` | the guard refused the axis | honest — a refusal |
| ⛔ `INERT` | the filter did not propagate | **a confident number that is the portfolio total** |

⭐ **`INERT` is why "does it error?" is not a sufficient test.** An inert axis neither errors nor
blanks; it looks perfectly healthy. Instrument: `aldc-launchpad/pbi_ops/_gp319_guide_reach_matrix.py`
(read-only, `--daily` retargets the sibling model, negative + positive controls mandatory).

Scripts: `aldc-launchpad/pbi_ops/_gp318_t5_*`, `_gp318_t6_*`, `_gp318_t7_*` — each takes
`--apply` / `--live` / `--delete`.

## ⭐ The guard blinds the measurer — read the unguarded column to tell ZERO from NOT-RECORDED

The companion convention to the answerability guard is **exact-zero blanking**: a pivot stores `0`,
not `NULL`, where a platform is not instrumented on a marketplace, so the measure blanks an exact
zero rather than publish `$0.00` as a measurement we do not have.

```dax
Spend - Amazon Sponsored Display =
IF ( [__ME Answerable] = 1,
    VAR v = SUM ( 'Marketing Efficiency'[Amazon Ad Spend — Sponsored Display (USD)] )
    RETURN IF ( COALESCE ( v, 0 ) = 0, BLANK (), v )   -- an exact 0 is NOT-RECORDED
)
```

That is correct **for the reader** and a trap **for the analyst**. The guard maps three distinct
states onto one blank, and the measure can no longer tell you which you are looking at:

| underlying state | guarded measure | what it actually means |
|---|---|---|
| no rows for this member | `BLANK` | **NOT-VISIBLE** — the member never reaches the fact |
| rows exist, column stores exact `0` | `BLANK` | **NOT-RECORDED** — instrumented, nothing to record |
| rows exist, column is genuinely `0.00` | `BLANK` | **ZERO** — a real measured nothing |
| the axis cannot propagate | `BLANK` | **refusal** — the answerability guard fired |

⇒ **Never conclude a verdict from a guarded measure. Read the underlying column, unguarded, and
count the rows in the same query.** The discriminating shape:

```dax
EVALUATE
SUMMARIZECOLUMNS(
  'Marketing Efficiency'[Marketplace],
  "raw_sd",  SUM('Marketing Efficiency'[Amazon Ad Spend — Sponsored Display (USD)]),
  "raw_sp",  SUM('Marketing Efficiency'[Amazon Ad Spend — Sponsored Products (USD)]),
  "me_rows", COUNTROWS('Marketing Efficiency')          -- ⭐ the row count is the discriminator
)
```

On [[GP-329]] this separated two blanks that looked identical and were not. Amazon UK returned
`BLANK` for Sponsored Display from the guarded measure. Unguarded: **407 rows present**, `raw_sd`
stored as **exact `0.0`**, `raw_sp` `6,633.04` ⇒ UK is instrumented and **Sponsored-Products-only**
— NOT-RECORDED, not absent, not zero. Amazon Brazil on the same axis returned `BLANK` from *both*
the measure and the column, with rows present ⇒ a different verdict entirely.

That distinction decided a real number: it is why the UK/Sponsored-Display overlap in the
margin-impact calculation is **genuinely $0.00** and no dollar was double-counted. Had the guarded
blank been read as "unknown, assume some overlap", the delta would have been hedged; had it been
read as "absent", UK Sponsored Display would have been proposed as deliverable when the data says
UK does not run it.

**Rule:** guards exist to protect the *reader* from a false zero. When you are the *measurer*, go
under them — and never publish `ZERO`, `NOT-RECORDED`, `NOT-VISIBLE` or `NOT-RETAINED` as if they
were the same finding.

## ⭐ 2026-09-02 — the column-level hole was already documented, and the Daily model still had 11

**This is a process finding as much as a technical one.** A measurement pass over the Daily Sales
Model `66151728` re-derived "a measure-level guard cannot close a column-level hole" from first
principles, reading Heather Tabor's specimen workbook's `pivotCache` XML to prove her nine value
fields were **columns** dragged as Excel implicit `Sum of`, not measures.

**That mechanism was already on this page**, written from GP-319 on **2026-08-24** — eight days
earlier. The grounding sweep at session start did not reach this page, so the finding was rebuilt
instead of retrieved. ⚠ **When a defect's mechanism feels novel, check this page before writing the
probe** — the section above it was the answer, and it named the remedy (hide the raw columns) too.

What the pass *did* add is the measurement the earlier entry lacked, on the **other** model:

| | |
|---|---|
| numeric fact columns examined on `66151728` | **138** |
| still client-visible **and** repeating their grand total across `Product[Master SKU]` | **11** |
| worst offender | `Budget[Forecast Gross Sales]` = **$95,016,664.29** on all 15,483 Master SKUs |
| Heather's own nine columns | already `IsHidden` — her exact route is closed |

So the GP-319 remedy was applied to the Marketing Model and **never carried across to the Daily
model**. Two of the 11 are *percentage* columns being summed (19,877.7 and 26,436.6), which needs
`SummarizeBy = None` rather than hiding.

⭐ **A date-correct repeated total is more dangerous than an absurd one.** Heather's repeated
$1,003,331.05 was not the column grand total ($87,547,935.40) — it was the **correct week-31
total**, wrong only on the product split. It survives every sanity check a human would apply. An
obviously silly number gets questioned; this one gets published.

### Refinement to the single-member rule above: check populated members, not just members

The rule at *"an axis with exactly ONE member correctly equals the grand total"* needs a sibling
clause. A first classifier pass flagged all **16** `Marketplace Measures` as inert on
`Marketplace[Marketplace Name]`. The axis has **30** members, so `rows > 1` passed — but only
**1** of the 30 carries any `Traffic Activity` row, and a single *populated* member equals the grand
total by the same arithmetic necessity.

```
members = 30   nonblank = 1   distinct_nonblank = 1   equals_grand_total = 1   ->  NOT a defect
```

**Rule: inertness requires `nonblank > 1`, not merely `members > 1`.** Verdict name used:
`ONE_POPULATED_MEMBER`. Without it the pass would have overstated by 12 pairs and 3 measures
(substantive offenders 247 → **235**, measures 41 → **38**).

⭐ **And a guard is value-neutral at the grand total** — `IF([__X Answerable]=1, <expr>)` with no
filter applied evaluates the guard to 1 and returns `<expr>` unchanged. So "the DAX differs because
one model is guarded" can **never** explain a difference in an *unfiltered* total. A TEST↔PROD
parity run labelled 26 measures `INTENTIONAL_CHANGE (DAX differs)` on exactly that reasoning and
was wrong to; the gaps were data, not logic.

Instruments (read-only, negative + positive controls, no `--apply` path in any):
`aldc-launchpad/pbi_ops/_sales_repair_axis_probe.py` (measure × axis, full population),
`_sales_repair_classify.py` (offline re-classification), `_sales_repair_heather_reproduce.py`
(carries `assert_no_repeated_total()`, the deterministic regression — it **FAILS with 11 failures**
today, which is what proves it can fail).

## Related

[[GP-318]] · [[GP-319]] · [[GP-329]] · [[model-enablement-guide]] · [[consumer-layer-validation]] ·
[[power-bi]] · [[pbi-xmla-automation]] · [[vacuous-verification]]
