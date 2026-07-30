---
name: inquest
description: Adversarial multi-lens bug resolution — diagnose, prove, fix, verify, deploy. Convenes a council of independent investigators on orthogonal layers, forces every root-cause claim to carry a discriminating test with its result predicted BEFORE it runs, proves the regression test fails without the fix, and gates the deploy on target + consumer-layer + no-regression + rollback evidence. Use for a reported bug, an incident, a "not loading" / "wrong number" / "error" report, a client-reported defect, or any fix whose blast radius reaches production. Sibling of `conclave` (which reviews PRs); this one resolves defects.
---

# 🔍 INQUEST — adversarial multi-lens bug resolution

> *An inquest does not ask who to blame. It establishes cause of death, on evidence, and says so plainly.*

A council of independent investigators, each locked to a different **layer** of the stack, hunting the same defect without seeing each other's work. Their hypotheses are then cross-checked and — critically — **every root-cause claim must survive a discriminating test whose outcome was predicted before it ran.**

Sibling skill to `conclave`. The difference is structural, not cosmetic:

| | `conclave` (PR review) | `inquest` (bug resolution) |
|---|---|---|
| The artifact | **Given** — a diff | **Unknown** — must be located and proven |
| Members hunt for | Problems in known code | The one true cause among many plausible ones |
| Failure mode | Plausible findings that waste the author's time | **Confident fix at the wrong layer** |
| Bias to fight | Reviewer wants to find something | Investigator wants their hypothesis to be right |
| Ends at | A posted review | A **deployed, proven** fix — or a proven non-bug |

The design goal is *fast but honest*. A bug hunt that produces a confident wrong answer is worse than one that reports "not yet proven, here's what I need" — because the wrong answer gets deployed.

## When to use

- A reported defect on a production or client-facing surface
- A symptom whose cause is genuinely unknown after a first look
- Any fix touching shared SQL, a data pipeline, or a dashboard/report/export
- An incident where the obvious cause has already failed once

**Don't** convene an inquest for a bug you can see in the stack trace, a typo, or a one-line fix with an obvious test. It is expensive by design. If Gate 3 reproduces the bug *and* the cause is immediately unambiguous from the failing request, just fix it.

---

## The three gates — run these BEFORE convening anything

A council investigating the wrong thing is worse than no council, because its confidence is unearned.

### Gate 1 — Freshness

Verify you are looking at the code and config that is *actually deployed on the surface the reporter used*. Not `main`, not your last branch.

```bash
git fetch origin --prune && git log --oneline -1 origin/<trunk>
git status --short              # uncommitted local state changes what you're testing
```

⚠ Trunk is per-repo and frequently **not** `main` (Eclipse work trunks on `eclipse-2.1`; `main` is stale and lacks merged work). Confirm, don't assume. State the verified SHA/branch in the final writeup.

> Real case (`conclave` reference run): a clone sat at PR #24 while reviewing #167. Every "this doesn't exist on main" claim would have been wrong.

### Gate 2 — Environment

Prove your own tooling works **before** reporting that something else is broken. Install deps, confirm credentials, confirm connectivity, run one known-good query.

```bash
ls node_modules >/dev/null 2>&1 || npm ci     # or the repo's equivalent
```

An investigator that cannot execute will predict behaviour and file the prediction as fact.

> Real case: two council members were silently blocked by a missing `node_modules`; one filed a BLOCKER predicting `tsc` would fail. It was clean. A false blocker became a correct MINOR after `npm ci`.

**⭐ Calibrate the instrument, not just the credentials.** Working deps and auth ≠ your probe being
able to tell pass from fail. **Run a positive control — a case you know returns data.** If it
doesn't light up, every "clean" result is worthless. **A uniform result across every cell of a
matrix is far more likely a broken parser than a uniform truth**; suspect your own tooling when
nothing varies.

> Real case (GP-309): a probe read `0 rows` for one query type at *every* object and *every*
> timeframe — accepted as "this path is clean". The handler returned a dict where the probe expected
> a list, and the parser silently coerced it to `[]`. **A false clean is worse than an error: it
> reads as passing.**

### Gate 3 — Reproduction ⭐ (this gate is what makes it an inquest)

**No hypothesis work begins until the bug reproduces, or is proven not to.** Five agents theorising about an unreproduced symptom is the most expensive way to be wrong.

#### ⭐ Reproduce THE REPORTED symptom — finding *a* defect is not passing this gate

