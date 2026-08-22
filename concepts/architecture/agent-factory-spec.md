---
tags: [architecture, spec, agent-factory, evaluation, greencontract, sandbox, control-plane, research]
aliases: [Agent Factory Spec, Agent Factory v1, Zeus Pantheon Suite spec, isolation ladder, AgentSpec]
sources: [github.com/ALDC-io/agent-factory@feat/readiness-generator, agent-factory/docs/specs/architecture-v0.md, agent-factory/docs/research/SYNTHESIS.md, agent-factory/BRAIN-DUMP.md, agent-factory/factory/readiness.py, agent-factory/factory/connector_contract.py, sources/agent-factory-design-research-2026-08-22/]
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

It is backed by **five deep-research passes run on 2026-08-22** (§18), which settled five of the
strawman's eight open risks — **two of them against the design** — and found four more.

**Contents** — §1 purpose · §2 invariants · §3 the four planes · §4 object model · §5 the isolation
ladder · §6 capability and credentials · §7 certification and the AgentSpec · §8 the control plane ·
§9 the contract · §10 the corpus · §11 session orchestration · §12 the readout · §13 teams ·
§14 build order · §15 deliberately not built · §16 where this is most likely wrong · §17 open
research · §18 what the research settled · §19 operational gotchas

**This page is the spine.** Two sections are long enough to live on their own pages, with
continuous section numbering: **§5–§6** on [[agent-factory-isolation-ladder]] and **§7, §9–§10** on
[[agent-factory-certification]]. Each appears here as a summary.

> ⚠ **Read §18.2 before quoting a vendor fact from this document.** The research ran behind a
> domain-allowlisting egress proxy that blocked most vendor documentation, so claims tiered
> `DOCUMENTED*` were reached through a search index and **not read in context**. §18.3 is the
> re-verification list.
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

> **Full text: [[agent-factory-isolation-ladder|Agent Factory — the Isolation Ladder and the
> Credential Boundary]].** Split out at four hundred lines; section numbering there is continuous
> with this page.

**The load-bearing idea in this spec.** It survived the research pass. Its *headline consequence*
did not.

> An agent's isolation tier is chosen by **what its task touches**, declared in the AgentSpec,
> **admitted** by the DECIDE plane and **constructed** by the launcher.

| Tier | Environment | May touch |
|---|---|---|
| **T0** | worktree + sandbox runtime, `allowedDomains: []` | repo files only. No egress, no DB verbs |
| **T1** | sandbox + allowlisted egress + **read-only** warehouse role, credential held by a broker | repo + `SELECT` on real data |
| **T2** | as T1, plus an **ephemeral clone *database*** and a role whose DDL grants stop at the clone | repo + full DDL/DML **inside the clone only** |

⭐ *Compute isolation and credential blast radius are different problems.* A perfect microVM holding
the operator's Snowflake password has the blast radius of the whole warehouse — which is why §6 is
not an appendix to §5, it is the more important half.

**The five findings that matter here, each argued on the sibling page:**

1. ⭐ **"Clone schema" must be "clone database"** (§5.5) — ALDC's warehouse DDL is schema-qualified
   and database-*un*qualified, so a schema clone leaves the sandbox a **no-op that reads as
   isolation**.
2. ⛔ **T2 does not raise the concurrency ceiling** (§5.7). Seven conflict edges survive it, and the
   replacement ceiling is a **compute** cap: `min(file-conflict independent set, warehouse
   concurrency budget)` ≈ 2–3.
3. ✅ **Containers on Windows are not required** (§5.3) — a kernel-level egress fence keyed on a
   separate account SID exists, with no WSL2 and no container. An open risk, struck.
4. ⚠ **An egress allowlist is not a confidentiality boundary** (§5.2) — the vendor says so, by name:
   domain fronting.
5. ⛔ **Teardown must be a Snowflake task keyed on ownership, and it precedes the first clone**
   (§5.9). The estate already has three orphaned sandbox schemas, **two of them now read by a
   production model.**

