---
tags: [concept, architecture, agentic-ai, observability, eval, telemetry]
aliases: [agent telemetry, AgentDecision, agent observability, AGENT_DECISIONS, online eval pyramid, shadow mode]
sources: [
  C:/Users/PaulRussell/repos/triage-agent/docs/architecture/overview.md,
  C:/Users/PaulRussell/repos/triage-agent/docs/project/decisions.md,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/telemetry/,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/shadow.py,
]
created: 2026-06-11
updated: 2026-06-11
---

# Agent Observability & Telemetry

How an ALDC agent makes **every decision it takes measurable and auditable** — the reusable pattern
behind the [[triage-agent]] telemetry layer (decisions R15-R18), built so the agent can be safely given
*more* autonomy only over decisions it can already measure. The principle: **instrument once into a
stable internal schema, export many times.** First realised in [[triage-agent]] session 13 (offline,
behind a SQLite/JSONL export seam); designed to extend to any future ALDC agent and to land in
[[observability-platform]]'s Snowflake beside `JOB_RUNS`.

> **Why this exists.** You cannot safely widen an agent's autonomy on decisions you can't measure. Before
> deepening any auto-apply path, every classify / triage / propose / decide step must emit an immutable,
> queryable record + a cheap always-on evaluation — so drift, regressions, and unsafe actions are visible.

## The three layers

### 1. Stable decision record + envelope span (R15)

**Instrument once into a stable internal schema; the mapping layer is permanent.** OpenTelemetry's OTLP
transport is stable, but its **GenAI semantic conventions are still "Development"** — so you do *not*
couple to them. You map *into* a stable `triage.*` / `agent.*` business schema (confidence bands, abstain
reasons, tenant, evidence provenance), and that mapping layer is permanent, not a shim. A future OTLP
exporter maps the same span tree out.

- **`AgentDecision`** — a lean, immutable, **join-friendly** audit row, one per agent invocation. The
  fields ARE the contract (renaming one is a contract change):
  - **Two IDs, kept separate:** a UUID4 `correlation_id` (the cross-plane **business** key — propagates
    observability → Slack → Jira, the [[observability-architecture]] convention) and a distinct 32-hex
    `trace_id` (the telemetry handle). Both stored on every row; never conflated.
  - Version stamps (model + prompt version + future ontology/route/policy versions), calibrated
    confidences + bands, abstain/escalation reason, **evidence as IDs + scores** (never content), action
    type + risk + a **payload hash**, safety flags (injection suspected/rule-hits, untrusted-context,
    tool-request-denied), an operator-override slot, and a backend trace-URL slot.
  - **Raw, untrusted content is stored by sha256 hash only** — the request and the action payload are
    fingerprints, evidence is IDs+scores. This is "evidence by reference, not payload" + the
    untrusted-input posture made concrete: the audit row can't leak a message body or a secret.
- **Envelope span** — one `invoke_workflow` span with nested step spans (classify / correlate / propose
  / persist), a *pure in-process recorder* (no `opentelemetry` dependency needed when there's no
  collector). The span TREE is what makes a later OTLP/Langfuse exporter mechanical.
- **Instrument, don't alter.** The instrumentation is purely additive — the agent's decision logic stays
  byte-equivalent, and the emit is **fail-safe** (a telemetry error is logged and swallowed; it never
  breaks the pipeline or changes a decision).

### 2. Online eval pyramid — layer 1: deterministic checks on ALL traffic (R17)

The cheap, always-on bottom of the pyramid. Every emitted decision is checked against fixed invariants,
producing `AgentEval` rows attached by corr_id + trace_id. Crucially these run against the **observable
decision record** (what a downstream auditor sees), not the agent's internals — which keeps the evaluator
decoupled and faithful to the audit contract. The [[triage-agent]] layer-1 checks:

| Check | Invariant |
|---|---|
| `schema_valid` | confidences/scores in [0,1] (guards model self-report ranges) |
| `label_in_registry` | every emitted label ∈ the servable ontology |
| `action_within_policy` | no action asserted above its risk class — e.g. a concrete remediation inferred from message text below its `fingerprint_confidence` apply-floor is a FAIL (authoritative incident-sourced actions + route-to-human defaults exempt) |
| `evidence_present` | a concrete action must be backed by a match or fingerprint (defensive invariant) |
| `retrieval_count_bounds` | grounding cards within [0, cap] (cards-not-dumps) |
| `injection_flag_present` | present on every decision; WARN on an actionable reading of injection-flagged content |

Each check is isolated (a bug → a FAIL row, never lost checks); the evaluator is pure and never raises.
**Layer 2** (LLM-as-judge on a stratified, tail-heavy sample of the final classification observation,
judges calibrated vs humans with an "Unknown" escape hatch) and **layer 3** (a standing human-calibration
loop) are seams that land `AgentEval` rows with `layer` > 1. The frozen benchmark stays frozen; production
traces feed a **quarantine pool** (dedupe + thread-split + curate → promote into the *next* version).
**Drift alerts fire only when a drift signal co-occurs with a degraded KPI** — a shift in, say, the
abstain rate is not actionable on its own. This is the continuous, operational form of the project's
offline eval-contamination protocol (see [[triage-agent]] eval section).

