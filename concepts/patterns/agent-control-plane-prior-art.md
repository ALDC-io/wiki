---
tags: [pattern, agents, orchestration, control-plane, prior-art, claude-code, sandboxes, agent-factory]
aliases: [Paperclip, Super Simple Software Factory, SSSF, Inkwell, agent control plane prior art, software factory prior art, best-of-N, worktree vs sandbox]
sources: [github.com/paperclipai/paperclip @ master (79734 stars, MIT), github.com/disler/super-simple-software-factory (773 stars, MIT), github.com/disler/inkwell-agent-sandboxes-and-software-factory (147 stars, MIT), agent-factory session 2026-08-31, agent-factory/.agent-platform/RECONCILIATION.md]
created: 2026-08-31
updated: 2026-08-31
---

# Agent control-plane prior art — mine, do not clone

> Three mature open-source agent orchestrators, read at source rather than from their READMEs on
> 2026-08-31, to answer one question before building anything: **does a simpler mechanism already
> exist?** All three are MIT. The most valuable output is not what to adopt — it is the five
> patterns that let you *delete* machinery, and the four README claims that do not survive contact
> with the code.

## ⚠ Read this first — three traps that cost time

| Trap | Reality |
|---|---|
| `paperclipai/paperclip` raw URLs 404 on `/main/` | Its default branch is **`master`**. The repo is very much alive — pushed daily. |
| Web search attributes **E2B sandboxes** to Inkwell | That is a *different* disler repo (`disler/agent-sandboxes`). Inkwell uses **exe.dev VMs over plain SSH** — no Docker, no E2B. Do not let the phrase into a downstream doc. |
| SSSF looks like a Claude Code factory | It drives **`pi`**, disler's own agent. `agent_cc.py` is a stub that raises `NotImplementedError`, and its config validator hard-rejects any non-`pi` agent. **Pattern-level prior art only — not a component you can run.** |

## ⭐ The five patterns that DELETE machinery (SSSF)

This is the highest-value section on the page. Each replaces something you would otherwise build.

1. **A Python function replaces the workflow engine.** No DAG, no YAML DSL, no state machine, no
   resumable graph. `main()` *is* the graph, a `with run.phase(...)` block is the node, `if
   verified:` is the edge. Nothing serialises workflow state because the call stack already holds
   it. *Replaces: workflow definition format, graph executor, node registry.*
2. **`kind="code"` phases replace whole agents.** Their hard rule: *"a known command is code, not an
   agent."* There is **no tester agent** — running the suite is a subprocess. Deleting it deletes a
   prompt pair, an envelope type, a token budget, and a source of nondeterminism. *This is the
   difference between a 5-agent factory and a 15-agent one.*
3. **One envelope adapter collapses result-type dispatch.** A deterministic command's result is
   adapted into the same shape an agent returns, so the repair loop has exactly one code path — no
   `isinstance` branching on "did a human, a subprocess or an agent produce this failure?"
4. **Post-hoc git change-set diffing replaces sandboxing.** Fingerprint the working tree before the
   agent runs, diff after. ~100 lines. It catches what a write-interceptor *cannot*: reversion.
   Their premise, from a real incident — *"`tools:` is a capability list, not a sandbox. A builder
   handed bash to run a test suite can also run `git checkout`, which is not hypothetical: one did,
   discarding uncommitted changes to the very quality check it was about to be judged by."* A path
   modified before the agent ran and clean afterwards **has been reverted, and a reversion is a
   modification.**
5. **SQLite + `rowid` polling replaces the entire streaming stack.** One file, WAL, `WHERE rowid > ?`
   every 500ms. No broker, no WebSocket server, no event bus, no ingest API — and because the live
   view and the history are literally the *same query*, **no replay subsystem either.**

## The patterns worth adopting (Paperclip)

Paperclip is the mature one — 288 server services, 232 migrations, a 20,402-line heartbeat module.

- **Atomic task checkout is a two-stage compare-and-swap**, not `SKIP LOCKED` (grepped: zero hits in
  the whole tree). Each stage is one statement: `UPDATE ... WHERE status='queued' RETURNING`. Under
  READ COMMITTED the loser blocks, re-evaluates against the committed row, and matches zero rows.
  Works identically in SQLite and Postgres, and is strictly simpler than the queue you would
  otherwise reach for.
- **Session identity keyed on `(agent, adapter, task)`, not `(agent)`.** One agent working three
  issues holds three independent live CLI sessions. *This is the difference between resuming work
  and restarting it.*
- **Resumability degrades in four layers**, each catching the previous one's failure: live session
  id → `--resume` → session rotation with a written handoff note → a durable continuation summary
  that survives total session loss.
- **A content-hashed skill bundle handed to `--add-dir`.** Build `<cache>/<sha256>/.claude/skills/<name>`
  as a symlink farm; the hash covers the instructions plus a recursive content hash of every skill
  file. Same skills ⇒ same path ⇒ **the prompt cache stays warm across runs and across agents**, and
  a changed skill busts the key *and* correctly refuses to `--resume` a session saved under the old
  one. Directly portable.
- **OS-level liveness (`kill(pid, 0)`) over timestamp heuristics** — cheaper and more truthful.
- **An approval bound to a hash of the exact reviewed arguments**, re-checked at execution, with a
  missing signing secret failing closed. *That is the difference between an approval and a rubber
  stamp.*
- **Git worktree per issue, not per run**, with a `branch_created_by_runtime` flag so cleanup never
  deletes a branch a human made.