**And the gate trap:** `refuses` counts any all-time event containing "reject", so satisfying it
with boot-time drills would build **a gate that certifies itself**. Two counters, not one — §5.12.

**What is built today: nothing.** Agents run as the operator, with the operator's credentials.
---

## 6. Capability and credentials — the plane the generic sandbox literature does not address

> **Full text: [[agent-factory-isolation-ladder|the sibling page, §6]].**

**Credentials are the whole job.** A data agent needs warehouse, API and vault access by definition,
so every sandbox story that assumes *"no network, no secrets"* answers a different question. The
tier ladder is only a control if the credential attached to each tier is a **different principal
with different grants**.

⭐ **The single highest-value change in the sandbox programme is not T1's container — it is that the
agent holds no credential at all**, and a broker outside the sandbox holds it and injects it on
egress. Three products converged on that shape and two can be quoted directly; **it is configuration
before it is code.**

Three rules, and the third is where the design gets teeth:

1. **The operator's credential is never the agent's credential.** Today it is. `MEASURED`
2. **Per-secret grant stays human** (I6) — and with masking the human approves a **host**, not a
   secret handover.
3. **A grant is scoped and expires.** ⛔ Snowflake's floors are real: a role-restricted PAT's
   **minimum lifetime is one day**; sub-hour needs key-pair JWT (60 min), OAuth (600 s) or a
   per-lease dynamic user (1 h).

⛔ **And one default makes "T1 = read-only warehouse role" false as written:** behaviour bundle
2024_08 changed `DEFAULT_SECONDARY_ROLES` to `ALL`, so the effective privilege is the **union** of
everything the agent's user holds. Set it to `()` *and* use a role-restricted PAT.

⭐ **The broker's refusal log is the point, not a side effect** — it is where gate `refuses` finally
gets an *organic* refusal to count, against the standing **0 of 22**.
---

## 7. Certification — the grader is a separate principal, and the agent is a versioned artefact

> **Full text: [[agent-factory-certification|Agent Factory — Certification, the Contract and the
> Corpus]].**

**The submission vocabulary is the whole design:** the agent supplies `{artifact_uri,
artifact_sha256, run_id}` and nothing else, and the service refuses a body carrying a fourth field
rather than silently filtering it. Four attacks were **watched being refused**, then mutation-tested
— three mutants introduced, three caught. `MEASURED`

**What the research changed:**

- ⭐ **The standard already names the missing field.** SLSA Build L3 requires that signing material
  *"MUST NOT be accessible to the environment running the user-defined build steps"* and that
  *"every field in the provenance MUST be generated or verified by the build platform in a trusted
  control plane."* A verdict here carries three of the four Verification Summary Attestation fields
  and is **missing exactly `policy`** — because the blueprint is simultaneously subject and policy.
  That conflation *is* the hole. The mitigation SLSA names is **two-party review**, plus
  alert-on-diff.
- ⛔ **The version hash covers 6 of 15, not 0** — and the `version` gate is grep-on-source, so **a
  comment naming the dimensions turns it green.** The same self-matching defect the evaluator gate
  already had fixed.
- ⛔ **Certification must expire by *time*, not by hash.** Current models have no dated snapshot id —
  the alias *is* the id — so a hash is stable across silently changed weights. On expiry a verdict
  becomes `NOT_RUN`, not FAIL.
- **Report `pass^k`, k=5, never `pass@1`.** τ-bench: 61% pass@1 → 25% pass^8.
- **A13, an identity assertion**, because A1–A12 are all behavioural and all satisfiable by a
  throwaway demo that inlines the tested state.

⛔ **Do not read the green `isolated` gate as "the agent cannot cheat."** The deployment is loopback
under one uid — rank 5, *"mostly theatre"*. The **design** is rank 1. The gap is a managed identity
the agent sandbox does not hold: **a deployment change, not a code change.**
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

### 8.7 Do not reimplement leases — Prefect already has the property `claims.py` lacks