### 3. Shadow mode — the safe cut-over primitive (R17)

Mirror a request through the SAME read-only reasoning, **suppress every side effect**, and emit a paired
trace (marked `shadow=True`) under the same correlation_id. That paired trace lets you compare a candidate
model / prompt / policy against the live one on real traffic **before** cutting over — without touching a
case, channel, or ticket.

**Suppression is by construction, not by flag:** the shadow path imports NONE of the mutation/outbound
functions (no store writes, no Slack post, no ticket create — not even a dry-run), so there is no code
path that could reach production even with outbound enabled; the only write is the observability sink (the
paired trace itself, which is not case state). A test locks the no-mutation-import property. This composes
with the agent's outbound safety gate by adding the stronger "don't even record a decision to the case"
guarantee.

## The export seam (R16) — instrument once, export many

A single `Exporter` interface takes the stable records and lands them. The weekend/offline exporters
write to **SQLite** (sibling `AGENT_DECISIONS` / `AGENT_EVALS` tables) and an optional **JSONL** mirror;
the production backends are simply new `Exporter` implementations that slot in behind the same seam — so
nothing upstream changes when creds land:

| Backend | Owns |
|---|---|
| **Langfuse** | raw trace topology, prompt lineage, span-level tokens/cost, step scores, datasets, experiments, replay |
| **Prometheus / Grafana** | RED metrics, per-phase latency, spend + cache-hit counters, abstain/escalation rates, alerting |
| **Snowflake + obs-api** | immutable decision records, governance evaluator outputs, aggregates, drift results |

## The Snowflake contract — `AGENT_*` tables, NOT `JOB_RUNS` (R18)

Per-decision agent telemetry is **high-volume request telemetry** and must NOT land in
[[observability-architecture|`OBSERVABILITY.JOB_RUNS`]] (a health/run-status surface for scheduled,
bounded jobs). It gets its own sibling tables:

- **`AGENT_DECISIONS`** — the lean immutable audit row above (one per agent invocation).
- **`AGENT_EVALS`** — one deterministic/LLM-judge/human eval result per row, joined by corr_id + trace_id.
- **`AGENT_DRIFT_WINDOWS`** — windowed drift facts.

Eval batches / drift jobs / prompt-regression runs stay *as jobs* in `JOB_RUNS`. **This is an open
contract to negotiate with the [[observability-platform]] workstream:** the table DDL + ownership (in
`OBSERVABILITY` or a sibling schema), the write path (an agent-owned Snowflake exporter vs an obs-api
ingest endpoint), and whether `AGENT_DRIFT_WINDOWS` is materialised by a scheduled `JOB_RUNS` job. Built
locally in SQLite first so the agent is observable on its own terms without blocking on the negotiation.

## Cost / cache / safety telemetry

The decision record carries the levers token-efficiency work needs (see [[classifier-recalibration-pattern]]
for the accuracy side): attributable model + escalation reason per tier (Haiku→Sonnet→Opus ≈ 1×/3×/5×),
prompt-cache hit accounting (`cache_creation` vs `cache_read`), and the safety flags
(`injection.{suspected,rule_hits}`, `untrusted_context_present`, `tool_request_denied`).

## Reusable principles

1. **Map into a stable internal schema; don't couple to a still-evolving wire spec.** The mapping layer is
   permanent; exporters are swappable.
2. **Two IDs, kept separate:** a business correlation key vs a telemetry trace handle — store both, never
   conflate.
3. **Audit rows store content by hash + evidence by ID/score — never raw (untrusted) content.**
4. **An online evaluator judges the observable record, not the agent's internals** — decoupled + faithful.
5. **Instrument, don't alter** — telemetry is additive and fail-safe; it never changes a decision.
6. **Shadow-mode suppression is strongest when it's by construction** (import no side-effecting function),
   not gated by a flag — and lock it with a test.
7. **Per-decision agent telemetry is its own surface** (`AGENT_*`), distinct from scheduled-job health.

## See Also

- [[triage-agent]] — first implementation (session 13); the `telemetry/` package + `shadow.py`
- [[observability-platform]] — the platform whose Snowflake the `AGENT_*` tables land beside; obs-api is
  the agent's signal source
- [[observability-architecture]] — the `OBSERVABILITY.JOB_RUNS` schema these tables sit *beside* (not in)
- [[classifier-recalibration-pattern]] — the accuracy/eval discipline this observability layer measures
- [[eclipse-incident-response]] — the human runbook the agent automates (the decisions being measured)
- [[zeus-memory]] — tenant memory used for grounding (a contamination concern the eval protocol guards)
