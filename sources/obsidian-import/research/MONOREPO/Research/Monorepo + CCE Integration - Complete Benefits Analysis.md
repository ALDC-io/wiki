# Monorepo + CCE Integration - Complete Benefits Analysis

  

**Date**: 2026-04-07

**Status**: Research Complete — Pending Decision

**Scope**: All repos under `C:\Users\PaulRussell\repos\`

  

---

  

## Current State

  

| Repo | Language | Git? | CLAUDE.md? | CI/CD? | Active? |

|---|---|---|---|---|---|

| **claude_code_enhanced** | TS/Python/Docs | Yes | Yes | GH Actions | Yes (Mar 2026) |

| **claude_code_system** | Config only | No | No | No | Empty placeholder |

| **phase-lab** | TypeScript (pnpm) | Yes (new) | No | No | Yes (Apr 2026) |

| **connector** | Python (Prefect) | Yes | No | No | Yes (Mar 2026) |

| **core_api** | Python (Azure Functions) | Yes | No | GH Actions | Stale (Jan 2026) |

| **enterprise knowledge system** | Python (Streamlit) | No | No | No | Prototype |

| **clients** | Power BI | Yes | No | No | Yes (Apr 2026) |

| **power_bi** | Power BI/DAX | No | No | No | Stale |

| **projects** | Mixed (42 subdirs) | Yes | Partial | Partial | Mixed |

| **lessonhub** | Unknown | No | No | No | Empty |

  

**Key problems today:** 4 repos have no git. 1 has CLAUDE.md. Version drift across shared deps. No cross-repo CI. CCE skills only benefit one repo. Zero shared packages.

  

---

  

## Improvements By Category

  

### 1. Claude Code Intelligence (Biggest Win)

  

| # | Improvement | What Changes | Impact |

|---|---|---|---|

| 1 | **CLAUDE.md hierarchy** | Root CLAUDE.md for global rules + per-app CLAUDE.md for domain context. Claude loads both automatically based on working directory. | Claude understands "this is a connector Python file" vs "this is a phase-lab React component" without manual prompting. Every repo gets context-aware AI assistance. |

| 2 | **Path-scoped .claude/rules/** | Rules with `paths:` frontmatter only load when Claude touches matching files. Python rules don't pollute TS context, and vice versa. | Smaller, more focused context = better code quality. No more 400-line CLAUDE.md files. |

| 3 | **Single .claude/ directory** | One skills library, one agents directory, one hooks config, one rules directory — shared across all services. | CCE's 178 skills + 14 commands become available in every service, not just `claude_code_enhanced`. |

| 4 | **@imports in CLAUDE.md** | `@../../packages/shared-types/README.md` lets per-service CLAUDE.md reference shared contracts without duplicating content. | Cross-service knowledge graph that Claude navigates automatically. |

| 5 | **Agent Teams across packages** | Spawn parallel Claude agents: one updating API contract, one updating connector, one verifying phase-lab compiles. | Only possible when all code is in one worktree. Multi-repo agents can't atomically change shared contracts. |

| 6 | **Skills per package** | Root skills (deploy, release) + package-level skills (run-pipeline, generate-prototype). Loaded on demand. | Every team gets specialized skills without context bloat. |

  

### 2. Dependency Management

  

| # | Improvement | Current Problem | Monorepo Solution |

|---|---|---|---|

| 7 | **Single version policy** | `snowflake-connector-python` is 3.18.0 in connector, 3.7.0 in core_api. `cryptography` is 44.0.2 vs 41.0.7. 6+ Azure SDK packages have minor version drift. | One lockfile, one version per dependency. `pnpm-lock.yaml` for TS, `constraints.txt` or `uv.lock` for Python. |

| 8 | **Shared Python packages** | `azure-cosmos`, `azure-storage-blob`, `azure-identity`, `pandas`, `pydantic` duplicated across connector + core_api + projects. | Extract `packages/azure-auth`, `packages/db-client` as internal packages with pip editable installs. |

| 9 | **Shared TypeScript packages** | Phase-lab already has `@phase-lab/core` with Zod schemas. Factoria uses `@anthropic-ai/sdk@0.73.0`, phase-lab uses `@0.39.0`. | Unified workspace means shared `@anthropic-ai/sdk` version, potential shared `@monorepo/api-contracts` package. |

| 10 | **Dependency deduplication** | Each repo installs its own copy of overlapping deps. | pnpm hoists shared deps. Python virtual envs can share a base layer. |

  

### 3. CI/CD & Deployment

  

| # | Improvement | Current Problem | Monorepo Solution |

|---|---|---|---|

| 11 | **Affected-only testing** | Change a shared pattern -> manually trigger builds in downstream repos. No way to know "connector depends on core_api's output format." | `nx affected -t test --base=origin/main` computes dependency graph, only tests what changed. |

| 12 | **Unified pipeline** | 3 repos have GH Actions, all different. Most have none. | One `.github/workflows/` with matrix strategy or Nx-driven affected builds. |

| 13 | **Atomic cross-service PRs** | Changing an API contract requires coordinated PRs across repos. | One PR touches contract + all consumers + infrastructure. Review the full change together. |

| 14 | **Shared Docker base images** | Connector and core_api have separate Dockerfiles with overlapping base layers. | `infra/docker/python-base.Dockerfile` shared by all Python services. |

| 15 | **Azure deployment coordination** | Manual `az containerapp update` per service, gets overwritten by GHA auto-deploy (known gotcha). | Monorepo deploys affected services in dependency order via one workflow. |

  

### 4. Code Sharing & Consistency

  

| # | Improvement | What You Gain |

|---|---|---|

| 16 | **Shared API contracts** | Define contracts in `packages/api-contracts` as Zod schemas or JSON Schema. Generate Python dataclasses AND TypeScript types from the same source. |

| 17 | **Shared Azure utilities** | Both connector and core_api do Azure auth, Cosmos queries, blob storage — extract once, use everywhere. |

| 18 | **Shared test fixtures** | Integration tests in `tests/integration/` spin up connector + core_api + phase-lab together via Docker Compose at monorepo root. |

| 19 | **Consistent linting/formatting** | One ESLint config for TS, one ruff/black config for Python. Currently: only demo-project has `.eslintrc.json`. |

| 20 | **Shared TypeScript tsconfig** | Base `tsconfig.json` at root with per-package overrides. Phase-lab already does this internally. |

  

### 5. CCE System Benefits

  

| # | Improvement | What Changes |

|---|---|---|

| 21 | **Zeus Memory for all repos** | Currently only CCE connects to Zeus. In a monorepo, every service can log learnings, failed approaches, and decisions to the same memory store. |

| 22 | **CCE project template everywhere** | `PROGRESS.md`, phase-based implementation, QA checklists — applied to connector work, core_api work, not just CCE projects. |

| 23 | **Learning capture across services** | `/cce-learn` works in any directory. Session learnings from connector debugging feed into the same Zeus knowledge base as phase-lab wins. |

| 24 | **Unified hooks** | PreCompact, PostToolUse, SessionStart hooks configured once at root, apply everywhere. Per-service hooks via matchers. |

| 25 | **Cross-service agent delegation** | `Task(Explore)` can search the entire monorepo. Find how connector's output format is consumed by core_api and phase-lab in one query. |

  

### 6. Developer Experience

  

| # | Improvement | What Changes |

|---|---|---|

| 26 | **One clone, full system** | `git clone` gets everything. No "which repos do I need?" onboarding. |

| 27 | **Single search** | `grep` / Claude Code search spans all services. Find every reference to a Snowflake table across connector, core_api, and projects. |

| 28 | **Unified git history** | See that a contract change, a connector update, and a phase-lab fix happened together in one commit. `git blame` tells the whole story. |

| 29 | **Simplified .env** | One root `.env` (already exists as `~/.env`) referenced by all services. No per-repo credential duplication. |

| 30 | **Discoverable architecture** | New team members see the full system in one directory tree. `docs/` at root for architecture, per-service `docs/` for specifics. |

  

### 7. Quality & Governance

  

| # | Improvement | What Changes |

|---|---|---|

| 31 | **Cross-file consistency enforcement** | Claude Code's path-scoped rules can enforce "when you change a schema in `packages/core`, also update the matching Python model in `apps/connector`." |

| 32 | **Workspace boundary hooks** | PreToolUse hooks can warn when Claude edits files outside the current service without explicit intent. |

| 33 | **Shared security scanning** | One `dependabot.yml`, one `codeql-analysis.yml` covering all languages and services. |

| 34 | **Contract testing** | Changes to `packages/api-contracts` automatically trigger consumer tests. Impossible to merge a breaking change that only passes in isolation. |

  

### 8. Eliminating Dead Weight

  

| # | Improvement | What Gets Cleaned Up |

|---|---|---|

| 35 | **Remove `claude_code_system`** | Empty placeholder — merge any `.claude/` config into the monorepo root. |

| 36 | **Remove `lessonhub`** | Empty directory. If needed later, create as a package in the monorepo. |

| 37 | **Consolidate `projects/`** | 42 subdirectories, many stale. Active ones become monorepo packages. Inactive ones get archived. |

| 38 | **Git-enable everything** | `enterprise knowledge system`, `power_bi` currently have no git. In a monorepo, they're versioned by default. |

  

---

  

## Cross-Repo Dependency Analysis

  

### Shared Python Dependencies (Version Drift)

  

| Dependency | connector | core_api | Drift |

|---|---|---|---|

| `azure-cosmos` | 4.3.1 | 4.5.1 | Minor |

| `azure-storage-blob` | 12.25.1 | 12.19.0 | 6 patches |

| `azure-identity` | 1.21.0 | 1.15.0 | 6 minor |

| `azure-core` | 1.33.0 | 1.30.0 | 3 minor |

| `snowflake-connector-python` | 3.18.0 | 3.7.0 | **11 minor** |

| `cryptography` | 44.0.2 | 41.0.7 | **3 major** |

| `pandas` | 2.2.3 | 2.2.0 | Patch |

| `pydantic` | 2.12.5 | 2.x | Minor |

  

### Shared TypeScript Dependencies (Version Drift)

  

| Dependency | phase-lab | factoria/openclaw |

|---|---|---|

| `@anthropic-ai/sdk` | 0.39.0 | 0.73.0 |

  

### Extractable Shared Packages

  

| Shared Package | Consumers | Type |

|---|---|---|

| `packages/shared-types` | phase-lab, connector, core_api | TypeScript Zod schemas for API contracts |

| `packages/db-client` | connector, core_api, enterprise-knowledge | Python PostgreSQL connection + query helpers |

| `packages/azure-auth` | connector, core_api, enterprise-knowledge | Python Azure credential management |

| `packages/api-contracts` | All services | JSON Schema / OpenAPI definitions |

| `infra/modules/container-app` | All deployable services | Reusable Bicep module |

  

---

  

## Recommended Tool: Nx

  

| Criteria | Nx | Turborepo | Pants | Bazel |

|---|---|---|---|---|

| TypeScript support | Native, first-class | Native | Experimental (v2.28+) | Heavy config |

| Python support | Plugins + task wrapping | None | Native, excellent | Heavy config |

| Team size fit | Perfect | OK | Overkill | Overkill |

| Azure integration | Good (custom executors) | Manual | Manual | Manual |

| Learning curve | Moderate | Low | High | Very high |

  

### Proposed Monorepo Structure

  

```

