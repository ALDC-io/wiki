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

## The three gates — run these BEFORE convening anything

A council that reviews the wrong bytes is worse than no council, because its confidence is unearned. All three gates are non-negotiable.

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

**⭐ Gate 1 re-fires before every consequential act, not just before posting.** A review that sat overnight is a review of a SHA, not of a PR. Re-run it before posting, before advising on merge, before answering "should I approve this?", and at the start of any resumed session. Advising a merge on stale findings is exactly as damaging as posting them.

> Real case: asked "LingJun wants me to approve and merge #128" the morning after a review, the re-check found **both** PRs force-pushed overnight (14→18 commits) *and* `origin/main` advanced. Every finding had to be re-verified against the new head before answering. Most held; the merge advice would have been given against bytes that no longer existed.

Three traps when a head moves:

```bash
git checkout --detach                       # `git fetch … :pr-N` FAILS if pr-N is checked out
git fetch origin pull/{n}/head:pr-{n} --force
git merge-base --is-ancestor <reviewed-sha> pr-{n}   # NO ⇒ force-push: re-verify EVERY finding
git diff origin/main...pr-{n} --stat        # three-dot. Two-dot conflates rebase-inherited
                                            # main changes with the author's actual work
```

### Gate 2 — Environment

If the repo has dependencies, **install them**. A reviewer that cannot execute will either stay silent about verification or — worse — predict compiler/test behaviour and file it as fact.

```bash
ls node_modules >/dev/null 2>&1 || npm ci     # or the repo's equivalent
```

Then actually run the project's checks yourself and record the real output. Never restate the author's test claims as verified.

> Real case: two council members were silently blocked by a missing `node_modules`; one filed a BLOCKER predicting `tsc` would fail. `tsc` was clean. Installing deps turned a false blocker into a correct MINOR.

**Decide the write policy before spawning, because members share one working tree.** Parallel members that mutate files in place will corrupt each other's runs — and each other's *reads*. Pick one:

- **Read-only members + synthesiser-run mutations** (default). Members execute tests but never edit; the synthesiser runs any mutation testing itself, serially, reverting between each.
- **Worktree isolation** for any member that must mutate. On Windows, junction the shared `node_modules` rather than copying — and when tearing down, **unlink the junction FIRST**, then remove the worktree, then verify the real `node_modules` survived. `rm -rf`/`git worktree remove` through a live junction deletes the real shared directory.

Tell members explicitly which policy is in force.

> Real case: three lenses declined to run tests at all, for fear of disrupting siblings — a self-inflicted coverage gap. A fourth reported "another agent is mutating the shared tree" after catching a transient modified file (it was the synthesiser). Only the lens that built an isolated worktree got full mutation results.

### Gate 3 — Cross-repo companion state

If the change has a companion PR in another repo — a backend half, a schema migration, a connector — **its merge state is part of your review**, and getting it wrong is a merge-order error, the most expensive kind.

```bash
gh pr view {n} --repo {owner}/{other} --json state,mergedAt,mergeCommit
git -C ../other-repo fetch origin --prune              # ALWAYS fetch first
git -C ../other-repo log origin/main --grep="{TICKET}"  # squash-merges live here
```

**`git merge-base --is-ancestor` is not proof of "unmerged."** A squash-merge creates a *new* commit, so the original branch commits are legitimately not ancestors of main. Verify by commit message / PR number, and read the file content on `origin/main`.

> Real case: a lens filed a BLOCKER — *"the backend is unmerged, so this PR ships dead code"* — from `--is-ancestor` returning NO on a **stale clone**. The companion PR had been squash-merged hours earlier and was the tip of main, with the required fields already present. That finding would have told the author their work was inert.

Then ask the question that actually matters: **which half fails OPEN?** Land that one last.

> Real case: a backend predicate `(NOT is_calendar_row OR <date bounds>)` silently no-ops the whole date filter for any source it doesn't recognise. Merging the frontend half first would have converted a visible "no events found" into a plausible wrong schedule — a silent failure on an act-on-it surface. The PR's documented merge order was the unsafe one.

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