The dangerous failure is not "I couldn't reproduce it" — it is **reproducing something else,
convincingly.** A real defect that is *not what the reporter saw* survives every check you apply
and then points the whole council the wrong way. So answer explicitly before convening: **does my
reproduction produce the reporter's described symptom, in their words?** If not, you have a
*second* defect — log it, keep hunting the first, and say which you have.

> Real case (GP-309): a bare `null` on a comparison endpoint, proven against 10/10 pre-committed
> predictions, was *not* the reported bug — it was guarded on both client and server. The council
> was convened on it anyway and spent its entire effort there.

#### ⭐ Ask the reporter — the cheapest instrument you have

Do this **early, in parallel with probing**, not after you run out of ideas. Ask for: the **exact
message text** (verbatim or screenshot), **which control they touched**, **the state of every
filter/slicer**, and **when**. "Not loading" distinguishes *none* of {blank page, error banner,
empty-state message, never-resolving spinner} — resolve that by asking, not by enumerating.

> Real case (GP-309): ~260 probes came back clean and the write-up said "surface proven healthy".
> The reporter had seen an **empty-state message** — that one detail reframed the search and the
> reproduction followed in ~20 minutes.

#### Reproduce with the CONSUMER's request state, not your own

A hand-built probe tests a user who doesn't exist. **Anything the client sends that the server does
not inject is invisible to a probe you construct yourself** — filter/slicer selections, query
params, headers, session identity, a `WHERE` clause the app appends. Read the consumer's real
configuration and replay it, including **every value the UI offers**, not just the defaults.

> Real case (GP-309): every probe sent an empty filter list. The dashboard's filter was
> browser-sent, and one value its dropdown offered was a blank string that zeroed every tile.
> ~260 probes and four council members missed it because none replayed the consumer's filter state.

Reproduce **as the affected user sees it**, on the deployed surface, and capture:

- the exact failing request (URL, method, payload) and its **status + response body**
- console errors, in full
- a screenshot of the rendered failure
- the timestamp and the identity/role used

Then ask the question that saves whole sessions: **does it still reproduce right now?** Caches expire, refreshes succeed, deploys land. A report is a claim about the past.

**"Not reproducible" is a first-class verdict, not a failure.** If it doesn't reproduce, the inquest pivots: what changed between the report and now, and is the surface *provably* healthy? That is a different investigation, and a cheaper one.

If reproduction requires access you don't have, stop and say so. Do not substitute theory.

---

## Phase 0 — Ground (synthesiser, before spawning)

1. Read the **ticket** verbatim. Extract its acceptance criteria as a numbered rubric.
2. Read the **reporter's own words**. Client phrasing is imprecise but load-bearing — "not loading" covers a blank page, an error state, an empty grid, and a spinner, which have different causes.
3. Search for **prior art**: has this signature been seen before? A documented failure mode found in five minutes beats a five-agent hunt. Check the wiki, related tickets, `docs/evidence/`.
4. Read the **surrounding architecture** — enough to name the layers the symptom could live in.
5. Write a **shared brief file** to scratchpad. Write it once; do not paste context into N prompts.

The brief contains: repo paths and verified branch/SHAs, the ticket verbatim with its rubric, **the Gate 3 reproduction artifacts** (status codes, response bodies, screenshots, console), the object IDs and environment in scope, the output contract, and a hard **read-only — do not mutate, deploy, commit, or comment** instruction.

### ⭐ The brief propagates YOUR error to every member — budget for that

Every member reads the same brief, so **any mistake in your framing reaches all of them at once**,
and N lenses agreeing inside a wrong frame is indistinguishable from N lenses converging on truth.
The council cannot correct a blind spot it inherited from you. Two cheap defences:

1. **Mark your framing provisional in the brief** — "my current read, not a finding; if the symptom
   doesn't fit it, say so and re-derive."
2. **Licence at least one member to reject the frame** — give `devil` an explicit instruction:
   *"re-derive the symptom from the reporter's own words and the consumer's real configuration. If
   this brief is aimed at the wrong thing, say so — that is your highest-value finding."*

> Real case (GP-309): the brief pointed all four members at a `null`-response defect the orchestrator
> had already proven. **None replayed the consumer's filter state** — where the real bug lived —
> because the frame excluded it. Four lenses, one shared blind spot. Same correlated-error failure
> already recorded against `conclave`, recurring for the same structural reason.

---

## Phase 1 — Convene the council

Spawn members **in parallel, in one message**, each with the brief plus its own layer. Name each one so you can address it later.

### The standard five — layers, not opinions

