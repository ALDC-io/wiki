---
tags: [concept, pattern, schema-versioning, snowflake, connector, prefect, core-api, testing]
aliases: [schema dialect drift, dtype drift, table fragmentation, versioned table forking, virgin schema test]
sources: [prefect-connectors/connector/base_connector.py, prefect-connectors/orchestrator/stage_scripts/snowflake_ops.py, core_api/v1/route_warehouse.py]
created: 2026-08-14
updated: 2026-08-14
---

# Schema Dialect Drift — when declared types and stored types are spelled differently

**A writer declares a column type in one vocabulary; the warehouse reports it back in another. Any
code that compares the two without folding the alias table concludes "schema changed" on every
single write — and forks a new versioned table each time.** The symptom is table *fragmentation*:
one logical dataset spread across `TABLE_1 … TABLE_48`, each holding a slice, each looking healthy
in isolation.

This has now bitten ALDC **three times in two independent codebases**, twice by engineers who had
each correctly diagnosed the mechanism and still shipped an incomplete fix. The durable lesson is
therefore not about types at all — see [[#The lesson]].

## The mechanism

Two vocabularies meet at a schema comparison:

| Side | Vocabulary | Example spellings |
|---|---|---|
| **Writer** (connector / session) | pandas-derived, lowercase | `bigint`, `datetime`, `int`, `varchar`, `float` |
| **Warehouse** (Snowflake, reporting back) | canonical, uppercase | `NUMBER`, `TIMESTAMP_NTZ`, `TEXT`, `FLOAT` |

`base_connector._get_column_list` emits `int -> "bigint"` and `datetime -> "datetime"`. Snowflake
reports those same columns as `NUMBER` and `TIMESTAMP_NTZ`. A normalizer that does not fold both
directions sees a mismatch on **every partition**, concludes the schema is new, and creates
`{table}_N`.

A table with a `DATE` column forks **unconditionally** — the `datetime` ↔ `TIMESTAMP_NTZ` pair never
matches. That is why `exchangeratesapi` fragmented on every run while other connectors only drifted
occasionally.

## The three occurrences

| When | Where | What was fixed | What was missed |
|---|---|---|---|
| **2026-05-27** | [[prefect-connectors]] `6308783` "normalize data types in schema matching" (Paul) | Introduced `_normalize_dtype` with a 5-alias map: `VARCHAR→TEXT`, `INT→NUMBER`, `INTEGER→NUMBER`, `FLOAT`, `BOOLEAN` | **`BIGINT` and `DATETIME`** — the two the writer actually emits. Bug survived **11 weeks** |
| **2026-06-02** | [[core_api]] `route_warehouse.py` Fix B ([[GP-277]]) | Dtype-*tolerant* matching — same column-NAME set + PK routes to the existing table, reconciling by widening `boolean<bigint<float<varchar`. Collapsed 24 real Navira Google versions to 1 | Nothing on the dtype axis — but note it solved the *same root cause* in a *different repo*, and neither fix knew about the other |
| **2026-08-14** | [[prefect-connectors]] session 1–2 | A metadata-column mismatch (4 columns the session declared that the table did not) — **real and measured** | Not the only mismatch. A virgin schema still produced **48 fragments** afterwards. The dtype dialect gap was still there |

> **Contradiction worth noting:** [[GP-277]] treats dtype drift as something to *tolerate and widen*;
> `prefect-connectors` treats it as something to *normalize away before comparing*. Both are valid,
> but they are different strategies for one problem in one company. If the two ever have to agree on
> a table, reconcile the strategies deliberately rather than letting whichever writes last win.

## The lesson

⭐ **A mismatch you can measure is not evidence that you found every mismatch.**

Both failed attempts were *competent*. Each engineer identified the real mechanism, measured a real
discrepancy, fixed it, and stopped — because a measured cause feels like *the* cause. It is only
*a* cause. Diagnosis by reading is how both attempts stalled.

Related failure in the same family: **a mutation test can itself be vacuous.** When the dtype folding
was removed to prove the guard, all 58 tests stayed **green** — the only dtype test covered metadata
columns whose `int` mapping already worked. The test existed, ran, and asserted nothing about the
defect. Write the failing case **first**, confirm **RED**, then write the fix. (See also
[[inquest-bug-resolution]], which encodes the same rule.)

## The only test that settles it

**Run into a virgin landing schema and count the fragments.**

```sql
SHOW TABLES IN SCHEMA <DB>.<CONNECTOR>__<SUFFIX>;
-- 48 objects  = broken
--  1 object   = fixed
```

Measured progression on `exchangeratesapi`, same connector, same method, **only the image changed**:

| Landing schema | After | Fragments |
|---|---|---|
| `EXCHANGE_RATES__PR` | (baseline) | **48** |
| `EXCHANGE_RATES__PR2` | metadata-column fix | **48** |
| `EXCHANGE_RATES__PR3` | dtype folding fix | **1** ✅ |

Nothing short of that number counts as proof. A virgin schema is essential — re-running into a
schema that already holds fragments cannot distinguish "stopped forking" from "forked into tables
that already existed".

**If fragmentation reappears, do not reason about which alias might be missing.** Query the stored
schema, build the field ids exactly the way `find_matching_schema` does, and diff them against what
the session declares. The answer is always a specific pair of spellings, and it takes one query to
find.

## Prevention checklist

- [ ] Fold **both** directions of the alias table, not just the spellings you happen to emit today
- [ ] Enumerate the writer's actual output (`_get_column_list`) rather than assuming its vocabulary
- [ ] Cover **every** emitted type in the dtype test, not the one that already worked
- [ ] Mutation-test the guard: remove the folding, confirm RED
- [ ] Verify with a **virgin-schema fragment count**, not by reading the diff
- [ ] Remember the fix ships in the **container image** — it needs merge → CI rebuild → new run, not
      a process restart. See [[prefect-connector-deployment]]

## See Also

- [[prefect-connectors]] — where the 2026-05-27 and 2026-08-14 occurrences live
- [[GP-277]] — the [[core_api]] sibling fix (dtype-*tolerant* strategy, widen rather than normalize)
- [[connector-development-standards]] — where PartitionScheme/MergeScheme choices interact with this
- [[orchestrator]] — the parity harness that measures the result
- [[inquest-bug-resolution]] — "mutation-test the regression test"; "enumerate rather than sample"
- [[Snowflake]] — the canonical-name side of the comparison