`DOCUMENTED` — Prefect implements concurrency slots as **timed leases with client-side renewal and
server-side expiry** (default 5 minutes, minimum 1), explicitly *"to ensure that all concurrency
slots are eventually released to prevent concurrency-related deadlocks"*, with `strict=True` as a
fail-closed mode you can watch refuse. It has a documented first-class Windows story, and **this
estate already runs it.**

That is precisely the property `factory/claims.py` does not have: `STALE_AFTER = 4h` *labels* a
claim stale and keeps blocking on it.

⚠ **Keep the plane distinction explicit in whatever gets written: using Prefect as a lease server is
not running build stages as Prefect flows, and a Prefect `COMPLETED` is never a contract PASS.**
Conflating those is how the false-`succeeded` diagnosis went to the wrong plane in the first place.

**Temporal is the stronger engine on the merits** — persisted timers, heartbeat timeout,
start-to-close as the zombie fuse, an append-only Event History, a hard `maximum_attempts`, and
**Workflow-ID uniqueness that *is* a claim lock**. It costs a server, a worker deployment and a
Windows-via-WSL2 story for a one-person build. **Prefect now; Temporal on a named trigger:**

> Adopt Temporal when (a) the build plane needs durable timers across process restarts, **or**
> (b) more than one machine runs stages, **or** (c) attempt caps must be enforced somewhere the
> agent cannot edit.

⛔ **And adopting either does not fix the false `succeeded`.** A Temporal workflow that retried 100
times also closes `COMPLETED`. **The engine gives you the log; you still write the projection.**
That is the single most important sentence in this section, because it is the one that would
otherwise be used to justify a migration that solves nothing.

### 8.8 `verdict(history)` — a pure function, and the five negative controls

The canonical design is event sourcing with a projection: **the append-only log is the system of
record, and the verdict is a pure, replayable function of it.** The negative control is the same
recipe every workflow engine uses in its own CI, generalised:

> **Feed the verdict function recorded *and synthetic* histories, and fail the build if the answer
> is wrong.**

The histories that must be in that suite, and the fourth is the one that matters:

| | History | Required verdict |
|---|---|---|
| N1 | `[stage_failed ×100, stage_completed ×1]` | **FAIL** — this is the defect, stated as a fixture |
| N2 | `[stage_started]` with no terminal event, older than the reap horizon | `ORPHANED`, never `NOT_RUN` and never a pass |
| N3 | a terminal event with **no** matching start | `UNMEASURABLE` — the log is incoherent, and saying so is the point |
| N4 | **replay all 14 recorded orchestrator runs** — the run that reads `succeeded` over 115 failures must turn **FAIL** | the whole point |
| N5 | an empty window | `UNMEASURABLE`, never PASS (§14.1) |

⭐ **This is the highest-value single item in the whole build order**: it is the defect the
programme exists to catch, it needs no new dependency, it can be written today, and **it produces
the first gate event that is a genuine, organic refusal** — against the standing `0 of 22`.

### 8.9 A lease needs a fencing token, not a longer timeout

The three-sessions-in-one-worktree incident (§11.3) is the textbook failure: a lock released while
its holder was still alive. The textbook fix is not a longer `STALE_AFTER` — it is a **fencing
token**. `REPORTED`

- `claims.py` gains `lease_seconds`, `renew_at`, `epoch` (the fencing token) and a `CLAIM_EXPIRED`
  event. Keep the loud refusal message; **drop the four-hour block.**
- `finish()`'s checks must include *"the claim's epoch is still mine"* before releasing. Keep
  *"a failed push must NOT release the claim"* exactly as it is.
- Narrow the module's scope to **cross-lane file conflicts only** — same-lane isolation is now
  covered by the harness (§11.6).
---

## 9. The contract — twelve assertions, and the two that already caught the harness

> **Full text: [[agent-factory-certification|the sibling page, §9]].**

Twelve assertions (A1–A12) a connector migration must satisfy end to end, executable, parameterised
per connector from YAML. **The contract is code; what "green" means for one connector is data.**