| Member | Owns the question |
|---|---|
| **`observer`** — symptom & scope | What *exactly* happens, and where doesn't it? Bracket the blast radius: which users, objects, environments, timeframes, filters are affected vs clean. **No theory.** A precise boundary usually names the cause by itself. |
| **`surface`** — consumer/render layer | Does the surface's own configuration explain it? Dashboard/report docs, visual options, dataset↔model binding, name-vs-ID resolution, RBAC, caching, client-side state. |
| **`substrate`** — data & query layer | Does the data underneath explain it? Source freshness, refresh/task history, row counts, nulls, a filter resolving to empty, grain mismatch, currency/units. |
| **`pathway`** — code path | Does the server code explain it? Read the actual route and query builder end-to-end for the specific path exercised. Never reason from the endpoint name. |
| **`devil`** — falsifier & no-change advocate | Argue there is no bug here: stale cache, already fixed, wrong environment, wrong object, correct-behaviour-misread, duplicate of a known issue. Then: **for each hypothesis the others will raise, what is the wrong fix, and what damage would it do?** |

Swap layers to fit the stack: *infra/network*, *auth/identity*, *third-party API*, *migration/schema*, *concurrency*, *cost/quota*.

`devil` is not optional and is not a formality. In the reference `conclave` run the highest-value category was **"valid comment, dangerous remedy"** — 2 of 9 findings would have made things *worse* if actioned as written. The bug analogue is worse still: a plausible fix deployed at the wrong layer.

### Rules every member gets

- **Verify by reading real code and real state.** Never cite a line or a row count you didn't open.
- **⭐ Every root-cause claim needs a DISCRIMINATING TEST, with both outcomes predicted BEFORE you run it:**

  ```
  HYPOTHESIS:   <mechanism, specifically>
  TEST:         <the exact query / request / command>
  IF TRUE:      <the precise observation expected>
  IF FALSE:     <the precise observation expected — MUST differ>
  ACTUAL:       <what happened>
  ```

  **If both branches predict the same observation, it is not evidence — it is a vibe.** Write the prediction down first; post-hoc rationalisation is invisible otherwise.

  A passing discriminating test earns **`LIKELY`**, not `PROVEN`. See *The standard of proof* in Phase 2 for what `PROVEN` requires — reproduce both sides, reconcile the gap arithmetically, name the culprit records, enumerate the candidate space, run a negative control. **Aim for that bar from the start**; it is usually cheaper than a second round of hypotheses.

  Precedent in this codebase: `eclipse_ops/_gp304_predict_scoping.py` wrote its predictions to `docs/evidence/gp304/predict_scoping.json` *before* the change, which is why the result was unarguable.

- **⭐ Never infer the target from matching values.** Two objects can hold identical values and still be different objects. Prove which one the consumer reads with something only one candidate has — a distinguishing column, the consumer's own query log, the import/partition source. *This exact inference caused a wrong-layer deploy and revert (GEP "Missing COGs", 2026-05-29).*
- **⭐ Killing your own hypothesis with evidence is a SUCCESS. Report it as one.** You are assigned a layer, not a conclusion. "My layer is clean, here's the proof" is a first-class deliverable and shortens the whole inquest. Members who confirm their assignment 100% of the time are useless.
- **Severity** ∈ `ROOT CAUSE | CONTRIBUTING | INCIDENTAL | CLEAN` and **confidence** ∈ `PROVEN | LIKELY | SPECULATIVE`, as **separate** axes. A PROVEN INCIDENTAL and a SPECULATIVE ROOT CAUSE are both useful and behave differently. In the reference run, a member's own `LIKELY` caveat is what exposed its error.
- **Report what you checked and found clean**, explicitly. Exclusion is evidence. It's how the boundary gets drawn.
- **Say what you could not verify and why.** Never fabricate a query result, a status code, or a test outcome.
- **Read-only.** No mutations, no deploys, no commits, no ticket comments. Diagnosis and remedy are separate phases with a human gate between.

### Feed members your own leads — and invite refutation

Hand each member your grounding hypotheses as *"confirm, refute, or extend"* — never as a conclusion. Include the prior-art candidate from Phase 0 step 3, explicitly flagged as **the most likely and therefore the most dangerous** lead, because a documented failure mode that *fits* is exactly what stops people looking further.

> In the run that produced `conclave`, members refuted **five** of the orchestrator's hypotheses with evidence — each of which would otherwise have reached the author as a confident false finding.

### Operational notes

