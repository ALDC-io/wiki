---
tags: [project, agentic-ai, triage, observability, hackathon]
aliases: [triage-agent, support-triage-agent, triage agent]
sources: [
  C:/Users/PaulRussell/repos/triage-agent/docs/project/decisions.md,
  C:/Users/PaulRussell/repos/triage-agent/docs/architecture/overview.md,
  C:/Users/PaulRussell/repos/triage-agent/docs/research/digests/,
]
created: 2026-06-05
updated: 2026-06-11
---

# triage-agent

Agentic support-message triage & auto-remediation system. Monitors inboxes/channels (Microsoft 365 +
Slack) → classifies inbound messages → triages against the **observability platform** → proposes a fix
(read-only / human-in-the-loop by default) → eventually reproduces and auto-fixes connector bugs in
Docker. It automates the proven human runbook in [[eclipse-incident-response]] and consumes the
[[observability-platform]]'s `obs-api`. Own repo at `C:\Users\PaulRussell\repos\triage-agent` (a
*consumer* of observability, not part of it). Hackathon project (started 2026-06-05; demo Mon
2026-06-08); bar = near-production-grade.

## Status (2026-06-11, session 10) — correlation accuracy + Phase-4 reconcile + deeper proposals

**Three independent real-depth increments, each self + Opus reviewed, all committed straight to `main`
(`9750bc1` correlation, `2b97f92` reconcile, `e588dd7` proposals). 139 → 163 tests.** Two reviews hit
CHANGES-REQUIRED and were fixed before commit (a correlation false-abstain; generic proposal cues that
false-fired). Still offline, read-only, outbound OFF. Demo polish remains deferred to its own session.

- **Phase-2 correlation hardened to an IDF distinctive-token scorer + a *measured* eval (`triage/correlate.py`,
  `eval/correlation.py`).** The session-8 recall-overlap scorer lost on near-duplicate templates: recall
  normalization *penalizes* the more-specific template (more tokens to cover → lower recall) and ties broke
  arbitrarily, so "Returns Report" beat "FBA Returns Report" and generic "ASIN granularity CHILD" beat
  "…- ONLY Amazon CA". New scorer: weight tokens by **IDF over the client's own incident-template set**, rank
  by `Σ idf(template∩msg)` normalized by the **message's** matchable IDF mass — the incident explaining the
  most *distinctive* message content wins; a specific template whose extra tokens are present beats its
  generic parent; a long template matching only generic words still scores low (abstain holds). Plus a
  **clause-level negation strip** ("the video-and-social one is fine" no longer counts as evidence for that
  report; fails safe, never strips to empty), **scope/intent soft signals** (upstream scope → 1.12× active
  tiebreak; billing/question intent → higher floor), and a **ranked top-5 shortlist**. Measured against a
  **frozen snapshot of the real 78-incident `alert_state.json`** with an 18-row gold set of near-duplicate
  traps: **top-1 0.80 → 1.00, in-top-3 1.00, abstain 1.00** (identical on the live file). Honest caveat
  (reviewer synonym-rewrite stress-tested): 1.00 is on 18 authored rows — IDF, not memorization, is the
  driver, but on real mail the *abstain rate will rise* (more punt-to-human), the correct failure direction.
