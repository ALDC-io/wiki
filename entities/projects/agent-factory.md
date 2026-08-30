---
tags: [project, agent-factory, prefect-connectors, evaluation, greencontract, readiness, research, power-bi]
aliases: [Agent Factory, GreenContract, Zeus Pantheon Suite, readiness gates, PBI GreenContract]
sources: [github.com/ALDC-io/agent-factory, agent-factory/docs/reviews/build-vs-adopt-2026-08-29.md, agent-factory/docs/BUILD-VS-ADOPT-PROMPT.md, agent-factory/docs/research/SYNTHESIS.md, agent-factory/factory/readiness.py, agent-factory/factory/pbi_contract.py, agent-factory/docs/research/answers/R16-answer-decision-review-and-order.md, agent-factory/docs/research/answers/R17-answer-data-engineering-external-survey.md, agent-factory/docs/research/answers/R18-answer-our-factory-internal-audit.md, agent-factory/docs/findings.d/F70-F75, agent-factory/scripts/local_tracker.py, agent-factory/docs/specs/, prefect-connectors/orchestrator/data/audits]
created: 2026-08-21
updated: 2026-08-30
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

## 2026-08-23, evening — a fast tracker, and five instances of one bug

### ⭐ Threading a server deleted a correctness property nothing had declared

The tracker took **27.3 s** per page and served one request at a time (`socketserver.TCPServer`), so
a second viewer sat on a spinner behind the first. Threading it fixed that and **silently broke
`claims.claim()`**, which is check-then-write: it reads `blockers()`, then writes, with nothing in
between. That was atomic *only* because the transport was serial — an accident, not a property of
the code. `/start/<lane>` is a **GET**, so a double-click or a browser prefetch was enough.

Negative control: with the lock removed, **17 of 20 concurrent threads claimed the same lane.** With
it, 1 of 20. That is F73 — two agents, one worktree, one branch — re-opened at the HTTP layer.

**Carry this:** when you remove a bottleneck, ask what was relying on it. Serialisation is a silent
mutex, and nothing in the code says so.

### A cache inherits every input its subject reads

Caching the `suite` gate (97.6% of a `measure()`) took the page to **0.84 s** warm. The first
version shipped three real holes, all found by *attacking* it rather than testing it:

- `scripts/` was not in the fingerprint **and the suite imports it** — so the one file under active
  edit could not invalidate its own cache
- the published artifact HTML was not in it, and a test reads it
- **the environment was not in it**, and `$PREFECT_CONNECTORS` changes the verdict — F72 returning
  through the cache door

Also: a cached **FAIL** must never be served (an env-only fix changes no bytes, so the board would
stay red — the F20/F21 shape), and the negative control deserves a TTL rather than being replayed
from JSON forever.

⚠ Keyed on a **content hash, not a git SHA** — deliberately against the written plan. A commit SHA
is stable across uncommitted edits, which is exactly when you are iterating and most likely to be
served a stale green.

### ⭐ `__file__.parent.parent` is right in the primary and wrong in every worktree — five times

Reproduced live in `.worktrees/certify`: `git status` reported the tree dirty while
`worktrees.is_dirty()` returned **`False`**, because `existing()` filters worktree paths under
`<root>/.worktrees` and from inside a worktree that root nests one level too deep. `finish.checks()`
reads that value to warn *"uncommitted work does not survive the worktree being removed"* — so the
warning stopped existing exactly where work is most likely to be lost.

Five modules had it: `claims`, `worktrees`, `handoff`, `bus`, `operator`. **`runs.py` already had
the correct resolver and kept it private**, which is precisely what let the other four stay wrong.
`handoff` was the worst — `BOOT.mkdir(parents=True, exist_ok=True)` *silently created* the wrong
directory inside `.worktrees/` and wrote the lane's closing note there.

**Fixing instances did not work.** The rule is now enforced by test: anything under `.data/` resolves
through `factory.repo`. Git-tracked content may legitimately be checkout-relative — that is the real
distinction, and it is why the guard targets `.data/` rather than banning the expression.

### Check the INDEX, not the working tree

A commit staged a `claims.py` importing `factory.repo` while `repo.py` was still **untracked**, and
HEAD stopped importing. **Every check anyone could run in the working directory passed** — the file
was sitting right there on disk. A pre-commit hook now exports `git checkout-index` to a temp dir and
imports from there, which is the tree a fresh clone would get.

Cause was two sessions in one checkout: one had the file open and unstaged, the other ran `git add`
across the directory. **Neither acted wrongly.** See [[session-contention-and-artefact-homes]].

### Verify a citation before promoting it to a settled decision

A research pass settled a long-open UNKNOWN by citing a specific commit. The SHA resolved and the
substance held — but its **line numbers were wrong** (`:88`/`:1158` against an actual `:101`/`:1288`).
Nobody would have known without re-fetching the raw file. In an estate whose own record contains
*"one answer invented its evidence"*, a verdict resting on one unchecked citation is that failure
wearing a better answer.