- Members' plain text is **not** visible to the orchestrator. Instruct explicitly: *"deliver your report by sending it to `main` via SendMessage."* They will otherwise idle holding a finished report.
- Shut each member down as soon as its deliverable lands and is verified.
- Tell them the branch is checked out and they must not switch branches, install, or mutate anything.
- **Time-box.** If the council returns only SPECULATIVE hypotheses with no discriminating test possible from available access, **stop and report what access is needed.** Do not iterate hopefully. A named blocker beats a guess.

---

## Phase 2 — Synthesis: establish cause

**The synthesiser is a verifier, not a stapler.**

1. **Re-run every ROOT CAUSE claim's discriminating test yourself.** Open the file. Run the query.
   **⭐ Re-verify REFUTATIONS to the same standard.** A member that kills a hypothesis — including
   yours — is making a load-bearing claim too. Verifying only the findings that *add* work while
   accepting the ones that *remove* it is an asymmetry that drifts the whole inquest toward
   "no bug". Read the code the refutation cites; re-run the probe it corrects.
2. **Prefer executed evidence over predicted behaviour** — always.
3. **Draw the boundary explicitly.** Affected: X. Clean: Y. The cause must explain *both*. A hypothesis that explains the failure but not the clean cases is incomplete, and that gap is usually where the real cause hides.
4. **Reconcile contradictions with evidence.** Never average two members.
5. **Report the honest tally**, including dissent. If `devil` still argues no-bug, say so and say why it was overruled.
6. **Name the layer that will be changed, and prove the consumer reads it** (the matching-values rule above). This is the single highest-value step in the whole method.
7. **Score the ticket rubric** — and be willing to conclude *"the reported symptom is real and its cause is in another system"*, with a discriminating test and a recommended scope split.

### ⭐ The standard of proof — what `PROVEN` actually requires

A discriminating test earns `LIKELY`. **`PROVEN` requires more, and it is usually available for less effort than people assume.** Reach for as many of these as the case allows — each one converts an argument into an artifact.

1. **Reproduce BOTH sides from one source.** Don't just explain the wrong number — *produce* it. Compute the broken output and the correct output from the same place, and show each matches its observed counterpart row-for-row. *"`OC raw` reproduces the dashboard 6/6 and `OC fixed` reproduces the client's pivot 6/6"* is unarguable in a way that no narrative is.
2. **Reconcile the discrepancy arithmetically, to the unit.** Not "orders are inflated" but `fixed + unknown == raw`, **in every row**. An identity that accounts for the gap *exactly*, decomposed into named components, is categorically stronger than a prediction of direction or magnitude. If your explanation leaves a remainder, you have part of the cause.
3. **Name the individual culprit records.** Not "there are placeholder rows" but *"2 real orders `SC_8996515`, `SC_8996539` plus 6 daily buckets `UNK_2026-07-11_USD` … `UNK_2026-07-17_USD` = the 8 shown."* Instance-level evidence survives scrutiny that aggregate evidence does not.
4. **Enumerate the whole candidate space to prove a negative.** Where the candidate set is finite and enumerable, *enumerate all of it* rather than sampling. "All **269** measures audited → **0** unguarded" and "swept **27** workspaces → **no** model reproduces the dashboard column" are conclusions no amount of spot-checking can reach. **This is the single biggest upgrade available in most investigations** — the set is usually smaller than it feels, and a script that checks all of it is rarely harder than one that checks five.
5. **Prove a cause inside a system you cannot read — by elimination plus capability.** When the defect lives in code you have no access to, you can still prove it: eliminate every readable layer *exhaustively* (4), then show the intermediate layer is **structurally incapable** of producing the symptom (e.g. *the API builds `SUMMARIZECOLUMNS` only, so it cannot apply an arbitrary distinct-count*). Cause is then established by construction, without reading a line of the offending source.
6. **Run a negative control.** Find the case where your hypothesis predicts **no difference**, and show there is none. A window with zero placeholder rows where broken and correct outputs must agree *exactly* is stronger evidence than ten more cases where they differ. Positive cases confirm; the negative control is what rules out over-correction and coincidence.
7. **State the sample and its limits.** Six rows, one vendor, one week is a real proof of *mechanism* and a weak proof of *scope*. Say which you have. Then widen it, or name the residual risk explicitly — don't let a mechanism proof masquerade as a blast-radius proof.

**If you cannot reach `PROVEN`, say `LIKELY` and name exactly which of the above is missing.** That sentence is what tells the next session where to start, and it is the difference between honest and merely confident.

### Verdicts — pick one, plainly

