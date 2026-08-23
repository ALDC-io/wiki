---
tags: [project, agent-factory, prefect-connectors, evaluation, greencontract, readiness, research]
aliases: [Agent Factory, GreenContract, Zeus Pantheon Suite, readiness gates]
sources: [github.com/ALDC-io/agent-factory, agent-factory/docs/research/SYNTHESIS.md, agent-factory/factory/readiness.py, prefect-connectors/orchestrator/data/audits]
created: 2026-08-21
updated: 2026-08-23
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
| a test named for a behaviour | `test_the_skipped_handles_survive_for_the_next_sweep` asserted only that the handles were still on the record — which a record **nothing will ever read again** satisfies identically. No sweep read them. **The promise was in the name, not the body** |
| an `except`-clause guard | it checked that an `except ControlRefused` clause **exists**, not that it comes first. `ControlRefused` subclasses `ValueError`, so a broad clause first makes it dead code with the clause visibly present — the original defect, reborn, guard green |

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

## 2026-08-23 — the cost was always measurable, and a test was writing to production

Three lessons, all reusable outside this repo.

### ⭐ A Claude Code session's cost is recoverable from its own transcript, retroactively

`terminal-configuration.md` said *"nothing currently records what a lane spent."* That was true of
**our code**, not of the substrate. Every assistant message in
`~/.claude/projects/<slug>/<session>.jsonl` carries a `usage` block, so **input/output/cache tokens,
the model actually used, and wall-clock are all recoverable — including for work that ran before
anyone thought to instrument it.** No agent has to be asked to report its own spend, which also
means it cannot misreport it.

The join is the directory slug, and it is the part that silently breaks: **each of `:` `\` `/` `.`
in a path becomes one dash.**

```
C:\Users\p\repos\agent-factory\.worktrees\control-plane
  -> C--Users-p-repos-agent-factory--worktrees-control-plane
```

Get it wrong and every lane reports NOT-RECORDED, because the directory is simply never found —
a measurement gap that reads as a finding about the work. `factory/runs.py::slug` holds the rule.

First measurement (2026-08-23), the first time per-lane cost could be asked at all:

| Lane | Output | Cache read | Wall | Model | Commits |
|---|---|---|---|---|---|
| control-plane | 1.23M | 322M | 22.8 h | opus-5 | 25 |
| artifact | 227k | 55M | 19.4 h | sonnet-5 | 5 |
| certify | 236k | 55M | 1.7 h | sonnet-5 | 4 |

One opus lane spent ~5x either sonnet lane's output for ~5x the commits. **One observation, not a
law** — but the model-per-lane table in the terminal spec was reasoning until this existed.

### A completed unit of work must leave a record, and the record cannot live where the work did

`finish()` asserted, pushed, announced and then **deleted the claim** — the entire trace. An hour
later a lane that ran nineteen hours and a lane that never launched read identically. The obvious
fallback, the bus, was rooted at `parent.parent/.data`, which inside a git worktree is *that
worktree's* `.data`: per-lane, invisible to every other lane, one event in the whole estate.

**A ledger with one copy per worker is not a ledger.** It has to resolve to a shared root — here,
the primary worktree from `git worktree list`. Same failure mode as the findings ledger that had to
become `findings.d/`.

And the basis vocabulary that came with it, which is the [[vacuous-verification]] discipline applied
to history: **RECORDED** (written as it happened) / **RECONSTRUCTED** (derived afterwards from git
and transcripts — can say what something cost, cannot say whether it *finished*) / **NOT-RECORDED**
(nothing ran, or nothing survived). A lane that never launched reports NOT-RECORDED, never `0`.

### ⚠ Adding a write path turned the existing test suite into a production writer

The sharpest one. `finish()` was wired to append to the new ledger. `tests/test_bus_and_finish.py`
already called `finish.finish("certify", ...)` against a fixture — so **every suite run began
appending real rows to the real ledger.** Twelve landed before anyone looked, and the UI duly
rendered *"certify — FINISHED, 12 recorded runs"* for a lane that had run once, the day before,
before the ledger existed.

**A fabricated history in the instrument built to stop history being lost is worse than a wrong
number**, because it is indistinguishable from evidence.

The generalisable rule: **when production code starts writing a record, audit what the existing
suite already calls before assuming the suite is read-only.** Fixed structurally — an autouse
`conftest.py` redirect so a test added later cannot forget, with an explicit opt-out fixture for
the live assertions, because a live check pointed at a tmp directory passes trivially and a check
that cannot fail is not a check.

### Two smaller ones, both about handoffs

- **An instruction conditional on access the reader does not have is not an instruction.** A
  research prompt said *"read R2, R3, R5 and R7 first **if you have them**"* — and named the
  *prompt* files, not the answers. The researcher had neither, answered on the prompt's summary
  tables, and its own verdict was that the comparison against the real system was not grounded. A
  whole research pass was spent. The fix is to **ship the sources with the question**, and to state
  that where the pack and the prompt disagree, the pack wins.
- **"Not answered yet" hides more than two states.** A prompt written and never sent waits on
  *you*; one in flight waits on the *researcher*; and one that was sent and came back unusable is a
  third that most trackers cannot express at all — filing the bad answer reads as ANSWERED, not
  filing it reads as never-sent, and both are false. Same shape as folding UNMEASURABLE into FAIL.

## 2026-08-23, afternoon — three lessons that generalise past this repo

### ⭐ Parallel speedup floors at the slowest single task, not total ÷ width

A page took 9.4 s because 30 readiness probes ran serially. The obvious fix — "independent,
I/O-bound, use an 8-wide pool, 9.3/8 ≈ 1.2 s" — is **wrong by about eight times**, and it was
produced, believed, and propagated into a research prompt, a synthesis section and a boot prompt
before an outside session measured the distribution:

```
total 9.39 s across 30 gates
  suite      9.16 s  = 97.6%   <- shells out to a full `python -m pytest`
  other 29   0.23 s  =  2.4%
