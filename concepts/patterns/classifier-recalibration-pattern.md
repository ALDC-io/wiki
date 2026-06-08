---
tags: [pattern, agentic-ai, classification, eval, safety, llm]
aliases: [noise-FPR gate, classifier recalibration, two-lever recalibration, deterministic pre-filter pattern]
sources: [
  C:/Users/PaulRussell/repos/triage-agent/docs/project/decisions.md,
  C:/Users/PaulRussell/repos/triage-agent/scripts/eval_gold.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/prefilter.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/cascade.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/llm.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/client_resolution.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/pipeline.py,
]
created: 2026-06-07
updated: 2026-06-07
---

# Classifier Recalibration Pattern (noise-FPR gate + deterministic levers)

A reusable method for getting an LLM classifier from "measured but wrong" to "safe and accurate"
**without retraining and without tuning confidence thresholds** — proven on [[triage-agent]] (session 5,
2026-06-07: intent accuracy 0.50 → 0.80, AUTO false-drop rate 4.76% → 0%). The core ideas generalize to
any auto-act-vs-human-review classifier with an asymmetric cost of error (auto-filing, auto-routing,
auto-merging, spam/junk classification, incident triage).

The pattern has three moves, in order: **(1) prove the auto-action is safe before trusting it; (2) fix
the dominant error with cheap deterministic rules, not model changes; (3) defer expensive calibration
until the model's inputs are actually informative.**

## 0. The setup: action bands over a confidence

Decisions are gated into bands — typically **AUTO** (act with no human), **REVIEW** (label, human
confirms), **ABSTAIN** (too uncertain, human decides). AUTO is the dangerous band: it acts without a
human, so its *precision* is the whole safety story. Coverage (the % in AUTO) is the efficiency story.
The tension is real — pushing coverage up risks letting a wrong call auto-act.

## 1. Prove AUTO is safe FIRST — the noise-FPR gate

Before any recalibration, **measure the costliest error directly** and treat it as a hard gate. Most
eval harnesses report aggregate accuracy and *discard per-row detail* — which hides exactly the
safety-critical question. So:

- **Persist per-row predictions** (predicted label, per-dimension confidences, the assigned band, and
  the gold label) to a detail file — not just an accuracy number. In triage-agent this is
  `eval_gold.py` → `eval_detail.jsonl`.
- **Compute the asymmetric-cost metric explicitly.** Here the costliest error is *real work silently
  auto-filed as junk*, so the gate is **noise-FPR = (AUTO-band rows where `pred=noise` but the gold is
  real work) ÷ (all AUTO-band rows)**, target ≤1–2%. Distinguish it from a benign cousin (e.g. a row
  with non-noise gold that auto-acted under a *correct* non-noise label — acted, but not *dropped*).
  Name and report both; gate on the dangerous one.
- **Show a confusion matrix** (predicted × gold) so the aggregate accuracy becomes legible — it tells
  you *which* confusion dominates, which drives move 2.

> **Decouple metric iteration from API spend.** Persisting per-row detail lets you recompute every
> metric **offline from the cache** (`--from-cache`) with zero further LLM calls. Re-run the live eval
> only once per real recalibration step, never per metric tweak. (See [[token-efficiency]] —
> [[triage-agent]] treats API spend as paramount.)

Result of this move on triage-agent: AUTO was **not** safe (noise-FPR 4.76%; 5 real client messages
auto-dropped). The gate blocked recalibration until fixed — exactly its job.

## 2. Fix the dominant error with deterministic rules, not model changes

The confusion matrix and the failing rows point at the highest-leverage fix. In practice it's almost
never "tune a threshold" or "retrain" — it's a cheap, high-precision deterministic rule the model
shouldn't have to learn at all. Two complementary levers:

### 2a. Deterministic pre-filter (short-circuit before the model)
If a large, mechanically-identifiable slice of inputs has a known label, classify it **before** the LLM
call. triage-agent's inbox is ~80% automated vendor/tool notifications; an allowlist of
automated-notification *sender domains* short-circuits them to `noise` deterministically. This
**saves tokens** (the model never sees them) **and fixes accuracy** (the LLM had been mislabelling 96
of them as `status_update`). Build the allowlist from the corrected gold (every listed domain was 100%
that label in ground truth).

