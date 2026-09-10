---
tags: [pattern, measurement, snowflake, power-bi, evidence]
aliases: ["is it in prod", "presence census", "silent orphan"]
sources:
  - ALDC-1192 platform census, 2026-09-10
  - GP-319 sweep, 2026-09-08 (ADVERTISEDASIN precedent)
  - clients GEP/development marketing_dim_platform.sql header
created: 2026-09-10
updated: 2026-09-10
---

# Three-layer presence census

**"Is X in production?" is three questions, not one, and answering the wrong one produces a
confident false negative about data we are already paying to land.**

## The three layers

| Layer | What it answers | How to measure |
|---|---|---|
| **L1 — deployed DDL** | Does the transformation *know about* X? | `GET_DDL` on the deployed object. **Not** the repo — the repo is a hypothesis about prod |
| **L2 — modelled data** | Can a client-facing visual *show* X? | `SELECT <axis>, COUNT(*), MIN/MAX(date) … GROUP BY 1` on the fact |
| **L3 — raw landing** | Is X *arriving*, whether or not anything reads it? | `INFORMATION_SCHEMA.TABLES` — name, `ROW_COUNT`, `LAST_ALTERED` |

⚠ **A platform absent at L2 is not evidence it is absent at L3, and vice versa.** They disagree
routinely, and each disagreement is a different finding.

## Why it matters — the silent orphan

Measured on [[GEP]] prod, 2026-09-10, answering "were Google and Meta accidentally promoted
alongside Sponsored Display?":

| | Sponsored Brands / Products | **Sponsored Display** | Google / Meta |
|---|---|---|---|
| L1 deployed DDL | ✅ | ❌ | ❌ |
| L2 modelled fact | ✅ current to that day | ❌ | ❌ |
| L3 raw landing | ✅ | ⭐ **~17,500 rows, written to that same day** | ❌ **zero objects** |

Three different verdicts from one question:

- **Google / Meta — genuinely absent.** Absent at every layer, including raw. Nothing to promote.
- **Sponsored Display — arriving and invisible.** Landing in prod raw, refreshed daily, exposed via
  `DATA_SHARE`, and **selected by nothing**. Reported as "not in prod" at L1/L2, which is true and
  deeply misleading: the data is there and paid for; only the fact arm is missing.
- **Nothing was accidentally promoted.** Deployed DDL matched the deploy branch exactly.

Had the census stopped at L1 or L2, the answer would have been "we don't have Sponsored Display in
production" — and the work would have been scoped as a connector request instead of a one-arm view
change.

## The mechanism that creates orphans

A hand-maintained fact whose branches are **named columns in a UNION** rather than data-driven. The
`clients` `GEP/development/marketing_dim_platform.sql` header states it plainly:

> *"adding an ad type upstream without editing this file produces a silent orphan, which is how
> Sponsored Display came to be unlabelled on the Platform axis in the first place."*

Upstream can start delivering a new category at any time. Nothing fails. Nothing alarms. The rows
land, the refresh stays green, and the category is simply never selected. See
[[connector-field-addition-forks-the-table]] for the sibling failure one layer up.

## When to run it

- Before answering any client or internal question of the form *"do we have X?"* / *"is X in prod?"*
- Before scoping a promotion — L3 decides whether the work is a view change or a data acquisition
- Before telling anyone a feed is dead — L3 separates **not arriving** from **arriving, unselected**
- When a repo branch and production disagree, or might

## Related

- [[vacuous-verification]] — a green gate that measured nothing
- [[power-bi]] — the consumer-side traps in the same measurement chain
- [[connector-field-addition-forks-the-table]] — how a new upstream field forks the landing table
- [[schema-dialect-drift]] — repo-vs-deployed divergence, same class
- [[data-share-pattern]] — L3 objects can be share-exposed while invisible to every model
