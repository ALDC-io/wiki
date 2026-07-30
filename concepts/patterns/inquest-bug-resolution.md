---
tags: [concept, pattern, ai, claude-code, skill, bug, incident, multi-agent, adversarial, engineering-standard]
aliases: [Inquest, /inquest, Inquest Bug Resolution, Council of Five, Adversarial Bug Resolution]
sources: []
created: 2026-07-30
updated: 2026-07-30
---

# Inquest — adversarial multi-lens bug resolution

Claude Code skill. Sibling to [[conclave-pr-review]]: conclave reviews a **change**, inquest
resolves a **defect**. A council of five investigators, each locked to a different layer of the
stack, hunting the same bug blind to each other — then a synthesiser that **re-runs every
root-cause claim before a human reads it**.

Tracked source: `skills/inquest-SKILL.md` (see [[README]] for the mirror contract).

> An inquest does not ask who to blame. It establishes cause of death, on evidence, and says so plainly.

## Why it exists

The failure mode it is built against is **a confident fix at the wrong layer**. That is worse than
no answer, because a wrong answer gets deployed. Precedent: a GEP "Missing COGs" fix was deployed
and reverted after the target object was inferred from matching values.

## What distinguishes it from conclave

| | conclave | inquest |
|---|---|---|
| The artifact | **given** — a diff | **unknown** — must be located and proven |
| Bias to fight | reviewer wants to find something | investigator wants their hypothesis to be right |
| Ends at | a posted review | a **deployed, proven** fix — or a proven non-bug |

## The three gates — before convening anything

1. **Freshness** — you are looking at what is actually deployed on the surface the reporter used.
   Trunk is frequently not `main` (Eclipse trunks on `eclipse-2.1`).
2. **Environment** — prove your own tooling works before reporting something else is broken.
3. **⭐ Reproduction** — *no hypothesis work begins until the bug reproduces, or is proven not to.*
   "Not reproducible" is a first-class verdict.

## The five layers

`observer` symptom & scope · `surface` consumer/render · `substrate` data & query ·
`pathway` code path · `devil` falsifier & no-change advocate.

`devil` is not a formality. Its highest-value output is the **"valid finding, dangerous remedy"**
category — a correct diagnosis whose obvious fix causes damage.

## The mechanics that pay out most

- **Discriminating test with both outcomes predicted BEFORE it runs.** If both branches predict the
  same observation it is not evidence, it is a vibe.
- **Never infer the target from matching values.** Two objects can hold identical values and still
  be different objects.
- **Killing your own hypothesis is a success.** A member that confirms its assignment every time
  bought you nothing.
- **Severity and confidence are separate axes** — that is what lets the synthesiser catch a
  member's error.
- **Enumerate the candidate set rather than sampling it.** "All 269 measures, 0 unguarded" is a
  conclusion; "I checked five" is a hint.
- **Negative control** — the case where your hypothesis predicts *no* difference. Stronger than ten
  more positive cases, because it rules out over-correction.
- **Mutation-test the regression test** — revert the fix, prove it goes RED.

## Reference run — [[GP-311]] (Navira SKU Profitability over-counted Orders)

First convened on GP-309/GP-310 (2026-07-29); GP-311 is the run that produced the durable lessons.

**Outcome:** root cause proven and fixed at the fact layer in both TEST and PROD, verified at the
rendered surface. **The council caught six factual errors in the pre-existing case file before
anything reached a partner** — including a safety warning that cited a column hard-coded to `$0.00`,
which the partner would have checked, found empty, and then dismissed the warning entirely.

Three findings worth remembering:

1. **The reasoning was wrong even though the verdict was right.** The app was believed to read the
   Power BI model; reading its public bundle proved it posts **raw SQL** and never touches Power BI.
   So the measure-level fix that had "already fixed this" could never have reached it.
2. **The guard was at the consumption layer for a fact-layer defect** — one DAX measure, while
   `LINE_STATUS` was filtered nowhere downstream of the fact builds. Every SQL consumer kept the bug
   and always had. That is why the same defect surfaced twice, five weeks apart, through different
   consumers.
3. **A verification that asserts only an absence can pass by destroying the population.** See the
   revision log below — this cost $423K of ad spend in a rolled-back attempt.

## Revision log

Each entry records the incident that drove the change, so the skill's evolution is auditable and can
feed a self-improvement loop. **Add an entry whenever `inquest-SKILL.md` changes.**

### 2026-07-30 — three additions after the GP-311 near-miss (374 lines)

Driven by a real deployed-and-rolled-back regression during GP-311. The durable fix nulled a
placeholder `ORDER_ID`; the **first attempt patched the wrong site in the view** — a `UNION ALL`
branch that fed `INNER JOIN … ON a.ORDER_ID = b.ORDER_ID`. `NULL = NULL` never matches, so it
**deleted 471,264 rows and $423,072.95 of advertising spend**. Detected, rolled back from a
live-captured DDL, verified restored.

| Added | Where | Why |
|---|---|---|
| *"Smallest means smallest blast radius, not the most local-looking edit"* + check what joins on a column before changing its values | Phase 3 step 2 | The skill's existing "smallest change" heuristic actively pointed at the wrong site: editing one union branch *looks* tighter than editing the shared output projection, and is far more dangerous. |
| *"Mutation-testing is necessary but NOT sufficient"* — an absence assertion can be satisfied by destroying the population, and still goes RED without the fix | Phase 3 step 3 | The bad check (`unknown_rows_with_id == 0`) printed "applied and verified" over the data loss, **and would have survived mutation-testing**. Step 5's "row counts stable" is the countermeasure, so it is now bound to step 3 as a precondition rather than a later formality. |
| Two anti-pattern rows | Anti-patterns | "Assert only that the bad thing is absent" and "Change a value without checking what joins on it". |

**Rejected in the same review, recorded so it is not re-proposed:** a Snowflake
`SECURE VIEW` / `COPY GRANTS` / owner-role redeploy recipe. It is estate-specific SQL mechanics,
already covered by Phase 4's environment-hygiene note and by Paul's global instructions, and would
have diluted a domain-general skill. Kept out deliberately.

### 2026-07-29 — created (first version)

Derived from [[conclave-pr-review]] by keeping what was proven there (the two gates, separate
severity/confidence axes, feeding leads for refutation, mutation-testing the tests, SendMessage
delivery) and replacing the review-specific machinery with **Gate 3 reproduction**, the
**discriminating-test contract**, the **wrong-layer tripwire**, **rendered-layer verification**, and
the **evidence-gated deploy** — the last four all drawn from this estate's own incidents.

## See Also

- [[conclave-pr-review]] — the sibling skill (reviews changes)
- [[README]] — mirror contract and drift check
- [[GP-311]] · [[ALDC-490]] — the reference run and the defect it inherited
- [[adversarial-investigation-skill]] — Vlad's `/investigate-adversarial`, a different skill
- [[ai-pr-workflow]]