**Report the outcome honestly** — *substance confirmed, precision off* is a publishable result.

## R16 — the decision review that found a live-broken gate hiding in a Python string literal (2026-08-23)

`docs/research/answers/R16-answer-decision-review-and-order.md`. Attacked the roadmap's eighteen
authored actions (not the field) and cites file+line throughout. Headline: **the "0 of 15
dimensions" figure quoted in four documents is not stale, it is wrong, and the instrument that
produced it can never say otherwise.**

`factory/readiness.py:870` built its regex as `f"\x08{d}\x08"` — an f-string missing the `r` prefix,
so Python resolved `\b` to a literal U+0008 backspace before the pattern was compiled. A backspace
cannot occur in Python source, so the pattern can never match and the gate can only ever return
`0 of 15` and FAIL. With the intended word-boundary regex the true value is **6 of 15** — and the
comment three lines above the bug (`readiness.py:857-862`, *"# we have these"*) already names the
six correct dimensions. The instrument disagreed with the comment sitting directly above it and
nobody had checked. The identical bug sits in `scripts/file_answers.py:74`.

⛔ **All three of the roadmap's gate-linked actions are wired to gates that cannot decide them**,
despite `roadmap.py:19-22`'s own claim that a gated action's status is `MEASURED` rather than
`AUTHORED`. a8 ("containerise agent execution") is gated on `isolated`, which only checks an env var
is set and a client class is defined — set the var, add the class, and a8 renders SHIPPED with zero
agents in containers. a10 ("restate the unattended goal as a 30–45 min run") is gated on `finishes`,
which counts completions with no duration term anywhere — a10 is an action to change the gate,
gated on the unchanged gate. a16 is gated on the broken `version` probe above.

Other findings worth carrying forward: **a14 ("build the notification channel first") is refuted by
both passes that landed after it was written**, and neither refusal reached `SYNTHESIS.md` despite
R14 being named there five times — its "three passes and one measurement agree" citation collapses
two measurements with different verdicts (four agents blocked on an unread question = PROVEN
absence; two PRs waiting 6–9 days = whether GitHub ever notified anyone was never checked) into
one. **The eval corpus has exactly one file** (`evals/corpus/windsorai-2026-08-20.json`) and none of
the eighteen actions names expanding it, despite three separate passes citing the ≥29-case
requirement and moving on. R16 independently re-derived the `/finish`-button defect covered below.

R16's own epistemic flag is worth keeping: it is a Claude subagent running inside this repo on this
estate's own conventions, so *"every pull is toward agreement"* — it compensated by forming a
verdict from the cited source before reading what the synthesis concluded from it.

## R17 — the external field survey, and the one control an agent cannot prompt its way around (2026-08-23)

`docs/research/answers/R17-answer-data-engineering-external-survey.md`. Five parallel lanes, ~196
searches, **38 citations independently verified against primary sources — 33 confirmed exactly, 5
corrected** rather than silently promoted (e.g. a CodeCRDT abstract read by an earlier pass as a
null result in fact reports "+21.1% on some tasks, −39.4% on others" with 5–10% semantic conflict
rates).

**Executive answer: build the Snowflake grant envelope; do not raise lane concurrency.** One role
per lane, `USAGE` + `CREATE TABLE`/`CREATE VIEW` on exactly one managed-access schema, owning
nothing in production, no policy object, `DEFAULT_SECONDARY_ROLES = ()`, a network policy, a
resource monitor per reader account. Reasoning: in Snowflake *"unless allowed by a grant, access is
denied"* and no super-role bypasses authorization — **a GRANT is the only control in the whole
survey an agent cannot ignore by ignoring its prompt.** Every dbt-side control (`--target` prefixes,
`--defer`, naming conventions) is an instruction living in a repo the agent can edit.

⛔ **The concurrency ceiling is a theorem, not a preference — confirmed, with a correction to the
framing.** Under a fixed conflict graph the instantaneous parallelism ceiling is the maximum
independent set; no coordination topology enlarges it, because a known static graph with
homogeneous agents leaves nothing to discover. But the file-level conflict graph is *coarse-grained
locking* — it over-approximates real conflict while under-counting semantic conflict to zero, "the
worst possible error profile." Field data: at 22,000 developers over two years, throughput rose
+33.7% while median PR review time rose +441.5% and no-review merges rose +31.3% [Faros, verified].
**Raising lane concurrency before the evidence gate is sublinear reduces safety, because a
saturated gate does not present as a queue — it presents as a bypass.**

