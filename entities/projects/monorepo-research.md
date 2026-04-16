---
tags: [entity, project, monorepo, cce, developer-experience, architecture]
aliases: [Monorepo Research, Monorepo + CCE Integration]
sources: [sources/obsidian-import/research/MONOREPO/Research/Monorepo + CCE Integration - Complete Benefits Analysis.md]
created: 2026-04-16
updated: 2026-04-16
---

# Monorepo Research

A comprehensive analysis (completed April 7, 2026) evaluating the benefits of consolidating all ALDC repos under `C:\Users\PaulRussell\repos\` into a single monorepo, with particular focus on maximizing [[CCE]] (Claude Code Enhanced) benefits. Status: **Research Complete -- Pending Decision**.

## Vision / Goal

Consolidate 10+ repositories into a single monorepo to unlock 38 concrete improvements across 8 categories, with the highest-value wins being Claude Code intelligence improvements that require only directory restructuring and CLAUDE.md files -- no build tool changes.

## Current State (Audit)

| Repo | Language | Git? | CLAUDE.md? | Active? |
|------|----------|------|------------|---------|
| claude_code_enhanced | TS/Python/Docs | Yes | Yes | Yes (Mar 2026) |
| claude_code_system | Config only | No | No | Empty placeholder |
| phase-lab | TypeScript (pnpm) | Yes (new) | No | Yes (Apr 2026) |
| connector | Python (Prefect) | Yes | No | Yes (Mar 2026) |
| core_api | Python (Azure Functions) | Yes | No | Stale (Jan 2026) |
| enterprise knowledge system | Python (Streamlit) | No | No | Prototype |
| clients | Power BI | Yes | No | Yes (Apr 2026) |
| power_bi | Power BI/DAX | No | No | Stale |
| projects | Mixed (42 subdirs) | Yes | Partial | Mixed |
| lessonhub | Unknown | No | No | Empty |

**Key problems**: 4 repos have no git. Only 1 has CLAUDE.md. Version drift across shared deps. No cross-repo CI. CCE skills only benefit one repo. Zero shared packages.

## Improvement Categories

### 1. Claude Code Intelligence (Biggest Win, Lowest Effort)
- **CLAUDE.md hierarchy**: Root CLAUDE.md for global rules + per-app CLAUDE.md for domain context
- **Path-scoped .claude/rules/**: Python rules don't pollute TypeScript context
- **Single .claude/ directory**: CCE's 178 skills + 14 commands available everywhere
- **@imports in CLAUDE.md**: Cross-service knowledge graph Claude navigates automatically
- **Agent teams across packages**: Parallel Claude agents updating API contract + connector + phase-lab atomically
- **Skills per package**: Root skills (deploy, release) + package-level skills (run-pipeline, generate-prototype)

### 2. Dependency Management
Critical version drift found:
- `snowflake-connector-python`: 3.18.0 (connector) vs 3.7.0 (core_api) -- **11 minor versions**
- `cryptography`: 44.0.2 vs 41.0.7 -- **3 major versions**
- `@anthropic-ai/sdk`: 0.39.0 (phase-lab) vs 0.73.0 (factoria)

Solution: Single lockfile per language, extractable shared packages (`packages/azure-auth`, `packages/db-client`, `packages/shared-types`, `packages/api-contracts`).

### 3. CI/CD & Deployment
- Affected-only testing via `nx affected -t test`
- Unified pipeline replacing 3 different GitHub Actions configs
- Atomic cross-service PRs (one PR touches contract + all consumers)
- Shared Docker base images
- Coordinated Azure deployment in dependency order

### 4. Code Sharing & Consistency
- Shared API contracts (Zod schemas generating both Python dataclasses and TypeScript types)
- Shared Azure utilities, test fixtures, linting/formatting configs, TypeScript tsconfig

### 5. CCE System Benefits
- [[Zeus Memory]] available across all repos (currently only CCE connects)
- CCE project templates (PROGRESS.md, phase-based implementation) applied everywhere
- Learning capture across services via `/cce-learn`
- Unified hooks with per-service matchers
- Cross-service agent delegation via `Task(Explore)`

### 6-8. Developer Experience, Quality/Governance, Dead Weight Elimination
One clone gets everything. Single search spans all services. Unified git history. Shared .env. Discoverable architecture. Plus cleanup of empty repos and stale projects.

## Key Decisions

- **Recommended tool: Nx** (over Turborepo, Pants, Bazel) for its native TypeScript support, Python plugins, moderate learning curve, and good Azure integration
- **Proposed structure**: `apps/` (phase-lab, connector, core_api, enterprise-knowledge), `packages/` (shared-types, db-client, azure-auth, api-contracts), `tools/` (power-bi, clients), `infra/` (docker, modules)

## Migration Order

1. **phase-lab** first (already a pnpm monorepo, nearly copy-paste)
2. **CCE** (becomes the `.claude/` layer at monorepo root)
3. **connector + core_api** (Python services with shared Azure deps)
4. **enterprise knowledge system** (small, low risk)
5. **clients + power_bi** (version-controlled assets, no build config)
6. **projects/** (archive stale, migrate active as packages)

## Open Questions / Next Steps

- Decision pending on whether to proceed with monorepo consolidation
- Need to evaluate impact on existing CI/CD workflows and team workflow
- Consider incremental migration vs big-bang approach
- Assess Nx learning curve for the team

## See Also

- [[cce]] -- the primary beneficiary of monorepo consolidation
- [[factoria]] -- would become an app in the proposed monorepo
- [[ai-driven-dev-workflow]] -- development methodology that would apply across the monorepo
