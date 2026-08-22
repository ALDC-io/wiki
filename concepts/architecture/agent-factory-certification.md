---
tags: [architecture, spec, agent-factory, evaluation, greencontract, attestation, slsa, metamorphic-testing, research]
aliases: [GreenContract v2, AgentSpec, evaluator as principal, metamorphic relations, eval corpus]
sources: [github.com/ALDC-io/agent-factory@feat/readiness-generator, agent-factory/factory/connector_contract.py, agent-factory/docs/evidence/evaluator-isolation-2026-08-22.md, agent-factory/docs/evidence/phase-a-windsorai.md, slsa.dev, sources/agent-factory-design-research-2026-08-22/RC-attestation-and-versioning.md, sources/agent-factory-design-research-2026-08-22/RE-data-oracle.md]
created: 2026-08-22
updated: 2026-08-22
---

# Agent Factory — Certification, the Contract and the Corpus

**§7, §9 and §10 of [[agent-factory-spec|Agent Factory — Design Spec v1]]**, split out because
together they are the *proving* half of the design: what a certification has to mean, what the
twelve assertions actually assert, and what would make the corpus able to detect a blind spot.
Section numbering is continuous with the parent spec.

The one-sentence version: **a certification is a statement by a party that is not the agent, about
an artefact identified by hash, against a contract the agent did not choose, recorded somewhere the
agent cannot rewrite** — and today the repo satisfies the first three in design and none in
deployment.

Every claim is tiered — `MEASURED` · `DOCUMENTED` · `DOCUMENTED*` · `REPORTED` · `REASONED` · `BET`.
⚠ See §18.2 on the parent page for what `DOCUMENTED*` costs you.

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

### 7.4 The standard already exists, and it names the missing field

Supply-chain attestation contains the answer, and the level that maps onto *"an agent cannot forge
its own PASS"* is **SLSA Build L3 — "Provenance is Unforgeable"**. Its two load-bearing clauses:
`DOCUMENTED`

> Signing material *"MUST NOT be accessible to the environment running the user-defined build
> steps"* — and — *"Every field in the provenance MUST be generated or verified by the build
> platform in a trusted control plane."*

Against that standard, this repo is at **L1 with an L2/L3 shape**: the service genuinely resolves
corpus, assertion set, tenants and identity from its own configuration, and it holds no signing
material, is not hosted, and runs as the same uid as the graded agent. L2's accuracy clause is the
standards body saying the same thing as *"mostly theatre"*: the platform must have some anti-tamper
control, *"however, there is no minimum bound on the strength."* `DOCUMENTED`

Useful corollary: **hermetic builds are explicitly NOT required for L3.** Reproducibility is not the
price of admission.

⭐ **The structurally valuable change is not cryptography — it is the SLSA Verification Summary
Attestation shape, which separates `subject` (the thing graded) from `policy: {uri, digest}` (the
rules, named and digested *by the verifier*).**

A verdict here already carries three of VSA's four fields — subject digest, verifier id and version
via the bundle hash, and input attestations via the corpus stamp. **It is missing exactly one:
`policy`.** And it is missing it because the blueprint is simultaneously the subject *and* the
policy. That conflation **is** the hole §7.2 names. SLSA has a threat entry for precisely this —
*"Tamper with recorded expectations"* — and exactly one mitigation: **two-party review of
expectation changes.** `DOCUMENTED`

**So the fix, concretely:**

- The submission stays three fields. **The verdict gains `policy: {uri, digest}`**, resolved by the
  service from its own targets directory keyed by `(connector, client, deployment)` — never from the
  submission.
- The submitted blueprint stops being the policy and becomes only *the declaration of which target
  to look up*. The target floor then degrades from a load-bearing control to a sanity check, which
  is where it belongs.
- **Two-party control on target change**, plus the nearly-free complement that catches the realistic
  attack: **the evaluator diffs the resolved target against the last one it used for that connector
  and refuses on any difference until a human acknowledges it.** Trust-on-first-use, alert-on-diff.
  It is only a control because the agent cannot merge — which `finish()` already guarantees (I5).

