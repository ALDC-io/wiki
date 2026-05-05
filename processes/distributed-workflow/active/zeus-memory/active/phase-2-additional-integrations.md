---
tags: [workflow, zeus-memory, phase-2, jira, git, connector]
aliases: [Zeus Memory Phase 2, Additional Integrations]
sources: []
created: 2026-05-02
updated: 2026-05-02
---

# Phase 2 — Additional Integrations (Jira + Git)

**Priority:** 2 · **Status:** Blocked on Phase 1

## Objective

Extend the connector pattern proven with Confluence to Jira and Git. Extract the common abstraction so adding future connectors is straightforward. Git integration is especially critical — code changes are the primary trigger for drift detection, which is the core Zeus Memory workflow.

## Prerequisites

- [ ] Phase 1 complete — Confluence connector proven end-to-end
- [ ] Connector abstraction extracted from Phase 1 implementation

## Deliverables

### Base Connector Abstraction
Extract the common pattern from the Confluence connector into a reusable interface:
- Authentication (OAuth 2.0 / API token / PAT)
- Resource enumeration (list what's available)
- Content extraction (pull content + metadata)
- Normalization (convert to Zeus document model)
- Storage (write to tenant KB)
- Incremental sync (detect changes since last run)
- Progress reporting (status, errors, counts)

### Jira Connector
- Issues, epics, stories, bugs (with status transitions)
- Comments and attachments
- Sprint/board context
- Incremental sync via JQL (`updated >= lastSyncTimestamp`)

### Git Connector
- Repository enumeration
- PR/MR listing with diffs
- Commit history with changed files
- Branch/tag metadata
- Webhook support for real-time change detection (vs. polling)

### Cross-Source Linking
When a Jira ticket references a Confluence page, or a Git PR references a Jira ticket, capture the relationship:
- Jira ticket mentions Confluence page URL → relationship stored
- Git commit message contains Jira ticket ID → relationship stored
- Confluence page embeds Jira macro → relationship stored

## Acceptance Criteria

- [ ] Base connector abstraction documented and implemented
- [ ] Jira connector: ingest issues from a real Jira project with incremental sync
- [ ] Git connector: ingest PRs and commits from a real Git repo with incremental sync
- [ ] Cross-source links captured (at least Jira ↔ Confluence and Git ↔ Jira)
- [ ] All three connectors run for the same tenant simultaneously without conflict

## Boot Prompt

````
You are resuming the Zeus Memory workstream, Phase 2: Additional Integrations (Jira + Git).

Boot procedure:
1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read the workstream hub: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\README.md`
3. Read this phase: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-2-additional-integrations.md`
4. Read Phase 1 findings: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-1-confluence-ingestion.md`
5. Read Phase 0 architecture: `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\active\zeus-memory\active\phase-0-discovery.md`

Plan mode rule: plan-mode on first session; skip for subsequent sessions if scope unchanged.
Checkpoint per `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § Checkpoint.
````

## Session Log

_(append sessions here)_

## See Also

- [[../README]] — workstream hub
- [[phase-1-confluence-ingestion]] — prerequisite (connector pattern)
- [[phase-3-batch-migration-orchestration]] — next phase (orchestrates all connectors)
