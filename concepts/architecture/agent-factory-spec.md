---
tags: [architecture, spec, agent-factory, evaluation, greencontract, sandbox, control-plane, research]
aliases: [Agent Factory Spec, Agent Factory v1, Zeus Pantheon Suite spec, isolation ladder, AgentSpec]
sources: [github.com/ALDC-io/agent-factory@feat/readiness-generator, agent-factory/docs/specs/architecture-v0.md, agent-factory/docs/research/SYNTHESIS.md, agent-factory/BRAIN-DUMP.md, agent-factory/factory/readiness.py, agent-factory/factory/connector_contract.py]
created: 2026-08-22
updated: 2026-08-22
---

# Agent Factory — Design Spec v1

The buildable specification for **`github.com/ALDC-io/agent-factory`**: what it is, what it
refuses to be, the four planes it is built from, and the order the work happens in. It supersedes
`docs/specs/architecture-v0.md` — that document called itself *"a strawman to be attacked"* and
named five places it expected to be wrong; this one carries the attack and the verdicts.

See [[agent-factory]] for the running project log and [[orchestrator]] for what the gates found in
the build plane. **Every claim here is tiered** — `MEASURED` · `DOCUMENTED` · `REPORTED` ·
`REASONED` · `BET` — and an untiered sentence in this document is a defect.

**Contents** — §1 purpose · §2 invariants · §3 the four planes · §4 object model · §5 the isolation
ladder · §6 capability and credentials · §7 certification and the AgentSpec · §8 the control plane ·
§9 the contract · §10 the corpus · §11 session orchestration · §12 the readout · §13 teams ·
§14 build order · §15 deliberately not built · §16 where this is most likely wrong · §17 open
research · §18 what the deep-research pass settled · §19 operational gotchas
---

## 1. What this is for

> A factory that manufactures **agent teams whose output can be certified rather than believed**,
> starting with one team that migrates a data connector end to end: source → container → Prefect →
> Snowflake.

The premise is not ambition, it is a scar. This estate has twice shipped mechanisms that *acted*
without anything measuring whether the action helped:

| | What it did | What measured it |
|---|---|---|
| Retired triage agent | 233 diagnoses, 234 escalations, **0 fixes**, 81 days | nothing |
| Orchestrator restart loop | 965 runs, recorded its own **1.6%** success rate | itself, and it never adjusted |

`MEASURED` — both figures are from recorded evidence, not recollection.

Both were capable. Neither was measurable. So the ordering is fixed and is the whole design:

```
what "done" means  →  whether that definition can fail  →  everything else
```

Every deferral in §14 follows from that sentence, and so does every refusal in §15.

### 1.1 Scope of the first team

**In:** source API → connector container → Prefect flow → Snowflake landing and merge.
**Out, deliberately:** Power BI. Power BI is the consumer-layer oracle (§9.4) and it is where the
estate's most expensive false greens have happened, but a team that cannot yet land rows cannot be
graded on what a dashboard renders. Power BI enters at Phase 3. `REASONED`

### 1.2 What "certified" has to mean

A certification is a statement by a party that is **not the agent**, about an artefact identified
by **hash**, against a contract the agent **did not choose**, recorded somewhere the agent
**cannot rewrite**. Anything short of all four is a claim, not a certification. Today the repo
satisfies the first three in design and none in deployment (§7). `MEASURED`
---

## 2. The invariants — nothing in this spec may violate these

These are specification, not configuration. §15 says explicitly that they are **never optimised**:
optimising a retry cap rewards more retries; optimising a gate threshold changes the ruler.

| # | Invariant | Enforced by |
|---|---|---|
| **I1** | **Four verdicts, never collapsed.** `PASS` / `FAIL` / `UNMEASURABLE` / `NOT_RUN`. `UNMEASURABLE` is not a pass and exits non-zero. | `factory/contract.py`, `factory/readiness.py` |
| **I2** | **Probes refuse by default.** An unwired harness returns 12× `UNMEASURABLE`, never 12× `PASS`. | `factory/connector_contract.py` |
| **I3** | **Every assertion must have been observed failing.** `test_every_assertion_has_been_proved_able_to_fail` reddens the suite if any has not. | `tests/test_eval_can_fail.py` |
| **I4** | **The graded party never writes the verdict.** The agent supplies `{artifact_uri, artifact_sha256, run_id}` and has nowhere to put anything else. | `factory/evaluator.py`, `evaluator_service/` |
| **I5** | **Merging stays human.** `finish()` asserts, pushes, announces, releases — and refuses to merge. | `factory/finish.py` |
| **I6** | **Per-secret grant stays human.** No tier self-serves a credential. | §6, §7 |
| **I7** | **Terminal verdicts are derived from append-only history, never read from a mutable status field.** | §8.3 |
| **I8** | **Tenancy scope is never read from landed rows.** "Which accounts arrived" is not "which were requested". | `A12`, §9.5 |
| **I9** | **A control that has never been watched refusing is decoration.** Every gate ships with a negative drill. | §11 |
| **I10** | **The presentation layer may never change state, counts, verdicts, measurements or epistemic labels.** | §12 |

> **I3 and I9 are the same rule at two altitudes**, and they are the rule this programme exists to
> enforce. The evidence they exist: **0 of 22** recorded gate events have ever been a refusal.
> `MEASURED`

### 2.1 The failure family, named

[[vacuous-verification]] — the work happened, it was just not the work anyone asked for. Every
defect below is one instance, and all of them are from **this** repo, this month. `MEASURED`

- A completeness assertion guarded on a blueprint field left empty: **it silently did not run** and
  reported *"18 rows satisfy every declared invariant"* over a partial extraction missing an entire
  account.
- An evaluator-isolation probe that **grepped for its own source strings** and reported an
  evaluator was configured when none existed.
- `--model` built into a variable nothing read: three lanes announced their model in the banner and
  all ran the session default.
- `setx VAR "value"` from bash storing the quote characters, while the gate — which only checks the
  variable is non-empty — read PASS.
- A published artifact reading `3 of 23` while the repo was at `9 of 30`, because a published
  artifact only changes when someone republishes it.

**The generalisation:** an invariant that quietly does not run is an assertion that quietly stopped
being made, and that is indistinguishable from a pass.
---

## 3. The four planes

The shape is four planes with a hard boundary between them — **DECIDE**, **RUN**, **PROVE**,
**APPROVE** — and one rule that makes the boundary mean something: *the thing being measured must
not be the thing doing the measuring.*

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  APPROVE   humans only.  merge · per-secret grant · promote to prod           │
│            never automated — finish() already refuses to merge          (I5)  │
└──────────────▲──────────────────────────────────────────────────┬─────────────┘
               │ evidence bundle                                   │ decisions
┌──────────────┴──────────────────────────────────────────────────▼─────────────┐
│  PROVE     GreenContract A1–A12 · readiness gates · corpus · findings.d        │
│            the evaluator is a SEPARATE PRINCIPAL the agent cannot be    (I4)  │
└──────────────▲──────────────────────────────────────────────────┬─────────────┘
               │ artefact uri + sha256 + run id                    │ verdict
┌──────────────┴──────────────────────────────────────────────────▼─────────────┐
│  RUN       the isolation ladder — T0 worktree · T1 container ·                 │
│            T2 container + ephemeral warehouse clone                     (§5)  │
└──────────────▲──────────────────────────────────────────────────┬─────────────┘
               │ claims · bus · finish · cost events               │ dispatch
