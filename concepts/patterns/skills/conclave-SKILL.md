---
name: conclave
description: Adversarial multi-lens pull-request review. Convenes a council of independent reviewers on orthogonal lenses, forces every finding to carry a concrete failure scenario, re-verifies every merge-gating claim against real code before it reaches a human, and delivers a draft the user approves before anything is posted. Use for PR review, code review of a branch or diff, reviewing someone else's work before sign-off, or auditing an existing bot/human review for blind spots.
---

# ⚖ CONCLAVE — adversarial multi-lens PR review

> *The conclave deliberates in isolation, then returns one verdict.*

A council of independent reviewers, each locked to a different lens, reviewing the same change without seeing each other's work. Their findings are then deduplicated, cross-checked, and — critically — **every merge-gating claim is re-verified against the actual code by the synthesiser before a human ever reads it.**

The design goal is *strict but reliable*. Strictness without reliability produces a wall of plausible-sounding findings that waste the author's time and train them to ignore reviews. Every rule below exists to make findings **falsifiable**.

## When to use

- Reviewing a PR — especially someone else's, especially before sign-off
- A bot review already exists and you need to know which comments are actually right
- High-stakes change: security-adjacent, data-integrity, money, multi-tenant, production
- Auditing whether a fix actually fixes its ticket

**Don't** convene a conclave for a typo, a version bump, or a diff you could read in two minutes. It is expensive by design.

**Sibling skill:** `inquest` resolves *defects* (diagnose → prove → fix → verify → deploy). If a conclave concludes *"this PR doesn't fix its ticket and the real cause is elsewhere"*, the follow-up is an inquest, not another review.

---

## The two gates — run these BEFORE convening anything

A council that reviews the wrong bytes is worse than no council, because its confidence is unearned. Both gates are non-negotiable.

### Gate 1 — Freshness

Never trust a local clone. Verify the working tree is the **exact** PR head:

```bash
gh api repos/{owner}/{repo}/pulls/{n} --jq '"head: \(.head.sha)\nbase: \(.base.sha)\nupdated: \(.updated_at)\ncommits: \(.commits)"'
git fetch origin --prune && git fetch origin pull/{n}/head:pr-{n}
git rev-parse pr-{n}          # MUST equal head.sha
git rev-parse origin/main     # MUST equal base.sha
```

State the verified SHAs in the final review. If a clone is stale by many merges, say so — it changes what "main" means in every finding.

> Real case: a clone sat at PR #24 while the PR under review was #167. Every "this doesn't exist on main" claim would have been wrong.

### Gate 2 — Environment

If the repo has dependencies, **install them**. A reviewer that cannot execute will either stay silent about verification or — worse — predict compiler/test behaviour and file it as fact.

```bash
ls node_modules >/dev/null 2>&1 || npm ci     # or the repo's equivalent
```

Then actually run the project's checks yourself and record the real output. Never restate the author's test claims as verified.

> Real case: two council members were silently blocked by a missing `node_modules`; one filed a BLOCKER predicting `tsc` would fail. `tsc` was clean. Installing deps turned a false blocker into a correct MINOR.

---

## Phase 0 — Ground (synthesiser, before spawning)

1. Read the **ticket** the PR claims to fix. Extract its acceptance criteria as a numbered list — this becomes a scoring rubric later.
2. Read **all existing review comments** (bot and human). They are input, not gospel.
3. Read the **diff** and the **repo's own conventions** (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING`).
4. Skim enough of the surrounding architecture to know what the changed code touches.
5. Write a **shared brief file** to scratchpad. Do not paste this context into N prompts — write it once and have every member read it.

The brief contains: repo path and verified branch/SHAs, the ticket verbatim (including its acceptance list), what the PR does, the existing review comments labelled with stable IDs (`R1-a`, `R2-c`…), the output contract, and a hard **read-only, do not post, do not commit** instruction.

---

## Phase 1 — Convene the council

Spawn members **in parallel, in one message**, each with the brief plus its own lens. Give each an explicit name so you can address it later.

### The standard five

| Lens | Owns the question |
|---|---|
| **Correctness & data-flow** | Does the code do what it claims, along the whole runtime path? Trace end-to-end; don't reason from the diff. |
| **Security & trust boundary** | What leaks, spoofs, or crosses a boundary? Injection, tenancy, authz, secrets, persistence, DoS/cost. |
| **Ticket acceptance & root cause** | Does this actually fix the bug, or only its presentation? Score every acceptance item. Hunt the real root cause independently. |
| **Adversarial red-team** | Assume it merges. Now make the bug reproduce anyway. Construct concrete scenarios; rank by likelihood × harm. |
| **Tests & verification** | Do the tests protect against recurrence, or just assert that code exists? **Execute** the checks. Mutation-test the assertions. |

Swap or add lenses to fit: *performance & scale*, *API/contract compatibility*, *migration & rollback*, *accessibility*, *observability*, *cost*, *docs & DX*. Five is the sweet spot; beyond seven the marginal lens mostly duplicates.

