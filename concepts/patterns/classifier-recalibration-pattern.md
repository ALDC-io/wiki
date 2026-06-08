---
tags: [pattern, agentic-ai, classification, eval, safety, llm]
aliases: [noise-FPR gate, classifier recalibration, two-lever recalibration, deterministic pre-filter pattern]
sources: [
  C:/Users/PaulRussell/repos/triage-agent/docs/project/decisions.md,
  C:/Users/PaulRussell/repos/triage-agent/scripts/eval_gold.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/prefilter.py,
  C:/Users/PaulRussell/repos/triage-agent/src/triage_agent/classify/cascade.py,
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

## Checklist

1. Persist per-row predictions + confidences + band + gold (not just aggregate accuracy).
2. Define the asymmetric-cost error as a named hard gate; report it + a confusion matrix.
3. Recompute metrics offline from cache; run the live eval once per recalibration step.
4. Fix the dominant confusion with a deterministic pre-filter (specific, fail-open, excludes high-cost cases).
5. Cap the band for cost-bearing contexts instead of moving global thresholds.
6. Defer post-hoc calibration / sweeps until model inputs (grounding) are improved.
7. Gate model-changing edits behind both self-review and an independent (Opus) review. (See [[ai-pr-workflow]].)

## See Also

- [[triage-agent]] — where this was proven (session 5); the live cascade + `eval_gold.py` noise-FPR gate
- [[token-efficiency]] — the cache-decoupled eval and pre-filter are also token-efficiency levers
- [[adversarial-investigation-skill]] — the adversarial/independent-review discipline this pattern's step 7 relies on
- [[ai-pr-workflow]] — ALDC's review gating (independent reviewer above trivial risk)