**The two tests that carry the argument:** a run that reaches `COMPLETED` with nothing landed —
**A6 passes, A7 fails**, and that gap is the entire reason the contract exists; and rows a *prior*
run populated returning a healthy count and proving nothing about this one.

⭐ **The hole the calibration found that review did not:** a **partial extraction passed**, because
the completeness invariant was guarded on a blueprint field left empty, so the check silently did
not run. *An invariant that quietly does not run is an assertion that quietly stopped being made.*

⛔ **And the hole the research found, one level up: the "independent" instruments are not
independent.** A9's requested-scope, A10's per-key counts and A12's tenant list are all restatements
of the landing in the positive calibration case — **the check ran against its own reflection** — and
`Probes.source()` is a stub, so **A10 will report `UNMEASURABLE` on the first live run.**

**Where A13+ goes:** there is no single oracle, there is a **ladder of five** — structural,
internal-consistency, independent-instrument, **metamorphic**, **render** — and A1–A12 occupy three.
⭐ **Metamorphic relations need nothing external**: they manufacture the second observation by
re-running with a transformed request. Ten are specified on the sibling page; **MR8 is the only one
that proves the tenancy filter is doing work, and it requires T2.**

**Power BI stays out until Phase 3**, because *a query-layer check is not a render check* — a
repoint once passed DAX parity while every visual showed *"Error loading data"*.
---

## 10. The corpus — one case is a fixture, not a calibration

> **Full text: [[agent-factory-certification|the sibling page, §10]].**

The corpus is hash-pinned data, verified on load; every replayed verdict carries `scored_against` and
is labelled **REPLAYED, not a live measurement**. **It holds one case and zero strata**, and that is
the single largest gap in the programme.

A blind spot affecting 10% of a stratum needs **29 cases** for a 95% chance of being seen once; 5%
needs 59; 1% needs 299. Two distributions, never one: a **regression corpus** of every semantically
distinct historical failure — **not** frequency-weighted, because *"your observed distribution is
endogenous to a badly broken system"* — and a **challenge corpus** stratified across 15 named
mechanisms.

⛔ **But case count is the wrong stopping rule.** EvalPlus held the problems fixed, added ~80× more
test inputs, and scores fell **19.3–28.9%** — the corpus had been mis-ranking all along with the
same number of cases. **The adequacy criterion is negative-control kill rate per assertion,
stratified by mechanism.** Add mutations, not cases; replay is sub-second and cases are not.
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

### 11.6 ⭐ The vendor has already overtaken this — six of nine modules are re-implementations

**Worktree-on-one-machine is a stepping stone, and its successor is already shipped.** `DOCUMENTED`

| What `factory/` builds | What the harness now ships |
|---|---|
| `worktrees.py` | `--worktree` per session with **enforced** isolation — it blocks edits and Bash cwd into the main checkout, and *"you can't turn this check off"* |
| `claims.py` | `git worktree lock` while an agent runs, plus a **stale-lock sweep that releases a lock whose process has exited** — the exact property §11.3 was written to add |
| `sessions.py` | background sessions under a supervisor, with `agents --json` / `attach` / `stop` / `rm` |
| `bus.py` | cross-session messaging over per-session sockets, with an inbound policy of accept / hold / refuse |
| `lanes.py` (partly) | agent teams with a **file-locked shared task list** and a mailbox |
| cost telemetry (unbuilt) | `total_cost_usd`, `model_usage`, `max_budget_usd`, `--max-turns` |

⛔ **And all three launcher defects in §11.2 are artefacts of generating PowerShell instead of using
the supported surface.** A bare `claude` cannot honour a `--model` field. `--name` already does
collision handling. `CLAUDE_CODE_CHILD_SESSION` would never have been inherited if the tracker had
not spawned a shell. **The fix is not three fixes — it is deleting the launcher.**

⚠ **With one thing to check first:** every capability above carries a minimum version, and nobody has
run `claude --version` on the operator's machine against them. If it is older, the finding is
*"upgrade first"* rather than *"delete the launcher"*. That is §18.3.

