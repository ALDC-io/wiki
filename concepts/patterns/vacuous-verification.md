---
tags: [pattern, verification, evidence, agents, review, quality, claude-code]
aliases: [vacuous verification, vacuous verdict, verdict without content, schema-degenerate agent return]
sources: [prefect-connectors session 2026-08-14 (docs/KNOWN_ISSUES.md issues 22-26), concepts/patterns/answerability-guard.md, concepts/patterns/schema-dialect-drift.md, concepts/patterns/conclave-pr-review.md, agent-factory session 2026-08-30 (research separation; contract.py fifth verdict, commit 0d4bdb1), agent-army-research/research/synthesis/W0-foundations.md]
created: 2026-08-14
updated: 2026-08-30
---

# Vacuous Verification

**A verification pass can return a result that is structurally perfect and completely empty.** The
verdict field says `CONFIRMED`; the reasoning field says `"test"`. Downstream, only the verdict is
read — so a verification that did no verifying is indistinguishable from one that did, and it
propagates as fact.

This is the generalisation of a failure ALDC has now hit across many mechanisms: an agent return, a
CI check, a mutation test, a guard-test battery, an exception-swallowing test helper — and then two
shapes where the content is **present and correct** and something downstream destroys it. In the
fifth, the **arithmetic** throws it away (a scoring layer). In the sixth, the **transport** does —
a shell pipeline replacing a failing exit code with `tail`'s.

Six shapes, in the order they were found:

| | Shape | Found |
|---|---|---|
| 1 | **Empty verdict** — healthy container, no content | 2026-08-14 |
| 2 | **A gate that cannot fire** (and its inverse, one that cannot pass) | 2026-08-22 |
| 3 | **An inert control** — correct, present, and doing nothing | 2026-08-27 |
| 4 | **A test pinning a weaker property than its own name** | 2026-08-29 |
| 5 | **The aggregate discards a correct verdict** | 2026-08-29 |
| 6 | **The transport discards a correct verdict** | 2026-08-30 |

## The reference case — verifier agents, 2026-08-14

Five defect claims about [[prefect-connectors]] were dispatched to independent verifier agents, each
told to confirm or refute one claim against real code, returning a **structured output schema**
(`verdict` / `reasoning` / `evidence`).

| | Result |
|---|---|
| 3 of 5 | returned `CONFIRMED` with `reasoning` literally the string `"test"` and `evidence` `"a"` / `"b"` |
| 1 of 5 | hit the schema retry cap and errored out |
| 1 of 5 | returned a substantive verdict |

**The agents had genuinely done the work** — 18–36 tool calls and 60–90k tokens each. Nothing was
lazy or short-circuited. It was the **final structured emission** that degenerated, after the
investigation was complete. The work existed; the report of it did not.

Re-running the *same five claims* with a **free-text return format** plus an explicit instruction —
*"if you write the word 'test' here you have failed the task"* — produced substantive, correct
verdicts, including a **programmatic byte-diff** proving three SQL statements identical and an
**in-process repro** showing an accumulator returning lengths 1, 2, 3 across successive calls. Same
claims, same code, same model: the format of the return was the whole difference.

## ⭐ The lesson

> **A schema-constrained agent return is not self-validating.** Check that the *content* of a verdict
> is substantive before trusting the verdict field.

The verdict is a **claim about work**. Only the content is **evidence of work**. Structured output
makes the claim machine-readable, which is exactly what makes an empty one dangerous: it flows
straight into a decision without a human ever reading the reasoning that was supposed to justify it.

Note what does *not* save you here: token spend and tool-call counts were high and honest in every
degenerate case. High spend is therefore **not** evidence the verdict is earned — though *near-zero*
spend remains a strong tell in the other direction.

## Practical rules

1. **Free-text return when the reasoning is the deliverable.** Reserve strict schemas for values you
   will compute on, not for the argument.