⭐ **Clone-per-agent does not lift the 3-lane cap — it swaps one conflict class for three.** It
removes exactly the class the file-conflict graph already catches cheaply (the physical write
collision), and adds three the graph has no representation for: a shared warehouse queue (lanes
starve rather than corrupt each other past `MAX_CONCURRENCY_LEVEL=8`, and a timed-out validation
reports a false negative), a shared name-and-manifest space (two lanes can share zero files and
zero rows and still both resolve `ref('dim_customer')` to the same physical relation), and a shared
clone-provenance surface (streams/pipes/external tables silently absent from a clone, policies that
can point outside it, one field report of "186 of 280 views had hardcoded production references"
after cloning). And a clone of a **share** does not degrade, it does not exist — imported databases
cannot be cloned or Time-Travelled, so any lane touching share-consumed data has no isolation story
at all. Cloning is still worth doing (near-free — cloud-services metadata, billed only above 10% of
daily warehouse usage; the real cost driver is the 60-second warehouse-resume minimum, not clone
count) — it just will not be the thing that removes the cap.

⚠ **The 41.7% cross-agent conflict rate this estate cites is a verified external measurement and
was never claimed as an internal one.** R5 always attributed it correctly to arXiv 2607.04697v2 (a
corpus of 33,596 agent PRs); R17 confirmed the figure verbatim against the paper. R18, below, found
the attribution had drifted downstream into four places that now read as if it were measured here.

## R18 — the factory audits itself, and finds its own ledger's citations have drifted (2026-08-23)

`docs/research/answers/R18-answer-our-factory-internal-audit.md`. `STRUCTURE_CRITIQUE`, run
blind-first against the repo at `feat/readiness-generator @ b46d27d` before opening any prior
finding, spec, or the R17 answer — where it converged with something found blind, that is credited
rather than claimed as novel.

**Three of the thirty readiness probes have no reachable PASS path**, confirmed by AST-walking
every `g_*` probe: `g_failure_is_bounded` (`factory/readiness.py:253-268`) returns `_fail`
unconditionally with no `_pass` branch reachable; two more at `:543-597` and `:799-806` are the same
shape. Not new — `F11` on `lane/control-plane` found the identical defect a day earlier by the same
method, and its fix (`tests/test_readiness_probes_can_pass.py`, `scripts/mutate_readiness_probes.py`)
exists **only on that branch**. `factory/launch.py`, written on the primary after F11 was filed,
built its three-level readiness model on top of two of the unfixable probes anyway.

⛔ **All 8 currently-passing gates are declarative, not behavioural** — file-exists, substring
match, non-empty-list, `git remote` non-empty, regex-in-a-draft. Every gate that measures actual
behaviour is FAIL, UNMEASURABLE or NOT_RUN.

⭐ **Five of this repo's own finding citations were re-checked line-by-line: substance held in all
five, precision held in none.**

| Finding | Cited | Actual |
|---|---|---|
| F72 | `readiness.py:33` | `readiness.py:35-37` |
| F72 | `readiness.py:811` | `readiness.py:1033` |
| F20 | `readiness.py:175` | `readiness.py:204-224` (condition at `:222-223`) |
| F21 | `readiness.py:188` / `:180-190` | `readiness.py:227-250` |
| F71 | `local_tracker.py:1181`, "single-threaded `TCPServer`" | `local_tracker.py:2357-2362`, now `ThreadingTCPServer` |

F71's case matters most: its argument against building a threaded broker rested partly on the
tracker being single-threaded, and by the time R18 checked it no longer was — the recorded
reasoning needs re-arguing on current grounds, not just a corrected line number.

**The F70 fix (ledger → `findings.d/`) converted a loud merge conflict into a silent semantic
loss.** `git merge-tree` reports the four lane ledgers merge cleanly, but `factory/findings.py`'s
`load()` reads the old `docs/findings.md` first, then the fragments, and silently `continue`s past
any id already seen. Simulated and confirmed: merging `lane/control-plane` would silently drop the
primary's `F20` and `F21` — the two ADOPTED findings that say a gate which cannot pass is a defect —
because `lane/control-plane` reuses the same ids for two entirely different findings. **55 findings
across four unmerged branches are waiting on this**, and nothing in the repo detects a duplicate id.

Also caught live: the `suite` gate returned `FAIL "1 failed, 245 passed"` then, at the same commit
~8 minutes later, `PASS "246 passed"` — `_suite_fingerprint()` hashes the working tree's bytes, and
another session's uncommitted edit changed the verdict mid-session. Same defect as F72, on the time
axis instead of the cwd axis.

## Findings F70–F75 (`docs/findings.d/`)

Filed across the 2026-08-22 three-lane launch and the 2026-08-23 stabilisation/R17-R18 session.

- **F70 — ADOPTED.** A shared `docs/findings.md` cannot survive parallel lanes: three worktrees each
  read F10 as the last id and independently minted three F11s and three F12s, a merge that would
  have silently dropped two of each. This is the formal filing of the incident already described
  above under "the ledger became a directory."
- **F71 — OPEN.** Fixing the merge collision did not fix the blindness: a fragment written on one
  lane is invisible to another until both merge — typically after the point where knowing would
  have helped. Every cross-lane correction that actually landed in time on 2026-08-22 arrived over
  `SendMessage`, none through the ledger. **Corrected 2026-08-23 by R18** — see above: the tracker
  stopped being single-threaded the same day, voiding half the recorded argument against a threaded
  broker. `factory/bus.py` (`.data/bus/`, one append-only file per writer) was built as the other
  rejected option and argues machine-local is the *correct* design, not a compromise — a live
  disagreement with F71's own premise, left standing on the record rather than smoothed over.