⚠ **Held-out tests are necessary and not sufficient.** `REPORTED` — the visible/held-out gap grows
~28pp per 10× code size and frontier agents saturate visible suites at 100%; and with an *honest,
hidden* oracle, agents still satisfied it by inlining tested state into a throwaway demo and leaving
the requested library dead. **A1–A12 are all behavioural and all satisfiable by that shape.** So the
contract needs an **identity assertion**:

> **A13 — the artefact the ticket asked for exists at the declared path, is the object the pipeline
> actually reads, and no substitute is standing in for it.**

Splitting the assertion set into a visible half (in the repo) and a held-out half (only in the
evaluator's configuration, never rendered into a failure message beyond its name) removes leakage
and memorisation. **It does not remove building-to-the-test**, and the spec must say so.

### 7.5 Verdict storage, and two corrections to the version gate

**Nothing written locally under one uid is a control.** Ranked by cost-effectiveness: `REPORTED`

| | Mechanism | What it buys |
|---:|---|---|
| 1 | **Hash chain** — `prev_sha256` on every verdict + a `HEAD` published out-of-band daily | hours. **Detection, not prevention** — and honest about it |
| 2 | **Object storage with Object-Lock compliance mode**, no agent-side write | a real control |
| 3 | **GitHub Actions + `actions/attest`** | free on public repos; ⚠ **a private repo needs GitHub Enterprise Cloud** — a purchasing decision, and it should be surfaced as one |

⛔ **Two corrections to what the repo currently believes about its own version hash.**

1. **It covers 6 of 15, not 0.** The oft-quoted "0 of 15" understates the position.
2. **The `version` gate is grep-on-source and can be turned green by a comment naming the
   dimensions.** That is the *same self-matching-probe defect* the evaluator-isolation gate already
   had fixed, sitting in the gate next to it. The fix is the same: construct a spec, call the
   sub-hash functions, and assert each named dimension **demonstrably reaches the computed digest**
   — change the value, the digest changes.

### 7.6 What can be hashed, what can only be recorded

Nothing in the prior art hashes a non-deterministic system's *behaviour*. Every workable scheme
hashes the **declared, resolvable inputs** and *records* everything else. The most instructive
analogue is dbt's `state:modified`, which decomposes into six named sub-checks, deliberately
**excludes** tags and metadata as *"metadata only"*, degrades to a *path* comparison for seeds too
large to hash, and ships a behaviour flag whose entire purpose is reducing false positives.
`DOCUMENTED`

| Dimension | Verdict |
|---|---|
| `contract_version`, `permissions`, `sandbox_image` (OCI digest), `harness_version`, `context_policy` (as declared *policy*) | **HASH** — cheap and stable |
| `tool_implementation` | **HASH BY SUBSUMPTION** — Bazel's answer, *"treat tools as source code"*: the image digest already covers CLI drift |
| `external_knowledge` | **HASH BY SUBSUMPTION** — a snapshot id, never live search |
| `model_routing`, `side_effect_replay` | ⛔ **RECORD, never hash** |

Three rules that follow, and they are why a hash over something unstable is worse than no hash:

- **Named sub-hashes plus a roll-up**, so a consumer can ask *"did the contract change?"* without
  *"did the harness patch bump?"* also firing.
- **An explicit `EXCLUDED` list with a reason string per entry**, printed by `--json`.
- **A degradation path**: where a dimension cannot be hashed (a host CLI on a non-containerised
  run), hash the *pointer* and **emit a warning** rather than silently omitting it. Silent omission
  is I1's collapse, one level down.

### 7.7 ⛔ Certification must expire by time, because the model cannot be hashed

The model dimension breaks the scheme, and worse than the repo assumed: `DOCUMENTED`

- **Current Anthropic models have no dated snapshot id — the alias *is* the id.** So
  `hash(model="claude-opus-5")` is stable across silently changed weights.
- `temperature` is not merely unreliable — it **returns HTTP 400** on the current model generation.

**Therefore a version hash cannot be a certification's expiry mechanism.** Certification is
**time-bounded and re-validated**:

- A verdict carries `timeVerified` and `valid_until`.
- **On expiry the verdict is `NOT_RUN`, not FAIL.** The four-verdict scheme already supports it, and
  it is the monotonic answer: nothing was measured, so nothing failed.
- Suggested initial window: **30 days, or until the provider's own capability tree changes**,
  whichever is sooner — hashing that tree as a change *detector*, never as an identity.
- Record the **served** model from the response, not the requested one.

### 7.8 Comparability — report `pass^k`, not `pass@1`

Determinism is a property of a serving stack this estate does not own: `REPORTED` — 1,000 runs at
temperature 0 produced **80 unique completions**. And the metric matters more than the count:
τ-bench reports **61% pass@1 collapsing to 25% pass^8**.

- Default **k = 5, all must pass**. Fewer than k replicates completed → `UNMEASURABLE`.
- **Record per-replicate verdicts** in the run record so variance is visible rather than averaged
  away.
- ⚠ This multiplies certification cost by k, so it **must land after cost telemetry** (§8.6).

### 7.9 One free mitigation, labelled as a mitigation

`REPORTED` — the vendor measured this line reducing the exact failure class this section is about,
at zero cost:

> *"Please write a high quality, general purpose solution. If the task is unreasonable or
> infeasible, or if any of the tests are incorrect, please tell me. Do not hard code any test
> cases."*

**It is a mitigation, not a control**, and the spec says so — but it is free, and it goes in today.
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

### 9.6 ⛔ The instruments are not independent — the calibration proves self-consistency and nothing else

`MEASURED` — read from `evals/corpus/windsorai-2026-08-20.json` and `factory/calibration.py`.

Three of the assertions the contract leans on hardest are, **in the positive calibration case,
restatements of the landing rather than observations of anything else**:

| Assertion | Its "independent" input | What the corpus actually supplies |
|---|---|---|
| **A9** completeness | what was *requested* | the requested-account list is **identical to the set of `account_id` values present in the landed rows** |
| **A10** source agreement | an independent per-key count | `{18, 2}` — sums to exactly the landed row count, and per-key to exactly the landed per-key count |
| **A12** tenancy scope | the declared tenant list | `calibration_target()` sets `allowed_tenants` from the corpus document's tenants — **the same two ids that appear in the landed rows** |

The repo is honest about *why* — *"so the world and the target cannot drift apart"* — and the
blueprint states the principle correctly. **The consequence stands anyway: the positive case proves
only that the assertions do not cry wolf against a self-consistent world.** The mutation cases prove
each *can* fail. Neither proves an assertion has an instrument that could **disagree with the
landing** on a live run.

⛔ **And `Probes.source()` raises `Unmeasurable`, so on the first live run A10 — the contract's only
claimed independent oracle — will report `UNMEASURABLE`, not PASS.**

> This is the same class of hole the calibration already caught once, one level up. Not *"the check
> silently did not run"* but ***"the check ran against its own reflection."*** §9.2 is the first
> instance; this is the second, and it was found by asking an outsider to read the corpus.

Two more, from the same read:

- **A8 checks count parity, not content parity.** *Emitted 20, landed 20, of which 10 duplicated and
  10 dropped* **passes**. It needs a row hash.
- **A9 cannot detect per-key page truncation** by construction — right keys, wrong counts. Only A10
  or a metamorphic relation can (§9.8, MR1).

### 9.7 There is no single oracle — there is a ladder of five, and the contract occupies three

| Rung | Class | What it can settle | Where A1–A12 sit |
|---:|---|---|---|
| 1 | **Structural** | does the thing exist, resolve, authenticate, pin | A1–A5 |
| 2 | **Internal consistency** | does the landing agree with itself and with what was emitted | A6–A9, A11 |
| 3 | **Independent instrument** | does a second observer agree | A10, A12 — **A10 is a stub** |
| 4 | ⭐ **Relational / metamorphic** | does the system agree with *itself under a transformed request* | **absent** |
| 5 | ⭐ **Render** | did the number a human will read actually paint | **absent** |

**Every one of the twelve assertions is a single-run, single-observation claim**, which means all
twelve can be satisfied simultaneously by a pipeline that is *consistently* wrong. The estate's own
history — a repoint that passed DAX parity while every visual showed *"Error loading data"* — is
exactly that shape.

The two missing rungs are cheap and available, and they are where A13+ goes.

### 9.8 Metamorphic relations — independence without a second source of truth

⭐ **The highest-value transferable idea in the research pass.** A metamorphic relation is a relation
between the outputs of *multiple* runs: *even if we do not know the correct output of a single
input, we might still know the relations between the outputs of multiple inputs.* `REPORTED`
(Chen et al., 1998; survey in ACM Computing Surveys 51(1), 2018.)

**Why it fits here exactly:** every one of A1–A12 needs *something outside the run* to compare
against — a source of truth, a declared scope, a pinned digest. Where that external thing does not
exist, the assertion is `UNMEASURABLE`, and several are. **Metamorphic relations need nothing
external. They manufacture the second observation by re-running with a transformed request.** For a
vendor API with no count endpoint, no sandbox and no second client, they are the *only* available
independent instrument.

Notation: `pull(S, W)` = the landing from a run requesting scope `S` over window `W`, restricted to
rows stamped with that run's session id.

| # | Relation | Detects |
|---|---|---|
| **MR1** | `pull({A,B,C},W)` ≡ `pull({A},W) ∪ pull({B},W) ∪ pull({C},W)` as a multiset | **truncation and tenancy leakage at once** — per-account pulls cannot share a paging cursor, so a whole-scope pull that silently stops after page N is a strict subset. *The check A9 structurally cannot make* |
| **MR2** | `Σ pull(S,[d1,d2])` = `Σ pull(S,[d1,dm])` + `Σ pull(S,[dm+1,d2])`, per key | off-by-one window boundaries, timezone-shifted date filters, double counting on the seam |
| **MR3** | for `W ⊆ W'`: `Σ pull(S,W) ≤ Σ pull(S,W')` and the (key,date) set is a subset | a filter applied *after* aggregation; a window parameter ignored |
| **MR4** | re-running the identical request under a **new session id** yields an identical row multiset on (PK, metrics) | vendor-side sampling, non-determinism, non-idempotent MERGE. **The metamorphic form of A8, and what makes "landed == emitted" mean something** |
| **MR5** | reordering the requested account or field list does not change landed content | cursor state carried across accounts |
| **MR6** | `rollup(campaign grain)` ≡ `pull(account grain)` for additive metrics — **and it must fail for ratio metrics** | hidden filters at one grain; dedup at the wrong level. *Discovering which metrics break it is how you learn which are non-additive* |
| **MR7** | an account with no data lands **exactly zero** rows, reports COMPLETED, and A7 classifies it as *legitimate-empty* distinguishably from *silent-empty* | **the shape this estate shipped twice** |
| **MR8** ⭐ | in a **T2 clone only**: `pull(no filter, W) ⊃ pull(S, W)`, and the difference consists **entirely** of tenants ∉ `allowed_tenants` | **the only relation that proves the tenancy filter is doing work** rather than the vendor happening to return only our accounts |
| **MR9** | where a unit option exists, `Σ pull(unit=micros)` = 10⁶ × `Σ pull(unit=units)` **exactly** | **unit drift** — the "spend is 1,000,000× too big" bug that passes every null, positivity and type check and is caught only when a human reads a dashboard |
| **MR10** | requesting a **subset** of fields returns the same PK set and the same values projected down | field-list-dependent server-side filtering; a join that fans out rows when a dimension is added |
| MR11 | re-pulling a window closed ≥ N days ago is identical, or differs within a **declared** restatement tolerance | vendors silently restating history. Needs elapsed time → belongs to the standing monitor, not the gate |

⭐ **MR8 is a better argument for T2 than parallelism ever was.** It cannot be run anywhere else: it
requires deliberately issuing an *unfiltered* pull, which is exactly the action that must never
touch a real table. **And it has a second payload — if the unfiltered pull returns exactly the
declared accounts, the vendor key is not what the blueprint claims and the entire A12 premise is
wrong.**

**Cost:** MR1 for six accounts is 7 runs, MR2 is 3, MR4 is 2, MR5 is 2. A full suite is **~15–20
connector runs against one date** — affordable once per connector migration, and clearly not
affordable per commit. So: **MR1, MR4, MR7, MR8 in the promotion gate; the rest in a certification
suite run once per connector and re-run when the connector changes.**

### 9.9 The render oracle exists, and it is buildable

`REPORTED` / `DOCUMENTED` — a published Power BI approach renders a report through a service
principal + embed token + a headless browser and matches **ten enumerated error strings**
(*"We are not able to identify the following fields"*, *"Couldn't retrieve the data for this
visual"*, …). It needs at least PPU capacity, and composite models are unsupported.

⚠ **That is an absence-of-error check, which violates this spec's own rule** (I2 — a probe must
assert what it means, not the absence of a symptom). The positive version is available: the embedded
client exposes a `visualRendered` event, so the assertion becomes **"the count of rendered visuals
equals the count declared in the report layout"**. Watch `hideErrors`.

Two things to record before anyone plans around it: `exportToFile` is Premium/Embedded/Fabric only —
**not PPU** — and it is **unverified whether a broken visual fails the export job or simply bakes
the error into the PNG.** And the documented mechanism behind the estate's own incident:
*"A renamed or removed column or table at the data source will be removed with a schema refresh, and
it can break visuals and DAX expressions."*

### 9.10 Completeness has a vocabulary, and its default is "off" everywhere

The techniques are older than data engineering: **control totals** from IT audit, packaged for
warehouses as **Audit–Balance–Control** — *Audit* is the per-step log of rows read/inserted/rejected,
*Balance* is *"the ability to explain the difference between source(s) and target(s) in each step"*,
*Control* is remediation. Plus **watermarks / high-water marks** for incremental boundaries,
**row-hash reconciliation** where there is no primary key, and **manifests with mandatory entries**
for declared input sets.

⭐ **The pattern to notice: `mandatory: true` in a load manifest is the same idea as `required_keys`
in the target — and the documented default is `false`. That is the same bug the calibration matrix
found.** *The default of a completeness guard is "off", everywhere.*

⛔ **Pagination has no completeness proof, and that is a finding, not a gap in the search.** For a
cursor-paginated vendor with no count endpoint there is **no canonical technique** — only
heuristics: page sizes match the request, records are non-overlapping and unique across pages, every
page returned 2xx, and the terminal condition was *actually reached* rather than the loop exiting on
an error or a max-pages guard. **So for such a connector, a completeness assertion must return
`UNMEASURABLE`, not PASS** — and MR1/MR2 are the only available substitute, because they detect
truncation without needing a total.

**Request-vs-result has no established name.** The nearest concepts are manifest-based load
verification, a reference check, and *Balance* in the ABC sense. **This spec names it a
declared-scope assertion:** the scope is an input to the run, recorded *before* the run, and the
landing is checked against it. The blueprint already states it better than any source found:
*"this list is the requested scope, not the observed landing. Reading it out of landed rows would
make completeness unfalsifiable."* That is I8.

### 9.11 The negative controls that are missing

Present today: A9 partial extraction, A10 off-by-one, A12 foreign row, A8 emitted≠landed. **Missing,
and each is a hole with a name:**

| Check | Missing negative control |
|---|---|
| A9 | requested-scope source **empty** → assert the verdict is `UNMEASURABLE`, not PASS |
| A9 | blueprint declares A,B,C; live config observes A,B → **the two disagree** → `UNMEASURABLE`. *This is the tenancy-staleness case the blueprint itself warns about* |
| A9 | all accounts present, one account truncated to page 1 → **A9 cannot catch it; only A10 or MR1 can** |
| A10 | the source probe returns **the landing's own counts** → must be detectable. *This is the live corpus's current state* (§9.6) |
| A12 | `allowed_tenants` **derived from the landing** must not be accepted as a declared scope. *`calibration_target()` does exactly this* |
| A12 | filter removed; the unfiltered pull returns 45 accounts of which 6 are ours → must fail. *This is MR8* |
| A8 | emitted 20, landed 20, **10 duplicated and 10 dropped** → needs a row hash |

### 9.12 Tooling — steal three things, ignore four

**Steal:** row-hash reconciliation (it removes the primary-key dependency currently blocking the
`windsorai` blueprint and §9.5's open question 1), Snowflake `HASH_AGG` + `MINUS` for whole-relation
fingerprints, and the output shape of a mature `table_diff`.

**Ignore for the gate:** Great Expectations, Soda, Elementary, Monte Carlo. **All of them need a
history to be anomalous against**, and `windsorai` landed its first row ever on 2026-08-20. They are
distributional monitors answering *"does this look like yesterday"* — which cannot see a first-ever
migration and cannot see request-vs-result at all. (Soda's reconciliation checks are paid-tier;
open-source `data-diff` was sunset in May 2024.)

**Contracts: adopt the Open Data Contract Standard as the serialisation of the blueprint, and reject
it as the definition of the GreenContract.** ODCS has no vocabulary for provenance tiering
(MEASURED/DERIVED/ASSUMED), for `UNMEASURABLE`, or for *which tenants were requested* — and those
three are the whole design. ⛔ **Never let a contract-tool PASS become a `Verdict.PASS`.**
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

### 10.5 ⛔ Case count is the wrong adequacy criterion

The 29/59/299 arithmetic in §10.1 is right about *breadth* and wrong as a **stopping rule**. The
adequacy criterion is not how many cases the corpus holds — it is **negative-control kill rate per
assertion, stratified by mechanism.**

The strongest external evidence: **EvalPlus held the problem set fixed, added ~80× more test inputs,
and top models' scores fell 19.3–28.9%.** `REPORTED` Same number of cases; the corpus had been
mis-ranking all along. **Add mutations, not cases** — and here replay is sub-second, so mutations
are nearly free while cases are not.

**The transferable rule from SWE-bench Verified is exclusion, not inclusion:** a case is dropped if
**any single annotator** flags it. A corpus built by consensus keeps the ambiguous cases; a corpus
built by veto does not.

Applied here, the corpus specification becomes:

```
11 strata · ~39 cases · every assertion carrying at least one mutation per stratum it claims to cover
report pass^k (k=5, all must pass), never pass@1        ← §7.8
adequacy = "which assertion killed which mutant", not "how many cases do we have"
```

⚠ **And the mutation registry must grow a second axis.** Today it asks *"has this assertion ever been
observed failing?"* (§10.3). With strata it must ask *"has this assertion been observed failing
**in each stratum it claims to cover**?"* An assertion proved able to fail on one mechanism and
never exercised on the other fourteen is a floor that has stopped rising.

### 10.6 The corpus's own defect, and why it is listed here as well as in §9.6

**The positive case's three "independent" inputs are restatements of the landing** (§9.6). That is a
*corpus* defect as much as a contract defect, and the fix belongs here: a corpus case must record
**where each observation came from**, and a case whose "independent" instrument shares a provenance
with the landing must be **labelled as such and excluded from any claim about agreement**.

> An assertion scored against its own reflection is `UNMEASURABLE` wearing a PASS.

---

## See Also

[[agent-factory-spec]] · [[agent-factory-isolation-ladder]] · [[agent-factory]] ·
[[vacuous-verification]] · [[answerability-guard]] · [[orchestrator]] · [[GEP]]