- **`cost_status: unpriced | reported`** — one column separating "spent nothing" from "could not
  measure". See [[vacuous-verification]]; this is that rule at the ledger row.

## ⛔ Four claims that do not survive the code (Paperclip)

Inheriting these would be the expensive mistake.

1. *"Task checkout and budget enforcement are atomic."* **The checkout half is true; the budget half
   is false.** Budget admission is 4–5 sequential unguarded `SELECT`s, no transaction, ~80 lines and
   several `await`s from the claim. Textbook TOCTOU.
2. **No per-model pricing table exists anywhere.** Cost is whatever the agent CLI self-reports, and
   several adapters hardcode `costUsd: null`. Those runs burn real tokens and contribute **zero** to
   every budget sum. The code even labels them `"unpriced"` and then sums **without filtering on
   it** — a blind instrument reporting a zero, in someone else's codebase.
3. **No task lease or TTL.** The lock timestamp is written in six places and *never compared to
   anything*. A dead worker's lock never expires. (Their one *correct* lease — unique-constraint
   anchor, `FOR UPDATE`, 30-minute TTL, six named stale reasons — is on workspaces, and is the best
   concurrency pattern in the repo. Copy that one, not the task lock.)
4. **It is a single-server design and this is documented nowhere.** The task claim is genuinely
   cross-process safe, but the orphan reaper and the concurrency cap key off **in-process maps**.

## The worktree-vs-sandbox boundary (Inkwell)

Inkwell is the isolation reference. Its answer for a local, single-operator factory is
**worktrees are enough** — but the boundary is worth stating exactly:

> A worktree is sufficient while a misbehaving agent's worst outcome is **losing work you can
> regenerate**. A sandbox becomes warranted when the worst outcome is **reaching something you
> cannot** — production credentials, a client's warehouse, the shared git object store, or an
> unbounded bill.

A worktree isolates exactly one thing: the working directory and the checked-out branch. It does
**not** bound ports, filesystem blast radius outside the tree, the **shared git object store**
(one `git gc` or `reset --hard` reaches every worktree), ambient credentials, or spend.

⭐ **So the gap to close first is credentials, not isolation** — and both are available without a VM:
a **capped, disposable, per-run credential**, plus the post-hoc git-diff enforcement above. Inkwell's
measured trap on revocation is worth carrying verbatim:

> *Right after a successful DELETE, `GET /key` still returns 200 for the dead key. **The LIST is the
> authoritative view. Never gate on `/key`.***

Other Inkwell patterns that transfer unchanged:

- **Teardown is never chained.** `mount` runs create → fill → setup → observe and **stops**, because
  *"a destroyed VM is the evidence and the artifacts, gone."* Maps directly onto never auto-running
  `git worktree remove`.
- **Ordering is itself the safety property.** Teardown goes spend → artifacts → harvest → revoke →
  destroy, and **a harvest failure aborts the entire teardown**, leaving the box alive.
- **Harvest writes only to `refs/sandbox/<id>`** — never a branch the user owns — and uses a *ranged*
  bundle, so `git fetch` refuses it if the work does not descend from the pinned base. A free
  integrity check on the return trip.
- **Best-of-N is a loop over configs, one isolation unit per arm**, seeded on exactly three axes
  (prompt, roster, model) with **the commit pin as the control variable** — *"pin every arm to the
  same sha or the comparison is noise."* And there is deliberately **no ranked table**: harvest each
  arm and diff the refs, because the code is the artifact, not a score.
- **Health gates assert on output, never exit codes.** Their model-check exits 0 while printing
  *"No models available"*; an unsynced VM copy produced **5,641 zero-byte files** and reported no
  error. Hence: check content, not existence.

## What to reject outright

- **Their budget engine** (Paperclip) — TOCTOU plus unpriced adapters counted as zero.
- **A deletable audit log** (Paperclip) — deleting an agent purges its own audit trail.
- **`echo` placeholder quality checks** (SSSF) — every check ships as `["echo", "PLACEHOLDER…"]`,
  `echo` exits 0, so a freshly stamped repo reports a verified green run **having tested nothing**.
  The authors warn about it in a 20-line banner. *A banner is not a control.* Adopt the module,
  invert the default to exit 1.
- **Vendor sandbox lock-in** (Inkwell's exe.dev) — Linux-only, single-vendor, and by its own README
  *"persistent and never expire… all billing until someone decides otherwise."*
- **A 70-page control-plane IA** (Paperclip) — that is what an orchestrator looks like after chasing
  an org-chart framing.

## The honest caveat on all three

**None of it is measured.** No eval harness, no benchmark, no roster A/B, no cost baseline in any of
the three repos. The design rationale is unusually well argued — several comments read as post-mortems
of real incidents — but **arguments are not evidence**. Treat every pattern here as a well-reasoned
hypothesis, and hold it to the same bar as anything else before it ships.

## See Also

- [[agent-factory]] — the estate's own factory, and the reconciliation that decided what of this to use
- [[vacuous-verification]] — the blind-instrument family; SSSF's `echo` gate and Paperclip's unpriced cost are both instances
- [[session-contention-and-artefact-homes]] — the worktree hygiene this assumes
- [[agent-action-safety-gate]] — the local equivalent of the signed-arguments approval
- [[agent-observability-telemetry]] — where the SQLite trace schema would land
- [[conclave-pr-review]] — the review council these were mined by
