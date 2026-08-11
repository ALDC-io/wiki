---
tags: [pattern, snowflake, warehouse, eclipse, data-quality, gotcha, build-order, gep, navira]
aliases: [circular dependency build order, T-1 dimension, stale denominator, self-referencing view, zero-copy vintage capture, table vs live view test]
sources: [aldc-launchpad/docs/evidence/gp322.md, GP-322 inquest 2026-08-10]
created: 2026-08-10
updated: 2026-08-10
---

# Circular dependency broken by build order — the T-1 input defect

A **self-referencing dependency** in a warehouse (object A reads B, B reads A) cannot be resolved by a
scheduler; it can only be *broken* by materialisation order. Whichever object builds first necessarily
reads a **24-hour-old copy** of the other. If a calculation depends on both sides agreeing — a share, a
ratio, an allocation, any conservation identity — it is **silently wrong on its most recent rows, on
every single build, forever**, while looking perfect in settled history.

Found the hard way on [[GP-322]] (Navira Amazon ad-cost allocation reading **3.6× campaign spend** in
the current month). Generalised here because nothing about it is Navira-specific.

## The shape

```
WAREHOUSE.SALES_FCT_COST  ──reads──▶  WAREHOUSE.SALES_DIM_ORDER
        ▲                                        │
        └──────────────── reads ─────────────────┘
```

The dimension appended rows read back out of the fact (`ATTRIBUTION_TYPE = 'No Match'` — see
[[gep-unknown-order-placeholders]]). So Snowflake had to pick an order, and it picked:

```
06:00:01  SALES_DIM_ORDER_BASE   <- the calculation's CONSUMER side   T-0 fresh
06:02:32  SALES_FCT_COST         <- the allocation materialises HERE
06:02:48  SALES_DIM_ORDER        <- the calculation's DENOMINATOR     T-1 STALE
```

**Sixteen seconds.** The allocation spread each day's ad cost across order lines using a *denominator*
built from yesterday's order list and a *numerator* built from today's. Orders that arrived in the
intervening 24h were in the numerator and absent from the denominator, so the shares summed to far more
than 1. On the newest day the denominator held **5.1%** of the sales it should have.

## Why it hides for months

- **It self-heals.** The whole history rebuilds nightly, so each day corrects as its orders land —
  substantially within 3 days, completely by ~21. GP-322: 18 divergent days out of **1,318**; nothing
  older than 21 days wrong at all; **98.7%** of the error in the newest 3 days.
- **All-time totals look fine.** +4.1% overall. Only the monthly or current-period cut exposes it.
- **A reconciliation measured across closed months "proves" health.** A 99.81%/26-month agreement was
  quoted as reassurance; it was dominated by the months that agree.
- **Nothing changed on the day it was noticed.** Build texts were byte-identical for 25 consecutive
  days. There is no regression to find in a diff, because it has fired since the object was deployed.

## ⚠ Do not describe the affected window as a calendar date

It is **age-relative**. The band always sits immediately behind whatever build you are looking at. On
GP-322 the first non-conserved day in the snapshot was 2026-07-22 — which was simply **age 19 from that
snapshot**, not an onset. Two investigators independently read it as "the defect started 22 July"; both
withdrew it. Correct phrasing:

> *"The affected window is always the ~N days preceding the current build. In the snapshot examined
> (<date>) that window began <date>."*

A materialisation-order cycle **has no start date.** Stating one is a false date claim.

## ⭐ Two reusable techniques this produced

### 1. Table vs live view — a one-query test for any build-order defect
Where a table is a plain materialisation of a view (`CREATE OR REPLACE TABLE x AS SELECT * FROM v`),
**query the table and the view side by side.** Same logic, different instants:

| | result |
|---|---|
| the **table** (built 06:02) | 26,710.87 / 100,009.52 |
| the **live view** (inputs now aligned) | **5,530.34 / 3,716.24** |
| campaign spend (the truth) | 5,522.55 / 3,559.93 |

