---
tags: [process, operations, jira, scrum]
aliases: [Jira Board Structure, ALDC Scrum Board]
sources: []
created: 2026-05-04
updated: 2026-05-04
---

# Jira Board Structure — ALDC Scrum Board

Standard board layout for client project boards (FU92, GP, etc.). Three swimlanes separate reactive support work, planned sprint work, and internal research/tooling.

## Swimlanes

### 1. Support

Client-reported bugs and production issues. Sprint-tied — support work consumes sprint capacity and must be visible in velocity.

**Columns:** Triage → In-Progress → Internal UAT → Waiting On Client → Client UAT → Done

| Column | Entry criteria | Exit criteria |
|--------|---------------|---------------|
| Triage | Support email or client-reported issue received | Root cause identified, fix plan documented |
| In-Progress | Developer actively working the fix | Code fix complete, ready for testing |
| Internal UAT | Fix deployed to test environment | Validated internally — data correct, no regressions |
| Waiting On Client | Blocked on client action (info, access, credentials, approval, UAT scheduling) | Client provides what's needed |
| Client UAT | Client actively validating the fix | Client confirms resolved |
| Done | Client confirmed, ticket closed | — |

**Examples:** FU92-394 (Viant actuals missing), FU92-395 (DAX role error)

### 2. Development

Planned sprint work — features, enhancements, scheduled tech debt. Sprint-tied.

**Columns:** To-Do → In-Progress → Code Review → Internal UAT → Client UAT → Done

| Column | Entry criteria | Exit criteria |
|--------|---------------|---------------|
| To-Do | Scoped, estimated, assigned to sprint | Developer picks it up |
| In-Progress | Developer actively working | PR opened |
| Code Review | PR open — Semgrep + Claude review + code owner | PR approved and merged |
| Internal UAT | Deployed to test/QA environment | Validated internally |
| Client UAT | Client testing the feature | Client signs off |
| Done | Merged to main, deployed to prod, client confirmed | — |

**Examples:** GP-217 (CI/CD pipeline), GP-218 (Work Pools), GP-208 (Inventory feed)

### 3. Research & Tooling

Internal tooling, infrastructure, architecture spikes, and investigations. **Sprint-agnostic** — does not count toward sprint velocity. Provides visibility for work that would otherwise be invisible.

**Columns:** Backlog → In-Progress → Done

| Column | Entry criteria | Exit criteria |
|--------|---------------|---------------|
| Backlog | Idea or need identified, worth tracking | Developer starts investigating |
| In-Progress | Active research or development | Outcome reached (tool built, spike concluded, or graduated to Development) |
| Done | Outcome documented, tool deployed, or decision made | — |

**Graduation rule:** When research proves out and becomes production-ready, create a proper sprint ticket in Development. The Research ticket links to it and moves to Done.

**Examples:** aldc-observability, aldc-shipyard, Prefect cost analysis, wiki infrastructure

## Cross-Cutting: Waiting On Client

"Waiting On Client" applies across all swimlanes. Tickets can enter this state from any column and return to where they were when unblocked. Common triggers:

- Need error details or reproduction steps (support)
- Need API tokens, OAuth grants, or account access (development)
- Need client approval on scope or design (development)
- Need client to begin UAT (all)

## Board Configuration (Jira)

FU92 is a team-managed (next-gen) project. To configure:

1. Board view → **...** menu → **Configure board**
2. Add/rename columns to match the layout above
3. Set up swimlanes based on issue labels or issue types:
   - Support: `Bug` issue type or `support` label
   - Development: `Story` / `Task` issue types
   - Research & Tooling: `research` label or custom issue type
4. Column constraints (optional WIP limits): In-Progress max 3, Code Review max 5

## Boot Prompt — Board Setup Session

````
You are configuring the ALDC Scrum Board in Jira for the FU92 project. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\wiki\CLAUDE.md`
2. Read this page: `C:\Users\PaulRussell\repos\wiki\processes\operations\jira-board-structure.md`

Task: Help Paul configure the FU92 Jira board with 3 swimlanes (Support, Development, Research & Tooling) and the column structure documented above.

Steps:
1. Check current board configuration — what columns and swimlanes exist today
2. Add/rename columns per the documented layout
3. Set up swimlane rules (Bug issue type → Support lane, Story/Task → Development, research label → Research & Tooling)
4. Move existing tickets to the correct swimlane:
   - FU92-394 (Viant connector) → Support / In-Progress
   - FU92-395 (DAX role error) → Support / Triage
   - FU92-342 (Viant conversions PK) → check current status
5. Verify the board looks right

If Jira API can't configure board layout, guide Paul step-by-step through the UI.
````

## See Also

- [[ai-pr-workflow]] — PR review workflow (Semgrep + Claude + code owner)
- [[ticket-breakdown-to-ship]] — ticket lifecycle from requirements through deploy
- [[flight-check-engineering-guide]] — DAX-specific context for Fusion92 support tickets
