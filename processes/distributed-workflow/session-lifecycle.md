---
tags: [process, distributed-workflow, lifecycle]
aliases: [Session Lifecycle, Plan-Mode Rules]
sources: []
created: 2026-04-18
updated: 2026-04-18
---

# Session Lifecycle

What a single distributed-workflow session looks like, end to end. Read with [[orchestration-pattern]] for the cross-session model.

## 1. Boot

In a fresh Claude Code session:

1. Read your wiki's `CLAUDE.md` (the schema you're operating under).
2. Read the workstream's tracker file (`processes/distributed-workflow/active/<workstream>.md`).
3. Read every page listed under the tracker's *Required Context* section. Use parallel tool calls.
4. Verify today's daily note exists (`daily/YYYY-MM-DD.md`); if not, create it from `daily/_template.md`.
5. Note the tracker's *Next Step*. That is your starting brief.

Each tracker ends with a copy-pasteable **Next Session Boot Prompt**. The simplest boot is to paste it into a fresh session.

## 2. Plan mode — when to enter

| Situation | Plan mode? |
|---|---|
| First session of a workstream | **Yes** |
| Scope is unclear or there are multiple viable approaches | **Yes** |
| Work would touch files outside the workstream's lane | **Yes** (or write a Cross-Lane Request) |
| Re-scoping after discovering scope was wrong | **Yes** |
| Resuming approved work from a clear checkpoint | No |
| Trivial doc fixes (typos, formatting) | No |
| Pure ingestion that follows an existing approved runbook | No |
| End-of-day merge session that applies pending updates | No (mechanical) |

Workstream-specific overrides live in each tracker's *Plan-Mode Rule* section. They tighten or relax the defaults above.

**Why plan mode is load-bearing here:** the auto-generated plan file is the cleanest handoff vehicle between sessions. A workstream that has produced an approved plan can resume in any future session by re-reading the tracker + plan, with no human re-briefing.

## 3. Approval

Paul reviews the plan (when in plan mode). Record the outcome in the tracker's *Decisions Log*:

- What was approved.
- Any modifications Paul requested.
- Anything explicitly out of scope.

If not in plan mode, *Decisions Log* is updated only when a non-trivial choice is made mid-session.

## 4. Implementation

Execute. Two rules:

- **Stay in your lane.** If the work expands to files outside the lane, stop and write a *Cross-Lane Request* (see [[orchestration-pattern]]).
- **Don't silently expand scope.** If implementation reveals the plan was wrong, stop and re-enter plan mode rather than making it up as you go.

Use TaskCreate inside the session to track sub-steps. That state is intentionally ephemeral.

## 5. Checkpoint

At the end of every session — even short ones — update the tracker:

- Append a new `### YYYY-MM-DD HH:MM — <one-line>` block to *Session Log* with sub-bullets: `did:`, `decided:`, `next:`.
- Add any durable choices to *Decisions Log*.
- Add any proposed shared-file edits to *Pending Wiki Updates*.
- Add anything blocking to *Blockers / Open Questions*.
- Refresh *Next Session Boot Prompt* if the next slice has changed.

Then append a 2–3 line summary to today's daily note under a `## Distributed Workflow Checkpoint` heading. The daily-note ingest pipeline picks it up automatically; the *Pending Wiki Updates* go through the merge session instead.

## 6. Handoff

The next session — possibly later today, possibly tomorrow, possibly weeks later — should be able to boot from:

1. The tracker.
2. The pages it references.
3. The most recent plan file (if plan mode was used).

Nothing should require Paul's memory or live re-briefing. If the boot prompt isn't enough, the previous session's checkpoint was incomplete — fix it next time.

## End-of-day merge session

A separate, optional session whose only job is to apply *Pending Wiki Updates* from each active tracker to the shared files (`index.md`, `log.md`, `action-items.md`).

- Read each tracker's *Pending Wiki Updates*.
- Apply them to the shared files in one pass.
- Clear the *Pending* sections in each tracker (move applied items to a `## Applied` sub-section dated today, or delete — author's call).
- Append a single `merge` row to `log.md` summarizing what landed.

No plan mode. No design judgment. If a pending update is ambiguous, leave it pending and ask in *Blockers*.

## See Also

- [[README]] — when to use distributed workflow at all.
- [[orchestration-pattern]] — lanes, shared-file protocol, performance techniques.
- [[tracker-template]] — what to write into a tracker.