### Consider a sixth: the author's advocate

Every lens above is incentivised to find something. Nobody is tasked to defend the PR — so a council can drift toward a block verdict that no single member would defend alone.

Add **`advocate`**: *"argue this should merge as-is. Which findings are theoretical? Which existing comments are noise? What is the cost of delay versus the cost of the residual risk?"*

Use it when the verdict matters socially — someone else's PR, a hotfix under time pressure, or a review that is trending toward a wall of blockers. It sharpens the tally rather than softening it: a block that survives an advocate is worth far more than one that was never contested.

### Rules every member gets

- **Verify by reading real code.** Never cite a line number you didn't open.
- **Every finding needs a concrete failure scenario** — specific inputs/state → specific wrong outcome. *If you can't write one, downgrade or drop it.* This single rule removes most noise.
- **Severity** ∈ `BLOCKER | MAJOR | MINOR | NIT` and **confidence** ∈ `CERTAIN | LIKELY | SPECULATIVE`, as **separate** axes. A CERTAIN NIT and a SPECULATIVE BLOCKER are both useful and behave differently.
- **Adjudicate the existing review comments.** For each: confirm with new evidence, refute with evidence, or improve the proposed fix. Say **REFUTE** explicitly when refuting.
- **Report what you checked and found clean.** Prevents re-litigation and shows coverage.
- **Distinguish "enforced in code" from "requested of a human/model."** For LLM features this is the whole ballgame — a prompt rule is a mitigation, not a guarantee.
- **Say what you could not verify and why.** Never fabricate a test result.
- Few high-signal findings beat many weak ones. No stylistic rewrites unless they prevent a defect.

### Feed members your own leads — and invite refutation

When you spot something during grounding, hand it to the relevant member as a **hypothesis to test**, explicitly inviting refutation. Phrase it as *"confirm, refute, or extend"* — never as a conclusion.

> This is where the method earns its keep. In the run that produced this skill, members refuted the orchestrator on the markdown-header hypothesis, the prompt-truncation hypothesis, the digest-bypasses-the-prompt-builder hypothesis, the vacuous-test hypothesis, and a fail-open tier claim — **five wrong leads killed with evidence**, each of which would otherwise have reached the author as a confident false finding.

### Operational notes

- Members' plain text is **not** visible to the orchestrator. Instruct them explicitly: *"deliver your report by sending it to `main` via SendMessage."* They will otherwise go idle holding a finished report.
- Shut each member down as soon as its deliverable lands and is verified. Don't let them loop.
- Tell them the branch is already checked out and they must not switch branches, install, commit, push, or comment.
- **Time-box, and escalate instead of iterating.** If a member returns only SPECULATIVE findings it cannot falsify with the access it has, that is its answer — take it. Name the missing access in the review rather than spawning a replacement and hoping. A stated blocker is worth more than a confident guess.

---

## Phase 2 — Synthesis (the part that makes it reliable)

**The synthesiser is a verifier, not a stapler.** Council output is raw material.

1. **Re-verify every BLOCKER and MAJOR yourself** against the code. Open the file. Run the command. In the reference run this caught a BLOCKER that was wrong — and confirmed nine that were right.
2. **Prefer executed evidence over predicted behaviour.** If a member says "this should fail to compile", compile it.
3. **Deduplicate across lenses**, keeping the sharpest formulation and the strongest evidence. Multiple lenses reaching the same finding independently is a *strength signal* — say so.
4. **Reconcile contradictions explicitly.** When members disagree, adjudicate with code and report the resolution. Never average them.
5. **Report the honest tally.** If four say block and one says approve-with-changes, say exactly that. Don't round to unanimity.
6. **Downgrade anything you can't reproduce.** SPECULATIVE findings go in only if cheap to falsify, and labelled as such.
7. **Score the acceptance rubric** — `COVERED | PARTIAL | NOT COVERED` per item, with evidence. This is usually where the biggest finding lives: *the PR is well-built and doesn't fix the bug.*
8. **⭐ Challenge the brief's own premises.** Every member read the *same* brief, so any error in it produces **correlated** error — five independent lenses agreeing on a wrong premise looks exactly like five lenses converging on the truth, and the strength-signal rule in step 3 will actively launder it. Before finalising, re-derive the brief's load-bearing claims from source: is the ticket's stated cause actually the cause? Is the "existing behaviour" you described real? Unanimity that traces back to one shared assumption is not corroboration.

### Three high-value categories the average review misses

- **"Valid comment, dangerous remedy."** An existing comment is correct, but the obvious fix makes things worse. Flag loudly — this is the single most useful thing a reviewer produces.
- **"Fixed nowhere, and not in this repo."** The real defect lives in another system. Say so, propose a discriminating test, and recommend a scope split so the author isn't held to it.
- **"The rule permits the bug."** Read new guard rules adversarially against the actual incident. A rule written to stop a bug frequently doesn't.

### Two techniques worth reaching for