> **The safety rule for a pre-filter: it must NEVER swallow a high-cost case, and it must fail OPEN.**
> Make the match **specific, not broad** — triage-agent allowlists *subdomains* (`techsupport.microsoft.com`),
> and deliberately **excludes apex domains** that also carry high-stakes mail (`microsoft.com` sends
> Power BI "Refresh failed" → `ticket_candidate`; `getgitguardian.com` sends secret-leak alerts). Make
> suffix matches dot-boundary-safe (`domain == base or domain.endswith("." + base)` — so `notsnowflake.com`
> and right-extension spoofs like `snowflake.com.evil.com` can't match). A malformed/unknown input must
> fall through to the model, never default into the cheap class.

### 2b. Cost-asymmetry band cap (let one signal veto AUTO)
When a specific, detectable context makes an auto-action disproportionately costly, **cap that
context's band at REVIEW** rather than globally raising a threshold. triage-agent: a *resolved external
client's* message classified `noise` caps at REVIEW (never AUTO) — dropping a client's short reply as
junk is expensive; dropping a newsletter is free. Vendor/internal/unresolved noise still auto-files.

Why a targeted cap beats raising the global threshold: the dangerous rows sat at 0.82–0.92 confidence,
so the threshold would have to rise high enough to *also* kill legitimate high-confidence auto-actions
elsewhere — trading broad coverage to fix a narrow, identifiable problem. A cap keyed on the
cost-bearing signal fixes the narrow problem precisely.

Result on triage-agent: noise-FPR 4.76% → **0%**, AUTO coverage 37% → **65%** (it went *up* — the
pre-filter correctly moved vendor noise into confident AUTO while the cap removed the dangerous drops),
intent accuracy 0.50 → **0.80** — all with **no threshold or model changes**.

## 3. Defer expensive calibration until inputs are informative

Post-hoc probability calibration (temperature / isotonic) and full threshold sweeps are real tools, but
they're only worth it once the model's raw confidences mean something. triage-agent's residual error
(ticket recall 55%, question precision 35%) lived **entirely inside the REVIEW band** (a safety
non-issue — a human sees those) and was a *content-understanding* gap on forwarded human mail that no
threshold can fix. The right next investment is better model **inputs** (a grounding/retrieval layer),
not calibration of uninformative outputs. So calibration was **deferred** — sequencing the cheap,
high-certainty wins ahead of the expensive, lower-certainty ones.

### 3a. …and when you add those inputs, *measure* the lift — don't assume it (session 6)

[[triage-agent]] then built the grounding layer step 3 pointed at (a deterministic retrieval planner over
the [[LLM Wiki]] → evidence cards into the prompt). The honest result: on the **255-char preview** corpus,
wiki-only grounding **net-regressed** (intent 0.796 → 0.775, scope 0.829 → 0.811, noise-FPR 0% → 0.55%) —
the lone win was the target metric, ticket recall 55% → 64%. Three transferable lessons:

- **Lexical/ontology grounding lifts *entity & scope*, not *intent*.** Knowing *which client* and *what
  tool* a message is about is an entity-resolution win; deciding *is this a question, a ticket, or just
  chatter* is a content-understanding judgment that static wiki facts don't carry. The intent lift needs
  **live, message-specific context** (prior thread, open tickets — i.e. tenant memory) + the **full
  message body**, not a knowledge base. Route grounding sources per-dimension accordingly.
- **Measure on the layer the consumer actually reads.** Cards over-fired on 255-char *previews* (11/19
  regressions were noise→status_update — a card primes the model to "read more into" a truncated reply).
  Evaluating retrieval-augmented classification on a truncated proxy of the real input can invert the
  result; defer the verdict to full content. (A direct application of the evidence-gating rule: validate
  at the consumer's layer.)
- **When a measured change regresses, gate it behind a flag — don't ship it on the hope it'll help
  later.** Grounding went in behind `GROUNDING_ENABLED` (default OFF), so the live path keeps the proven
  behavior; the flag flips on to re-measure once the inputs are real (full bodies + tenant memory). The
  build is preserved and reviewed; only its *activation* waits for evidence.

A clean side-benefit surfaced *by* the grounding eval: the dominant error source (8 automated
`azure-noreply@microsoft.com` notices the cards upgraded to status_update) became a deterministic
**exact-ADDRESS** pre-filter entry (move 2a, refined) — `microsoft.com` apex is shared with the
`ticket_candidate`-bearing `no-reply-powerbi@…`, so the local part, not the domain, is the safe key. That
fix is flag-independent and helps even with grounding off.

## 4. Robustness hardening for the live path — and the train/serve traps it exposes (session 7)

With the full-input re-eval still blocked, [[triage-agent]] session 7 hardened the *proven* path with two
flag-independent fixes. Each carried a transferable lesson about the gap between what the **eval** measures
and what the **live pipeline** actually does.

### 4a. Repair schema-violations in the USER turn, not the system prompt
A schema-constrained classifier (`messages.parse(output_format=…)`) will *occasionally* emit a value
outside a field's enum — e.g. an `operational_scope` value (`'credentials'`) in the `intent` field — which
the SDK rejects with a `pydantic.ValidationError`. Don't let it crash the row; **retry once with a
per-field value-list hint**. The key move: append the hint to the **user turn**, never the system prompt.
The system prefix is *prompt-cached* and version-stamped — editing it bumps the prompt version, invalidates
the cache, and shifts *every* currently-passing classification (forcing a full eval re-run). Putting the
repair in the user turn means only the rare retry pays the extra tokens and **no passing verdict moves** —
so the fix needs no re-validation of the baseline. On a second failure, degrade to a conservative
abstain-bound result (reuse the existing refusal path); never raise on a model-output problem. Keep genuine
API/transport errors propagating (catch the *specific* validation exception, not a broad `Exception`, so
network errors still reach the caller's fallback). Lock it with a unit test that asserts the cached system
block is **byte-identical across the repair retry**. (Token-efficiency link: [[token-efficiency]].)

### 4b. Resolve entities from the RAW body, not the LLM-normalised body (a train/serve skew)
The internal-forward attribution fix — recover the client from a staff `@aldc.io` forward by reading the
quoted original sender (`From:` / "… wrote:") — looked correct and *passed its unit tests*, but an
independent review caught that it was **inert on the live pipeline**: `normalize_text` strips the quoted
header before classification, so the live path resolved against a body with the very signal removed. The
eval, meanwhile, fed the *raw* gold body, so the feature fired there — a classic **train/serve skew** where
the offline harness and the online path disagree on the input. The fix: give the deterministic resolver the
**raw** body while the LLM keeps the trimmed/normalised body (here, a `raw_body` param threaded from the
pipeline). General rule: **different consumers need different views of the input** — a normalisation step
that helps the model can starve a rule-based extractor. Always confirm a new feature actually fires on the
*live* path, not just in the eval; an offline-only firing is a skew bug, not a working feature.

### 4c. Bound every regex over untrusted input (ReDoS)
The forwarded-sender extractor ran an email regex over an *uncapped* body. An unbounded local-part run
before `@` made it O(n²) (measured 80 KB → 26 s). Untrusted input + unbounded quantifiers = a DoS vector.
Fix with layered bounds, any one of which suffices: a length cap on the scanned text *before* matching, plus
bounded quantifiers (`{1,64}@{1,255}\.{2,24}`). 200 KB pathological body → 0.0001 s after. (Mirrors the
CLAUDE.md untrusted-input posture: the message body is hostile data.)

> Both 4b and 4c were caught by the **independent (Opus) reviewer**, not the author — concrete payoff for
> step 8's review gate. The author's own tests passed; the second context found the live-path gap and the
> DoS. (See [[ai-pr-workflow]], [[adversarial-investigation-skill]].)

Result: validated by one live grounding-OFF eval — **noise-FPR 0% → 0%**, intent **0.797 → 0.801**, scope
flat, AUTO 65% — no regression, slight lift; and the ValidationError repair **fired and self-corrected live**
on a real Sonnet `'credentials'`-in-`intent` error during that same run.

## Checklist

1. Persist per-row predictions + confidences + band + gold (not just aggregate accuracy).
2. Define the asymmetric-cost error as a named hard gate; report it + a confusion matrix.
3. Recompute metrics offline from cache; run the live eval once per recalibration step.
4. Fix the dominant confusion with a deterministic pre-filter (specific, fail-open, excludes high-cost cases).
5. Cap the band for cost-bearing contexts instead of moving global thresholds.
6. Defer post-hoc calibration / sweeps until model inputs (grounding) are improved.
7. When you add those inputs, **measure the lift on full/real input — don't assume it**; route grounding per-dimension (entity/scope ≠ intent); flag-gate any measured regression rather than shipping on hope (§3a).
8. Gate model-changing edits behind both self-review and an independent (Opus) review. (See [[ai-pr-workflow]].)
9. Repair schema-violating LLM output in the **user turn** (preserve the cached system prefix); degrade to a conservative abstain, never crash; catch the *specific* validation error so API errors still propagate (§4a).
10. Feed deterministic extractors the **raw** input and the model the normalised input — and verify the feature fires on the **live** path, not just the eval (train/serve skew, §4b).
11. Bound every regex over untrusted input — length cap + bounded quantifiers (ReDoS, §4c).

## See Also

- [[triage-agent]] — where this was proven (session 5); the live cascade + `eval_gold.py` noise-FPR gate
- [[token-efficiency]] — the cache-decoupled eval and pre-filter are also token-efficiency levers
- [[adversarial-investigation-skill]] — the adversarial/independent-review discipline this pattern's step 7 relies on
- [[ai-pr-workflow]] — ALDC's review gating (independent reviewer above trivial risk)