`ROOT CAUSE PROVEN` · `ROOT CAUSE LIKELY (named residual risk)` · `NOT REPRODUCIBLE (surface proven healthy)` · `CORRECT BEHAVIOUR (report invalid — explain kindly)` · `BLOCKED ON ACCESS (name it)` · **`DEFECT FOUND — NOT THE REPORTED ONE`**

Never dress up `LIKELY` as `PROVEN` to close a ticket.

**On `DEFECT FOUND — NOT THE REPORTED ONE`:** a genuinely common bug-hunt outcome, and the one most
often mis-reported. You proved a real defect *and* proved it cannot produce the reported symptom.
**State the two separately, each with its own severity and confidence** — "here is a real bug worth
its own ticket" and "here is what remains unexplained about the report". Do not let a well-evidenced
side-finding stand in for the answer, and do not bury it either.

---

## Phase 3 — Fix and prove it

1. **Write the failing test FIRST**, against the reproduction from Gate 3. It must fail for the documented reason.
2. **Fix at the proven layer.** Smallest change that closes the cause. Not the symptom.

   ⚠ **"Smallest" means smallest blast radius, not the most local-looking edit.** Before changing a *value*, establish whether anything selects *rows* by it — a join, a filter, a semi-join. **Changing a value can silently change the row set, not just the field.** Editing one branch of a union looks tighter than editing the shared output projection, and is far more dangerous when that branch feeds an inner join on the column you touched. *Real case: nulling a placeholder id in the branch that produced it deleted 471k rows and $423K of spend, because a downstream `INNER JOIN … ON a.ID = b.ID` stopped matching. The identical null in the outer projection — evaluated after every join — was correct and inert.*
3. **⭐ MUTATION-TEST THE REGRESSION TEST.** Revert the fix; confirm the new test goes **RED**; restore the fix; confirm **GREEN**. Record both outputs.

   **A regression test never observed failing without the fix guards nothing.** This is the most valuable technique carried over from `conclave`, and it is stronger here: in the reference run, mutation proof showed new tests staying green while *three of five* new rules were gutted.

   ⚠ **Mutation-testing is necessary but NOT sufficient — and the reason is specific.** It proves an assertion is *sensitive to the fix*. It cannot prove the assertion is *insensitive to catastrophe*. An assertion shaped "the bad thing is absent" can be satisfied by destroying the population it measures, and still goes RED without the fix — so it passes this gate cleanly while guarding nothing. *Real case: `unknown_rows_with_id == 0` printed "applied and verified" when the change had deleted every one of those rows; it is trivially true once `unknown_rows` is itself 0.* **Pair every absence assertion with an explicit expected value for the population** — `total_rows == N`, the subpopulation count, both distinct counts, the money column. That is what step 5's "row counts stable" is for, so **treat step 5 as a precondition of step 3, not a later formality.**
4. **Verify at the consumer's layer — the rendered surface, not the query.** For any dashboard/report/UI:
   - **every visual paints** — no error or empty states
   - headline numbers **anchored** to a source of truth (source==consumer, or old==new parity when repointing)
   - **exercise every filter/slicer/timeframe** and record which respond vs are **inert** — a silent no-op is a finding to document, never an acceptable default
   - labelled **before/after screenshots**

   A query-layer check can pass while every visual is blank. Proven: a repoint passed DAX parity while every visual showed "Error loading data" from a stale name binding.
5. **Prove no regression.** Out-of-scope rows/objects/users unchanged; before/after deltas equal to expectation; row counts stable. State this explicitly — "I didn't touch that" is not evidence.
6. **Re-run the surrounding suite**, not just your new test.

---

## Phase 4 — The deploy gate

**Present the evidence, then stop. The human opens the gate.** Never `CREATE OR REPLACE` / `UPDATE` / deploy on inference.

The gate needs all five:

| | Requirement |
|---|---|
| 1 | **Target proven** — the object the consumer actually reads, by discriminating check |
| 2 | **Correct at the consumer's layer** — rendered, with artifacts |
| 3 | **No regression** — stated, with numbers |
| 4 | **Rollback captured** — original DDL/doc saved + a revert script, *before* the mutation |
| 5 | **Validated non-destructively first** — shadow copy, dry run, `WHERE FALSE` permission probe |

Re-task `devil` here as **deploy adversary**: *"here is the fix and the evidence — argue this should not ship."* Cheapest possible insurance at the highest-consequence moment.

Environment hygiene: assert the account/environment before any mutation (`assert current_account() == '<EXPECTED>'`). Beware lookalike objects — the same document ID can exist in TEST and PROD pointing at different targets.

