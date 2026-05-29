---
tags: [workstream, zeus-memory, wiki, ingestion, active]
aliases: [Wiki Ingestion, Wiki Zeus Ingestion]
sources: []
created: 2026-05-26
updated: 2026-05-26
---

# Wiki -> Zeus Memory Ingestion

Ingest the ALDC LLM Wiki (262 pages, ~3.76 MB) into [[zeus-memory]] for hybrid search (keyword + vector), MCP tool access, and cross-session AI retrieval.

## Motivation

The wiki is currently only accessible via direct file reads in Claude Code sessions. Ingesting it into Zeus Memory makes all operational knowledge — processes, client details, architecture decisions, ticket histories, runbooks — searchable via MCP `recall`/`search` tools and available to all Zeus-powered AI interactions.

## Jira Tracking

| Ticket | Phase | Summary | Status |
|--------|-------|---------|--------|
| [ALDC-209](https://analyticlabsdc.atlassian.net/browse/ALDC-209) | Epic | Wiki -> Zeus Memory Ingestion Pipeline | To Do |
| [ALDC-210](https://analyticlabsdc.atlassian.net/browse/ALDC-210) | P1 | Wiki chunker — heading-aware markdown splitter | To Do |
| [ALDC-211](https://analyticlabsdc.atlassian.net/browse/ALDC-211) | P1 | Wiki ingestion service — BaseIngestionService subclass | To Do |
| [ALDC-212](https://analyticlabsdc.atlassian.net/browse/ALDC-212) | P1 | Source registration — wiki prefix group + classification | To Do |
| [ALDC-213](https://analyticlabsdc.atlassian.net/browse/ALDC-213) | P1 | Alembic migration — wiki retention policy (permanent) | To Do |
| [ALDC-214](https://analyticlabsdc.atlassian.net/browse/ALDC-214) | P2 | Wiki ingestion daemon + dry-run validation | To Do |
| [ALDC-215](https://analyticlabsdc.atlassian.net/browse/ALDC-215) | P3 | Git-based incremental sync + reconciliation | To Do |
| [ALDC-216](https://analyticlabsdc.atlassian.net/browse/ALDC-216) | P3 | Wikilink -> entity_mentions graph materialization | To Do |

## Architecture

### Approach

BaseIngestionService subclass (direct DB, same pattern as Nextcloud/Fireflies/Slack) — not the rate-limited API. This gives batch inserts, automatic dedup via ingestion_ledger, parallel PII scanning, and embedding queue population.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Ingestion path | `BaseIngestionService` subclass | Direct DB: no rate limits, batch transactions, proven pattern |
| Chunking | H2-boundary split, 6K target | 132 of 255 pages exceed 8K Voyage truncation; heading split preserves semantics |
| External ID | `wiki\x1f{path}\x1f{git_sha}\x1f{chunk_idx}` | Git SHA is ground truth for change; \x1f matches Nextcloud convention |
| Change detection | Git-native (`git diff --name-only`) | Fast path: 0-20 files per cycle. Full reconciliation weekly. |
| Classification | Per-directory source types | Clients/tickets = confidential+operational; concepts/processes = internal+reference |
| Retention | Permanent (`ttl_days = -1`) | Wiki is SSOT — never expires. Deletion via reconciliation sync. |
| Path denylist | vault/, sources/, templates, non-.md | vault/ = credentials, sources/ = 260 archived imports |

### Chunking Strategy

```
Pages <= 6K chars  -->  single chunk (no split) -- ~120 pages
Pages > 6K chars   -->  split on ## (H2) boundaries
                   -->  + summary chunk (frontmatter + first paragraph + heading list)
                   -->  each chunk gets context preamble:
                        [Wiki: {title}] [Path: {path}] [Tags: {tags}]
                        [Section: {heading}] [Chunk {n}/{total}]

If single H2 section > 6K  -->  sub-split on ### (H3) then paragraph boundaries
```

Expected output: ~600-800 total chunks from 255 ingestible pages.

### Source Classification Matrix

| Wiki Directory | `item.source` | content_origin | sensitivity | intent |
|---|---|---|---|---|
| `entities/clients/` | `wiki_entity_client` | authoritative | confidential | operational |
| `entities/people/` | `wiki_entity_people` | authoritative | confidential | operational |
| `entities/repos/`, `entities/tools/` | `wiki_entity` | authoritative | internal | reference |
| `concepts/` | `wiki_concept` | authoritative | internal | reference |
| `processes/` | `wiki_process` | authoritative | internal | reference |
| `tickets/` | `wiki_ticket` | authoritative | confidential | operational |
| `daily/`, `workplan/`, `standup/` | `wiki_daily` | user_contributed | internal | personal_note |
| Everything else | `wiki` | authoritative | internal | reference |

### Metadata Schema (per chunk, JSONB)

```json
{
  "wiki_path": "entities/clients/active/gep.md",
  "wiki_category": "entity/client",
  "wiki_tags": ["gep", "client", "active"],
  "wiki_aliases": ["GEP", "Global E-commerce Partners"],
  "wiki_updated": "2026-05-22",
  "wiki_section": "## Deployment History",
  "wiki_links": ["Snowflake", "gep-snowflake-pbi-deployment", "GP-256"],
  "chunk_index": 2,
  "chunk_total": 7,
  "is_summary_chunk": false,
  "git_sha": "18e6ca1f"
}
```

## Phases

### Phase 1 — Core Infrastructure

Build the foundational components in `zeus-memory` repo:

1. **Markdown chunker** (`ingestion/_wiki_chunker.py`) — pure-function module, no DB deps. Heading-aware splitting, frontmatter parsing, wikilink extraction, context preamble generation. Unit tests included.
2. **Ingestion service** (`ingestion/wiki_ingestion.py`) — `WikiIngestionService(BaseIngestionService)`. fetch_items reads wiki files, chunks them, builds IngestionItems. Git integration for file SHA lookups. Dry-run support.
3. **Source registration** — add `wiki` prefix group + classification to `source_normalization.py` and `content_origin.py`.
4. **Alembic migration** — seed permanent retention policy (`ttl_days = -1`).

### Phase 2 — Daemon + Validation

5. **Daemon** (`scripts/wiki_ingestion_daemon.py`) — asyncio poll loop following Nextcloud pattern. `--once` for initial load, `--reconcile` for full reconciliation.
6. **Dry-run validation** — verify path filtering, chunking, chunk counts against real wiki.
7. **Initial load** — ingest all 255 pages, verify ~600-800 chunks, test MCP search quality.

### Phase 3 — Incremental + Graph

8. **Git-based incremental sync** — store last_synced_sha in ingestion_ledger, only re-ingest changed files per cycle.
9. **Reconciliation** — detect deleted wiki pages, soft-delete their memories.
10. **Wikilink graph** (optional) — materialize `[[wikilinks]]` into `entity_mentions` table for enhanced graph-based retrieval.

## Files to Create (zeus-memory repo)

| File | Purpose |
|------|---------|
| `ingestion/_wiki_chunker.py` | Pure-function markdown chunker |
| `ingestion/wiki_ingestion.py` | WikiIngestionService subclass |
| `scripts/wiki_ingestion_daemon.py` | Daemon runner |
| `Dockerfile.wiki` | Docker image |
| `ingestion/tests/test_wiki_chunker.py` | Chunker unit tests |
| `ingestion/tests/test_wiki_ingestion.py` | Integration tests |

## Files to Modify (zeus-memory repo)

| File | Change |
|------|--------|
| `ingestion/source_normalization.py` | Add `wiki` prefix group |
| `api/services/content_origin.py` | Add `wiki` classification |
| `docker-compose.ingestion.yml` | Add wiki-ingestion service |
| `alembic/versions/` | New migration for retention policy |

## Key Reference Files

- `zeus-memory/ingestion/base.py` — BaseIngestionService to subclass
- `zeus-memory/ingestion/nextcloud_ingestion.py` — Closest reference (file-based ingestion)
- `zeus-memory/scripts/nextcloud_ingestion_daemon.py` — Daemon pattern
- Full plan: `C:\Users\PaulRussell\.claude\plans\fluttering-wondering-starlight.md`

## Open Questions for Team Review

- [ ] Which ALDC tenant_id should wiki content be routed to?
- [ ] Should the daemon run as a Docker service alongside existing ingesters, or as a standalone cron?
- [ ] Any wiki directories that should be excluded beyond vault/sources?
- [ ] Priority: should this go into the current sprint or next?

## Session Log

| Date | Session | Notes |
|------|---------|-------|
| 2026-05-26 | Plan + ticket creation | Explored zeus-memory ingestion architecture, designed chunking/dedup/classification strategy, created epic ALDC-209 + 7 stories (ALDC-210 through ALDC-216). Wiki tracker created. Pending team review. |

## See Also

- [[zeus-memory]] — target system
- [[processes/distributed-workflow/active/zeus-memory/README|zeus-memory workstream]] — parallel workstream for tenant data source ingestion
- [[confluence-migration]] — related: Confluence content migration into wiki