monorepo/

  .claude/

    commands/          # CCE skills (all 14)

    skills/            # CCE skill library (178 skills)

    agents/            # Custom subagents

    rules/             # Path-scoped rules (Python, TS, Azure, Power BI)

    settings.local.json

  CLAUDE.md            # Root: global rules, monorepo conventions

  apps/

    phase-lab/         # TypeScript pnpm monorepo (API + Web + packages)

      CLAUDE.md        # Pipeline architecture, provider pattern

    connector/         # Python Prefect pipelines

      CLAUDE.md        # Prefect flows, Docker, Azure SDK

    core_api/          # Python Azure Functions

      CLAUDE.md        # Serverless, Cosmos, Snowflake

    enterprise-knowledge/  # Python Streamlit

      CLAUDE.md        # Streamlit patterns

  packages/

    shared-types/      # TypeScript Zod schemas (API contracts)

    db-client/         # Python database utilities

    azure-auth/        # Python Azure credential management

    api-contracts/     # JSON Schema / OpenAPI definitions

  tools/

    power-bi/          # Power BI templates and custom visuals

    clients/           # Client configurations

  infra/

    docker/            # Shared Dockerfiles

    modules/           # Reusable Bicep/Terraform modules

  docs/                # Architecture, onboarding

  .github/workflows/   # Unified CI/CD

```

  

---

  

## Migration Order

  

1. **Phase-lab** first — already a pnpm monorepo, nearly copy-paste

2. **CCE** — becomes the `.claude/` layer at monorepo root

3. **connector** + **core_api** — Python services with shared Azure deps

4. **enterprise knowledge system** — small, low risk

5. **clients** + **power_bi** — version-controlled assets, no build config needed

6. **projects/** — archive stale ones, migrate active ones as packages

  

---

  

## Summary

  

**38 concrete improvements** across 8 categories:

- 6 Claude Code intelligence improvements (highest value, lowest effort)

- 4 dependency management fixes

- 5 CI/CD improvements

- 5 code sharing patterns

- 5 CCE system benefits

- 5 developer experience gains

- 4 quality/governance improvements

- 4 dead weight eliminations

  

The highest-value, lowest-effort wins are items 1-6 (Claude Code intelligence) — they require only directory restructuring and CLAUDE.md files, no build tool changes.