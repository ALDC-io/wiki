# Shared context for the agent-factory design research (2026-08-22)

You are researching for a design spec for `github.com/ALDC-io/agent-factory` (private).
A read-only clone of the repo is at `/home/user/agent-factory` (branch `work` =
`origin/feat/readiness-generator`). Read it. Do NOT write to it, and do NOT write to
/home/user/wiki at all.

## What the thing is

A factory for building and certifying agent teams that do **data engineering** work
(connector migration into Snowflake, then Power BI) at a small consultancy (ALDC).
Its premise: this estate has twice shipped mechanisms that acted without anything
measuring whether the action helped — an agent with 233 diagnoses / 234 escalations /
**0 fixes** over 81 days, and a loop that ran 965 times, recorded its own 1.6% success
rate, and never adjusted. So the ordering is: what "done" means, then whether that
definition can fail, then everything else.

## Measured state (2026-08-22)

| Fact | Value |
|---|---|
| Isolation unit | git worktree on the operator's Windows machine |
| Max concurrent lanes (conflict graph max independent set) | 3 |
| Cross-agent PR conflict rate on a shared branch (published study, ~33k agent PRs) | 41.7% |
| Sandboxing | **none** — agents run as the user with the user's credentials |
| Data blast-radius control | **none** — no dry-run gate, no row-count diff, no rollback capture |
| Cost telemetry | **none** — nothing records tokens or wall clock |
| Readiness gates passing | 9 of 30 |
| Eval corpus | 1 case, 0 strata |
| Agent version-hash dimensions covered | 0 of 15 |
| Gate events that were ever a refusal | 0 of 22 |
| Recorded orchestrator runs that finished with no human | 3 of 14 |

## Prior research already done (read these before duplicating)

`/home/user/agent-factory/docs/research/SYNTHESIS.md` and `docs/research/answers/`.
Headline conclusions already settled — do NOT re-litigate, build on them:
- **Do not build a 3-agent architect→implementer→tester team.** One end-to-end worker
  agent + a **non-LLM verifier** holding the authoritative PASS bit. Multi-agent averaged
  −3.5% across 180 configs; sequential tasks degraded 39–70%.
- **Do not optimise yet.** Bounded, reapable, fail-closed, independently evaluable first.
- Four verdicts never collapsed: PASS / FAIL / **UNMEASURABLE** / NOT_RUN.
- Tamper-evidence (hash-pinned corpus) is not a trust boundary; an evaluator **service with
  its own identity** is (a separate local process is "mostly theatre").
- Calibrating on one run is folklore; a 10%-prevalence blind spot needs 29 cases.

## The strawman being attacked

`/home/user/agent-factory/docs/specs/architecture-v0.md` — four planes (DECIDE / RUN /
PROVE / APPROVE) and an **isolation ladder** where an agent's tier is chosen by *what its
task touches*, not by what kind of agent it is:
- **T0** git worktree, repo files only, no egress, no DB verbs
- **T1** container, egress allowlist, read-only warehouse role (SELECT on real data)
- **T2** container + **ephemeral zero-copy clone schema** dropped on exit, full DDL/DML
  inside the clone only

§7 of that doc names where it is most likely wrong. Your job is to settle those with
external evidence.

## Evidence tiering — MANDATORY

Every claim you report must carry one of:
- `MEASURED` — you or the repo ran it and have the number (name the file/command)
- `DOCUMENTED` — vendor/primary docs say so (give the URL and quote the sentence)
- `REPORTED` — a paper, study or credible practitioner writeup says so (URL + the number)
- `REASONED` — an argument from constraints, no source
- `BET` — a judgement call that could be wrong

Read the primary source, not the launch post. A vendor blog claiming a feature is
`REPORTED`, not `DOCUMENTED`, until you find it in the reference docs. If you cannot
verify something, say **"could not verify"** — that is a finding, not a failure.

## Output

Write your report to the path given in your task prompt (under the scratchpad).
Structure it as:
1. **Verdict** — 3–6 sentences, the answer to your brief
2. **What the evidence says** — findings, each tiered, each with a URL where applicable
3. **What this changes in the spec** — concrete, name files/sections in agent-factory
4. **What I could not settle** — the honest gaps, and what would settle them
5. **Sources** — URL list

Then return a ~400-word summary as your final message. Be concrete and numeric.
Prefer "could not verify" over a confident guess.
