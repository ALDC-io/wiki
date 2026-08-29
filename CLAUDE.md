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
│                          # (artifact registry lives in aldc-launchpad/docs/artifacts/REGISTRY.md)
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
├── workplan/              # Daily work plans (start-of-day task tracker)
├── standup/               # Generated stand-up notes (end-of-day summaries)
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

### 1b. Ingest Daily Notes

When Paul says "ingest today's notes" or "process my daily notes":

1. **Read** the daily file at `daily/YYYY-MM-DD.md` (use today's date if not specified)
2. **Parse** each `## Note` block. Each has a `type:` tag and optional `ref:` tag
3. **Route** each note to the correct wiki page based on type + ref:
   - `type: ticket, ref: GP-208` → update `tickets/gep/GP-208.md`
   - `type: process, ref: deployment` → update relevant page in `processes/deployment/`
   - `type: business-logic, ref: GEP` → update or create page in `concepts/business-logic/`
   - `type: tool, ref: Snowflake` → update `entities/tools/snowflake.md`
   - `type: decision` → update the page referenced by `ref:`
   - `type: general` → use judgment based on content
4. **Update** the target page with the new information. Add to the most relevant section, or create a new section if needed. Update the `updated:` date in frontmatter.
5. **Cross-reference**: Add `[[wikilinks]]` where the note mentions other entities/concepts
6. **Extract action items** (both explicit and heuristic):
   - **Explicit**: any `## Note` block with `type: action` — the note body is the action description, `ref:` (if present) becomes the action's ref wikilink
   - **Heuristic**: scan all note bodies regardless of type for natural-language action items. Positive signals: "need to", "have to", "should", "remember to", "follow up", "confirm", "figure out", "delete", "refactor", "add", "verify", imperatives with a clear actor. Negative signals: past-tense descriptions, already-done statements, passive context. Use judgment — err toward capturing when the phrase reads like a TODO, skip when it's a completed fact
   - A single note can yield multiple action items (e.g., one infrastructure note may require "confirm X", "decide Y", and "decommission Z"). Treat each extracted action as its own subject; do not collapse distinct actions into one line
   - For each extracted item:
     - Build idempotency key = `(daily_file_name, semantic description of the action)`. Check every existing line in the Open and Done sections of `action-items.md` whose source is `from [[<daily_file>]]`. If any of those lines describes the same action (semantic match — minor paraphrasing counts as equivalent), **skip** the new extraction. Otherwise it's new
     - Exact-string matching is not sufficient — an LLM re-run may word the extracted description slightly differently each time. Compare intent, not surface text
     - Append new items to the **Open** section of `action-items.md`:
       `- [ ] <concise description> — from [[YYYY-MM-DD]] · ref: [[target-page]] · added YYYY-MM-DD`
     - Use the note's `ref:` as the `ref:` wikilink when obvious; infer from context (ticket ID, tool name, client name mentioned) when not; omit entirely when no clean anchor exists
   - Update `action-items.md` frontmatter `updated:` date to today
7. **Update index.md** if any new pages were created
8. **Append to log.md**: `| date | ingest-daily | Processed N notes from daily/YYYY-MM-DD.md → list of pages touched; added M action items |`

The daily file itself is **never modified** — it stays as a permanent record in `daily/`.

See `daily/_template.md` for the note format and type reference.

### 2. Query

When Paul asks a question:

1. **Search** index.md and relevant wiki pages for information
2. **Synthesize** an answer citing specific pages with `[[wikilinks]]`
3. **If the answer reveals a gap**: suggest creating a new page or updating an existing one
4. **Optionally**: if the query produced valuable synthesis not captured anywhere, offer to file it as a new concept or process page

### 3. Rescan Action Items

On-demand sweep of all historical daily files for action items. Use when Paul says "rescan action items" or "refresh action items":

1. **Enumerate** every file matching `daily/YYYY-MM-DD.md` (skip `_template.md` and any `daily/archive/` subfolder if present)
2. **For each file** apply the same explicit + heuristic extraction defined in step 6 of "Ingest Daily Notes". Remember that a single note may yield multiple distinct action items; treat each as its own subject
3. **Idempotency**: for each extracted item, compare against all existing Open and Done lines sourced `from [[<daily_file>]]` using the `(daily_file_name, semantic description)` key. Skip when an existing line describes the same action (semantic match, not string equality). Otherwise add as new
4. **Append** new items to the **Open** section, then sort Open by `added` date descending (newest first)
5. **Update** `action-items.md` frontmatter `updated:` and `last_rescan:` dates
6. **Report back** to Paul: `Scanned N files, extracted X candidate items, added M new, skipped K as duplicates`
7. **Append to log.md**: `| date | rescan-actions | Scanned N daily files, added M new action items |`

### 4. Lint

Periodic health check. Run when Paul says "lint the wiki" or proactively after large ingests:

1. **Orphan pages**: Pages with no inbound `[[wikilinks]]` from other pages
2. **Stale information**: Pages whose `updated` date is old relative to related pages
3. **Missing cross-references**: Mentions of entities/concepts without `[[wikilinks]]`
4. **Index gaps**: Pages that exist but aren't in index.md
5. **Contradictions**: Conflicting facts across pages (flag explicitly, don't silently resolve)
6. **Empty sections**: Pages with placeholder content that needs filling

Report findings as a checklist. Fix simple issues (missing cross-refs, index gaps) automatically. Flag contradictions and stale info for Paul to review.

## Parallel Ingestion (Large Sources)

For large ingests (hundreds of pages — e.g., Confluence migration, full Obsidian import), parallelize with subagents under a strict rule: **subagents read and propose; only the main agent writes.** For daily notes, single-source ingests, or routine updates, stay single-agent — coordination overhead outweighs the win.

**Pattern:**

1. **Partition** the source into disjoint batches (one subagent per Confluence space, or ~50 pages per batch). Aim for partitions whose target wiki pages don't overlap.
2. **Spawn 2–3 subagents** via the `Agent` tool. Each subagent:
   - Reads its assigned batch
   - Extracts entities, concepts, processes
   - Checks `index.md` for existing pages that would be touched
   - Returns a **structured proposal**: list of `(target_page, action, proposed_content_or_diff, index_entries, wikilinks_to_add)`
   - Does **not** call `Edit` or `Write` on any wiki file
3. **Main agent** merges proposals, resolves overlaps where two subagents touch the same page, applies writes sequentially, updates `index.md` once with the union of entries, and appends a single `log.md` row for the whole batch.

**Why:** Subagents editing shared files (`index.md`, `log.md`, high-traffic entity pages) would produce lost updates. Centralizing writes eliminates that class of bug. Reading and proposing is the expensive part and parallelizes cleanly — structured proposals also force subagents to surface decisions (page name, section placement, wikilink targets) where the main agent can spot-check them before committing.

### 5. Work Plan (Start of Day)

**This is the first operation at the start of every work day.** Before any ticket work begins, generate (or confirm) a daily work plan at `workplan/YYYY-MM-DD.md`. This is Paul's live task tracker for the day — items move through statuses as work progresses, and feed directly into the end-of-day standup.

1. **Read the previous day's standup** (`standup/` most recent file) — pull "Plan for Tomorrow" items as carried-forward work
2. **Check blockers from previous standup** — scan for any that may have been unblocked (new emails, Jira updates, Slack messages mentioned in conversation)
3. **Check the Navira roadmap** ([[navira/README|Navira Roadmap]]) and sprint tickets for S2/S3 items that are actionable
4. **Generate** the work plan using the template at `workplan/_template.md`:
   - **Carried Forward** — items from previous standup's "Plan for Tomorrow"
   - **Unblocked Today** — items that were blocked but can now proceed (with context on what unblocked them)
   - **Today's Plan** — ordered table with `#`, `Ticket`, `Task`, `Status`, `Notes`. Statuses: `Planned` | `In Progress` | `Done` | `Blocked` | `Deferred`
   - **Waiting On Others** — items blocked on external parties (who, what, last contact date)
   - **Ad-Hoc** — empty section for unplanned work that comes up during the day
   - **End-of-Day Status** — empty section filled in at standup time
5. **If a work plan already exists for today**, update it rather than creating a duplicate
6. **During the day**, update item statuses as work progresses (`Planned` → `In Progress` → `Done`)
7. **Do not append to log.md** for work plan generation (it's a planning artifact, not an operation)

The work plan is the live contract for the day. Keep it honest — if something gets deferred, mark it `Deferred` with a reason, don't delete it.

### 6. Stand-Up (End of Day)

At the end of a work session (or when Paul asks for a standup), generate a daily stand-up note at `standup/YYYY-MM-DD.md`:

1. **Read today's work plan** (`workplan/YYYY-MM-DD.md`) — use completed items as the primary source for "What I Did Today"
2. **Scan `log.md`** for all entries dated today
3. **Scan wiki pages** with `updated:` date of today (check frontmatter)
4. **Review conversation context** for work done in the current session
5. **Generate** the standup note with three sections:

```markdown
---
tags: [standup, daily]
date: YYYY-MM-DD
---

# Stand-Up — YYYY-MM-DD

## What I Did Today
<!-- Group by workstream/ticket. Each item: one sentence of what was done + outcome. -->

## Blockers
<!-- Anything blocked on someone else. Include who and what's needed. -->

## Plan for Tomorrow
<!-- 2-4 bullet points. Concrete next actions, not vague goals. -->
```

6. **Update today's work plan** — fill in the "End-of-Day Status" section with a brief summary
7. **If a standup already exists for today**, update it rather than creating a duplicate
8. **Do not append to log.md** for standup generation (it's a report, not an operation)

The standup is Paul's cheat sheet for the next morning's team standup. Keep it scannable — bullet points, not paragraphs. Prioritize "what changed" and "what's blocked" over process details.

## Rules

1. **Never modify files in sources/**. They are immutable raw material.
2. **Never expose credentials outside vault/**. Wiki pages may reference credentials by name (e.g., "uses the SellerCloud REST credentials") but never include actual passwords, tokens, or keys. **When an ingested source (e.g. a Confluence page) contains hard-coded credentials, extract them to `vault/` so the values aren't lost** — redact in the wiki page and leave a pointer naming the credential + its vault file. Never skip this step even if the vault file has to be created.
3. **Always update index.md** when creating or significantly updating a page.
4. **Always append to log.md** for ingest and lint operations.
5. **Prefer updating over creating**. Check if a page exists before making a new one.
6. **Flag contradictions explicitly**. If new information conflicts with existing wiki content, add a `> **Contradiction**:` callout block. Don't silently overwrite.
7. **Cite your sources**. Every factual claim should trace back to a source file, a repo file, or a conversation.
8. **Subagents are read-only for the wiki**. During parallel ingestion, only the main agent applies writes. Subagents return structured proposals.
9. **Bulk ingests are additive.** When ingesting from bulk sources (Confluence import, Obsidian dump, large source folder), add new detail and new sections rather than rewriting existing content. Rewrites are only for explicit corrections, targeted single-source updates, or contradictions flagged per rule #6.

## Key Context

### ALDC Stack
- **Eclipse**: Connector platform — templates define data pulls, connections hold auth, tasks schedule execution
- **Snowflake**: Data warehouse — star schema with shared_dim_* (dimensions) and *_fct_* (facts), extract_* (staging), report_common* (reporting layer)
- **Power BI**: Visualization — consumes report_common views; refresh cadence configured per semantic model (GEP Test: scheduled daily, ad-hoc refresh available)
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