2. **Plant a canary in the instruction** — name the degenerate output explicitly ("if you write the
   word 'test' here you have failed") so the failure mode is addressed rather than assumed away.
3. **Read one field deeper than the one you act on.** If you act on `verdict`, read `reasoning`. If
   you act on a CI conclusion, read the job. If you act on a test result, read what it asserted.
4. **Treat a retry-cap error as a null result, not a refutation.** The one agent that errored had
   said nothing about its claim; it must be re-run, not counted as unconfirmed.
5. **Anything gating a decision gets re-verified by a different route.** This is the same discipline
   as [[conclave-pr-review]]'s re-verification of merge-gating findings.

## The same family

Every one of these is the identical shape — a healthy container, no content:

| Mechanism | How it went vacuous |
|---|---|
| **Agent verdict** (this page) | `CONFIRMED` / `reasoning: "test"` after 18–36 real tool calls |
| **`claude / review` CI check** | A green check means the bot **ran**, not that anything was reviewed — the zeus-memory bot was paused and the [[core_api]] bot only COMMENTED. Read the review body |
| **Mutation test** | Removing the dtype folding left **all 58 tests green** — the only dtype test covered columns whose mapping already worked ([[schema-dialect-drift]]) |
| **Guard-test battery** | Comparing a value to itself, and rebuilding cases from post-apply state: 50 cases → 24, still ALL GREEN ([[answerability-guard]]) |
| **Exception-swallowing helper** | `trigger_and_wait` wraps its body in `try/except`, so a sentinel-exception assertion passes unconditionally and tests nothing ([[orchestrator]]) |
| **Skipped publish job** | A workflow run whose publish job was **skipped** (not failed) still reports a conclusion; the registry timestamp is the fact ([[github-actions]]) |
| **Parity coverage check** | Nothing supplies an intended window, so coverage is `NOT_COMPARABLE`, lands in `advisories` rather than `inconclusive`, and the run still reports **PASS** ([[prefect-connectors]] issue 25) |

The last row is worth dwelling on: a check that **cannot** produce a failing answer will report
success forever. That is a vacuous verification with no agent involved at all.

## Detection

- **Grep the artifact for the placeholder vocabulary** — `"test"`, `"a"`, `"foo"`, `"n/a"`, empty
  strings — in any field that is supposed to carry an argument.
- **Ask what a FAIL would have looked like.** If you cannot describe the failing output concretely,
  the check may be structurally incapable of producing one.
- **Ask whether the instrument was live in the window measured.** A zero from an instrument you have
  not proved can see is not a measurement — the analysis-side statement of the same rule.

## 2026-08-22 — four more, and the inverse (agent-factory lane run)

All four returned success, or a number, while doing nothing or the wrong thing. See
[[agent-factory]].

- **A flag built into a dead variable.** Every lane launcher printed the model it intended
  (`Bound the loop · opus`) and ran a bare `claude`: the `--model` string was assigned to a
  variable nothing read. Nothing failed — the work happened, just not on the model requested, and
  the *cheap* lane was the expensive one. Advertised ≠ wired.
- **A detector that degrades instead of failing.** `impeccable`'s 59-rule engine falls back to
  regex-only without four npm packages and reports **1 finding where the real engine reports
  313**. A fresh run concludes the page is clean. The instrument was never proved able to see.
- **A Win32 call that succeeds on the wrong handle.** `GetConsoleWindow()` under Windows Terminal
  returns a hidden pseudo-console; `FlashWindowEx` on it is a no-op **that returns success**.
- **A non-discriminating test.** `claude -p` was used to verify a transcript fix; it passed — and
  so did the control with the fix removed, because print mode never suppresses transcripts. A test
  both arms pass is not evidence. The result was discarded rather than reported.

⭐ **The inverse also exists: a gate that cannot PASS.** `finishes` requires every recorded run to
be terminal, and four are stuck forever; `succeeds` is an all-time ratio needing 837 net
successes and permanently carries one capped incident. Neither can go green however good the agent
gets, so the board reports failure at work already done. A gate that cannot refuse is decoration;
a gate that cannot pass is a wall. Both have stopped measuring.

And a measurement with no stated basis: the same readiness board reads **9 from the main checkout
and 10 from a lane worktree at the same commit**, because paths resolve relative to cwd. Neither
is wrong — the number simply does not mean anything until you say where it was taken.

## 2026-08-27 — the inert control: correct, present, and doing nothing ([[GP-329]])

A third shape, and the most dangerous of the three because it survives inspection. The verdict-shaped
failures above are empty; the gate-shaped failures cannot fire. **An inert control is genuinely
correct and genuinely does nothing**, so anyone who reads it concludes the risk is handled.

`CORE_API_CLIENT_TOKEN` — a live bearer credential embedded as a Power BI model parameter — reached
**9 tracked files across 10 pushed commits** over roughly twelve weeks. Two controls existed the
whole time:

| Control | Why it was inert |
|---|---|
| `pbi_ops/.gitignore` excluding `*.tmsl.json` and `*_rollback*.json`, added 2026-06-26 | **gitignore never affects already-tracked files.** Four of the six offending files predate the rule, so it landed and silently did nothing about them. Two more were force-added after it. The rule reads as coverage and is correct as written |
| A redaction function in `_gp319_clone_rehearse.py`, added 2026-08-25 after the leak was first noticed | **It lived in one script out of thirteen that serialize TMSL.** The very next rollback capture, `_gp328_add_seller_dim.py`, wrote the credential again **two days later** — the fix was one file away and nobody called it |

⭐ **A fix that lives in a single call site is not a control; it is a coincidence that has to be
re-enacted by memory every time.** The remedy in both halves was structural rather than more
diligence: one shared `write_tmsl_safely` in `pbi_ops/xmla.py` that **every** dump routes through,
fail-closed so it refuses the write rather than warning, plus `git rm --cached` so the ignore rule
finally applies to the files it always named.

Detection questions that would have caught both, and neither of which is "is the rule correct?":

- **"How many call sites bypass it?"** Not "does it exist". Thirteen scripts serialized TMSL; one
  redacted. That ratio is the control's real strength.
- **"Does this rule apply to the objects already in the state it forbids?"** A `.gitignore` added
  after the fact answers *no*, always, and silently.
- **"Would it refuse, or merely warn?"** A warning on a secret write is a secret write.

The same run also produced the positive form: name-based redaction of `model.expressions` was
sufficient for today's model, but a deliberately planted secret in an annotation sailed past it — so
the writer additionally scans the **whole serialized document** for every literal it redacted and
raises. The guard-that-can-fire was proved by making it fire, which is the [[inquest-bug-resolution]]
discipline applied to a control rather than a defect.

## 2026-08-29 — the fourth shape: a test that pins a weaker property than its own name

[[agent-factory]]'s `factory/evaluator.py` opens with an explicit guarantee:

> *"A verdict is accepted only if it names the evaluator identity, the evaluator bundle hash, and
> the corpus it was scored against."*

`RemoteVerdict.parse()` enforced it by checking that the attribution **keys existed**, then read
their values with `payload.get("evaluator") or {}`. Reproduced verbatim:

```
RemoteVerdict.parse({'verdict':'PASS','promotable':True,'evaluator':None,'scored_against':None})
  is_pass    : True
  promotable : True
  summary    : PASS for r1 - by unidentified, bundle ?
```

`certify --remote` exits **0** on that, and anything on a socket can emit it. This is the promotion
gate for the whole factory.

⭐ **The part that generalises is not the missing null check — it is the test.** A test named
`test_an_unattributed_verdict_is_not_believed` existed and passed, and it **omitted the attribution
keys entirely**. It therefore pinned *presence* while the guarantee it is named for is about
*content*, and could not express the payload that defeats the gate. Rewritten as 9 parametrised
cases supplying the keys with null, empty, whitespace and wrong-typed values, **8 of 9 failed
against the unfixed file** — the ninth was the single case the old test already covered.

> **A test that supplies fewer fields than the failure mode needs is testing a different property
> than the one in its name.**

That is a fourth shape on this page. The earlier three are an **empty verdict**, a **gate that
cannot fire**, and an **inert control**; this is a *guarantee whose test cannot express its own
violation*. All four survive a review that reads the assertion and the check side by side, because
in every one of them both are correct — the gap is in what the test never supplies.

**Detection.** For any test named after a guarantee, construct the **cheapest payload that satisfies
the check and defeats the guarantee**. If that payload is not in the test, the test is not pinning
the guarantee. Prefer parametrised cases varying **one field at a time**: the null case, the empty
case and the wrong-type case are three different bugs, and one of them is usually live.

⚠ **The counterpart trap on the fix side.** The obvious hardening — *require every attribution field
on every verdict* — would have broken the service's honest refusals, which emit
`scored_against: None` on purpose for `REFUSED` and `UNMEASURABLE` because nothing was scored. A
strictness that turns an honest refusal into a parse error destroys the reason the caller needed.
The rule that survives both is **verdicts that were scored must name their world; verdicts that were
never scored must not be required to invent one.**

## 2026-08-29 — the fifth shape: the verdict exists and the AGGREGATE discards it

The first four shapes are all *content absent from a healthy container*. This one is the opposite
and is harder to see: the content is **present and correct at the row level**, and the arithmetic
one layer up throws it away. Found by a six-lens `/prospect` build-vs-adopt pass over
[[agent-factory]]'s four-verdict model (`PASS / FAIL / UNMEASURABLE / NOT_RUN`), which set out to
show the model was novel and found the opposite — then found something better.

**Six mature tools and standards already carry a "could not measure" state**, all read at primary
source: OpenSSF Scorecard (`InconclusiveResultScore = -1`, *"returned when no reliable information
can be retrieved by a check"*), Soda Core (`CheckOutcome.NOT_EVALUATED` **and** `EXCLUDED` — two
states for two different claims), datacontract-cli (`ResultEnum` with seven members), Dagster
(`EXECUTION_FAILED  # hit some exception`, `SKIPPED  # the check didn't execute`), W3C EARL 1.0
(`earl:CannotTell`, `earl:NotTested`), and XCCDF/NIST IR 7275 (`ERROR`, `UNKNOWN`, `NOT_CHECKED`,
`NOT_APPLICABLE`, `NOT_SELECTED`). The state is twenty years old and standardised.

**And every one of them discards it at the score:**

| Tool | How the aggregate defeats the verdict |
|---|---|
| **OpenSSF Scorecard** | Inconclusive checks are `continue`d — dropped from **both** numerator and denominator. **10 of 18 checks inconclusive can still score 10.0/10.** |
| **OHDSI DataQualityDashboard** | `countPassed <- countTotal - countOverallFailed`, and `notApplicable`/`isError` rows carry `failed == 0` — so both **round UP to passed** in the published `percentPassed`. A run where the table is missing entirely reports those checks as *passed*. |
| **XCCDF / OpenSCAP** | The ignore-list covers `NOT_SELECTED`/`NOT_APPLICABLE`/`INFORMATIONAL`/`NOT_CHECKED` — but **not** `ERROR` or `UNKNOWN`, which fall through and score **0.0, identical to FAIL**. The richest verdict enum in existence, and its scoring layer still cannot say "I could not measure this." |
| **Great Expectations** | `successful = sum(exp.success or False ...)`; `unsuccessful = evaluated - successful`. **No third bucket**, and `success=None` (its own *unresolved* state) coerces to `False`. An expectation whose instrument crashed is counted as a **failing** expectation. |
| **Grafana** | "No Data" is a real, distinct state — shipped with a configurable **"Set Normal state"** handler that rounds absence-of-measurement to healthy. |
| **pytest** | `skipped` / `xfailed` exist and, in the docs' own words, *"don't fail the test suite by default."* |

⭐ **The representation problem is solved everywhere. The aggregation problem is solved nowhere.**

So the property worth protecting is not *having* a fourth verdict — it is that **UNMEASURABLE must
survive aggregation as a refusal**: not dropped from the denominator, not counted as passed, not
scored as failed, and **with no configuration path to defeat it**. Grafana ships the switch; pytest
ships the default. [[agent-factory]]'s `readiness.py` keeps an UNMEASURABLE gate **in the
denominator** so it holds the board below all-pass, and `contract.py` ranks
`ERROR > FAIL > UNMEASURABLE > PASS` — *"a crash is not a pass."*

⚠ **Corrected 2026-08-30.** This paragraph read *"ranks `FAIL > UNMEASURABLE > PASS` with any
instrument exception becoming UNMEASURABLE"*, which was accurate then and was **itself a collapse**
— an unhandled crash and a probe that declined to look are different claims. Fixed the same day;
see the 2026-08-30 section below.

**The same pass found the shape inside a candidate tool, in the classic form.** `datacontract-cli`'s
`create_checks.py` (673 lines) has **seven** `logger.warning(...) → return []` paths — a declared
rule that cannot compile emits **zero** check objects — and the file **never imports `Run`**, so the
warning reaches a module logger and never the structured result. The rule vanishes and the run still
reports `passed`. That is `bash-guard.sh` exiting 127, shipped inside a maintained product.

⭐ **The generalisable rule: a correct verdict is not a control until you have read what consumes
it.** Check the aggregate, the score, the rollup and the exit code — the enum is where you *look*
for the property and the arithmetic is where it *dies*. Ask: *if every check returned "could not
measure", what does this system print?* If the answer is a green number, the verdict is decorative.

⚠ **Instrument note from the same pass, worth its own line:** `gh api search/code` and `gh search
code` returned **0** for a string verified to exist in the target repo (a `gho_` OAuth token without
code-search scope), with **no error**. A positive control caught it. Every code-search zero without
one is **NOT-VISIBLE, not ABSENT**. And `WebFetch` returns a *small model's summary* even when
pointed at raw source — it is a `DOCUMENTED`-tier instrument, and it produced a materially
incomplete read that `curl` + `cat` settled as fact. Use `curl`/`gh api` for any claim that will
carry a verdict.

## 2026-08-30 — the sixth shape: the verdict was correct and the TRANSPORT discarded it

The fifth shape is an *aggregate* that throws away a correct verdict. This is the same loss one
layer lower and far more mundane: **the shell**. Three findings from one [[agent-factory]] session,
the first of which produced two confidently wrong reports to Paul inside an hour.

### ⛔ The pipe that eats the exit code

```bash
python -m pytest tests/ -q 2>&1 | tail -25     # reports exit 0 on a FAILING suite
```

The shell reports the **pipeline's** exit status — `tail`'s — not pytest's. A run with **15
failures** was reported as "completed, exit code 0", twice, and believed both times. The failure
list was in the output; the *verdict* was replaced by an unrelated process's success.

The same trap wears a second costume: `timeout 300 <cmd>` kills the run at the limit, yielding exit
143 **and an empty output file** — which reads as "nothing to report" rather than "no result".
Three separate measurements were lost to this in one session.

```bash
python -u -m pytest tests/ -q > /tmp/out.txt 2>&1     # redirect, don't pipe
echo "EXIT=$?"                                        # capture on its own line
```

⭐ **Any command whose exit code is the evidence must not be piped, and must not be wrapped in
`timeout` unless the timeout itself is the measurement.** This is the fifth shape at shell
granularity: the instrument was correct and the transport lost it.

### An absence is only as wide as the repos you opened

A fourteen-component ecosystem inventory declared four components **`ABSENT` across the estate**
— having opened two of the four repositories that hold them. `conductor` was never opened, and it
contains `engine/work_guard.py` (*"repo safety checks, session locks, and execution gating"*, driven
by a declarative `config/work-guard-policy.json` with `blockedPaths` and `approvalRequiredFor`,
whose `safe_to_run()` is an admission function) and `engine/audit.py`, an append-only evidence log.

⭐ **A component audit must NAME the repositories it searched, and may record `ABSENT` only when
every named repository was actually read.** Otherwise the verdict is `NOT-VISIBLE`. This is the
`gh api search/code` instrument note above, generalised from one tool to a whole estate — and it was
committed *inside the document defining the estate's component inventory*, hours after a research
wave made the same class of error and caught it.

### The distinction we were proud of was one category coarser than 1991

[[agent-factory]]'s flagship property is *never collapse FAIL and UNMEASURABLE*. A prior-art pass
found the discipline **standardised in ISO/IEC 9646 and carried by TTCN-3** (ITU-T Z.140 §24.2) as a
monotone lattice with **five** verdicts:

```
none < pass < inconc < fail < error
```

`inconc` is UNMEASURABLE. **`error` is failure of the test apparatus itself** — set by the test
system, never the test case, and overridable by nothing. `contract.py` had no such state: a bare
exception became UNMEASURABLE, so *a broken probe and a probe that declined to look were the same
verdict*. The module whose entire purpose is refusing to collapse two kinds of not-knowing was
collapsing two kinds of not-knowing.

Fixing it **exposed a second live bug**: `evals.py` folded every non-PASS into FAIL, so a mutation
that **crashed the instrument scored as a mutation caught** — a broken probe counted as evidence the
contract works, which is this page's reference shape exactly.

⭐ **Before claiming a verification distinction is novel, check whether conformance testing
standardised it decades ago.** The answer here was thirty-five years old, better shaped than ours,
and free.

### And the harness that certifies a tree that no longer exists — second occurrence

`scripts/mutate_readiness_probes.py` holds anchors copied from production source in
[[prefect-connectors]]. **Fourteen match no current branch**, and the second harness
(`tests/orchestrator/mutate_control_plane.py`) exists on no branch at all. So fourteen mutation
controls are UNTESTED while a twenty-minute harness still reports *"all mutations flipped their gate
off PASS"* — true of a tree that no longer exists. The file's own docstring records this happening
on 2026-08-22 and exists to prevent it. **A guard that fires only when someone runs it has not
stopped being a mechanism.** It is caught in the ordinary suite now, but only because the suite was
run — there is **no CI in that repo** (`.github/workflows` does not exist), and the strict tracker
drift check runs only at lane handoff.

## See Also

- [[agent-session-completion-signals]] — the sibling failure: content genuinely PARTIAL while every instrument reports arrival (a proxy for done-ness fails toward "done")
- [[pbi-xmla-automation]] — the operational half of the 2026-08-27 case: TMSL exports carry credentials, and surgical vs full-model rollback on a shared model
- [[answerability-guard]] — the four ways a guard test battery lies, including vacuous passes
- [[schema-dialect-drift]] — the vacuous mutation test, and *a mismatch you can measure is not evidence you found every mismatch*
- [[conclave-pr-review]] — adversarial re-verification of every merge-gating claim before it reaches a human
- [[inquest-bug-resolution]] — discriminating tests with the result predicted before the run
- [[github-actions]] — the green run that published nothing
- [[orchestrator]] — `trigger_and_wait` swallows exceptions; assert on the absence of the specific refusal
- [[prefect-connectors]] — where the reference case was produced
- [[agent-factory]] — the 2026-08-29 promotion gate, and the intake portal whose whole safety property is that an unanswered question stays unanswered
