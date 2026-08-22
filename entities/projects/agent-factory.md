---
tags: [project, agent-factory, prefect-connectors, evaluation, greencontract, readiness, research]
aliases: [Agent Factory, GreenContract, Zeus Pantheon Suite, readiness gates]
sources: [github.com/ALDC-io/agent-factory, agent-factory/docs/research/SYNTHESIS.md, agent-factory/factory/readiness.py, prefect-connectors/orchestrator/data/audits]
created: 2026-08-21
updated: 2026-08-21
---

# Agent Factory

> A factory for agent teams whose output can be **certified** rather than believed. Repo:
> **`github.com/ALDC-io/agent-factory`** (private, created 2026-08-21). Local:
> `C:\Users\PaulRussell\repos\agent-factory`. Work lands on `feat/readiness-generator`.
>
> Boot prompt and evidence live in `aldc-launchpad`, not here — the factory repo holds code and
> contracts only, same rule as [[prefect-connectors]].

## The premise, in one line

This estate has twice built mechanisms that *acted* without anything measuring whether the action
helped — a retired agent producing 233 diagnoses, 234 escalations and **zero fixes** over 81 days,
and a loop that ran 965 times, recorded its own 1.6% success rate, and never adjusted. Both were
capable. Neither was measurable. So the ordering is: **what "done" means, then whether that
definition can fail, then everything else.**

## The GreenContract

Twelve assertions (A1–A12) a connector migration must satisfy end to end, executable, parameterised
per connector from YAML. **Four verdicts, never collapsed** — `PASS` / `FAIL` / `UNMEASURABLE` /
`NOT_RUN`. `UNMEASURABLE` is explicitly not a pass and exits non-zero.

- **Probes refuse by default.** An unwired harness returns 12× `UNMEASURABLE`, not 12× `PASS`.
- **A mutation registry is a test.** `test_every_assertion_has_been_proved_able_to_fail` fails the
  suite if any assertion has never been observed failing. Adding an A13 without a mutation turns it
  red.
- **The corpus is hash-pinned data, not code.** `evals/corpus/*.json` + `MANIFEST.sha256`, verified
  on load. Editing the recorded run so a `FAILED` reads `completed` is refused with both hashes.
  Every replayed verdict carries `scored_against` — corpus id, sha, recorded date.
- ⚠ **Tamper-evident, not tamper-proof.** Anyone with write access to both the corpus and its
  manifest can re-pin silently. The fix is credential separation, not a cleverer hash.

⭐ **The calibration found a hole review did not.** The first matrix run *passed a partial
extraction* — an entire account missing, and the completeness assertion reporting "18 rows satisfy
every declared invariant" — because the invariant was guarded on a blueprint field left empty, so
the check silently did not run. Fixed structurally. **An invariant that quietly does not run is an
assertion that quietly stopped being made, and that is indistinguishable from a pass.**

## Readiness gates — the measurement that replaced a checkbox grid

`python -m factory.readiness` scores one question: *can an agent team run a connector migration
unattended?* **23 gates, 3 passing** as of 2026-08-21, in four phases — can the loop run, is it
bounded, can it tell success from failure, can its output be certified.

Every gate is measured from a file at run time and names the path it came from. Three surfaces, one
measurement: the terminal command, `scripts/local_tracker.py --serve` (re-measures on every browser
refresh), and section 10 of the published artifact via `scripts/build_tracker.py`.

⛔ **A gate shipped a false PASS and it is worth remembering how.** The evaluator-isolation probe
grepped `factory/*.py` for `EVALUATOR_URL` and friends — and **matched its own source**, because
those strings were in the regex doing the searching. It reported "an evaluator service is
configured" when none existed. A self-matching probe producing a false green is the exact defect the
programme exists to stop, reproduced inside the instrument.

See [[orchestrator]] for what the gates found in the build plane.

## Research — four passes, one verdict

Four Deep Research prompts (`docs/research/R1`–`R4`, answers in `docs/research/answers/`, synthesis
in `docs/research/SYNTHESIS.md`). Only R3 was *asked* whether to build an optimiser; the other three
volunteered it.

