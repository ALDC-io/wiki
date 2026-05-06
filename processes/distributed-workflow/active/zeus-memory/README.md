---
tags: [workflow, zeus-memory, opentribe, tenant-ingestion, data-sources]
aliases: [Zeus Memory Ingestion, Tenant Data Source Ingestion]
sources: []
created: 2026-05-02
updated: 2026-05-02
---

# Zeus Memory — Automated Tenant Data Source Ingestion

Automated ingestion of a new tenant's existing tool data (Confluence, Jira, Git, etc.) into their Zeus Memory knowledge base. Phases build incrementally: prove the pattern with a single Confluence connector (Option 1), then expand to batch multi-source migration (Option 2) and self-service onboarding.

## Architecture Overview

```
  Tenant's Existing Tools              Zeus Memory Platform
  ─────────────────────              ──────────────────────

  ┌──────────┐
  │Confluence │──┐
  └──────────┘  │
  ┌──────────┐  │   ┌──────────────┐   ┌────────────────┐   ┌───────────────┐
  │  Jira    │──┼──►│  Ingestion   │──►│  Tenant KB     │──►│Drift Detection│
  └──────────┘  │   │  Layer       │   │  (normalized)  │   │+ Update Props │
  ┌──────────┐  │   └──────────────┘   └────────────────┘   └───────────────┘
  │   Git    │──┘         │                                        │
  └──────────┘      ┌─────▼──────┐                           ┌─────▼──────┐
                    │  Progress  │                           │  Human     │
                    │  Tracking  │                           │  Approval  │
                    └────────────┘                           └────────────┘
```

## Roadmap — Priority Order

| Phase | Domain | Status |
|---|---|---|
| **0** | Discovery & Architecture Planning (docs-only, no codebase access) | **Current** |
| **1** | Single-Tool Ingestion — Confluence API (prove the connector pattern) | Blocked on Phase 0 + codebase access |
| **2** | Additional Integrations — Jira + Git | Blocked on Phase 1 |
| **3** | Batch Migration Orchestration | Blocked on Phase 2 |
| **4** | Tenant Onboarding Automation (self-service) | Blocked on Phase 3 |

## Lane

Wiki: **ALDC**

Owned paths (this workstream may write here):

- `processes/distributed-workflow/active/zeus-memory/` (this folder)
- `entities/projects/zeus-memory.md` (product entity page)

Read-only outside the lane. Cross-lane edits go through *Cross-Lane Request*.

## Required Context

Every session must read these at boot:

- `C:\Users\PaulRussell\repos\wiki\CLAUDE.md` — wiki schema
- This README — workstream hub
- `C:\Users\PaulRussell\repos\wiki\entities\projects\zeus-memory.md` — product entity
- `C:\Users\PaulRussell\repos\wiki\entities\projects\cce.md` — CCE integration context

Cross-wiki references use absolute paths, never wikilinks:

- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\orchestration-pattern.md`
- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md`

## Plan-Mode Rule

**Phase 0: plan-mode-first every session** (architecture decisions are the deliverable).

**Phase 1+: plan-mode on the first session of each phase** until Paul approves the phase spec. Sub-phase sessions (1a, 1b, etc.) skip plan mode if scope is unchanged.

## Decisions Log

- 2026-05-02 — **Option 1 first**: Start with single-tool Confluence ingestion to prove the connector pattern before attempting batch migration (Option 2). Confluence is the natural first choice — it's the product wedge and ALDC has demonstrated Confluence API access via MCP.
- 2026-05-02 — **Subfolder structure**: Using the Navira pattern (README hub + `active/phase-*.md`) because this workstream has 5 phases spanning distinct domains.
- 2026-05-02 — **No codebase access yet**: Phase 0 is docs-only. Codebase exploration deferred until Paul gets access.

## Session Log

### 2026-05-02 — bootstrap

- **did**: Created workstream tracker (this README) + 5 phase pages. Updated `index.md` and `zeus-memory.md` entity page. Designed phased plan from Option 1 → Option 2 progression.
- **decided**: Subfolder pattern (like Navira). Phase 0 is docs-only since no codebase access yet. Confluence first as the proof-of-pattern connector.
- **next**: Phase 0 session — document current state from existing wiki/source docs, design tenant ingestion architecture, produce gap analysis.

## Pending Wiki Updates

- `index.md`: Add Zeus Memory workstream entry under Distributed Workflow section
- `log.md`: `| 2026-05-02 | workstream-create | Created zeus-memory workstream tracker + 5 phase pages |`

## Blockers / Open Questions

- ~~2026-05-02 — **Codebase access**: Paul does not have access to the Zeus Memory codebase yet. Blocks Phase 1+.~~ **RESOLVED 2026-05-05** — Repo cloned to `C:\Users\PaulRussell\repos\zeus-memory`. Phase 0 can now include codebase exploration.
- 2026-05-02 — **Current product state**: Wiki describes Zeus Memory as a Streamlit prototype (April 2026). Product has evolved (tenant model, Food Bank Canada demo, 75-person audience, CCE integration). Phase 0 must reconcile wiki with reality.
- 2026-05-02 — **Demo audience roles**: The 75-person demo — what domains/roles are they in? If user-testing stage, a workshop format could work (CEO, Engineer, Product Owner, DevOps, QA all stress-test differently).

## Workflow Pages

### Active

- [[phase-0-discovery]] — Discovery & architecture planning (docs-only, no codebase access)
- [[phase-1-confluence-ingestion]] — Single-tool pattern: Confluence API
- [[phase-2-additional-integrations]] — Jira + Git integrations
- [[phase-3-batch-migration-orchestration]] — Multi-source orchestration
- [[phase-4-tenant-onboarding-automation]] — Self-service onboarding

### Completed

_(none yet)_

## Next Session Boot Prompt

````
You are resuming the Zeus Memory workstream, Phase 0: Discovery and Architecture Planning.

Repo cloned at `C:\Users\PaulRussell\repos\zeus-memory`. Codebase exploration is now available.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read the workstream hub: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\README.md`
3. Read this phase: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-0-discovery.md`
4. Read in parallel:
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\zeus-memory.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\cce.md`
   - `C:\Users\PaulRussell\repos\wiki\sources\obsidian-import\research\OpenTribe\Research and Planning\Zeus Memory Prototype Architecture - Trigger, Drift Detection, and Writeback.md`

Plan mode rule: Phase 0 is plan-mode-first every session.

DELIVERABLES:
1. Current-state summary from existing docs
2. Confluence API integration design (endpoints, auth, data model)
3. Tenant ingestion architecture proposal (connector pattern, storage, sync)
4. Gap analysis (what unknowns require codebase access to resolve)
5. Architecture decision document

Write findings into phase-0-discovery.md. Update README.md session log.
Checkpoint per `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## See Also

- [[zeus-memory]] — product entity page
- [[cce]] — uses Zeus Memory as its backend for cross-session knowledge persistence
- [[confluence-migration]] — ALDC's own Confluence migration (demonstrates Confluence API via MCP)
- [[processes/distributed-workflow/active/navira/README|navira]] — prior art for multi-phase workstream structure
