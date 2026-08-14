---
tags: [pattern, power-bi, dax, data-modelling, navira, gep, correctness]
aliases: [answerability guard, __ME Answerable, inert axis, silent grand total, guard measure]
sources: [GP-318 T5/T6/T7 2026-08-13, aldc-launchpad docs/evidence/gp318, conversation 2026-08-13]
created: 2026-08-13
updated: 2026-08-13
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

## Where this has been applied

| Model | Fact | Guard |
|---|---|---|
| Navira Daily Sales `66151728` | `Marketing Efficiency` | `__ME Answerable`, 16 tables |
| Navira Daily Sales `66151728` | `Marketing Efficiency Product` | `__MEP Answerable`, 17 tables |
| Navira Daily Sales `66151728` | `Order Line` | `__Sales Answerable`, 9 tables, 38 measures |
| Navira Marketing `2d8587b5` | `Marketing Efficiency` | 20 tables, 58 measures, + 17 hidden columns |

Scripts: `aldc-launchpad/pbi_ops/_gp318_t5_*`, `_gp318_t6_*`, `_gp318_t7_*` — each takes
`--apply` / `--live` / `--delete`.

## Related

[[GP-318]] · [[model-enablement-guide]] · [[consumer-layer-validation]] · [[power-bi]] ·
[[pbi-xmla-automation]]