```

One gate is a single indivisible subprocess. A pool of any width takes this from 9.39 s to 9.16 s.

**The general rule: a figure derived by dividing a total by a width assumes the total is
divisible.** Before quoting `total ÷ N`, measure the distribution — if one task dominates, the
floor is that task and concurrency buys nothing.

⚠ And the reason nobody re-derived it: **it agreed with what we wanted.** The page felt slow, 1.2 s
felt fast, and the arithmetic was plausible. A number that confirms the desired conclusion is the
one least likely to be checked.

The real fix is architectural, not concurrency: take the expensive thing out of the request path
and cache it against the git SHA of the code it tests, rendered with its age attached — which the
no-silent-cache rule permits, because the age travels with the figure.

### "X routes through Y" is a claim to grep, not a premise to inherit

A rebuild was being considered partly to decouple connectors from `core-api`. Two greps settled it:

| field | uses | |
|---|---|---|
| `environment_level` | 4 | builds three strings |
| `environment_deployment_group` | 2 | the same strings |
| `core_url` | **0** | required, plumbed through container env, defended by tests, **read by nothing** |
| `core_api_token` | **0** | same |

There was no request path to decouple from — the dependency was four lines of config, half of it
dead. **A rebuild justified by escaping it would have been escaping something that was not there.**

The failure mode underneath is worth keeping too: `get_global_config()` did
`try: ... except Exception: return None`, called at **package import**. A missing credential that
nothing reads silently yields `None`, and every consumer then raises `AttributeError` at runtime
inside a container. **A bare except at import time converts a config error into a runtime mystery.**

### ⭐ Three research passes failed in one day, and not one failed on model capability

| Pass | How it failed | Cause |
|---|---|---|
| R8 run 1 | asserted internal facts it could not check; answer discarded | its prompt said *"read these first **if you have them**"* — conditional on access it did not have, and it named the *prompt* files rather than the answers |
| R13 run 1 | invented an entire migration section; struck from the record | never read its own **named attachment** |
| R15 | supported a recommendation with a fabricated user study | *"in our user studies we found…"* — there were none |

**Every one was a competent model, a clear question, and an incomplete brief.** None would have
been saved by a better model or a different agent; all three would have been stopped by a
file-existence check on the named attachments.

The repair that worked, three times:

1. **Ship the evidence with the question** — a generated pack containing every source the question
   depends on, rebuilt before each dispatch because a copy is stale on the next edit.
2. **State that the pack wins** where it disagrees with the prompt, and that the disagreement is
   itself a finding.
3. **Let `NOT-SUPPLIED` beat a plausible assumption.** The last assumption cost a whole section.

⭐ **This generalises from research prompts to agent task briefs — they are the same object:** a
question plus the evidence it depends on, handed to something that will answer confidently either
way. It also reorders the roadmap: optimising *agent configuration* tunes the wrong variable if the
failures come from *requirement quality*, and it will converge, confidently, on a setting that was
never the problem.

### A filing convention can describe an organisation that does not exist

`boot-prompts/` holds **186 files with 183 distinct name prefixes**, 74% of them undated in the
filename. The standing instruction is *"read the newest one matching the ticket or workstream"* —
which cannot work: there is nothing to match against and mostly no date to be newest by. **Nothing
declares which handoff is CURRENT for anything.**

Same failure class as research prompts before a dispatch instrument existed: state living in prose,
no instrument, and a human sorting from memory. The fix is a declared workstream key and a state
(`CURRENT` / `SUPERSEDED` / `SPENT` / `ORPHAN` / `UNCLASSIFIED`), with one assertion that makes it
real — **exactly one `CURRENT` per workstream**. And do not backfill: the old files report
`UNCLASSIFIED`, which is a fact about the convention's age, not about the files.

## 2026-08-23, evening — four surfaces that answered a question they had not measured

Four defects found in one session, all the same shape: **a surface reported a verdict it had
inferred rather than looked at.** Worth carrying because none of them was a bug in the usual
sense — every one was code doing exactly what it said, over a population or a signal it had
silently narrowed.

### 1. `claims.py` read liveness off a clock

`STALE` meant "older than `STALE_AFTER` (4h)" and the refusal text read *"release it if that
session is gone"*. Three lanes claimed 29h earlier were labelled STALE while **all three sessions
were still running**. Following that advice would have freed the lanes, let a relaunch start a
second agent in an occupied worktree, and recreated F73 — through the claim store's own advice text.

`finish()` had always consulted `sessions.live()` before releasing. `claims.py` never did, so two
modules disagreed about one question and **the one that talked to the operator was the one that had
not looked.** Now `holder()` measures against the process table and returns three verdicts, never
two: `HELD-LIVE` / `HELD-GONE` / `HELD-UNVERIFIED`.

### 2. ⭐ The blocked-question inbox hid the oldest questions

`blocked()` was `[r for r in inventory() if r["needs"]]`, and `inventory()` iterates the **session
registry**. A question whose session had exited was filtered out of the surface built to display it.

**Five agents were blocked. The tab showed two.** And the bias has a direction:

```
hidden   812h, 61h, 61h      <- two of them credential requests
shown     13h,  2h
```

The longer a question waits, the more likely its session has exited — so a session-keyed inbox
**systematically hides the questions that have waited longest**. The oldest had been blocked since
21 July, 33 days. Fix: read JOBS as the primary source and join back to the registry. A question is
a fact on disk and outlives the process that wrote it; liveness is metadata about *how to answer*,
never a filter on *whether to show*. New state `NO-SESSION`, kept distinct from `EXITED-GONE`.

Age is keyed on the agent's own `updatedAt`, not file mtime — mtime is a filesystem property and a
copy or sync would silently reset the age of the very questions the list ranks *by* age.

### 3. `truthful` passed over a population of one

The gate that catches a record contradicting its own event log reported *"recorded status agrees
with the event log"* having compared **exactly one pipeline, with 13 event logs unexamined**:

```
2 pipelines listed · 14 runs with an event log · 1 actually compared
```

It iterates `pipelines.json`, not the audits, so a run with a log but no entry is invisible to it.
Meanwhile `from-history` — the FAIL it declares a dependency on — was naming *"3 runs recorded
succeeded over 115, 21 and 15 failures"*. Those are precisely the records `truthful` exists to
catch, sitting in the 13 it never looked at.

**No `comparable != 0` check before scoring.** That is the same false-certification shape the
connector parity gate already closed structurally — *the lesson was learned in one place and not
carried to the other*. Now raises `Unmeasurable` below a floor of 3. **The board went 10 → 9 of 30**,
which is the honest number.

### 4. `tenancy` over-claimed in its title, and its edge asked a different question

Gate title read *"Is blast radius certifiable?"*; the probe passes on a non-empty `allowed_tenants`
list. So PASS announced certifiable blast radius while meaning *"somebody wrote six account ids
down"* — ids verified 2026-05-29, ~12 weeks before the blueprint that carries them, which itself
says *"Confirm against a live pull before activation."* Retitled to **"Is a tenant scope DECLARED?
(declared, not verified)"**, and the `tenancy -> certified` edge removed: reading a list out of a
blueprint needs no live instrument. The edge was written for *"is the list still correct?"*, which
no gate asks. **The missing gate is real** — `tenancy-verified` — and adding it changes `len(GATES)`
and the pinned artifact, so it is its own job.

## `factory/launch.py` — three questions, not one word

The board answers *which gates pass*. An operator wants *may I press start, and what happens if I
walk away*. Those conflate into "ready" and had **different answers**:

```
May I RUN it, watching?     SUPERVISED-OK
May I LEAVE it?             UNATTENDED-BLOCKED   cap · reaper · ceiling · concurrency · bounded
May I TRUST the output?     OUTPUT-UNCERTIFIED   certified · corpus · version · breadth · isolated
```

⭐ **The circle this breaks:** `finishes` and `succeeds` are UNMEASURABLE *because no run has
started since the controls landed*. They cannot go green until something runs; nothing should run
unattended until they are green. The way out is a **supervised** run — a human is a cap, a reaper
and a spend ceiling, just an expensive one — and a board rendering a single "9 of 30" cannot say
so, leaving an operator to read 30% and not start the run that is both safe and the only way to
measure the loop at all.

`UNGATED` is preserved for a team with no contract: **not 0%**. Same distinction as `NO-SESSION`.

## Two features both called `sessions`

`factory/sessions.py` existed on the integration branch *and* on the control-plane lane, with **zero
API overlap** — one about OS processes (pids, liveness, transcripts), one about work (waves,
running order, mutual exclusion, handoff cards). Neither a superset, both wanted.

**git reported it only as an add/add conflict on one filename**, which is the weakest possible
warning for two features quietly claiming one name; resolving it by hand would have silently
deleted a feature. The lane side was renamed to `factory/workplan.py` (tab `Plan`) because the
substrate already owns the word — `~/.claude/sessions/<pid>.json`, `CLAUDE_CODE_SESSION_NAME`,
`claude agents` are not ours to redefine.

## The findings-id collision, proven rather than inherited

`load()` reads `docs/findings.md` first, then `findings.d/*.md`, keeping the **first** occurrence.
Materialising the post-merge tree and running `load()` against it:

```
39 findings after merge
F20 -> "An instrument that counts its own writes"      <- lane's
F21 -> "pipelines.py has no in-process lock"           <- lane's
```

The `findings.d` pair — *gate finishes can never pass* and *gate succeeds is an all-time ratio* —
**silently vanish from every consumer**, while remaining on disk. `git merge-tree` reports the
findings CLEAN because they are in different files. A second collision waits: control-plane holds
F1–F34, certify holds F30–F32.

## See Also

[[orchestrator]] · [[prefect-connectors]] · [[vacuous-verification]] · [[GEP]]
