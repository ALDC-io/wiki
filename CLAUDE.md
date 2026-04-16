# LLM Wiki — Schema

You are maintaining Paul Russell's personal LLM Wiki. Paul is a Data & Agentic AI Engineer at Analytic Labs (ALDC). This wiki is a persistent, compounding knowledge base covering his work, clients, repos, tools, business logic, and processes.

## Purpose

This wiki exists so that any Claude Code session pointed at this directory can immediately understand:
- What Paul works on (clients, tickets, repos)
- How ALDC's data stack works (Eclipse → Snowflake → Power BI)
- How to deploy, test, and ship changes
- Business logic and domain rules for each client
- Credentials and access information (in the gitignored vault/)

## Directory Structure

```
wiki/
├── CLAUDE.md              # THIS FILE — read first, always
├── index.md               # Master catalog — search here to find pages
├── log.md                 # Append-only operation log
├── sources/               # RAW SOURCES — immutable, never modify
│   └── obsidian-import/   # Paul's Obsidian notes (original form)
├── vault/                 # CREDENTIALS — .gitignore'd, never expose outside this dir
│   └── credentials.md     # All passwords, tokens, keys, connection strings
├── entities/              # One page per distinct thing
│   ├── clients/           # GEP, Fusion92, etc.
│   ├── repos/             # clients, connector, core_api
│   ├── tools/             # Snowflake, Power BI, Eclipse, Prefect
│   └── people/            # Team members, contacts
├── concepts/              # Ideas, architecture, business rules
│   ├── architecture/      # System design, data flows, environment models
│   ├── business-logic/    # Client-specific domain rules
│   └── patterns/          # ALDC conventions and recurring patterns
├── processes/             # Step-by-step runbooks
│   ├── deployment/        # End-to-end deployment guides
│   ├── ticket-lifecycle/  # Breakdown → develop → test → ship
│   └── operations/        # Snowflake tasks, PBI refresh, data shares
├── tickets/               # One page per ticket (decisions, design, outcome)
│   ├── gep/
│   └── fusion92/
├── daily/                 # Daily notes, POAs
└── assets/                # Images
```

## Page Format

Every wiki page uses this format:

```markdown
---
tags: [entity, gep, client]           # Obsidian-compatible tags
aliases: [GEP, Navira, Global E-commerce Partners]  # Alternative names
sources: [sources/obsidian-import/work/gep/...md]    # What this was derived from
created: 2026-04-16
updated: 2026-04-16
---

# Page Title

Brief one-paragraph summary of what this page covers.

## Section

Content with [[wikilinks]] to related pages. Always cross-reference related
entities, concepts, and processes.

## See Also

- [[Related Page 1]]
- [[Related Page 2]]
```

### Conventions
- Use `[[wikilinks]]` for all internal cross-references (Obsidian-compatible)
- Tags go in YAML frontmatter, not inline
- Cite sources: when a fact comes from a source file, note it
- One page per entity/concept/process — update existing pages rather than creating duplicates
- Keep pages focused: if a section grows beyond ~200 lines, split into its own page
- Image references use relative paths: `![description](../assets/filename.png)`

## Core Operations

### 1. Ingest

When Paul says "ingest [source]" or adds files to sources/:

1. **Read** the source file(s) thoroughly
2. **Extract** entities (people, tools, clients, repos), concepts (business rules, architecture), and processes (step-by-step workflows)
3. **For each extracted item:**
   - Check if a wiki page already exists (search index.md)
   - If yes: **update** the existing page with new information, flag contradictions
   - If no: **create** a new page using the page format above
4. **Cross-reference**: Add `[[wikilinks]]` in both directions between related pages
5. **Update index.md**: Add/update entries for all touched pages
6. **Append to log.md**: Record the ingest with timestamp, source, and pages affected

A single source might touch 5-15 wiki pages. That's expected — the value is in the cross-references.

### 2. Query

When Paul asks a question:

1. **Search** index.md and relevant wiki pages for information
2. **Synthesize** an answer citing specific pages with `[[wikilinks]]`
3. **If the answer reveals a gap**: suggest creating a new page or updating an existing one
4. **Optionally**: if the query produced valuable synthesis not captured anywhere, offer to file it as a new concept or process page

### 3. Lint

Periodic health check. Run when Paul says "lint the wiki" or proactively after large ingests:

1. **Orphan pages**: Pages with no inbound `[[wikilinks]]` from other pages
2. **Stale information**: Pages whose `updated` date is old relative to related pages
3. **Missing cross-references**: Mentions of entities/concepts without `[[wikilinks]]`
4. **Index gaps**: Pages that exist but aren't in index.md
5. **Contradictions**: Conflicting facts across pages (flag explicitly, don't silently resolve)
6. **Empty sections**: Pages with placeholder content that needs filling

Report findings as a checklist. Fix simple issues (missing cross-refs, index gaps) automatically. Flag contradictions and stale info for Paul to review.

## Rules

1. **Never modify files in sources/**. They are immutable raw material.
2. **Never expose credentials outside vault/**. Wiki pages may reference credentials by name (e.g., "uses the SellerCloud REST credentials") but never include actual passwords, tokens, or keys.
3. **Always update index.md** when creating or significantly updating a page.
4. **Always append to log.md** for ingest and lint operations.
5. **Prefer updating over creating**. Check if a page exists before making a new one.
6. **Flag contradictions explicitly**. If new information conflicts with existing wiki content, add a `> **Contradiction**:` callout block. Don't silently overwrite.
7. **Cite your sources**. Every factual claim should trace back to a source file, a repo file, or a conversation.

## Key Context

### ALDC Stack
- **Eclipse**: Connector platform — templates define data pulls, connections hold auth, tasks schedule execution
- **Snowflake**: Data warehouse — star schema with shared_dim_* (dimensions) and *_fct_* (facts), extract_* (staging), report_common* (reporting layer)
- **Power BI**: Visualization — consumes report_common views, manual model refresh
- **Prefect**: Orchestration — workflow scheduling and monitoring

### Repos (at C:\Users\PaulRussell\repos\)
- **clients**: Per-client Eclipse configs + Snowflake warehouse SQL. The primary repo.
- **connector**: The Eclipse connector runtime (Docker-based)
- **core_api**: ALDC's core API service

### Active Clients
- **GEP / Navira**: E-commerce analytics — Amazon (US/UK/CA), SellerCloud, Galactica. Snowflake env: PROD_DG1_GEP / TEST_DG1_GEP
- **Fusion92**: Media activation — Meta, Google, Viant, Trade Desk, Amazon Ads. Snowflake env uses Advantage360

### Environment Model (GEP)
| Branch | Snowflake | Power BI |
|--------|-----------|----------|
| feature/* | none | none |
| GEP/development | none | none |
| GEP/user-testing | TEST_DG1_GEP | GEP Test Models |
| main | PROD_DG1_GEP | Production |

Code merge does NOT auto-deploy. Snowflake and Power BI deploys are manual.

### Paul's Preferences
- Handles git commits himself — never run git commit
- Prefers detailed step-by-step guidance for Snowflake/PBI UI operations
- Prefers concise output for SQL and git operations
