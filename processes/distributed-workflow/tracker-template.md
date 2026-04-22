---
tags: [process, distributed-workflow, template]
aliases: [Tracker Template]
sources: []
created: 2026-04-18
updated: 2026-04-18
---

# Tracker Template

Copy this file as `processes/distributed-workflow/active/<workstream-slug>.md` to start a new workstream. Replace placeholders in `{{ }}`.

---

```markdown
---
tags: [distributed-workflow, active, {{workstream-tag}}]
aliases: [{{Workstream Display Name}}]
sources: []
created: {{YYYY-MM-DD}}
updated: {{YYYY-MM-DD}}
---

# {{Workstream Title}}

## Goal

{{One paragraph: what "done" looks like for this workstream. If you can't write this clearly, you don't have enough scope yet — go to plan mode.}}

## Lane

Wiki: {{ALDC | Neurospect}}

Owned paths (this workstream may write here):

- `{{path/under/wiki/}}`
- `{{another/path/}}`

Read-only outside the lane. Cross-lane edits go through *Cross-Lane Request* (see [[../orchestration-pattern]]).

## Required Context

Every session must read these at boot:

- [[{{page-1}}]] — {{why it matters}}
- [[{{page-2}}]] — {{why it matters}}

Cross-wiki references use absolute paths, never wikilinks:

- `C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\orchestration-pattern.md`

## Plan-Mode Rule

{{Workstream-specific override of the defaults in [[../session-lifecycle]]. Examples: "always plan-mode the first session of each Confluence space; subsequent batches skip if scope unchanged" or "every session is plan-mode-first until a written design exists".}}

## Session Log

Append-only. Newest at the bottom.

### {{YYYY-MM-DD HH:MM}} — {{one-line summary}}

- did: {{what was done}}
- decided: {{what was chosen}}
- next: {{what the next session picks up}}

## Decisions Log

Durable choices that affect future sessions. One bullet per decision; date it.

- {{YYYY-MM-DD}} — {{decision and reason}}

## Pending Wiki Updates

Proposed edits to shared files (`index.md`, `log.md`, `action-items.md`, daily notes). Applied during end-of-day merge session.

- `index.md`: {{exact line/section to add or change}}
- `log.md`: {{exact row to append}}
- `action-items.md`: {{Open-section line(s) to add}}

## Blockers / Open Questions

For Paul. Each gets a date so it's clear how long it has been pending.

- {{YYYY-MM-DD}} — {{question or blocker}}

## Cross-Lane Requests

Wanted to write outside the lane? Don't. Write here instead.

- {{YYYY-MM-DD}} — wanted to change `{{path}}` for `{{reason}}`. Belongs to `{{other-workstream}}`'s lane.

## Next Session Boot Prompt

Copy-paste the block below into a fresh Claude Code session.

````
You are resuming the {{workstream}} workstream. Boot procedure:

1. Read `C:\Users\PaulRussell\repos\{{wiki-name}}\CLAUDE.md`.
2. Read this tracker: `C:\Users\PaulRussell\repos\{{wiki-name}}\processes\distributed-workflow\active\{{workstream-slug}}.md`.
3. Read every page in *Required Context* (parallel reads).
4. Pick up at the *next:* line of the most recent *Session Log* entry.

Plan mode rule for this workstream: {{quote the Plan-Mode Rule above}}.

When you're done, follow the checkpoint procedure in
`C:\Users\PaulRussell\repos\wiki\processes\distributed-workflow\session-lifecycle.md` § *Checkpoint*.
````
```

---

## See Also

- [[README]]
- [[orchestration-pattern]]
- [[session-lifecycle]]