┌──────────────┴──────────────────────────────────────────────────▼─────────────┐
│  DECIDE    conflict graph · claims · scheduling · attempt caps · budgets       │
│            the build plane — bespoke, and does NOT import Prefect       (§8)  │
└───────────────────────────────────────────────────────────────────────────────┘
```

**The load-bearing boundary is RUN ↔ PROVE.** Everything else is organisation; that one is a
security property. It is currently **aspirational**: the evaluator runs as loopback under one uid,
which prior research grades *rank 5, "mostly theatre"*. The design is rank 1. The gap is a managed
identity the agent sandbox does not hold — **a deployment change, not a code change**. `MEASURED`

### 3.1 Why four and not three

The obvious collapse is PROVE into APPROVE: a human reads the evidence, so why is proving separate
from approving? Because the two fail differently. PROVE fails by **measuring nothing and saying so
in green** — the whole subject of §2.1. APPROVE fails by **a human clicking through**. They need
different controls: PROVE needs negative drills (I9), APPROVE needs the evidence bundle to be
mechanically produced so the human is reading something they did not have to assemble. `REASONED`

The genuine risk is the reverse: PROVE and APPROVE do **not** separate cleanly when the evidence a
human needs is itself produced by the thing being judged. That is tracked as a live risk in §16.
---

## 4. The object model — and the tiers that stay empty

The original brief asked for **Agent Army → Agent Team Manager → Agent Team → Agent**, with
messaging across every pair. The research verdict was blunt: **one end-to-end worker agent, plus a
non-LLM verifier holding the authoritative PASS bit.** No LLM manager, no LLM architect, no LLM
tester, no agent-to-agent channel. `REPORTED` — 180 configurations across 5 architectures, 3 model
families and 4 agentic benchmarks; multi-agent averaged **−3.5%**, and *sequential shared-state
tasks degraded 39–70%*. Connector migration is sequential shared-state work: the class that did
worst.

So the spec keeps the **nouns** and instantiates almost none of them:

```
Army        a data model row. ZERO supervisor LLMs instantiated.        (schema only)
Team        a named set of AgentSpecs + one Contract + one Corpus.      (one exists: connector-e2e)
Agent       ONE end-to-end worker: inspect → plan → implement → self-test → repair
Verifier    non-LLM. Owns the PASS bit. Not an agent, not addressable, not persuadable.
Human       merge, per-secret grant, promotion.                          (I5, I6)
```

> ⭐ **Build the data model so a supervisor tier *could* be added; instantiate zero supervisor
> LLMs.** The schema is cheap now and expensive to retrofit; the LLM is expensive now and cheap to
> add later. This is the only place in the spec where "build it before you need it" is correct, and
> it is correct because a schema is not a behaviour.

### 4.1 The agent is an artefact, not a session

Today an agent is a `Lane`: a prompt string, a model, a gate list — that is a *launcher input*. The
`version` gate wants 15 dimensions and covers **0 of 15**. `MEASURED`

The manufacturing step the repo does not yet have is this: **the factory's output is an AgentSpec,
not a session.** Full definition and the honest limits of hashing a non-deterministic system in §7.

### 4.2 Communication — the record and the channel are different objects

One file was asked to be a permanent mergeable archive *and* a live nudge between running
processes. It could not be: three isolated worktrees each correctly read `F10` as the last id and
each wrote its own `F11` and `F12`, and a merge would have silently destroyed two of each.
`MEASURED`

| | The **RECORD** | The **CHANNEL** |
|---|---|---|
| Where | `docs/findings.d/`, one file per finding | `.data/bus/`, one append-only file per writer |
| In git | yes — reviewed, permanent | **no**, and that is correct |
| Lifetime | forever | dies with the lanes |
| Delivery | read at lane start | **hook-injected** as `additionalContext` |
| Answers | "what did we learn" | "what do you need to know now" |

**The read path is the load-bearing half.** A channel nobody reads is decoration, and telling an
agent to poll at checkpoints works until the session that does not bother — which is the session
that most needed telling. So delivery is a hook, not a convention. `MEASURED`

**Agent ↔ agent request/response stays unbuilt.** Every question that actually arose during three
parallel lanes needed a *human* — a credential grant, a go/no-go. Building agent dialogue before a
case exists is inventing a requirement. Unlock condition in §15. `REASONED`

### 4.3 Findings carry KIND, and that is not bookkeeping

Most findings are **corrections**: read it, fix it, spent. A **design consequence** is not spent
until it is built or deliberately refused. The ledger could not tell those apart, so design
findings were filed, admired and never acted on. `CHANGES` is now mandatory when the kind is a
design one, and `design_debt()` is the list that must shrink. `MEASURED`
---

## 5. The isolation ladder — tier by what the task touches, not by what the agent is

**The load-bearing idea in this spec**, and the one most likely to be wrong (§16).

> An agent's isolation tier is chosen by **what its task touches**, declared up front in the
> AgentSpec, and **enforced by the DECIDE plane** — not chosen by what kind of agent it is.

| Tier | Environment | May touch | Use for |
|---|---|---|---|
| **T0** | git worktree, operator machine *(built)* | repo files only. **No network egress, no DB verbs** | code edits, docs, specs, tests |
| **T1** | container, egress allowlist, **read-only** warehouse role | repo + `SELECT` on real data | analysis, reconciliation, *"is this number right"* |
| **T2** | container + **ephemeral clone schema**, dropped on exit | repo + full DDL/DML **inside the clone only** | building views, migrations, backfills |

Three consequences, and they are the argument:

1. **T2 removes the file-conflict cap for data work.** Two agents in two clone schemas conflict on
   nothing, so the 3-lane ceiling (§11.5) applies to T0 code lanes and does not generalise.
   `DERIVED` — and see §5.4, where this is attacked.
2. **The dangerous verb is contained by construction, not by prompt.** *"Do not touch prod"* in a
   prompt is a **request**; a role with no grant on prod is a **control**. This is the thing generic
   agent frameworks miss: isolating a filesystem does nothing when the risk is DDL on a shared
   warehouse. `REASONED`
3. **Promotion out of a clone is an APPROVE-plane act.** The estate's evidence-gated rule already
   says: prove the target, validate at the consumer's layer, prove no regression, capture a
   rollback. Against a clone that becomes a **clone→real diff, mechanically producible from a T2
   run** rather than assembled by hand. `REASONED`

### 5.1 The tier is enforced, and a refusal is an audit event

An agent that asks for a verb its tier does not carry is **refused**, and the refusal is recorded
where the operator can reach it (§11.4). That is not only safety — it is the only way gate
`refuses` ever gets something real to record, and **0 of 22 gate events have ever been a refusal**.
`MEASURED`

Enforcement lives in the launcher: the sandbox is **constructed from the spec**, so a tier is not a
field an agent can talk its way past. A tier declared in a spec that nothing reads is the `--model`
defect again (§11.2) — so **the ladder needs a test per tier asserting the constraint reaches the
process**, not a test asserting the field is set.

### 5.2 What is actually built today

**Nothing.** `MEASURED` — agents run as the operator, on the operator's Windows machine, with the
operator's credentials, and there is no dry-run gate, no row-count diff and no rollback capture.
T0's isolation is a git worktree, which isolates *files* and nothing else: a T0 agent today can
reach the network and hold every credential the operator holds. **T0 as specified above does not
exist either.**
---

## 6. Capability and credentials — the plane the generic sandbox literature does not address

**Credentials are the whole job.** A data agent needs warehouse, API and vault access by
definition, so every sandbox story that assumes *"no network, no secrets"* answers a different
question than this one. The tier ladder in §5 is only a control if the credential attached to each
tier is a *different principal with different grants* — otherwise T1 and T2 are the same tier
wearing different labels.

### 6.1 The three rules

1. **The operator's credential is never the agent's credential.** Today it is. `MEASURED`
2. **Per-secret grant stays human** (I6). No tier self-serves a credential; a tier *requests*, a
   human *grants*, and both the grant and the refusal are recorded.
3. **A grant is scoped and expires.** A credential that outlives the run it was issued for is a
   standing grant with extra steps.

### 6.2 What this buys that a prompt cannot

The estate's blast-radius problem is not the filesystem. `git revert` does not undo a `CREATE OR
REPLACE` that stripped ownership and a share grant, and it does not un-invoice a client against a
number that silently changed. A role with no grant on production is the only version of *"do not
touch prod"* that is a control rather than a request.

**And it is measurable in a way a prompt is not:** a refused verb produces an audit event; a prompt
that worked and a prompt that was ignored look identical.
---

## 7. Certification — the grader is a separate principal, and the agent is a versioned artefact

### 7.1 The submission vocabulary is the whole design

**The agent supplies `{artifact_uri, artifact_sha256, run_id}` and nothing else.** Not the corpus,
not the manifest, not the assertion set, not the evaluator. Those are resolved by the service from
its own configuration on every request, and the client has nowhere to put them — `Submission` has
three fields and the service **refuses a body carrying a fourth**, rather than silently filtering
it. `MEASURED`

| | |
|---|---|
| `factory/evaluator.py` | `EvaluatorClient` — three verbs, no writer, **no local fallback** |
| `evaluator_service/` | the separate principal; write-once verdict store outside the repo |
| `factory/certify.py --remote` | certification routed through the service |

Four refusals were **watched happening**, then mutation-tested — three mutants introduced, three
caught: `MEASURED`

| Attack an agent with shell + repo write could actually mount | Result |
|---|---|
| **Weaken the target** — submit a blueprint with `expect_rows: false`, empty `primary_key`, empty `non_null_positive`, no `tenant_column` | `REFUSED` — *"weaker than this evaluator's floor"* |
| **Name your own corpus** — POST a body carrying a fourth field, `corpus_path` | HTTP 400 — *"not part of the submission vocabulary"* |
| **Swap the artefact** — claim the real blueprint's sha256, present a different file | `REFUSED` — sha mismatch. **Not a FAIL: nothing was scored** |
| **Replace an unkind verdict** — resubmit under an existing run id | Scored, **not recorded**; the original is intact |

**Nothing that is not a PASS exits 0.** `REFUSED` → 1. No endpoint configured → 1, and explicitly
*"not a licence to score locally"*. Unreachable → 1, `UNMEASURABLE`.

⭐ The discriminating test is `test_the_service_supplies_the_tenants_not_the_submission`: the
shipped blueprint's six dash-formatted account ids do **not** appear in the corpus, whose tenants
are two ten-digit ids. If the submission governed tenancy, A12 would FAIL. It passes — which is
only possible if the service overrode it. A test that would pass either way proves nothing; this
one cannot.

### 7.2 Two holes, stated plainly

⛔ **Do not read the green `isolated` gate as "the agent cannot cheat."** The deployment is loopback
under one uid — rank 5, *"mostly theatre"*. The **design** is rank 1. The gap is a managed identity
the agent sandbox does not hold, which is a **deployment change, not a code change**. `MEASURED`

⚠ **The real remaining hole: the contract is parameterised by a blueprint the graded party
writes.** An agent that softens its own blueprint softens its own grading, process boundary or not.
A four-rule target floor and the artefact hash narrow it. **A per-connector target pinned by the
evaluator would close it, and nobody has written one.** That is Phase 3 work and it is named in
§16.

⚠ **Tamper-evident is not tamper-proof.** Anyone with write access to both the corpus and its
manifest can re-pin silently. The fix is credential separation, not a cleverer hash.

### 7.3 The AgentSpec — the manufacturing output

```yaml
AgentSpec:
  id: navira-view-builder
  version: 7                     # bumped on ANY field below — that is the point
  prompt_ref: prompts/view-builder@a3f9c1      # content-addressed, never inline
  model: sonnet
  effort: medium
  tools: [read, edit, bash, snowflake_ro]
  tier: T2                       # chooses the sandbox — §5
  budget: {tokens: 400k, wall_clock: 45m, warehouse_credits: 2}
  contract: green@v5             # which assertions must pass to be certified
  gates: [grain, no-regression, consumer-render]
  needs_human: [credential-grant, merge, promote]
