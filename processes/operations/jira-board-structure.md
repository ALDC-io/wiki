---
tags: [process, operations, jira, scrum]
aliases: [Jira Board Structure, ALDC Scrum Board]
sources: []
created: 2026-05-04
updated: 2026-05-07
---

# Jira Board Structure — ALDC Scrum Board

Cross-project board layout for ALDC. Three swimlanes separate reactive support work, planned sprint work, and internal research/tooling across all projects.

**Original board:** [Board 38](https://analyticlabsdc.atlassian.net/jira/people/712020:2edc7338-25ca-4661-8616-4f5d117be21c/boards/38) — "ALDC - Scrum" board (not a people board as originally assumed). Swimlane config is locked (not board admin).

**Decision (2026-05-07):** Create a new prototype board backed by a saved cross-project JQL filter. Board 38 stays as-is; tickets migrate to the new board once validated.

**Projects:** GP (GEP/Navira), FU92 (Fusion 92), DV (Eclipse), KA (Kit and Ace). ZC (Zeus Chat) excluded — service desk with its own workflow.

**Routing mechanism:** Labels (`support`, `development`, `research-tooling`). Every ticket gets exactly one swimlane label.

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

**Sprint assignment:** Do NOT assign sprints to R&T tickets. They appear in the swimlane via label, not sprint. Velocity reports automatically exclude them.

**Examples:** aldc-observability, aldc-shipyard, Prefect cost analysis, wiki infrastructure

## Cross-Cutting: Waiting On Client

Implemented as a **label** (`waiting-on-client`), not a status. Any ticket in any column can be flagged. Optionally also use Jira's built-in flag (red flag icon) for visual urgency. Common triggers:

- Need error details or reproduction steps (support)
- Need API tokens, OAuth grants, or account access (development)
- Need client approval on scope or design (development)
- Need client to begin UAT (all)

## Labels

| Label | Purpose |
|---|---|
| `support` | Swimlane: Support |
| `development` | Swimlane: Development |
| `research-tooling` | Swimlane: Research & Tooling |
| `waiting-on-client` | Cross-cutting: blocked on client action |

Every new ticket must have exactly one swimlane label at creation.

## Board Column Layout

The cross-project board maps columns from all three swimlanes:

| Board column | Swimlane(s) | Status mapping |
|---|---|---|
| Triage | Support | New bug/issue received |
| Backlog | R&T | Idea tracked, not active |
| To-Do | Development | Scoped and sprint-assigned |
| In-Progress | All | Active work |
| Code Review | Development | PR open |
| Internal UAT | Support, Development | Deployed to test |
| Waiting On Client | Support | Blocked on client |
| Client UAT | Support, Development | Client validating |
| Done | All | Complete |

## Ticket Classification (current → target)

### GP Project

| Ticket | Current Status | Target Swimlane | Target Status | Labels | Notes |
|---|---|---|---|---|---|
| GP-199 | Development | Development | In-Progress | `development` | ASIN attribution, active |
| GP-218 | Development | Development | In-Progress | `development` | Work Pools, blocked Snowflake |
| GP-197 | Development | Development | In-Progress | `development` | Marketplace filter, active |
| GP-217 | Development | Development | Done | `development` | CI/CD pipeline, done per wiki |
| GP-200 | QA | Development | Internal UAT | `development` | Amazon UK order line |
| GP-219 | Consulting/Design | Development | To-Do | `development` | Sellercloud migration, S2/S3 |
| GP-246 | Consulting/Design | Development | To-Do | `development` | Migration testing, S3 |
| GP-225 | Consulting/Design | Development | To-Do | `development` | Unified marketing schema, S3 |
| GP-221 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | UK PPC OAuth, blocked |
| GP-226 | Consulting/Design | Development | To-Do | `development` | Google Ads, S4 |
| GP-222 | Consulting/Design | Development | To-Do | `development` | Facebook Ads, S4 |
| GP-223 | Consulting/Design | Development | To-Do | `development` | Target+, S4 |
| GP-230 | Consulting/Design | Development | To-Do | `development` | SP-API registration, S4 |
| GP-227 | Consulting/Design | Development | To-Do | `development` | Historical backfill, S5 |
| GP-228 | Consulting/Design | Development | To-Do | `development` | TikTok/Creator, S5 |
| GP-229 | Consulting/Design | Development | To-Do | `development` | Email campaigns, S5 |
| GP-231 | Consulting/Design | Development | To-Do | `development` | Seller Central, S5 |
| GP-232 | Consulting/Design | Development | To-Do | `development` | Sellercloud inventory, backlog |
| GP-233 | Consulting/Design | Development | To-Do | `development` | COGS, backlog |
| GP-237 | Consulting/Design | Development | To-Do | `development` | Access epic |
| GP-238 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | Google Ads access |
| GP-239 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | Facebook access |
| GP-240 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | Target+ access |
| GP-241 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | UK PPC follow-up |
| GP-242 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | Sellercloud creds |
| GP-244 | Consulting/Design | Development | To-Do | `development` | GHCR auth |
| GP-245 | Consulting/Design | Development | To-Do | `development`, `waiting-on-client` | SmartScout access |
| GP-234 | Consulting/Design | Research & Tooling | Backlog | `research-tooling` | SmartScout — needs refinement |
| GP-235 | Consulting/Design | Research & Tooling | Backlog | `research-tooling` | Unstructured data — needs refinement |
| GP-211 | Consulting/Design | (inspect) | (TBD) | (TBD) | Check if R&T or Dev |
| GP-212 | Consulting/Design | (inspect) | (TBD) | (TBD) | Check if R&T or Dev |
| GP-183 | To Do | Development | To-Do | `development` | Google Ads connection |

### FU92 Project

| Ticket | Current Status | Target Swimlane | Target Status | Labels | Notes |
|---|---|---|---|---|---|
| FU92-394 | In Progress | Support | In-Progress | `support` | Viant DSP actuals |
| FU92-395 | To Do | Support | Triage | `support` | DAX role error |
| FU92-393 | To Do | Support | Triage | `support` | NetSuite QA connection |
| FU92-392 | To Do | Support | Triage | `support` | Viant connector timeout |
| FU92-342 | To Do | (inspect) | (TBD) | (TBD) | LinkedIn conversions — check if support or dev |
| FU92-341 | To Do | (inspect) | (TBD) | (TBD) | Viant conversions — check |
| FU92-387 | To Do | (inspect) | (TBD) | (TBD) | Manual entry blocked |
| FU92-386 | To Do | (inspect) | (TBD) | (TBD) | Legacy flight check templates |
| FU92-379 | To Do | (inspect) | (TBD) | (TBD) | Flight check data sync |
| FU92-378 | To Do | (inspect) | (TBD) | (TBD) | App improvements |
| FU92-381 | To Do | (inspect) | (TBD) | (TBD) | Locked fields (subtask) |
| FU92-366 | To Do | (inspect) | (TBD) | (TBD) | Info button tooltip (subtask) |
| FU92-365 | To Do | (inspect) | (TBD) | (TBD) | Graceful calculations (subtask) |
| FU92-361 | To Do | (inspect) | (TBD) | (TBD) | Job number (subtask) |
| FU92-355 | To Do | (inspect) | (TBD) | (TBD) | Delete data store (subtask) |
| FU92-353 | To Do | (inspect) | (TBD) | (TBD) | Platform name matching (subtask) |
| FU92-352 | To Do | (inspect) | (TBD) | (TBD) | Model updates (subtask) |
| FU92-335 | To Do | (inspect) | (TBD) | (TBD) | Admin screen reload (subtask) |

## Current Status Schemes (audited 2026-05-07)

### GP Project Workflow

All transitions are global (any status → any status). Team-managed project.

| Status | ID | Category | Maps to target column |
|---|---|---|---|
| Needs Priority | 10587 | To Do | *(legacy — not in target layout)* |
| Consulting/Design | 10176 | To Do | *(legacy — not in target layout)* |
| To Do | 10182 | To Do | To-Do |
| Development | 10177 | In Progress | In-Progress |
| QA | 10179 | In Progress | Internal UAT |
| GEP QA | 10180 | In Progress | Client UAT |
| Done | 10178 | Done | Done |

**Missing statuses:** Triage, Code Review, Backlog, Waiting On Client

### FU92 Project Workflow

All transitions are global. Team-managed project.

| Status | ID | Category | Maps to target column |
|---|---|---|---|
| Needs Priority | 10586 | To Do | *(legacy — not in target layout)* |
| To Do | 10320 | To Do | To-Do |
| In Progress | 10321 | In Progress | In-Progress |
| QA | 10452 | In Progress | Internal UAT |
| Ready for Customer | 10485 | In Progress | Client UAT |
| Done | 10322 | Done | Done |

**Missing statuses:** Triage, Code Review, Backlog, Waiting On Client

### Current labels in use (no swimlane labels yet)

GP: `BLOCKED`, `PendingApproval`, `navira-roadmap`, `phase-0`/`1a`/`1b`/`1c`/`2`/`3`/`4`, `credentials`, `infrastructure`, `prefect`, `needs-refinement`
FU92: `BLOCKED`, `Approved`

## Implementation Phases

### Phase 0 — Verify Board Capabilities ✅ COMPLETE (2026-05-07)

**Finding:** Board 38 is a Scrum board ("ALDC - Scrum"), not a people board. Swimlane configuration exists but is disabled — Paul is not a board/project admin.

**Decision:** Create a new prototype Scrum board backed by a saved cross-project JQL filter. Manual UI process — steps documented below.

#### New board creation steps (manual)

1. **Create saved filter:** Filters → Advanced → JQL: `project in (GP, FU92, DV, KA) AND statusCategory != Done ORDER BY priority DESC` → Save as "ALDC Sprint Board"
2. **Create board:** Boards → Create board → Scrum board → Board from existing Saved Filter → select "ALDC Sprint Board"
3. **Configure swimlanes:** Board settings → Swimlanes → Select method: Queries → add:
   - Support: `label = support`
   - Development: `label = development`
   - Research & Tooling: `label = research-tooling`
   - (default "Everything Else" catches unlabeled)
4. **Configure columns:** after creating missing statuses on project boards

### Phase 1 — Label Scheme + Column Structure (1-2 hours)

Establish labels and board column layout on the new prototype board. No tickets moved yet.

**Prerequisite:** New board created per Phase 0 steps above.

````
**Phase 1 — Labels + Columns**

1. Read `C:\Users\PaulRussell\repos\wiki\processes\operations\jira-board-structure.md`

Steps:
1. Add missing statuses to each project's board (team-managed: Settings → Columns → add column):
   - GP needs: Triage, Code Review, Backlog, Waiting On Client
   - FU92 needs: Triage, Code Review, Backlog, Waiting On Client
   - Note: GP already has QA (→ Internal UAT) and GEP QA (→ Client UAT)
   - Note: FU92 already has QA (→ Internal UAT) and Ready for Customer (→ Client UAT)

2. Configure new board columns (union of all 3 swimlanes):
   Triage | Backlog | To-Do | In-Progress | Code Review | Internal UAT | Waiting On Client | Client UAT | Done

3. Verify swimlanes configured per Phase 0 step 3:
   - Support: JQL `label = support`
   - Development: JQL `label = development`
   - Research & Tooling: JQL `label = research-tooling`
   - Everything Else: catches unlabeled tickets (triage prompt)

Rollback: columns and swimlanes can be reconfigured any time. Labels removed via bulk edit.
````

### Phase 2 — Ticket Migration (1-2 hours)

Label and re-status all open tickets per the classification table above.

````
**Phase 2 — Ticket Migration**

1. Read `C:\Users\PaulRussell\repos\wiki\processes\operations\jira-board-structure.md` § Ticket Classification

Pre-flight:
- Export current state of all open GP + FU92 tickets (key, status, labels) as snapshot for rollback

Steps:
1. Apply swimlane labels first (non-destructive):
   - Jira API: PUT /rest/api/3/issue/{key} with label update
   - Use the classification table — GP tickets are pre-classified, FU92 "(inspect)" tickets need reading first

2. Classify the "(inspect)" tickets:
   - Read each FU92 ticket and GP-211/GP-212 in Jira
   - Assign swimlane label based on: is this a client-reported bug (support), planned feature (development), or internal research (R&T)?

3. Transition statuses:
   - For each ticket: GET /rest/api/3/issue/{key}/transitions → find target status → POST transition
   - Bulk: all "Consulting/Design" GP tickets → "To-Do"
   - GP-217 → Done (already complete)
   - FU92-395, FU92-393, FU92-392 → Triage

4. After all tickets migrated: verify the "Everything Else" swimlane is empty

Rollback: labels removable, status transitions reversible. Snapshot from pre-flight enables full restore.
````

### Phase 3 — Validation + Wiki Update (30-60 min)

````
**Phase 3 — Validation**

1. Open new prototype board → verify 3 swimlanes display correctly
2. Verify each swimlane shows expected tickets in expected columns
3. Verify "Everything Else" swimlane is empty
4. Test sprint filter: R&T tickets should NOT appear on sprint boards
5. Update this wiki page: mark phases complete, remove "(inspect)" entries
6. Update Navira README if GP ticket statuses changed
7. Add labeling requirement to ticket-breakdown-to-ship.md
````

### Phase 4 — Process Enforcement (ongoing)

- Every new ticket gets exactly one swimlane label at creation
- Sprint planning: review "Everything Else" swimlane for unlabeled tickets
- Consider Jira automation: "When issue created without swimlane label, add comment to classify"

## See Also

- [[SHIP-002]] — Team Pulse tool (reads board data to generate Highs/Lows/Celebrations)
- [[ai-pr-workflow]] — PR review workflow (Semgrep + Claude + code owner)
- [[ticket-breakdown-to-ship]] — ticket lifecycle from requirements through deploy
- [[flight-check-engineering-guide]] — DAX-specific context for Fusion92 support tickets
