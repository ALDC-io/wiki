---
tags: [backlog, wiki, infrastructure, automation, restructure]
status: backlog
created: 2026-05-02
updated: 2026-05-02
---

# Backlog: Wiki Client-Centric Restructure

## Idea

Reorganize the wiki from its current entity/type-centric layout into a client-first structure, with tighter Jira integration.

## Motivation

- Daily work is client-scoped (GEP, Fusion92) — having client pages scattered across `tickets/gep/`, `entities/clients/`, `processes/` adds navigation friction
- Jira state (backlog / in-progress / done) is not surfaced in the wiki — no quick way to see "what's in-progress for GEP right now"
- Workflow Automation monitoring layer (Option A, 2026-05-02) signals growing automation — wiki structure should support automated state sync, not just manual ingest

## Proposed Structure

```
wiki/
├── clients/
│   ├── gep/
│   │   ├── README.md          ← hub: lists tickets by Jira status (from frontmatter)
│   │   ├── tickets/           ← GP-*.md (moved from tickets/gep/)
│   │   └── processes/         ← GEP-specific runbooks (moved from processes/)
│   └── fusion92/
│       ├── README.md
│       ├── tickets/           ← FU92-*.md
│       └── processes/
├── concepts/                  ← unchanged (cross-client patterns)
├── entities/                  ← unchanged (tools, repos, people)
├── processes/                 ← cross-client processes only
├── daily/ workplan/ standup/  ← unchanged
└── vault/                     ← unchanged
```

## Key Decision: Frontmatter over Folders for Jira State

Jira state MUST live in frontmatter, not folder paths. Ticket state changes constantly — folder-based state would require `git mv` on every transition, breaking all wikilinks.

Correct pattern:
```yaml
---
jira_status: In Progress   # updated when ticket transitions
jira_ticket: GP-248
client: gep
phase: phase-0
---
```

Client hub `README.md` scans frontmatter and renders tickets by status. State change = one frontmatter field update, no file moves.

## Migration Steps (when actioned)

1. Write a migration script: rename all `tickets/gep/GP-*.md` → `clients/gep/tickets/GP-*.md`
2. Bulk-update all `[[wikilinks]]` pointing to old paths
3. Move GEP-specific process pages (e.g. `gep-snowflake-pbi-deployment.md`) into `clients/gep/processes/`
4. Create `clients/gep/README.md` hub with frontmatter-driven ticket index
5. Update `index.md` to point to new locations
6. Run wiki lint to catch any broken links

## Scope estimate

~2-3 hours. Primarily file moves + wikilink updates. The migration script makes it safe.

## See Also

- [[client-workflow-automation]] — the automation layer being built (GEP)
- [[sandbox-feature-delivery]] — patterns that would live in `concepts/` post-restructure
- [[cce-troubleshooting]] — patterns that would stay in `concepts/`