```

Two rules follow, and the second is the expensive one:

- **The version hash covers every field.** A certification granted under `green@v4` must not
  silently transfer to `v5`. Verifier drift bites today: the corpus is hash-pinned but the
  **contract version is not in the agent hash**, so a certification can outlive the thing that
  granted it. `MEASURED`
- **A spec field that nothing reads is worse than no field.** This month produced a `--model` flag
  in a dead variable, a detector degrading to 1 finding instead of 313, and gates reporting PASS
  while measuring nothing. **Every field needs a test asserting it reaches the process.** `MEASURED`
---

## 8. The control plane — bounding a loop that has never been bounded

DECIDE is a **bespoke engine at `:8765` that does not import Prefect**. That matters more than it
sounds: two research passes prescribed Prefect's configured retry limits, tag-based concurrency and
zombie handling as *available primitives*. They are not available on this plane. Attempt caps,
leases, orphan timeouts and concurrency reservation must be **built**, not enabled. It changes
implementation cost, not direction — and whether to move the plane onto Prefect rather than
reimplement its primitives is the highest-value unasked research question (§17). `MEASURED`

### 8.1 What has to be true before anything else

```
1  hard external attempt / spend / concurrency budget       ← non-negotiable
2  timeout + cancellation + orphan reaping + restart reconciliation
3  terminal verdict computed from append-only history, not current state
4  refusal-capable gates, with negative drills
5  tenant capability isolation at every persistence/promotion boundary
6  complete attempt/cost telemetry, including failures
7  external evaluator trust boundary (a service, not a directory)
8  expand and freeze the evaluation corpus
9  ── only here ── configuration experiments
```

Steps 1–4 are non-negotiable. Steps 5–7 must also precede optimisation *"because otherwise the
optimisation score itself is not safe to trust."* `REPORTED`

### 8.2 The numbers that say why

| Figure | Value | Basis |
|---|---:|---|
| Recorded runs that finished with no human | **3 of 14** | `MEASURED`, audits |
| Stage attempts failed vs completed, all-time | **1,001 / 165** | `MEASURED` — mostly one uncapped-restart incident |
| Worst restarts in a single run | **352** | `MEASURED` |
| Gate events that were ever a refusal | **0 of 22** | `MEASURED` |
| Cost per agent run | **not instrumented** | nothing records tokens or wall clock |

⚠ **The audit log those gates measure stopped on 2026-05-28.** Nothing has run in the orchestrator
since, and it is not currently running. *"3 of 14 runs finished"* is true of a history three months
old, and until the measurement window landed the gates did not say so. `MEASURED`

### 8.3 ⛔ The false `succeeded`, and what replaces it

The mechanism is a **last-write-wins per-stage status field used as evidence about a history**. A
stage that failed 100 times and succeeded on the 101st reads `completed`, so `any_failed` is False.
`orchestrator/pipelines.py` does not import Prefect — an earlier diagnosis attributing this to
Prefect's final-state rules was wrong, and was carried into a second research question before
anyone walked the route. `MEASURED`

**The correct form: a terminal verdict computed from the append-only event log**, never read from
current state. Current state cannot answer a question about what it cost to get there. Gate
`from-history` measures exactly this, and gate `truthful` — *"does a recorded status match its own
event log?"* — is the same defect one level up.

**The negative control this needs:** a fixture in which a false `succeeded` is *constructible* —
100 recorded failures then one success — with the verdict refusing it. A test that cannot express
the defect is not a control.

### 8.4 Leases, reaping, and the four runs that will never finish

`claims.py` has `STALE_AFTER = 4h` and **does not auto-expire**; a closed lane leaves its claim held
for four hours with nothing to reap it — which is the `reaper` gate the same lane is building.
Meanwhile four orchestrator runs sit at `stage_started` **forever**, and gate `finishes` requires
every recorded run to be terminal, so a perfect agent still reads FAIL (§14.1). **The reaper only
helps if it backfills terminal events for those four.** `MEASURED`

The design rule from §11.3 applies here too, and it is the one to get right: **a lock guards a
resource, not a worker.** Anything that releases a lease must first establish the holder has
stopped, and *"could not tell"* is a third verdict, never a silent release.

### 8.5 The lifecycle — four external states over a richer internal one

Four terminal states are a useful **external business-outcome projection**, not an industry
standard. The internal lifecycle is richer: `RESERVED` · `DISPATCHING` · `RUNNING` ·
`CANCEL_REQUESTED` · `REAPING` · `ORPHANED`. `REPORTED`

⚠ `NEEDS_HUMAN` is **incoherent as a terminal state** if a run can be resumed from it. Either close
the run and create a continuation carrying `parent_run_id`, or model `PAUSED_FOR_HUMAN` separately.
Adopted as stated.

**Three attempts** ships as a policy default and is recorded as `ASSUMED` — graded *"a defensible
safety default, not validated for this workload"* — and same-failure detection is weaker still:
*"'same failure' for an LLM software agent has no mature standard definition."* Revisit from data,
and **never from an optimiser** (§13.1).

### 8.6 Cost telemetry is a prerequisite, not a report

Gate `ceiling` depends on gate `cost`, and the dependency is authored rather than inferred for a
reason: **a ceiling read from a figure blind to failures is not a ceiling.** Today nothing records
tokens or wall clock, so every claim in this spec about a *cheap* lane or an *expensive* search is
reasoning, not measurement — including the 1,584-agent-hour figure in §13.1, which excludes the
1,001 failed attempts whose cost is unrecorded. **There is no honest dollar estimate of anything
here until failed attempts record cost.** `MEASURED`
---

## 9. The contract — twelve assertions, and the two that already caught the harness

The **GreenContract** is twelve assertions a connector migration must satisfy end to end,
executable, parameterised per connector from YAML. **The contract is code; what "green" means for
one connector is data.** Keeping them apart is what lets the same twelve assertions judge every
connector, and what lets a target be pinned in a lockfile beside the code that judges it.

| | Assertion | What it is for |
|---|---|---|
| **A1** | `config-satisfiable` | connection + options construct for this account |
| **A2** | `credential-authenticates` | **live auth**, not vault presence |
| **A3** | `exact-image-resolves` | the digest that will run imports the connector |
| **A4** | `deployment-binding` | the deployment pins the digest A3 proved |
| **A5** | `regression-suite` | pinned suite green at the **pinned revision** |
| **A6** | `run-completed` | necessary, **insufficient** — see A7 |
| **A7** | `fresh-landing-proven` | rows stamped with **this** run's session id |
| **A8** | `load-fidelity` | landed == emitted |
| **A9** | `semantic-invariants` | the connector's own meaning |
| **A10** | `source-agreement` | an independent second instrument |
| **A11** | `no-forbidden-action` | policy scan |
| **A12** | `tenancy-scope` | no other client's rows landed here |

### 9.1 The two tests that carry the argument

- **`test_silent_empty_is_caught_by_a7_while_a6_still_passes`** — the runtime swallows non-200
  responses and returns an empty dataframe, so the flow run reaches `COMPLETED` with nothing
  landed. **A6 passes. A7 fails.** That gap is the entire reason the contract exists.
- **`test_rows_from_a_previous_run_do_not_satisfy_a7`** — a table a prior run populated returns a
  healthy row count and proves nothing about this one. Only the session-id stamp does.

Calibration on the one recorded end-to-end success (`windsorai`, 2026-08-20): three runs — the
known-good world **PASS 12/12** (the contract does not cry wolf), a mutated credential **FAIL on
A2**, and one requested account dropped from the landing **FAIL on A9 and A10 while A6 still
PASSES**. The third reproduces the shape of both historical failures in this estate: *a mechanism
reporting success over a population it could not see.* `MEASURED`

### 9.2 ⭐ The hole the calibration found that review did not

The first matrix run **passed a partial extraction** — an entire account missing, and A9 reporting
*"18 rows satisfy every declared invariant"*. Cause: the completeness invariant was guarded on
`target.required_keys`, which the blueprint left **empty**, so the check silently did not run.

Fixed **structurally**, not by filling the list: requested keys now come from the live config
observation, and when neither the blueprint nor the config can supply them, **A9 raises
`Unmeasurable`**. `MEASURED`

> **An invariant that quietly does not run is an assertion that quietly stopped being made**, and
> that is indistinguishable from a pass unless the harness says so.

The general form, and it should be applied to every future assertion: **a guard clause on an
assertion is a silent opt-out unless the empty case raises.**

### 9.3 A12 — and why `windsorai` is not certifiable today

```
connector-e2e/windsorai@GEP: UNMEASURABLE (PASS=11, UNMEASURABLE=1)
  [UNMEASURABLE] A12-tenancy-scope: target declares no tenancy scope — cannot certify blast radius
