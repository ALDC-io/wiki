---
tags: [process, operations, workflow, telemetry, measurement, agent-factory, boot-prompts, evidence-gate]
aliases: [workflow telemetry, ninety-three days of commits, workflow weaknesses]
sources:
  - "Artifact: Ninety-Three Days of Commits — https://claude.ai/code/artifact/57aebb0b-f2b5-4538-bfc1-9a7dfbcb79bf"
  - "Measured from working copies in C:\\Users\\PaulRussell\\repos, 2026-08-29"
created: 2026-08-29
updated: 2026-08-29
---

# Workflow telemetry, 29 May – 29 Aug 2026

**1,958 commits · 23 active repositories · 93 days, 89 of them active.** Every figure below was
measured from the working copies, carries the command that produced it, and can be re-run. Nothing is
sampled or estimated.

⚠ **Two caveats the source states and this page keeps:** commit counts are a **proxy** for effort, not
a measure of it — a 105-commit day and a 3-commit day can be the same work. And 45 of the 68
directories under `repos/` were dormant and are **excluded**, not counted as zero.

## What is working — do not "fix" these

| Strength | Measure |
|---|---|
| **Documentation is the largest single output** | `docs:` 427 commits — ahead of `fix:` (333) and `feat:` (331). Plus 70 new wiki pages, 262 evidence docs, a 135-commit wiki maintained in parallel with delivery. Inverted from almost every engineer's history: knowledge is externalised rather than held in one head. |
| **Commits are small and bisectable** | Across the six busiest repos, 60–74% of commits touch ≤3 files; averages 3.0–8.4. A bisect would actually work. |
| **The evidence gate produces artifacts** | 104 evidence docs in `aldc-launchpad`, 66 in its docs repo, 40 in `prefect-connectors`, 32 in `agent-factory`. A written process that leaves no artifacts is decoration; this one leaves them at scale. |
| **Four contexts held without stalling** | 793 commits client delivery · 724 Zeus platform · 361 internal agent tooling · 85 own product. |

## Where it leaks — ranked by cost

### ⭐ 01 · The session handoff has become the work

**247 boot prompts in 93 days — 2.8 per active day, 31,354 lines.** A mid-sized codebase written
purely as context-reload scaffolding. The problem is the ratio, not the practice:

- **214 live · 25 archived** — threads open ~9× faster than they close.
- **124 of the 214 (58%) untouched for over a month.** Largest age bucket is 31–60 days.
- **The `navira` family alone is 101 distinct live topics.**

> They are no longer handoffs. They are a backlog wearing a handoff's clothes.

```
ls -1 boot-prompts/*.md | wc -l           # 214 live
ls -1 boot-prompts/_archive/*.md | wc -l  #  25 archived
```

### 02 · Three repos absorb five fixes per feature

`fix:`/`feat:` above 1.0 means re-entering code more often than extending it.
**`core_api` 5.50 · `zeus-chat-exp` 5.07** — and together the three worst carry 789 of the 1,958
commits. By contrast `neurospect-learn` is **0.10** and `triage-agent` **0.15**: the same hands, when
the code is new and the loop is tight. **The tell: the feedback loop in those repos is a human running
the thing and noticing, not a test failing.**

### ⭐ 03 · The busiest delivery repo is the least test-protected

| Repo | Files touched | Test files | Share | Evidence docs |
|---|---:|---:|---:|---:|
| `aldc-launchpad` | 2,939 | 17 | **0.6%** | 104 |
| `neurospect-learn` | 472 | 34 | 7% | 21 |
| `agent-factory` | 194 | 27 | 13% | 32 |
| `zeus-memory` | 389 | 113 | 29% | — |
| `zeus-chat-exp` | 358 | 129 | 36% | 17 |
| `prefect-connectors` | 251 | 97 | 38% | 40 |

**The substitution is the finding.** An evidence document proves a fix worked *once*, on the day it
was written, under a human's eye. **It does not re-run.** CLAUDE.md gate #3 asks for "prove no
regression" — that proof currently has a shelf life of one afternoon. The repos with the heaviest
churn lean hardest on narrative evidence and thinnest on automated cover.