**What `factory/` should keep**, because nothing ships it: the readiness gates, the GreenContract,
the evaluator service, the findings ledger, `verdict(history)` (§8.8), and the conflict graph.

### 11.7 > **Contradiction**: the 41.7% figure is the wrong number for this estate

Three docstrings — `lanes.py`, `worktrees.py`, `local_tracker.py` — and §11.5 above cite **41.7%** as
the cross-agent conflict rate justifying worktree isolation. `REPORTED`

**In the same study, only 0.5% of co-active PR pairs were cross-agent. The intra-agent rate is
19.8%** — and the estate's actual case is intra-agent, because *every lane is the same agent*.

**So the argument for worktrees is roughly half as strong as every docstring in the repo states it.**
Recorded as a contradiction rather than silently corrected, per the wiki's own rule — and the paper
should be read before the number is changed anywhere, because it is now load-bearing (§18.3).

The conclusion does not flip: 19.8% is still a bad bet on a shared branch, and worktree isolation is
still right. **What flips is the reason to build more of it**, and the corollary below.

### 11.8 Parallelism is not the bottleneck — measurement is

Independent corroboration arrives from an unexpected direction: the vendor's own guidance lands on
**the same team size** (*"start with 3–5 teammates"*; *"if you have 15 independent tasks, 3 teammates
is a good starting point"*) and **the same partitioning rule** (*"break the work so each teammate
owns a different set of files"*). `DOCUMENTED`

And the published improvement is not *more lanes* — it is **dependency-cohesion partitioning with
hub-file isolation: +14% pass rate, 2.1× speed-up.** `REPORTED` Applied here: **one lane owns
`orchestrator/pipelines.py`; the rest partition around it.** That is a change to `conflicts()`, not
a change to the lane count.

> ⭐ **Set against 9 of 30 gates, 1 corpus case and 0 of 22 refusals, a fourth lane is not what is
> missing.** The ceiling of 3 is not the constraint worth spending on.

### 11.9 What cloud sessions change — and what they cost

Moving sessions off the operator's machine **kills T0's rationale on Windows specifically**: the
Bash sandbox has no native-Windows support, so *"no egress"* is a **convention** there, while a
cloud VM enforces it and keeps git credentials **outside** the sandbox behind a proxy (§6.3). That
is the same broker pattern, already running.

The cost: the worktree demotes from an isolation unit to a **local review unit**, and the round trip
becomes **branch-mediated** — pulling a cloud session back locally requires a clean tree and a pushed
branch. That is a workflow change, not a blocker, and it is the same direction §5.4's cloud test
points: *if moving to cloud requires editing the AgentSpec, the tier was a deployment detail.*
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

### 14.3 The work the research pass added — placed, sized, and ordered

Fourteen items, each traceable to a section. **Ordered by effect on time-to-one-certifiable-run**,
not by phase tidiness — but nothing here reorders §14's phase boundaries.

| # | Change | Phase | Size |
|---:|---|---|---|
| 1 | **`factory/verdict.py` — a pure `verdict(history)` plus negative controls N1–N5** (§8.8). Highest-value single item in the programme: it is the defect the estate exists to catch, needs no new dependency, and produces the **first organic refusal** | 2 | days |
| 2 | **The first drill** — a two-sided boot assertion per tier (§5.12). Lands *before* the tier work, so the tier work has a way to be wrong | 1 | hours |
| 3 | **Split `refuses` into `refusals_organic` / `refusals_drilled`**, both required non-zero, FAIL on a **stale** drill (§5.12) | 1 | hours |
| 4 | **Fix `version` — construct a spec and assert each dimension reaches the digest** (§7.5). Same fix the evaluator gate already received | 3 | hours |
| 5 | **The credential broker** — the agent stops holding any credential (§6.5 steps 1–2). Configuration first, then ~200 lines. **This is the change that ends "agents run with the operator's credentials"** | 1–3 | days |
| 6 | **Delete the launcher; launch through the supported surface** (§11.6). Deletes the class of defect that produced all three silent failures. ⚠ Check `claude --version` first | 0 | hours |
| 7 | **`claims.py`: lease + fencing token, drop the 4-hour block**; back it with a server-side concurrency lease rather than writing one (§8.7, §8.9) | 1 | days |
| 8 | **Verdict gains `policy: {uri, digest}`**, resolved by the service from its own targets directory — the blueprint stops being the policy (§7.4) | 3 | days |
| 9 | **Two-party control on target change + alert-on-diff** (§7.4) | 3 | hours |
| 10 | **The Snowflake reaper task, keyed on ownership** (§5.9). ⛔ **No clone is created before it exists** | 3 | days |
| 11 | **T2 split into 10a reaper · 10b clone + scoped role (no container) · 10c container-hosted.** ⭐ The clone-and-role half is entirely server-side and can be **watched refusing something** before any sandbox runtime exists (§5.11) | 3 | weeks |
| 12 | **A13 identity assertion + a visible/held-out assertion split** (§7.4) | 3 | days |
| 13 | **MR1, MR4, MR7, MR8 in the promotion gate** (§9.8); the rest in a per-connector certification suite | 3 | weeks |
| 14 | **`pass^k`, k=5** replacing `pass@1` (§7.8) — ⚠ multiplies certification cost by k, so it lands **after** cost telemetry | 3 | days |

**Two orderings inside that table are not negotiable:**

- ⛔ **The reaper precedes the first clone.** The estate has three orphaned sandbox schemas and **two
  of them are now read by a production model.** A sandbox that outlives its ticket becomes
  load-bearing.
- ⛔ **Cost telemetry precedes `pass^k`,** because k replicates multiply a cost nothing currently
  records.

### 14.4 One more thing that costs nothing

Add to the worker's system prompt today: *"Please write a high quality, general purpose solution. If
the task is unreasonable or infeasible, or if any of the tests are incorrect, please tell me. Do not
hard code any test cases."* `REPORTED` — measured by the vendor as reducing exactly the failure class
§7.4 is about. **It is a mitigation, not a control**, and it must be labelled as one — but it is
free.
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

## 16. Where this is most likely wrong — with the research verdicts attached

A design document that does not say where it expects to be wrong is a document nobody can check.
The strawman named eight. **Five are now settled — two of them against the design — and four new
ones arrived.**

### 16.1 The strawman's eight, adjudicated

| # | The claim at risk | Verdict |
|---:|---|---|
| 1 | **T2 is cheap** | ✅ **Settled — true, and it was the wrong worry.** Clone creation is metadata-only and free of warehouse credits; storage is ~2% of estate spend. **The real correction was granularity**: schema→database (§5.5), or the sandbox is a no-op |
| 2 | **"Data work does not conflict"** | ⛔ **Refuted. Seven edges** (§5.7). T2 removes one and *defers* another — and deferring is worse, because both runs report green. The replacement ceiling is a **compute** cap, and T2 may not raise 3 at all |
| 3 | **Four planes may be three** | 🟡 **Still open.** No external evidence found either way. §3.1 carries the argument |
| 4 | **The blueprint is written by the graded party** | 🟢 **Mechanism settled, deployment open.** The missing field has a name — VSA's `policy` — and the mitigation is two-party review plus alert-on-diff (§7.4). Nothing is built |
| 5 | **The lane model may be the wrong abstraction** | ✅ **Settled: a stepping stone whose successor is already shipped** (§11.6). The ladder survives; the launcher does not |
| 6 | **T1/T2 assume containers on Windows via WSL2** | ✅ **Struck.** Neither WSL2 nor a container is required — a kernel-level egress fence keyed on a separate account SID exists (§5.3). Replaced by: *the runtime is alpha and unproven on this machine* |
| 7 | **The 15-dimension hash may be unachievable** | 🟡 **Partly true, and worse than feared.** 5 hashable, 2 by subsumption, **2 must be recorded** — and the model has no dated snapshot id at all, so **certification expires by time, not by hash** (§7.7) |
| 8 | **Three attempts is `ASSUMED`** | 🟡 **Unchanged.** Still a policy default; *"same failure"* still has no mature definition |

### 16.2 The four that the research found

| # | Risk | Why it is worse than the eight above |
|---:|---|---|
| **9** | ⛔ **The contract's independent instruments are not independent.** A9, A10 and A12's "external" inputs are restatements of the landing, and A10's probe is a stub that will report `UNMEASURABLE` on the first live run (§9.6) | Every claim of the form *"eleven assertions pass"* is weaker than it reads. This is §9.2's defect one level up: not *the check did not run* but *the check ran against its own reflection* |
| **10** | ⛔ **Two gates can be satisfied without measuring anything.** `refuses` counts any all-time event containing "reject", so **boot-time drills would let it certify itself**; `version` is grep-on-source, so **a comment naming the dimensions turns it green** (§5.12, §7.5) | Both are the self-matching-probe defect the programme already caught once — reproduced twice more, in the gates sitting next to the fixed one |
| **11** | ⚠ **The tenancy filter has never been proved to do anything.** A12 checks that landed rows are within scope; it cannot distinguish *"the filter worked"* from *"the vendor happened to return only our accounts"*. Only MR8 can — **and MR8 requires T2** (§9.8) | It makes T2 load-bearing for *correctness*, not throughput — a better argument than the one that just died in §5.7 |
| **12** | ⚠ **Roughly a third of the vendor claims behind §5, §8 and §9 are one tier weaker than they look**, because the research ran behind an egress proxy that blocked most vendor documentation. One pair came back **self-contradictory** (§18.2) | The re-verification list in §18.3 is not housekeeping. It is the difference between a spec grounded in primary sources and one grounded in a search index |

### 16.3 Two things that are not risks because they are certainties

- **The published artifact will go stale again.** It is a separate surface that only changes when
  someone republishes it. The guard exists; the failure mode is nobody running it, which is why it
  is in the suite rather than in a runbook.
- **A gate will ship a false PASS.** One already did — the evaluator-isolation probe grepped for
  `EVALUATOR_URL` and matched **its own source**, because those strings were in the regex doing the
  searching. **Risk 10 says two more are live right now.** The mitigation is not vigilance; it is I3
  and I9 — every probe must have been watched refusing something, and drilled refusals must be
  counted separately from organic ones.
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

## 18. What the deep-research pass settled — and what it is not safe to quote yet

Five passes ran on 2026-08-22 against the repo at `feat/readiness-generator`, each briefed with the
measured state and the mandatory evidence tiering, and each asked to prefer *"could not verify"* over
a confident guess.

| Pass | Brief | Headline verdict |
|---|---|---|
| **R-A** | Is the T2 ephemeral data sandbox real, cheap and safe? | **Cheap — but the granularity is wrong and the ceiling claim loses.** §5.5, §5.7 |
| **R-B** | How is a capability tier enforced when the agent needs real credentials? | **Containment is on the credential axis, not the kernel.** And containers on Windows are not required. §5.3, §6 |
| **R-C** | What must "certified" mean, and what is an agent as a versioned artefact? | **SLSA Build L3 is the target; the missing field is `policy`.** And the hash covers 6 of 15, not 0. §7 |
| **R-D** | What should run the sessions? Is worktree-on-one-machine a dead end? | **A stepping stone the vendor has already overtaken.** Six of nine `factory/` modules re-implement shipped features. §11 |
| **R-E** | What is the oracle for data work, and what makes a corpus adequate? | **There is no single oracle — there is a ladder of five, and A1–A12 occupy three.** §9 |

### 18.1 The four findings that changed the design, not just the wording

1. ⭐ **"Clone schema" must be "clone database"** (§5.5). ALDC's warehouse DDL is schema-qualified and
   database-*un*qualified, so a schema clone leaves the sandbox a **no-op that reads as isolation**.
2. ⛔ **"Data work does not conflict" is false — seven edges** (§5.7), and the ceiling that replaces
   the file cap is a *compute* cap. T2 may not raise 3 at all without buying compute.
3. ⛔ **The calibration corpus's three "independent" instruments are restatements of the landing**
   (§9.2). The positive case proves self-consistency and nothing else.
4. ⛔ **The `refuses` and `version` gates can both be satisfied without measuring anything** (§5.12,
   §7.5) — one by a deliberate drill, one by a comment. Both are the self-matching-probe defect the
   programme already caught once, in the two gates sitting next to it.

### 18.2 ⚠ An evidence-access caveat that belongs in the spec, not a footnote

**All five passes ran behind a domain-allowlisting egress proxy, and it blocked most vendor
documentation** — `docs.snowflake.com`, `learn.microsoft.com`, `docs.getdbt.com`, `arxiv.org`,
`slsa.dev`, `docs.temporal.io`, `docs.prefect.io`, `dl.acm.org` and others. What remained open was
GitHub raw content and a search index.

Consequences, and they are the reason this section exists:

- Vendor reference claims reached only through a search index are tiered **`DOCUMENTED*`** — *the
  page was not opened and the sentence not read in context.* **Roughly a third of the vendor claims
  behind §5, §8 and §9 are one tier weaker than they look.**
- **One pair already came back self-contradictory**: whether Snowflake object tagging requires
  Enterprise Edition. That is why §5.9 keys the reaper on **ownership**, which is
  edition-independent, rather than on tags.
- ⭐ **The failure mode was a silent research gap, not an error** — a blocked host returns nothing
  and the researcher moves on. This is exactly what §5.2 warns will happen to a T1 agent, observed
  in the very pass that documented it.

### 18.3 The re-verification list — read these before staking a decision on them

| Claim | Why it matters | What settles it |
|---|---|---|
| Snowflake clone/share/monitor wording | all of §5 | open `user-guide/object-clone`, `sql-reference/sql/create-clone`, `user-guide/resource-monitors`, `user-guide/data-share-consumers` from an unblocked machine |
| Is `PROD_DG1_GEP` an imported share DB? | decides whether GP-219 step 6 is executable at all | `CREATE TRANSIENT SCHEMA scratch.probe CLONE PROD_DG1_GEP.SELLERCLOUD_SQL;` — expect failure |
| Object tagging vs Snowflake Edition | only if the reaper keys on tags — it should not | `SHOW TAGS;` |
| The **19.8%** intra-agent conflict rate | it is now load-bearing for §11.5, and it replaces a number three docstrings currently cite | read the paper |
| SpecBench and "Building to the Test" | they carry A13 and the held-out split (§7.4) | 2026 preprints with no independent trace — open both |
| Snowflake password-deprecation milestones | two sources disagree (Nov 2025 vs Aug–Oct 2026) | `user-guide/security-mfa-rollout`. **If a deadline is live, this is a schedule input** |
| Does the installed Claude Code have the features in §11.6? | half of §11's recommendation depends on it | `claude --version` against the stated minimums |
| Switchboard, R7's central artefact | never examined | one `git clone` |
| WSL2 escape specifics | before anyone says "WSL2 is a VM so it is a boundary" | read the published escape work |

> **The estate's own standing rule applies to this entire section: an object named by a handoff is a
> hypothesis, not a finding.** These passes are handoffs.

### 18.4 The raw reports are kept, because this spec quotes conclusions and not evidence trails

`sources/agent-factory-design-research-2026-08-22/` holds all five reports verbatim plus the shared
brief they were given. Each carries its source URLs, the tier assigned to every claim, its own
blocked-host list, and its own account of what it could not settle. **When §18.3 says re-verify,
that is where the trail starts.**
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

---

## See Also

- [[agent-factory-isolation-ladder]] — §5–§6 in full: the tiers, the Snowflake clone sandbox, the credential broker
- [[agent-factory-certification]] — §7, §9–§10 in full: SLSA/VSA, the twelve assertions, metamorphic relations, the corpus
- [[agent-factory]] — the running project log
- [[orchestrator]] — what the gates found in the build plane
- [[prefect-connectors]] — where build-order steps 1–4 actually land
- [[vacuous-verification]] — the failure family this whole spec is organised around
