---
tags: [project, agent-factory, prefect-connectors, evaluation, greencontract, readiness, research]
aliases: [Agent Factory, GreenContract, Zeus Pantheon Suite, readiness gates]
sources: [github.com/ALDC-io/agent-factory, agent-factory/docs/research/SYNTHESIS.md, agent-factory/factory/readiness.py, prefect-connectors/orchestrator/data/audits]
created: 2026-08-21
updated: 2026-08-22
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
unattended?* **30 gates, 9 passing** as of 2026-08-22 (was 23/3 the day before), in four phases —
can the loop run, is it bounded, can it tell success from failure, can its output be certified.

Every gate is measured from a file at run time and names the path it came from. Three surfaces, one
measurement: the terminal command, `scripts/local_tracker.py --serve` (re-measures on every browser
refresh, and since 2026-08-22 has a **reload button** that re-imports the probe modules — a running
server otherwise holds the code it started with and will re-measure faithfully against a stale gate
list), and section 10 of the published artifact via `scripts/build_tracker.py`.

⚠ **The published artifact is a fourth, separate surface and it goes stale silently.** It read
`3 of 23` while the repo was at `9 of 30`, because a published artifact only changes when someone
republishes it. `scripts/build_tracker.py --check` detects the drift and
`tests/test_tracker_is_current.py` now fails the suite on it — before that, the guard existed and
nobody ran it, which is the same shape as an eval nobody watches fail.

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
- **`setx VAR "value"` from bash stores the quote characters too.** It broke `$AGENT_FACTORY_EVALUATOR`
  while the gate still read PASS, because the gate only checks the variable is non-empty. Use
  `[Environment]::SetEnvironmentVariable(...,'User')` and always read the value back — *SUCCESS:
  Specified value was saved* is not evidence of **what** was saved.
- **`git checkout <path>` is a silent no-op on an untracked file.** Back up before mutating a new
  file, or the revert does nothing and the mutant ships.
- **A long-running Python server holds the modules it imported.** `local_tracker.py --serve`
  re-measured on every refresh against a 23-gate list for hours. `importlib.reload` alone is not
  enough either — `from x import y` binds by value, so the reload must **rebind** the names or it
  is a no-op that looks like it worked.
- **`getBoundingClientRect()` on a WRAPPED inline element returns the union of its line boxes**, so
  it overlaps whatever precedes it on the first line. Compare `getClientRects()` per line box.
- **The audit log the loop gates measure stopped on 2026-05-28.** Nothing has run in the
  orchestrator since, and it is not currently running. "3 of 14 runs finished" is true of a history
  three months old, and the gates do not say so.

## Evaluator isolation — the grader is a separate principal (2026-08-22)

Gate `isolated` was the only one with a queue behind it (`isolated -> certified -> tenancy`). It
now passes, and **not by moving `evals/`** — R3 retired that plan in as many words: *"moving only
the files to another directory changes nothing; moving ownership/credentials out of the agent's
capability set does."*

The design, in one sentence that is really a statement about `factory/evaluator.py`: **the agent
supplies `{artifact_uri, artifact_sha256, run_id}` and nothing else.** Not the corpus, not the
manifest, not the assertion set, not the evaluator. Those are resolved by the service from its own
configuration on every request, and the client has nowhere to put them — `Submission` has three
fields and the service refuses a body carrying a fourth.

| | |
|---|---|
| `factory/evaluator.py` | `EvaluatorClient` — three verbs, no writer, **no local fallback** |
| `evaluator_service/` | the separate principal; write-once verdict store outside the repo |
| `factory/certify.py --remote` | certification routed through the service |

Four refusals were **watched happening** and then mutation-tested: a weakened blueprint, a smuggled
`corpus_path`, a swapped artefact (sha mismatch), and a replaced verdict. Three mutants introduced,
three caught.

⛔ **Do not read the green gate as "the agent cannot cheat."** The deployment is loopback under one
uid — R3's rank 5, *"mostly theatre"*. The *design* is rank 1; the gap is a managed identity the
agent sandbox does not hold, which is a **deployment change, not a code change**.

⚠ **The real remaining hole:** the contract is parameterised by a blueprint the graded party
writes. An agent that softens its own blueprint softens its own grading, process boundary or not.
A four-rule target floor and the artefact hash narrow it; a per-connector target pinned by the
evaluator would close it, and nobody has written one.

## Rendering the readout — six refusals, then a different route (2026-08-22)

`claude-in-chrome` refused for the sixth session running, so the published figure had shipped five
defects with a human finding every one. Every inspectable link is healthy — extension installed and
enabled, service worker alive, account matches, native messaging host registered with the right
extension id and spawnable, no enterprise policy — and `list_connected_browsers` still returns
`[]`. The failure sits in the extension's own service-worker pairing state, the one place not
inspectable from outside.

**The fix was to stop waiting.** `scripts/render_pass.py` drives the *installed* Chrome through
Playwright — no extension, no claude.ai account, no pairing. First run found four real defects:

1. ⭐ **The figure declared a category it never drew.** Caption said 115 attempts, legend carried an
   amber *"5 started, no outcome recorded"*, and 110 bars painted — none amber. The dropped
   category was the **unmeasured** one, in a figure arguing that unmeasured outcomes get dropped.
   The 5 cannot be interleaved: pairing starts to terminals locates **24** unterminated starts, not
   5, so their position is unrecoverable and they are drawn past a divider, in no order.
2. **The page scrolled sideways at 700px.** `.body-grid` uses `minmax(0,1fr)` on desktop; the
   `max-width:940px` override dropped the guard to a bare `1fr` — which is `minmax(auto,1fr)`.
3. **Two `<text>` elements clipped** by their viewBox under `overflow:hidden`, one by 373px.
4. The tracker subtitle read *"Thirteen gates"* while the generator emitted 30.

## Measuring the build itself (2026-08-22)

`factory/schedule.py` reads velocity out of the artifact's own git history — every commit carries a
generated `n of N gates pass` headline and a date, so progress is already an append-only log.

⭐ **It refuses to give a completion date, and names its criterion.** Over 6.4h gates passed went
1 → 9 (1.25/h) while the gate *set* went 13 → 30 (2.65/h). **Remaining grew 12 → 21.** More work is
being discovered than completed — the correct shape while the system is still being measured — but
an ETA divided by a moving denominator flatters. It will project once the total holds still for
24h. "Ahead or behind" reports NOT-SET, because no target was ever stated.

`factory/lanes.py` groups gates into five parallel lanes **by file locality, not the dependency
graph**: 16 gates are startable, and two sessions editing `orchestrator/pipelines.py` simply
conflict. `docs/findings.d/` is the ledger between lanes (was `docs/findings.md` until 2026-08-22) — corrected premises only, four mandatory
fields, and closing a lane with `NOTHING TO REPORT` is itself an entry so silence means checked.

## 2026-08-22 — the first real three-lane run, and three defects in the launcher itself

Three lanes (`control-plane` on opus, `certify`, `artifact`) ran end to end for the first time.
**The claim → work → finish loop completed for real**, which the pre-flight boot prompt listed as
unproven. All four branches pushed (`lane/*` in agent-factory, plus `lane/control-plane` in
[[prefect-connectors]], where the control primitives actually live: cap, bounded, concurrency,
reaper, from-history, with **39 negative controls and a mutation harness proving each is
load-bearing**).

⭐ **The launcher was wrong in three ways, and none of them failed.** This is the same family as
[[vacuous-verification]] — the work happened, it was just not the work anyone asked for:

1. **Every lane ran the wrong model.** `--model` was built into a variable that nothing read
   (`inner = f"claude --model {lane.model} ..."`, dead since the launch path moved to a `.ps1`).
   The banner printed the intended model, so `control-plane` announced opus and ran the session
   default, and `grain` announced haiku and ran something dearer. A label, not a setting.
2. **Transcript saving was off.** Lanes inherited `CLAUDE_CODE_CHILD_SESSION` from the session
   that started the tracker, so an hour's work would have been unresumable with no record.
   ⚠ `claude -p` **cannot test this** — print mode never suppresses, so the obvious test is
   non-discriminating. The gate is `tor()` in the shipped binary:
   `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` short-circuits suppression unconditionally.
3. **All three lanes had the same name** — they inherit the parent's session name, so a peer
   listing showed three identical rows and a question from one lane could only be answered by
   messaging all three and letting two ignore it. Fixed via `CLAUDE_CODE_SESSION_NAME`.

**A restarted server serves the code it started with.** The tracker was launched 12 seconds
*before* the transcript fix was committed and served pre-fix code for hours. Restart after any
change; confirm exactly one listener.

### The ledger became a directory

`docs/findings.md` is no longer the write target — **`docs/findings.d/`** is, one file per
finding. Three lanes appended to the single file from three isolated worktrees, each correctly
read F10 as the last id, and each took the next number: **three F11s and three F12s**, and a merge
that would have silently destroyed two of each. Worktree isolation is the feature, so the ledger
could not be one mutable file. Ids remain (they are how `[[F20]]` resolves) but are now a naming
convention allocated in per-lane blocks, not a lock on a shared file.

Findings also gained **KIND / CHANGES / STATUS**. Most findings are corrections — read it, fix it,
spent. A *design consequence* is not spent until it is built or deliberately refused, and the
ledger could not tell those apart, so they were filed, admired and never acted on. `CHANGES` is
mandatory when the kind is a design one; `design_debt()` is the list that should shrink.

### ⚠ Two gates cannot pass, and the board's number has no basis without a cwd

- **`finishes`** requires `len(fin) == len(runs)` all-time. Four runs sit at `stage_started`
  forever and new runs raise both sides, so a perfect agent still reads FAIL. The reaper only
  helps if it **backfills terminal events for those four**.
