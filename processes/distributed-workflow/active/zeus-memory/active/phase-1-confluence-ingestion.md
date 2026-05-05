---
tags: [workflow, zeus-memory, phase-1, confluence, ingestion, connector]
aliases: [Zeus Memory Phase 1, Confluence Ingestion]
sources: []
created: 2026-05-02
updated: 2026-05-02
---

# Phase 1 — Single-Tool Ingestion (Confluence API)

**Priority:** 1 · **Status:** Blocked on Phase 0 + codebase access

## Objective

Build the end-to-end pipeline for ingesting a tenant's Confluence content into their Zeus Memory knowledge base. This is the proof-of-pattern phase — the connector architecture established here becomes the template for all subsequent integrations (Phase 2+).

## Prerequisites

- [ ] Phase 0 complete — architecture direction approved
- [ ] Codebase access granted
- [ ] Confluence API integration design finalized (from Phase 0)
- [ ] Tenant data model confirmed

## Sub-Phases

### 1a — Confluence API Client
Backend connector: authenticate to a tenant's Confluence instance, enumerate spaces, list pages, extract content + metadata.

**Deliverables:**
- Confluence API client (REST v2)
- OAuth 2.0 (3LO) auth flow for Confluence Cloud
- Space enumeration + page listing with pagination
- Content extraction (storage format → markdown/structured)

### 1b — Normalization
Convert Confluence pages into Zeus Memory's internal document model.

**Deliverables:**
- Confluence page → Zeus Document Record mapping
- Section-level parsing (heading-delimited sections as units of drift detection)
- Metadata extraction (labels, last-modified, author, parent page)
- Attachment handling strategy (link vs. download)

### 1c — Storage
Write normalized documents into the tenant's knowledge base with deduplication and versioning.

**Deliverables:**
- Tenant-scoped document storage
- Deduplication (same page re-ingested = update, not duplicate)
- Version history (track changes across ingestion runs)
- Relationship preservation (page hierarchy, cross-page links)

### 1d — Incremental Sync
After initial full ingest, detect new/updated/deleted pages efficiently.

**Deliverables:**
- CQL-based change detection (`lastModified > lastSyncTimestamp`)
- Delta processing (only re-ingest changed pages)
- Deletion handling (page removed from Confluence → mark stale in Zeus)
- Sync state tracking (last successful sync timestamp per space)

### 1e — Configuration API/UI
Tenant admin connects their Confluence, selects what to ingest, triggers the initial migration.

**Deliverables:**
- Configuration endpoint / UI for connecting Confluence
- Space selection (which spaces to include/exclude)
- Initial ingest trigger
- Ingestion status/progress API (what was ingested, what failed, what's pending)

## Acceptance Criteria

- [ ] Can authenticate to a real Confluence instance via OAuth 2.0
- [ ] Full space ingest: all pages in a space extracted, normalized, stored
- [ ] Incremental sync: re-running picks up only changes since last run
- [ ] Admin can configure which spaces to ingest
- [ ] Ingestion errors are logged and surfaced, not silently dropped
- [ ] Confluence API rate limits respected with backoff
- [ ] At least one real-tenant test (ALDC's own Confluence as tenant zero)

## Boot Prompt

````
You are resuming the Zeus Memory workstream, Phase 1: Confluence Ingestion.

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read the workstream hub: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\README.md`
3. Read this phase: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-1-confluence-ingestion.md`
4. Read Phase 0 findings: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-0-discovery.md`
5. Read in parallel:
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\zeus-memory.md`
   - `C:\Users\PaulRussell\repos\wiki\entities\projects\cce.md`

Plan mode rule: plan-mode on first session; skip for sub-phase sessions if scope unchanged.

Pick up at the sub-phase listed in the most recent Session Log entry below.
Checkpoint per `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## Session Log

_(append sessions here)_

## See Also

- [[../README]] — workstream hub
- [[phase-0-discovery]] — prerequisite (architecture decisions)
- [[phase-2-additional-integrations]] — next phase (extends the connector pattern)
- [[confluence-migration]] — ALDC's own Confluence migration (Atlassian MCP experience)