### 04 · 3.6 repositories per day, and the week never tapers

49 of 89 active days touched ≥4 repos; six touched seven. **Friday is the heaviest day (444
commits)**; weekends carry 350 more. Peak hour 16:00 (188), **110 commits land between midnight and
05:00**, and the 18:00-onward tail carries 517 — over a quarter of the window.
**Finding 01 is a symptom of this**, not an independent problem: every switch costs a context reload.

### 05 · Real work stranded outside version control

Measured on the day: **126 uncommitted in `aldc-launchpad`, 29 in `prefect-connectors`, 25 in
`neurospect-learn`, 22 unpushed commits on `triage-agent` main.** Loss risk with no upside.

### 06 · The system accretes faster than it is pruned

Two habits in CLAUDE.md are **dead in practice**: the daily-notes inbox has had no entry since
2026-05-22, and `skills/INDEX.md` has drifted **twice** — corrected 08-11, wrong again by 08-29 — in a
file whose own text warns about that failure. **Dead rules dilute live ones and train you to skim the
document that is supposed to be authoritative.**

### 07 · Commit discipline regressing on the newest repo

`neurospect-learn`: **25.5 files/commit, 18% of commits over fifty files**, against 3.0–8.4 elsewhere.
The newest, most personally-owned codebase is the one place the batching habit has not carried.

## The six changes, by return on effort

1. **Make closing a thread as cheap as opening one.** Archive-on-open: any session that reads a boot
   prompt must archive or rewrite it before finishing — never leave it as found. Weekly sweep moving
   anything untouched 21 days into `_archive/` clears **124 files today**. Collapse the 101 live
   `navira` topics into one status document with a task list. **Target: ≤20 live boot prompts.**
2. **Add a failing test to the evidence gate.** Amend CLAUDE.md gate #3 so accepted proof of "no
   regression" is a test that **fails without the fix and passes with it**, committed beside the
   evidence doc. Start with `core_api`, `zeus-chat-exp`, `zeus-memory`. **Target: fix:feat < 2.0.**
3. **WIP-limit repositories per day.** Batch a repo into a day rather than scattering it across a
   week. Upstream fix for handoff volume. **Target: ≤3 repos/day, from a mean of 3.63.**
4. **Make counts unwritable by hand.** The rule has been documented twice and re-rotted twice, so the
   rule is not the fix — the mechanism is. A `make stats` target plus a pre-commit hook that fails on
   a stale generated block. **Target: zero hand-maintained counts.**
5. **Schedule the rest instead of hoping for it.** Four idle days in ninety-three, Friday heaviest,
   110 post-midnight commits — and the two worst rework repos are the ones worked latest.
   **Target: 1 rest day/week.**
6. **Prune instructions as hard as you extend them.** Delete or revive the daily-notes workflow; run
   the same pass over the skills library. **Target: every CLAUDE.md rule fired at least once this
   quarter.**

## Why this belongs beside [[agent-factory]]

⭐ **Each leak already has a mechanism in `agent-factory` — several built, several unwired.**

| Finding | The mechanism that answers it | State |
|---|---|---|
| 01 boot prompts as backlog | `factory/tasks.py` — append-only, **close requires MEASURED or DERIVED evidence** | built, unused for this |
| 02 / 03 evidence that cannot re-run | `GreenContract` + known-bad calibration — an assertion proven able to FAIL | built for connectors only |
| 05 stranded work | the `durable` readiness gate | ⛔ **broken** — runs `git remote`, never reads push state; green by coincidence |
| 06 hand-typed counts | generated-registry pattern (`docs/artifacts/registry/build.py`) | built, applied to artifacts only |

**`factory/tasks.py` is the direct answer to Finding 01.** 214 live boot prompts opened nine times
faster than closed is precisely *a hand-maintained board wearing a computed status* — which
`factory/board.py` already names as the defect it exists to prevent. Migrating handoffs into the task
store converts a 31,354-line scaffolding corpus into a tracked backlog whose rows cannot close without
evidence.

## See Also

- [[agent-factory]] — the mechanisms above
- [[session-contention-and-artefact-homes]] — where a given file belongs, and the registry that measures it
