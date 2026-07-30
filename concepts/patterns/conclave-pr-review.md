---
tags: [concept, pattern, ai, claude-code, skill, code-review, pr, multi-agent, adversarial, engineering-standard]
aliases: [Conclave, /conclave, Conclave Review, Multi-Lens PR Review, Council of Five]
sources: []
created: 2026-07-29
updated: 2026-07-29
---

# Conclave — adversarial multi-lens PR review

Claude Code skill developed by Paul Russell, 2026-07-29. Convenes a **council of independent reviewers**, each locked to a different lens, reviewing the same change without seeing each other's work — then deduplicates, cross-checks, and **re-verifies every merge-gating claim against real code before a human reads it**.

**Skill name:** `/conclave`
**Location:** `C:\Users\PaulRussell\.claude\skills\conclave\SKILL.md` (+ `references/council-brief-template.md`)
**Slots into:** the *Code Owner Review* step of the [[ai-pr-workflow]] chain.
**Sibling method:** [[adversarial-investigation-skill]] (`/investigate-adversarial`, Vlad) — same adversarial philosophy, different target: that one investigates a *problem*, this one reviews a *change*.

> The conclave deliberates in isolation, then returns one verdict.

## Why it exists

ALDC repos already auto-run an Opus PR reviewer (`claude-review.yml` in [[zeus-chat-exp]] and elsewhere). Those reviews are useful but **advisory and sometimes wrong** — in the reference run below, 3 of 9 bot comments needed pushback, and 2 of those would have made things *worse* if actioned as written.

A single reviewer — human or model — has one perspective and no adversary. The failure mode is not missing things; it is **confident plausibility**: findings that read well and don't survive contact with the code. Every rule in this method exists to make findings **falsifiable**.

Design goal: **strict but reliable**. Strictness alone produces a wall of plausible findings that wastes the author's time and trains them to ignore reviews.

## The two gates — before convening anything

A council that reviews the wrong bytes is worse than no council, because its confidence is unearned.

### Gate 1 — Freshness
Never trust a local clone. Verify the working tree is the **exact** PR head SHA, and the base matches too:
```bash
gh api repos/{owner}/{repo}/pulls/{n} --jq '.head.sha, .base.sha'
git fetch origin --prune && git fetch origin pull/{n}/head:pr-{n}
git rev-parse pr-{n}; git rev-parse origin/main
```
> Reference run: the clone sat at **PR #24** while the PR under review was **#167**. Every "this doesn't exist on main" claim would have been wrong.

### Gate 2 — Environment
Install dependencies so checks can be **executed**, not predicted. Then run the project's own checks and record real output — never restate the author's test claims as verified.
> Reference run: `node_modules` was absent, silently blocking two council members. One filed a **BLOCKER predicting `tsc` would fail**. After `npm ci`, `tsc` was clean and the full suite passed 1291/1291. Installing deps turned a false blocker into a correct MINOR.

## The five lenses

| Lens | Owns the question |
|---|---|
| **Correctness & data-flow** | Does the code do what it claims, along the whole runtime path? |
| **Security & trust boundary** | What leaks, spoofs, or crosses a boundary? |
| **Ticket acceptance & root cause** | Does this fix the bug, or only its presentation? Score every acceptance item. |
| **Adversarial red-team** | Assume it merges — now make the bug reproduce anyway. |
| **Tests & verification** | Do tests protect against recurrence, or just assert code exists? **Execute** them. |

Swap/add to fit: performance & scale, API compatibility, migration & rollback, accessibility, observability, cost, docs & DX. **Five is the sweet spot** — beyond seven the marginal lens mostly duplicates.

## Rules every member gets

- **Verify by reading real code.** Never cite a line number you didn't open.
- **Every finding needs a concrete failure scenario** — inputs/state → wrong outcome. *Can't write one? Downgrade or drop it.* This single rule removes most noise.
- **Severity and confidence are SEPARATE axes** — `BLOCKER|MAJOR|MINOR|NIT` × `CERTAIN|LIKELY|SPECULATIVE`. This is what lets the synthesiser catch a member's error.
- **Adjudicate every pre-existing review comment** — confirm with new evidence, **REFUTE** with evidence, or improve the fix.
- **Report what you checked and found clean** — prevents re-litigation, shows coverage.
- **Distinguish "enforced in code" from "requested of a human/model."** For LLM features this is the whole ballgame — a prompt rule is a mitigation, not a guarantee.
- **Say what you could not verify and why.** Never fabricate a command result.

## The mechanic that pays out most

**Feed members your own leads as hypotheses, explicitly inviting refutation** — *"confirm, refute, or extend"*, never as a conclusion.

In the reference run this killed **five** of the orchestrator's own hypotheses with evidence (markdown-header degradation, prompt truncation, digest bypassing the prompt builder, a vacuous test assertion, a fail-open tier default). Each would otherwise have reached the PR author as a confident false finding.

## Synthesis — the part that makes it reliable

**The synthesiser is a verifier, not a stapler.**

1. **Re-verify every BLOCKER and MAJOR yourself** against the code.
2. **Prefer executed evidence over predicted behaviour.** If a member says "this won't compile", compile it.
3. **Deduplicate**, keeping the sharpest formulation. Independent convergence across lenses is a *strength signal* — say so.
4. **Reconcile contradictions explicitly** with code. Never average them.
5. **Report the honest tally.** 4-block/1-approve is not unanimity — don't round.
6. **Score the acceptance rubric** — `COVERED | PARTIAL | NOT COVERED`. This is usually where the biggest finding lives: *the PR is well-built and doesn't fix the bug.*

