---
tags: [entity, project, phaselab, ai-development, prototype, agent-sandbox]
aliases: [PhaseLab, Phase Lab]
sources: [sources/obsidian-import/research/PhaseLab/High-Level Idea.md, sources/obsidian-import/research/PhaseLab/TO-DO - Use- Cases.md, sources/obsidian-import/research/PhaseLab/config.md, sources/obsidian-import/research/PhaseLab/Agent Sandbox Selection.md, sources/obsidian-import/research/PhaseLab/Projectile Prompt.md]
created: 2026-04-18
updated: 2026-04-18
---

# PhaseLab

PhaseLab is an AI-powered prototype exploration product for generating, comparing, reviewing, and refining UI/feature variants from a brief input. As of Phase 0 (April 2026), it is **demo-ready for prototype exploration** with a working generation and evaluation pipeline.

The longer-term vision pairs PhaseLab with **Phase Forge** — a repo-agnostic agent sandbox execution engine — to move from "prototype exploration" to "guarded, testable, merge-ready implementation variants."

## Current State (Phase 0)

Working features:
- Brief input → canonical spec generation → design lane generation
- Multi-variant UI generation with SSE live progress + screenshots
- Evaluator scoring + recommendation
- Human review, selection, notes, and refinement
- Persistence, recent run history, and child refinement runs
- Preview rendering

**Not yet**: repo-backed execution, production quality gates, cross-repo support, or Snowflake-aware data access.

## Architecture

Two-layer system:

### Phase Lab (product exploration layer)
For prototyping, comparison, review, and refinement. The existing product.

### Phase Forge (execution layer — planned)
A repo-agnostic agent sandbox system that:
- Clones real repos and reads their `phase-forge.yaml` manifest
- Executes scoped changes inside isolated sandboxes
- Runs mandatory quality gates (install, lint, typecheck, test, build, screenshot)
- Returns reviewable, merge-ready variants (PRs, patch bundles, or review branches)

## Roadmap

| Phase | Target |
|-------|--------|
| 0 (done) | Demo-ready prototype exploration |
| 1 | True React preview fidelity; tighter evaluator trust |
| 2 | Repo-backed mode for one real internal repo (manifest + sandbox + scoped changes + quality gates) |
| 3 | Production-quality gates (patch summaries, forbidden path checks, max diff, test coverage, PR output) |
| 4 | Repo-agnostic engine (multiple repos via manifest + adapters) |
| 5 | Feature data packages (snapshots, fixtures, optional Snowflake extracts) |
| 6 | Snowflake-aware mode (read-only, guardrailed, audited) |
| 7 | Cross-product integration with [[zeus-memory]] context + [[cpma]] compliance |

## Key Design Rules

- **Agents generate, systems verify, humans approve** — the model for production-eligible output
- **Hard gates, not suggestions** — repo contract, change scope rules, mandatory verification pipeline, policy checks, code review summary
- **Repo adapter contract** — each supported repo defines `phase-forge.yaml` with commands, quality gates, constraints, and sandbox config

## See Also

- [[zeus-memory]] — planned context layer for Phase 7 integration
- [[cpma]] — planned compliance layer for Phase 7 integration
- [[factoria]] — related autonomous data engineering platform (different domain but similar agent-driven delivery model)
- [[openclaw]] — agent runtime used by Factoria; relevant architecture reference for Phase Forge execution layer