### Reviewing two or more PRs together

When PRs touch the same subsystem, review them in **one** conclave rather than two — the interaction is invisible to a per-PR review, and to the bots, which see one PR each.

- **Split the correctness lens per PR** (`correctness-161`, `correctness-128`); keep security / acceptance / red-team / tests / advocate **spanning both**, so someone is looking at the seam.
- **Actually merge them and read the result.** `git merge-tree --write-tree pr-A pr-B` — a *clean* merge is the dangerous case, because nothing forces a human to reconcile the semantics. In run 2 the merge was clean while one PR established "calendar ≠ `graph.calendar`" and the other hardcoded `source=graph.calendar` into the briefing template — post-merge, a Google-Calendar tenant would get events in chat and a permanent "No calendar events for today." in their briefing. Neither PR's own reviewers could see it.
- **Attribute the fix to the right PR.** "It's a #128 change that only becomes wrong because of #161" is the useful sentence; it tells the author which diff to touch and stops a finding being filed against the wrong person.
- Write **one draft per PR** (each author reads only theirs), and put the cross-PR finding in both, phrased from each side.

### Always add the author's advocate

Every lens above is incentivised to find something. Nobody is tasked to defend the PR — so a council reliably drifts toward a block verdict that no single member would defend alone.

Add **`advocate`**: *"argue this should merge as-is. Which findings are theoretical? Which existing comments are noise? What is the cost of delay versus the cost of the residual risk? What did the author get RIGHT — name the good decisions specifically, because no other lens will supply them."*

Originally listed here as optional. Promoted to standard on the strength of the second run, where it produced the single most valuable correction of the review: it proved the headline finding — the one three other lenses had confirmed and escalated — belonged to **trunk, not the PR**. `git log -S'"graph.calendar"'` on the file returned empty (the source was *never* allowlisted) and the offending commit was an ancestor of `main`, predating the PR by two weeks. That demoted a BLOCKER to "pre-existing P1, file separately, don't hold this author." It also correctly reframed comment volume as churn: 39 inline comments on one PR resolved to 12 distinct issues, 8 already fixed, and re-raised 2–4× each by a bot that re-runs on every push.

Weight its findings like any other lens — it is not a rubber stamp, and in that run it conceded two real test defects unprompted. But when it contradicts the pile, **check it first**: it is the only lens whose incentive is to look for the exculpatory evidence nobody else is hunting for.

A block that survives an advocate is worth far more than one that was never contested.

#### ⭐ Require the advocate to return VERIFIABLE CHECKS, not judgements

"Which findings are theoretical?" and "cost of delay vs residual risk?" both invite prose, and prose
loses to a pile of confident findings. Notice that the advocate's best result was **not** an opinion —
it was `git log -S'"graph.calendar"'` returning empty plus a commit shown to be an ancestor of `main`.
That is why a BLOCKER three lenses had escalated collapsed in one line. Make it the standard, not a
happy accident. Require, **per finding it disputes**:

| Required | Not acceptable |
|---|---|
| The **command or query** that discharges it — `git log -S`, `git merge-base --is-ancestor`, blame, the failing/passing test, the actual config value | "this looks pre-existing" |
| **Scope as a number** where the finding claims breadth — call sites, affected rows/users, occurrences on trunk vs in the diff | "this pattern is used widely" |
| **The cost of ACTIONING it**, measured — what the proposed remedy changes beyond the reported problem | "the fix seems heavy-handed" |
| Explicit **"does the remedy fix the stated problem — yes/no"**, separate from whether it is safe | conflating the two |

The last two matter most, because `conclave`'s highest-value category is **"valid comment, dangerous
remedy"**: the comment is right, the fix is worse than the bug. That verdict is only actionable with a
measured remedy cost — a reviewer told "this feels risky" will merge anyway.