| | Verdict |
|---|---|
| R1 eval harness | *"The weakest parts are not primarily LLM-eval sophistication. They are control-plane problems."* |
| R2 topology | *"Control-plane changes are more urgent than agent architecture."* |
| R3 control plane | *"This system should not be optimised yet. It should first be made bounded, reapable, fail-closed and independently evaluable."* |
| R4 agnostic ×2 | *"Feasible as infrastructure, premature as an optimisation target."* |

⛔ **The three-agent team is rejected.** R2 was asked whether architect → implementer → tester is
defensible and answered directly: **one end-to-end worker agent, plus a non-LLM verifier holding the
authoritative PASS bit.** No LLM manager, no LLM architect, no LLM tester, no agent-to-agent
channel. Evidence: 180 configurations across 5 architectures and 4 benchmarks, multi-agent averaging
−3.5%, sequential tasks degrading 39–70%. Connector migration is sequential shared-state work — the
class that did worst. `blueprints/orchestrator_team.yaml` is marked superseded and kept, with the
unlock threshold in the file.

⛔ **Calibrating on one run graded FOLKLORE.** A blind spot affecting 10% of a stratum needs **29
cases** for a 95% chance of being seen once; 5% needs 59; 1% needs 299. The prescription is two
distributions — a regression corpus of every distinct historical failure (**not** frequency-weighted,
because the observed distribution is endogenous to a broken system) and a challenge corpus across 15
mechanisms.

⚠ **Offline replay does not make configuration search cheap** — a correction to an earlier claim of
mine. Replay scores *the evaluator*, not an unrun candidate configuration. Real cost stands: 20
configs × 3 replicates ≈ 1,584 agent-hours, 16.5 days at four-way parallelism, and no honest dollar
figure until failed attempts record cost.

## Build order — configuration experiments last

```
1 hard external attempt/spend/concurrency budget      5 tenant isolation at every boundary
2 timeout + cancellation + orphan reaping             6 complete attempt/cost telemetry
3 terminal verdict from append-only history           7 external evaluator trust boundary
4 refusal-capable gates with negative drills          8 expand and freeze the corpus
                                                      9 ── only here ── config experiments
```

Steps 1–4 are changes to [[prefect-connectors]], and they are the **first team's work, not hand
work**. The reason to fix them first is that a team cannot be certified until the loop it runs in
can tell success from failure.

## Tenancy — the six account ids were already written down

`allowed_tenants` blocked certification until 2026-08-21, when the ids were found in
`prefect-connectors/connector/accounts/GEP/deployments/windsorai.py:23`, declaring what the flow
**requests**: Brinno, Bridgford, bigsostore, Cibu, Slobproof, GEP-Amazon. Its own note — *"GP-226,
verified 2026-05-29: an unfiltered team-key pull returns 45 Google accounts, of which these 6 are
Navira's."*

⚠ Verified twelve weeks before use, and the source says *"confirm against a live pull before
activation."* A PASS means "the landing matched what we declared", not "what we declared is still
correct". Meta stays unfilled — 3 accounts of 19, ids never recorded, and the
`REPLACE_BEFORE_ACTIVATION_SEE_TODO` placeholder is **good design**: it matches nothing, so the flow
lands zero rows instead of silently mixing in another client's.

**Never read tenancy scope from landed rows.** "Which accounts arrived" is not "which were
requested" — that is the A9 hole exactly.

## Gotchas

- **`pytest` addopts is already `-q`.** Passing `-q` again makes `-qq`, which suppresses the summary
  line. A probe parsing that line was blinded by a config it had not read.
- **Filenames are claims.** Two research answers arrived with their contents swapped.
  `scripts/file_answers.py` classifies by content and refuses when uncertain; it has twice been
  caught by its own dry run, once about to overwrite a second run of a prompt.
- **Nothing here has touched the live warehouse.** Every number is replayed from recorded evidence.
  No Snowflake or Prefect credential has been requested or used.

## See Also

[[orchestrator]] · [[prefect-connectors]] · [[vacuous-verification]] · [[GEP]]
