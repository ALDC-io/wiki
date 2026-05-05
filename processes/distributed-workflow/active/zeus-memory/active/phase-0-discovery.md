---
tags: [workflow, zeus-memory, phase-0, discovery, architecture]
aliases: [Zeus Memory Phase 0, Discovery and Architecture Planning]
sources: []
created: 2026-05-02
updated: 2026-05-02
---

# Phase 0 — Discovery & Architecture Planning

**Priority:** 0 (prerequisite) · **Status:** Not Started · **Blocker:** No codebase access yet — this phase is docs-only

## Objective

Document everything known about Zeus Memory's current state from existing wiki pages, source documents, and CCE integration context. Design the target architecture for tenant data source ingestion. Produce a gap analysis that's ready to execute once codebase access is granted.

This phase does NOT require codebase access. It works from:
- The `zeus-memory.md` entity page (stale — last updated April 2026)
- Source docs in `sources/obsidian-import/research/OpenTribe/`
- CCE project docs (Zeus Memory is CCE's backend)
- The Zeus Onboarding Doc at `sources/obsidian-import/research/CCE/Setup/Zeus Onboarding Doc - Steps.md`

## Current State (to be filled by Phase 0 session)

_This section will be populated by the first Phase 0 session._

### What the wiki says (April 2026)
- Streamlit prototype with mocked Lululemon data
- Core workflow proven: ingest → drift detection → update proposal → human approval
- Deterministic routing + LLM-assisted explanation/rewriting
- No real API integrations (Confluence, Jira, Git all mocked)
- No multi-tenant architecture
- No production deployment

### What we know has changed (May 2026)
- Product is running with real tenants
- Food Bank Canada demo to 75 people
- CCE integration (Zeus is the backend for cross-session memory)
- Tenant model in use (tenant IDs, API keys documented in Zeus Onboarding Doc)

### Gap: what's unknown
- Where the production codebase lives
- What the current tenant data model looks like
- What API integrations exist today vs. still mocked
- How the CCE Zeus API relates to the tenant ingestion system

## Confluence API Integration Design

_To be designed during Phase 0 session. Key areas:_

### Endpoints needed
- Space enumeration: `GET /wiki/api/v2/spaces`
- Page listing: `GET /wiki/api/v2/spaces/{id}/pages`
- Page content: `GET /wiki/api/v2/pages/{id}` (with `body-format=storage`)
- CQL search: `GET /wiki/rest/api/content/search` (for incremental sync)

### Authentication model
- **Confluence Cloud**: OAuth 2.0 (3LO) or API token (basic auth)
- **Confluence Data Center**: Personal access tokens or OAuth
- For tenant onboarding: OAuth 2.0 preferred (no credential sharing)

### Rate limits
- Confluence Cloud: ~100 requests/minute (varies by plan)
- Pagination: cursor-based for v2 API
- Strategy: respect `Retry-After` headers, exponential backoff

### Data model mapping
- Confluence Space → Zeus Knowledge Domain
- Confluence Page → Zeus Document Record
- Page section (heading-delimited) → Zeus Section (unit of drift detection)
- Page labels/metadata → Zeus tags/classification

## Tenant Ingestion Architecture Proposal

_To be designed during Phase 0 session. Key decisions:_

1. **Connector pattern**: How do individual tool connectors (Confluence, Jira, Git) plug into the system? Interface/protocol? Plugin model?
2. **Storage model**: Where do ingested documents live? Same store as CCE's Zeus Memory? Separate tenant-scoped storage?
3. **Sync strategy**: Full initial ingest + incremental delta? Webhook-driven? Polling?
4. **Normalization**: Common document model across all source types? Or source-specific models with a query abstraction?

## Gap Analysis

_To be produced during Phase 0 session. Template:_

| # | Gap | Requires Codebase Access? | Estimated Effort | Priority |
|---|---|---|---|---|
| 1 | _example: "No real Confluence API client exists"_ | Yes — need to verify | | |

## Architecture Decision: Extend vs. New Service

_To be documented during Phase 0 session. Options:_

- **A: Extend existing Zeus Memory API** — add ingestion endpoints to whatever CCE connects to
- **B: New ingestion service** — separate service that writes into Zeus Memory's storage
- **C: Connector plugin model** — each data source is a standalone plugin/worker that follows a common interface

## Open Questions

- 2026-05-02 — What is the Zeus Memory production stack? (Framework, hosting, database)
- 2026-05-02 — Is the CCE Zeus API the same system that would handle tenant data ingestion?
- 2026-05-02 — What roles/domains were the 75 demo attendees in? (Affects testing strategy)
- 2026-05-02 — Is there a Jira project for Zeus Memory work?

## Boot Prompt

````
You are starting the Zeus Memory workstream, Phase 0: Discovery and Architecture Planning.

CONSTRAINT: Paul does not have codebase access yet. This phase works from existing docs only. Do NOT attempt to explore any Zeus Memory repo.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read the workstream hub: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\README.md`
3. Read this phase: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-0-discovery.md`
4. Read in parallel:
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\zeus-memory.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\cce.md`
   - `C:\Users\PaulRussell\repos\wiki\sources\obsidian-import\research\OpenTribe\Research and Planning\Zeus Memory Prototype Architecture - Trigger, Drift Detection, and Writeback.md`
   - `C:\Users\PaulRussell\repos\wiki\sources\obsidian-import\research\CCE\Setup\Zeus Onboarding Doc - Steps.md`

Plan mode rule: Phase 0 is plan-mode-first every session.

DELIVERABLES:
1. Current-state summary from existing docs (fill the "Current State" section)
2. Confluence API integration design (fill endpoints, auth, rate limits, data model sections)
3. Tenant ingestion architecture proposal (fill connector pattern, storage, sync sections)
4. Gap analysis table (what unknowns require codebase access to resolve)
5. Architecture decision document (evaluate options A/B/C)

Write findings into this file (phase-0-discovery.md). Update README.md session log.
Checkpoint per `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## Session Log

_(append sessions here)_

## See Also

- [[../README]] — workstream hub
- [[phase-1-confluence-ingestion]] — next phase (blocked on codebase access)
- [[zeus-memory]] — product entity page
- [[cce]] — CCE integration context
- [[confluence-migration]] — ALDC's own Confluence migration (demonstrates the API)