```

Eleven assertions pass against the recorded run. The twelfth blocks, and should: **one ALDC Windsor
key returns every client's accounts**, so an unfiltered pull lands Fusion92 rows in a GEP table and
nothing downstream can tell. That is a true statement about the estate, not a limitation of the
harness. **The refusal is the deliverable.** `MEASURED`

The six GEP account ids were eventually found written down in
`prefect-connectors/connector/accounts/GEP/deployments/windsorai.py:23` — Brinno, Bridgford,
bigsostore, Cibu, Slobproof, GEP-Amazon — declaring what the flow **requests**, with its own note:
*"an unfiltered team-key pull returns 45 Google accounts, of which these 6 are Navira's."*

⚠ Verified **twelve weeks** before use, and the source says *"confirm against a live pull before
activation."* A PASS means *"the landing matched what we declared"*, not *"what we declared is
still correct"*. Meta stays unfilled — 3 accounts of 19, ids never recorded — and the
`REPLACE_BEFORE_ACTIVATION_SEE_TODO` placeholder is **good design**: it matches nothing, so the
flow lands zero rows instead of silently mixing in another client's.

> **I8, restated:** never read tenancy scope from landed rows. *"Which accounts arrived"* is not
> *"which were requested"* — that is the A9 hole exactly, one table over.

### 9.4 Where A13+ has to go — the consumer-layer oracle

The four assumptions that generic agent-orchestration writing makes, and that data work breaks:

1. **The oracle is downstream and expensive.** A warehouse view can be syntactically perfect, pass
   every test, deploy cleanly, and be wrong in a way only visible when a dashboard renders a number
   a human recognises as impossible.
2. **Blast radius is not bounded by the repo.** `git revert` does not undo a `CREATE OR REPLACE`
   that stripped ownership and a share grant.
3. **Correctness is a *measurement*, not a test** — a before/after row-count and delta question
   against production-scale data.
4. **Credentials are the whole job.** Every sandbox story that assumes "no network, no secrets"
   answers a different question than ours.

**The standing estate rule that follows: a query-layer check is not a render check.** A repoint once
passed DAX parity while every visual showed *"Error loading data"*. `MEASURED` — this is why Power
BI is Phase 3 and why the contract needs a consumer-render assertion before it can claim end to
end.

### 9.5 Open questions the calibration produced — for a human, not a researcher

1. **The declared primary key cannot be right, or the grain is not what we think.** 20 rows across
   18 distinct campaigns on a single date cannot satisfy a unique `(account_id, campaign_id, date)`
   under one account. If the real table holds one account, the PK is wrong and A9 will say so on
   the first live run. *(This is lane `grain`.)*
2. **The image digest in the evidence is truncated** to 19 chars, so `expected_image_digest` is left
   empty rather than pinned to a prefix. Re-measure from the registry before pinning.
3. **No pinned test revision exists.** Pinning a *count* is wrong the moment a test is added — A5
   needs a test-tree revision hash.
4. **No live probes.** `Probes` refuses everything by design; `CtxProbes` serves the eval corpus.
   Prefect / Snowflake / registry / API implementations are the next unit of work, and each needs
   credentials. **Nothing here has touched the live warehouse** — every number is replayed from
   recorded evidence, and no Snowflake or Prefect credential has been requested or used. `MEASURED`
---

## 10. The corpus — one case is a fixture, not a calibration

`evals/corpus/*.json` + `MANIFEST.sha256`, verified on load. Editing a recorded run so a `FAILED`
reads `completed` is refused with both hashes shown. Every replayed verdict carries
`scored_against` — corpus id, sha, recorded date — and is labelled **REPLAYED, not a live
measurement**. `MEASURED`

**It holds one case and zero strata**, and that is the single largest gap in the programme.

### 10.1 The arithmetic that makes it a gap rather than a nit

`REPORTED` — the probability a corpus of *n* cases sees a blind spot affecting *p* of the stratum
at least once:

| Blind spot affects | Cases for a 95% chance of seeing ≥1 |
|---|---:|
| 10% of the stratum | **29** |
| 5% | **59** |
| 1% | **299** |

> *"One example per failure class has essentially no calibration meaning."*

### 10.2 Two distributions, never one

**Regression corpus** — every semantically distinct historical failure, **not frequency-weighted**.
The reason is the sharpest single sentence in the research: *"your observed distribution is
endogenous to a badly broken system."* Weighting to match event counts teaches the eval to imitate
the runtime's defects. Deduplicate identical signatures but keep their count as metadata.

**Challenge corpus** — stratified across 15 named mechanisms, **not** prevalence-weighted:
identity/auth · container/bootstrap · SDK drift · pagination/completeness · tenant scope · schema
drift · timeouts · duplicate/idempotency · stale state · orchestration/liveness · Snowflake load
semantics · downstream BI visibility · evaluator failure · gate failure · tamper/reward-hacking.

**The 352 unclassified stay their own stratum.** *"Unclassified is itself a first-class stratum
until someone demonstrates otherwise."* Do not redistribute them into the five known classes to get
a clean pie chart — that is precisely what the retired 8-pattern classifier did.

⭐ **Manufactured positive worlds are scorer-validation fixtures, not evidence the agent can create
those worlds.** They vary structural dimensions — single vs multi-account, pagination, legitimate
zero-row, full vs incremental, schema variants, auth forms — and they prove the *scorer* behaves,
never the agent.

### 10.3 The mutation registry is a floor, not an adequacy criterion

`test_every_assertion_has_been_proved_able_to_fail` compares the assertions the contract declares
against the mutations registered for them and names any that has never been shown to fail. **Adding
an A13 without a mutation turns the suite red.** `MEASURED`

That is a floor. It proves each assertion *can* fail; it does not prove the set of assertions
covers the failure space. Corpus breadth (§10.1) is what addresses coverage, and the two are not
substitutes.

### 10.4 The corpus is data, and it lives where the agent cannot write

Hash-pinning is tamper-**evidence**. The trust boundary is the evaluator service owning the corpus
resolution (§7.1) — the agent cannot name a corpus, so it cannot point the grader at a kinder one.
The remaining exposure is anyone with write access to **both** the corpus and its manifest, and the
fix for that is credential separation, not a cleverer hash.
---

## 11. Session orchestration — the thing nobody set out to build

**Paul, 2026-08-22:** *"what we have built here is a session orchestrator… I want to flag this
because it could be efficient, but let's keep on track."*

He is right, and it is worth recording that nobody set out to build it. The readiness tracker began
as a page that re-measured 30 gates. Over one session it acquired lane definitions grouped by file
locality, a dependency order and a conflict map, per-lane model recommendations, a claim/release
lock, one git worktree and branch per lane, launch-into-terminal, a pre-answer channel for declared
blockers, a preflight, and generated per-lane and per-session handoffs.

⚠ **It is not on the gate list and nothing measures it.** By this programme's own standard it is
unproven infrastructure with a nice interface. Its parts have been individually exercised — claim
refusal, worktree lifecycle, handoff preflight, blocked launch — and before 2026-08-22 the
orchestrator as a whole had never run three lanes to completion. **Before it is trusted or
extended, it earns gates like everything else.** `MEASURED`

### 11.1 What is built, and what each piece is for

| Module | What it does | Honest state |
|---|---|---|
| `factory/lanes.py` | groups gates into parallel lanes **by file locality, not the dependency graph** | grouping is `ASSUMED` and says so in its own docstring; gate ids validated at import |
| `factory/board.py` | dependency order; `DEPENDS` is *the only authored knowledge* in the module | validated on import — a renamed gate breaks the build rather than dangling |
| `factory/claims.py` | claim/lease per lane, refuses overlap | `STALE_AFTER = 4h`, and it does **not** auto-expire |
| `factory/worktrees.py` | one git worktree + branch per lane | 3 lanes, 20 commits, **zero** cross-lane conflicts |
| `factory/sessions.py` | liveness against the **process table**, not the registry file | added after F73 |
| `factory/bus.py` | the live channel, one append-only file per writer, hook-delivered | machine-local by design |
| `factory/finish.py` | assert → push → announce → release; **never merge** | I5 |
| `factory/schedule.py` | velocity from the artifact's own git history | refuses an ETA, §14.2 |

### 11.2 The launcher was wrong in three ways and none of them failed

The clearest instance of [[vacuous-verification]] in the programme, because the work happened — it
was just not the work anyone asked for. `MEASURED`

1. **Every lane ran the wrong model.** `--model` was built into a variable nothing read
   (`inner = f"claude --model {lane.model} …"`, dead since the launch path moved to a `.ps1`). The
   banner printed the intended model, so `control-plane` announced opus and ran the session
   default, and `grain` announced haiku and ran something dearer. **A label, not a setting.**
2. **Transcript saving was off.** Lanes inherited `CLAUDE_CODE_CHILD_SESSION` from the session that
   started the tracker, so an hour's work would have been unresumable with no record. ⚠ `claude -p`
   **cannot test this** — print mode never suppresses, so the obvious test is non-discriminating.
3. **All three lanes had the same name** — they inherit the parent's session name, so a peer listing
   showed three identical rows and a question from one lane could only be answered by messaging all
   three and letting two ignore it.

**And a fourth, structural:** a restarted server serves the code it started with. The tracker was
launched **12 seconds before** the transcript fix was committed and served pre-fix code for hours.

### 11.3 A lock guards a resource, not a worker

`finish()` released a claim out from under a live session — idle, but alive. A relaunch then saw a
free lane and started a second agent in the same worktree. For a period on 2026-08-22 there were
**three control-plane sessions and two artifact sessions sharing one worktree and one branch each**
— the shared-checkout arrangement the entire lane model exists to avoid, recreated from the inside
by the tool written to close lanes safely. Nothing collided, because two of the three were idle.
**That was luck, not a control.** `MEASURED`

The rule, which is worth more than the fix: **anything that releases a lock must first establish
that the thing holding it has actually stopped.** Liveness is now read from the process table, and
*"could not read the process table"* returns a distinct `unverified` verdict rather than collapsing
into "nothing is running" — a guard that cannot see must not silently pass. (That is I1 again, at
the level of a lock.)

### 11.4 A path whose only diagnostic is stdout has no diagnostic at all

The research-answer upload path *worked*, and read as broken from outside: the tracker normally
runs `-WindowStyle Hidden`, and the only diagnostic on the path was a `print()`. A refusal — a
mismatched stem, an empty body, a file already filed — produced no file, no visible message and no
record, so **the failure and the absence of the feature looked identical**, and the honest report
from outside was "it does not persist". Every attempt is now appended to `.data/answer-log.jsonl`
with the exact refusal message before the redirect. `MEASURED`

**Generalises to every control in this spec:** anything that can refuse must record the refusal
somewhere the operator can reach it. An invisible refusal is indistinguishable from a broken
feature, and it means gate `refuses` can never see it either.

### 11.5 The ceiling of 3 is a file limit, not a concurrency limit

The 3-lane cap is the **max independent set of the conflict graph** in `lanes.py` — two lanes would
edit `orchestrator/pipelines.py` and simply conflict. `DERIVED`. Corroborating evidence: a study of
~33,000 agent-generated GitHub PRs found *same-agent* PRs in flight conflicted **19.8%** of the
time and *different-agent* PRs **41.7%**, and most conflicts were **structural** — one agent
deleting a file another edited — not line-level. `REPORTED`

⭐ **That is a property of code work.** The claim §5 is built on is that **data work does not
conflict that way**: two agents building two views in two schemas share no file and no row. The
claim is `BET` until §5 settles it — and §16 keeps it on the list of things most likely wrong.
---

## 12. The readout — two modes, one state

The brief called a Platform UI *"extremely important"*. It is, and it is also the surface where
this estate's signature defect is cheapest to commit: a published figure that reads green while
measuring nothing. Five defects shipped to the published artifact this month with a human finding
every one, including **a figure that declared a category it never drew** — the caption said 115
attempts, the legend carried an amber *"5 started, no outcome recorded"*, and 110 bars painted,
none amber. The dropped category was the **unmeasured** one, in a figure arguing that unmeasured
outcomes get dropped. `MEASURED`

### 12.1 The rule the skin must not break

```
Mode:  ├── Instrument      the default, never removed
       └── GTA             presentation only
```

Switching modes changes presentation, terminology, animation, sound, narrator and character. It
**never** changes state, counts, verdicts, measurements, agent results, gate results, epistemic
labels, readiness or workflow execution. That is invariant **I10**, and it needs a test, not a
promise: a mode-parity test asserting the two renderers derive from one measurement call.

The architecture that makes it enforceable is a one-way adapter:

```
Canonical Factory Event → Narration Adapter → Script Generator → Voice → Audio + subtitle + animation
```

Nothing downstream of the adapter may write back. `factory/crew.py` is the presentation layer and
it is **keyed by lane id** — ids never change, because branches are `lane/<id>`, claims key on the
id, worktrees are named for it, and `findings.d` routes a correction by matching the id. Renaming
lanes would silently unroute every finding. `MEASURED`

### 12.2 Four surfaces, and the fourth goes stale silently

One measurement, four places it appears: the terminal command, the local server, the published
artifact, and the wiki. **The published artifact only changes when someone republishes it** — it
read `3 of 23` while the repo was at `9 of 30`. `scripts/build_tracker.py --check` detects the
drift and `tests/test_tracker_is_current.py` fails the suite on it. Before that, the guard existed
and nobody ran it, which is the same shape as an eval nobody watches fail. `MEASURED`

⚠ **A long-running server holds the modules it imported.** `local_tracker.py --serve` re-measured
faithfully against a 23-gate list for hours. `importlib.reload` alone is not enough either —
`from x import y` binds by value, so the reload must **rebind** the names or it is a no-op that
looks like it worked. Restart after any change; confirm exactly one listener. `MEASURED`

### 12.3 The open question the skin has not answered

Whether a game-styled HUD makes an operator **more accurate and faster** at supervising N agents,
or slower and more confident — the worst combination, and the one that would kill the idea. That is
`R9`, written and **not dispatched**. Until it is answered, GTA mode ships behind a dropdown with
the instrument panel as the default, and no operational decision may depend on it. `BET`
---

## 13. Teams — one, and a catalogue that stays a catalogue

The brief listed eleven team types (Zeus Chat, Snowflake, Zeus Foundry, Monitoring/Alerting, API,
Model Selection, Optimization, Triage, Defect Resolution, Client, R&D). The spec ships **one**:

> **`connector-e2e`** — migrate one data connector end to end, source → container → Prefect →
> Snowflake, and be certified against A1–A12 for that connector.

The catalogue survives as a **registry of unlock conditions**, not a backlog. `REPORTED` — the
research position is that a specialist is justified only when enough tasks show it beats the
generic worker, and that ten team types before one certified team is the same error as ten agents
before one measurable one.

| Proposed team | Unlock condition — measured, not argued |
|---|---|
| Snowflake / warehouse | `connector-e2e` certified on ≥3 connectors, and a warehouse task class that the connector worker measurably underperforms on |
| Defect Resolution | a defect corpus with ≥29 cases in its stratum (§10), otherwise it is the retired triage agent again |
| Triage | evidence that static routing misroutes ≥10% over ≥200 adjudicated examples |
| Monitoring / Alerting | cost telemetry exists at all (§8.5) — today nothing records tokens or wall clock |
| Model Selection | the version hash covers model routing (§7.3), otherwise "which model" is not a recordable fact |
| Optimization / AgnosticOptimizer | build-order step 9 — everything in §14 Phases 1–3 done first |
| R&D | the research loop already runs by hand (`docs/research/`); a team is warranted when synthesis is the bottleneck, and it is not |
| Client teams (GEP, Fusion92) | a certified generic team plus a client-specific assertion the generic contract cannot express |
| Zeus Chat / Zeus Foundry / API | out of scope for the factory until one team is certified; these are products, not teams |

### 13.1 The optimiser, and why it is last

Four independent research passes reached one verdict without three of them being asked:

| | In its own words |
|---|---|
| R1 eval harness | *"The weakest parts are not primarily LLM-eval sophistication. They are control-plane problems."* |
| R2 topology | *"Control-plane changes are more urgent than agent architecture."* |
| R3 control plane | *"This system should not be optimised yet. It should first be made bounded, reapable, fail-closed and independently evaluable."* |
| R4 agnostic ×2 | *"Feasible as infrastructure, premature as an optimisation target."* |

**The mechanism they all name:** an optimiser cannot distinguish a better agent from a
configuration that happened to encounter fewer infrastructure failures. `REPORTED` — work
strengthening SWE-bench found **77% of its 500 Verified instances** had at least one semantically
altered variant that survived the original tests, and a separate analysis rejected **19.78% of
11,041 supposedly-solved patches** once tests were strengthened. Optimise against an
under-constrained oracle and apparent performance rises while correctness does not.

⚠ **Offline replay does not make configuration search cheap** — a correction to a claim made
earlier in this programme. Replay scores *the evaluator*, not an unrun candidate configuration.
The real cost stands: **20 configs × 3 replicates ≈ 1,584 agent-hours ≈ 16.5 days** at four-way
parallelism, and there is no honest dollar figure until failed attempts record cost. `DERIVED`

**When search does start**, screen in this order — model (`REPORTED`: published 9–13pp differences
between backends), reasoning effort, tool interface, context layout, system-prompt structure, and
prompt micro-wording **last**. *Do not spend live 11-hour evaluations searching commas.*

**Never optimised, at any phase:** retry caps, gate thresholds, tenancy checks, timeout and
concurrency limits, evaluator thresholds, the corpus. These are safety specification. Optimising
eventual success simply rewards more retries; optimising on the candidate's own score changes the
ruler rather than the system.
---

## 14. Build order — five phases, and the gates are the exit criteria

The 30 readiness gates are not a progress bar. **They are the acceptance test for each phase**, and
that is why the phase boundaries are stated as gate ids rather than as dates. `python -m
factory.readiness` scores the whole thing from files at run time and names the path each verdict
came from.

Two research passes and one prerequisite chain agree on the order; it is reproduced here with the
sandbox and specification work slotted in.

```
PHASE 0  run the loop once, for real                       ← nothing precedes a single real run
PHASE 1  bound it            (build order 1–2)
PHASE 2  make it able to tell success from failure  (3–4)
PHASE 3  certify it          (5–8)
PHASE 4  ── only here ──     configuration experiments (9)
```

### Phase 0 — a real run, and a cost number

Two gates read `UNMEASURABLE` because **nothing has run since the control primitives landed**, and
one reads its numbers off an audit log that stopped on **2026-05-28**. "3 of 14 runs finished" is
true of a history three months old, and until 2026-08-22 the gates did not say so. `MEASURED`

| Work | Why first |
|---|---|
| Run one connector migration end to end with the new primitives | No architecture decision should precede a single real run |
| **Instrument cost** — tokens + wall clock on the `finished` bus event | Every claim about a cheap lane is currently reasoning. Cheapest possible measurement, and gate `ceiling` depends on gate `cost` |

**Exit:** `finishes` and `cost` are measurable — not necessarily PASS, but not `UNMEASURABLE`.
**Must not happen:** a windowed gate reading PASS on an empty window. An empty window is
`UNMEASURABLE`, never a pass; *"no runs since the controls landed"* is the honest answer and must
not read as *"the controls work"*.

### Phase 1 — bound it

`cap` · `ceiling` · `concurrency` · `reaper`. These are changes to [[prefect-connectors]], and they
are **the first team's work, not hand work** — that is the point of a factory. The reason to fix
them first is that a team cannot be certified until the loop it runs in can tell success from
failure.

Concrete numbers, supplied by the build-velocity pass: `--memory 512m --cpus 1.0 --security-opt
no-new-privileges`, read-only filesystem except the work directory, no network by default, circuit
break after 3–5 consecutive failures or T minutes, and a human approval step before any container
launch. `REPORTED`

**Exit:** all four PASS, **and each has been watched refusing something** (I9).

### Phase 2 — make it able to tell success from failure

`from-history` · `checks` · `refuses` · `truthful` · `honest` · `attributable` · `general`.

⛔ The live defect this phase exists to kill: a **last-write-wins per-stage status field used as
evidence about a history**. A stage that failed 100 times and succeeded on the 101st reads
`completed`, so `any_failed` is False. It is not a Prefect behaviour — `orchestrator/pipelines.py`
does not import Prefect — and an earlier diagnosis that said it was got carried into a second
research question before anyone walked the route. `MEASURED`

**Exit:** `truthful` PASS, and a negative control exists that makes a false `succeeded`
*constructible* and shows the verdict refusing it.

### Phase 3 — certify it

`isolated` · `certified` · `tenancy` · `version` · `breadth` · `corpus` · `suite` · `durable`, plus
the sandbox ladder (§5) and the credential broker (§6).

**Exit:** one connector certified against A1–A12 by a service the agent cannot impersonate, scored
against a corpus with real strata, under an AgentSpec whose hash covers the dimensions §7.3 says
are hashable.

### Phase 4 — configuration experiments

Only here. §13.1 says why, and what to screen in what order.

### 14.1 Two gates cannot pass as written, and that is a defect in the instrument

- **`finishes`** requires `len(finished) == len(runs)` all-time. Four runs sit at `stage_started`
  forever and every new run raises both sides, so a perfect agent still reads FAIL. The reaper only
  helps if it **backfills terminal events for those four**.
- **`succeeds`** is an all-time ratio needing **837 net successful stages**, permanently carrying
  one capped 2026-08-14 incident. It answers *"has this ever been reliable"* while being read as
  *"is it reliable now"*.

Both are now windowed from `MEASURED_SINCE = 2026-08-22`, the date the control primitives landed.
**Windowing is not forgiving:** an empty window is `UNMEASURABLE`, excluded runs are named in the
evidence, and the audits are never deleted because the `bounded` gate cites them.

> ⭐ **A gate that cannot pass is the mirror of a gate that cannot refuse.** It stops measuring the
> work and starts reporting failure at work already done. Both are instruments that have quietly
> detached from the thing they name.

### 14.2 Velocity — and why there is no completion date

`factory/schedule.py` reads velocity out of the artifact's own git history: every commit carries a
generated `n of N gates pass` headline and a date, so progress is already an append-only log.

**It refuses to give a completion date, and names its criterion.** Over 6.4 hours, gates passed
went 1 → 9 (1.25/h) while the gate *set* went 13 → 30 (2.65/h). **Remaining grew 12 → 21.** More
work is being discovered than completed — the correct shape while a system is still being measured
— but an ETA divided by a moving denominator flatters. It will project once the total holds still
for 24h. "Ahead or behind" reports `NOT-SET`, because no target was ever stated. `MEASURED`

⚠ **The board's number has no basis without a cwd.** It reads 9 from the main checkout and 10 from
a lane worktree **at the same commit**, because `CONNECTORS` resolves relative to the checkout and
a worktree sees an unmerged lane branch. Neither run is wrong. **State the cwd with any
before/after claim.** `MEASURED`
---

## 15. Deliberately not built — and exactly what unlocks each

Every row is cheap to add after its precondition and expensive to unwind before it. The unlock
column is the point: a deferral without a stated trigger is procrastination, and a deferral with
one is a design.

| Not built | Unlocks when |
|---|---|
| Separate architect LLM | a same-budget A/B shows ≥10pp terminal-success gain **or** ≥20% efficiency, with no new seam failures |
| Mandatory tester LLM | a non-executable criterion exists where blinded LLM judgement demonstrably improves agreement with experts |
| `agent ↔ agent` messaging | production-like tasks with genuine concurrent branches show ≥5pp net gain **after** coordination cost |
| `manager ↔ manager` | several independently certified teams **plus** a measured inter-team bottleneck |
| `army → managers`, `army ↔ army` | ≥3 stable team types and evidence one manager is a real bottleneck. ⚠ **no production evidence was found for peer-army at all** |
| Dynamic team-selection LLM | ≥200 adjudicated examples **and** static misrouting ≥10% |
| Ten team types | §13 — a specialist beats the generic worker on a measured task class |
| Agentic gym | a stable verifier plus hundreds of clean labelled trajectories. *"Training on current traces risks learning pathological loops"* |
| AgnosticOptimizer | build-order step 9. Interfaces now (cheap), search later (§13.1) |
| Framework migration | fault injection showing an invariant the bespoke engine cannot satisfy and a candidate can |
| Supervisor tiers | never as LLMs before §4's schema is carrying real rows |
| In-page terminal | ⛔ declined three times. It is a PTY bridge plus a multiplexer to arrive somewhere worse than the Windows Terminal already installed |

⭐ **The one thing to build *early* that looks like it belongs here:** repo-agnostic **interfaces**
(contract, environment, evaluator) without the agnostic optimiser behind them. The research passes
disagreed on how agnostic and how soon, and the resolution is that they were answering different
questions — *interface shape* is cheap now and expensive to retrofit; *running a search* is not yet
safe. Adopt both positions. `REPORTED`
---

## 16. Where this is most likely wrong — attack these first

A design document that does not say where it expects to be wrong is a document nobody can check.
Ordered by *how much of the spec collapses if it is wrong*.

| # | The claim at risk | If it is wrong |
|---:|---|---|
| **1** | **T2 is cheap.** A clone is metadata; *validating* against one is compute, and a clone of a share may not behave like the real thing | §5.1 collapses, the ceiling stays at 3, and data work gets no more parallelism than code work |
| **2** | **"Data work does not conflict."** Asserted, not measured. Two agents building two views can conflict on a shared dimension, a naming convention, or the same `REPORT_COMMON` object | the conflict graph needs *different edges*, not fewer — and §11.5's ceiling generalises after all |
| **3** | **Four planes may be three.** PROVE and APPROVE do not separate cleanly when the evidence a human needs is produced by the thing being judged | §3.1's defence is the argument; if it fails, APPROVE is a rubber stamp with extra ceremony |
| **4** | **The blueprint is written by the graded party.** A target floor and an artefact hash narrow it; only an evaluator-pinned per-connector target closes it, and nobody has written one | §7 is a boundary against an *accidental* softening, not a determined one |
| **5** | **The lane model may be the wrong abstraction entirely** — worktree-on-one-machine as a dead end rather than a stepping stone | most of §5 survives (the ladder is about *what is touched*), most of §3's deployment story does not |
| **6** | **T1/T2 assume containers on Windows via WSL2**, unmeasured here, with start-up cost a guess | Phase 3 slips, and the ladder needs a different substrate |
| **7** | **The 15-dimension version hash may be unachievable.** Hashing something unstable makes every run a new version and the registry useless | certification becomes per-run rather than per-agent, which is a weaker but still honest claim |
| **8** | **Three attempts** is a policy default recorded as `ASSUMED`, and *"same failure"* for an LLM agent has no mature standard definition | the cap still bounds cost; it just may not bound the *right* thing |

### 16.1 Two risks that are not on that list because they are certainties

- **The published artifact will go stale again.** It is a separate surface that only changes when
  someone republishes it. The guard exists (`--check`, plus a test); the failure mode is nobody
  running it, which is why it is in the suite rather than in a runbook.
- **A gate will ship a false PASS.** One already did — the evaluator-isolation probe grepped
  `factory/*.py` for `EVALUATOR_URL` and matched **its own source**, because those strings were in
  the regex doing the searching. A self-matching probe producing a false green is the exact defect
  the programme exists to stop, reproduced inside the instrument. The mitigation is not vigilance;
  it is I3 and I9 — **every probe must have been watched refusing something.**
---

## 17. Open research — what is still unanswered, and why each matters

Nine research prompts exist. **Six have answers** (R1 eval harness, R2 topology, R3 control plane,
R4 agnostic optimiser ×2, R5 build velocity, R6 automation and alerting). **Three are written and
not dispatched.**

| # | Question | Blocks |
|---|---|---|
| **R7** | A session manager for agent teams: what to adopt, what to build | §11 — whether the accidental orchestrator should be replaced |
| **R8** | An agent factory for *data engineering*, not software engineering | §5, §9.4 — the isolation ladder and the downstream oracle |
| **R9** | Does a game-styled supervision UI make an operator more accurate, or slower and more confident? | §12.3 — whether GTA mode ships at all |

⚠ **R7, R8 and R9 answers do not exist anywhere on disk**, and for a while that was
indistinguishable from a broken upload path (§11.4). The path works; nothing was ever uploaded.

### 17.1 Three follow-ups, cheaper than re-running

None needs a new prompt — each carries its own thread's context.

1. **R3 thread** — the false-`succeeded` correction: our verdict is computed from a last-write-wins
   status field in a bespoke engine, **not Prefect**. What is the correct design for a terminal
   verdict computed from append-only history, and what negative control proves a false `succeeded`
   is impossible?
2. **R2 thread** — our build plane is not Prefect, so your prescription's retry limits, concurrency
   reservation and zombie handling are not available primitives. What must we build, what does it
   cost, and **does it change your recommendation — including whether to move the build plane onto
   Prefect rather than reimplement its primitives?** *(Gate `r2-followup`: the highest-value
   unasked question on the board.)*
3. **R1 thread** — one-liner: the `COMPLETED`-over-failures defect is not Prefect but a
   last-write-wins status field. Does anything else in your answer depend on that misattribution?

### 17.2 ⛔ A constraint asserted in a research prompt is a hypothesis like any other

`R6-automation-and-alerting.md` asserted, as a constraint, *"there is currently no runner budget or
appetite for one."* **That is false.** The same GitHub org runs three Actions workflows in
[[prefect-connectors]] (`ci.yml`, `quality-gate.yml`, `branch-sync.yml`); `agent-factory` merely has
no `.github/workflows` directory — **an absence, not a constraint.**

R6 explicitly deferred *"a full CI on every push"* on the strength of that sentence and ranked a
nightly scheduled gate-diff first instead. **So R6's ordering optimises against a world that was
described to it, not the one that exists**, and CI-on-push is very likely the correct first move.
Filed as finding **F7**, and it is the F1 pattern — an unverified premise carried into research —
committed by the author of a prompt whose own Method note warns against it. `MEASURED`

### 17.3 What the answered passes could not settle

Declared gaps are worth more than confident answers, so they are kept:

| Question | Gap |
|---|---|
| When to freeze a measurement-derived backlog | no studies found; inferred from agile theory |
| Drift across multiple generated surfaces | no direct analogue in the literature |
| Handoffs between agent sessions | little published; analogy to human handoffs |
| Alert thresholds for agent work | no AI-specific guidance on where to set them |
| **Multi-agent repo standards** | **no widely adopted standard exists** — blog posts and academic prototypes only |
| Recovering from a failed pre-close check | tooling is just emerging |

> The fifth row is the one to remember. **There is no consensus practice for what this programme is
> about to do**, so its own measurements are the best evidence available and should be recorded as
> they accumulate — which is what `docs/findings.d/` and the readiness gates are for.

### 17.4 Filenames are claims

Two research answers arrived with their contents swapped. `scripts/file_answers.py` classifies by
**content** and refuses when uncertain; it has twice been caught by its own dry run, once about to
overwrite a second run of a prompt. `MEASURED`
---

## 19. Operational gotchas — every one of these cost a session

Not trivia. Each is an instance of the same failure family: **a step that succeeded at doing
something other than what was asked, with nothing to say so.** They belong in the spec because the
spec's own controls are built out of these primitives. `MEASURED`, all of them.

| Gotcha | Why it is the same defect |
|---|---|
| **`pytest` addopts is already `-q`.** Passing `-q` again makes `-qq`, which suppresses the summary line | a probe parsing that line was blinded by a config it had not read |
| **`setx VAR "value"` from bash stores the quote characters too** | it broke `$AGENT_FACTORY_EVALUATOR` while the gate still read PASS, because the gate only checks the variable is non-empty. Use `[Environment]::SetEnvironmentVariable(…,'User')` and **read the value back** — *"SUCCESS: Specified value was saved"* is not evidence of **what** was saved |
| **`git checkout <path>` is a silent no-op on an untracked file** | back up before mutating a new file, or the revert does nothing and the mutant ships |
| **A long-running Python server holds the modules it imported** | `local_tracker.py --serve` re-measured faithfully against a 23-gate list for hours. `importlib.reload` alone is not enough either — `from x import y` binds by value, so the reload must **rebind** the names |
| **A restarted server serves the code it started with** | the tracker was launched 12 seconds *before* the transcript fix was committed. Restart after any change; confirm exactly one listener |
| **`getBoundingClientRect()` on a WRAPPED inline element returns the union of its line boxes** | it overlaps whatever precedes it on the first line. Compare `getClientRects()` per line box |
| **`claude -p` cannot test transcript suppression** | print mode never suppresses, so the obvious test is non-discriminating. The gate is `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` in the shipped binary |
| **`~/.claude/skills/` is not worktree-isolated** | an edit there is live for every session immediately and will not roll back with the branch |
| **`impeccable`'s detector silently degrades to 1 finding instead of 313** without four npm packages | now pinned, and recorded with the other machine-local state |
| **A closed lane holds its claim for 4 hours with nothing to reap it** | which is the `reaper` gate the same lane is building |
| **The board reads 9 from the main checkout and 10 from a lane worktree at the same commit** | `CONNECTORS` resolves relative to the checkout. Neither is wrong. **State the cwd with any before/after claim** |

### 19.1 Rendering the readout — six refusals, then a different route

`claude-in-chrome` refused for the sixth session running, so the published figure had shipped five
defects with a human finding every one. Every inspectable link is healthy — extension installed and
enabled, service worker alive, account matches, native messaging host registered with the right
extension id and spawnable, no enterprise policy — and `list_connected_browsers` still returns
`[]`. The failure sits in the extension's own service-worker pairing state, the one place not
inspectable from outside.

**The fix was to stop waiting.** `scripts/render_pass.py` drives the *installed* Chrome through
Playwright — no extension, no account, no pairing. First run found four real defects, including the
figure that declared a category it never drew (§12), a page that scrolled sideways at 700px because
a `max-width` override dropped `minmax(0,1fr)` to a bare `1fr` (which is `minmax(auto,1fr)`), two
`<text>` elements clipped by their viewBox under `overflow:hidden` — one by 373px — and a subtitle
reading *"Thirteen gates"* while the generator emitted 30.

> **A static check proves the file parses, not that a visual painted.** That is gate `rendered`,
> and it is the same rule as §9.4's *a query-layer check is not a render check*, one layer up.
