---
tags: [concept, pattern, ai, claude-code, skill, investigation, multi-agent]
aliases: [Adversarial Investigation, /investigate-adversarial, Adversarial Multi-Agent Protocol]
sources: [Confluence AIRA/1763246091 (Adversarial Multi-Agent Investigation Protocol, 2026-04-06)]
created: 2026-04-18
updated: 2026-04-18
---

# Adversarial Investigation Skill

Claude Code skill developed by Vlad Ryzhkov. A 6-phase adversarial investigation protocol for bugs, architecture decisions, technology evaluations, concept validation, solution improvement, and competitive analysis.

**Skill name:** `/investigate-adversarial`
**Repo location:** `.claude/skills/investigate-adversarial/skill.md`
**Effort:** max

> Never stop at plausible. Stop at proven.

## When to use

| Problem type | What it does |
|---|---|
| Bug / defect | Find root cause, prove it, fix it, verify the fix |
| Technology evaluation | Map the landscape, stress-test the leading option, quantify trade-offs |
| Architecture decision | Evaluate approaches adversarially, prove which survives scrutiny |
| Concept validation | Define what "sound" means, then try to break it from every angle |
| Solution improvement | Forensically map current solution, find weaknesses, design what's better |
| Competitive analysis | Exhaustive landscape, adversarial evaluation of contenders, evidence-backed ranking |
| "How does X work?" | Trace forensically, verify against docs and source, surface undocumented behaviour |

## The 6 phases

Every phase has a **gate** — a mandatory self-check that must pass before proceeding. Skipping a gate is a protocol violation.

### Phase 0 — ANCHOR
Create a task with the full problem statement. Create `_thoughts/<investigation-name>/anchor.md` with problem type, acceptance criteria, and load-bearing assumptions. Before declaring completion, re-read the anchor: "did I solve the actual problem, or did I just complete a checklist?"

### Phase 1 — OUTSIDE-IN (Scope before depth)
Do NOT dive into code or search immediately. Frame the problem: (1) what category? (2) what does a correct answer look like? Define acceptance criteria BEFORE investigating. (3) what are the load-bearing assumptions? These become attack targets later. Surface framing to user in 3–5 lines.

**Gate:** problem category, acceptance criteria, and load-bearing assumptions all identified.

### Phase 2 — FORENSIC EVIDENCE (Data before opinion)
Launch parallel agents with opposing vectors. Every agent must return file paths with line numbers, URLs with excerpts, exact search patterns used, and negative results.

**Agent patterns by problem type:**

*Codebase problems:* Forward tracer (trigger → output), Backward tracer (output → cause), Absence hunter (what SHOULD exist but DOESN'T).

*Technology eval / concept validation:* Landscape mapper, Success hunter (production deployments, benchmarks), Failure hunter (postmortems, "why we moved away" posts).

*Solution improvement:* Current-state auditor, Weakness finder (TODOs, suppressed errors, hardcoded limits), State-of-art researcher.

*Always include:* Assumption cracker (known issues, edge cases, dependency surprises).

**Trust protocol:** "Nothing found" → REJECT and relaunch with broader scope. Two agents contradict → most valuable signal. Write findings to `_thoughts/<investigation-name>/findings.md`.

**Gate:** 3+ agents with opposing vectors, "nothing found" rejected and relaunched, contradictions flagged, hypothesis stated in one sentence.

### Phase 3 — ADVERSARIAL TRIANGULATION (Attack your own findings)
Three agents on the leading hypothesis:
- **PROVE** — every piece of evidence that supports it
- **DISPROVE** — every piece of evidence that contradicts it; alternative explanations, counterexamples, failure modes
- **BLIND-SPOT** — what did both agents miss? Adjacent systems, upstream/downstream effects, second-order consequences

Evaluate like a judge, not a participant.

**Gate:** DISPROVE launched (mandatory), BLIND-SPOT launched, contradictions investigated, unexamined territory searched.

### Phase 4 — QUANTIFY (Numbers, not adjectives)
No "it's slow" — HOW slow. No "it's widespread" — HOW MANY. No "it's risky" — WHAT SPECIFICALLY breaks. No "it's better" — BY HOW MUCH.

**Gate:** every finding has a number; a decision-maker could act on quantification alone.

### Phase 5 — CLASSIFY IN CONTEXT (You're not the first)
- **ADVOCATE** — evidence the conclusion is sound, proven, adopted in industry
- **CRITIC** — evidence it fails at scale, has hidden costs, was abandoned

Truth is in the tension between advocate and critic.

**Gate:** both launched, tension analysed, industry context established.

### Phase 6 — CONVERGE AND STRESS-TEST
Re-read the anchor. Synthesise conclusion adapted to problem type. Stress-test: edge cases? new assumptions? simpler path? Would DISPROVE accept this?

**Final gate:** (1) re-read anchor, (2) conclusion answers the original problem, (3) all phases executed, (4) DISPROVE ran and strongest counterargument addressed, (5) no adjectives where numbers should be, (6) you would bet money on this conclusion.

## Core execution rules

1. Never present assumption as conclusion
2. Never stop at first plausible answer — always launch DISPROVE
3. Negative results are diagnostic, not dead ends
4. Contradictions are the most valuable signal
5. Progressive depth, not width
6. Surface findings at phase boundaries
7. Three rounds minimum before "doesn't exist"
8. Verify outcomes, not just findings
9. Problems cluster — scan for the same pattern elsewhere
10. The methodology is the guarantee

## See Also

- [[ai-pr-workflow]] — the ALDC development workflow this skill supports (AI-augmented code review, CCX)
- [[ai-development-project-standard]] — tracking standard for AI-developed projects
