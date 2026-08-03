# ⚔ ARMY — parallel agent orchestration for arbitrary tasks

> Scale is not the skill. **Knowing what must stay serial is the skill.**

A general-purpose method for decomposing any task across parallel agents — and, more importantly, for
refusing to when parallelism would manufacture failures that look like findings.

Sibling to the three domain councils: `inquest` (resolves defects), `conclave` (reviews PRs),
`assay` (answers measurement questions). Those fix the *lens set* in advance because their domain is
known. **`army` chooses the decomposition itself**, which is why its failure mode is worse and its
guardrails need to be stricter.

---

## ⛔ Read this before spawning anything

**The default is NOT parallel.** Most tasks are faster done directly. Spawning agents costs a brief,
a synthesis pass, coordination risk, and tokens — and it *adds* a failure mode: agents corrupting each
other's evidence while both report success.

| Don't parallelise | Because |
|---|---|
| A task with a serial dependency chain | read → write → run → mutate → verify cannot be split; you'll just add handoff latency |
| Anything under ~3 genuinely independent work units | the brief costs more than the work |
| A task you can't yet decompose | you'll brief agents on the wrong frame and all of them will hunt it |
| "To be thorough" on something already verified | that's theatre, and it reads as diligence to nobody who checks |

**⭐ Size the fan-out to the independent work units, never to ambition or to the word the user used.**
If a user asks for "twenty agents" and the task contains four independent units, run four and say so.
Delivering the honest number with the reasoning beats delivering the requested number.