Settled days agree between the two — that is the negative control. **This test needs no theory and no
reconstruction**, and on GP-322 it found the mechanism after three theory-driven reconstructions had
failed. Reach for it *first* whenever a materialised object is wrong but its logic looks right.

⚠ **Check the view actually reads the sources and not the table.** On GP-322 the sibling test on
`SALES_FCT_ORDERLINE` returned table == view at **$0.00 in every month**, which looks like a clean bill
of health and means nothing: that view reads the *cost table*, not the cost view. A uniform result is a
broken instrument until proven otherwise.

### 2. Zero-copy clone to capture a vintage when time travel is 0-day
Daily `CREATE OR REPLACE` **resets time travel**, so `AT(OFFSET => …)` fails and the exact input a build
consumed is destroyed by the next build. GP-322 lost 20 of 20 time-travel attempts across 10 objects and
had to *reconstruct* the stale input from connector row-level history stamps.

The cheap fix, if you catch it in time:

```sql
CREATE TABLE <sandbox>.SALES_DIM_ORDER_ASOF_<stamp> CLONE WAREHOUSE.SALES_DIM_ORDER;
```

Instant, metadata-only, no compute, and it pins exactly one vintage of micro-partitions.

**The timing insight worth remembering:** if the dimension is rebuilt *after* the fact, then between
those two moments the dimension's **current** content is precisely what **tomorrow's** fact build will
read. So you can capture the pairing any time that day — you do not have to sit on the 06:0x window.

⚠ **What this does and does not buy you.** It makes the *settled* days' arithmetic computable
immediately — GP-322 confirmed three predicted figures to the dollar the same afternoon. It does **not**
let you compute the newest day, because that day's inflation depends on the *order population growing*
overnight relative to the pinned dimension. Holding both sides fixed removes the very asymmetry under
test. Learned by getting it wrong: a pinned-dim substitution returned results identical to the fixed
version on all five days, because the pinned dim and the fresh one were written two minutes apart.

## The fix, and why the obvious one is worse

**Repoint the dependent side at the object the other side already reads**, so both read one object and
the cycle is gone. On GP-322 that was two join sites moved from `SALES_DIM_ORDER` to
`SALES_DIM_ORDER_BASE` — measured: 42 of 44 months change by **exactly $0.00**, schema parity exact,
no real rows lost.

**Reordering the build is the tempting alternative and it is defective:**
- It often **cannot** be done — the dimension reads the fact, so there is no valid order.
- It degenerates into *running the build twice*, which **is not provably a fixed point**: pass 2 changes
  which placeholder rows exist, which changes the dimension, which could change pass 3.
- It leaves the cycle in place to re-break the next time someone reorders the pipeline.

**"The logic is correct, so changing the SQL is a wrong-layer fix" is a trap.** The logic is only
*conditionally* correct — correct if two inputs are read at the same instant, which its own dependency
graph guarantees they are not. A view whose correctness depends on the execution order of the job that
materialises it is defective **at the SQL layer**, because that is where the self-reference lives.

## How to detect this class proactively

1. Look for **self-reference**: does any dimension read a fact that reads that dimension? `GET_DDL` the
   dimension and grep for the fact's name. Cheap, and there is no other way to see it.
2. For every conservation identity in the warehouse, check the **two sides read the same object**. A
   share whose numerator and denominator come from differently-named objects is a latent bug even if
   both are correct today.
3. Compare **materialised table against its own source view**, per day, for the trailing 30 days.
4. Where retention is 0-day on a load-bearing input, **clone a vintage daily** so the next incident is
   measurable rather than reconstructed.

## See Also

- [[GP-322]] — the incident, full evidence and remedy
- [[gep-unknown-order-placeholders]] — the `UNK_` No-Match rows that close this particular cycle
- [[navira-daily-model-lineage]] — where the affected objects sit in Navira's lineage
- [[data-pipeline-flow]] · [[star-schema-convention]]
- [[gep-snowflake-pbi-deployment]] — deploy mechanics (secure views, `COPY GRANTS`, ownership)