- **Phase-4 orphan reconcile — closes the session-9 carry-in nit (`decide.reconcile_pending_jira`,
  `store.list_orphan_approved_jira`).** Redrives the `approved`+`jira is None` crash window (claim committed,
  Jira create/backfill never ran) through the **idempotent** `jira.create_issue` (JQL label probe finds a
  pre-crash issue → `idempotent_hit`, never a duplicate; dry-run when outbound off) and backfills; errored
  rows stay orphaned for the next pass; never raises. *Key constraint:* reconcile does NOT re-claim, so its
  only no-duplicate guard is the JQL probe — safe ONLY with no competing writer. Wired to run once on
  startup, synchronously, **before** the intake listeners / `/slack/actions` come up (loud guard comment:
  don't make it periodic without a `jira IS NULL` claim).
- **Deeper proposals — confidence-gated, runbook-anchored (`triage/propose.py`, `triage/slack_card.py`).**
  Tier-A playbook 9 → 12 fingerprints (PowerOutage→escalate_canary, QueueDrainLatency→wait,
  PartitionWedge→recommend_review HIGH — all faithful to [[eclipse-incident-response]], reviewer-verified).
  New **`fingerprint_confidence`** (0..1) from cue strength: a multi-word technical phrase / distinctive
  token is strong (0.72); an ambiguous single token (e.g. "viant") is weak (0.50) and **capped below the
  0.66 apply-floor** so extra weak hits can't stack over it. Below the floor the concrete action is NOT
  asserted — it falls back to incident-aware Tier-B but *surfaces the suspected fingerprint*. Each action
  maps to its **runbook step**, and ESCALATE_CANARY carries **client-parameterized canary guidance**
  (runbook Step 3); both render in the Slack card + Jira draft.

**Reusable patterns (session 10):** build the eval *before* the fix and let it find the failure class;
distinctive-token (IDF) ranking normalized by the message, not the template, is the lever for "the right
one wins" among near-identical client templates; confidence-gate substring-cue inference and cap the weak
path below the apply-floor (surface a suspicion, never auto-assert); a redrive that doesn't re-claim is
safe only before listeners start. (Folded into [[classifier-recalibration-pattern]].)

## Status (2026-06-10/11, session 9)

**Phase-3 PROPER built — the human-in-the-loop loop now closes.** The session-8 triage slice was
**merged to `main` (PR #1, `c6596c0`)**; session 9 built the real inbound write path + first external
mutation on top of it, plus richer (incident-aware) proposals. Committed straight to `main`
(`78b13d3` HITL + `d5867a2` proposals). Self + Opus reviewed; **139 tests** (was 115). Still offline,
read-only by default, outbound OFF by default; demoable end-to-end with no Slack tokens (HTTP endpoint).

- **The loop:** classify → correlate → propose → Slack card → **human Approve/Reject → idempotent
  decision → gated Jira create → board reflects it.**
- **`triage/decide.py` — claim-then-mutate decision engine.** `record_decision` builds the decision,
  **atomically claims** the transition (`store.claim_decision`: a single conditional
  `UPDATE … WHERE status NOT IN (terminal)` — the one serialization point under SQLite's write lock),
  and **only the winner** calls `jira.create_issue`. Fail-closed: unknown corr_id / missing proposal /
  non-terminal status / malformed corr_id (charset-validated) → typed outcome, never raises.
- **`integrations/jira.py` — gated Jira Cloud REST v3 create.** **Dry-run by default**
  (`safety.jira_create_allowed()` requires `OUTBOUND_ENABLED` + all 3 creds); idempotent via a JQL
  probe on the correlation_id label. Mirrors [[aldc-launchpad]]'s `jira_ops.py` (ADF, basic auth).
- **`triage/slack_actions.py` + `api/app.py`.** `parse_action` (pure) + `handle_block_actions`
  (control-channel-gated) wired into **Socket Mode** (`@app.action`) AND a new **`POST /slack/actions`**
  HTTP endpoint that HMAC-verifies (`safety.verify_slack_signature`) and **fails closed (401)** with no
  signing secret unless the explicit dev flag `ALLOW_UNSIGNED_SLACK` is set.
- **Richer proposals (Task E).** Tier-A playbook 5 → 9 fingerprints (FirebaseDoubleInit, SourceHostDown,
  InitSelfHeal, DownstreamWarehouse + broader cues), all grounded in [[eclipse-incident-response]].
  **Tier-B is now incident-aware:** a RESOLVED incident → `VERIFY_DOWNSTREAM` (runbook Step 4), an
  ACTIVE `P2_hint` → `RECOMMEND_REVIEW` at MEDIUM risk, else the prior LOW default.
- **`OBS_ALERT_STATE_PATH` proven LIVE** against the real observability `alert_state.json` (read-only):
  77 incidents, `source=alert_state_file`, `degraded=False`, client codes resolved — the degradation
  chain promotes a live file over the committed fixture.

**Reusable pattern — claim-then-mutate for "decide once → one external action":** never perform the
irreversible external action before the local decision is durably + exclusively claimed; the claim is a
single state-guarded conditional UPDATE, so N concurrent approvals with *different* idempotency keys
collapse to one winner (a same-key check alone does NOT stop differing-key double-clicks). Don't fold the
network call into the write txn (it would stall every other writer). Independent Opus review caught the
differing-key concurrency hole; an 8-thread test now guards it. **Carry-in (Phase 4):** a reconcile for
the `approved` + `jira is None` + outbound-on orphan (the crash window between claim and Jira backfill).

## Status (2026-06-08/09, session 8) — triage slice (since MERGED to main, PR #1)

**Phase-2 triage + Phase-3 propose thin slice BUILT** — the end-to-end demo middle: classify →
**correlate against observability incidents → propose a remediation action + draft Jira → safety-gated
Slack approval card → board**. Offline, read-only, outbound OFF by default. Branch
**`feat/triage-phase2-3` (pushed, OPEN, not merged)**; commits `44f4039` + `d41c7e7` + `35aa399`; Opus
review APPROVE; 16 new tests / 115 total; offline end-to-end smoke green.

- **`integrations/obs_api.py`** — obs-api is a Week-1 stub (only `/heartbeat`), so incident state is read
  via a degradation chain: obs-api `/incidents` (→ None on the stub) → configured `OBS_ALERT_STATE_PATH`
  → committed `data/fixtures/alert_state.json`. Returns an `IncidentSnapshot{incidents, source, degraded}`
  — never a bare list, so **"no signal" is never read as "healthy"**. Never raises.
- **`data/registry/obs_account_map.json`** — the account-display → client_code join. alert_state keys
  embed display names that do NOT match the registry (`Global Ecom Partners` ≠ registry
  `Global E-commerce Partners`; `da8904db` = GEP's prefect account_id). A naive name/alias join matched
  only Fusion92 → GEP (the bulk of incidents) would show unmatched — a demo-killer caught in design
  review. Fix: an explicit committed override table (deterministic, testable) + registry/alias fallbacks.
- **`triage/correlate.py`** — client-first then template-token overlap (≥0.34 **and** ≥2 shared tokens);
  **abstains** on weak match or unresolved client (no cross-client incident merge — the costliest error,
  per `cascade.py`). Severity is a DERIVED `severity_hint`, not obs-api authoritative.
- **`triage/propose.py`** — alert_state has no error fingerprint, so the honest default is **Tier-B
  `RECOMMEND_REVIEW`** (+ draft Jira labeled with the correlation_id); **Tier-A** infers a fingerprint
  from explicit message cues (quota/timeout/zombie/…) and applies the runbook playbook
  (mark_noise/escalate_canary/retrigger) — conservative, only after an incident match, read-only actions.
- **`triage/slack_card.py`** — Block Kit builder (pure) + `post_card` routed through
  `safety.safe_slack_channel()`: posts NOTHING unless outbound is enabled AND a control channel is set,
  never to a client channel. **No Jira is ever created** (draft fields only). Persisted via
  `store.attach_triage` (new `triage` JSON column, status `triaged`); board gains a Triage column.

**Three engineering patterns worth reusing** (also in [[triage-agent]]'s `PROGRESS.md` + Zeus learnings):
explicit override table beats fuzzy matching for known-messy display-name joins; carry a snapshot with a
`degraded`/`source` flag so a fallback-to-empty is never misread as healthy; default to a human-review
recommendation rather than guess a concrete action from incomplete data.

**Next:** land the slice (PR/merge `feat/triage-phase2-3`); optional gated upgrades — live Slack card to the
control channel, interactive approve/reject webhook, live Jira create on approval (Atlassian MCP),
live obs-api via `OBS_ALERT_STATE_PATH`. Full-body grounding re-eval STILL gated on Entra admin consent.

## Status (2026-06-07, session 7)

**Robustness lane — two flag-independent fixes to the proven session-5 path, validated live with no
regression; branch `feat/grounding-layer-wiki` MERGED to `main`.** The Monday full-body re-pull is still
blocked (no Graph admin consent / no `GRAPH_*` in `.env`), so grounding stays parked behind
`GROUNDING_ENABLED` (default OFF). Worked the carry-forward robustness instead — both fixes Opus-reviewed
(APPROVE) and gated on one live grounding-OFF eval. Commits `b41f7da` (Fix 1) + `4df6e45` (Fix 2) + docs;
patterns at [[classifier-recalibration-pattern]] §4.

- **Fix 1 — cascade ValidationError repair (`llm.py`).** A tier occasionally emits a value outside a
  field's enum (e.g. scope value `'credentials'` in `intent`) → `messages.parse` raises a
  `pydantic.ValidationError`; a first-tier error previously crashed the row. Now: retry once with a
  per-field value-list hint appended to the **user turn only** (system prompt / `PROMPT_VERSION` / cached
  prefix untouched → no passing classification shifts, no eval re-run forced); second failure → conservative
  abstain-bound NOISE, never raise; API/transport errors still propagate. **Fired & self-corrected LIVE**
  on a Sonnet `'credentials'`-in-`intent` error during the eval. 6 unit tests.
- **Fix 2 — internal-forward client attribution (`client_resolution.py` + `cascade.py` + `pipeline.py` +
  `registry.py`).** `@aldc.io` forwards recover the client from the quoted original sender
  (`From:` / "… wrote:"); internal-scoped (worst case a safer REVIEW hint, never an action). Resolution
  reads the **raw** body via a new `cascade.classify(raw_body=)` param (pipeline passes `raw_body=msg.text`;
  the LLM still sees the trimmed body) — because `normalize_text` strips the quoted header, without this the
  feature was **inert on the live path** (train/serve skew, caught in review). ReDoS-hardened (8000-char
  scan cap + bounded regex quantifiers; 200 KB body 26 s → 0.0001 s).
- **Validated (one live grounding-OFF eval vs pre-change baseline): noise-FPR 0% → 0%, intent 0.797 →
  0.801, scope flat 0.829, AUTO 65%, client-res 1.0 — no regression, slight lift; all R8 gates hold.**
  Zero-spend pre-check: Fix 2 attributes 14/281 forwards with strictly-protective banding. 99 tests pass.
- **Branch merged to `main`** (grounding flagged OFF = safe infra; sessions 4–7 integrated cleanly, pushed).

**Next:** unchanged — Monday full-body re-pull (gated on Entra admin consent) → flip `GROUNDING_ENABLED=true`
→ full-body grounding re-eval; wire the Zeus half behind availability-time handling.

### Session 6 (prior) — grounding layer built (wiki half), flagged off

**Grounding layer (cascade stage 2) BUILT — wiki half — but held behind a default-OFF flag because, on
the 255-char preview corpus, wiki-only grounding *net-regressed* accuracy.** This is an honest,
evidence-gated outcome, not a setback: the infrastructure is sound (Opus review, no blockers; 84 tests)
and the one clean win is exactly the target metric (**ticket_candidate recall 55% → 64%**). The lesson is
folded into [[classifier-recalibration-pattern]] §3a. Session 6 delivered (branch
`feat/grounding-layer-wiki`, commits `65236e4` + `86cd83f`):

- **`classify/grounding/` package** — a *deterministic* retrieval planner (if/then, NOT an LLM) →
  compiled wiki lookups (`client_aliases` / `tool→scope` / `symptom→ticket`) + an **in-house BM25F** over
  this wiki → ≤5 evidence cards (~2k-tok hard cap; wiki + Zeus **never merged**) injected into the Claude
  prompt, plus scalar `RetrievalFeatures`. `scripts/build_wiki_index.py` compiles committed
  `data/grounding/` artifacts, snapshot by **wiki git SHA** (`7b53e65`). [[zeus-memory|Zeus]] is **stubbed**
  (always unavailable; `as_of` contract in place) — gated behind the availability-time/contamination
  handling. Safety: the trusted grounding block is provably **wiki-derived only** (untrusted message text
  reaches retrieval *solely as a query*); the cached system prefix is untouched.
- **One live eval (frozen 281-row gold): wiki-only grounding net-regressed previews** — intent acc
  0.796 → 0.775, scope 0.829 → 0.811, noise-FPR 0% → 0.55% — with the lone win being ticket recall
  55% → 64%. Net intent flips +13 / −19. **Root cause: cards over-fire on truncated 255-char previews**
  (11/19 regressions were noise→status_update). So grounding is **held behind `GROUNDING_ENABLED`
  (default OFF)** — when off, the cascade is byte-for-byte the proven session-5 path (noise-FPR 0%). Flip
  on for the Monday full-body re-eval, where [[zeus-memory|Zeus]] (the *primary* intent source) also comes
  online. Confirms the §5.3 thesis: wiki grounds scope/entity; the intent lift needs live tenant memory +
  full content.
- **Flag-independent follow-on (`86cd83f`):** an **exact-address** pre-filter for
  `azure-noreply@microsoft.com` (8/8 noise in gold; the dominant noise→status_update error source). It
  can't be domain-pre-filtered — `microsoft.com` apex is shared with `no-reply-powerbi@microsoft.com`
  (3/3 `ticket_candidate`) — so it's keyed by full address. Improves the classifier with grounding OFF
  too (those 8 rows now short-circuit free + deterministically, same labels).

**Next:** Monday full-body re-pull (still gated on Entra admin consent — no `GRAPH_*` creds in `.env`) →
flip `GROUNDING_ENABLED=true` → re-eval on full bodies; wire the Zeus half behind availability-time
handling; tune the symptom→ticket over-fire. Post-hoc calibration/sweep still deferred until grounding
proves a lift.

### Session 5 (prior) — AUTO proven safe + deterministic recalibration

**AUTO band PROVEN safe (noise-FPR 0%); classifier recalibrated to the corrected gold — all three R8
switch-gates met with two cheap deterministic levers, no threshold changes.** The reusable method is
written up at [[classifier-recalibration-pattern]]. Session 5 delivered:

- **Per-row eval + the noise-FPR safety gate** (`scripts/eval_gold.py`, commit `2b356c2`). It now
  classifies each gold row once and persists per-row predictions / per-dimension confidences / band to
  `eval_detail.jsonl`, then computes **noise-FPR** = AUTO-band rows where `pred=noise` but the gold is
  real work (real mail silently auto-dropped as junk — the costliest error), a broader AUTO-precision
  view, and a predicted×gold confusion matrix. `--from-cache` recomputes every metric at **zero API
  spend** (decouples metric iteration from LLM calls); `--limit N` is a cheap live smoke test.
- **Baseline measurement: AUTO was unsafe.** noise-FPR **4.76%** — 5 of 105 AUTO rows were real
  *client* messages auto-dropped as noise (short `Re:` replies the model misread as junk at 0.82–0.92
  conf). Every one of the 7 non-noise-in-AUTO rows was client-domain mail — a clean signal.
- **Two deterministic recalibration levers** (commit `e8b95e2`, Opus review **APPROVE**, 59 tests):
  1. **Sender pre-filter** (`classify/prefilter.py`) — a high-precision allowlist of automated-
     notification domains (`*.atlassian.net`, `avoma.com`, `*.snowflake.com`, `notify.cloudflare.com`,
     MS *support* subdomains, `slack.com`, `email.claude.com`) short-circuits to `noise` **before any
     LLM call** (token saver + the highest-leverage accuracy fix — the live cascade had mislabelled 96
     automated-noise messages `status_update`). Allowlist is **subdomain-specific**: apex `microsoft.com`
     (Power BI "Refresh failed" → `ticket_candidate`) and `getgitguardian.com` (secret-leak →
     `ticket_candidate`) are **excluded**; suffix match is dot-boundary-safe; senders fail OPEN to the LLM.
  2. **Client-noise cap** in `cascade.py::_band` — a *resolved external client* + intent `noise` caps at
     REVIEW (never AUTO), so a client's message is never silently auto-dropped. Vendor / internal /
     unresolved noise still auto-files. Narrows but doesn't undo the session-4 "noise is client-
     independent for the *abstain* case" fix.

> **Result on the frozen 281-row gold** (one live re-eval): noise-FPR **4.76% → 0.00%** (gate ≤1–2% ✅);
> AUTO coverage **37% → 65%** (gate 50–70% ✅); **ticket_candidate precision @AUTO** vacuously safe —
> **zero** ticket/question/billing rows reach AUTO (gate ≥90–95% ✅). Intent accuracy **0.498 → 0.797**,
> scope **0.488 → 0.829**. The only intents that auto-file are `noise` (182/182 = 100% precision) and one
> correct `status_update`; **100% of actionable mail routes to REVIEW** for a human. That is the ideal
> Phase-1 posture: clear the ~80% noise inbox cheaply at 100% precision, human-confirm everything else.

> **Where the residual accuracy lives:** ticket recall 55% / question precision 35% — **entirely inside
> the REVIEW band** (a safety non-issue) and a *content-understanding* gap on forwarded human mail that
> thresholds can't fix. It's the grounding layer's job. **Post-hoc calibration / threshold sweep is
> therefore DEFERRED to after grounding** — tuning thresholds now would trade REVIEW↔AUTO on intents
> whose raw confidences aren't yet trustworthy.

**Next:** Monday full-body re-pull (admin consent) → re-eval → then the **grounding layer**. See
`docs/project/next-session-boot.md`.

## Architecture (the cascade)

Single Python **FastAPI** service, single-agent topology (no agent team until Phase 4), SQLite→Postgres
case store, Anthropic **structured outputs**. Classification is a cost-efficient cascade:

1. **Deterministic** registry + metadata client resolution (against [[aldc-launchpad]]'s
   `shared/client-registry.json` — never hardcode client codes).
   - **1a. Sender pre-filter** (session 5, `classify/prefilter.py`): known automated-notification senders
     short-circuit to `noise` *before* any LLM call — a token saver and the highest-leverage accuracy
     lever (the LLM otherwise mislabels them `status_update`). Subdomain-specific allowlist; apex
     `microsoft.com` + `getgitguardian.com` excluded (they carry failure/security `ticket_candidate`s).
     **Session 6 added an exact-ADDRESS tier** (`_EXACT_NOISE_ADDRESSES`) for `azure-noreply@microsoft.com`
     — automated senders on a shared apex the domain rule can't blanket (`no-reply-powerbi@microsoft.com`
     on the same apex is `ticket_candidate`); the local part disambiguates.
2. **Grounding layer** (session 6, BUILT — wiki half, behind `GROUNDING_ENABLED`, default OFF): a
   *deterministic* retrieval planner routes the static **LLM Wiki** (this wiki — compiled lookups +
   in-house BM25F) and the live **[[zeus-memory|Zeus Memory]]** (tenant-scoped, after client resolution)
   into ≤5 evidence cards injected into the Claude call. Wiki = stable ontology/entity grounding; Zeus =
   live tenant state. Never merged, never full-snapshot. Zeus is **stubbed** (availability-time/
   contamination-gated). Held off the live path: wiki-only grounding net-regressed the preview corpus
   (cards over-fire on truncated bodies) — see Status above + [[classifier-recalibration-pattern]] §3a.
3. **Claude** schema-constrained classification — **Haiku → Sonnet → Opus** cascade: escalate on low
   confidence at any tier, and on high-impact scope (connector/orchestration/credentials) only from the
   cheapest tier; Opus only if still uncertain after Sonnet. Most messages stop at Haiku (token-efficient).
4. **Abstain / calibrate** — 3-band thresholds (auto / review / abstain). `_band` is **decoupled from
   client resolution** (session 4, commit `38edf27`): confident `noise` → AUTO regardless of client;
   non-noise intents cap at REVIEW (not ABSTAIN) when the client is unresolved; the `0.90` linkage floor
   still guards auto-linking. **Plus the session-5 client-noise cap** (commit `e8b95e2`): a *resolved*
   client + `noise` caps at REVIEW (never auto-dropped). Thresholds (`_AUTO_INTENT=0.80`,
   `_AUTO_LINKAGE=0.90`, `_REVIEW_FLOOR=0.50`) are **unchanged** — the deterministic levers met the R8
   gates without a sweep; post-hoc calibration is deferred to after grounding. Validated by the per-row
   noise-FPR gate in `eval_gold.py` (0% on the corrected gold).
5. **Local classifier** (deferred) — a cheap middle layer promoted behind frozen-eval gates once
   ~300–600 corrected labels exist. The same grounding retrieval stage that builds cards now also emits
   scalar features that become priors for this model later ("grounding now, features later").

Four classification dimensions: `client`, `intent`, `ticket_linkage`, `operational_scope`. Correlation
IDs (UUID4) are the traceability backbone (observability → Slack → Jira), matching the
[[observability-architecture]] convention.

## Safety posture (non-negotiable)

- **Read-only by default.** Phases 1–2 never mutate; Phase 3 only *drafts* + routes to a human via
  Slack; Phase 4 is gated + isolated (Docker). Evidence-gated changes the moment Phase 4 touches real
  services.
- **Internal tool — never contact clients in testing.** All outbound routes through `safety.py`:
  OFF by default, internal allowlist (Paul only), client domains (navira.io, fusion92.com, …) hard-blocked.
- **Untrusted input.** Every message body is data, never instructions — prompt-injection containment
  (delimited untrusted region; classifier has no acting tools).
- **Least-privilege** Graph/Slack scopes (`Mail.Read`, not `.ReadWrite`).

## Eval / benchmark protocol (R11/R12)

The gold eval is built from real M365 mailbox content (read-only). One contamination protocol:
thread-split by Graph `conversationId` (never message-split); freeze a human-labeled eval set FIRST
(250–300 incl. 100–150 noise); **Claude drafts → human corrects** with a blinded audit subset; store
both `draft_label` and `final_label`. **[[zeus-memory|Zeus]] already ingests ALDC's O365 email** — so
any Zeus-grounded eval must use availability-time snapshots / same-thread exclusion, or prospective
shadow mode. `content_hash` near-dup leakage guard. Staging code: `src/triage_agent/eval/benchmark.py`
(sharded write + race-free merge; corpus lives in gitignored `data/benchmark/` — real client PII, never
committed). Pull/label/eval tooling: `scripts/pull_inbox.py` (`--auth app|device` direct Graph, or
`--stage-search` preview mode), `scripts/label_corpus.py` (`draft --via api` → `assign-splits` →
`export-gold`), `scripts/eval_gold.py`. **v1 is the interim preview corpus** (subject-proxy `thread_id`,
255-char bodies); the full-body re-pull replaces it once admin consent lands — records carry
`body_source=preview` + `thread_id_source=subject_proxy` flags so the upgrade is auditable.

### Labelling policy (session 4 — ruled by Paul; reuse for the Monday re-label)

The real mailbox is mostly NOT client-support mail (of 281 frozen: only ~34 are a client asking ALDC —
32 navira/GEP + 2 fusion92; the rest is automated notifications, vendor threads, and internal chatter).
The corrected-gold policy:
- **Automated / vendor / Jira-activity senders → `noise`** (schema: "automated notification = noise").
  Covers Jira activity notifications + weekly digests (`jira@…atlassian.net`), Avoma meeting-notes,
  Cloudflare/Atlassian-account/Slack/Claude notifications.
- **Vendor SUPPORT threads where Paul is the customer → `noise`** (Snowflake support cases, MS support /
  Azure quota tickets). Not ALDC's support queue.
- **Internal `@aldc.io` → `noise` UNLESS a genuine ask to look/fix/advise/answer** (then keep its
  actionable intent — e.g. Lori/support forwarding a client defect "please look into asap"). ~26 of 79
  internal rows are genuine asks. The client resolver abstains on internal senders → `client_code` null.
- **Client mail (navira/fusion92) → confirm the content-based draft** (acks → `status_update`, defects →
  `ticket_candidate`, access → `billing_or_access`, calendar → `noise`); these were drafted well.
- **Automated FAILURE / SECURITY alerts are NOT notification-noise — they're actionable signals:**
  Power BI "Refresh failed" → `ticket_candidate/reporting_only`; GitGuardian secret-leak →
  `ticket_candidate/credentials`. (Distinct from Jira *activity* notifications, which are noise.)

> **Gotcha — internal-forward client attribution gap:** the client resolver is *sender-based*, so an
> internal `@aldc.io` forward about a GEP/Navira issue resolves to `client_code=null` (the resolver
> can't see the forwarded-from domain). The gold reflects this (null for internal). A future enhancement
> could parse the quoted `From:` domain to recover client attribution on forwards.

## Key facts & gotchas

- **Anthropic auth/billing:** the SDK auto-resolves an `ant auth login` OAuth profile, but the **ALDC
  org has $0 API credit** → live Messages API calls 400 with "credit balance too low." The claude.ai
  subscription does NOT bill programmatic API calls. Resolution: a credited `ANTHROPIC_API_KEY` in
  gitignored `.env`. **Token/cost efficiency is paramount** — Haiku-first cascade, `trim_body` (strips
  quoted history + signatures), prompt caching, batched subagents for bulk pulls, Batches API for eval.
  > **Contradiction / correction (2026-06-06):** earlier guidance said use `claude -p` (subscription)
  > for bulk label-drafting. **Don't** — measured ~**30K cache-creation tokens per call** (it spins up a
  > full Claude Code session: system prompt + tools + this repo's CLAUDE.md), so ~242 calls burned ~7M
  > tokens / ~$9 and tripped a subscription rate-limit. Use the project's **own API path**
  > (`classify/llm.py::classify_message`, Haiku + prompt caching, ~600 tok/call) for label-drafting —
  > exposed as `label_corpus.py draft --via api`. Reserve `claude -p` for genuinely interactive/one-off
  > work, never volume.
- **Graph auth blocker:** the bulk mailbox pull needs full bodies + real `conversationId`, which the
  claude.ai M365 MCP can't supply cleanly (`read_resource` returns raw multi-KB HTML an LLM can't
  faithfully transcribe). Direct Microsoft Graph is the path (`scripts/pull_inbox.py --auth app`), but
  the **ALDC tenant has user-consent disabled** → an Entra app (`triage-agent-pull`) was registered but
  needs a **tenant admin to Grant admin consent** before any pull (delegated or app-only) works. Until
  then the corpus is the MCP **preview** version. See [[graph-auth-runbook]] (TODO) / project memory.
- **Windows .env BOM:** PowerShell `Set-Content -Encoding utf8` writes a BOM that breaks
  pydantic-settings; config uses `utf-8-sig` to tolerate it.
- **Channels:** M365/Outlook via Microsoft Graph = primary email (NOT Gmail); Slack = second intake +
  the HITL control surface.

## Phased roadmap

| Phase | Name | State |
|---|---|---|
| 1 | Monitor & classify | live-validated; **AUTO proven safe (noise-FPR 0%), R8 gates met (intent acc 0.50→0.80)**; grounding layer BUILT (wiki half) but flagged OFF — net-regressed previews, pending full-body + Zeus re-eval |
| 2 | Triage (read obs-api: correlate failures) | **hardened (s10): IDF distinctive-token scorer + negation strip + scope/intent + ranked top-5; measured vs the real 78-incident file via `eval/correlation.py` — top-1 0.80→1.00** |
| 3 | Propose remediation (draft → Slack HITL) | **PROPER built (s9) + deepened (s10): full HITL loop → claim-then-mutate decision → gated Jira → board; proposals now 12 fingerprints + fingerprint confidence (0.66 floor) + runbook step + canary; Opus APPROVE, 163 tests** |
| 4 | Reproduce & auto-fix in Docker | teaser; **orphan-reconcile carry-in DONE (s10)** — `reconcile_pending_jira` redrives `approved`+`jira=None` on startup; Docker isolated repro still hard (Cosmos/Queue/Blob coupling in [[core_api]]) |
| UI/Jira | Triage board + Jira sync | injection-verified |

All five Deep Research reports are integrated (decisions R1–R26). The three from session 3:
**agent-observability** (R15–R18: OTel→Langfuse+Prometheus+Snowflake; online-eval pyramid; new
`AGENT_DECISIONS/EVALS/DRIFT_WINDOWS` tables, not `JOB_RUNS`), **generalization-platform** (R19–R23:
microkernel intake core + pluggable handlers; dimensioned ontology + route compiler → typed action
envelope → `risk_class`×`mode` safety gate; bug-triage = vertical #1), and **coding-review-agents**
(R24–R26: hybrid graph-first grounding + SEPARATE author/reviewer agents above trivial risk; build at
Phase 4). Digests in `docs/research/digests/`.

## See Also

- [[classifier-recalibration-pattern]] — the reusable method this session proved: noise-FPR safety gate
  + deterministic pre-filter & cost-asymmetry band cap before any model retraining/threshold sweep
- [[observability-platform]] — the signal source; triage-agent consumes its `obs-api`
- [[eclipse-incident-response]] — the human runbook this agent automates
- [[zeus-memory]] — live semantic memory used for inference-time grounding + contamination concern
- [[connector]] / [[core_api]] — Phase-4 reproduction surfaces + constraints
- [[aldc-launchpad]] — client-registry source of truth + UI/backend patterns reused