---

## Phase 5 — Deliver

Evidence lives in three homes; **link, don't duplicate**:

- **Branch/repo** = reproducible source of truth — validation *scripts*, `docs/evidence/<ticket>.md`, screenshots
- **Jira** = acceptance + the client-relevant subset — before/after screenshots, a one-line "validated: X; evidence in commit `<sha>`". **Never wiki links in Jira** (wiki is private) — point to the branch/commit/PR
- **Wiki** = the durable lesson — the gotcha and the reusable check, not per-run blobs

Then write the honest close: verdict, cause, fix, what was proven and *how*, what remains open, TEST-vs-PROD. If it shipped to TEST only, say TEST only.

---

## Parallel inquests — the mutation lock

Two inquests on overlapping surfaces will corrupt each other's evidence. **Read-only diagnosis in parallel is safe and encouraged. Mutations must serialise.**

Before Phase 4, each session appends to a shared lock file (e.g. `docs/evidence/INQUEST-LOCK.md`):

```
## <TICKET> — <session start time>
INTENDS TO MUTATE: <object IDs / views / files>
STATUS: pending | applied | rolled back
```

Read the file first. **If another session lists an overlapping object, do not proceed — hand back to the human to sequence.** An A/B rollback measurement is worthless if a second session changed the same object mid-measurement.

Also: if a shared asset is touched (one visual serving many dashboards, one view feeding many reports), say how many consumers inherit the change, and re-run the shared suite.

---

## Anti-patterns

| Don't | Because |
|---|---|
| Theorise before reproducing | The most expensive way to be wrong |
| Infer the target from matching values | Caused a real wrong-layer deploy + revert |
| Run a test whose outcome you didn't predict | You'll rationalise whatever you see |
| Accept the first fitting documented failure mode | A plausible fit is what stops people looking |
| Let a member confirm its own assignment every time | Then the layer split bought you nothing |
| Validate at the query layer and call it done | Every visual can be blank while DAX passes |
| Ship a regression test never seen failing | It guards nothing; you've tested that code exists |
| Assert only that the bad thing is absent | Deleting the population satisfies it — and it still passes mutation-testing. Pin the population's expected size too |
| Change a value without checking what joins on it | A value change can change the row set; one union branch cost 471k rows and $423K |
| Mutate prod without a saved rollback | There is no undo for `CREATE OR REPLACE` |
| Report LIKELY as PROVEN to close a ticket | The next session inherits a false fact |
| Sample when the candidate set is enumerable | "All 269 checked, 0 unguarded" is a conclusion; "I checked five" is a hint |
| Explain the wrong number without reproducing it | Producing the broken output is the proof; explaining it is a story |
| Leave a remainder in the arithmetic | An unaccounted gap means you have part of the cause, not the cause |
| Skip the negative control | Positive cases can't rule out coincidence or over-correction |
| Mutate a shared object while another inquest measures it | Both sets of evidence become worthless |
| Convene 5 agents for a visible stack trace | Cost without benefit; just fix it |
| Convene on *a* defect you found instead of *the* reported symptom | Your frame reaches every member; they'll all hunt the wrong thing |
| Trust a matrix where every cell reads the same | Almost always a broken parser, not a uniform truth |
| Probe with your own request state instead of the consumer's | Client-sent filters/params/identity are invisible to a hand-built probe |
| Re-verify findings but accept refutations on trust | The asymmetry drifts you toward "no bug" |
| Exhaust probing before asking the reporter one question | Their one sentence routinely beats hundreds of requests |

---

## Provenance

Derived from `conclave` (adversarial PR review, `ALDC-io/zeus-chat-exp#167` / ALDC-739), keeping what
was proven there — the two gates, separate severity/confidence axes, leads fed for refutation,
mutation-tested tests, SendMessage delivery — and replacing the review machinery with **Gate 3
reproduction**, the **discriminating-test contract**, the **wrong-layer tripwire**, **rendered-layer
verification**, and the **evidence-gated deploy**, from this estate's own incidents.

Hardened after the **GP-309** run (2026-07-30): Gate 2 instrument calibration; Gate 3's
reported-symptom rule, ask-the-reporter step, and consumer-request-state rule; the brief's
correlated-error warning; symmetric verification of refutations; and the
`DEFECT FOUND — NOT THE REPORTED ONE` verdict. Stack-specific gotchas from that run live in the
wiki, not here — this skill stays stack-agnostic.
