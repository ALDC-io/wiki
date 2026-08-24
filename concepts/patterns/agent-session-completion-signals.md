---
tags: [pattern, agents, verification, evidence, claude-code, agent-factory, liveness]
aliases: [when is an agent session finished, agent completion signal, session liveness, done-ness, mtime stability]
sources: [agent-factory session 2026-08-23 (R17 dispatch + SYNTHESIS reconcile), aldc-launchpad/boot-prompts/agent-factory-tracker-2026-08-23-evening.md]
created: 2026-08-23
updated: 2026-08-23
---

# Agent Session Completion Signals

**Nothing an agent session leaves behind reliably says "I am finished."** Every cheap proxy for
done-ness fails in a different direction, and each failure produces the same downstream damage: a
consumer reads a partial artefact as a complete one and acts on it.

Measured on 2026-08-23 in `agent-factory`, where **three different completion signals were tried in
one evening and all three were wrong**. This is the specific-mechanism companion to
[[vacuous-verification]] — that page is about a result whose *content* is empty while its container
is healthy; this one is about a result that is *genuinely partial* while every instrument says it
has arrived.

## The three proxies, and how each fails

| Proxy | Why it looks right | How it actually fails |
|---|---|---|
| **The file exists** | the agent was told to write exactly one file | flips on the **first byte**. R17's answer registered `ANSWERED` and then grew **13 KB** |
| **The process exited** | a finished program exits | the `claude` CLI **stays resident** after finishing. A watcher polling for process exit never fired at all |
| **mtime stable for N seconds** | a finished writer stops writing | sessions **pause between sections**. A 60 s window declared done; the session wrote **751 more lines**. Retried at **5 minutes** on the next run — it fired at 144,203 bytes and the file reached **180,166**. ⭐ Lengthening the window does not fix it; there is no N that does |

### 1. File existence — `ANSWERED` means "a file exists"

`dispatch._answered_ids()` globs `answers/R[0-9]*.md`. The moment a session opens its answer file,
the research board flips that pass to `ANSWERED` and **unlocks every dependent pass**.

R17's answer was 116,925 bytes at one check and 130,397 at the next — *after* the board had called
it answered and offered R18's run button. R18 is a `STRUCTURE_CRITIQUE` that audits R17's
recommendations against our code. **Running it against a two-thirds-written R17 does not fail — it
silently produces a worse answer**, which is the exact outcome the dependency edge exists to
prevent.

⚠ Note what the existing guard did *not* cover. `blocked_by()` already had a subtle rule — a
dependency counts as met only when `ANSWERED` **and** it owes no pending run-log row — added after
an earlier scar. That rule guards *"answered once but a further run is owed"*. It has nothing to say
about *"the answer is mid-write"*.

### 2. Process exit — the CLI outlives the work

A watcher was set on the spawned pid, polling for it to disappear. It never fired. `claude` stays
resident after completing its task, so **process-alive and work-in-progress are independent facts**.

⚠ Related and separately proven: **a `wt` pid is not the session's pid.** `wt new-tab` returns
immediately and the `claude` process outlives it, so recording the launcher's pid as a liveness
token makes a claim read *free* while the session runs — a guard reporting itself unheld. This is
why `factory.claims.task_claim` records **no pid at all** and fails closed on `HELD_UNVERIFIED`
rather than storing a token it knows is wrong.

### 3. mtime stability — the pause looks like the end

The corrected watcher waited for the file to be written **and then unchanged for 60 seconds**, plus
the relevant gate turning green. Both conditions held. The work was committed.

The session then added **751 lines** — a whole new section — taking the file from 80,565 to 143,989
bytes. The commit was honest about its contents and **wrong by implication about what "reconciled"
meant**.

⭐ **A quiet window is a measurement of the agent's rhythm, not of its progress.** Long-running
sessions think, search, and read between writes; the gap between sections is indistinguishable from
the gap after the last one.

## ⭐ The lesson

**Completion is a claim only the worker can make. Everything else is a proxy for it, and a proxy
for done-ness fails toward "done".**

That direction matters. All three proxies here fail *optimistically* — they report finished while
work continues — which is the expensive direction, because a consumer proceeds. Compare
[[vacuous-verification]]'s rule that an instrument which could not look must never report a pass:
same principle, applied to time rather than content.

## Practical rules

1. **Do not treat artefact presence as completion.** If a board derives state from a glob, it is
   reporting *arrival*, not *finishing*. Say so on the surface.
2. **A gate turning green is not a completion signal either.** The gate measures its own condition,
   which a partial artefact can satisfy — the R17 reconcile cleared both `unsynthesised()` and
   `unreconciled()` while a third of its output was still unwritten.
3. **Never commit an artefact another session owns while that session is alive.** Commit *after* the
   worker says it is done, or accept that the commit captures a snapshot and say so in the message.
4. **Prefer an explicit end-of-work declaration** — a sentinel line, a status file, a registry
   update the session writes last. Nothing in this estate builds one yet; that is the gap.
5. **Where only proxies are available, state which one you used and its failure mode.** "Stable for
   60 s" is a defensible basis if it is written down as a basis. It is indefensible as an unstated
   assumption behind the word "done".
6. ⭐ **The declaration is the only signal that worked.** Measured across three attempts on 2026-08-23: 60 s stability wrong, 5 min stability wrong, process-exit never fired — and the run ended correctly the one time the session *said* it had finished, and used the same message to flag what it had NOT verified (`path:line` claims inherited from two other answers, left `REPORTED`). A worker that can declare completion can also declare its own limits, which no external proxy can ever do.
7. **Ask the human when the human is right there.** On 2026-08-23 Paul could see the terminal and
   said *"its finished"* in one message — cheaper and more accurate than every instrument tried.

## Detection

- A commit whose diff is much smaller than the work it describes.
- An artefact that grows after the surface reporting it stops changing.
- A watcher that never fires (process-exit style) — silence read as "not yet" when it is "never".
- Any board that derives state from `glob()` and reports a state word implying finality
  (`ANSWERED`, `COMPLETE`, `DONE`).

## Where this bites beyond agent-factory

The same shape applies wherever an unattended mechanism writes an artefact a consumer reads:
Prefect flow runs landing rows ([[connector-development-standards]] — "the run did not raise" is
compatible with a total extraction failure), PBI refreshes ([[pbi-xmla-automation]] — a ~0.5 s
refresh is metadata-only and still reports `Completed`), and any orchestrator gate that polls for
an output file. In each case the instrument observes an *effect* of completion rather than
completion itself.

## See Also

- [[vacuous-verification]] — the container is healthy, the content is empty
- [[session-contention-and-artefact-homes]] — two sessions in one checkout; where an artefact belongs
- [[agent-factory]] — the estate this was measured in
- [[answerability-guard]] — guards that are wrong by omission
- [[conclave-pr-review]] — verifying a claim before promoting it to a finding
