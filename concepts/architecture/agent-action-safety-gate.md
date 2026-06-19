---
tags: [concept, architecture, agentic-ai, safety, generalization-platform]
aliases: [action envelope, risk_class x mode, uniform safety gate, ActionEnvelope, handler manifest, generalization platform core]
sources: [
  C:/Users/PaulRussell/repos/triage-agent/docs/architecture/overview.md,
  C:/Users/PaulRussell/repos/triage-agent/docs/project/decisions.md,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/routing/,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/safety.py,
]
created: 2026-06-12
updated: 2026-06-12
---

# Agent Action Safety Gate (typed action envelope + `risk_class × mode`)

How an ALDC agent expresses its **safety policy once, uniformly, across every action of every vertical** —
the reusable pattern behind the [[triage-agent]] generalization-platform core (decisions R19-R22), so a
single agent can grow new "verticals" (bug-triage, doc-answering, repro/fix) **without changing the
safety-critical code** each time. The principle: **the router emits a typed *action*, not a module; one
uniform gate decides disposition from `(risk_class, mode)`; and that gate is a fail-closed assertion layer
ABOVE the proven enforcer, never a rewrite of it.** First realised in [[triage-agent]] session 14
(increment 1: the typed envelope + the gate, with the two existing actions routed through it and proven
byte-equivalent on a live Claude call), then **session 15** (increment 2: the **route compiler** — the
implicit, scattered route decision lifted into one declarative rule table that emits the envelope, with
propose-becomes-a-handler the compiler dispatches to). Sits *around* the pipeline that
[[agent-observability-telemetry]] instruments — the telemetry is what makes this refactor *measurable*
(shadow-diff the before/after).

> **Why this exists.** Bug-triage is **vertical #1 of a general inbound-work platform, not the product
> definition.** Without a stable nucleus, every new capability re-touches the safety choke point — the most
> dangerous code to keep editing. The fix: make verticals *peers* behind a typed action space + one gate,
> so adding a vertical is configuration (a handler manifest entry + a route rule), not core surgery.

## The microkernel split (R19)

- **Stable nucleus** (changes rarely, reviewed hard): ontology/concept IDs · **action contracts** ·
  memory scopes · **safety policies**. Plus the canonical inbound model, grounding interfaces, the route
  compiler, observability, the learning ledger.
- **Replaceable edge** (changes per vertical, configuration-only): prompts, **handlers**, agent topologies.

The pipeline gains a `route` step: `classify (independent dimension predictions) → ground → ROUTE → act
→ learn`. Today's 4 predictions (client/intent/linkage/scope) ARE the dimensioned classifier; the route
step turns them into a typed action.

## The three pieces of the core

### 1. The typed `ActionEnvelope` (R20)

The router emits a typed action contract, not "a module": `action_type` (a fixed enum —
`route_record` / `apply_remediation` / `reproduce_issue` / `draft_answer` / `stage_access_change` /
`no_action`), a `risk_class`, a `mode` (the operation phase: **propose** vs **execute**), structured
`inputs`, the `required_evidence` refs, the `handler_id` that will implement it, and version stamps.
**Content by reference only** — inputs/evidence are labels/IDs/scalars (incident `resource_key`,
fingerprint name), never raw message bodies — so the envelope is safe to log and store in the
[[agent-observability-telemetry|audit row]] (same posture as "evidence by reference, not payload").

### 2. The handler manifest — verticals as peers; the gate's `risk_class` source (R21/R22)

A `HandlerManifest` declares a capability module: `id` (e.g. `propose.triage.v1`), an **immutable
`concept_id`**, its `action_type`, its `risk_class`, and a three-state **lifecycle**
(`declared → servable → experimental`). The load-bearing job: **the gate reads `risk_class` from the
manifest, never a hardcode** — so the policy code contains no per-action danger logic, and adding a
vertical is a manifest entry (data). An unknown handler **fails closed to `privileged_write`**. Bug-triage
is expressed as peer handlers (`propose.triage.v1` = internal_write, `apply.jira.v1` = external_write); a
`declared`-not-`servable` peer (`repro.connector_bug.v1` = privileged_write) proves the core is agnostic —
adding it changed no core file. (The richer manifest fields — IO schemas, resources/tools/skills,
per-step model+params, `evaluation_contract` — and the full lifecycle machinery are the next increment;
the `concept_id` + lifecycle give the [[triage-agent]] `operational_scope` taxonomy backlog its home.)

