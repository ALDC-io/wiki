---
tags: [architecture, decision, adr, environments, snowflake, test, prod, parity, connectors, navira, gep]
aliases: [Environment Parity Strategy, TEST vs PROD Parity, Preview-of-prod-next, Full-Parity Promotion-Gate]
sources: [aldc-launchpad/navira-dashboard-redesign/reports/navira-lori-priorities-tickets-draft.md, "GP-294", "GP-207"]
created: 2026-07-21
updated: 2026-07-21
---

# TEST↔PROD Environment Parity — Decision Record

> **Status:** ACCEPTED 2026-07-21 (Paul + Claude). **Tracking ticket:** GP-294 (Navira / [[GEP]]).
> **Supersedes** the ad-hoc "TEST reads PROD via the share" posture that grew out of [[snowflake-data-share-refresh|GP-207]].
> Applies org-wide (GEP first), not just Navira.

## Context / problem

We run two separate Snowflake **accounts** — non-prod `og35375.canada-central.azure` (`LSUBOGT.YX94045`) and
prod `wj66376` (`LSUBOGT.MY89318`), both `AZURE_CANADACENTRAL`. See [[azure-environments]] / [[deployment-groups]].

Historically TEST ingestion was turned **off** and a **PROD→TEST data share** (`PROD_DG1_GEP`, [[GP-207]]) was
stood up so TEST could read prod raw. That was correct **while TEST had no connectors**. But we are now building
**new connectors / new data sources**, and a new source *cannot exist in prod yet* — so it has to land somewhere.
The result is a **mixed, hard-to-validate provenance**:

- **Established sources** arrive in TEST via the **PROD share**.
- **New sources** are written **directly into TEST** by their connectors.

TEST is therefore neither a faithful mirror of PROD nor a clean independent environment, and "is this feature/data
correct?" has no clean answer. This is the [[project_gp281_test_clone_staleness|GP-281 clone-staleness]] failure
mode's structural cousin.

## The key reframe

The trap: trying to make **TEST == PROD-now**. That is impossible the moment new sources are born in TEST (they
have no prod counterpart yet).

**Decision: TEST is a *preview of prod-next*, not a mirror of prod-now.** TEST is where sources and features are
**proven before promotion**. PROD's future state = TEST's current state. What keeps them honest is **not identical
data** — it is:

1. **Identical transformation code** (the repo DDL that builds TEST facts is byte-identical to prod's), plus
2. **Schema parity** (same tables/views/columns/grain), plus
3. **A promotion gate** (nothing reaches prod except by promoting proven TEST work).

Because TEST/PROD connectors pull at different times, **row-for-row equality is neither achievable nor a goal.**

## Decision — full-parity + promotion-gate

Adopt Paul's target: *"TEST runs the same way as PROD, with connectors on a less-frequent schedule to save cost."*

1. **TEST ingests everything itself.** TEST [[Eclipse]] runs **every** connector (this is the purpose of the
   in-flight [[project_test_eclipse_rehab|TEST-Eclipse rehab]]) → retire the runtime dependency on the PROD share.
2. **One connector definition per source, deployed to both environments**, differing only by environment config:

   | Dimension | PROD | TEST |
   |---|---|---|
   | Connector code / transformation SQL | **identical (from repo)** | **identical (from repo)** |
   | Target account + credentials | prod | test |
   | **Schedule** | prod cadence | **slower — daily / weekly** |
   | Warehouse size + auto-suspend | prod-sized | XS, 60s suspend |
   | Retention / time-travel | prod | short (0–1 day); transient raw where acceptable |

3. **New-source lifecycle** (the fix for the mess): born in **TEST** (slow schedule) → validated end-to-end
   (TEST raw → TEST warehouse → TEST consumer) → **promoted to PROD** (same code, flip env config) → now runs in
   **both**. No more "new-in-test / old-via-share."
4. **Drain the PROD→TEST share to zero.** Keep it only for not-yet-migrated sources, on a checklist that empties.
5. **Guardrail:** TEST holds **≤ one promotion cycle ahead** of PROD — don't let unproven connectors pile up, so
   the TEST−PROD diff is always small and explainable ("TEST has exactly these N items prod doesn't, each on a
   known promotion path").

## Parity is validated at four levels (strongest first) — NOT row-exact

This is the definition of the **parity harness** (GP-294 scope c; generalizes the existing `Ad Spend Integrity
Check` / Flag B):

1. **Transformation-code parity** — repo DDL byte-identical test↔prod. If code is identical and input schema is
   identical, behavior is identical. ~80% of confidence, essentially free (a git diff).
2. **Schema parity** — every table/view/column/grain identical across accounts (`INFORMATION_SCHEMA` diff; the PBI
   layer already has `pbi_ops/_compare_models.py`, which reports "0 PROD-only" today). Runs in CI.
3. **Freshness + volume assertions** — TEST `max(date)` within the expected lag of its schedule; row counts within
   an expected ratio; no null/zero-value spikes. Catches "the connector silently stopped."
4. **Spot reconciliation on a closed historical window** — for a period both envs have fully ingested, key
   aggregates match within tolerance. Proves the **pipeline**, not pull-timing. The only place actual numbers are
   compared.

## Cost controls (what makes full parity affordable)

Slower TEST cadence (daily/weekly); XS warehouse + aggressive auto-suspend; a **dedicated TEST resource monitor
with a hard monthly credit cap** (so TEST can never surprise the bill); short/zero time-travel; transient raw.
Full-rebuild facts (the current norm, see [[snowflake-cost-analysis]]) are fine on a slow schedule.

## Consequences

- **Positive:** TEST becomes a genuine, independent, prod-like environment; new work has a real home; the share
  dependency dies; confidence rests on identical code + schema parity, not on identical data; validating a feature
  in TEST genuinely predicts prod after promotion.
- **Cost:** double ingestion + storage for sources that run in both — mitigated by the controls above.
- **Discipline required:** every source must be promotable by config flip (no hand-wired test-only pipelines); the
  ≤1-cycle-ahead guardrail must be honored.

## Alternatives considered (rejected)

- **Prod-only ingestion; TEST reads the share.** Cheapest, but you cannot test a new connector without shipping it
  to prod first — the chicken-and-egg that created today's mess.
- **TEST periodically clones prod raw (share/zero-copy clone).** Cheapest + row-exact for *existing* sources, but
  new sources have no prod counterpart to clone → same chicken-and-egg. Fine only as a *supplement* for a large
  historical source we don't want to re-pull, never as the model.

## Migration (GP-294 phases)

(a) write this ADR *(done — this page)* → (b) **provenance discovery** (enumerate every source: test-native vs
prod-share → the drain checklist; verify TEST-Eclipse can schedule all connector types — the linchpin) →
(c) **build the 4-level parity harness** (runnable + CI) → (d) **share-decommission migration** (move each shared
source to test-native ingestion, retire the share path; checklist → zero).

## Related
[[azure-environments]] · [[deployment-groups]] · [[snowflake-data-share-refresh]] · [[data-share-pattern]] ·
[[star-schema-convention]] · [[snowflake-cost-analysis]] · [[project_test_prod_share]] ·
[[project_gp281_test_clone_staleness]] · [[GP-207]] · [[Eclipse]] · [[Snowflake]]