- **`succeeds`** is an all-time ratio needing **837 net successful stages**, permanently carrying
  the 2026-08-14 incident that has since been capped. It answers "has this ever been reliable"
  while being read as "is it reliable now".
- **The board reads 9 from the main checkout and 10 from a lane worktree at the same commit.**
  `CONNECTORS` is `FACTORY.parent/"prefect-connectors"`, so a worktree sees an unmerged lane
  branch; the `ticket` gate resolves to a `.worktrees/aldc-launchpad/` that does not exist and
  goes UNMEASURABLE. Neither run is wrong. **State the cwd with any before/after claim.**

A gate that cannot pass is the mirror of a gate that cannot refuse: it stops measuring and starts
reporting failure at work already done.

### Also earned

A closed lane leaves its claim held for **4 hours** with nothing to reap it — which is the
`reaper` gate the same lane is building. `~/.claude/skills/` is **not** worktree-isolated, so an
edit there is live for every session immediately and will not roll back with the branch. And
`impeccable`'s detector **silently degrades to 1 finding instead of 313** without four npm
packages — now pinned, and recorded with the other machine-local state in
`docs/evidence/machine-local-state-2026-08-22.md`.

## 2026-08-22, control-plane lane — the gate count did not move, and that was the finding

All six control-plane gates already read PASS. **Three of them were passing over the defect
they are named for**, and the session's whole value was making them honest: 15 of 30 before,
15 of 30 after.

### `reaper` — "either finished or killed" killed only the record

`reap_expired_leases` marked the stage failed, freed the slot and reconciled the run. The
Prefect flow run and its **ACI container survive the orchestrator**, and the reaped stage's own
error string handed that half to a person — *"if this stage launches cloud work, check whether
it is still running."* The record was never the thing holding the shared 10-core quota, which is
what ten orphaned containers took on 2026-08-13.

Two things had to exist first. **A durable handle**: the flow run id lived in a local variable on
a thread-pool thread, so in the exact case that produces orphans — the process dies — the only
handle on a running container died with it. **A terminator that fails closed**: ownership is
unprovable from a container name (`<flow>-<run-uuid>`, no operator suffix), so unproven ownership
is NOT_ATTEMPTED, never a delete. A leaked container is recoverable; a colleague's live backfill
deleted mid-merge is not.

⚠ The verdict vocabulary is the contract's four, and **NOT_RECORDED does not mean "it launched
nothing"** — it means we cannot tell, and every stage dispatched before this date is in that
state.

### `cap` — the refusal was invisible at the surface a human watches

The override existed only in `server.py`. Tracing why found worse: `api()` in the dashboard has
**no `res.ok` check anywhere**, so a 400 arrived as `{error: …}`, the caller read
`result.dispatched || 0`, and a refused retry rendered as a **green success toast**. The route
past was Delete Pipeline — the 2026-08-14 workaround that destroyed the evidence along with the
loop.

⭐ And an independent review found the fix was still not enough: `ControlRefused` subclasses
`ValueError`, and `_handle_post_pipeline_restart`'s `except ValueError` answers **404**, which
tells the browser the pipeline does not exist. Now **409** with the control named in the body, so
no client parses prose.

## ⭐ The lesson worth carrying out of this lane

**A grep is not an instrument, and a probe is only as honest as the half it did not supply
itself.** Four separate instruments in this repo reported green over systems with the defect
intact:

| instrument | how it lied |
|---|---|
| the `reaper` gate's wiring checks | `"cloud_reaper" in source` was satisfied by a **surviving import** after the registration call was deleted; an ordering guard compared **string positions**; a count of `_report_run(ctx,` counted **call sites** while the callee did nothing |
| the browser probe for the cap | derived the engine's real **message** (because the known lesson was about a message) and **invented the status** — the half the guard actually branched on |
| `mutate_control_plane.py` | its verdict depended on `-q` inherited from a **different repository two directories up**; pytest walks upward for rootdir config |
| both mutation harnesses | a mutation anchor is a **copy of production source**, so a refactor disarms it silently — and one harness was still quoting a load-bearing count from a run that predated the change it was meant to certify |

The rule that falls out: **if a check would still pass with the function body deleted, it is not
measuring the function.** Extract a named seam and call it. And **take the whole answer from the
thing that answers** — anything a probe hands itself is a premise.

### What is NOT done

- **Nothing has run.** No control has been watched refusing during a live migration; the
  orchestrator has not run since 2026-05-28.
- **No container has ever been deleted by this code.** There is no Azure subscription in the
  suite, so three `az`/Prefect functions are untested by construction.
- ⚠ **Cloud termination is ARMED BY DEFAULT against the production resource group**
  `aldcprodrsgpprefectworkers1c`, with an env-var kill switch as the only brake. The argument for
  it is written down and sound — a default-off switch is off during the incident — but nobody has
  made that call out loud.

## See Also

[[orchestrator]] · [[prefect-connectors]] · [[vacuous-verification]] · [[GEP]]
