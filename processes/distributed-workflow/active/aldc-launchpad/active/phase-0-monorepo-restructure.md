---
tags: [ops-platform, launchpad, monorepo, restructure, active]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 0R: Monorepo Restructure

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase0r.md` → `/launchpad-phase0r`
**Status:** Active
**Effort:** 1–2 days
**Blocks:** All new development (credential hub, tracker, client portal)

## Goal

Graduate ops-platform from a subdirectory in aldc-shipyard into its own monorepo (`aldc-launchpad`) structured for multi-service development: master platform, client portal, connectors, warehouse, tracker, and API services. Every future module lands in the right place from day 1.

## Deliverables

1. `aldc-launchpad/` repo created on GitHub with full directory structure
2. `platform/master/` — existing ops-platform code migrated and functional
3. `connectors/` — git submodule pointing to prefect-connectors
4. `shared/client-registry.json` — GEP + Fusion92 entries linking all systems
5. Placeholder READMEs for warehouse/, tracker/, portal/, api/, infra/
6. `.claude/commands/` — migrated Launchpad skill files
7. Product-level CLAUDE.md
8. All existing pages load correctly from new paths

## Directory Structure

```
aldc-launchpad/
├── platform/
│   ├── master/             # ALDC internal (moved from ops-platform/)
│   └── portal/             # Client-facing (Phase 3+)
├── connectors/             # git submodule → prefect-connectors
├── warehouse/              # Snowflake schemas, SQL templates
├── tracker/                # Jira replacement engine (Phase 2+)
├── api/                    # Azure Functions
│   └── credential-exchange/
├── shared/
│   └── client-registry.json
├── infra/                  # Terraform/Bicep
├── .claude/commands/
├── CLAUDE.md
└── README.md
```

## Session Log

### 2026-05-13 18:00 — Phase created during planning session

- did: Designed monorepo structure, created wiki tracker, created `/launchpad-phase0r` boot prompt skill
- decided: Directory structure finalized (platform/master, portal, connectors, warehouse, tracker, api, shared, infra). aldc-shipyard stays as-is.
- next: Execute restructure — create repo, migrate files, set up submodules, verify pages load

## Key Decisions

- 2026-05-13 — Monorepo over multi-repo: all components linked via client registry; one onboarding touches every package
- 2026-05-13 — aldc-shipyard remains for general ops docs, non-product scripts
- 2026-05-13 — prefect-connectors stays as its own repo, linked as git submodule

## Next Session Boot Prompt

````
You are working on **ALDC Launchpad Phase 0R** (Monorepo Restructure).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this tracker: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\aldc-launchpad\active\phase-0-monorepo-restructure.md`
3. Read the approved plan: `C:\Users\PaulRussell\.claude\plans\floating-giggling-neumann.md` — Phase 0 section
4. Read `C:\Users\PaulRussell\repos\aldc-shipyard\ops-platform\index.html` — understand current SPA shell

Goal: Create aldc-launchpad repo, migrate ops-platform, set up submodules, verify all pages load.
````

## See Also

- [[phase-1a-credential-dashboard]] — First module to build in the new structure
- [[../README]] — Launchpad project overview