### Three high-value finding categories most reviews miss
- **"Valid comment, dangerous remedy."** The existing comment is right, but the obvious fix makes things worse. The single most useful thing a reviewer produces.
- **"Fixed nowhere, and not in this repo."** The real defect lives in another system → propose a discriminating test and a scope split, so the author isn't held to it.
- **"The rule permits the bug."** Read new guard rules adversarially against the actual incident.

### Two reusable techniques
- **Unique-string provenance.** Grep a distinctive artifact from the bug report (exact error text, badge string, a figure) across the repo. If it exists in exactly one place, you have *proven* where it came from — and may overturn the reported diagnosis.
- **Mutation-testing the tests.** Introduce the semantic regressions the tests claim to prevent, then re-run. "All assertions pass while the rule is gutted" is unarguable; "these tests look weak" is an opinion.

## Delivery

**Draft → human reads → then post. Never post unreviewed.**

Summary comment order: verified facts (SHAs, commands, real output) → **what's right** → the single most important finding → disposition table for every pre-existing comment → acceptance rubric → tiered work list (merge-gating / follow-up / hardening) → honest verdict tally.

Inline comments **must anchor to lines in the diff** or they silently fail to attach — check hunks with `git diff origin/main...pr-N -U0 | grep '^@@'` first, then verify they landed:
```bash
gh api repos/{o}/{r}/pulls/{n}/comments --paginate \
  --jq '.[] | select(.pull_request_review_id=={id}) | "\(.path):\(.line)"'
```
Build the payload by **parsing the approved draft file** so what posts is byte-identical to what was read. Default `event: COMMENT` — a formal `REQUEST_CHANGES` is a social act that belongs to the human.

**Tone:** the author is a colleague, often more familiar with the code. Lead with what works. Attribute structural problems to the system, not the person. Offer the smallest change that closes each finding.

## Gotchas

- **Subagents' plain text is invisible to the orchestrator.** Instruct them explicitly to deliver via `SendMessage` to `main`, or they go idle holding a finished report.
- **Shut members down** as soon as their deliverable lands and is verified ([[feedback_agent_shutdown]]).
- Write **one shared brief file** to scratchpad; don't paste context into N prompts.
- Tell members the branch is already checked out and they must not switch branches, install, commit, push, or comment.
- Don't convene a conclave for a typo or a version bump. It is expensive by design.

## Reference run — [[ALDC-739]] / [[zeus-chat-exp]] PR #167

Zeus Chat fabricated a full financial digest with a fake "Verified (100%)" provenance badge, shown to the CEO. Five lenses; **4 block / 1 approve-with-changes**. Two prior Opus bot reviews existed.

**What the method surfaced that the bot reviews did not:**
- **The root cause** — cross-turn carry-forward through *text-only* conversation history (`projectClientHistory` drops tool results). Proven by a badge substring existing in exactly one file, corroborated by `$118,902,434` repeating byte-identically across two separately-reported failures.
- **The PR's headline rule permitted the very bug it was written to stop** — Rule 1 allowed figures "returned in THIS conversation"; the carried-forward figures *were*. One-word fix: *this turn*.
- The rule **broke two shipping features** (`get_metrics_digest`, the QuickBooks revenue playbook) for 7 of 8 privileged tenants.
- The PR was the **first producer of a dead code path** feeding an LLM judge unsanitised row data.
- **Mutation proof** that the 12 new tests stayed green while three of the five new rules were gutted — and went red on an em-dash edit.
- The ticket's worst defect (a Power BI measure ignoring its period filter) **could not be fixed in that repo at all** → recommended scope split.

**What it corrected:** one false BLOCKER from its own council, one refuted bot comment, two bot comments whose obvious fix would have made things worse, and five wrong orchestrator hypotheses.

**Artifacts:** `aldc-launchpad/docs/reviews/ALDC-739-PR167-council-review.md` (consolidated) and `…-DRAFT-pr-comments.md` (as-posted draft). Posted review: `zeus-chat-exp#167` review `4804432198`.

## Revision log

Each entry records what drove the change, so the skill's evolution is auditable and can feed a
self-improvement loop. **Add an entry whenever `conclave-SKILL.md` changes.**
Tracked source: `skills/conclave-SKILL.md` — see [[README]] for the mirror contract and drift check.

### 2026-07-29 — created (226 lines)

First run on `zeus-chat-exp#167` / [[ALDC-739]] — see the reference run above. Established the two
gates, the five lenses, separate severity/confidence axes, feeding leads for refutation,
mutation-testing the tests, unique-string provenance, and draft-then-post delivery.

### No changes since — and one candidate deliberately NOT applied (2026-07-30)

The [[inquest-bug-resolution]] revision of that date added *"mutation-testing is necessary but not
sufficient — an absence assertion can be satisfied by destroying the population it measures"*. That
lesson came from a **deploy**, and conclave does not deploy: it reviews a diff and posts a review, so
it has no population to destroy. Its mutation-testing guidance (verify a PR's new tests actually fail
without the change) is unaffected and still correct.

**Recorded so the lesson is not reflexively copied across on a later pass.** The two skills share
ancestry but not blast radius. If conclave ever grows a step that mutates anything, revisit this.

## See Also

- [[inquest-bug-resolution]] — the sibling skill (resolves defects), derived from this one
- [[README]] — mirror contract and drift check
- [[ai-pr-workflow]] — the org-standard PR chain this plugs into
- [[adversarial-investigation-skill]] — sibling adversarial method for *problems* rather than *changes*
- [[zeus-chat-exp]] — repo of the reference run
- [[ALDC-739]] — ticket of the reference run
- [[ai-development-project-standard]]