- **Unique-string provenance.** Grep a distinctive artifact from the bug report (an exact error string, badge text, a figure) across the repo. If it exists in exactly one place, you've proven where it came from — which can overturn the reported diagnosis. This found the root cause in the reference run.
- **Mutation-testing the tests.** Introduce the semantic regressions the tests claim to prevent, then re-run them. "All assertions still pass while the rule is gutted" is an unarguable finding; "these tests look weak" is an opinion.
- **Predict before you run.** Before executing a check that settles a finding, write down what you expect if the finding is **true** and what you expect if it is **false**. If both branches predict the same output, the check settles nothing and you will rationalise whatever appears. This costs one line and is the difference between evidence and confirmation.

---

## Phase 3 — Deliver

**Draft → human reads → then post. Never post unreviewed.**

Write the full review — summary body *and* every inline comment, each with its anchor — to one file and have the user read it. Then post.

Structure of the summary comment:

1. **Verified facts up front** — SHAs reviewed, commands run, real output. Establishes that this review executed things.
2. **What's right.** Genuinely. Name the good decisions. A review that opens with nine defects gets read defensively.
3. **The single most important finding**, with its evidence chain.
4. **Disposition table for every pre-existing comment** — valid / understated / refuted / valid-but-don't-fix-as-suggested.
5. **Acceptance rubric table.**
6. **Tiered work list** — merge-gating vs follow-up vs hardening, so the author knows the shortest path to green.
7. **Footer** noting the method and the honest verdict tally.

**Re-check the head SHA immediately before posting.** A PR that gained commits during the review invalidates line anchors and can invalidate findings outright. If `head.sha` moved since Gate 1, diff the delta and re-verify every affected finding before posting — or say plainly which SHA the review covers.

```bash
gh api repos/{owner}/{repo}/pulls/{n} --jq .head.sha    # MUST still equal Gate 1's value
```

Inline comments must anchor to lines **in the diff** or they silently fail to attach. Verify first:

```bash
git diff origin/main...pr-{n} -U0 -- <paths> | grep -E "^@@"
```

Then post as one review with all comments attached, and confirm they landed:

```bash
gh api repos/{owner}/{repo}/pulls/{n}/reviews --method POST --input payload.json
gh api repos/{owner}/{repo}/pulls/{n}/comments --paginate \
  --jq '.[] | select(.pull_request_review_id=={id}) | "\(.path):\(.line)"'
```

Build the payload by **parsing the approved draft file**, so what posts is byte-identical to what was read.

Default `event` to `COMMENT` unless the user asks for `REQUEST_CHANGES` — a formal block is a social act that belongs to the human.

### Tone

The author is a colleague, often more familiar with the code than you. Lead with what works. Attribute structural problems to the system, not the person ("the badge is model-authored *by design*" — not "you let the model author the badge"). Offer to pair. Give the smallest change that closes each finding; a one-word fix stated plainly is worth more than a paragraph of principle.

---

## Anti-patterns

| Don't | Because |
|---|---|
| Review a stale clone | Every claim about "main" is then wrong |
| Restate the author's test claims as verified | You've laundered an assertion into a finding |
| File a finding without a failure scenario | It's a hunch wearing a severity label |
| Predict compiler/runtime behaviour | Run it. Prediction is how false blockers get filed |
| Round the verdict to unanimity | Destroys the signal that dissent carries |
| Let members mark everything CERTAIN | The confidence axis is what lets you catch their errors |
| Treat existing bot comments as ground truth | In the reference run, 3 of 9 needed pushback |
| Post before a human reads it | Reviews are outward-facing and hard to retract |
| Treat unanimity as corroboration without checking the brief | Every member read the same brief; shared premises produce correlated error |
| Spawn a replacement member when one reports "can't verify" | That's the answer. Name the missing access instead |
| Post against a SHA that moved mid-review | Anchors break silently and findings may be stale |
| Convene 5 agents for a small diff | Cost without benefit; just read it |

---

## Reference run

First convened on `ALDC-io/zeus-chat-exp#167` (ALDC-739 — Zeus Chat fabricating financial metrics with a fake "Verified (100%)" badge). Five lenses; 4 block / 1 approve-with-changes.

What the method surfaced that two prior Opus bot reviews did not:
- The **root cause** — cross-turn carry-forward through text-only history, proven by a badge substring existing in exactly one file, and corroborated by a 9-digit figure repeating byte-identically across two reported failures.
- That the PR's **headline rule permitted the very bug it was written to stop** (a one-word fix).
- That the rule **broke two shipping features** for the majority of privileged tenants.
- That the PR was the **first producer of a dead code path** feeding an LLM judge unsanitised.
- **Mutation proof** that the new tests stayed green while three of the five new rules were gutted.
- That the ticket's worst defect **could not be fixed in that repo at all** → scope split.

And what it corrected: one false BLOCKER from its own council, one refuted bot comment, two bot comments whose obvious fix would have made things worse, and five wrong hypotheses from the orchestrator.
