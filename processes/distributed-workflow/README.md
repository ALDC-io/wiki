---
tags: [process, distributed-workflow, meta]
aliases: [Distributed Workflow, Parallel Sessions]
sources: []
created: 2026-04-18
updated: 2026-05-12
---

# Distributed Workflow

Coordination kit for running **multiple Claude Code sessions in parallel** — across separate workstreams, on the same shared knowledge base — without lost updates, context drift, or plan-mode misuse.

This is the **session-level** extension of the wiki's existing page-level [[CLAUDE|Parallel Ingestion]] pattern. There, subagents propose and a single main agent writes. Here, **each session is the single writer for its own workstream**, and shared files (`index.md`, `log.md`, `action-items.md`, daily notes) are updated through proposals collected in per-workstream tracker files and merged once a day.

## When to use it

- More than one workstream in flight on the same day across different Claude Code sessions.
- A single workstream that spans multiple sessions and needs explicit handoffs (long-running tickets, multi-day migrations, research → design → build sequences).
- Anytime you'd otherwise risk two sessions stepping on the same shared file.

If you're doing one focused thing in one session, you don't need this. Use [[action-items]] and the daily-note ingest pipeline.

## Read these first

- [[orchestration-pattern]] — the pattern itself: lanes, write isolation, shared-file protocol, performance techniques.
- [[session-lifecycle]] — boot → plan-mode → approval → implementation → checkpoint → handoff.
- [[tracker-template]] — copy this when starting a new workstream.

## Active workstreams (this wiki)

- [[active/confluence-migration]] — session coordinator for the Confluence ingest. Mechanics live in [[confluence-migration]] (the runbook); this tracks per-session state.
- [[active/client-workflow-automation]] — design (not yet build) of an automated, sandboxed feature-delivery flow for GEP-style work.

### Client workstreams

- [[active/navira/README|Navira]] — e-commerce analytics (Amazon + DTC). Prefect foundation, marketing ad platforms, sales, inventory, competitor data. 4 phases active, 3 backlog.
- [[active/fusion92/README|Fusion 92]] — dashboards, data pipelines, platform integrations. 11 active (FU92-400–414), 4 backlog, 6 completed. Sprint S3.

When a workstream finishes, move its tracker from `active/` to `archive/` (folder created on first archive).

## Backlog

Ideas scoped but not yet started. Pick one up by moving it to `active/` and opening a tracker.

- [[backlog/wiki-client-restructure]] — reorganize wiki from type-centric to client-centric (GEP/Fusion92 top-level folders, frontmatter-driven Jira state). ~2-3hr migration script.

## Archived workstreams

- [[archive/dv-444-dashboard-rename]] — ✅ 2026-04-21: Renamed the Navira-demo sidebar app's `app_name` from "Dashboard" → "SKU Profitability" via direct CosmosDB patch. Pure data change; no eclipse-2.1 code commits. See [[DV-444]].

## Used by other wikis

A separate sub-wiki at `C:\Users\PaulRussell\repos\neurospect-wiki` (one of Paul's personal projects) references the three pattern docs in this folder **by absolute path**, never by wikilink. This is the only allowed cross-wiki coupling: ALDC research → that sub-wiki, one direction. No content from that sub-wiki appears anywhere in this wiki — per Paul's isolation rule (saved to memory).

## See Also

- [[CLAUDE]] § *Parallel Ingestion* — the parent pattern.
- [[action-items]] — durable TODO registry; trackers feed into this via end-of-day merge.
