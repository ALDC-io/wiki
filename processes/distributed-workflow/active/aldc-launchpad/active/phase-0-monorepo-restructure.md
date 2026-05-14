---
tags: [ops-platform, launchpad, monorepo, restructure, completed]
created: 2026-05-13
updated: 2026-05-13
---

# Phase 0R: Monorepo Restructure

**Boot prompt:** `aldc-launchpad/.claude/commands/launchpad-phase0r.md` → `/launchpad-phase0r`
**Status:** COMPLETED (2026-05-13)
**Effort:** 1 session
**Unblocks:** All new development (Phase 0C, 1A, 1B, 1C)

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

### 2026-05-13 — Phase 0R executed and completed

- did: Created `aldc-launchpad/` repo with full directory structure. Migrated all ops-platform files to `platform/master/` (11 pages, 3 data files, base.css, SPA shell). Added `prefect-connectors` as git submodule at `connectors/`. Created `shared/client-registry.json` (GEP + Fusion92). Copied CLAUDE.md from draft. Migrated 16 skill files to `.claude/commands/` with updated paths. Created placeholder READMEs for all packages. Created `api/credential-exchange/` from api-auth-exchange. Verified all SPA routes resolve correctly (CSS + data fetch relative paths confirmed). Created Phase 0C (Connector Framework & Live Deployment) as new demo-priority phase. Updated execution-path.md with Lane D for connector work.
- decided: Phase 0C added to run alongside Phase 1A — live connector deployment is capstone demo moment. `migrations/connectors/` directory created for legacy connector catalog. Amazon Ads US is demo deploy candidate.
- next: `/launchpad-phase0c` for connector framework analysis + deploy pipeline. `/launchpad-phase1a` for credential dashboard.

## Key Decisions

- 2026-05-13 — Monorepo over multi-repo: all components linked via client registry; one onboarding touches every package
- 2026-05-13 — aldc-shipyard remains for general ops docs, non-product scripts
- 2026-05-13 — prefect-connectors stays as its own repo, linked as git submodule
- 2026-05-13 — Phase 0C (Connector Framework) added: analyze prefect-connectors + core_api, build migration catalog, enable live demo deployment

## See Also

- [[phase-1a-credential-dashboard]] — First module to build in the new structure
- [[../README]] — Launchpad project overview