*Real case: asked to "10x with an extreme parallel agent team" for two component tests plus surrounding
follow-ups. The tests were irreducibly serial (mutation-testing edits source; two agents running the
suite concurrently would corrupt each other's RED/GREEN). Correct answer was **one** agent owning that
repo exclusively, plus **three** on genuinely independent work. Four, not twenty — and the critical path
was unchanged.*

---

## ⭐ Phase 1 — The conflict analysis (do this FIRST, in writing)

Before decomposing, enumerate every **shared mutable resource**. Anything two agents could both write,
or one writes while another reads, must be assigned a **single owner** or serialised.

| Shared resource | Hazard | Resolution |
|---|---|---|
| **Source files under mutation-testing** | Agent A reverts a fix to prove RED while Agent B runs the suite → both get false results | **One owner per repo.** Mutation-testing is serial by nature. |
| **A working tree's branch** | `checkout` switches HEAD under another agent/session | One owner per tree. Use `git worktree add` for isolation. |
| **A tree with another session's uncommitted work** | Your checkout strands or conflicts with live work | Read-only, or worktree. Check `git status --porcelain` count first. |
| **The same file** | Last write wins, silently | Partition by file, and say which agent owns which. |
| **Production objects** | An A/B or rollback measurement is void if a second agent mutates mid-measurement | Serialise through a lock file (see `inquest`'s `INQUEST-LOCK.md` pattern). |
| **External write APIs** (Jira, Slack, GitHub) | Duplicate tickets/comments; no idempotency | **One owner.** Make it check for duplicates before creating. |
| **State one agent reads and another mutates** | Reader gets a mixed snapshot and reports it as truth | Order them, or make the reader explicitly read-only-before. |
| **`node_modules` via junction/symlink (Windows)** | Removing a worktree through a live junction deletes the REAL shared `node_modules` | **Never** symlink it in. Verify absence before any worktree removal. |
| **Shared caches / build output** | Concurrent builds interleave | One builder, or separate output dirs. |

**Write the ownership map into the brief.** "Agent X has EXCLUSIVE ownership of Y" is the single most
useful sentence in an orchestration brief.

---

## Phase 2 — Pick the shape

Don't default to flat fan-out. Match the shape to the task.

| Shape | Use when | Note |
|---|---|---|
| **Flat fan-out** | N independent units, no cross-talk needed | The common case. Cheapest. |
| **Pipeline** (per-item stages, no barrier) | Multi-stage work over many items | Default over fan-out+barrier — wall-clock is the slowest *chain*, not the sum of slowest-per-stage |
| **Barrier** (collect all, then proceed) | Stage N genuinely needs cross-item context — dedup, early-exit, "compare against the others" | Only then. A barrier wastes every fast agent's idle time. |
| **Judge panel** | Solution space is wide; one attempt-iterated is weak | N independent attempts from different angles → score → synthesise from the winner, grafting from runners-up |
| **Adversarial verify** | A finding will drive an expensive or irreversible action | Spawn refuters prompted to **kill** it. Majority refutes ⇒ drop. |
| **Perspective-diverse verify** | A claim can fail in several ways | Give each verifier a *different lens* (correctness / security / perf / does-it-reproduce) rather than N identical ones |
| **Loop-until-dry** | Unknown-size discovery | Keep going until K consecutive rounds find nothing new. Counters miss the tail. |
| **Multi-modal sweep** | One search angle won't find everything | Agents each search differently — by container, by content, by entity, by time |
| **Completeness critic** | Before declaring done | One agent asks "what's missing — modality not run, claim unverified, source unread?" |

For deterministic control flow (loops, conditionals, budget-scaled depth), author a **`Workflow`**
script instead of hand-spawning — it gives you `pipeline()`, `parallel()`, schema-validated returns,
and resume-from-run.

---

## Phase 3 — The brief

Write it **once**, to a file. Never paste context into N prompts — they'll drift.

Every member gets:

- **Its exclusive ownership**, and what it must not touch.
- **Verify by reading real code and real state.** Never cite a line, a row count, or a result you
  didn't open or run.
- ⭐ **A negative claim needs a positive control.** Before reporting "nothing found" / "not used" /
  "no regression", prove the instrument *can* detect the thing. *A failed check is not a passing
  check — treat `error` and `empty` as different branches.*
- ⭐ **An assertion that only checks an absence can be satisfied by destroying the population.**
  Pair it with an explicit expected value. *This survives mutation-testing, so that gate won't catch it.*
- **Killing your own hypothesis is a SUCCESS.** Members are assigned a lane, not a conclusion.
- **Say what you could not verify, and why.** Never fabricate a result.
- **Severity and confidence as separate axes** — a proven-minor and a speculative-major behave
  differently.
- **Read-only unless explicitly granted a mutation**, and mutations named in advance.
- 🚨 **Delivery: your plain text is NOT visible to the orchestrator. You MUST SendMessage to `main`.**
  Otherwise you finish and idle holding the work. Cap the report length.

**Feed members your own hypotheses as "confirm, refute, or extend"** — never as conclusions. Refutation
of the orchestrator is the highest-yield output there is.

---

## Phase 4 — Synthesis: be a verifier, not a stapler

1. **Re-run the load-bearing claims yourself.** Open the file. Run the query.
2. **Prefer executed evidence over predicted behaviour**, always.
3. **Reconcile contradictions with evidence** — never average two agents.
4. **Report dissent**, including where you overruled it and why.
5. **Relay what matters.** Agent reports aren't shown to the user; a summary that drops the caveats is
   worse than no summary.
6. **Shut agents down** as their deliverable lands and is verified. Don't let them idle or loop.

---

## ⭐ Phase 5 — The self-improvement loop

This is what makes it a compounding skill rather than a static prompt. **Do all four after every run.**

1. **Score the decomposition honestly.** Was parallelism justified? Which agent was redundant? Which
   conflict did you miss? Which agent's brief was wrong? *If parallelism wasn't justified, record that —
   the anti-theatre guard is only as good as the evidence behind it.*
2. **Add a Revision-log entry** naming the **incident** that drove any change to this file. A rule
   without its provenance gets deleted by the next reader who finds it inconvenient.
3. **Mirror to version control.** `~/.claude/` is **not a git repo**, so this file is unbacked. Copy it
   byte-identically to `wiki/concepts/patterns/skills/army-SKILL.md` — byte-identical *on purpose*, so
   drift is detectable by a plain `diff`. See that directory's `README.md` for the sync contract.
4. **`/cce-learn`** the durable lessons. One dense entry beats eight padded ones.

### Mutability — how to extend this without bloating it

- **Add a row, not a section.** New hazards go in the Phase 1 table; new shapes in the Phase 2 table.
- **Before adding a rule, ask: is this genuinely new, or did I just not follow what's already here?**
  *That question removed a third of a proposed revision to `inquest` — one item was already covered
  twice elsewhere, and one was me having ignored an existing rule rather than finding a gap.*
- **Estate-specific mechanics do not belong here.** SQL dialect gotchas, one client's grant model,
  a particular repo's CI — those go in the wiki or in a domain skill. This file stays domain-general
  or it dies of bloat.
- **A lesson that doesn't transfer, doesn't go in.** Record *why* in the revision log so the next pass
  doesn't re-propose it.

---

## Revision log

### 2026-08-03 — created

Written after a session that ran three parallel councils (`inquest` on GP-309/310/311) and then a
four-agent fan-out on follow-up work. The anti-theatre guard, the sizing rule and the conflict table
are all from measured experience in that session, not theory:

- **Mutation-testing is serial** — two agents editing source while both run a suite corrupt each
  other's RED/GREEN.
- **The `node_modules` junction hazard** — a worktree removal through a live junction deletes the real
  shared directory on Windows.
- **A failed instrument is not a clean negative** — a probe reported "not consumed" when its query had
  *errored*; fixing it flipped the answer to four readers. Same class as an absence-assertion that
  passes by destroying the population, which had already cost $423K in a rolled-back deploy earlier the
  same day. **Both are in Phase 3 because both recurred after being written down once.**
- **Members refuting the orchestrator** was the highest-yield mechanic across all three councils —
  six factual errors caught before reaching a partner in one ticket alone.

## Provenance

Derived from `inquest` and `conclave` by extracting what is domain-**general** — the two gates, the
separate severity/confidence axes, feeding leads for refutation, `SendMessage` delivery, the
verifier-not-stapler synthesis — and adding what only a general orchestrator needs: **the conflict
analysis**, **the sizing rule**, and **the anti-theatre guard**.

## See Also

- `inquest` — defects · `conclave` — PRs · `assay` — measurement questions
- The `Workflow` tool, for deterministic control flow over hand-spawned agents