- **F72 — ADOPTED.** The board's headline number depends on which directory it's run from.
  Re-verified independently this session (2026-08-29, see the gotcha below): **10 of 30** from the
  main checkout, **12 of 30** from `.worktrees/artifact`, same commit.
- **F73 — ADOPTED.** A claim is an intent, not a process: `finish()` released a lane claim while its
  session was still alive (idle, not dead), and a relaunch started a second agent in the same
  worktree — for a period on 2026-08-22 there were three control-plane sessions and two artifact
  sessions sharing one worktree and branch each. Nothing collided only because the extras were idle.
  Fixed: liveness now checked against the process table, with a distinct `unverified` verdict when
  the table can't be read, never collapsed into "nothing running."
- **F74 — ADOPTED.** A research-answer upload path that worked perfectly reported as broken from
  outside, because its only diagnostic was `print()` to a server usually started
  `-WindowStyle Hidden` — a refusal produced no file, no message, no record, so failure and
  "feature doesn't exist" were indistinguishable from outside. Fixed: every attempt now logs to
  `.data/answer-log.jsonl` regardless of outcome.
- **F75 — OPEN.** The important one. Both reconciliation checks (`unsynthesised()`,
  `unreconciled()`) read green — `[] ['R18']` — immediately before the session that actually read
  the answers found **R13 run 2 substantially unabsorbed, R14 unabsorbed, and R18 entirely
  unabsorbed**, with `SYNTHESIS.md` stating twice, in the same document, that R14 "has not run"
  while R14 had been `ANSWERED` and on disk for hours. Root cause: the checks measure **mention**
  and **mtime**, not **absorption** — a sentence saying "R14 has not run" *mentions* R14, satisfying
  the mention check while stating the opposite of absorption, and reconciling one answer clears the
  mtime signal for every other answer as a side effect. No fix adopted: accept-and-label,
  self-reported per-answer absorption markers, and tense/negation detection on mentions are all
  considered and each rated worse than it sounds; tightening the mtime check to per-answer
  comparison is explicitly refused as "a stricter proxy for the same unmeasured thing." Same shape
  as the R8 filename-swap defect noted in the Gotchas above, repeating in the same document, after
  the check written to catch it.

## The Power BI GreenContract — M1 through M12 (`factory/pbi_contract.py`, 2026-08-23)

Mirrors the connector-migration GreenContract for the same reason, one layer up: *"a model an agent
produces that nothing can check is not a deliverable, it is a liability."* Built **before** any
Power BI agent exists, per `boot-prompts/power-bi-data-model-designer.md` — the ordering is the
point.

Twelve assertions, preflight → model layer → consumer layer: rollback captured before mutation (M1);
target identity by dataset id + environment, never by matching values (M2 — REPORTED in the file's
own docstring as citing the GEP "Missing COGs" wrong-layer deploy this estate already has a standing
rule about, and GP-318); every written field appended or prior-asserted (M3 — REPORTED citing a
GP-318 fix that asserted one field's prior value while blanket-overwriting `Description` and
destroying 693 characters of unrelated guidance); additive-only manifest, no rename or delete
because a TOM rename doesn't rewrite dependent DAX (M4); refresh moved data not metadata (M5 —
REPORTED citing a client model whose last three refreshes were ~0.5s); anchors hold (M6); enumerated
no-regression (M7); absence renders BLANK never 0 (M8 — REPORTED citing GP-318's B26, 17 months of
literal $0.00 where the source simply didn't report a value); an independent warehouse-agreement
instrument (M9); and three consumer-layer assertions.

⭐ **The central design decision: M10 ("every visual paints") and M11 ("each slicer responds") are
declared even though no XMLA/DAX instrument can make either observation, and default to
`Unmeasurable` rather than being silently dropped.** The citation, per the file's own docstring
(REPORTED — not yet a wiki entry of its own): a repoint on ticket GP-293 passed DAX parity while
every visual rendered "Error loading data" from a stale `dataset_name`. *"A contract that quietly
drops the two assertions only a renderer can make is a contract that certifies the wrong layer — and
would have returned GREEN on GP-293 while every visual was broken."* An estate with no renderer
wired gets `Unmeasurable` for the whole contract — the honest verdict, distinguishing "did not
observe a failure" from "observed a pass." M12 additionally requires bound reports to be
**enumerated, never assumed** — on the client's live dataset `66151728`, neither of the two bound
reports binds a single Sales Measures field even though 38 of 70 guarded measures live there, and a
naive scan of PBIR's escaped visual JSON returns 0 bound entities (NOT-VISIBLE, not ZERO, unless the
scan decodes the escaping first).

This generalises the same GP-293/GP-318 lesson [[power-bi]] already records from the consumer-layer
side, applied here prospectively as a contract rather than retrospectively as a postmortem.
Cross-linked from that page.