> Sibling precedent (`inquest`, FU92-421): a whole council converged on loosening an `INNER JOIN`.
> The adversary did not object — it measured: **+$119,922 (+16.9%) across 23,883 multi-claimed pairs,
> worst pair 97 entities**, *and* answered efficacy — **no, it fixes nothing**. Both axes, both
> numeric. That is the bar.

Where a number genuinely cannot be obtained, the advocate says **"unmeasurable — here is why and what
access it needs"**. Never an adjective standing in for evidence.

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
- **A member that hasn't reported is not a member that found nothing.** If one goes quiet past the time-box, `SendMessage` it a *prioritised* request — "send what you have now, partial is fine; here are the three answers I still need, in order." In run 2 the tests lens landed last and carried the most executed evidence of any lens; the priority list is what got it out. If it still doesn't land, run its decisive check yourself and say in the review which lens didn't report.
- **Tell members what the other lenses already established**, when it saves duplicated work — but frame it as *"X reported this; agree or refute independently"*, never as settled fact. Two lenses independently reaching the same executed result is the strongest signal available; two lenses copying each other is the weakest.
- Members go idle holding their transcript rather than terminating. Once every deliverable has landed and been verified, they're done — leave them addressable if a follow-up is likely, and say so rather than silently abandoning them.

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

### Techniques worth reaching for

- **Unique-string provenance.** Grep a distinctive artifact from the bug report (an exact error string, badge text, a figure) across the repo. If it exists in exactly one place, you've proven where it came from — which can overturn the reported diagnosis. This found the root cause in the reference run.
- **Mutation-testing the tests.** Introduce the semantic regressions the tests claim to prevent, then re-run them. "All assertions still pass while the rule is gutted" is an unarguable finding; "these tests look weak" is an opinion. **Mutate one thing at a time, revert between each, and verify the tree is clean at the end** (`git status --short` + confirm the branch). Report the *shape* of the result, not a verdict: in run 2, gutting round-0 suppression left the file *named* for that behaviour 100% green — but deleting the whole determinism rule failed a *different* test file, which downgraded the finding from "coverage hole" to "test-quality, CI still catches it." Both halves belong in the review.
- **Predict before you run.** Before executing a check that settles a finding, write down what you expect if the finding is **true** and what you expect if it is **false**. If both branches predict the same output, the check settles nothing and you will rationalise whatever appears. This costs one line and is the difference between evidence and confirmation.
- **⭐ A green check does not prove the test ran.** Tests self-skip on missing env (`const ready = !!(PROXY && KEY)`), get excluded by config (`exclude: ['**/*.integration.test.*']`), or are wired into no workflow at all — and the check still reports `pass`. When a test is the load-bearing evidence for a merge decision, **read the job log and confirm execution**:

  ```bash
  gh run view {run-id} --repo {owner}/{repo} --log --job {job-id} | grep -iE "skip|Test Files|Tests |✓"
  ```

  In run 2 this cut both ways: it confirmed a new real-LLM integration test genuinely executed (`✓ … (3 tests) 17369ms` — 17s of real network), which was a point *for* the author. Same family as "a test in no CI workflow is dead code."
- **Interrogate the fixture, not just the assertion.** A test is worth exactly what its inputs are. `expect(out).not.toContain("organizer")` looks like a PII guard, but if the fixture's payload is the bare string `"Sprint Review"` while the real producer emits `Event: … / Organizer: <email> / Attendees: …`, the assertion certifies safety for a payload that does not exist. **Derive the expected shape from the actual producer** (the ingester, the API response, the serialiser) and re-read the assertion against that. Watch for the mirror case too: an assertion that passes *harder* when the data disappears — `expect(frame).toBeDefined(); expect(frame).not.toContain(pii)` is satisfied by an empty frame, so it needs a positive `toContain(id)` first.

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