### 3. The uniform `risk_class × mode` guard matrix (R22)

One policy table, evaluated for every action of every vertical. The two axes:

- **`risk_class`** (intrinsic danger, declared by the manifest): `read` < `internal_write` <
  `external_write` < `privileged_write`.
- **`mode`** (operation phase): `propose` (draft / route a would-be effect to a human) vs `execute`
  (actually commit it). This second axis is what gives `internal_write` its two cells.

| `risk_class` ↓  /  `mode` → | `propose` | `execute` |
|---|---|---|
| `read` | auto-allow | auto-allow |
| `internal_write` | **auto-draft** | gated-execution |
| `external_write` | auto-draft | **require-approval** |
| `privileged_write` | auto-draft | require-approval *(→ dual when a privileged handler is servable)* |

An **unmapped cell fails closed to DENY.** The matrix output (`Disposition`) is consumed by two
fail-closed helpers: `may_draft` (a propose-phase effect may proceed unless DENY — drafting commits
nothing) and `may_execute(approval_recorded)` (an execute-phase effect proceeds only if its disposition
is satisfied — `require_approval` needs a recorded approval; `require_dual` blocks until a dual mechanism
exists; `auto_draft`/DENY can never execute).

### 4. The route compiler — a declarative rule table, not a DSL (R20)

The `ROUTE` step decides *which handler + action_type* a message dispatches to (or `no_action`) from the
dimension predictions. It is a **declarative, non-Turing rule table**, NOT a DSL interpreter and NOT a
monolithic cross-product label (which explodes classes and blocks abstain-to-ancestor): a list of
`RouteRule(predicate → action_type + handler_id)` evaluated **top-down, most-specific-first**, with an
**explicit `no_action` fallthrough**. The handler then produces the concrete action; the gate (above)
evaluates the resulting envelope. Two design rules that keep it scalable *and* safe:

- **Per-route viability threshold, derived from `risk_class` — not hardcoded.** Each route's minimum
  classification band is looked up from the **same manifest the gate reads danger from**
  (`min_band[risk_class_for(handler_id)]`). A dispatch rule whose floor the message's band doesn't meet
  **falls through to the next rule** (→ eventually `no_action`) — i.e. *abstain when not confident enough
  for this action's risk*. Calibrate every floor to the lowest band to make it a **no-op** when you first
  introduce it (routing stays identical), so the mechanism is live + tested before any route actually
  relies on it. Unmapped risk → most-restrictive floor (fail closed).
- **Propose-becomes-a-handler — wrap, don't rewrite.** The concrete-action logic (here: the reviewed
  `correlate → propose` with its fingerprint/apply-floor internals) becomes the *body* of the handler the
  compiler dispatches to, via a **thin read-only wrapper** — the most-scrutinised path is untouched. The
  compiler decides *which handler + action_type + risk_class*; the handler still decides the concrete
  action. Side effects (the case write, the card post, the gate) stay in the pipeline AFTER the handler,
  so the handler is reusable by [[agent-observability-telemetry|shadow mode]] verbatim — which means the
  shadow mirror **can't drift** from the live routing (no duplicated skip-logic to keep in sync).
- **Version-stamp the route.** The compiler stamps a `route_bundle_version` + the matched-rule name on the
  audit row (additively — keep the existing coarse `route` field byte-identical), so every decision records
  *which* rule routed it (incl. *why* a `no_action` message was not triaged).

## The non-negotiable: the gate is a layer ABOVE the enforcer, not a rewrite

This is the crux that makes generalising a **safety-critical** path safe. The matrix is the *generalised
expression* of the policy; it does **not** re-implement enforcement. In [[triage-agent]], `safety.py`
(outbound-off-by-default · internal allowlist · client-domain hard-block · control-channel-only Slack ·
gated/dry-run Jira) stays the **single enforcement choke point, byte-identical**, and is still called at
every effect site (`safe_slack_channel` inside the Slack post, `jira_create_allowed` inside the Jira
create). The gate sits above it as a **fail-closed assertion**: a call site routes its action through the
gate and proceeds only if the disposition matches what that effect may be — then runs the same
enforcer-guarded effect. So:

- In the normal path the downstream enforcer code runs **byte-identically** → no behaviour change.
- The gate can only **prevent** an effect (on a misconfigured matrix/manifest), never add one or skip an
  enforcer check → strictly *stronger*, never weaker. "Exactly as strong" is provable by `git diff` of the
  enforcer (empty) + the unchanged prior test suite.

## How you PROVE a safety-critical refactor changed nothing

The discipline that gated the [[triage-agent]] increment (self + independent-Opus review + these proofs):

1. **The prior test suite, unchanged, stays green** — locks the decision logic byte-for-byte.
2. **An exhaustive invariant** — across *every* action × risk class (incl. the HIGH-risk credential path),
   nothing maps to auto-execute; every propose is draft-only, every apply requires a recorded approval.
3. **A gate-composes-with-enforcer test** — with outbound off, the gate may say "draft/execute" but the
   enforcer still blocks (no post, dry-run only).
4. **A live shadow-diff** ([[agent-observability-telemetry|shadow mode]]) — run real traffic through the
   refactored path and confirm the [[agent-observability-telemetry|`AgentDecision`]] rows carry the
   expected gate disposition with **zero side effects**. (triage-agent: a live credential-exposure report
   → `auto_draft`, no case row created.) For a refactor of a **deterministic** stage that sits *below* the
   LLM (the route decision is a pure function of the classified candidate), use **classify-once / dual-route**:
   classify each fixture **once** on the real model, then run that single candidate through BOTH the old
   logic (a verbatim reference copy) and the new code, and assert identical output. Running old vs new as
   two separate model calls would invite false diffs from LLM non-determinism — diff *below* the LLM, not
   *around* it. (triage-agent session 15: all fixtures MATCH on dispatch/action/gate.)
5. **A dormant trip-wire for a future footgun** — the privileged-execute cell is single-approval today
   (nothing privileged is servable); a *skipped* test fires automatically the day any `privileged_write`
   handler is marked `servable`, forcing the escalation to `require_dual` exactly when it becomes
   load-bearing. (Prefer a trip-wire test over a comment for "this is safe only while X holds".)

## Reusable principles

1. **Verticals are peers behind a typed action space.** The router emits an *action*, not a module;
   adding a work type that maps to an existing action is configuration, not core change.
2. **The gate reads danger (`risk_class`) from a declarative manifest, never a hardcode** — and fails
   closed to maximal danger for an unknown handler.
3. **Two axes — danger × operation phase.** `mode` (propose vs execute) is what lets one risk class draft
   freely yet gate execution; no action draft ever auto-commits.
4. **Generalise a safety path as a fail-closed assertion layer ABOVE the proven enforcer, not a rewrite.**
   The enforcer stays byte-identical and still runs; the new layer can only prevent, never weaken.
5. **An unmapped policy cell fails closed to DENY**; every helper fails closed.
6. **Prove "no regression" with the prior suite + an exhaustive no-auto-execute invariant + a live
   shadow-diff** — measurability ([[agent-observability-telemetry]]) is the safety net that lets you
   refactor the safety path at all.
7. **Leave a dormant trip-wire, not a comment, for a future under-gating** — it fires when the assumption
   breaks.
8. **The route decision is a declarative rule table (top-down, most-specific-first, explicit
   `no_action` fallthrough), not a DSL or a cross-product label** — and its per-route threshold reads
   `risk_class` from the same manifest the gate does. To reproduce scattered control-flow as a table
   safely, **build the truth table first, then order the rules to match it**, and diff the table against a
   verbatim copy of the old logic across the whole matrix (mechanical proof, not argued).
9. **Generalise a concrete step into "a handler the router dispatches to" by wrapping, not rewriting** —
   the reviewed internals become the handler body via a thin read-only wrapper; side effects stay outside
   it so the wrapper is reusable by shadow mode (and the mirror can't drift).

## See Also

- [[triage-agent]] — first implementation (session 14); the `routing/` package + the `safety.py` enforcer
- [[agent-observability-telemetry]] — the decision record + shadow mode this refactor is proven against
- [[classifier-recalibration-pattern]] — the dimension predictions the route step consumes
- [[eclipse-incident-response]] — the human runbook the agent's first vertical (bug-triage) automates
- [[observability-platform]] — obs-api, the agent's signal source