## The tracker as a named surface (`scripts/local_tracker.py`, `python -m factory.local_tracker --serve`)

Eight tabs (`TABS`, `local_tracker.py:93-98`): Gates, Goals, Roadmap, Flow, Lanes, Sessions,
Research, Handoff. Since 2026-08-23 the server is a `socketserver.ThreadingTCPServer` with
`daemon_threads = True` (`:2357-2362`) — see the earlier note on what threading silently broke in
`claims.claim()`. Several buttons carry real server-side effects, not just navigation: `/finish`
(releases a lane's claim and writes a handoff), `/start/<lane>` (launches a lane), `/research/start`
(dispatches a research pass, dry-run capable), `/synthesize/start` (dispatches a synthesis pass).

⚠ **`/finish` never calls `factory.finish`.** Re-verified against the current file: the handler
(`local_tracker.py:2102-2116`, out of 15 `factory` modules imported at `:39-60`) calls
`ho.write_lane_handoff()` then `claimlib.release()` only — `factory.finish` is not among the
imports. Closing a lane through the UI therefore writes no `.data/runs.jsonl` row, pushes nothing,
and announces nothing on the bus, even though `factory/finish.py` exists specifically to guarantee
those three things happen together. First found by R14, independently re-derived by R16 (§2.9,
calling it the reason "every recorded outcome is FINISHED — three of three, zero REFUSED").

The synthesize button (commits `0c050ec`, `08f2939`) shipped without a re-entry guard: two clicks —
plausibly two people, or one double-click — could dispatch two synthesis agents against the same
file. Fixed the same day.

## Three specs written 2026-08-23 (`docs/specs/`)

Explicitly marked in their own text as design proposals to be attacked, not conclusions.

- **`product-end-state.md`** — states, for the first time, what the product is commercially *for*:
  two products, **Zeus Chat** (enterprise knowledge/institutional memory, MCP-reached) and
  **Zeus Foundry** (pipeline construction/proof/assurance, the build plane at `:8765`). Flags its
  own overdue-ness: R8, R13 and R14 were all dispatched *before* this existed — three research
  passes asked what to build with no statement of what it is for.
- **`control-room.md`** — answers "should we build a session-manager UI now" with **no, and the
  reason matters for build order**: of three measured time costs, two are not UI problems at all (an
  unread question file blocking 4 agents; 5 of 12 sessions sharing one name, fixable with an env
  var) and only the third (a single-threaded server re-running 30 probes serially, ~19s per load) is.
  Recommends building in slices, cheapest first, with an explicit stop line before the expensive
  terminal-grid/attach layer.
- **`ui-future-features.md`** — the three ideas Paul named in conversation (an agent-team config
  surface, a config optimizer, requirement-quality tooling), each rated: the team shape is already
  decided (R2's worker + non-LLM-verifier verdict) and invisible, so a **read-only** config surface
  is justified now; the optimizer and requirement-quality tooling both carry measured arguments
  against building yet, stated explicitly rather than deferred to prose.

## Gotchas (added 2026-08-29)

- **The readiness board's headline number depends on which `prefect-connectors` checkout
  `$PREFECT_CONNECTORS` (or its default sibling-path fallback) resolves to — and that can be a
  different *branch*, not just a different cwd.** Re-measured directly this session: from the main
  checkout, `python -m factory.readiness` reads **10 of 30** against the sibling `prefect-connectors`
  clone; from `.worktrees/artifact`, the same command reads **12 of 30** against
  `.worktrees/prefect-connectors`, which sits on `lane/control-plane` and carries finished
  control-plane work the main clone lacks. This generalises `[[F72]]` from cwd to *branch*: two runs
  from two worktrees are not just measuring "here" vs "there", they can be measuring two different
  codebases entirely.
- **The tracker's `/finish` button does not call `factory.finish`.** See above — closing a lane
  through the UI silently skips the run ledger, the push and the bus announcement that
  `factory/finish.py` exists to guarantee.

## 2026-08-29 — a defeated promotion gate, and the client intake portal design

**The gate.** `factory/evaluator.py`'s `RemoteVerdict.parse()` believed an unattributed verdict: it
checked that the attribution *keys existed*, then did `payload.get("evaluator") or {}`. A payload of
`{"verdict":"PASS","promotable":True,"evaluator":None,"scored_against":None}` parsed as
`is_pass=True, promotable=True`, summarised itself as *"PASS for r1 - by unidentified, bundle ?"*,
and `certify --remote` exited **0** on it. Fixed by checking attribution **content**: the evaluator
block must be a mapping stating a non-empty `identity` and `bundle_sha256`, and any *scored* verdict
must name a corpus. ⚠ `REFUSED` / `UNMEASURABLE` / `NOT_RUN` are explicitly **exempt from the corpus
requirement** — the service emits `scored_against: None` for those on purpose, and demanding one
would have turned an honest refusal into a parse error. **299 tests** (was 287); the 9 new
parametrised cases were run against the unfixed file first and **8 of 9 failed**. The reusable
lesson is on [[vacuous-verification]] — *a test that supplies fewer fields than the failure mode
needs is testing a different property than the one in its name*.

**The client intake portal — design only, nothing built.** Spec:
`agent-factory/docs/specs/client-intake-portal.md`. Readout:
https://claude.ai/code/artifact/0b01e843-cb59-4fdc-bee9-cecfbb0d1909

Paul's three decisions this session: **internal now, client-facing path designed in** (so §7 of
`docs/specs/product-end-state.md` is *deferred, not resolved*); **contract-authoring first**, with an
assisted layer so a client is never asked to invent an answer; and answers land in an **internal
ticket in ALDC's own UI**, which then creates a linked Jira issue — our record is the original, Jira
a projection.

⭐ **The measurement that reframed the build: the questions already exist.**
`aldc-launchpad/docs/evidence/gep-intake/` holds a machine-readable triage of one real client's
request sheet — **36 rows, 21 UNDERSPECIFIED (58%), 25 already carrying a drafted
`question_for_client`, 9 drafts all carrying a `blocking_question`, and 0 with a surface the client
can answer in.** Nothing in this wiki pointed at that store before today. So the portal is a
**render target for a question store that exists and is populated**, not a new questionnaire —
building it blank would rebuild the finished half. Regenerate:

```bash
cd aldc-launchpad/docs/evidence/gep-intake
python -c "import json;d=json.load(open('triage.json'));r=d['rows'];print(len(r), d['counts'], sum(1 for x in r if str(x.get('question_for_client') or '').strip()))"
```

⭐ **And the form already exists as a dataclass.** `ConnectorTarget` carries a block commented
`# canary expectations` — `required_keys`, `key_column`, `primary_key`, `non_null_positive`,
`date_column`, `run_date`, `expect_rows`, plus `allowed_tenants`/`tenant_column` — and **A9 reads its
entire meaning from it**. "Which markets must all appear?" *is* `required_keys`. So the client's
answers compile directly into the assertions the connector is certified against, closing design
alignment to verified delivery in one object. **Generate the form from the dataclass, never by hand**
— the same rule `factory/board.py` states about boards.

⛔ **The load-bearing safety rule, and it is already proven in this repo.** A9's own comment records
that *"with this list empty, A9 passed a partial extraction that had dropped an entire account"*. An
unanswered question and a declared "no constraint" both produce an empty list, so every portal
control is **three-state** — declared / declared-not-applicable / **unanswered, which emits no value
at all** and yields `UNMEASURABLE`. Every cell also carries provenance, and only two of four values
compile: `CLIENT-DECLARED` and `CLIENT-CONFIRMED` become live assertions; `PROPOSED-UNANSWERED`
(drafted by probe, chat or precedent) becomes `NOT_RUN`; `INFERRED` becomes `UNMEASURABLE` until
confirmed. **A proposal is never an answer** — that single distinction is the entire safety property
of the assisted layer, without which the portal manufactures the client's consent and then certifies
against it.

Boundary inherited from `evaluator.py`: **the client authors the expectation and never the verdict.**
There must be no field anywhere in the portal through which a client can influence their own grade.
Contracts freeze and hash as v*n*; a run certified against v3 while the client is on v5 gets its own
verdict, `CERTIFIED-AGAINST-SUPERSEDED`, rather than a pass.

**Build order.** Slices 1 (one answer → one assertion, proved able to FAIL) and 2 (render the 25
existing questions) are **unblocked and need nothing that does not already exist**. Slice 3
(probe-grounded feasibility, with `AVAILABLE` / `ABSENT` / `UNPROBED` never collapsed) is ⛔ **blocked
on running real connectors** — `evals/corpus/` holds exactly one fixture, `windsorai-2026-08-20.json`,
and synthesising more would make every feasibility answer a `PROXY` wearing a measurement's clothes.

⛔ **Tripwire to keep §7 from being crossed by accident:** the moment anyone proposes sending a portal
link to a client, that reopens the internal-vs-product question — it is an architecture change, not a
deployment task. Write that sentence beside the code.

**Honesty note.** The portal attacks the **client-response** bottleneck (the GEP domain). It does not
attack connector delivery, whose measured shape is different — one migration was 21.6 min of active
stage time inside 8 h 20 m of wall clock, 4.3%. Two domains, two bottlenecks.

### ⚠ Two corrections to the 2026-08-29 boot prompt

1. **`artifact.yaml`'s `decisions` and `change_requests` are NOT unused.** Measured across
   `clients/GEP/tickets/*/artifact.yaml`: **2 of 2 tickets carry populated `decisions` (8 in total)**
   and 1 carries a change request. GP-199's entry reads *"Client (Justin Shuster) approved Approach A
   via email 2026-05-01"* — it **already records who approved, through what channel, on what date**.
   The portal therefore does not invent decision capture; it makes that line the product of a click
   rather than a transcription. Also **2 tickets, not 3**.
2. **26 artifacts in the gallery, not 24** (`aldc-launchpad/docs/artifacts/REGISTRY.md`). The
   8-with-no-source and 13-orphaned figures are confirmed. Giving artifacts an engagement to belong
   to is the cheapest fix on the table for both.

## 2026-08-29 — build vs adopt, decided: the thesis narrows and the orchestration bet flips

`docs/BUILD-VS-ADOPT-PROMPT.md` (277 lines, never run) asked, component by component, which parts of
this system are re-implementations of mature tooling. Run as a six-lens `/prospect` council; output
at `agent-factory/docs/reviews/build-vs-adopt-2026-08-29.md` (491 lines). Every `BET-CHANGING` claim
was re-verified by the synthesiser at primary source before it entered the record.

⛔ **The sequencing constraint that outranks every verdict: the factory has never certified a
connector.** `python -m factory.launch` prints `certified NOT_RUN — 12 assertions have no instrument
wired` and `breadth FAIL — 1 case(s), 0 strata`. `factory/live_probes.py` wires **A1 and A5 only**,
and its docstring notes both are reachable *"with no credential and no network call"*; every other
verb inherits `Probes._refuse`. So **A2, A3, A4, A6, A7, A8, A9, A10, A11, A12 have never run against
a live target** — the whole assertion battery the pass was asked to price an adoption for, plus the
tenancy claim. ⭐ **Every migration cost in the review is priced against interfaces that have never
carried traffic**, so A9 cannot be compared with `pandera` on merit: A9 has never done anything. This
is not dishonesty — `live_probes.py` refuses *on purpose* so UNMEASURABLE cannot become PASS just
because some instrument exists — but no ADOPT should be actioned before `CIP-05` closes.

**Verdicts:** ADAPT on data contracts (take ODCS as the *artefact*, keep our validator), agent
orchestration (build the runner, adopt only the Claude Agent SDK as transport) and intake forms
(most of CIP-09/10 already exists upstream). **BUILD** on the other seven.

⭐ **The inherited "adopt before you abstract" recommendation is falsified** — it lived in
`boot-prompts/execution-plane-2026-08-30.md` as a starred section and has been **corrected in place**.
The six frameworks cover **3 of 8** requirements; worktree isolation, lane claiming, the persisted
retry ledger, the event ledger and the verdict model are ABSENT from all of them, so you build those
either way. **AutoGen** is in maintenance mode by its own README; **CrewAI**'s core abstraction
(`role`/`goal`/`backstory`, hierarchical process that *"automatically assigns a manager"*) **is** the
topology R2 rejected on a 180-configuration study, and it owns control flow so it cannot sit below
`GreenContract`; **SWE-agent** and **Aider** fail on release staleness; **LangGraph** drags
`langsmith` — a hosted telemetry client — as the *first entry* of `langchain-core`'s **mandatory**
`dependencies`. Pricing: **~370–510 new lines** hand-rolled (~310–420 with the SDK) on top of
**1,682 lines that already exist and work**, against 150–300 lines of adaptation *plus* a framework.
⭐ **And the zero-callers premise drew the wrong conclusion**: of `deploy.py`'s 265 lines, **140 are
`AttemptLedger`**, a cap that survives restart — and every framework's budget control is
per-invocation and resets, *which is the exact bug `AttemptLedger` was written to fix*.
The SDK's cost is **negative**: `deploy.py:230-234` already hard-codes `--max-turns` /
`--max-budget-usd` / `--output-format stream-json` / `--model` against an undocumented, unversioned,
**unpinned** argv surface, so adopting it makes an existing invisible coupling typed and pinnable.

⭐ **The headline thesis was refuted at the level of representation and survives only at aggregation
— see [[vacuous-verification]]'s fifth shape** for the six tools and the arithmetic that defeats each.
The publishable claim is now *"UNMEASURABLE must survive aggregation as a refusal"*, not *"a fourth
verdict is uncommon"*; as drafted it was falsifiable in four minutes by opening
`ossf/scorecard/checker/check_result.go`.

**The other three theses, all narrowed, none dead:**
- **Evidence-basis at the API boundary** — the *vocabulary* is NIST prior art (OSCAL
  `Observation Method`: `EXAMINE`/`INTERVIEW`/`TEST`/`UNKNOWN`), but OSCAL's `Relevant Evidence` is
  **`min-occurs="0"` — optional**, and it will validate a finding with zero evidence. `tasks.py:129`
  *raises*. The structural ancestor is **Perl taint mode**, not assurance cases: a provenance label
  that makes a privileged operation fatal until explicitly cleared. A proven mechanism in a new
  domain is an easier claim to defend than an invention.
- **Mandatory negative controls** — mature in three neighbouring fields (`promtool test rules`,
  Atomic Red Team, and **EICAR c.1991**, whose own page says it is *"like setting fire to the dustbin
  in your office to see whether the smoke detector is working"*). Uncommon part is making it a
  per-gate shipping requirement for a *delivery scorecard*.
- ⛔ **Spec-and-test-as-one-artefact is TRIED-AND-FAILED prior art.** It **is** BDD, and Cucumber's
  own creator published in 2014 that adopters *"completely missed out on the underlying practices"*
  and used it *"uniquely as a testing tool. No collaboration."* Concordion's last release: 2023-07-16.
  ⭐ **BDD did not fail on format — it failed because the stakeholder does not fill it in**; an
  engineer does it afterwards and the artefact becomes a config file the client never read. **That is
  a prediction for CIP-07.** The only differentiator is already in the plan — *pre-fill from a live
  schema probe so the client confirms rather than authors* — and it belongs on the critical path.

⭐ **The cleanest adopt in the repo, which nobody was looking for: `claims.py:200-247` should be
`tox-dev/filelock`** (Unlicense, **zero transitive deps**, 3.32.4 on 2026-08-23). It deletes ~48
lines whose Windows `EACCES`-vs-`EEXIST` race the author's own comment records being bitten by —
*"Twenty racing threads reproduce it every time; two rarely do."* A lock is not a judgement, so no
verdict semantics change and no adapter is needed. `grep -rn filelock` returns **nothing** in the
repo, and the prompt's candidate landscape **has no locking row at all**, so the search never ran.
Also flagged, larger and not recommended yet: `scripts/local_tracker.py` is **2,554 lines** of
hand-rolled `socketserver` HTTP and *caused* the concurrency bug `filelock` would fix — threading it
removed the accidental atomicity that made `/start/<lane>`, a **GET that mutates state**, safe.

⛔ **Prerequisite to any adoption, filed as `BVA-01`: there is no gate protecting the dependency
surface.** `pyproject.toml:6` is `dependencies = ["pyyaml>=6.0"]` — the entire runtime surface — with
**no lockfile of any kind, no `.github/` and therefore no CI**, and **none of the 27 readiness gates
measures a dependency**. The repo gates a *corpus byte* changing (`corpus.py:89-96` raises
`CorpusError`) and does not gate its grader's dependencies changing. Compounding it: the starred
candidates (**datacontract-cli, Great Expectations, Soda Core, Dagster, LangGraph, CrewAI**) have
**zero Windows CI between them — 0 of 68 workflow files**. Pure-Python packaging means they
*install*; it does not mean a path or subprocess bug would ever be caught upstream. **Any ADOPT on
those means "we are the Windows CI", as a standing cost.** And the **adapter tax** is uncounted
everywhere: `contract.py:52-58` turns any instrument exception into UNMEASURABLE, while every adopted
tool returns a boolean — so each adoption is a new place UNMEASURABLE can silently become FAIL, and
no test guards an adapter boundary today because no adapter exists (`BVA-06`).

**Corrections this pass published** (the prompt's own figures were stale the day it was written):
`factory/` **9,227** lines across 40 files, not 8,886/38 · `tests/` **4,684** across 31, not 3,873 ·
`docs/` **56,125** across 93, not 54,232/89 · `local_tracker.py` **2,554**, not 2,470. ⭐ **And
"304 tests passing" is three different numbers, none reproducible without its condition** — 301
`def test_` definitions, **388 then 409** executed within one hour as a concurrent session added
tests, and 304 from an unrecorded sibling-repo state. The suite is currently **RED at 21 failed**,
and those failures are the sibling checkout (`prefect-connectors` on `chore/artefact-homes`, 29 dirty
files, `mutate_control_plane.py` absent), **not a regression**. Part 4's candidate landscape was
`RECALLED / UNVERIFIED` and six of its rows are now corrected — AutoGen (maintenance mode), Schemata
(last release 2023-05-08), dbt-expectations (2024-09-10), deepchecks (2024-12-15), Formbricks (K1
fail + AGPLv3), and the "cheapest place to adopt" line itself. Also: `docs/reviews/external/verification.md:43`
is now **stale** — `tasks.py` is NOT dead code; `TaskStore` is imported by
`scripts/export_board.py:16` and `scripts/local_tracker.py:827`.

**Ticketed** (`.data/tasks.jsonl`, 165 → 185 events): created `BVA-01` (dependency gate), `BVA-02`
(filelock), `BVA-04` (ODCS reshape), `BVA-06` (adapter contract), `BVA-07` (retitle the claim).
⭐ **Three of the eight drafts were NOT created because they duplicated existing tickets** — checked
first, because the prior external review was caught proposing two tickets for code that already
existed. They became evidence on `CIP-05` (now the gate on all adoption), `RUN-03` (the BUILD verdict
plus the line-by-line pricing) and `CIP-09`/`CIP-10` (already built upstream). `next:` remains
**RUN-01** — the pass removed a question rather than creating priority work; boot prompt at
`boot-prompts/build-vs-adopt-2026-08-30.md`.

## See Also

[[orchestrator]] · [[prefect-connectors]] · [[vacuous-verification]] · [[agent-session-completion-signals]] · [[session-contention-and-artefact-homes]] · [[GEP]] · [[power-bi]]
