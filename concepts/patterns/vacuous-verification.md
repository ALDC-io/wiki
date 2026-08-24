---
tags: [pattern, verification, evidence, agents, review, quality, claude-code]
aliases: [vacuous verification, vacuous verdict, verdict without content, schema-degenerate agent return]
sources: [prefect-connectors session 2026-08-14 (docs/KNOWN_ISSUES.md issues 22-26), concepts/patterns/answerability-guard.md, concepts/patterns/schema-dialect-drift.md, concepts/patterns/conclave-pr-review.md]
created: 2026-08-14
updated: 2026-08-23
---

# Vacuous Verification

**A verification pass can return a result that is structurally perfect and completely empty.** The
verdict field says `CONFIRMED`; the reasoning field says `"test"`. Downstream, only the verdict is
read — so a verification that did no verifying is indistinguishable from one that did, and it
propagates as fact.

This is the generalisation of a failure ALDC has now hit in five different mechanisms: an agent
return, a CI check, a mutation test, a guard-test battery, and an exception-swallowing test helper.
In every case the *container* of the evidence was healthy and the *content* was absent.

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

## See Also

- [[agent-session-completion-signals]] — the sibling failure: content genuinely PARTIAL while every instrument reports arrival (a proxy for done-ness fails toward "done")
- [[answerability-guard]] — the four ways a guard test battery lies, including vacuous passes
- [[schema-dialect-drift]] — the vacuous mutation test, and *a mismatch you can measure is not evidence you found every mismatch*
- [[conclave-pr-review]] — adversarial re-verification of every merge-gating claim before it reaches a human
- [[inquest-bug-resolution]] — discriminating tests with the result predicted before the run
- [[github-actions]] — the green run that published nothing
- [[orchestrator]] — `trigger_and_wait` swallows exceptions; assert on the absence of the specific refusal
- [[prefect-connectors]] — where the reference case was produced
