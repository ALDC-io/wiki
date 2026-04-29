---
tags: [workflow, navira, phase-4, unstructured, email, documents, vector-search, priority-4]
aliases: [Navira Phase 4, Unstructured Data]
sources: [eclipse_exp/frontend/public/navira/navira-project-plan.html]
created: 2026-04-27
updated: 2026-04-27
---

# Phase 4 — Unstructured Data

**Priority:** 4 · **Interfaces:** 3 · **Status:** Not Started

## Objective

Build a document ingestion and search layer that makes institutional knowledge — trapped in emails, meeting notes, and Word documents — searchable and queryable through Eclipse/Zeus Chat. Architecturally distinct from the structured DW: requires document parsing, embedding, and vector search rather than tabular ETL.

## Interfaces — Build Order

| # | Interface | Rationale |
|---|---|---|
| 1 | **Email** | Highest volume. Well-documented APIs (Graph/Gmail). Establishes parsing + embedding pipeline. |
| 2 | **Meeting Notes** | Structured enough to extract high-value content (date, attendees, agenda, action items). Source depends on tooling. |
| 3 | **Word Documents** | Largest, most complex parsing (tables, images, formatting). Benefits from proven pipeline. |

## High-Level Requirements

- **Document parsing:** Extract text from email bodies, .docx, meeting transcripts, attached documents
- **Chunking & embedding:** Split into searchable chunks, generate vector embeddings for semantic search
- **Vector store:** Store embeddings with metadata (source, date, author, type) for filtered retrieval
- **Zeus Chat integration:** Surface relevant documents via natural language queries
- **Access control:** Respect document-level permissions
- **Incremental sync:** Only process new/modified documents
- **PII handling:** Define policy for sensitive content (redaction, access tiers, or full inclusion)

## Open Questions

| ID | Question | Impact |
|---|---|---|
| Q1 | Microsoft 365 or Google Workspace? | API choice (Graph vs Gmail), auth model |
| Q2 | All company email or specific mailboxes? Include attachments? Retention window? | Data volume (could be massive), storage costs, privacy |
| Q3 | Where do meeting notes live? (Teams, Zoom, Notion, OneNote, Google Docs, shared drive?) | API/connector choice, transcription needs |
| Q4 | Where are Word documents stored? (SharePoint, OneDrive, GDrive, local server?) Single source or scattered? | Connector scope |
| Q5 | Legal/HR constraints on indexing? Employee consent? Data governance policy? | **Hard blocker** — must resolve before any ingestion |
| Q6 | Vector store technology? (Snowflake Cortex, Pinecone, Weaviate, pgvector, Zeus Memory?) | Infra cost, query performance |
| Q7 | What does "searchable" mean? Keyword search or semantic/NL? ("Find emails about Target+ launch" vs "What did we decide about packaging?") | Keyword search (simpler) vs full RAG pipeline |

## Dependencies

| Dependency | Detail |
|---|---|
| **Privacy / Legal Approval** | **Hard blocker.** Cannot ingest employee email or internal documents without explicit approval and data governance policy. |
| **Eclipse / Zeus Chat (Production)** | Primary consumption layer. Must integrate with existing Zeus interface. |
| **Embedding Infrastructure** | Requires embedding model + vector storage. Cost/latency depends on volume — scope after Q2. |

## Acceptance Criteria

- [ ] Users can find relevant documents via Zeus Chat using natural language
- [ ] Results include source attribution (email subject/date, meeting title, document name)
- [ ] Access control prevents unauthorized document discovery
- [ ] Incremental sync runs daily without re-processing existing documents
- [ ] Query response time under **5 seconds**
- [ ] Privacy policy documented and approved before first production ingestion

## See Also

- [[navira/README|Navira Roadmap]]
- [[zeus-memory]] — potential vector store integration