**If the head moved, re-verifying is the work — and the delta usually contains good news too.** Don't just re-anchor: walk each finding against the new head and report the state change honestly. Say which findings survived, which the author already fixed, and what the new commits *added*. In run 2, four new commits properly hardened a numeric-coercion finding out of existence and added a real integration test — while six findings survived verbatim. A review that only lists what's still wrong after the author pushed fixes reads as bad faith and gets discounted.

When the delta is large, open the summary with a one-line freshness statement — *"re-verified at `<new sha>`; force-pushed since my last pass, N→M commits; here's what changed"* — so the author can see you reviewed their current work, not their old work.

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
| Advise on merge from a review that sat overnight | Gate 1 re-fires before *advising*, not just before posting |
| Conclude "unmerged" from `--is-ancestor` alone | Squash-merge makes a new commit; verify by message/PR and fetch first |
| Read a companion repo without fetching it | A stale clone turns a shipped fix into a phantom BLOCKER |
| Trust a green CI check as proof a test executed | Tests self-skip, get excluded, or run in no workflow — read the log |
| Judge an assertion without reading its fixture | The assertion is worth only what the input shape is |
| Let parallel members mutate one shared tree | They corrupt each other's runs *and* reads; isolate or serialise |
| Treat comment volume as a merge signal | A push-triggered bot re-raises the same nit 4×; count *distinct* issues |
| Review interacting PRs separately | The seam is invisible per-PR — and a clean merge hides it |

---

## Reference runs

### Run 1 — `ALDC-io/zeus-chat-exp#167` (ALDC-739)

Zeus Chat fabricating financial metrics with a fake "Verified (100%)" badge. Five lenses; 4 block / 1 approve-with-changes.

What the method surfaced that two prior Opus bot reviews did not:
- The **root cause** — cross-turn carry-forward through text-only history, proven by a badge substring existing in exactly one file, and corroborated by a 9-digit figure repeating byte-identically across two reported failures.
- That the PR's **headline rule permitted the very bug it was written to stop** (a one-word fix).
- That the rule **broke two shipping features** for the majority of privileged tenants.
- That the PR was the **first producer of a dead code path** feeding an LLM judge unsanitised.
- **Mutation proof** that the new tests stayed green while three of the five new rules were gutted.
- That the ticket's worst defect **could not be fixed in that repo at all** → scope split.

And what it corrected: one false BLOCKER from its own council, one refuted bot comment, two bot comments whose obvious fix would have made things worse, and five wrong hypotheses from the orchestrator.

### Run 2 — `zeus-chat-exp#161` (ALDC-707) + `#128` (ALDC-337), reviewed together

Two interacting PRs from the same author, each already carrying 4+ bot review rounds (39 and 150 inline comments). Seven lenses. Tally: 3 block / 2 merge-with-fixes / 1 merge-as-is / 1 mixed — reported unrounded.

What the method surfaced that ~190 bot comments did not:
- **The PII tests certified a payload the producer never emits** — the real ingester writes organizer/attendee emails into `content`, which the decorator only *appends* to. The fixture used a bare subject string, so both negative assertions passed.
- **The documented merge order was the unsafe one** — the backend predicate no-ops the entire date filter for the unrecognised source, so landing the frontend first converts "no events found" into a plausible wrong schedule.
- **A user-visible regression in the PR's own symptom class** — the briefing pill renders as a *user bubble*, so its rewritten text printed the exact internal field names the same PR's system prompt forbids in output.
- **The load-bearing allowlist gap belonged to trunk, not the PR** (the advocate's find), demoting a council BLOCKER to a separate P1.
- **Mutation proof in both directions** — the file named for CoT suppression stayed green while suppression was gutted; the contract test that three reviewers called vacuous caught its mutation 3/4.

And what it corrected: a BLOCKER built on a stale clone + squash-merge misreading, a MAJOR field-name defect refuted by the companion PR's own contract test, a "the client mitigates this" claim refuted by reading the guard, one orchestrator hypothesis refuted by reading the sanitiser — and its own author-advocate overturning the review's headline attribution.
